# AgLoop (Claude Code Plugin)

**AgLoop** is a lightweight, Git-based orchestration framework for autonomous AI agents (like Claude and Gemini). This plugin bundles the Claude Code integration for the AgLoop "War Room" protocol: multi-agent debate and consensus over a single `war_room.md` file, using Git as the concurrency lock.

## What this plugin does

- **MCP server** (`agloop`): exposes `read_war_room`, `post_war_room_message` and `get_lock_status` tools, restricted to `war_room.md`/`HISTORICO.md` in the active project.
- **SessionStart hook**: prints a one-line War Room status (state and last speaker) when a session starts in a project that has one.
- **Slash commands**: `/vigia`, `/status`, `/debate` — guide an agent through opening or responding to a formal turn in the War Room.

## Data handling

- Runs entirely locally. It reads and writes only `war_room.md` and `HISTORICO.md` inside the active project's working directory.
- No data is sent to any server other than the LLM API you're already using in your session.
- PII (emails, CPFs) is sanitized before being included in any LLM prompt by the agent-side code (`core.agent.sanitize_prompt_pii`), not by this plugin itself.

## Requirements

This plugin's MCP server and hook run Python and import the `agloop` package, so it must be installed in the environment running Claude Code:

```bash
pip install agloop
```

## Source

Full source, the orchestration engine (`core/`), and governance docs live at the project root: https://github.com/yuremarketing/AgLoop
