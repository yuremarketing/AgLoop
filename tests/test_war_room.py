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


# --------------------------------------------------------------------------- #
# append_message — idempotent header (Issue #44)
# --------------------------------------------------------------------------- #
def test_append_message_without_header_prepends_one(tmp_path):
    wr = _room(tmp_path, "# AgLoop War Room\n")
    wr.append_message("Claude", "hello from Claude")

    content = wr.read_all()
    assert content.count("## Claude") == 1
    assert "## Claude\n\nhello from Claude" in content


def test_append_message_with_matching_header_is_not_duplicated(tmp_path):
    wr = _room(tmp_path, "# AgLoop War Room\n")
    wr.append_message("Claude", "## Claude\n\n**Réplica**\n\nconteudo")

    content = wr.read_all()
    assert content.count("## Claude") == 1
    assert "**Réplica**" in content


def test_append_message_with_different_header_gets_its_own_prepended(tmp_path):
    """A stray '## OtherAgent' inside the body isn't mistaken for this agent's header."""
    wr = _room(tmp_path, "# AgLoop War Room\n")
    wr.append_message("Claude", "## Gemini\n\nquoting Gemini's header")

    content = wr.read_all()
    assert content.count("## Claude") == 1
    assert "## Claude\n\n## Gemini\n\nquoting Gemini's header" in content
