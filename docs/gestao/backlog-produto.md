# Backlog do Produto — AgLoop

Registro priorizado dos épicos e histórias técnicas do **AgLoop**, mantendo rastreabilidade direta com as Issues do repositório [`yuremarketing/AgLoop`](https://github.com/yuremarketing/AgLoop/issues) e com as ADRs em [`docs/arquitetura/decisoes/`](../arquitetura/decisoes/).

---

## Ordem de Priorização (Sequenciamento Oficial)

`E01 (Concluído)` → `E02 (Governança & DRY — Concluído)` → `E03 (Google ADK & Consenso — Concluído)` → `E04 (Plugin & MCP — Concluído)` → `E05 (Gate de PR+CI — Concluído)`

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
- **Status:** ✅ Concluído (Turnos 1 e 2)
- **ADR:** [ADR 0004](../arquitetura/decisoes/0004-governanca-dry-ssot-autoria-e-fechamento-atomico.md)
- **Entregas Documentais (Delegadas — Concluídas no Turno 1):**
  - [x] `E02.1` — Fonte Única da Verdade do protocolo em `.claude/skills/vigilia/SKILL.md` e ponteiros enxutos em `CLAUDE.md` / `GEMINI.md`.
  - [x] `E02.2` — Termo de Abertura (`docs/gestao/termo-abertura.md`), Artefato Mestre (`docs/gestao/artefatos/artefato-mestre-agloop.md`), Glossário (`docs/gestao/glossario.md`) e Elicitação de Requisitos (`docs/gestao/concepcao-e-elicitacao-requisitos.md`).
  - [x] `E02.3` — Matriz de Riscos (`docs/gestao/matriz-riscos.md`) cobrindo `R01`–`R08`.
  - [x] `E02.4` — ADRs fundacionais `0001` a `0005` em `docs/arquitetura/decisoes/`.
- **Entregas de Código (Autorizadas pelo PO Yure Mark — Concluídas no Turno 2):**
  - [x] `E02.5` — Parametrizar `author_name`/`author_email` em `GitLock.commit()` injetando `GIT_AUTHOR_*` e `GIT_COMMITTER_*` de forma isolada no ambiente do subprocesso Git (`custom_environment`), + fallback `main` em `_branch()`.
  - [x] `E02.6` — Implementar `close_turn_and_archive()` e `archive_old_turns()` em `core/war_room.py` acoplados aos marcadores `<!--FIM_TURNO-->` / `CONSENSUS`, arquivando turnos antigos em `HISTORICO.md` em commit único atômico.
  - [x] `E02.7` — Refatorar `scripts/vigia.py` como thin wrapper DRY de `core.runner.watch_war_room` com suporte a `--agent` e `--once` (`exit 0` ao mudar o orador).
  - [x] `E02.8` — Novos testes em `tests/test_git_lock.py` e `tests/test_runner.py` (26 passed) validando autoria Git isolada, fallback de branch, arquivamento atômico e `watch_war_room(once=True)`.

---

### E03 — Motor Cognitivo Google ADK, Tools Seguras e Controle de Consenso ([Issue #4](https://github.com/yuremarketing/AgLoop/issues/4))
- **Status:** ✅ Concluído (Turnos 3 e 4 — Marco M3)
- **ADR:** [ADR 0005](../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md)
- **Entregas:**
  - [x] `E03.1` — Janela deslizante `WarRoom.read_recent(max_turns=6)` mantendo retrocompatibilidade de `read_all()`.
  - [x] `E03.2` — Protocolo de consenso e pausa humana (`<!-- AGLOOP_STATE: WAITING_HUMAN -->` e `<!-- AGLOOP_STATE: CONSENSUS -->`) via `WarRoom.get_state()` + pausa de inferência no `core/runner.py`.
  - [x] `E03.3` — Integração de `google-adk` (`LlmAgent` + `LiteLlm`) em `core/agent.py` com tools seguras somente-leitura (`read_file`, `list_dir`, `git_diff`, `run_pytest`), confinamento `os.path.commonpath` (`LGPD-01`) e sanitização `sanitize_prompt_pii` (`LGPD-02`). `think_and_act()` invoca de fato o motor (`InMemoryRunner` do ADK ou loop multi-round de tool-calling do `litellm`) — corrigido após achado de auditoria do Claude de que o agente ficava "cego" (36/36 testes verdes). **Pendente de validação futura:** o ramo assíncrono real do `InMemoryRunner` (`run_async`) só é exercitado via mock (`run_text`) — precisa ser validado com `google-adk` de fato instalado antes de depender dele em produção.
  - [x] `E03.4` — Empacotamento moderno via `pyproject.toml` expondo os comandos CLI `agloop` e `agloop-vigia`.
  - [x] `E03.5` — Hardening de exceções em `watch_war_room()` (`core/runner.py`): captura genérica (*catch-all*) com retry/backoff exponencial + jitter para falhas atípicas de E/S ou rede fora do escopo de `GitCommandError`, evitando paralisação silenciosa do watcher (`R04`, identificado na auditoria do Turno 3 e autorizado pelo PO Yure Mark). Coberto por `tests/test_runner.py::test_watch_war_room_recovers_from_transient_exception` (27/27 verdes).

---

### E04 — Plugin Oficial Claude Code & Antigravity + Servidor MCP ([Issue #2](https://github.com/yuremarketing/AgLoop/issues/2))
- **Status:** ✅ Concluído (Turno 6)
- **ADR:** [ADR 0005](../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md)
- **Entregas:**
  - [x] `E04.1` — Manifesto `.claude-plugin/plugin.json` e comandos slash (`commands/vigia.md`, `commands/status.md`, `commands/debate.md`).
  - [x] `E04.2` — Servidor MCP (`core/mcp_server.py` + `.mcp.json`) expondo `read_war_room`, `post_war_room_message` e `get_lock_status`, restritos por *allowlist* (`LGPD-03`) a `war_room.md`/`HISTORICO.md`.
  - [x] `E04.3` — Hooks de eventos (`hooks/hooks.json`) com verificação de status da Sala de Guerra no `SessionStart`.
  - [x] `LGPD-04` — `agloop audit --privacy` (`core/privacy_audit.py`) via subcomando `audit` em `main.py` (retrocompatível com `--name`).

---

### E05 — Gate de PR+CI Antes do Merge na Main ([Issue #5](https://github.com/yuremarketing/AgLoop/issues/5))
- **Status:** ✅ Concluído (Turno 7, PR #7 squash-merged)
- **Motivação:** o Sysoft já exige, antes de qualquer merge na `main`, branch de feature + PR real + `gh pr review --approve` + CI verde (`SKILL.md` do Sysoft, seção 5). O AgLoop hoje aprova só textualmente no `war_room.md` (`STATUS: ACORDO`) seguido de commit direto — sem gate automatizado de terceiro, dependendo inteiramente do auditor ter corrido o `pytest` manualmente antes de commitar.
- **Risco que mitiga:** nada impede hoje, por construção, um commit com testes vermelhos chegar na `main` além da disciplina manual do auditor.
- **Entregas:**
  - [x] `E05.1` — Branch de feature por turno técnico (`feat/issue-N-...`) em vez de commit direto na `main` para mudanças em `core/`/`scripts/`.
  - [x] `E05.2` — Workflow de CI (GitHub Actions) rodando `pytest` automaticamente em cada PR na matriz Python 3.10/3.11/3.12.
  - [x] `E05.3` — Tech Lead aprova via `gh pr review --approve` só com CI verde (port da Autoridade Delegada do Sysoft).
  - [x] `E05.4` — Atualizar `.claude/skills/vigilia/SKILL.md` (seção 6, Gate de PR+CI e STATUS: PR_ABERTO) para refletir o novo fluxo com PR.

---

### E06 — Painel de Gestão Portável entre Agentes ([Issue #6](https://github.com/yuremarketing/AgLoop/issues/6))
- **Status:** ✅ Concluído (Turno 5)
- **Motivação:** o Sysoft tem painel ao vivo via Claude Artifact, mas essa ferramenta é exclusiva da plataforma Claude — portar a regra dele sem ajuste criaria dependência de plataforma única, contradizendo a proposta heterogênea do AgLoop (ADR 0005).
- **Entregas:**
  - [x] `E06.1` — `docs/gestao/painel-agloop.html`: painel-fonte autocontido (tema claro/escuro), KPIs de Marcos/Issues/Riscos/testes, atualizável por qualquer agente.
  - [x] `E06.2` — Publicação ao vivo como Claude Artifact (*best effort*, só quando sessão Claude está ativa).
  - [x] `E06.3` — Regra de fallback explícita: toda mensagem de fechamento de turno relevante declara `PAINEL: ...` (publicado ao vivo ou só local), nunca falha silenciosamente.
  - [x] `E06.4` — Seção 5 nova em `.claude/skills/vigilia/SKILL.md` (SSOT) formalizando a divisão de responsabilidade portável.
