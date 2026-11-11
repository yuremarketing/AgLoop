"""
Testes unitários e de integração para o Gate de Prontidão (Issue #42, Fase B).
"""

import os
from pathlib import Path

import pytest

from core.init_scaffold import run_init
from core.readiness_gate import (
    ReadinessReport,
    check_readiness,
    format_report_text,
)
from main import parse_cli_args


def test_check_readiness_passes_on_agloop_repo():
    """O próprio repositório AgLoop deve ter Gate 🟢 (todas as obrigações atendidas)."""
    repo_root = Path(__file__).parent.parent
    report = check_readiness(str(repo_root))
    assert report.passed is True
    assert len(report.blocking_issues) == 0


def test_check_readiness_fails_on_freshly_initialized_repo(tmp_path):
    """
    Um repositório recém-inicializado pelo `agloop init` deve ter Gate 🔴
    porque os templates gerados contêm marcadores AGLOOP_TODO e não há termo de abertura.
    """
    run_init(repo_root=str(tmp_path), quiet=True)

    report = check_readiness(str(tmp_path))
    assert report.passed is False
    assert len(report.blocking_issues) > 0

    blocking_ids = [item.id for item in report.blocking_issues]
    # termo de abertura não é gerado pelo init, deve estar bloqueado
    assert "charter" in blocking_ids
    # backlog, riscos e roster gerados pelo init têm marcadores AGLOOP_TODO
    assert "backlog" in blocking_ids or "risks" in blocking_ids or "roster" in blocking_ids


def test_check_readiness_passes_when_all_requirements_met(tmp_path):
    """Garante Gate 🟢 quando todos os arquivos 🔒 estão presentes e sem AGLOOP_TODO."""
    # 1. war_room.md
    (tmp_path / "war_room.md").write_text("# Sala de Guerra\nAtiva.\n", encoding="utf-8")

    # 2. AGENTS.md
    (tmp_path / "AGENTS.md").write_text("# Instruções\nProtocolo ativo.\n", encoding="utf-8")

    # 3. docs/gestao/
    gestao = tmp_path / "docs" / "gestao"
    gestao.mkdir(parents=True, exist_ok=True)

    (gestao / "termo-abertura.md").write_text("# Termo de Abertura\nProblema e metas definidos.\n", encoding="utf-8")
    (gestao / "backlog-produto.md").write_text("# Backlog\n- E01: Primeira feature.\n", encoding="utf-8")
    (gestao / "matriz-riscos.md").write_text("# Riscos\n- R01: Risco mitigado.\n", encoding="utf-8")
    (gestao / "roster-agentes.md").write_text("# Roster\n| Agente | Ferramenta |\n| Alice | Git |\n", encoding="utf-8")

    report = check_readiness(str(tmp_path))
    assert report.passed is True
    assert len(report.blocking_issues) == 0


def test_format_report_text_quiet_mode():
    """Garante saída sintética de 1 linha no modo quiet."""
    report_pass = ReadinessReport(items=[])
    assert "🟢" in format_report_text(report_pass, quiet=True)

    from core.readiness_gate import ReadinessItem

    item_fail = ReadinessItem("test", "Item Falho", "desc", required=True, passed=False)
    report_fail = ReadinessReport(items=[item_fail])
    assert "🔴" in format_report_text(report_fail, quiet=True)


def test_format_report_text_no_color(monkeypatch):
    """Garante que NO_COLOR desativa sequências ANSI."""
    monkeypatch.setenv("NO_COLOR", "1")
    report = ReadinessReport(items=[])
    output = format_report_text(report, quiet=False)
    assert "\033[" not in output


def test_parse_cli_args_check_subcommand():
    """Garante suporte ao subcomando check na CLI."""
    args = parse_cli_args(["check"])
    assert args.command == "check"
    assert args.quiet is False
    assert args.repo_root == "."

    args_q = parse_cli_args(["check", "-q", "--repo-root", "/tmp/teste"])
    assert args_q.command == "check"
    assert args_q.quiet is True
    assert args_q.repo_root == "/tmp/teste"


def test_parse_cli_args_run_force_bypass_flag():
    """Garante suporte à flag --force-bypass-gate no subcomando run."""
    args = parse_cli_args(["run", "--name", "Alice", "--force-bypass-gate"])
    assert args.command == "run"
    assert args.force_bypass_gate is True


def test_main_check_exits_cleanly_on_green_repo(monkeypatch):
    """Garante que main() sai com código 0 em repositório verde."""
    import main as main_mod

    monkeypatch.setattr(main_mod, "parse_cli_args", lambda: parse_cli_args(["check"]))
    # Não deve levantar SystemExit(1)
    main_mod.main()


def test_main_check_exits_with_1_on_red_repo(monkeypatch, tmp_path):
    """Garante que main() sai com SystemExit(1) em repositório vermelho."""
    import main as main_mod

    monkeypatch.setattr(
        main_mod,
        "parse_cli_args",
        lambda: parse_cli_args(["check", "--repo-root", str(tmp_path)]),
    )

    with pytest.raises(SystemExit) as exc:
        main_mod.main()
    assert exc.value.code == 1


def test_main_run_blocks_when_gate_is_red(monkeypatch, tmp_path):
    """Garante que `agloop run` recusa execução com SystemExit(1) quando o gate for 🔴."""
    import main as main_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        main_mod,
        "parse_cli_args",
        lambda: parse_cli_args(["run", "--name", "Alice"]),
    )

    with pytest.raises(SystemExit) as exc:
        main_mod.main()
    assert exc.value.code == 1


def test_main_run_allows_bypass_with_flag(monkeypatch, tmp_path):
    """Garante que `agloop run --force-bypass-gate` não bloqueia no gate."""
    import main as main_mod

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(
        main_mod,
        "parse_cli_args",
        lambda: parse_cli_args(["run", "--name", "Alice", "--force-bypass-gate"]),
    )
    # Mock run_agent_loop para não entrar em loop infinito
    executed = []
    monkeypatch.setattr(main_mod, "run_agent_loop", lambda **kw: executed.append(True))

    main_mod.main()
    assert executed == [True]


def test_protocol_version_item_in_readiness_gate(tmp_path):
    """Garante que o item 9 (protocol_version) é inspecionado no Gate."""
    run_init(repo_root=str(tmp_path), quiet=True)
    report = check_readiness(str(tmp_path))
    proto_item = next((item for item in report.items if item.id == "protocol_version"), None)
    assert proto_item is not None
    assert proto_item.required is False
    assert proto_item.passed is True

