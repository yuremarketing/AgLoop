# ADR 0004: Governança DRY (SSOT em `SKILL.md`), Autoria Git Isolada e Fechamento Atômico

- **Status:** Aceita
- **Data:** 2026-11-01 ([Issue #3](https://github.com/yuremarketing/AgLoop/issues/3) / Turno 1)
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

No projeto-mãe **Sysoft** (Turno 72 / PR #39), identificamos e corrigimos débitos arquiteturais e de governança no harness da Sala de Guerra que precisavam ser portados para o **AgLoop** ([Issue #3](https://github.com/yuremarketing/AgLoop/issues/3)):
1. **Triplicação de Prompt:** As regras operacionais completas da Sala de Guerra estavam copiadas em `CLAUDE.md`, `GEMINI.md` e `.claude/skills/vigilia/SKILL.md`, inflando o consumo de tokens em toda sessão e criando risco de divergência normativa.
2. **Autoria Git Inconsistente:** `GitLock.commit()` não definia `GIT_AUTHOR_*` nem `GIT_COMMITTER_*`, herdando o usuário global da máquina e sem isolar a identidade de cada agente no histórico do Git.
3. **Crescimento Ilimitado do War Room e Duplo Commit de Arquivamento:** Separar o fechamento de turno (`<!--FIM_TURNO-->`) do arquivamento em `HISTORICO.md` em dois commits distintos dobrava o risco de condição de corrida (`lost_race`) e poluía o `git log`.

## Decisão

1. **Fonte Única da Verdade (SSOT DRY) em `.claude/skills/vigilia/SKILL.md`:**
   - Concentrar 100% do protocolo detalhado da Sala de Guerra em `.claude/skills/vigilia/SKILL.md`.
   - Manter `CLAUDE.md` e `GEMINI.md` na raiz como resumos executivos enxutos contendo apenas os papéis, a autoridade delegada, os limites invioláveis do PO (Yure Mark) e o ponteiro para `SKILL.md`.
2. **Autoria Git Escopada por Chamada em `GitLock.commit()`:**
   - Aceitar `author_name` e `author_email` opcionais em `GitLock.commit()` / `acquire_lock_and_push()` e injetar `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` e `GIT_COMMITTER_EMAIL` exclusivamente no ambiente do subprocesso Git (`repo.git.custom_environment`), sem mutar `os.environ` global do processo Python.
3. **Fechamento e Arquivamento Atômico (`close_turn_and_archive`):**
   - Acoplar o arquivamento de turnos antigos em `HISTORICO.md` à detecção/gravação dos marcadores de encerramento (`<!--FIM_TURNO-->` ou `<!-- AGLOOP_STATE: CONSENSUS -->`), realizando o commit e push de `["war_room.md", "HISTORICO.md"]` em uma única transação atômica do `GitLock`.

## Consequências

### Positivas
- Redução imediata do consumo de tokens de sistema por sessão e eliminação do risco de regras divergentes entre Claude e Gemini (Risco `R05` mitigado).
- Rastreabilidade limpa no `git log` identificando exatamente qual agente assinou cada turno, sem efeitos colaterais em processos concorrentes (Risco `R08` mitigado).
- Controle contínuo do tamanho de `war_room.md` com commit único atômico (Risco `R07` mitigado).
