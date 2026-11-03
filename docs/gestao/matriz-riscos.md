# Matriz de Riscos e Plano de Mitigação — AgLoop

Documento de governança de riscos técnicos, operacionais e financeiros do **AgLoop**, estruturado segundo o padrão do projeto **Sysoft**. Todo novo épico ou alteração arquitetural em `core/` deve ser avaliado contra esta matriz.

---

## 1. Escala de Classificação

- **Probabilidade (P):** Baixa | Média | Alta
- **Impacto (I):** Baixo | Médio | Alto | Crítico
- **Status:** `Mitigado` (defesa ativa no código/processo) | `Em Mitigação` (implementação em andamento) | `Monitorado` (contingência definida)

---

## 2. Tabela Consolidada de Riscos

| ID | Categoria | Risco Identificado | Causa Raiz | P | I | Mitigação Implementada / Planejada | Status |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- | :---: |
| **R01** | Financeiro / Operacional | **Ping-pong infinito de turnos e exaustão de tokens/API** | Dois agentes em loop autônomo continuam respondendo indefinidamente mesmo após atingirem consenso ou entrarem em impasse. | Alta | Crítico | 1. Limite de 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) na governança (`SKILL.md`).<br>2. Protocolo de parada automática em `WarRoom.get_state()` + `run_agent_loop()` ao detectar `<!-- AGLOOP_STATE: CONSENSUS -->`, `WAITING_HUMAN` ou `<!--FIM_TURNO-->` (`E03.2` — Turno 4 / Issue #4). | **Mitigado** |
| **R02** | Integridade de Dados | **Perda de código não commitado em colisão de push (`lost_race`)** | Dois agentes tentam dar push simultaneamente; o perdedor executava `git add -A` ou `git reset --hard HEAD~1`, destruindo arquivos em edição na working tree. | Média | Crítico | 1. Commits estritamente escopados aos paths da Sala de Guerra (`git commit -- <paths>`).<br>2. Reversão cirúrgica em `_resolve_lost_race()` via `git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`, coberta por `tests/test_git_lock.py`. | **Mitigado** |
| **R03** | Concorrência / Disponibilidade | **Deadlock por trava órfã (*Stale Lock* em `.agloop.lock`)** | Processo de um agente sofre crash ou kill abrupto antes de executar `_release_local_lock()`. | Média | Alto | Registro de `owner.json` (`pid`, `host`, `ts`). Se no mesmo host, checa `os.kill(pid, 0)` e libera imediatamente se o processo morreu; se remoto, expira após `AGLOOP_LOCK_TIMEOUT` (default 300s). | **Mitigado** |
| **R04** | Orquestração / UX | **Monitor de vigília não acorda a sessão do agente** | Script `scripts/vigia.py` rodando em `while True` infinito em background nunca retorna `exit 0`, impedindo o gatilho de conclusão de task de acordar a LLM. | Alta | Alto | Modo one-shot (`--once` / exit `0` ao detectar mudança de orador para o colega), unificando a lógica de polling com `core/runner.py` (DRY — Turno 2 / Issue #3). **Hardening (Turno 3, `E03.5`):** o laço de `watch_war_room()` agora envolve cada iteração em `try/except Exception` com backoff exponencial + jitter (mesmo padrão de `run_agent_loop()`), cobrindo falhas atípicas de E/S/rede fora de `GitCommandError`. Coberto por `tests/test_runner.py::test_watch_war_room_recovers_from_transient_exception` (27/27 verdes). | **Mitigado** |
| **R05** | Governança / Contexto | **Divergência de regras operacionais e inflação de tokens no prompt inicial** | Regras completas da Sala de Guerra triplicadas em `CLAUDE.md`, `GEMINI.md` e `SKILL.md` (anti-padrão identificado no Turno 72 do Sysoft). | Alta | Médio | Centralização DRY: protocolo completo apenas em `.claude/skills/vigilia/SKILL.md`, mantendo `CLAUDE.md` e `GEMINI.md` como resumos executivos enxutos (Issue #3 / Turno 1). | **Mitigado** |
| **R06** | Segurança / Execução | **Execução destrutiva ou vazamento via Tools do Agente (Google ADK)** | Ao equipar `core/agent.py` com ferramentas no Google ADK (Issue #4), um agente autônomo poderia modificar código de produção ou expor `.env` sem autorização humana. | Média | Crítico | 1. Cláusula Pétrea (`SKILL.md` / `termo-abertura.md`): proibição de alterar código de produção sem aval do PO.<br>2. Tools padrão restritas a leitura e diagnóstico seguro (`read_file`, `list_dir`, `git_diff`, `run_pytest`), confinadas via `os.path.commonpath` e com blacklist ativa para `.env`, `id_rsa`, `*.pem`/`*.key` (`LGPD-01` / Turno 4).<br>3. Tools de fato conectadas ao caminho de resposta real: `InMemoryRunner` (Google ADK) ou loop multi-round de tool-calling do `litellm` (`_run_litellm_with_tools`), não apenas construídas e ociosas (36/36 testes verdes). | **Mitigado** |
| **R07** | Performance / Contexto | **Degradação de latência e estouro de contexto por crescimento do `war_room.md`** | `WarRoom.read_all()` lê o arquivo inteiro a cada turno; após dezenas de turnos, o custo de input tokens explode. | Alta | Alto | 1. Fechamento atômico com arquivamento automático de turnos antigos em `HISTORICO.md` (`close_turn_and_archive` — Issue #3 / Turno 2).<br>2. Janela deslizante (`read_recent(max_turns=N)`) no `WarRoom` (Issue #4 / Turno 4). | **Mitigado** |
| **R08** | Rastreabilidade Git | **Poluição de autoria Git e colisão de commits no arquivamento** | Commits da Sala de Guerra herdando committer local da máquina ou gerando 2 commits separados (fim de turno + arquivo de histórico). | Média | Médio | 1. Injeção isolada de `GIT_AUTHOR_*` e `GIT_COMMITTER_*` no ambiente do subprocesso Git em `GitLock.commit()`.<br>2. Commit único atômico contendo `["war_room.md", "HISTORICO.md"]` (Issue #3 / Turno 2). | **Mitigado** |
| **R09** | Privacidade / LGPD | **Exposição não intencional de PII de desenvolvedores em logs e commits** | Metadados pessoais da máquina hospedeira vazando no histórico de commits automatizados dos agentes. | Baixa | Médio | Isolamento de variáveis `GIT_AUTHOR_*` e `GIT_COMMITTER_*` por subprocesso (`E02.5`) sem poluir `os.environ` global (`lgpd-conformidade-agloop.md`). | **Mitigado** |
| **R10** | Privacidade / LGPD | **Transferência internacional de dados pessoais via payload de LLM** | Trechos de código ou dados de teste contendo PII (CPFs, e-mails reais, chaves) enviados no prompt de revisão para provedores externos. | Média | Alto | Sanitização automática de payloads via `sanitize_prompt_pii()` (mascarando CPFs, chaves de API e qualquer e-mail exceto `@agloop.local`) e bloqueio de arquivos sensíveis (`LGPD-01` e `LGPD-02` — Turno 4 / Issue #4). | **Mitigado** |

---

## 3. Histórico de Revisão da Matriz

| Data | Turno | Alteração |
| :--- | :---: | :--- |
| 2026-11-01 | Turno 1 | Criação inicial da Matriz de Riscos (`R01` a `R08`) consolidando lições do Sysoft e das Issues #1, #2, #3 e #4. |
| 2026-11-03 | Pós-Turno 2 | Atualização de `R04`, `R07` e `R08` para `Mitigado` após conclusão da Issue #3 e inclusão de `R09` e `R10` oriundos do estudo de conformidade LGPD (`lgpd-conformidade-agloop.md`). |
| 2026-11-03 | Turno 3 (Auditoria NotebookLM) | `R04` revertido para `Em Mitigação`: os próprios relatórios importados (`auditoria-governanca-agloop.md`, `estudo-campo-e-governanca-agloop.md`) apontam a ausência de captura genérica de exceção em `watch_war_room()` como *blind spot* não resolvido, contradizendo o status `Mitigado` que havia sido atribuído. |
| 2026-11-03 | Turno 3 (`E03.5`, autorizado pelo PO Yure Mark) | `R04` de volta a `Mitigado`: implementado o hardening real de exceções em `watch_war_room()` (`core/runner.py`), com teste de regressão dedicado. |
| 2026-11-03 | Turno 4 (`E03.1`–`E03.4` + `LGPD-01`/`LGPD-02`, autorizado pelo PO Yure Mark) | `R01`, `R06` e `R10` passam a `Mitigado` após implementação de `WarRoom.get_state()`, `read_recent()`, tools seguras confinadas via `os.path.commonpath` e `sanitize_prompt_pii()` (34/34 testes verdes). |
| 2026-11-03 | Turno 4 (correção de auditoria — `think_and_act` cego) | `R06`: achado do Claude (Tech Lead) de que `self.adk_agent` era construído mas nunca invocado — tools ficavam inacessíveis em tempo de execução. Corrigido: `think_and_act()` agora chama `_run_adk()` (via `InMemoryRunner`) ou `_run_litellm_with_tools()` (loop multi-round de tool-calling), tornando as 4 tools de fato alcançáveis (36/36 testes verdes). |
