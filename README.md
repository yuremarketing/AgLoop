# AgLoop

**AgLoop** is a lightweight, Git-based orchestration framework for autonomous AI agents (like Claude and Gemini). It provides a robust, multi-agent loop system that relies on Git for process locking and Markdown for Inter-Process Communication (IPC).

## Core Concepts

- **Git-based Locking:** Uses standard `git push` and `git pull` as a reliable lock to manage agent concurrency across different machines or sessions.
- **Turn-based Execution:** Agents take "turns" executing work in an orchestrated manner, avoiding merge conflicts.
- **Markdown IPC:** The "War Room" (Sala de Guerra) approach where agents propose, debate, and agree on implementations via a single `.md` file.

*Originated from the Sysoft project.*

## Platform Support

Tested in CI on Linux, macOS and Windows (Python 3.10, 3.11, 3.12).

## Installation

```bash
pip install agloop
```

## Quick Start

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
