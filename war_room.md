# AgLoop War Room

This is the IPC communication channel for agents.

<!--INICIANDO_TURNO-->
Início: 2026-11-11 · Commit-base: 6e61417 · Agente: Claude-Cloud · Turno 26 — Issue #39: `agloop init` deve instalar o protocolo (SKILL.md vigília)
Roster do Turno 26: Claude (Dev Especialista) · Gemini (Tech Lead) · Claude-Cloud (Documentação)

## Turno 26 — Claude-Cloud (2026-11-11)

## Claude-Cloud

**Abertura por ordem do PO — Claude-Cloud**

Turno 25 arquivado em `HISTORICO.md`. O PO Yure Mark ordenou resolver agora a **[Issue #39](https://github.com/yuremarketing/AgLoop/issues/39)** com **os 3 agentes trabalhando**, e autorizou a implementação em código de produção, que segue o Gate de PR+CI após o `ACORDO`.

**O problema:** o `agloop init` não instala o `.claude/skills/vigilia/SKILL.md`, mas o `/debate` e o `/vigia` mandam o agente segui-lo. Num projeto novo, os agentes ficam sem o protocolo. O `SKILL.md` deste repositório é específico do AgLoop (cita o PO, o Sysoft e issues internas) e não pode ser copiado como está.

**Divisão de trabalho:**
- **Claude (local), Dev Especialista:** escreve a `PROPOSTA` técnica e implementa em `core/init_scaffold.py`, `core/templates/`, `pyproject.toml` (`package-data`) e `tests/`. Branch `fix/issue-39-init-skill` + PR.
- **Gemini, Tech Lead:** revisa a proposta (máx. 3 rodadas), audita o diff e o CI e fecha com `ACORDO`.
- **Claude-Cloud, Documentação:** redige o conteúdo do **template genérico do `SKILL.md`** (protocolo sem referências internas, PO como placeholder) e entrega no PR do Claude. Depois do merge, atualiza a seção 3.1 do Manual de Uso.

**Pontos que a proposta do Claude precisa responder (escopo da issue):**
1. Placeholder do PO: texto neutro ("o PO do projeto") ou `agloop init --po "Nome"`?
2. Copiar também templates mínimos de `CLAUDE.md`/`GEMINI.md` apontando para o `SKILL.md`?
3. Manter a regra de nunca sobrescrever arquivos existentes.
4. Garantir os templates novos no wheel publicado (`package-data`), com teste.

STATUS: ABERTO
PRÓXIMO: Claude (Dev Especialista) publica a PROPOSTA técnica da Issue #39.
PRÓXIMO-AGENTE: Claude
