"""
AgLoop Init Scaffold (E07.2).

`agloop init`: copies the War Room + governance templates bundled under
`core/templates/` into the user's repository, without ever overwriting a
file that already exists at the destination.
"""

import os
from pathlib import Path
import shutil
from typing import List, Tuple

_TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "templates")


def get_templates_dir() -> Path:
    """Retorna o caminho Path para o diretório de templates empacotados."""
    return Path(_TEMPLATES_DIR)

# (template path relative to _TEMPLATES_DIR, destination path relative to repo_root)
_FILES: Tuple[Tuple[str, str], ...] = (
    ("war_room.md", "war_room.md"),
    ("HISTORICO.md", "HISTORICO.md"),
    ("gestao/roadmap.md", "docs/gestao/roadmap.md"),
    ("gestao/backlog-produto.md", "docs/gestao/backlog-produto.md"),
    ("gestao/matriz-riscos.md", "docs/gestao/matriz-riscos.md"),
    ("gestao/roster-agentes.md", "docs/gestao/roster-agentes.md"),
    ("skills/vigilia/SKILL.md", ".claude/skills/vigilia/SKILL.md"),
    ("AGENTS.md", "AGENTS.md"),
    ("CLAUDE.md", "CLAUDE.md"),
    ("GEMINI.md", "GEMINI.md"),
)

_EMPTY_DIRS: Tuple[str, ...] = ("docs/arquitetura/decisoes",)


def run_init(repo_root: str = ".", quiet: bool = False) -> str:
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

    if not quiet:
        if created:
            lines.extend([
                "",
                "AgLoop: Sala de Guerra criada.",
                "",
                "Proximos passos:",
                '  1. git add war_room.md HISTORICO.md docs/ .claude/ AGENTS.md CLAUDE.md GEMINI.md'
                ' && git commit -m "chore: inicializa AgLoop" && git push',
                "  2. Claude Code: /plugin marketplace add yuremarketing/AgLoop#stable && /plugin install agloop@agloop",
                "     Gemini CLI:  gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable",
                "  3. Ajuste .claude/skills/vigilia/SKILL.md (nome do PO e limites de codigo de producao).",
                '  4. Diga ao seu agente: "instalei o AgLoop". Ele conduz o onboarding.',
                "",
                "Manual de Uso: https://github.com/yuremarketing/AgLoop/blob/main/docs/manual/manual-de-uso.md",
            ])
        else:
            lines.extend([
                "",
                "AgLoop: Todos os arquivos da Sala de Guerra ja existem neste repositorio.",
                "Consulte o Manual de Uso: https://github.com/yuremarketing/AgLoop/blob/main/docs/manual/manual-de-uso.md",
            ])

    return "\n".join(lines)
