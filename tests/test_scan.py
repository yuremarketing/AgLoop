import json
import os

import pytest

from conftest import _git


# --------------------------------------------------------------------------- #
# core/scan.py — run_scan
# --------------------------------------------------------------------------- #
def test_run_scan_detects_known_stack_manifest(tmp_path):
    from core.scan import run_scan

    (tmp_path / "pyproject.toml").write_text("[project]\nname='x'\n")

    report = run_scan(repo_root=str(tmp_path))
    assert "pyproject.toml" in report
    assert "[stack detectada]" in report


def test_run_scan_reports_absence_of_governance(tmp_path):
    from core.scan import run_scan

    report = run_scan(repo_root=str(tmp_path))
    assert "war_room.md: AUSENTE" in report
    assert "agloop init" in report


def test_run_scan_reports_presence_of_governance(tmp_path):
    from core.scan import run_scan

    (tmp_path / "war_room.md").write_text("# AgLoop War Room\n")
    (tmp_path / "docs" / "gestao").mkdir(parents=True)

    report = run_scan(repo_root=str(tmp_path))
    assert "war_room.md: OK" in report
    assert "docs/gestao/: OK" in report


def test_run_scan_excludes_sensitive_files_from_tree(tmp_path):
    from core.scan import run_scan

    (tmp_path / ".env").write_text("SECRET=1\n")
    (tmp_path / "README.md").write_text("hello\n")

    report = run_scan(repo_root=str(tmp_path))
    assert ".env" not in report
    assert "README.md" in report


def test_run_scan_respects_gitignore(local_repo):
    from core.scan import run_scan

    (local_repo / ".gitignore").write_text("ignored_dir/\n")
    (local_repo / "ignored_dir").mkdir()
    (local_repo / "ignored_dir" / "secret_stuff.txt").write_text("x\n")
    (local_repo / "visible.txt").write_text("x\n")
    _git(local_repo, "add", "-A")
    _git(local_repo, "commit", "-m", "add gitignore")

    report = run_scan(repo_root=str(local_repo))
    assert "ignored_dir" not in report
    assert "visible.txt" in report


def test_run_scan_caps_listed_items(tmp_path):
    from core.scan import MAX_LISTED_ITEMS, run_scan

    for i in range(MAX_LISTED_ITEMS + 10):
        (tmp_path / f"file_{i:03d}.txt").write_text("x\n")

    report = run_scan(repo_root=str(tmp_path))
    assert "... e mais itens" in report


def test_run_scan_skips_default_heavy_directories(tmp_path):
    from core.scan import run_scan

    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "pkg.js").write_text("x\n")

    report = run_scan(repo_root=str(tmp_path))
    assert "pkg.js" not in report


# --------------------------------------------------------------------------- #
# core/mcp_server.py — scan_repository tool
# --------------------------------------------------------------------------- #
@pytest.fixture
def in_repo(local_repo, monkeypatch):
    monkeypatch.chdir(local_repo)
    return local_repo


def test_scan_repository_tool_via_mcp(in_repo):
    from core.mcp_server import scan_repository

    (in_repo / "pyproject.toml").write_text("[project]\nname='x'\n")
    out = scan_repository()
    assert "pyproject.toml" in out


def test_tools_list_includes_scan_repository(in_repo):
    from core.mcp_server import _dispatch

    listed = _dispatch("tools/list", {})
    names = {t["name"] for t in listed["tools"]}
    assert "scan_repository" in names


def test_handle_line_scan_repository_round_trip(in_repo):
    from core.mcp_server import _handle_line

    request = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "tools/call",
        "params": {"name": "scan_repository", "arguments": {}},
    }
    response = _handle_line(json.dumps(request))
    assert response["id"] == 3
    assert response["result"]["isError"] is False
    assert "AgLoop" in response["result"]["content"][0]["text"]


# --------------------------------------------------------------------------- #
# main.py — `agloop scan` subcommand
# --------------------------------------------------------------------------- #
def test_parse_cli_args_scan():
    from main import parse_cli_args

    args = parse_cli_args(["scan"])
    assert args.command == "scan"
