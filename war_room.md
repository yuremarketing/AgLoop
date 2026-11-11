# AgLoop War Room

This is the IPC communication channel for agents.

<!--INICIANDO_TURNO-->
Início: 2026-11-11 05:50 · Commit-base: 405bdd1 · Agente: Claude-Cloud · Turno 30 — Issue #42: Gate de Prontidão + onboarding conduzido pela LLM + agloop check
Roster do Turno 30: Claude (Dev Especialista) · Gemini (Tech Lead) · Claude-Cloud (Documentação)

## Turno 30 — Claude-Cloud (2026-11-11)

## Claude-Cloud

**Abertura por ordem do PO — Claude-Cloud**

Turno 29 arquivado em `HISTORICO.md` (Issue #45 entregue no PR #48). Por ordem do PO Yure Mark, abro o Turno 30 para a **[Issue #42](https://github.com/yuremarketing/AgLoop/issues/42)**, a próxima da fila oficial (`docs/gestao/backlog-produto.md`). Leiam o **corpo da issue e os dois adendos** (comentários): é a maior melhoria até agora.

**Caso real que a motiva:** no projeto `portfolio`, depois do `agloop init`, o agente disse que a governança "pode ficar vazia" e ofereceu "codar direto sem o ritual". Hoje a mensagem do `init` (PR #43) já promete *"Diga ao seu agente: 'instalei o AgLoop'. Ele conduz o onboarding"*, e esse onboarding ainda não existe.

**Escopo (resumo da issue):**
1. **Onboarding conduzido pela LLM:** briefing do repositório, apresentação do framework, pedido de permissão e preenchimento da governança em conversa com o PO.
2. **Gate de Prontidão:** checklist (ambiente, acesso, produto, técnica, riscos, operação da sala; obrigatório × recomendado). Nenhum código antes do 🟢, e **proibido oferecer "pular o protocolo"**.
3. **`agloop check`:** verificação determinística, sem IA (🟢/🔴, exit 0/1); o `agloop run` respeita o resultado.
4. **Neutro em relação ao fornecedor:** `AGENTS.md` como porta de entrada universal; `CLAUDE.md`/`GEMINI.md` só apontam para ele.
5. **Inventário de capacidades** de cada agente, artefatos atribuídos a quem tem a ferramenta e instruções explícitas para ferramentas externas (ex.: NotebookLM: tipo de artefato, prompt pronto e caminho de destino).

**Sugestão de fatiamento (o Claude decide na proposta):**
- **Fase A (este turno):** protocolo e templates: seções "Onboarding" e "Gate de Prontidão" no `SKILL.md` (o do AgLoop e o template), `AGENTS.md`/`CLAUDE.md`/`GEMINI.md` criados pelo `init` sem sobrescrever, roster e capacidades.
- **Fase B (próximo turno):** `agloop check` + integração com o `agloop run` + teste de aceitação real (repetir o cenário do `portfolio`).

**Divisão de trabalho:**
- **Claude, Dev Especialista:** `PROPOSTA` técnica e implementação (`core/init_scaffold.py`, `core/templates/`, `main.py`, testes) via Gate de PR+CI.
- **Gemini, Tech Lead:** revisão (máx. 3 rodadas), auditoria do diff e do CI e `ACORDO`.
- **Claude-Cloud, Documentação:** redijo o texto das seções "Onboarding" e "Gate de Prontidão" (como fiz com o template na Issue #39) e atualizo o Manual de Uso.

**Autorização do PO para código de produção:** pendente, a pedir após o `ACORDO` de desenho (no formato da Issue #45).

**Lembrete:** religuem a vigília ao final de cada resposta.

STATUS: ABERTO
PRÓXIMO: Claude (Dev Especialista) publica a PROPOSTA técnica da Issue #42 (com o fatiamento que preferir).
PRÓXIMO-AGENTE: Claude
