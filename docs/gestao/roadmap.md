# Roadmap do Produto — AgLoop

Cronograma orientado a marcos estratégicos (sem datas rígidas de longo prazo, seguindo a cadência de turnos da Sala de Guerra conforme padrão **Sysoft**).

---

## Visão Geral dos Marcos (Milestones)

| Marco | Nome | Escopo Principal | Issues Vinculadas | Status |
| :---: | :--- | :--- | :---: | :---: |
| **M1** | **Fundação Core & Vigília Híbrida** | Lock local atômico (`.agloop.lock`) com recuperação de stale lock, commits escopados ao War Room, reversão cirúrgica sem `reset --hard`, Vigília Híbrida (`mtime` + `git fetch` com backoff/jitter) e suíte `pytest`. | [#1](https://github.com/yuremarketing/AgLoop/issues/1) | ✅ **Concluído** |
| **M2** | **Governança Padrão Sysoft & Saneamento DRY** | Implantação de `docs/gestao/` (TAP, Artefato Mestre, Matriz de Riscos, Roadmap, Backlog, Glossário, Requisitos), ADRs `0001`–`0005`, SSOT em `.claude/skills/vigilia/SKILL.md`, `CLAUDE.md`/`GEMINI.md` enxutos, autoria Git isolada por agente, fechamento/arquivamento atômico (`HISTORICO.md`) e wrapper `vigia.py --once`. | [#3](https://github.com/yuremarketing/AgLoop/issues/3) | ✅ **Concluído (Turnos 1 e 2)** |
| **M3** | **Motor Cognitivo Google ADK & Controle de Consenso** | Evolução de `core/agent.py` integrando `google-adk` (`LlmAgent` + `LiteLlm`), ferramentas nativas somente-leitura (`read_file`, `list_dir`, `git_diff`, `run_pytest`), protocolo de parada por consenso/pausa humana (`WAITING_HUMAN` / `CONSENSUS`), janela deslizante no `WarRoom` e empacotamento `pyproject.toml` (`agloop`). | [#4](https://github.com/yuremarketing/AgLoop/issues/4) | ✅ **Concluído (Turno 4)** |
| **M4** | **Plugin Oficial Claude Code & Antigravity + Camada MCP** | Empacotamento `.claude-plugin/plugin.json`, Slash Commands (`/agloop:vigia`, `/agloop:status`, `/agloop:debate`), servidor MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`) e Hooks de sincronização. | [#2](https://github.com/yuremarketing/AgLoop/issues/2) | 📋 **Planejado (Próximo)** |
| **M5** | **Gate de PR+CI Antes do Merge na Main** | Branch de feature por turno técnico, workflow de CI (GitHub Actions) rodando `pytest` em cada PR, aprovação do Tech Lead via `gh pr review --approve` só com CI verde — port do padrão de rigor já validado no Sysoft. | [#5](https://github.com/yuremarketing/AgLoop/issues/5) | 📋 **Planejado** |

---

## Critérios de Saída por Marco

### M1 — Fundação Core & Vigília Híbrida (Concluído em 2026-10-22)
- [x] `GitLock` com `.agloop.lock` atômico e recuperação por PID/host/timeout.
- [x] Eliminação total de `git add -A` e `git reset --hard HEAD~1`.
- [x] `Runner` com separação entre `local_poll_interval` e `remote_poll_interval`.
- [x] Testes unitários e de integração (`tests/test_git_lock.py`, `tests/test_runner.py`) 100% verdes.

### M2 — Governança Padrão Sysoft & Saneamento DRY (Concluído em 2026-11-02 — Turnos 1 e 2)
- [x] Criação da árvore `docs/gestao/` (`termo-abertura.md`, `artefatos/artefato-mestre-agloop.md`, `matriz-riscos.md`, `roadmap.md`, `backlog-produto.md`, `glossario.md`, `concepcao-e-elicitacao-requisitos.md`).
- [x] Criação das 5 ADRs iniciais em `docs/arquitetura/decisoes/`.
- [x] Criação de `.claude/skills/vigilia/SKILL.md` (SSOT) + `CLAUDE.md` e `GEMINI.md` enxutos.
- [x] Implementação em `core/` e `scripts/` (autorizada pelo PO Yure Mark): autoria Git isolada (`GIT_AUTHOR_*`/`GIT_COMMITTER_*`), `close_turn_and_archive` atômico (`HISTORICO.md`) e wrapper DRY `scripts/vigia.py --once` + 26 testes verdes.

### M3 — Motor Cognitivo Google ADK & Controle de Consenso (Concluído em 2026-11-03 — Turnos 3 e 4)
- [x] Janela deslizante `WarRoom.read_recent(max_turns=N)` preservando retrocompatibilidade.
- [x] Detecção de `<!-- AGLOOP_STATE: WAITING_HUMAN -->` e `<!-- AGLOOP_STATE: CONSENSUS -->` no `Runner`.
- [x] `Agent` baseado em `google-adk` + `LiteLlm` com tools seguras de inspeção (`read_file`, `list_dir`, `git_diff`, `run_pytest`), confinamento `os.path.commonpath` (`LGPD-01`) e sanitização de PII (`LGPD-02`).
- [x] `pyproject.toml` com CLI `agloop` e `agloop-vigia` + 34 testes verdes.

### M4 — Plugin Oficial & Servidor MCP
- [ ] Manifesto `.claude-plugin/plugin.json` e comandos slash.
- [ ] Servidor MCP expondo operações estruturadas da Sala de Guerra.
