# AgLoop

[![PyPI version](https://img.shields.io/pypi/v/agloop.svg)](https://pypi.org/project/agloop/)
[![CI](https://github.com/yuremarketing/AgLoop/actions/workflows/ci.yml/badge.svg)](https://github.com/yuremarketing/AgLoop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue.svg)](pyproject.toml)

🇧🇷 **[Leia em português](README.pt-BR.md)**

> "I'm the Product Owner; Claude and Gemini debate and ship under a governance protocol I designed."

**AgLoop** is a lightweight, serverless orchestration framework for heterogeneous AI agents (Claude, Gemini, and anything else [LiteLLM](https://docs.litellm.ai/) supports). Agents propose, debate, and agree on changes to your repository through a single Markdown file — no server, no database, no Docker. Git does the locking, Markdown does the talking, and a human Product Owner has the final word on production code.

## Why AgLoop

- **Heterogeneous by design** — mix Claude, Gemini, and any LiteLLM-supported model in the same War Room; each agent keeps its own identity and turn.
- **Zero-infra, local-first** — everything lives in your Git repo. No hosted service, no database, no new attack surface.
- **Git-based concurrency** — `git push`/`git pull` act as the lock. Whoever pushes first speaks first; the loser retries cleanly (`lost_race`), never a hard reset.
- **Human governance baked in** — a Product Owner authorizes every change to production code; agents debate freely but never bypass that gate.

## Installation

The only supported path is PyPI, plus the `stable` branch for editor plugins/extensions (see [ADR 0006](docs/arquitetura/decisoes/0006-distribuicao-segura-repositorio-publico-e-branch-stable.md) — `stable` only fast-forwards on a published release, never from an in-progress `main` commit):

```bash
pip install agloop
```

**Claude Code plugin** (self-hosted marketplace):
```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

**Gemini CLI extension**:
```bash
gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
```

Both expose the same MCP server (`core/mcp_server.py`) and the War Room slash commands (`/vigia`, `/status`, `/debate`). The plugin bundle lives in `plugin/` so installers receive only the distributed package, not the project's own governance files.

## Quick Start

```bash
cd my-project
agloop init          # scaffolds war_room.md, governance docs and protocol files
```

Then tell your agent: **"I installed AgLoop."** It runs the onboarding — briefing, roster, governance interview — until the Readiness Gate turns green:

```bash
agloop check         # deterministic, no LLM call — 🟢 or 🔴 with what's missing
```

Once 🟢, open your first turn (`/debate` in Claude Code, or write the proposal by hand) and let the agents debate up to 3 rounds (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) until `ACORDO`. You, as PO, authorize anything that touches production code.

## How the War Room works

A single Markdown file, `war_room.md`, is the IPC channel. Each agent writes under its own heading, proposes a plan, and a Tech Lead counterpart reviews it — all serialized through `git push`/`git pull` as the lock. Closed turns are archived to `HISTORICO.md`. The full protocol — role rotation, the 3-round debate cap, `PRÓXIMO-AGENTE:` routing, and the PR+CI gate for production code — is documented in the [User Guide](docs/manual/user-guide.md) and the canonical [`SKILL.md`](.claude/skills/vigilia/SKILL.md).

## Learn more

- 📘 [User Guide](docs/manual/user-guide.md) — installation to your first closed debate, in English.
- 📘 [Manual de Uso](docs/manual/manual-de-uso.md) — the same guide in Portuguese, with day-to-day usage and troubleshooting.
- 🏛️ [Governance & decisions](docs/gestao/) — roadmap, backlog, ADRs.
- 📜 [Closed turns (`HISTORICO.md`)](HISTORICO.md) — the project's own change log, written by the agents that shipped each change.

## Platform Support

Tested in CI on Linux, macOS and Windows (Python 3.10, 3.11, 3.12).

*Originated from the Sysoft project.*
