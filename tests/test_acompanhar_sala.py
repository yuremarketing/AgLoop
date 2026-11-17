"""
Testes unitários e de integração para o script de acompanhamento da Sala de Guerra (Issue #66).
Requisitos: 3 painéis, tema roxo/laranja, posse diária explícita (--claim),
bloqueio por padrão e liberação automática (--kill/--release).
"""

import json
import os
from pathlib import Path
import subprocess

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "acompanhar_sala.sh"
OWNER_FILE = Path(__file__).parent.parent / ".agloop" / "tmux-session.owner.json"


def teardown_function():
    # Garante limpeza de sessão e arquivo de posse após cada teste
    subprocess.run([str(SCRIPT_PATH), "--kill"], capture_output=True, check=False)
    if OWNER_FILE.exists():
        OWNER_FILE.unlink(missing_ok=True)


def test_script_exists_and_is_executable():
    assert SCRIPT_PATH.is_file(), f"{SCRIPT_PATH} não encontrado"
    assert os.access(SCRIPT_PATH, os.X_OK), f"{SCRIPT_PATH} não tem permissão de execução"


def test_help_flag_displays_usage():
    res = subprocess.run(
        [str(SCRIPT_PATH), "--help"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Uso:" in res.stdout
    assert "--claim" in res.stdout
    assert "--release" in res.stdout
    assert "--attach" in res.stdout
    assert "--kill" in res.stdout
    assert "--status" in res.stdout
    assert "agloop-live" in res.stdout


def test_blocks_by_default_without_claim():
    """Requisito do PO: Sem reivindicação de posse ativa, recusa iniciar por padrão."""
    teardown_function()
    res = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 1
    assert "Bloqueio" in res.stderr
    assert "--claim" in res.stderr


def test_claim_records_owner_file_and_starts_session():
    """Requisito do PO: Posse diária explícita salva owner e since."""
    teardown_function()
    res = subprocess.run(
        [str(SCRIPT_PATH), "--claim", "Alice"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "Alice" in res.stdout
    assert OWNER_FILE.is_file()

    with open(OWNER_FILE, encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("owner") == "Alice"
    assert "since" in data


def test_kill_automatically_releases_owner_file():
    """Requisito do PO: Liberação automática ao terminar."""
    subprocess.run([str(SCRIPT_PATH), "--claim", "Bob"], capture_output=True, check=False)
    assert OWNER_FILE.is_file()

    res = subprocess.run(
        [str(SCRIPT_PATH), "--kill"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "encerrada e posse liberada" in res.stdout
    assert not OWNER_FILE.exists()


def test_status_flag_shows_unoccupied_and_claimed_states():
    teardown_function()
    res1 = subprocess.run(
        [str(SCRIPT_PATH), "--status"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res1.returncode == 0
    assert "Nenhum (sessão desocupada)" in res1.stdout

    subprocess.run([str(SCRIPT_PATH), "--claim", "Carlos"], capture_output=True, check=False)
    res2 = subprocess.run(
        [str(SCRIPT_PATH), "--status"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res2.returncode == 0
    assert "Carlos" in res2.stdout


def test_script_contains_purple_orange_theme_and_panes():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    # Requisito do PO: Fundo roxo (colour55) e texto/letras em laranja (colour208)
    assert "colour55" in content, "Tema deve incluir cor roxa (colour55)"
    assert "colour208" in content, "Tema deve incluir cor laranja (colour208)"
    # Layout de 3 painéis
    assert "split-window -h" in content
    assert "split-window -v" in content
    assert "tail -f" in content
    assert "agloop-live" in content


def test_missing_tmux_exits_with_informative_error(tmp_path):
    fake_bin = tmp_path / "bin"
    fake_bin.mkdir()
    for tool in ("bash", "sh", "dirname", "basename", "cat", "python3"):
        tool_path = subprocess.run(["which", tool], capture_output=True, text=True, check=False).stdout.strip()
        if tool_path and os.path.exists(tool_path):
            (fake_bin / tool).symlink_to(tool_path)

    env = os.environ.copy()
    env["PATH"] = str(fake_bin)

    res = subprocess.run(
        [str(SCRIPT_PATH)],
        capture_output=True,
        text=True,
        env=env,
        check=False,
    )
    assert res.returncode == 1
    assert "tmux não encontrado" in res.stderr
    assert "watch" in res.stderr
