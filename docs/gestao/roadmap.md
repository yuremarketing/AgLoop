# Roadmap do Produto — AgLoop

Cronograma orientado a marcos estratégicos (sem datas rígidas de longo prazo, seguindo a cadência de turnos da Sala de Guerra conforme padrão **Sysoft**).

---

## Visão Geral dos Marcos (Milestones)

| Marco | Nome | Escopo Principal | Issues Vinculadas | Status |
| :---: | :--- | :--- | :---: | :---: |
| **M1** | **Fundação Core & Vigília Híbrida** | Lock local atômico (`.agloop.lock`) com recuperação de stale lock, commits escopados ao War Room, reversão cirúrgica sem `reset --hard`, Vigília Híbrida (`mtime` + `git fetch` com backoff/jitter) e suíte `pytest`. | [#1](https://github.com/yuremarketing/AgLoop/issues/1) | ✅ **Concluído** |
| **M2** | **Governança Padrão Sysoft & Saneamento DRY** | Implantação de `docs/gestao/` (TAP, Artefato Mestre, Matriz de Riscos, Roadmap, Backlog, Glossário, Requisitos), ADRs `0001`–`0005`, SSOT em `.claude/skills/vigilia/SKILL.md`, `CLAUDE.md`/`GEMINI.md` enxutos, autoria Git isolada por agente, fechamento/arquivamento atômico (`HISTORICO.md`) e wrapper `vigia.py --once`. | [#3](https://github.com/yuremarketing/AgLoop/issues/3) | ✅ **Concluído (Turnos 1 e 2)** |
| **M3** | **Motor Cognitivo Google ADK & Controle de Consenso** | Evolução de `core/agent.py` integrando `google-adk` (`LlmAgent` + `LiteLlm`), ferramentas nativas somente-leitura (`read_file`, `list_dir`, `git_diff`, `run_pytest`), protocolo de parada por consenso/pausa humana (`WAITING_HUMAN` / `CONSENSUS`), janela deslizante no `WarRoom` e empacotamento `pyproject.toml` (`agloop`). | [#4](https://github.com/yuremarketing/AgLoop/issues/4) | ✅ **Concluído (Turno 4)** |
| **M4** | **Plugin Oficial Claude Code & Antigravity + Camada MCP** | Empacotamento `.claude-plugin/plugin.json`, Slash Commands (`/agloop:vigia`, `/agloop:status`, `/agloop:debate`), servidor MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`) e Hooks de sincronização. | [#2](https://github.com/yuremarketing/AgLoop/issues/2) | ✅ **Concluído (Turno 6)** |
| **M5** | **Gate de PR+CI Antes do Merge na Main** | Branch de feature por turno técnico, workflow de CI (GitHub Actions) rodando `pytest` em cada PR na matriz 3.10/3.11/3.12, aprovação do Tech Lead via `gh pr review --approve` só com CI verde — port do padrão de rigor já validado no Sysoft. | [#5](https://github.com/yuremarketing/AgLoop/issues/5) | ✅ **Concluído (Turno 7, PR #7)** |
| **M6** | **Productização do AgLoop** | Empacotamento PyPI (`pip install agloop` v0.6.0, MIT), scaffolding de governança (`agloop init`) com templates limpos e varredura segura de repositórios (`agloop scan` + MCP). | [#8](https://github.com/yuremarketing/AgLoop/issues/8) | ✅ **Concluído (Turnos 8 e 9, PRs #9 e #10)** |

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

### M4 — Plugin Oficial & Servidor MCP (Concluído em 2026-11-03 — Turno 6)
- [x] Manifesto `.claude-plugin/plugin.json`, `.mcp.json`, hooks e slash commands (`commands/{vigia,status,debate}.md`).
- [x] Servidor MCP `core/mcp_server.py` (`read_war_room`, `post_war_room_message`, `get_lock_status`) com allowlist estrita (`LGPD-03`).
- [x] Subcomando `agloop audit --privacy` (`LGPD-04`) em `main.py` retrocompatível com `--name` e 56 testes verdes.

### M5 — Gate de PR+CI Antes do Merge na Main (Concluído em 2026-11-05 — Turno 7, PR #7)
- [x] Workflow `.github/workflows/ci.yml` executando `pytest` em matriz Python 3.10/3.11/3.12 em todo PR e push contra a `main`.
- [x] Port do padrão Sysoft: branch de feature (`feat/issue-5-pr-ci-gate`) + PR real + CI 100% verde antes do merge.
- [x] Atualização da governança canônica no `.claude/skills/vigilia/SKILL.md` (v1.2.0, Seção 6 e novo `STATUS: PR_ABERTO`).
- [x] Squash merge do PR #7 com branches deletadas e histórico linear preservado.

### M6 — Productização do AgLoop (Concluído em 2026-11-05 — Turnos 8 e 9, PRs #9 e #10)
- [x] Empacotamento PyPI com licença MIT, classifiers, project.urls e versão `0.6.0` (`E07.1`).
- [x] Scaffolding de governança (`agloop init`) com templates limpos em `core/templates/` (`E07.2`).
- [x] Varredura segura de repositórios (`agloop scan`, tool MCP `scan_repository` e hook informativo) (`E07.3`).
- [x] Suíte de 70 testes verdes no `pytest` local e no GitHub Actions CI.
