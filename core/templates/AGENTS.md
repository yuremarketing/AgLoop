# AGENTS.md

Este projeto usa o **AgLoop**: agentes de IA debatem e trabalham em turnos na Sala de Guerra (`war_room.md`), e o PO do projeto tem a palavra final sobre código de produção.

**Antes de qualquer tarefa, leia e siga o protocolo:** [`.claude/skills/vigilia/SKILL.md`](.claude/skills/vigilia/SKILL.md).

1. Se o **Gate de Prontidão** (Seção 7 do protocolo) não estiver 🟢, conduza o **Onboarding** (Seção 6). Nenhum código antes disso, e nunca ofereça pular o protocolo.
2. Use um nome de agente distinto na sala e registre-o em `docs/gestao/roster-agentes.md`.
3. Ao final de cada resposta na sala, religue a vigília: `agloop-vigia --agent <SeuNome> --once`.

Este arquivo vale para qualquer agente (Claude, Gemini, Codex, Cursor, Copilot, modelos locais e outros). `CLAUDE.md` e `GEMINI.md`, quando existirem, apenas apontam para cá.
