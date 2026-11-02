# Backlog do Produto — AgLoop

Registro priorizado dos épicos e histórias técnicas do **AgLoop**, mantendo rastreabilidade direta com as Issues do repositório [`yuremarketing/AgLoop`](https://github.com/yuremarketing/AgLoop/issues) e com as ADRs em [`docs/arquitetura/decisoes/`](../arquitetura/decisoes/).

---

## Ordem de Priorização (Sequenciamento Oficial)

`E01 (Concluído)` → `E02 (Governança & DRY — Em andamento)` → `E03 (Google ADK & Consenso)` → `E04 (Plugin & MCP)`

---

## Detalhamento dos Épicos

### E01 — Sincronização Git Resiliente e Vigília Híbrida ([Issue #1](https://github.com/yuremarketing/AgLoop/issues/1))
- **Status:** ✅ Concluído (Commit `2e5cc85`)
- **ADRs:** [ADR 0001](../arquitetura/decisoes/0001-ipc-markdown-e-git-serverless-broker.md), [ADR 0002](../arquitetura/decisoes/0002-lock-hibrido-atomico-e-reversao-cirurgica-lost-race.md), [ADR 0003](../arquitetura/decisoes/0003-vigilia-hibrida-mtime-local-e-fetch-remoto.md)
- **Entregas:**
  - [x] `E01.1` — Lock local atômico via `.agloop.lock` com `owner.json` (`pid`, `host`, `ts`) e recuperação de stale lock.
  - [x] `E01.2` — Commits escopados apenas aos caminhos da Sala de Guerra (`war_room.md`).
  - [x] `E01.3` — Resolução não-destrutiva de `lost_race` (`reset --soft HEAD~1` + `checkout HEAD -- <paths>`).
  - [x] `E01.4` — Vigília Híbrida no `core/runner.py` (`mtime` local barato + `git fetch` remoto com backoff/jitter).
  - [x] `E01.5` — Suíte de testes automatizados (`tests/test_git_lock.py`, `tests/test_runner.py`).

---

### E02 — Governança Padrão Sysoft, Matriz de Riscos, ADRs e Saneamento DRY ([Issue #3](https://github.com/yuremarketing/AgLoop/issues/3))
- **Status:** 🔄 Em andamento (Turno 1)
- **ADR:** [ADR 0004](../arquitetura/decisoes/0004-governanca-dry-ssot-autoria-e-fechamento-atomico.md)
- **Entregas Documentais (Delegadas — Concluídas no Turno 1):**
  - [x] `E02.1` — Fonte Única da Verdade do protocolo em `.claude/skills/vigilia/SKILL.md` e ponteiros enxutos em `CLAUDE.md` / `GEMINI.md`.
  - [x] `E02.2` — Termo de Abertura (`docs/gestao/termo-abertura.md`) e Artefato Mestre (`docs/gestao/artefatos/artefato-mestre-agloop.md`).
  - [x] `E02.3` — Matriz de Riscos (`docs/gestao/matriz-riscos.md`) cobrindo `R01`–`R08`.
  - [x] `E02.4` — ADRs fundacionais `0001` a `0005` em `docs/arquitetura/decisoes/`.
- **Entregas de Código (Aguardando aprovação do PO Yure Mark para tocar `core/` e `scripts/`):**
  - [ ] `E02.5` — Parametrizar `author_name`/`author_email` em `GitLock.commit()` injetando `GIT_AUTHOR_*` e `GIT_COMMITTER_*` de forma isolada no ambiente do subprocesso Git.
  - [ ] `E02.6` — Implementar `close_turn_and_archive()` em `core/war_room.py` acoplado aos marcadores `<!--FIM_TURNO-->` / `CONSENSUS`, arquivando turnos antigos em `HISTORICO.md` em commit único atômico.
  - [ ] `E02.7` — Refatorar `scripts/vigia.py` como thin wrapper DRY de `core/runner.py` com suporte a `--agent` e `--once` (`exit 0` ao mudar o orador).
  - [ ] `E02.8` — Novos testes em `tests/` validando autoria Git isolada e arquivamento atômico.

---

### E03 — Motor Cognitivo Google ADK, Tools Seguras e Controle de Consenso ([Issue #4](https://github.com/yuremarketing/AgLoop/issues/4))
- **Status:** 📋 Planejado (Marco M3)
- **ADR:** [ADR 0005](../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md)
- **Entregas:**
  - [ ] `E03.1` — Janela deslizante `WarRoom.read_recent(max_turns=6)` mantendo retrocompatibilidade de `read_all()`.
  - [ ] `E03.2` — Protocolo de consenso e pausa humana (`<!-- AGLOOP_STATE: WAITING_HUMAN -->` e `<!-- AGLOOP_STATE: CONSENSUS -->`) no `core/runner.py`.
  - [ ] `E03.3` — Integração de `google-adk` (`LlmAgent` + `LiteLlm`) em `core/agent.py` com tools seguras somente-leitura (`read_file`, `list_dir`, `git_diff`, `run_pytest`).
  - [ ] `E03.4` — Empacotamento moderno via `pyproject.toml` expondo o comando CLI `agloop` e suporte a `adk web`.

---

### E04 — Plugin Oficial Claude Code & Antigravity + Servidor MCP ([Issue #2](https://github.com/yuremarketing/AgLoop/issues/2))
- **Status:** 📋 Planejado (Marco M4)
- **ADR:** [ADR 0005](../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md)
- **Entregas:**
  - [ ] `E04.1` — Manifesto `.claude-plugin/plugin.json` e comandos slash (`commands/vigia.md`, `commands/status.md`, `commands/debate.md`).
  - [ ] `E04.2` — Servidor MCP (`mcp_server.py` + `.mcp.json`) expondo `read_war_room`, `post_war_room_message` e `get_lock_status`.
  - [ ] `E04.3` — Hooks de eventos (`hooks/hooks.json`) para verificação pós-fetch.
