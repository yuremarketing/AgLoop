import os
import subprocess
import sys

import pytest
from git import Repo

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ROOM = "war_room.md"


def _git(path, *args):
    return subprocess.run(["git", *args], cwd=path, check=True, capture_output=True, text=True).stdout


def _configure(path):
    _git(path, "config", "user.name", "AgLoop Test")
    _git(path, "config", "user.email", "test@agloop.local")
    _git(path, "config", "commit.gpgsign", "false")


@pytest.fixture
def remote_setup(tmp_path, monkeypatch):
    """
    remote.git  -> bare repo playing the role of GitHub
    a/          -> agent workspace under test
    b/          -> "another machine"
    """
    monkeypatch.delenv("AGENT_LOOP_LOCAL_MODE", raising=False)
    bare = tmp_path / "remote.git"
    _git(tmp_path, "init", "--bare", "-b", "main", str(bare))

    seed = tmp_path / "seed"
    _git(tmp_path, "init", "-b", "main", str(seed))
    _configure(seed)
    (seed / ROOM).write_text("# AgLoop War Room\n")
    (seed / "app.py").write_text("print('v1')\n")
    _git(seed, "add", "-A")
    _git(seed, "commit", "-m", "init")
    _git(seed, "remote", "add", "origin", str(bare))
    _git(seed, "push", "origin", "main")

    clones = {}
    for name in ("a", "b"):
        path = tmp_path / name
        _git(tmp_path, "clone", "-q", str(bare), str(path))
        _configure(path)
        clones[name] = path
    return clones["a"], clones["b"], bare


@pytest.fixture
def local_repo(tmp_path, monkeypatch):
    monkeypatch.delenv("AGENT_LOOP_LOCAL_MODE", raising=False)
    path = tmp_path / "local"
    _git(tmp_path, "init", "-b", "main", str(path))
    _configure(path)
    (path / ROOM).write_text("# AgLoop War Room\n")
    _git(path, "add", "-A")
    _git(path, "commit", "-m", "init")
    return path


def append(path, speaker, text="hello"):
    with open(os.path.join(path, ROOM), "a", encoding="utf-8") as f:
        f.write(f"\n## {speaker}\n\n{text}\n")


def push_from(path, speaker, text="hi"):
    append(path, speaker, text)
    _git(path, "commit", "-am", f"{speaker} msg")
    _git(path, "push", "-q", "origin", "main")


def head(path):
    return Repo(path).head.commit.hexsha


def files_in_last_commit(path):
    return set(_git(path, "show", "--name-only", "--format=", "HEAD").split())
