"""
AgLoop Privacy Audit (LGPD-04).

Local-only diagnostic (`agloop audit --privacy`): checks `.gitignore` coverage
for `.env`, lists git author e-mails (flagging which are isolated `@agloop.local`
agent identities), and scans the War Room files for residual unmasked PII —
reusing the same regexes `sanitize_prompt_pii` already uses in `core.agent`.
"""

import os
import subprocess
from typing import Dict, List

from core.agent import _CPF_RE, _EMAIL_RE, _SECRET_TOKEN_RE

ROOM_FILES = ("war_room.md", "HISTORICO.md")


def _gitignore_protects(repo_root: str, pattern: str) -> bool:
    gitignore = os.path.join(repo_root, ".gitignore")
    if not os.path.isfile(gitignore):
        return False
    with open(gitignore, "r", encoding="utf-8") as f:
        lines = [line.strip() for line in f if line.strip() and not line.strip().startswith("#")]
    return any(pattern in line for line in lines)


def _git_author_emails(repo_root: str) -> List[str]:
    try:
        res = subprocess.run(
            ["git", "log", "--all", "--format=%ae"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception:
        return []
    return sorted({e.strip() for e in res.stdout.splitlines() if e.strip()})


def _scan_pii(repo_root: str) -> Dict[str, List[str]]:
    findings: Dict[str, List[str]] = {}
    for name in ROOM_FILES:
        path = os.path.join(repo_root, name)
        if not os.path.isfile(path):
            continue
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            text = f.read()

        hits: List[str] = []
        if _CPF_RE.search(text):
            hits.append("CPF")
        if _SECRET_TOKEN_RE.search(text):
            hits.append("API_SECRET")
        for m in _EMAIL_RE.finditer(text):
            if m.group(1).lower() != "agloop.local":
                hits.append(f"EXTERNAL_EMAIL:{m.group(0)}")
        if hits:
            findings[name] = hits
    return findings


def run_privacy_audit(repo_root: str = ".") -> str:
    """Builds the LGPD-04 privacy diagnostic report as plain text."""
    root = os.path.realpath(repo_root)
    lines = ["AgLoop - Relatorio de Auditoria de Privacidade (LGPD-04)", "=" * 56, ""]

    env_protected = _gitignore_protects(root, ".env")
    lines.append(f"[.gitignore] .env protegido: {'OK' if env_protected else 'FALTANDO'}")

    emails = _git_author_emails(root)
    lines.append(f"\n[git log] e-mails de autoria encontrados ({len(emails)}):")
    for email in emails:
        tag = "isolado (agente)" if email.endswith("@agloop.local") else "ATENCAO: nao isolado"
        lines.append(f"  - {email} [{tag}]")

    findings = _scan_pii(root)
    lines.append(f"\n[PII residual] arquivos verificados: {', '.join(ROOM_FILES)}")
    if findings:
        for name, hits in findings.items():
            lines.append(f"  - {name}: {len(hits)} ocorrencia(s) -> {hits}")
    else:
        lines.append("  Nenhuma ocorrencia de CPF, chave de API ou e-mail externo nao mascarado encontrada.")

    return "\n".join(lines)
