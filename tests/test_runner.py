import os

import pytest

from conftest import ROOM, _git, append
from core import runner as runner_mod
from core.git_lock import GitLock


class FakeAgent:
    model = "fake"

    def __init__(self, name):
        self.name = name
        self.calls = 0

    def think_and_act(self, context):
        self.calls += 1
        return f"message #{self.calls}"


def run_with_sleep_hook(monkeypatch, agent, hook, max_sleeps=8):
    """Runs the loop; every time.sleep() call invokes hook(n). Stops after max_sleeps."""
    counter = {"n": 0}

    def fake_sleep(_seconds):
        counter["n"] += 1
        hook(counter["n"])
        if counter["n"] >= max_sleeps:
            raise KeyboardInterrupt

    monkeypatch.setattr(runner_mod.time, "sleep", fake_sleep)
    runner_mod.run_agent_loop(agent, war_room_file=ROOM, local_poll=0, jitter=0)


@pytest.fixture
def in_repo(local_repo, monkeypatch):
    monkeypatch.chdir(local_repo)
    return local_repo


def test_retries_after_busy_lock_no_lost_wakeup(in_repo, monkeypatch):
    """Regression: a failed iteration used to update last_mod_time and never retry."""
    gl = GitLock(".")
    os.mkdir(gl.lock_dir)
    with open(os.path.join(gl.lock_dir, "owner.json"), "w") as f:
        import json, socket, time
        json.dump({"pid": os.getppid(), "host": socket.gethostname(), "ts": time.time()}, f)

    agent = FakeAgent("Alice")

    def hook(n):
        if n == 1:  # the other local agent finishes its turn
            import shutil
            shutil.rmtree(gl.lock_dir)

    run_with_sleep_hook(monkeypatch, agent, hook)
    assert agent.calls == 1
    assert "## Alice" in (in_repo / ROOM).read_text()
    assert "Alice" in _git(in_repo, "log", "-1", "--format=%s")


def test_idle_loop_spends_no_tokens(in_repo, monkeypatch):
    append(in_repo, "Alice")
    _git(in_repo, "commit", "-qam", "alice spoke last")

    attempts = {"n": 0}
    original = GitLock.acquire_lock_and_push

    def counting(self, *a, **kw):
        attempts["n"] += 1
        return original(self, *a, **kw)

    monkeypatch.setattr(GitLock, "acquire_lock_and_push", counting)
    agent = FakeAgent("Alice")
    run_with_sleep_hook(monkeypatch, agent, lambda n: None, max_sleeps=10)

    assert agent.calls == 0          # never called the LLM
    assert attempts["n"] == 1        # only the startup check took the lock


def test_local_write_by_other_agent_triggers_turn(in_repo, monkeypatch):
    agent = FakeAgent("Alice")

    def hook(n):
        if n == 3:  # another agent on the same disk writes to the room
            append(in_repo, "Bob", "your turn")
            st = os.stat(in_repo / ROOM)
            os.utime(in_repo / ROOM, ns=(st.st_atime_ns, st.st_mtime_ns + 1_000_000))

    run_with_sleep_hook(monkeypatch, agent, hook, max_sleeps=10)
    assert agent.calls == 2
    assert (in_repo / ROOM).read_text().rstrip().endswith("message #2")
