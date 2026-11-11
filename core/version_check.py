"""
Módulo de checagem não-intrusiva de nova versão do AgLoop no PyPI.

Issue #54: Consulta leve, cache diário (24h), timeout curto (2s),
fail-silent offline e desligamento automático em CI / opt-out.
"""

from __future__ import annotations

import json
import os
import re
import time
import urllib.request
from pathlib import Path

DEFAULT_TIMEOUT = 2.0
CACHE_TTL_SECONDS = 86400  # 24 horas
PYPI_URL = "https://pypi.org/pypi/agloop/json"


def parse_semver(version_str: str) -> tuple[int, ...]:
    """
    Converte uma string de versão semântica simples em tupla de inteiros.
    Ex: '0.8.0' -> (0, 8, 0), 'v1.4.1' -> (1, 4, 1).
    """
    cleaned = version_str.strip().lstrip("vV")
    parts = []
    for part in re.split(r"[.-]", cleaned):
        if part.isdigit():
            parts.append(int(part))
        else:
            break
    return tuple(parts) or (0,)


def is_version_newer(latest: str, current: str) -> bool:
    """Retorna True se `latest` for estritamente mais recente que `current`."""
    try:
        return parse_semver(latest) > parse_semver(current)
    except Exception:
        return False


def get_installed_version() -> str:
    """
    Obtém a versão atualmente instalada do pacote agloop.
    Usa importlib.metadata com fallback para leitura local de pyproject.toml ou '0.8.0'.
    """
    try:
        import importlib.metadata

        return importlib.metadata.version("agloop")
    except Exception:
        pass

    # Fallback para desenvolvimento local: ler pyproject.toml se disponível
    try:
        root = Path(__file__).resolve().parent.parent
        pyproject = root / "pyproject.toml"
        if pyproject.is_file():
            for line in pyproject.read_text(encoding="utf-8").splitlines():
                if line.strip().startswith("version"):
                    parts = line.split("=")
                    if len(parts) == 2:
                        return parts[1].strip().strip('"').strip("'")
    except Exception:
        pass

    return "0.8.0"


def _get_default_cache_path() -> Path:
    """Retorna o caminho padrão do arquivo de cache de versão."""
    xdg_cache = os.getenv("XDG_CACHE_HOME")
    if xdg_cache:
        base = Path(xdg_cache)
    else:
        base = Path.home() / ".cache"
    return base / "agloop" / "pypi_version.json"


def is_update_check_disabled() -> bool:
    """Retorna True se a checagem estiver desativada por variável de ambiente ou CI."""
    if os.getenv("AGLOOP_NO_UPDATE_CHECK", "").lower() in ("1", "true", "yes"):
        return True
    if os.getenv("CI", "").lower() in ("1", "true", "yes"):
        return True
    if os.getenv("GITHUB_ACTIONS", "").lower() == "true":
        return True
    return False


def fetch_latest_pypi_version(timeout: float = DEFAULT_TIMEOUT) -> str | None:
    """
    Consulta o PyPI pelo endpoint JSON público oficial.
    Fail-silent: retorna None em caso de timeout, offline ou erro.
    """
    req = urllib.request.Request(
        PYPI_URL,
        headers={"User-Agent": "agloop-version-check"},
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as response:
            if response.status == 200:
                data = json.loads(response.read().decode("utf-8"))
                return data.get("info", {}).get("version")
    except Exception:
        return None
    return None


def check_pypi_update(
    current_version: str | None = None,
    cache_path: Path | None = None,
    timeout: float = DEFAULT_TIMEOUT,
) -> str | None:
    """
    Verifica se há versão mais recente no PyPI com cache diário e fail-silent.

    :param current_version: Versão instalada (se None, auto-detecta).
    :param cache_path: Caminho customizado para o cache (usado em testes).
    :param timeout: Timeout da chamada HTTP.
    :return: String com o aviso de atualização ou None se atualizado/offline/desativado.
    """
    if is_update_check_disabled():
        return None

    current = current_version or get_installed_version()
    cache_file = cache_path or _get_default_cache_path()
    now = time.time()
    latest: str | None = None

    # Tenta ler do cache se válido (< 24h)
    if cache_file.is_file():
        try:
            cached_data = json.loads(cache_file.read_text(encoding="utf-8"))
            last_checked = cached_data.get("timestamp", 0)
            if now - last_checked < CACHE_TTL_SECONDS:
                latest = cached_data.get("latest_version")
        except Exception:
            pass

    # Se não obteve do cache válido, busca na rede
    if not latest:
        latest = fetch_latest_pypi_version(timeout=timeout)
        if latest:
            try:
                cache_file.parent.mkdir(parents=True, exist_ok=True)
                cache_file.write_text(
                    json.dumps({"latest_version": latest, "timestamp": now}),
                    encoding="utf-8",
                )
            except Exception:
                pass

    if latest and is_version_newer(latest, current):
        return f"AgLoop: versão {latest} disponível (instalada: {current}). Atualize: pip install --upgrade agloop"

    return None
