---
description: Guia de abertura ou resposta de um turno formal na Sala de Guerra do AgLoop (PROPOSTA -> RÉPLICA -> TRÉPLICA -> ACORDO), via GitLock.
---

Siga o protocolo canônico em `.claude/skills/vigilia/SKILL.md` (fonte única da verdade) para abrir ou responder a um turno formal no `war_room.md`:

1. **Abrindo um turno novo:** adicione `<!--INICIANDO_TURNO-->` com `Início`, `Commit-base` (HEAD atual) e `Agente`, seguido de `## Turno N — <Agente> (data)` e sua `**Proposta — <Agente> (Dev Especialista)**`. Termine com `STATUS: PROPOSTA` e `PRÓXIMO: <passo claro>`.
2. **Respondendo como Tech Lead:** audite a proposta (releia o código/diff relevante antes de responder), escreva sua `**Réplica**`/`**Tréplica**` com `STATUS: RÉPLICA` ou `STATUS: TRÉPLICA`, e feche com `STATUS: ACORDO` apenas quando convergir — no máximo 3 rodadas; sem convergência, escale ao PO.
3. **Comitando:** use `GitLock.acquire_lock_and_push` (ou `git commit -- war_room.md HISTORICO.md`) — nunca comite outros arquivos junto. Autoria isolada (`GIT_AUTHOR_NAME`/`EMAIL` do agente).
4. **Fechando o turno:** ao atingir `ACORDO`, use `<!--FIM_TURNO-->` — isso arquiva turnos antigos em `HISTORICO.md` atomicamente no mesmo commit.
5. Qualquer mudança em código de produção (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `.env`) exige aprovação explícita do PO antes de commitar — mesmo após `ACORDO` entre os agentes.
