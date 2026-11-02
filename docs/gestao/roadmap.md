# Roadmap do Produto — AgLoop

Cronograma orientado a marcos estratégicos (sem datas rígidas de longo prazo, seguindo a cadência de turnos da Sala de Guerra conforme padrão **Sysoft**).

---

## Visão Geral dos Marcos (Milestones)

| Marco | Nome | Escopo Principal | Issues Vinculadas | Status |
| :---: | :--- | :--- | :---: | :---: |
| **M1** | **Fundação Core & Vigília Híbrida** | Lock local atômico (`.agloop.lock`) com recuperação de stale lock, commits escopados ao War Room, reversão cirúrgica sem `reset --hard`, Vigília Híbrida (`mtime` + `git fetch` com backoff/jitter) e suíte `pytest`. | [#1](https://github.com/yuremarketing/AgLoop/issues/1) | ✅ **Concluído** |
| **M2** | **Governança Padrão Sysoft & Saneamento DRY** | Implantação de `docs/gestao/` (TAP, Artefato Mestre, Matriz de Riscos, Roadmap, Backlog), ADRs `0001`–`0005`, SSOT em `.claude/skills/vigilia/SKILL.md`, `CLAUDE.md`/`GEMINI.md` enxutos, autoria Git isolada por agente, fechamento/arquivamento atômico (`HISTORICO.md`) e wrapper `vigia.py --once`. | [#3](https://github.com/yuremarketing/AgLoop/issues/3) | 🔄 **Em Execução (Turno 1)** |
| **M3** | **Motor Cognitivo Google ADK & Controle de Consenso** | Evolução de `core/agent.py` integrando `google-adk` (`LlmAgent` + `LiteLlm`), ferramentas nativas somente-leitura (`read_file`, `list_dir`, `git_diff`, `run_pytest`), protocolo de parada por consenso/pausa humana (`WAITING_HUMAN` / `CONSENSUS`), janela deslizante no `WarRoom` e empacotamento `pyproject.toml` (`agloop`). | [#4](https://github.com/yuremarketing/AgLoop/issues/4) | 📋 **Planejado (Próximo)** |
| **M4** | **Plugin Oficial Claude Code & Antigravity + Camada MCP** | Empacotamento `.claude-plugin/plugin.json`, Slash Commands (`/agloop:vigia`, `/agloop:status`, `/agloop:debate`), servidor MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`) e Hooks de sincronização. | [#2](https://github.com/yuremarketing/AgLoop/issues/2) | 📋 **Planejado** |

---

## Critérios de Saída por Marco

### M1 — Fundação Core & Vigília Híbrida (Concluído em 2026-10-22)
- [x] `GitLock` com `.agloop.lock` atômico e recuperação por PID/host/timeout.
- [x] Eliminação total de `git add -A` e `git reset --hard HEAD~1`.
- [x] `Runner` com separação entre `local_poll_interval` e `remote_poll_interval`.
- [x] Testes unitários e de integração (`tests/test_git_lock.py`, `tests/test_runner.py`) 100% verdes.

### M2 — Governança Padrão Sysoft & Saneamento DRY (Em andamento — Turno 1)
- [x] Criação da árvore `docs/gestao/` (`termo-abertura.md`, `artefatos/artefato-mestre-agloop.md`, `matriz-riscos.md`, `roadmap.md`, `backlog-produto.md`).
- [x] Criação das 5 ADRs iniciais em `docs/arquitetura/decisoes/`.
- [x] Criação de `.claude/skills/vigilia/SKILL.md` (SSOT) + `CLAUDE.md` e `GEMINI.md` enxutos.
- [ ] Implementação em `core/` e `scripts/` (após aprovação do PO Yure Mark): autoria Git isolada (`GIT_AUTHOR_*`/`GIT_COMMITTER_*`), `close_turn_and_archive` atômico (`HISTORICO.md`) e wrapper DRY `scripts/vigia.py --once`.

### M3 — Motor Cognitivo Google ADK & Controle de Consenso
- [ ] Janela deslizante `WarRoom.read_recent(max_turns=N)` preservando retrocompatibilidade.
- [ ] Detecção de `<!-- AGLOOP_STATE: WAITING_HUMAN -->` e `<!-- AGLOOP_STATE: CONSENSUS -->` no `Runner`.
- [ ] `Agent` baseado em `google-adk` + `LiteLlm` com tools seguras de inspeção.
- [ ] `pyproject.toml` com CLI `agloop`.

### M4 — Plugin Oficial & Servidor MCP
- [ ] Manifesto `.claude-plugin/plugin.json` e comandos slash.
- [ ] Servidor MCP expondo operações estruturadas da Sala de Guerra.
