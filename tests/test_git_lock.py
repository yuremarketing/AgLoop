import json
import os
import socket
import subprocess
import sys
import time

import pytest

from conftest import ROOM, _git, append, files_in_last_commit, head, push_from
from core.git_lock import GitLock


def lock(path, **kw):
    return GitLock(repo_path=str(path), **kw)


# --------------------------------------------------------------------------- #
# commit() never touches files that aren't the War Room
# --------------------------------------------------------------------------- #
def test_commit_only_includes_room_file(remote_setup):
    a, _, _ = remote_setup
    (a / "app.py").write_text("print('half written by another agent')\n")  # dirty tracked
    (a / "new_test.py").write_text("def test(): pass\n")                    # untracked
    _git(a, "add", "new_test.py")                                           # even staged!

    gl = lock(a)
    ok = gl.acquire_lock_and_push(lambda: append(a, "Alice"), "msg", [ROOM])

    assert ok and gl.last_status == "ok"
    assert files_in_last_commit(a) == {ROOM}
    assert (a / "app.py").read_text() == "print('half written by another agent')\n"
    assert (a / "new_test.py").exists()
    assert head(a) == _git(a, "rev-parse", "origin/main").strip()


# --------------------------------------------------------------------------- #
# Regression: push rejected used to `reset --hard` and wipe other agents' work
# --------------------------------------------------------------------------- #
def test_lost_race_preserves_dirty_files_and_adopts_remote_room(remote_setup):
    a, b, _ = remote_setup
    (a / "app.py").write_text("print('WIP from Claude')\n")
    (a / "scratch.py").write_text("x = 1\n")

    def action():
        push_from(b, "Bob", "I was faster")  # another machine wins the race mid-turn
        append(a, "Alice", "stale reply")

    gl = lock(a)
    ok = gl.acquire_lock_and_push(action, "msg", [ROOM])

    assert not ok and gl.last_status == "lost_race"
    assert (a / "app.py").read_text() == "print('WIP from Claude')\n"
    assert (a / "scratch.py").read_text() == "x = 1\n"
    room = (a / ROOM).read_text()
    assert "I was faster" in room and "stale reply" not in room
    assert head(a) == head(b)
    assert not os.path.exists(gl.lock_dir)


def test_rejected_push_with_clean_rebase_retries_and_succeeds(remote_setup):
    a, b, _ = remote_setup

    def action():
        (b / "other.txt").write_text("code from another machine\n")
        _git(b, "add", "other.txt")
        _git(b, "commit", "-m", "code")
        _git(b, "push", "-q", "origin", "main")
        append(a, "Alice")

    gl = lock(a)
    assert gl.acquire_lock_and_push(action, "msg", [ROOM])
    _git(b, "pull", "-q", "origin", "main")
    assert "## Alice" in (b / ROOM).read_text()
    assert (a / "other.txt").exists()


def test_unpushed_commit_is_pushed_on_next_iteration(remote_setup):
    a, b, _ = remote_setup
    gl = lock(a)
    append(a, "Alice")
    assert gl.commit("left behind by a network failure", [ROOM])

    assert gl.acquire_lock_and_push(lambda: None, "noop", [ROOM])
    _git(b, "pull", "-q", "origin", "main")
    assert "## Alice" in (b / ROOM).read_text()


# --------------------------------------------------------------------------- #
# has_remote_updates(): only "remote ahead of me" counts
# --------------------------------------------------------------------------- #
def test_has_remote_updates_false_when_in_sync(remote_setup):
    a, _, _ = remote_setup
    assert lock(a).has_remote_updates() is False


def test_has_remote_updates_true_when_remote_ahead(remote_setup):
    a, b, _ = remote_setup
    push_from(b, "Bob")
    assert lock(a).has_remote_updates() is True


def test_has_remote_updates_false_when_local_ahead(remote_setup):
    a, _, _ = remote_setup
    gl = lock(a)
    append(a, "Alice")
    gl.commit("unpushed", [ROOM])
    assert gl.has_remote_updates() is False


def test_has_remote_updates_false_without_origin(local_repo):
    assert lock(local_repo).has_remote_updates() is False


def test_has_remote_updates_survives_fetch_failure(remote_setup):
    a, _, _ = remote_setup
    _git(a, "remote", "set-url", "origin", "/nonexistent/repo.git")
    assert lock(a).has_remote_updates() is False


# --------------------------------------------------------------------------- #
# Regression: "cannot pull with rebase: You have unstaged changes"
# --------------------------------------------------------------------------- #
def test_sync_does_not_pull_when_no_remote_updates(remote_setup):
    a, _, _ = remote_setup
    (a / "app.py").write_text("unstaged change\n")
    before = head(a)
    assert lock(a).sync_if_needed([ROOM])
    assert head(a) == before
    assert (a / "app.py").read_text() == "unstaged change\n"


def test_sync_with_remote_updates_keeps_unstaged_changes(remote_setup):
    a, b, _ = remote_setup
    (a / "app.py").write_text("unstaged change\n")
    push_from(b, "Bob")
    assert lock(a).sync_if_needed([ROOM])
    assert head(a) == head(b)
    assert (a / "app.py").read_text() == "unstaged change\n"


# --------------------------------------------------------------------------- #
# Local lock + stale lock recovery
# --------------------------------------------------------------------------- #
def _write_lock(gl, pid, ts=None, host=None):
    os.mkdir(gl.lock_dir)
    with open(os.path.join(gl.lock_dir, "owner.json"), "w") as f:
        json.dump({"pid": pid, "host": host or socket.gethostname(), "ts": ts or time.time()}, f)


def _dead_pid():
    p = subprocess.Popen([sys.executable, "-c", "pass"])
    p.wait()
    return p.pid


def test_live_lock_blocks(local_repo):
    gl = lock(local_repo)
    _write_lock(gl, os.getppid())
    assert gl.acquire_lock_and_push(lambda: append(local_repo, "Alice"), "m", [ROOM]) is False
    assert gl.last_status == "locked"


def test_lock_of_dead_process_is_recovered(local_repo):
    gl = lock(local_repo)
    _write_lock(gl, _dead_pid())
    assert gl._acquire_local_lock()
    gl._release_local_lock()
    assert not os.path.exists(gl.lock_dir)


def test_lock_past_timeout_is_recovered(local_repo):
    gl = lock(local_repo, lock_timeout=5)
    _write_lock(gl, os.getppid(), ts=time.time() - 60)
    assert gl._acquire_local_lock()


def test_lock_from_other_host_not_broken_before_timeout(local_repo):
    gl = lock(local_repo)
    _write_lock(gl, _dead_pid(), host="some-other-host")
    assert gl._acquire_local_lock() is False


def test_release_does_not_delete_someone_elses_lock(local_repo):
    gl = lock(local_repo)
    _write_lock(gl, os.getppid())
    gl._release_local_lock()
    assert os.path.exists(gl.lock_dir)


# --------------------------------------------------------------------------- #
# No origin / deprecation
# --------------------------------------------------------------------------- #
def test_works_without_origin(local_repo):
    gl = lock(local_repo)
    assert gl.acquire_lock_and_push(lambda: append(local_repo, "Alice"), "local msg", [ROOM])
    assert files_in_last_commit(local_repo) == {ROOM}
    assert "local msg" in _git(local_repo, "log", "-1", "--format=%s")


def test_local_mode_env_is_deprecated(local_repo, monkeypatch):
    monkeypatch.setenv("AGENT_LOOP_LOCAL_MODE", "true")
    with pytest.warns(FutureWarning, match="deprecated"):
        lock(local_repo)
