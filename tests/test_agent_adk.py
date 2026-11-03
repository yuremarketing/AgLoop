from types import SimpleNamespace

from core import agent as agent_mod
from core.agent import (
    Agent,
    git_diff,
    list_dir,
    read_file,
    run_pytest,
    sanitize_prompt_pii,
)


def test_sanitize_prompt_pii_masks_cpf_tokens_and_external_emails():
    raw = (
        "CPF: 123.456.789-00 | "
        "OpenAI: sk-proj1234567890abcdef1234 | "
        "GitHub: ghp_1234567890abcdefghij12345 | "
        "Personal: cliente.real@empresa.com.br | "
        "Synthetic: claude@agloop.local and gemini@AGLOOP.LOCAL"
    )
    cleaned = sanitize_prompt_pii(raw)
    assert "123.456.789-00" not in cleaned
    assert "[CPF_REDACTED]" in cleaned
    assert "sk-proj1234567890abcdef1234" not in cleaned
    assert "ghp_1234567890abcdefghij12345" not in cleaned
    assert "[SECRET_REDACTED]" in cleaned
    assert "cliente.real@empresa.com.br" not in cleaned
    assert "[EMAIL_REDACTED]" in cleaned
    assert "claude@agloop.local" in cleaned
    assert "gemini@AGLOOP.LOCAL" in cleaned


def test_read_file_blocks_sensitive_files_and_outside_workspace(tmp_path):
    repo = tmp_path / "AgLoop"
    repo.mkdir()
    sibling = tmp_path / "AgLoopEvil"
    sibling.mkdir()

    (repo / ".env").write_text("API_KEY=secret", encoding="utf-8")
    (repo / "id_rsa").write_text("PRIVATE KEY", encoding="utf-8")
    (repo / "safe.txt").write_text("Hello world\n", encoding="utf-8")
    (sibling / "leak.txt").write_text("Sibling secret", encoding="utf-8")

    # LGPD-01 blacklist
    assert "Access denied" in read_file(".env", repo_root=str(repo))
    assert "Access denied" in read_file("id_rsa", repo_root=str(repo))

    # Path traversal and sibling prefix attack (`AgLoopEvil` vs `AgLoop`)
    assert "Access denied" in read_file("../AgLoopEvil/leak.txt", repo_root=str(repo))

    # Legitimate file works
    assert read_file("safe.txt", repo_root=str(repo)) == "Hello world"


def test_list_dir_hides_sensitive_entries_and_blocks_outside(tmp_path):
    repo = tmp_path / "AgLoop"
    repo.mkdir()
    (repo / ".env").write_text("SECRET=1", encoding="utf-8")
    (repo / "README.md").write_text("# Doc", encoding="utf-8")

    listing = list_dir(".", repo_root=str(repo))
    assert "README.md" in listing
    assert ".env" not in listing
    assert "Access denied" in list_dir("..", repo_root=str(repo))


def test_git_diff_and_run_pytest_reject_flags_and_escape(tmp_path):
    repo = tmp_path / "AgLoop"
    repo.mkdir()
    (repo / "tests").mkdir()

    assert "Access denied" in git_diff("--output=/tmp/pwn", repo_root=str(repo))
    assert "Access denied" in run_pytest("--version", repo_root=str(repo))
    assert "Access denied" in run_pytest("../outside", repo_root=str(repo))


def test_agent_sanitizes_context_before_calling_litellm(monkeypatch):
    captured = {}

    def fake_completion(model, messages):
        captured["model"] = model
        captured["messages"] = messages
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Ack from LLM"))]
        )

    monkeypatch.setattr(agent_mod.litellm, "completion", fake_completion)
    ag = Agent(name="Gemini", role_prompt="Tech Lead", model="gemini/test", use_adk=False)
    reply = ag.generate_response("User CPF 111.222.333-44 and email user@gmail.com")

    assert reply == "Ack from LLM"
    user_msg = captured["messages"][1]["content"]
    assert "111.222.333-44" not in user_msg
    assert "user@gmail.com" not in user_msg
    assert "[CPF_REDACTED]" in user_msg
    assert "[EMAIL_REDACTED]" in user_msg
    assert len(ag.tools) == 4


def test_agent_invokes_adk_runner_when_adk_enabled(monkeypatch):
    adk_calls = {}

    class FakeLiteLlm:
        def __init__(self, model):
            self.model = model

    class FakeLlmAgent:
        def __init__(self, name, model, instruction, tools):
            self.name = name
            self.model = model
            self.instruction = instruction
            self.tools = tools

    class FakeInMemoryRunner:
        def __init__(self, agent, app_name):
            adk_calls["agent"] = agent
            adk_calls["app_name"] = app_name

        def run_text(self, prompt):
            adk_calls["prompt"] = prompt
            return "ADK response after using tools"

    monkeypatch.setattr(agent_mod, "ADK_AVAILABLE", True)
    monkeypatch.setattr(agent_mod, "LiteLlm", FakeLiteLlm)
    monkeypatch.setattr(agent_mod, "LlmAgent", FakeLlmAgent)
    monkeypatch.setattr(agent_mod, "InMemoryRunner", FakeInMemoryRunner)

    ag = Agent(name="Claude", role_prompt="Tech Lead", model="anthropic/claude", use_adk=True)
    assert ag.adk_agent is not None
    assert len(ag.adk_agent.tools) == 4

    out = ag.think_and_act("Check CPF 999.888.777-66 in context")
    assert out == "ADK response after using tools"
    assert adk_calls["agent"] is ag.adk_agent
    assert "[CPF_REDACTED]" in adk_calls["prompt"]
    assert "999.888.777-66" not in adk_calls["prompt"]


def test_agent_executes_tool_calls_in_litellm_loop(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    (tmp_path / "notes.txt").write_text("Important architecture note", encoding="utf-8")

    rounds = {"n": 0}
    seen_messages = []

    def fake_completion(model, messages, tools=None):
        rounds["n"] += 1
        seen_messages.append(list(messages))
        if rounds["n"] == 1:
            tc = SimpleNamespace(
                id="call_read_1",
                function=SimpleNamespace(name="read_file", arguments='{"filepath": "notes.txt"}'),
            )
            return SimpleNamespace(
                choices=[SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[tc]))]
            )
        return SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="Verified notes.txt content!", tool_calls=None))]
        )

    monkeypatch.setattr(agent_mod.litellm, "completion", fake_completion)
    ag = Agent(name="Gemini", role_prompt="Dev", model="gemini/test", use_adk=False)
    result = ag.think_and_act("Please inspect notes.txt")

    assert result == "Verified notes.txt content!"
    assert rounds["n"] == 2
    tool_msg = seen_messages[1][-1]
    assert tool_msg["role"] == "tool"
    assert tool_msg["name"] == "read_file"
    assert "Important architecture note" in tool_msg["content"]

