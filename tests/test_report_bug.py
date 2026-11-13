"""
Issue #61: `agloop report`. Toda chamada a `gh`/`git` é mockada via
`core.report_bug._run` — a suíte nunca pode disparar uma chamada real pro
GitHub a partir do CI.
"""

import subprocess

import pytest

from core.report_bug import (
    EnvironmentInfo,
    ReportResult,
    _sanitize_slug,
    detect_environment,
    find_duplicate,
    render_issue_body,
    run_report,
    submit_report,
)


def _completed(returncode=0, stdout="", stderr=""):
    return subprocess.CompletedProcess(args=[], returncode=returncode, stdout=stdout, stderr=stderr)


# --------------------------------------------------------------------------- #
# _sanitize_slug
# --------------------------------------------------------------------------- #
@pytest.mark.parametrize(
    "origin_url,expected",
    [
        ("https://github.com/yuremarketing/AgLoop.git", "github-com-yuremarketing-AgLoop"),
        ("git@github.com:yuremarketing/my-repo.git", "github-com-yuremarketing-my-repo"),
        ("", "local-project"),
    ],
)
def test_sanitize_slug(origin_url, expected):
    assert _sanitize_slug(origin_url) == expected


# --------------------------------------------------------------------------- #
# detect_environment
# --------------------------------------------------------------------------- #
def test_detect_environment_uses_git_remote(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(stdout="https://github.com/acme/widgets.git\n"))
    monkeypatch.setattr(report_bug, "_in_docker", lambda: False)

    env = detect_environment(repo_root=".")
    assert env.origin_url == "https://github.com/acme/widgets.git"
    assert env.source_slug == "github-com-acme-widgets"
    assert env.in_docker is False


def test_detect_environment_falls_back_without_git(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(returncode=1))
    monkeypatch.setattr(report_bug, "_in_docker", lambda: True)

    env = detect_environment(repo_root=".")
    assert env.origin_url == "unknown"
    assert env.source_slug == "local-project"
    assert env.in_docker is True


def test_detect_environment_survives_subprocess_timeout(monkeypatch):
    import core.report_bug as report_bug

    def _raise(cmd, cwd=None, timeout=15):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(report_bug, "_run", _raise)
    monkeypatch.setattr(report_bug, "_in_docker", lambda: False)

    env = detect_environment(repo_root=".")
    assert env.origin_url == "unknown"
    assert env.source_slug == "local-project"


# --------------------------------------------------------------------------- #
# render_issue_body
# --------------------------------------------------------------------------- #
def test_render_issue_body_includes_all_fields():
    env = EnvironmentInfo(
        origin_url="https://github.com/acme/widgets.git",
        source_slug="github-com-acme-widgets",
        agloop_version="0.8.0",
        platform="Linux-6.8-x86_64",
        in_docker=True,
    )
    body = render_issue_body("Título do achado", "Descrição detalhada.", "high", env)

    assert "https://github.com/acme/widgets.git" in body
    assert "0.8.0" in body
    assert "Linux-6.8-x86_64 (Docker)" in body
    assert "high" in body
    assert "Descrição detalhada." in body


# --------------------------------------------------------------------------- #
# find_duplicate
# --------------------------------------------------------------------------- #
def test_find_duplicate_returns_url_when_found(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(stdout="https://github.com/yuremarketing/AgLoop/issues/99\n"))

    assert find_duplicate("algo quebrou") == "https://github.com/yuremarketing/AgLoop/issues/99"


def test_find_duplicate_returns_none_when_not_found(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(stdout=""))

    assert find_duplicate("algo novo") is None


def test_find_duplicate_is_non_blocking_on_gh_failure(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(returncode=1, stderr="rate limited"))

    assert find_duplicate("algo") is None


def test_find_duplicate_is_non_blocking_on_timeout(monkeypatch):
    import core.report_bug as report_bug

    def _raise(cmd, cwd=None, timeout=15):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=timeout)

    monkeypatch.setattr(report_bug, "_run", _raise)

    assert find_duplicate("algo") is None


# --------------------------------------------------------------------------- #
# submit_report
# --------------------------------------------------------------------------- #
def test_submit_report_creates_labels_and_issue(monkeypatch):
    import core.report_bug as report_bug

    calls = []

    def _fake_run(cmd, cwd=None, timeout=15):
        calls.append(cmd)
        if cmd[:3] == ["gh", "issue", "create"]:
            return _completed(stdout="https://github.com/yuremarketing/AgLoop/issues/100\n")
        return _completed()

    monkeypatch.setattr(report_bug, "_run", _fake_run)

    url = submit_report("Título", "corpo", "acme-widgets", repo="yuremarketing/AgLoop")

    assert url == "https://github.com/yuremarketing/AgLoop/issues/100"
    label_calls = [c for c in calls if c[:3] == ["gh", "label", "create"]]
    assert any("area:field-report" in c for c in label_calls)
    assert any("source:acme-widgets" in c for c in label_calls)


def test_submit_report_raises_on_gh_failure(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(returncode=1, stderr="not authenticated"))

    with pytest.raises(RuntimeError, match="not authenticated"):
        submit_report("Título", "corpo", "acme-widgets")


# --------------------------------------------------------------------------- #
# run_report — orchestration & the mandatory-confirmation guarantee
# --------------------------------------------------------------------------- #
def test_run_report_errors_without_gh_binary(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_gh_available", lambda: False)

    result = run_report(title="t", description="d")
    assert result.submitted is False
    assert result.error is True
    assert "gh" in result.message.lower()


def test_run_report_errors_when_not_authenticated(monkeypatch):
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_gh_available", lambda: True)
    monkeypatch.setattr(report_bug, "_run", lambda cmd, cwd=None, timeout=15: _completed(returncode=1))

    result = run_report(title="t", description="d")
    assert result.submitted is False
    assert result.error is True
    assert "autenticado" in result.message.lower()


def _auth_ok_env(monkeypatch, *, duplicate=None, submit_url="https://github.com/yuremarketing/AgLoop/issues/1"):
    """Shared plumbing: gh present, authenticated, env detection trivial."""
    import core.report_bug as report_bug

    monkeypatch.setattr(report_bug, "_gh_available", lambda: True)
    monkeypatch.setattr(
        report_bug,
        "detect_environment",
        lambda repo_root=".": EnvironmentInfo(
            origin_url="unknown", source_slug="local-project", agloop_version="dev", platform="Linux", in_docker=False
        ),
    )
    monkeypatch.setattr(report_bug, "find_duplicate", lambda title, repo=report_bug.DEFAULT_REPO: duplicate)
    monkeypatch.setattr(report_bug, "submit_report", lambda title, body, slug, repo=report_bug.DEFAULT_REPO: submit_url)

    def _fake_auth(cmd, cwd=None, timeout=15):
        assert cmd[:2] == ["gh", "auth"]
        return _completed(returncode=0)

    monkeypatch.setattr(report_bug, "_run", _fake_auth)


def test_run_report_never_submits_without_yes_or_confirm(monkeypatch):
    _auth_ok_env(monkeypatch)

    result = run_report(title="t", description="d")

    assert result.submitted is False
    assert result.error is False
    assert "confirme" in result.message.lower()
    assert result.rendered_body  # draft is shown so a human can review before re-running with --yes


def test_run_report_submits_with_yes(monkeypatch):
    _auth_ok_env(monkeypatch)

    result = run_report(title="t", description="d", yes=True)

    assert result.submitted is True
    assert result.url == "https://github.com/yuremarketing/AgLoop/issues/1"


def test_run_report_respects_interactive_confirm_decline(monkeypatch):
    _auth_ok_env(monkeypatch)

    result = run_report(title="t", description="d", confirm=lambda body: False)

    assert result.submitted is False
    assert result.error is False
    assert "cancelado" in result.message.lower()


def test_run_report_respects_interactive_confirm_accept(monkeypatch):
    _auth_ok_env(monkeypatch)

    result = run_report(title="t", description="d", confirm=lambda body: True)

    assert result.submitted is True
    assert result.url == "https://github.com/yuremarketing/AgLoop/issues/1"


def test_run_report_stops_on_duplicate_unless_forced(monkeypatch):
    _auth_ok_env(monkeypatch, duplicate="https://github.com/yuremarketing/AgLoop/issues/42")

    result = run_report(title="t", description="d", yes=True)

    assert result.submitted is False
    assert result.duplicate_url == "https://github.com/yuremarketing/AgLoop/issues/42"


def test_run_report_force_bypasses_duplicate_check(monkeypatch):
    _auth_ok_env(monkeypatch, duplicate="https://github.com/yuremarketing/AgLoop/issues/42")

    result = run_report(title="t", description="d", yes=True, force=True)

    assert result.submitted is True
    assert result.duplicate_url is None


def test_run_report_rejects_invalid_severity():
    with pytest.raises(ValueError):
        run_report(title="t", description="d", severity="catastrophic")
