from core.war_room import WarRoom


def _room(tmp_path, content):
    path = tmp_path / "war_room.md"
    path.write_text(content, encoding="utf-8")
    return WarRoom(str(path))


def test_get_next_agent_returns_none_when_absent(tmp_path):
    wr = _room(tmp_path, "# AgLoop War Room\n\n## Alice\n\nhello\n")
    assert wr.get_next_agent() is None


def test_get_next_agent_returns_last_occurrence(tmp_path):
    wr = _room(
        tmp_path,
        "# AgLoop War Room\n\n"
        "## Alice\n\nPRÓXIMO-AGENTE: Bob\n\n"
        "## Bob\n\nPRÓXIMO-AGENTE: Carol\n",
    )
    assert wr.get_next_agent() == "Carol"


def test_get_next_agent_strips_whitespace(tmp_path):
    wr = _room(tmp_path, "# AgLoop War Room\n\nPRÓXIMO-AGENTE:   Gemini   \n")
    assert wr.get_next_agent() == "Gemini"


def test_get_next_agent_coexists_with_free_text_proximo(tmp_path):
    wr = _room(
        tmp_path,
        "# AgLoop War Room\n\nPRÓXIMO: aguardando revisão\nPRÓXIMO-AGENTE: Gemini\n",
    )
    assert wr.get_next_agent() == "Gemini"
