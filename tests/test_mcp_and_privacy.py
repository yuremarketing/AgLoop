import json
import os

import pytest

from conftest import ROOM, _git, append


@pytest.fixture
def in_repo(local_repo, monkeypatch):
    monkeypatch.chdir(local_repo)
    return local_repo


# --------------------------------------------------------------------------- #
# core/mcp_server.py — tool functions
# --------------------------------------------------------------------------- #
def test_read_war_room_returns_recent_sanitized(in_repo):
    from core.mcp_server import read_war_room

    append(in_repo, "Alice", "contact me at leak@external.com")
    _git(in_repo, "commit", "-qam", "alice spoke")

    out = read_war_room(max_turns=6)
    assert "## Alice" in out
    assert "leak@external.com" not in out
    assert "[EMAIL_REDACTED]" in out


def test_read_war_room_blocks_file_outside_allowlist(in_repo):
    from core.mcp_server import read_war_room

    with pytest.raises(ValueError):
        read_war_room(filepath="docs/gestao/backlog-produto.md")


def test_read_war_room_discards_traversal_prefix(in_repo):
    """A directory prefix is ignored entirely; only the basename is ever used (LGPD-03)."""
    from core.mcp_server import read_war_room

    out = read_war_room(filepath="../../etc/war_room.md")
    assert "AgLoop War Room" in out


def test_post_war_room_message_appends_commits_and_isolates_author(in_repo):
    from core.mcp_server import post_war_room_message

    result = post_war_room_message(agent_name="Claude", message="hello from MCP")
    assert result["pushed"] is True
    assert result["status"] == "ok"
    assert "## Claude" in (in_repo / ROOM).read_text()
    assert "hello from MCP" in (in_repo / ROOM).read_text()
    assert "Claude" in _git(in_repo, "log", "-1", "--format=%an")
    assert "@agloop.local" in _git(in_repo, "log", "-1", "--format=%ae")


def test_post_war_room_message_without_push_skips_git(in_repo):
    from core.mcp_server import post_war_room_message

    result = post_war_room_message(agent_name="Claude", message="dry run", push=False)
    assert result == {"pushed": False, "status": "ok"}
    assert "dry run" in (in_repo / ROOM).read_text()
    assert _git(in_repo, "status", "--porcelain").strip() != ""  # left uncommitted on purpose


def test_post_war_room_message_has_no_filepath_parameter(in_repo):
    """The tool is fixed to war_room.md by design — no caller-supplied path, even internally."""
    from core.mcp_server import post_war_room_message

    with pytest.raises(TypeError):
        post_war_room_message(agent_name="Claude", message="x", filepath="docs/gestao/backlog-produto.md")


def test_get_lock_status_reports_state(in_repo):
    from core.mcp_server import get_lock_status

    append(in_repo, "Gemini", "waiting for Claude")
    _git(in_repo, "commit", "-qam", "gemini spoke")

    status = get_lock_status()
    assert status["locked"] is False
    assert status["last_speaker"] == "Gemini"
    assert status["state"] == "ACTIVE"
    assert status["paths"]


def test_get_lock_status_blocks_sensitive_or_outside_allowlist(in_repo):
    from core.mcp_server import get_lock_status

    with pytest.raises(ValueError):
        get_lock_status(filepath=".env")


# --------------------------------------------------------------------------- #
# core/mcp_server.py — JSON-RPC 2.0 dispatch
# --------------------------------------------------------------------------- #
def test_initialize_and_tools_list(in_repo):
    from core.mcp_server import _dispatch

    init = _dispatch("initialize", {})
    assert init["serverInfo"]["name"] == "agloop"

    listed = _dispatch("tools/list", {})
    names = {t["name"] for t in listed["tools"]}
    assert names == {"read_war_room", "post_war_room_message", "get_lock_status", "scan_repository"}


def test_handle_line_tools_call_round_trip(in_repo):
    from core.mcp_server import _handle_line

    request = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/call",
        "params": {"name": "get_lock_status", "arguments": {}},
    }
    response = _handle_line(json.dumps(request))
    assert response["id"] == 1
    assert response["result"]["isError"] is False
    payload = json.loads(response["result"]["content"][0]["text"])
    assert payload["state"] == "ACTIVE"


def test_handle_line_notification_returns_no_response(in_repo):
    from core.mcp_server import _handle_line

    request = {"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}}
    assert _handle_line(json.dumps(request)) is None


def test_handle_line_unknown_method_returns_json_rpc_error(in_repo):
    from core.mcp_server import _handle_line

    request = {"jsonrpc": "2.0", "id": 7, "method": "not/a/method", "params": {}}
    response = _handle_line(json.dumps(request))
    assert response["id"] == 7
    assert response["error"]["code"] == -32602


def test_handle_line_blocked_tool_call_surfaces_as_json_rpc_error(in_repo):
    from core.mcp_server import _handle_line

    request = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {"name": "read_war_room", "arguments": {"filepath": ".env"}},
    }
    response = _handle_line(json.dumps(request))
    assert "error" in response
    assert "Access denied" in response["error"]["message"]


# --------------------------------------------------------------------------- #
# core/privacy_audit.py (LGPD-04)
# --------------------------------------------------------------------------- #
def test_run_privacy_audit_flags_missing_gitignore_env(in_repo):
    from core.privacy_audit import run_privacy_audit

    report = run_privacy_audit(repo_root=str(in_repo))
    assert "FALTANDO" in report


def test_run_privacy_audit_detects_gitignored_env(in_repo):
    from core.privacy_audit import run_privacy_audit

    (in_repo / ".gitignore").write_text(".env\n")
    report = run_privacy_audit(repo_root=str(in_repo))
    assert "[.gitignore] .env protegido: OK" in report


def test_run_privacy_audit_lists_isolated_author_emails(in_repo):
    from core.privacy_audit import run_privacy_audit

    append(in_repo, "Alice")
    import subprocess

    env = dict(os.environ, GIT_AUTHOR_NAME="Alice", GIT_AUTHOR_EMAIL="alice@agloop.local")
    subprocess.run(["git", "commit", "-qam", "alice"], cwd=in_repo, env=env, check=True)

    report = run_privacy_audit(repo_root=str(in_repo))
    assert "alice@agloop.local" in report
    assert "isolado (agente)" in report


def test_run_privacy_audit_flags_residual_pii_in_war_room(in_repo):
    from core.privacy_audit import run_privacy_audit

    append(in_repo, "Bob", "CPF 123.456.789-00 and email leak@external.com")
    _git(in_repo, "commit", "-qam", "bob leaked pii")

    report = run_privacy_audit(repo_root=str(in_repo))
    assert "CPF" in report
    assert "EXTERNAL_EMAIL:leak@external.com" in report


# --------------------------------------------------------------------------- #
# main.py — subcommand parsing stays backward compatible
# --------------------------------------------------------------------------- #
def test_parse_cli_args_backward_compatible_bare_name_flag():
    from main import parse_cli_args

    args = parse_cli_args(["--name", "Alice"])
    assert args.command == "run"
    assert args.name == "Alice"


def test_parse_cli_args_explicit_run_subcommand():
    from main import parse_cli_args

    args = parse_cli_args(["run", "--name", "Bob", "--sleep", "5"])
    assert args.command == "run"
    assert args.name == "Bob"
    assert args.sleep == 5


def test_parse_cli_args_audit_privacy():
    from main import parse_cli_args

    args = parse_cli_args(["audit", "--privacy"])
    assert args.command == "audit"
    assert args.privacy is True


def test_parse_cli_args_init():
    from main import parse_cli_args

    args = parse_cli_args(["init"])
    assert args.command == "init"


# --------------------------------------------------------------------------- #
# core/init_scaffold.py — `agloop init` (E07.2)
# --------------------------------------------------------------------------- #
def test_run_init_creates_war_room_and_governance_templates(tmp_path):
    from core.init_scaffold import run_init

    report = run_init(repo_root=str(tmp_path))

    assert (tmp_path / "war_room.md").is_file()
    assert (tmp_path / "HISTORICO.md").is_file()
    assert (tmp_path / "docs" / "gestao" / "roadmap.md").is_file()
    assert (tmp_path / "docs" / "gestao" / "backlog-produto.md").is_file()
    assert (tmp_path / "docs" / "gestao" / "matriz-riscos.md").is_file()
    assert (tmp_path / "docs" / "arquitetura" / "decisoes").is_dir()
    assert (tmp_path / ".claude" / "skills" / "vigilia" / "SKILL.md").is_file()
    assert "war_room.md" in report
    assert "[criado]" in report


def test_run_init_never_overwrites_existing_files(tmp_path):
    from core.init_scaffold import run_init

    (tmp_path / "war_room.md").write_text("conteudo do usuario, nao mexer", encoding="utf-8")
    skill_dir = tmp_path / ".claude" / "skills" / "vigilia"
    skill_dir.mkdir(parents=True)
    (skill_dir / "SKILL.md").write_text("conteudo do usuario, nao mexer", encoding="utf-8")

    report = run_init(repo_root=str(tmp_path))

    assert (tmp_path / "war_room.md").read_text(encoding="utf-8") == "conteudo do usuario, nao mexer"
    assert (skill_dir / "SKILL.md").read_text(encoding="utf-8") == "conteudo do usuario, nao mexer"
    assert "ja existia, preservado" in report
    assert "war_room.md" in report


def test_init_skill_template_has_no_agloop_internal_references():
    template_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "core", "templates", "skills", "vigilia", "SKILL.md",
    )
    content = open(template_path, encoding="utf-8").read().lower()

    for forbidden in ("yure mark", "sysoft"):
        assert forbidden not in content, f"template genérico nao deve citar '{forbidden}'"
