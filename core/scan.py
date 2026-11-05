"""
AgLoop Repository Scan (E07.3).

`agloop scan` / MCP tool `scan_repository`: read-only inspection of a
repository — directory structure (bounded depth, defensive caps) and known
stack manifests — reusing the same confinement/PII primitives already
enforced for `read_file`/`list_dir` in `core.agent`. Never triggered
automatically (see the informational-only `SessionStart` hook); always an
explicit, user-initiated action.
"""

import os
import subprocess
from typing import List, Optional

from core.agent import _is_sensitive_path, _is_within_workspace, sanitize_prompt_pii

MAX_DEPTH = 3
MAX_LISTED_ITEMS = 30
GITIGNORE_CHECK_TIMEOUT = 3

_DEFAULT_IGNORED_DIRS = {
    "node_modules", ".venv", "venv", "__pycache__", ".git", ".agloop.lock",
    "target", "dist", "build", ".pytest_cache",
}

_STACK_MANIFESTS = (
    "pyproject.toml", "requirements.txt", "package.json", "Cargo.toml",
    "go.mod", "pom.xml", "Dockerfile",
)


def _is_gitignored(repo_root: str, rel_path: str) -> bool:
    """`git check-ignore` with a short timeout; defensively returns False if not a git repo or on any error."""
    try:
        result = subprocess.run(
            ["git", "check-ignore", "-q", rel_path],
            cwd=repo_root,
            capture_output=True,
            timeout=GITIGNORE_CHECK_TIMEOUT,
            check=False,
        )
    except Exception:
        return False
    return result.returncode == 0


def _detect_stack(root: str) -> List[str]:
    return [name for name in _STACK_MANIFESTS if os.path.isfile(os.path.join(root, name))]


def _walk(root: str, current: str, depth: int, lines: List[str], counter: List[int]) -> None:
    if depth > MAX_DEPTH or counter[0] >= MAX_LISTED_ITEMS:
        return
    try:
        entries = sorted(os.listdir(current))
    except OSError:
        return

    for entry in entries:
        if counter[0] >= MAX_LISTED_ITEMS:
            lines.append("  " * depth + "... e mais itens (limite do relatório atingido)")
            return

        full = os.path.join(current, entry)
        rel = os.path.relpath(full, root).replace("\\", "/")

        if entry in _DEFAULT_IGNORED_DIRS:
            continue
        if not _is_within_workspace(root, full) or _is_sensitive_path(root, full):
            continue
        if _is_gitignored(root, rel):
            continue

        is_dir = os.path.isdir(full)
        lines.append("  " * depth + entry + ("/" if is_dir else ""))
        counter[0] += 1

        if is_dir:
            _walk(root, full, depth + 1, lines, counter)


def run_scan(repo_root: str = ".") -> str:
    """Builds a read-only structure + stack report as plain text."""
    root = os.path.realpath(repo_root)
    lines = ["AgLoop - Relatorio de Varredura do Repositorio", "=" * 48, ""]

    stack = _detect_stack(root)
    lines.append(f"[stack detectada] {len(stack)} manifesto(s):")
    if stack:
        for name in stack:
            lines.append(f"  - {name}")
    else:
        lines.append("  Nenhum manifesto de stack conhecido encontrado na raiz.")

    has_war_room = os.path.isfile(os.path.join(root, "war_room.md"))
    has_gestao = os.path.isdir(os.path.join(root, "docs", "gestao"))
    lines.append(f"\n[governanca AgLoop] war_room.md: {'OK' if has_war_room else 'AUSENTE'}")
    lines.append(f"[governanca AgLoop] docs/gestao/: {'OK' if has_gestao else 'AUSENTE'}")
    if not has_war_room:
        lines.append("  Dica: execute 'agloop init' para criar a governanca.")

    lines.append(f"\n[estrutura de diretorios] profundidade maxima {MAX_DEPTH}, até {MAX_LISTED_ITEMS} itens:")
    tree_lines: List[str] = []
    _walk(root, root, 0, tree_lines, [0])
    lines.extend(tree_lines if tree_lines else ["  (vazio)"])

    return sanitize_prompt_pii("\n".join(lines))
