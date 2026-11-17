"""
Testes unitários e de integração para o script de acompanhamento da Sala de Guerra (Issue #66).
"""

import os
from pathlib import Path
import subprocess

SCRIPT_PATH = Path(__file__).parent.parent / "scripts" / "acompanhar_sala.sh"


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
    assert "--attach" in res.stdout
    assert "--kill" in res.stdout
    assert "--status" in res.stdout
    assert "agloop-live" in res.stdout


def test_status_flag_executes_observability_check():
    res = subprocess.run(
        [str(SCRIPT_PATH), "--status"],
        capture_output=True,
        text=True,
        check=False,
    )
    assert res.returncode == 0
    assert "OBSERVABILIDADE" in res.stdout
    assert "Sala de Guerra" in res.stdout
    assert "Vigília Híbrida" in res.stdout


def test_script_contains_purple_orange_theme_and_panes():
    content = SCRIPT_PATH.read_text(encoding="utf-8")
    # Requisito do PO: Fundo roxo e texto/letras em laranja
    assert "colour55" in content, "Tema deve incluir cor roxa (colour55)"
    assert "colour208" in content, "Tema deve incluir cor laranja (colour208)"
    # Layout de 3 painéis
    assert "split-window -h" in content
    assert "split-window -v" in content
    assert "tail -f" in content
    assert "agloop-live" in content


def test_missing_tmux_exits_with_informative_error(tmp_path):
    # Cria diretório de PATH com bash e python3, mas sem tmux
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
