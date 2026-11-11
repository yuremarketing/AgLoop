"""
Testes unitários para o módulo core/update_scaffold.py e comando agloop update (Issue #54).
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from core.init_scaffold import get_templates_dir, run_init
from core.update_scaffold import (
    ProtocolFileStatus,
    UpdateReport,
    check_protocol_update_status,
    extract_protocol_version,
    format_update_summary,
    run_update,
)
from main import parse_cli_args


def test_extract_protocol_version():
    content = """---
name: vigilia
metadata:
  version: "1.4.0"
---
# Protocolo
"""
    assert extract_protocol_version(content) == "1.4.0"

    content_unquoted = """---
name: vigilia
metadata:
  version: 1.2.0
---
"""
    assert extract_protocol_version(content_unquoted) == "1.2.0"

    assert extract_protocol_version("sem frontmatter") is None


def test_check_protocol_update_status_detects_outdated(tmp_path):
    # Inicializa um repositório limpo no tmp_path
    run_init(repo_root=str(tmp_path), quiet=True)

    # Força versão antiga no SKILL.md local
    skill_path = tmp_path / ".claude" / "skills" / "vigilia" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    downgraded = content.replace('version: "1.4.0"', 'version: "1.0.0"')
    skill_path.write_text(downgraded, encoding="utf-8")

    statuses = check_protocol_update_status(repo_root=str(tmp_path))
    skill_status = next(s for s in statuses if s.rel_path == ".claude/skills/vigilia/SKILL.md")

    assert skill_status.needs_update is True
    assert skill_status.local_version == "1.0.0"
    assert skill_status.template_version == "1.4.0"
    assert len(skill_status.diff) > 0


def test_run_update_dry_run_leaves_files_untouched(tmp_path):
    run_init(repo_root=str(tmp_path), quiet=True)

    skill_path = tmp_path / ".claude" / "skills" / "vigilia" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    downgraded = content.replace('version: "1.4.0"', 'version: "1.0.0"')
    skill_path.write_text(downgraded, encoding="utf-8")

    report = run_update(repo_root=str(tmp_path), dry_run=True, yes=True)

    # Nenhuma alteração aplicada
    assert len(report.applied_files) == 0
    assert len(report.backup_files) == 0
    # O arquivo local deve continuar com a versão 1.0.0
    assert extract_protocol_version(skill_path.read_text(encoding="utf-8")) == "1.0.0"
    assert not skill_path.with_name("SKILL.md.bak").exists()


def test_run_update_applies_changes_and_creates_backup(tmp_path):
    run_init(repo_root=str(tmp_path), quiet=True)

    skill_path = tmp_path / ".claude" / "skills" / "vigilia" / "SKILL.md"
    content = skill_path.read_text(encoding="utf-8")
    downgraded = content.replace('version: "1.4.0"', 'version: "1.0.0"')
    skill_path.write_text(downgraded, encoding="utf-8")

    report = run_update(repo_root=str(tmp_path), dry_run=False, yes=True)

    assert ".claude/skills/vigilia/SKILL.md" in report.applied_files
    backup_file = skill_path.with_name("SKILL.md.bak")
    assert backup_file.is_file()
    assert extract_protocol_version(backup_file.read_text(encoding="utf-8")) == "1.0.0"
    assert extract_protocol_version(skill_path.read_text(encoding="utf-8")) == "1.4.0"


def test_run_update_preserves_existing_roster_governance(tmp_path):
    run_init(repo_root=str(tmp_path), quiet=True)

    roster_path = tmp_path / "docs" / "gestao" / "roster-agentes.md"
    custom_roster_content = "# Roster Customizado do Projeto X\n- Agente Especial: Alpha"
    roster_path.write_text(custom_roster_content, encoding="utf-8")

    report = run_update(repo_root=str(tmp_path), dry_run=False, yes=True)

    # Roster existente nunca pode ser sobrescrito nem modificado
    assert "docs/gestao/roster-agentes.md" not in report.applied_files
    assert roster_path.read_text(encoding="utf-8") == custom_roster_content


def test_format_update_summary_up_to_date():
    report = UpdateReport(statuses=[])
    text = format_update_summary(report)
    assert "100% atualizado" in text
    assert "Nenhuma alteração necessária" in text


def test_format_update_summary_with_changes():
    status = ProtocolFileStatus(
        rel_path=".claude/skills/vigilia/SKILL.md",
        target_path=Path("target"),
        template_path=Path("tmpl"),
        exists_locally=True,
        is_identical=False,
        local_version="1.0.0",
        template_version="1.4.0",
        diff="--- diff ---",
    )
    report = UpdateReport(
        statuses=[status],
        applied_files=[status.rel_path],
        backup_files=["target.bak"],
    )
    text = format_update_summary(report, dry_run=False)
    assert "[DEFASADO]" in text
    assert "Atualizado: .claude/skills/vigilia/SKILL.md" in text
    assert "backup criado" in text


def test_cli_parse_update_args():
    args = parse_cli_args(["update", "--yes", "--dry-run", "--repo-root", "/tmp/test"])
    assert args.command == "update"
    assert args.yes is True
    assert args.dry_run is True
    assert args.repo_root == "/tmp/test"
