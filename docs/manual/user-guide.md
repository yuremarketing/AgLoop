# AgLoop User Guide

Full guide, from installation to your first agent debate closed with `ACORDO`.

> **Manual version:** 2026-11-13 · AgLoop `0.8.0`
> **Canonical protocol source:** [`.claude/skills/vigilia/SKILL.md`](../../.claude/skills/vigilia/SKILL.md). If this manual and `SKILL.md` disagree, `SKILL.md` wins.

> 🇧🇷 **[Leia em português](manual-de-uso.md)** — covers everything below plus day-to-day usage, multi-agent scenarios, governance/security detail and troubleshooting (§5–§8).

---

## Table of contents

1. [What is AgLoop](#1-what-is-agloop)
2. [Installation](#2-installation)
3. [First steps](#3-first-steps)
4. [Concepts](#4-concepts)
5. [FAQ](#5-faq)

> **Scope note:** this English edition covers installation, first steps and core concepts (Issue #58, phase 1). Day-to-day usage, multi-agent scenarios, governance/security detail and troubleshooting already exist in the Portuguese [Manual de Uso](manual-de-uso.md) (§5–§8) and will be translated in a follow-up pass.

---

## 1. What is AgLoop

AgLoop puts different AI agents (Claude, Gemini, and others) to **debate and work in turns** on the same repository, with no server:

- **Git** is the concurrency and transport mechanism: whoever pushes first speaks first.
- **Markdown** is the communication channel: a single file, `war_room.md` (the **War Room**), where agents propose, review, and close agreements.
- **A human (the PO)** has the final word on any change to production code.

It is **local-first** and **zero-infra**: no database, no Docker, no hosted service. Everything stays in your repository.

---

## 2. Installation

### 2.1 Requirements

- **Python** 3.10, 3.11, or 3.12 (tested in CI on Linux, macOS, and Windows)
- **Git**, with a remote (`origin`) configured if more than one machine or session will participate
- An **API key** for whichever LLM provider each agent will use (see §2.5)

### 2.2 As a Claude Code plugin (self-hosted marketplace)

Inside a Claude Code session:

```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

This installs the `/vigia`, `/status`, and `/debate` slash commands and the `agloop` MCP server. The MCP server imports the Python package, so install it too (§2.3). `#stable` pins the install to the branch that only advances by fast-forward on each published Release — it never points at a `main` commit from an open turn (see [ADR 0006](../arquitetura/decisoes/0006-distribuicao-segura-repositorio-publico-e-branch-stable.md)).

> AgLoop is **not** listed in Claude's official plugin directory: that directory only accepts local MCP servers and Python scripts from verified organizations. The self-hosted marketplace delivers the full plugin.

### 2.3 As a Python package (CLI)

```bash
pip install agloop
# or, from a clone of the repository:
pip install -e ".[dev]"
```

Installed commands: `agloop`, `agloop-vigia`, and `agloop-mcp`.

### 2.4 As a Gemini CLI extension

```bash
gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
```

Exposes the same MCP server (`core/mcp_server.py`). `--ref=stable` points at the same `stable` branch as §2.2, for the same reason.

### 2.5 API keys and environment variables

`agloop` loads a `.env` file at the project root (via `python-dotenv`). **Never** commit `.env`: the agent already refuses to read `.env`, `.env.*`, and `*.pem` (requirement `LGPD-01`).

| Variable | Purpose | Default |
| :--- | :--- | :--- |
| Provider key (e.g. `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) | Authenticates model calls, made via [LiteLLM](https://docs.litellm.ai/) | — |
| `LLM_TIMEOUT` | Max duration of a model call (s) | `60` |
| `LLM_MAX_RETRIES` | Retries on transient failure | `3` |
| `AGLOOP_LOCK_TIMEOUT` | Age (s) after which a local lock is considered abandoned | `300` |
| `AGLOOP_AGENT` | Default agent name for `agloop-vigia` | `Gemini` |
| `AGLOOP_STALL_MINUTES` | Minutes of inactivity before the vigília records `WAITING_HUMAN` (stall alarm) | `0` (off) |

---

## 3. First steps

### 3.1 Initialize governance in your repository

```bash
cd my-project
agloop init
```

Creates, **without overwriting existing files**:

- `war_room.md`: the War Room
- `HISTORICO.md`: the archive of closed turns
- `docs/gestao/roadmap.md`, `docs/gestao/backlog-produto.md`, `docs/gestao/matriz-riscos.md`
- `docs/gestao/roster-agentes.md`: who participates in the room and what each agent can produce (capability inventory)
- `AGENTS.md`: the entry point for **any** agent (Claude, Gemini, Codex, Cursor, Copilot, local models); points to the protocol
- `CLAUDE.md` and `GEMINI.md`: minimal files that just point to `AGENTS.md`
- `docs/arquitetura/decisoes/` (empty folder for ADRs)
- `.claude/skills/vigilia/SKILL.md`: the War Room protocol (roles, 3-round limit, `PRÓXIMO-AGENTE:`, PO boundaries, PR+CI gate), in a generic version for you to adapt to your project

At the end, `init` prints the next steps:

```
AgLoop: War Room created.

Next steps:
  1. git add war_room.md HISTORICO.md docs/ .claude/ && git commit -m "chore: initialize AgLoop" && git push
  2. Claude Code: /plugin marketplace add yuremarketing/AgLoop#stable && /plugin install agloop@agloop
     Gemini CLI:  gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
  3. Adjust .claude/skills/vigilia/SKILL.md (PO name and production-code boundaries).
  4. Tell your agent: "I installed AgLoop." It runs the onboarding.

User Guide: https://github.com/yuremarketing/AgLoop/blob/main/docs/manual/user-guide.md
```

- If every file already existed, `init` just prints a short reminder with the manual's link.
- For scripts and CI, use `agloop init -q` (or `--quiet`): only the file list is printed.

### 3.2 Onboarding and the Readiness Gate

After `init`, tell your agent: *"I installed AgLoop."* It follows the protocol's **Onboarding**:

1. reads the repository and gives you a **briefing** (what it found, what's missing);
2. introduces AgLoop in a few lines and asks permission to start;
3. asks which agents will participate and records the **roster and capabilities** of each one;
4. fills in governance **in conversation with you** (vision, PO, backlog with user stories and acceptance criteria, risks, etc.);
5. suggests support tools for each artifact, with explicit instructions (which tool, which sources, a ready-made prompt, where to save it in the repo).

While the **Readiness Gate** isn't 🟢, the agent does not write production code and **never offers to skip the protocol**. Pending items are marked in files with `<!-- AGLOOP_TODO: ... -->`. To check the Gate at any time (no LLM call, deterministic):

```bash
agloop check        # full report: 🔒 required and 📌 recommended, with what's missing
agloop check -q     # summary only, e.g. "Readiness Gate: 🔴 (4 blocking item(s))"
```

- Exits with code `0` when the Gate is 🟢 and `1` when it's 🔴, so it also works in CI.
- `agloop run` **refuses to run** while the Gate is 🔴. Bypass only in an emergency and with explicit PO authorization: `agloop run --force-bypass-gate ...`.
- On a freshly initialized repository the result is 🔴, as expected: Onboarding exists precisely to get you to 🟢.

### 3.3 Protocol updates and version notice (`agloop update`)

When a new AgLoop release brings changes to the protocol files (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), the Readiness Gate (`agloop check`) shows a recommended 📌 item flagging the drift.

You can inspect and update the files with full safety:

```bash
agloop update --dry-run   # previews the unified diff without touching files
agloop update --yes       # applies the updates, creating automatic (.bak) backups
```

- **Replace with backup (.bak):** `agloop update` updates protocol files by replacing them with the new version's templates and creating a `.bak` copy of the original file in the same directory. It does **not** do automatic (3-way) merging. If your `SKILL.md` or protocol file has deep local customization (e.g. PO names, project-specific sections), always run `agloop update --dry-run` first and reapply your customizations from the `.bak` copy.
- **Filled-in governance is immutable:** completed governance documents (`roadmap.md`, `backlog-produto.md`, `matriz-riscos.md`) are **never** touched by update. `roster-agentes.md` is only created if it didn't already exist.
- **Interactive transparency:** running `agloop update` without `--yes` shows the unified diff for each file before asking for explicit confirmation.
- **Non-intrusive PyPI notice:** when running commands like `agloop init`, `agloop check`, or `agloop update`, if a newer package version is published on PyPI, a fail-silent informational line appears at the end:
  `💡 AgLoop: version X.Y.Z available (installed: A.B.C). Upgrade: pip install --upgrade agloop`
  *(automatically disabled in CI environments, or via `AGLOOP_NO_UPDATE_CHECK=1`)*.

### 3.4 Explore the project (read-only)

```bash
agloop scan
```

Lists the repository structure and recognized stack manifests (`pyproject.toml`, `package.json`, `go.mod`, `Dockerfile`, etc.). Doesn't change anything.

### 3.5 Run your first debate

1. Commit and push the `war_room.md` generated by `init`.
2. In one session (e.g. Claude Code), ask the agent to open a turn with `/debate`, or write the proposal in the format from §4.3.
3. In the other agent's session, start the vigília (see the Portuguese manual, §5.3). It wakes the agent up when it's their turn.
4. Agents exchange at most 3 rounds (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) until `ACORDO`.
5. You, as PO, authorize whatever touches production code.

---

## 4. Concepts

### 4.1 The War Room (`war_room.md`)

A single Markdown file where all the debate happens. Each participant writes under a heading with their own name (`## Claude`, `## Gemini`). Closed turns move to `HISTORICO.md`.

### 4.2 Roles (rotate every turn)

| Role | What it does |
| :--- | :--- |
| **Specialist Dev** | Opens the turn (`<!--INICIANDO_TURNO-->`), proposes, implements after agreement, and submits for audit |
| **Tech Lead** | Reviews the proposal, audits the diff and tests, and approves (`STATUS: ACORDO`) |
| **Observer** | In rooms with 3+ agents: stays silent and only speaks if addressed via `PRÓXIMO-AGENTE:` or called by the PO |
| **PO (human)** | Authorizes changes to production code and breaks ties on debates that don't converge |

### 4.3 Turn format

```markdown
<!--INICIANDO_TURNO-->
Início: YYYY-MM-DD HH:MM · Commit-base: <hash> · Agente: <Name> · <Short title>
Roster do Turno N: <Dev> (Dev Especialista) · <TL> (Tech Lead) · <others> (Observadores)

## Turno N — <Agent> (YYYY-MM-DD)

## <Agent>

**Proposta — <Agent> (Dev Especialista)**
...
STATUS: PROPOSTA
PRÓXIMO: <next step, free text>
PRÓXIMO-AGENTE: <name of who should act>
```

The `Roster` line is only required with 3 or more participants.

### 4.4 `STATUS`

| Value | Meaning |
| :--- | :--- |
| `PROPOSTA` / `RÉPLICA` / `TRÉPLICA` | Debate rounds (maximum 3) |
| `ACORDO` | Consensus closed by the Tech Lead |
| `FEITO` | Documentation-only implementation finished, awaiting audit |
| `PR_ABERTO` | Production-code change submitted via Pull Request |
| `CONCLUIDO` | Turn closed |
| `WAITING_HUMAN` | Paused: awaiting a PO decision |

Special markers read by the code: `<!-- AGLOOP_STATE: CONSENSUS -->` and `<!-- AGLOOP_STATE: WAITING_HUMAN -->` pause inference; `<!--FIM_TURNO-->` closes the turn and triggers archival.

### 4.5 `PRÓXIMO:` vs. `PRÓXIMO-AGENTE:`

- `PRÓXIMO:` is **free text**, for humans and LLMs to understand context.
- `PRÓXIMO-AGENTE:` is **read by code** (`WarRoom.get_next_agent()`) and decides **who wakes up**. Only the named agent wakes; the others keep sleeping, spending no tokens.
- Without `PRÓXIMO-AGENTE:`, the legacy behavior wakes **any agent that wasn't the last speaker**. In rooms with 3+ agents that wakes two agents at once, so the field is **mandatory** there.

### 4.6 The 3-round limit

Without convergence after `TRÉPLICA`, the debate escalates to the PO. This prevents infinite loops and unbounded token spend.

### 4.7 Multiple tasks per turn (Issue #57)

A turn can contain **more than one task**, as long as they're independent (don't touch the same files/modules). Each task gets an identifier `T<turn>.<n>` (e.g. `T42.1`), cited in `TAREFA:` alongside `STATUS:`; with more than one open task, `PRÓXIMO-AGENTE:` lists each agent next to its task (`Gemini (T42.1); Claude (T42.2)`). PO authorization (§7.1 of the Portuguese manual) and the 3-round limit apply **per task**, not per turn, and the turn only closes once every task is `ACORDO` or explicitly deferred. Tracking which issue/PR/file belongs to which turn/task lives in [`docs/gestao/matriz-rastreabilidade.md`](../gestao/matriz-rastreabilidade.md) — no longer scattered across the backlog, the Artefato Mestre, and `HISTORICO.md`. Full, current rule: [`SKILL.md`](../../.claude/skills/vigilia/SKILL.md).

---

## 5. FAQ

**Does the vigília spend tokens?**
No. It's a plain script that only checks file timestamps and runs `git fetch`. Tokens are only spent when the agent wakes up to respond.

**Do I need Docker?**
No. AgLoop is zero-infra by design.

**Can I use models other than Claude and Gemini?**
Yes. Any model supported by LiteLLM, by passing `--model provider/model`.

**Who has the final say?**
The PO. Agents debate and implement; changes to production code only land with their explicit approval.

**Where can I see what's already been decided?**
In `HISTORICO.md` (closed turns) and the Decision Log in [`docs/gestao/artefatos/artefato-mestre-agloop.md`](../gestao/artefatos/artefato-mestre-agloop.md).

---

For day-to-day usage (`agloop run`, slash commands, the hybrid vigília in full, MCP server tools, privacy audit), multi-agent scenarios, the full governance/security rules, and troubleshooting, see the Portuguese [Manual de Uso](manual-de-uso.md), §5 through §8.
