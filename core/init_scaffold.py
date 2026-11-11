"""
AgLoop Init Scaffold (E07.2).

`agloop init`: copies the War Room + governance templates bundled under
`core/templates/` into the user's repository, without ever overwriting a
file that already exists at the destination.
"""

import os
import shutil
from typing import List, Tuple

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")

# (template path relative to _TEMPLATES_DIR, destination path relative to repo_root)
_FILES: Tuple[Tuple[str, str], ...] = (
    ("war_room.md", "war_room.md"),
    ("HISTORICO.md", "HISTORICO.md"),
    ("gestao/roadmap.md", "docs/gestao/roadmap.md"),
    ("gestao/backlog-produto.md", "docs/gestao/backlog-produto.md"),
    ("gestao/matriz-riscos.md", "docs/gestao/matriz-riscos.md"),
    ("skills/vigilia/SKILL.md", ".claude/skills/vigilia/SKILL.md"),
)

_EMPTY_DIRS: Tuple[str, ...] = ("docs/arquitetura/decisoes",)


def run_init(repo_root: str = ".") -> str:
    """Scaffolds War Room governance files into `repo_root`. Returns a plain-text report."""
    root = os.path.realpath(repo_root)
    created: List[str] = []
    skipped: List[str] = []

    for template_rel, dest_rel in _FILES:
        dest_path = os.path.join(root, dest_rel)
        if os.path.exists(dest_path):
            skipped.append(dest_rel)
            continue
        os.makedirs(os.path.dirname(dest_path), exist_ok=True)
        shutil.copyfile(os.path.join(_TEMPLATES_DIR, template_rel), dest_path)
        created.append(dest_rel)

    for dir_rel in _EMPTY_DIRS:
        dir_path = os.path.join(root, dir_rel)
        if os.path.isdir(dir_path):
            skipped.append(f"{dir_rel}/")
        else:
            os.makedirs(dir_path, exist_ok=True)
            created.append(f"{dir_rel}/")

    lines = ["AgLoop - Inicializacao da Sala de Guerra", "=" * 42, ""]
    lines.append(f"[criado] {len(created)} item(ns):")
    for item in created:
        lines.append(f"  - {item}")
    if skipped:
        lines.append(f"\n[ja existia, preservado] {len(skipped)} item(ns):")
        for item in skipped:
            lines.append(f"  - {item}")

    return "\n".join(lines)
