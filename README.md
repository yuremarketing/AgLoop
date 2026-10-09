# AgLoop

**AgLoop** is a lightweight, Git-based orchestration framework for autonomous AI agents (like Claude and Gemini). It provides a robust, multi-agent loop system that relies on Git for process locking and Markdown for Inter-Process Communication (IPC).

## Core Concepts

- **Git-based Locking:** Uses standard `git push` and `git pull` as a reliable lock to manage agent concurrency across different machines or sessions.
- **Turn-based Execution:** Agents take "turns" executing work in an orchestrated manner, avoiding merge conflicts.
- **Markdown IPC:** The "War Room" (Sala de Guerra) approach where agents propose, debate, and agree on implementations via a single `.md` file.

*Originated from the Sysoft project.*
