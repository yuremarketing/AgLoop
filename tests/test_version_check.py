"""
Testes unitários para o módulo core/version_check.py (Issue #54).
"""

import json
import time
from unittest.mock import MagicMock, patch

import pytest

from core.version_check import (
    CACHE_TTL_SECONDS,
    check_pypi_update,
    fetch_latest_pypi_version,
    get_installed_version,
    is_update_check_disabled,
    is_version_newer,
    parse_semver,
)


def test_parse_semver():
    assert parse_semver("0.8.0") == (0, 8, 0)
    assert parse_semver("v1.4.1") == (1, 4, 1)
    assert parse_semver("2.0.0-rc1") == (2, 0, 0)
    assert parse_semver("10.2") == (10, 2)
    assert parse_semver("invalid") == (0,)


def test_is_version_newer():
    assert is_version_newer("0.8.0", "0.7.0") is True
    assert is_version_newer("1.0.0", "0.9.9") is True
    assert is_version_newer("0.8.1", "0.8.0") is True
    assert is_version_newer("0.7.0", "0.8.0") is False
    assert is_version_newer("0.8.0", "0.8.0") is False
    assert is_version_newer("invalid", "0.8.0") is False


def test_get_installed_version():
    ver = get_installed_version()
    assert isinstance(ver, str)
    assert len(ver) > 0


def test_is_update_check_disabled(monkeypatch):
    monkeypatch.delenv("AGLOOP_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)
    assert is_update_check_disabled() is False

    monkeypatch.setenv("AGLOOP_NO_UPDATE_CHECK", "1")
    assert is_update_check_disabled() is True

    monkeypatch.setenv("AGLOOP_NO_UPDATE_CHECK", "0")
    monkeypatch.setenv("CI", "true")
    assert is_update_check_disabled() is True

    monkeypatch.delenv("CI", raising=False)
    monkeypatch.setenv("GITHUB_ACTIONS", "true")
    assert is_update_check_disabled() is True


def test_fetch_latest_pypi_version_success():
    mock_payload = json.dumps({"info": {"version": "0.8.5"}}).encode("utf-8")
    mock_response = MagicMock()
    mock_response.status = 200
    mock_response.read.return_value = mock_payload
    mock_response.__enter__.return_value = mock_response

    with patch("urllib.request.urlopen", return_value=mock_response):
        latest = fetch_latest_pypi_version(timeout=1.0)
        assert latest == "0.8.5"


def test_fetch_latest_pypi_version_fail_silent():
    with patch("urllib.request.urlopen", side_effect=Exception("Network error")):
        latest = fetch_latest_pypi_version(timeout=1.0)
        assert latest is None


def test_check_pypi_update_notice(tmp_path, monkeypatch):
    monkeypatch.delenv("AGLOOP_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    cache_file = tmp_path / "cache.json"

    with patch("core.version_check.fetch_latest_pypi_version", return_value="0.9.0"):
        notice = check_pypi_update(
            current_version="0.8.0",
            cache_path=cache_file,
            timeout=1.0,
        )
        assert notice is not None
        assert "0.9.0" in notice
        assert "0.8.0" in notice
        assert "pip install --upgrade agloop" in notice
        assert cache_file.is_file()


def test_check_pypi_update_no_notice_when_up_to_date(tmp_path, monkeypatch):
    monkeypatch.delenv("AGLOOP_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    cache_file = tmp_path / "cache.json"

    with patch("core.version_check.fetch_latest_pypi_version", return_value="0.8.0"):
        notice = check_pypi_update(
            current_version="0.8.0",
            cache_path=cache_file,
            timeout=1.0,
        )
        assert notice is None


def test_check_pypi_update_uses_valid_cache(tmp_path, monkeypatch):
    monkeypatch.delenv("AGLOOP_NO_UPDATE_CHECK", raising=False)
    monkeypatch.delenv("CI", raising=False)
    monkeypatch.delenv("GITHUB_ACTIONS", raising=False)

    cache_file = tmp_path / "cache.json"
    cache_file.write_text(
        json.dumps({"latest_version": "0.9.5", "timestamp": time.time()}),
        encoding="utf-8",
    )

    # Não deve chamar fetch_latest_pypi_version
    with patch("core.version_check.fetch_latest_pypi_version") as mock_fetch:
        notice = check_pypi_update(
            current_version="0.8.0",
            cache_path=cache_file,
            timeout=1.0,
        )
        assert mock_fetch.call_count == 0
        assert notice is not None
        assert "0.9.5" in notice


def test_check_pypi_update_disabled_flag(tmp_path, monkeypatch):
    monkeypatch.setenv("AGLOOP_NO_UPDATE_CHECK", "1")
    cache_file = tmp_path / "cache.json"

    with patch("core.version_check.fetch_latest_pypi_version") as mock_fetch:
        notice = check_pypi_update(
            current_version="0.8.0",
            cache_path=cache_file,
            timeout=1.0,
        )
        assert mock_fetch.call_count == 0
        assert notice is None
