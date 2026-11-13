"""
Issue #61: `agloop report` — formaliza achados de campo (bugs cross-projeto)
como issue real em `yuremarketing/AgLoop`, com confirmação humana obrigatória
antes de qualquer submissão pública (decisão do PO, 2026-11-12): mesmo quando
é o próprio LLM que compôs o relato via `--title`/`--body-file`, o comando só
chama `gh issue create` com `-y`/`--yes` explícito ou "s" no prompt interativo.
"""

from __future__ import annotations

import platform
import re
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

DEFAULT_REPO = "yuremarketing/AgLoop"
SEVERITIES = ("low", "medium", "high")


def _run(cmd: list[str], cwd: Optional[str] = None, timeout: float = 15.0) -> subprocess.CompletedProcess:
    """Single seam for every `gh`/`git` call, so tests mock exactly this function."""
    return subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout)


def _in_docker() -> bool:
    return Path("/.dockerenv").exists()


def _sanitize_slug(origin_url: str) -> str:
    """Turns a git remote URL into a GitHub-label-safe slug (alphanumeric/hyphen only)."""
    slug = origin_url.strip()
    if slug.endswith(".git"):
        slug = slug[:-4]
    slug = re.sub(r"^[a-zA-Z]+://", "", slug)  # https://
    slug = re.sub(r"^[^@/]+@", "", slug)  # git@
    slug = slug.replace(":", "/")  # ssh host:owner/repo -> host/owner/repo
    slug = slug.strip("/")
    slug = re.sub(r"[^a-zA-Z0-9_-]", "-", slug)
    slug = re.sub(r"-{2,}", "-", slug).strip("-")
    return slug or "local-project"


@dataclass
class EnvironmentInfo:
    origin_url: str
    source_slug: str
    agloop_version: str
    platform: str
    in_docker: bool


def detect_environment(repo_root: str = ".") -> EnvironmentInfo:
    """Best-effort: never raises. Falls back to 'unknown'/'local-project' outside a git repo."""
    origin_url = "unknown"
    try:
        res = _run(["git", "config", "--get", "remote.origin.url"], cwd=repo_root)
        if res.returncode == 0 and res.stdout.strip():
            origin_url = res.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass

    source_slug = _sanitize_slug(origin_url) if origin_url != "unknown" else "local-project"

    try:
        from importlib.metadata import PackageNotFoundError, version

        try:
            agloop_version = version("agloop")
        except PackageNotFoundError:
            agloop_version = "dev"
    except ImportError:  # pragma: no cover - importlib.metadata ships with Python 3.8+
        agloop_version = "dev"

    return EnvironmentInfo(
        origin_url=origin_url,
        source_slug=source_slug,
        agloop_version=agloop_version,
        platform=platform.platform(),
        in_docker=_in_docker(),
    )


def render_issue_body(title: str, description: str, severity: str, env: EnvironmentInfo) -> str:
    env_line = env.platform + (" (Docker)" if env.in_docker else "")
    return (
        "## Achado de Campo\n\n"
        f"**Projeto de origem:** {env.origin_url}\n"
        f"**Versão do agloop:** {env.agloop_version}\n"
        f"**Ambiente:** {env_line}\n"
        f"**Severidade:** {severity}\n\n"
        "---\n\n"
        f"{description}\n"
    )


def find_duplicate(title: str, repo: str = DEFAULT_REPO) -> Optional[str]:
    """Best-effort dedupe: a transient `gh` failure never blocks the report, just skips dedupe."""
    try:
        res = _run(
            ["gh", "issue", "list", "-R", repo, "--search", f"{title} in:title", "--json", "url", "--jq", ".[0].url"],
            timeout=15,
        )
    except (OSError, subprocess.TimeoutExpired):
        print("[agloop report] aviso: checagem de duplicatas indisponível (timeout) — seguindo sem dedupe.", file=sys.stderr)
        return None
    if res.returncode != 0:
        print(f"[agloop report] aviso: 'gh issue list' falhou — seguindo sem dedupe ({res.stderr.strip()[:200]}).", file=sys.stderr)
        return None
    url = res.stdout.strip()
    return url or None


def _ensure_label(name: str, repo: str, color: str = "ededed") -> None:
    """Idempotent: `--force` updates the label if it already exists instead of erroring."""
    try:
        _run(["gh", "label", "create", name, "-R", repo, "--color", color, "--force"], timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        pass  # best-effort; `gh issue create` below will surface a clear error if the label truly can't exist


def submit_report(title: str, body: str, source_slug: str, repo: str = DEFAULT_REPO) -> str:
    source_label = f"source:{source_slug}"
    _ensure_label("area:field-report", repo)
    _ensure_label(source_label, repo)

    res = _run(
        ["gh", "issue", "create", "-R", repo, "--title", title, "--body", body, "--label", "area:field-report", "--label", source_label],
        timeout=30,
    )
    if res.returncode != 0:
        raise RuntimeError(f"'gh issue create' falhou: {res.stderr.strip()}")
    return res.stdout.strip()


@dataclass
class ReportResult:
    submitted: bool
    error: bool = False
    url: Optional[str] = None
    duplicate_url: Optional[str] = None
    rendered_body: str = ""
    message: str = ""


def _gh_available() -> bool:
    return shutil.which("gh") is not None


def run_report(
    *,
    title: str,
    description: str,
    severity: str = "medium",
    repo_root: str = ".",
    repo: str = DEFAULT_REPO,
    force: bool = False,
    yes: bool = False,
    confirm: Optional[Callable[[str], bool]] = None,
) -> ReportResult:
    """
    Orchestrates environment detection, dedupe, mandatory human confirmation and submission.

    Never calls `gh issue create` unless `yes=True` or `confirm(body)` returns True — there is
    no code path here that publishes an issue without one of those two explicit human signals.
    """
    if severity not in SEVERITIES:
        raise ValueError(f"severity deve ser um de {SEVERITIES!r}, recebido: {severity!r}")

    if not _gh_available():
        return ReportResult(submitted=False, error=True, message="'gh' (GitHub CLI) não encontrado no PATH. Instale: https://cli.github.com/")

    try:
        auth = _run(["gh", "auth", "status"], timeout=15)
    except (OSError, subprocess.TimeoutExpired):
        return ReportResult(submitted=False, error=True, message="Não foi possível checar 'gh auth status' (timeout/indisponível).")
    if auth.returncode != 0:
        return ReportResult(submitted=False, error=True, message="Não autenticado no GitHub CLI. Rode 'gh auth login' antes de usar 'agloop report'.")

    env = detect_environment(repo_root)
    body = render_issue_body(title, description, severity, env)

    if not force:
        dup = find_duplicate(title, repo)
        if dup:
            return ReportResult(
                submitted=False,
                duplicate_url=dup,
                rendered_body=body,
                message=f"Issue parecido já existe: {dup} (use --force para abrir mesmo assim).",
            )

    if not yes:
        if confirm is None:
            return ReportResult(
                submitted=False,
                rendered_body=body,
                message="Rascunho pronto. Revise e confirme com -y/--yes para publicar (nunca submete sem confirmação explícita).",
            )
        if not confirm(body):
            return ReportResult(submitted=False, rendered_body=body, message="Cancelado — issue não publicado.")

    try:
        url = submit_report(title, body, env.source_slug, repo)
    except RuntimeError as exc:
        return ReportResult(submitted=False, error=True, rendered_body=body, message=str(exc))

    return ReportResult(submitted=True, url=url, rendered_body=body, message=f"Issue criado: {url}")
