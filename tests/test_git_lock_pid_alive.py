import ctypes
from types import SimpleNamespace

from core.git_lock import GitLock

# These tests exercise the win32 branch of GitLock._pid_alive() on any host OS
# by faking ctypes.windll (not present outside Windows) and sys.platform.
# core/git_lock.py:_pid_alive() re-imports `ctypes` locally, so patching the
# real `ctypes` module's `windll` attribute here is picked up transparently.

STILL_ACTIVE = 259
ERROR_ACCESS_DENIED = 5
ERROR_INVALID_PARAMETER = 87


def _fake_kernel32(open_process_handle, last_error=0, exit_code=STILL_ACTIVE):
    calls = SimpleNamespace(closed=None)

    def open_process(desired_access, inherit, pid):
        return open_process_handle

    def get_exit_code_process(handle, code_ref):
        code_ref._obj.value = exit_code
        return True

    def close_handle(handle):
        calls.closed = handle
        return True

    kernel32 = SimpleNamespace(
        OpenProcess=open_process,
        GetExitCodeProcess=get_exit_code_process,
        CloseHandle=close_handle,
    )
    return kernel32, calls


def test_pid_alive_windows_running_process(monkeypatch):
    kernel32, calls = _fake_kernel32(open_process_handle=1234, exit_code=STILL_ACTIVE)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel32), raising=False)

    assert GitLock._pid_alive(999) is True
    assert calls.closed == 1234  # handle always released


def test_pid_alive_windows_exited_process(monkeypatch):
    kernel32, _ = _fake_kernel32(open_process_handle=5678, exit_code=0)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel32), raising=False)

    assert GitLock._pid_alive(999) is False


def test_pid_alive_windows_open_process_denied_means_alive(monkeypatch):
    # OpenProcess returns NULL and GetLastError() == ERROR_ACCESS_DENIED:
    # the process exists but is owned by another user (parity with POSIX PermissionError).
    kernel32, _ = _fake_kernel32(open_process_handle=0)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel32), raising=False)
    monkeypatch.setattr(ctypes, "GetLastError", lambda: ERROR_ACCESS_DENIED, raising=False)

    assert GitLock._pid_alive(999) is True


def test_pid_alive_windows_open_process_fails_means_dead(monkeypatch):
    # OpenProcess returns NULL and GetLastError() == ERROR_INVALID_PARAMETER: no such pid.
    kernel32, _ = _fake_kernel32(open_process_handle=0)
    monkeypatch.setattr("sys.platform", "win32")
    monkeypatch.setattr(ctypes, "windll", SimpleNamespace(kernel32=kernel32), raising=False)
    monkeypatch.setattr(ctypes, "GetLastError", lambda: ERROR_INVALID_PARAMETER, raising=False)

    assert GitLock._pid_alive(999) is False
