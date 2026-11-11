# AgLoop

**AgLoop** is a lightweight, Git-based orchestration framework for autonomous AI agents (like Claude and Gemini). It provides a robust, multi-agent loop system that relies on Git for process locking and Markdown for Inter-Process Communication (IPC).

> 📘 **Manual de Uso (PT-BR):** [`docs/manual/manual-de-uso.md`](docs/manual/manual-de-uso.md), da instalação ao primeiro debate fechado em `ACORDO`.

## Quick Install (Claude Code Plugin)

Install the full AgLoop plugin directly in Claude Code via the self-hosted GitHub marketplace:

```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

Once installed, use slash commands `/vigia`, `/status`, `/debate` and the built-in MCP server (`agloop`) directly in your sessions.

For local development or running the Python CLI:
```bash
pip install -e .
# or from PyPI:
pip install agloop
```

## Core Concepts

- **Git-based Locking:** Uses standard `git push` and `git pull` as a reliable lock to manage agent concurrency across different machines or sessions.
- **Turn-based Execution:** Agents take "turns" executing work in an orchestrated manner, avoiding merge conflicts.
- **Markdown IPC:** The "War Room" (Sala de Guerra) approach where agents propose, debate, and agree on implementations via a single `.md` file.

*Originated from the Sysoft project.*

## Platform Support

Tested in CI on Linux, macOS and Windows (Python 3.10, 3.11, 3.12).

## Python CLI Quick Start

Scaffold a clean `war_room.md` and governance templates in your repo:

```bash
agloop init
```

Run an agent loop (e.g. "Alice", a senior architect persona, debating with "Bob", a pragmatic developer persona):

```bash
agloop run --name Alice --model gemini/gemini-1.5-pro-latest
```

Other built-in commands:

```bash
agloop scan             # read-only scan of the repo structure
agloop audit --privacy  # LGPD-04 privacy diagnostic report
```

## Native Extensions & Plugins

Besides `pip install agloop`, the repo is natively installable inside the AI tools it orchestrates:

**Claude Code** (self-hosted plugin marketplace):
```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

**Gemini CLI** (direct extension install):
```bash
gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
```

Both install from the `stable` branch, which only ever advances by fast-forward when a new PyPI release ships (never from an in-progress `main` commit — see [ADR 0006](docs/arquitetura/decisoes/0006-distribuicao-segura-repositorio-publico-e-branch-stable.md)). Both expose the same MCP server (`core/mcp_server.py`) and the War Room slash commands. The Claude Code plugin bundle lives in `plugin/` (manifests, commands and scripts) so installers receive only the distributed package, not the project's War Room governance files; the self-hosted marketplace catalog (`.claude-plugin/marketplace.json`) stays at the repo root and points at `./plugin`. The Gemini CLI extension (`gemini-extension.json`) stays at the repo root.
