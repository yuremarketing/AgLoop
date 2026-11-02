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
| **R01** | Financeiro / Operacional | **Ping-pong infinito de turnos e exaustão de tokens/API** | Dois agentes em loop autônomo continuam respondendo indefinidamente mesmo após atingirem consenso ou entrarem em impasse. | Alta | Crítico | 1. Limite de 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) na governança (`SKILL.md`).<br>2. Protocolo de parada automática no `Runner`/`WarRoom` ao detectar `<!-- AGLOOP_STATE: CONSENSUS -->` ou `WAITING_HUMAN` (Issue #4 / Turno 1). | **Em Mitigação** |
| **R02** | Integridade de Dados | **Perda de código não commitado em colisão de push (`lost_race`)** | Dois agentes tentam dar push simultaneamente; o perdedor executava `git add -A` ou `git reset --hard HEAD~1`, destruindo arquivos em edição na working tree. | Média | Crítico | 1. Commits estritamente escopados aos paths da Sala de Guerra (`git commit -- <paths>`).<br>2. Reversão cirúrgica em `_resolve_lost_race()` via `git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`, coberta por `tests/test_git_lock.py`. | **Mitigado** |
| **R03** | Concorrência / Disponibilidade | **Deadlock por trava órfã (*Stale Lock* em `.agloop.lock`)** | Processo de um agente sofre crash ou kill abrupto antes de executar `_release_local_lock()`. | Média | Alto | Registro de `owner.json` (`pid`, `host`, `ts`). Se no mesmo host, checa `os.kill(pid, 0)` e libera imediatamente se o processo morreu; se remoto, expira após `AGLOOP_LOCK_TIMEOUT` (default 300s). | **Mitigado** |
| **R04** | Orquestração / UX | **Monitor de vigília não acorda a sessão do agente** | Script `scripts/vigia.py` rodando em `while True` infinito em background nunca retorna `exit 0`, impedindo o gatilho de conclusão de task de acordar a LLM. | Alta | Alto | Modo one-shot (`--once` / exit `0` ao detectar mudança de orador para o colega), unificando a lógica de polling com `core/runner.py` (DRY — Turno 1 / Issue #3). | **Em Mitigação** |
| **R05** | Governança / Contexto | **Divergência de regras operacionais e inflação de tokens no prompt inicial** | Regras completas da Sala de Guerra triplicadas em `CLAUDE.md`, `GEMINI.md` e `SKILL.md` (anti-padrão identificado no Turno 72 do Sysoft). | Alta | Médio | Centralização DRY: protocolo completo apenas em `.claude/skills/vigilia/SKILL.md`, mantendo `CLAUDE.md` e `GEMINI.md` como resumos executivos enxutos (Issue #3 / Turno 1). | **Mitigado** |
| **R06** | Segurança / Execução | **Execução destrutiva ou vazamento via Tools do Agente (Google ADK)** | Ao equipar `core/agent.py` com ferramentas no Google ADK (Issue #4), um agente autônomo poderia modificar código de produção ou expor `.env` sem autorização humana. | Média | Crítico | 1. Cláusula Pétrea (`SKILL.md` / `termo-abertura.md`): proibição de alterar código de produção sem aval do PO.<br>2. Tools padrão do ADK restritas a leitura e diagnóstico seguro (`read_file`, `list_dir`, `git_diff`, `run_pytest`) com bloqueio de leitura a `.env`/secrets. | **Em Mitigação** |
| **R07** | Performance / Contexto | **Degradação de latência e estouro de contexto por crescimento do `war_room.md`** | `WarRoom.read_all()` lê o arquivo inteiro a cada turno; após dezenas de turnos, o custo de input tokens explode. | Alta | Alto | 1. Fechamento atômico com arquivamento automático de turnos antigos em `HISTORICO.md` (`close_turn_and_archive` — Issue #3).<br>2. Janela deslizante (`read_recent(max_turns=N)`) no `WarRoom` (Issue #4). | **Em Mitigação** |
| **R08** | Rastreabilidade Git | **Poluição de autoria Git e colisão de commits no arquivamento** | Commits da Sala de Guerra herdando committer local da máquina ou gerando 2 commits separados (fim de turno + arquivo de histórico). | Média | Médio | 1. Injeção isolada de `GIT_AUTHOR_*` e `GIT_COMMITTER_*` no ambiente do subprocesso Git em `GitLock.commit()`.<br>2. Commit único atômico contendo `["war_room.md", "HISTORICO.md"]` (Issue #3). | **Em Mitigação** |

---

## 3. Histórico de Revisão da Matriz

| Data | Turno | Alteração |
| :--- | :---: | :--- |
| 2026-11-01 | Turno 1 | Criação inicial da Matriz de Riscos (`R01` a `R08`) consolidando lições do Sysoft e das Issues #1, #2, #3 e #4. |
