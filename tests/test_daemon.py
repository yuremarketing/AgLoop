"""
Testes unitários e de integração para o AgLoop Host Daemon (Issue #74 / ADR-0008).
Valida o orquestrador supervisor de processos desacoplado do ciclo de vida das LLMs.
"""

import os
import signal
import subprocess
import sys
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.daemon import (
    DEFAULT_DAEMON_PID_FILE,
    AgLoopDaemon,
    get_daemon_status,
    is_daemon_running,
    start_daemon_background,
    stop_daemon,
)
from core.runner import STALL_SENTINEL


def test_pid_file_lifecycle(tmp_path):
    pid_file = str(tmp_path / "test_daemon.pid")

    assert not is_daemon_running(pid_file)

    # Escreve PID atual (ativo)
    from core.daemon import _read_pid_file, _remove_pid_file, _write_pid_file

    _write_pid_file(pid_file)
    assert _read_pid_file(pid_file) == os.getpid()
    assert is_daemon_running(pid_file)

    # Remove PID
    _remove_pid_file(pid_file)
    assert _read_pid_file(pid_file) is None
    assert not is_daemon_running(pid_file)


def test_stale_pid_is_cleaned_up(tmp_path):
    pid_file = str(tmp_path / "test_daemon.pid")
    from core.daemon import _write_pid_file

    # Usa um PID que certamente não existe (ex: 999999)
    with open(pid_file, "w", encoding="utf-8") as f:
        f.write("999999")

    # is_daemon_running deve detectar PID morto e limpar o arquivo
    assert not is_daemon_running(pid_file)
    assert not os.path.exists(pid_file)


def test_daemon_loop_rearms_automatically(tmp_path):
    pid_file = str(tmp_path / "daemon.pid")
    room_file = str(tmp_path / "war_room.md")
    Path(room_file).write_text("# Test Room\n", encoding="utf-8")

    daemon = AgLoopDaemon(
        war_room_file=room_file,
        repo_path=str(tmp_path),
        pid_file=pid_file,
        local_poll=0.1,
        remote_poll=1.0,
        stall_minutes=5.0,
        audio_alert=False,
    )

    mock_speakers = ["Claude", "Gemini"]
    with patch("core.daemon.watch_war_room", side_effect=mock_speakers) as mock_watch:
        daemon.run(max_iterations=2)
        assert mock_watch.call_count == 2

    assert not os.path.exists(pid_file)


def test_daemon_handles_stall_sentinel_with_alert(tmp_path):
    pid_file = str(tmp_path / "daemon.pid")
    room_file = str(tmp_path / "war_room.md")
    Path(room_file).write_text("# Test Room\n", encoding="utf-8")

    daemon = AgLoopDaemon(
        war_room_file=room_file,
        repo_path=str(tmp_path),
        pid_file=pid_file,
        local_poll=0.1,
        remote_poll=1.0,
        stall_minutes=5.0,
        audio_alert=True,
    )

    with patch("core.daemon.watch_war_room", return_value=STALL_SENTINEL), \
         patch("core.daemon.play_formal_auth_alert") as mock_alert:
        daemon.run(max_iterations=1)
        mock_alert.assert_called_once()


def test_daemon_signal_handling(tmp_path):
    pid_file = str(tmp_path / "daemon.pid")
    room_file = str(tmp_path / "war_room.md")
    Path(room_file).write_text("# Test Room\n", encoding="utf-8")

    daemon = AgLoopDaemon(
        war_room_file=room_file,
        repo_path=str(tmp_path),
        pid_file=pid_file,
        local_poll=0.1,
        remote_poll=1.0,
        stall_minutes=5.0,
        audio_alert=False,
    )

    daemon.running = True
    daemon.handle_signal(signal.SIGINT, None)
    assert not daemon.running


def test_daemon_status_reporting(tmp_path):
    pid_file = str(tmp_path / "daemon.pid")
    status = get_daemon_status(repo_path=str(tmp_path), pid_file=pid_file)
    assert status["running"] is False
    assert status["pid"] is None

    from core.daemon import _write_pid_file
    _write_pid_file(pid_file)

    status_running = get_daemon_status(repo_path=str(tmp_path), pid_file=pid_file)
    assert status_running["running"] is True
    assert status_running["pid"] == os.getpid()

    from core.daemon import _remove_pid_file
    _remove_pid_file(pid_file)


def test_cli_daemon_commands(tmp_path):
    # Testa subcomando daemon --help
    res = subprocess.run(
        [sys.executable, "main.py", "daemon", "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "start" in res.stdout
    assert "stop" in res.stdout
    assert "status" in res.stdout
    assert "run" in res.stdout

    # Testa status com daemon parado
    pid_file = str(tmp_path / "cli_daemon.pid")
    res_status = subprocess.run(
        [sys.executable, "main.py", "daemon", "status", "--pid-file", pid_file],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res_status.returncode == 0
    assert "PARADO" in res_status.stdout
