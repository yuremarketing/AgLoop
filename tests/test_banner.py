"""
Testes unitários para o módulo core/banner.py (Issue #45).
"""

import pytest

from core.banner import SOLID_BANNER_ASCII, format_formal_auth_banner, play_formal_auth_alert


def test_solid_banner_ascii_dimensions():
    """Garante que a moldura ASCII sólida tem dimensões uniformes (68 chars)."""
    lines = SOLID_BANNER_ASCII.splitlines()
    assert len(lines) == 6
    for line in lines:
        assert len(line) == 68


def test_format_banner_markdown_default():
    """Garante que o modo padrão (Markdown) gera moldura e callout de segurança."""
    output = format_formal_auth_banner()
    assert "```text" in output
    assert SOLID_BANNER_ASCII in output
    assert "> [!CAUTION]" in output
    assert "AUTORIZAÇÃO FORMAL DO PO NECESSÁRIA" in output
    assert "Aguardando confirmação explícita do PO." in output
    assert 'responda **"ok"** ou **"autorizo"**' in output
    assert "\033[" not in output  # Zero ANSI cru em Markdown


def test_format_banner_markdown_with_reason_and_context():
    """Garante inclusão de motivo e contexto customizados em Markdown."""
    output = format_formal_auth_banner(
        reason="Merge do PR #47 em produção",
        context="Arquivo: core/runner.py",
        is_terminal=False,
    )
    assert "**Motivo:** Merge do PR #47 em produção" in output
    assert "**Contexto:** Arquivo: core/runner.py" in output


def test_format_banner_terminal_ansi(monkeypatch):
    """Garante aplicação de ANSI e blink quando is_terminal=True e NO_COLOR ausente."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    output = format_formal_auth_banner(
        reason="Alteração de código de produção",
        context="Branch fix/algo",
        is_terminal=True,
        blink=True,
    )
    assert "\033[1;31m" in output  # Vermelho
    assert "\033[1;33m" in output  # Amarelo
    assert "\033[5m" in output  # Blink
    assert "Alteração de código de produção" in output
    assert "Branch fix/algo" in output


def test_format_banner_terminal_no_blink(monkeypatch):
    """Garante ausência do código de blink quando blink=False."""
    monkeypatch.delenv("NO_COLOR", raising=False)
    output = format_formal_auth_banner(
        reason="Teste",
        is_terminal=True,
        blink=False,
    )
    assert "\033[5m" not in output
    assert "\033[1;31m" in output


def test_format_banner_terminal_no_color(monkeypatch):
    """Garante respeito à variável de ambiente NO_COLOR."""
    monkeypatch.setenv("NO_COLOR", "1")
    output = format_formal_auth_banner(
        reason="Teste sem cor",
        context="Contexto sem cor",
        is_terminal=True,
    )
    assert "\033[" not in output
    assert "MOTIVO: Teste sem cor" in output
    assert "CONTEXTO: Contexto sem cor" in output
    assert "ACAO DO PO: Responda 'ok' ou 'autorizo' para prosseguir." in output


# --------------------------------------------------------------------------- #
# play_formal_auth_alert — alerta sonoro best-effort (Issue #45, adendo)
# --------------------------------------------------------------------------- #
def test_play_alert_returns_false_without_player(monkeypatch):
    """Sem paplay/aplay/afplay disponível (ex.: container minimalista), nunca levanta."""
    import core.banner as banner_mod

    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(banner_mod.shutil, "which", lambda _name: None)

    assert play_formal_auth_alert() is False


def test_play_alert_returns_false_without_matching_sound_file(monkeypatch):
    """Player existe, mas nenhum caminho candidato existe no disco (ex.: CI headless)."""
    import core.banner as banner_mod

    monkeypatch.delenv("AGLOOP_AUTH_SOUND", raising=False)
    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(banner_mod.shutil, "which", lambda _name: "/usr/bin/paplay")
    monkeypatch.setattr(banner_mod.os.path, "isfile", lambda _path: False)

    assert play_formal_auth_alert() is False


def test_play_alert_plays_first_existing_candidate(monkeypatch):
    import core.banner as banner_mod

    monkeypatch.delenv("AGLOOP_AUTH_SOUND", raising=False)
    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(banner_mod.shutil, "which", lambda _name: "/usr/bin/paplay")
    monkeypatch.setattr(banner_mod.os.path, "isfile", lambda _path: True)

    calls = []
    monkeypatch.setattr(
        banner_mod.subprocess, "run", lambda cmd, **kw: calls.append(cmd)
    )

    assert play_formal_auth_alert() is True
    assert calls and calls[0][0] == "/usr/bin/paplay"


def test_play_alert_respects_custom_sound_override(monkeypatch):
    import core.banner as banner_mod

    monkeypatch.setenv("AGLOOP_AUTH_SOUND", "/tmp/custom.wav")
    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(banner_mod.shutil, "which", lambda _name: "/usr/bin/paplay")
    monkeypatch.setattr(banner_mod.os.path, "isfile", lambda path: path == "/tmp/custom.wav")

    calls = []
    monkeypatch.setattr(
        banner_mod.subprocess, "run", lambda cmd, **kw: calls.append(cmd)
    )

    assert play_formal_auth_alert() is True
    assert calls[0] == ["/usr/bin/paplay", "/tmp/custom.wav"]


def test_play_alert_never_raises_on_unexpected_exception(monkeypatch):
    import core.banner as banner_mod

    def boom(_name):
        raise OSError("simulated audio subsystem failure")

    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Linux")
    monkeypatch.setattr(banner_mod.shutil, "which", boom)

    assert play_formal_auth_alert() is False


def test_play_alert_uses_message_beep_on_windows(monkeypatch):
    import sys
    import types

    import core.banner as banner_mod

    fake_winsound = types.SimpleNamespace(MessageBeep=lambda *_a, **_kw: None, MB_ICONEXCLAMATION=1)
    monkeypatch.setitem(sys.modules, "winsound", fake_winsound)
    monkeypatch.setattr(banner_mod.platform, "system", lambda: "Windows")

    assert play_formal_auth_alert() is True
