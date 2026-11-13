# AgLoop

[![PyPI version](https://img.shields.io/pypi/v/agloop.svg)](https://pypi.org/project/agloop/)
[![CI](https://github.com/yuremarketing/AgLoop/actions/workflows/ci.yml/badge.svg)](https://github.com/yuremarketing/AgLoop/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python 3.10–3.12](https://img.shields.io/badge/python-3.10%E2%80%933.12-blue.svg)](pyproject.toml)

🇬🇧 **[Read in English](README.md)**

> "Eu sou o Product Owner; Claude e Gemini debatem e entregam sob um protocolo de governança que eu desenhei."

**AgLoop** é um framework leve e sem servidor para orquestração de agentes de IA heterogêneos (Claude, Gemini e qualquer modelo suportado pelo [LiteLLM](https://docs.litellm.ai/)). Os agentes propõem, debatem e fecham acordo sobre mudanças no seu repositório através de um único arquivo Markdown — sem servidor, sem banco de dados, sem Docker. O Git faz o lock, o Markdown faz a comunicação, e um Product Owner humano tem a palavra final sobre código de produção.

## Por que o AgLoop

- **Heterogêneo por design** — misture Claude, Gemini e qualquer modelo do LiteLLM na mesma Sala de Guerra; cada agente mantém sua própria identidade e seu turno.
- **Zero-infra, local-first** — tudo vive no seu repositório Git. Sem serviço hospedado, sem banco de dados, sem superfície de ataque nova.
- **Concorrência via Git** — `git push`/`git pull` funcionam como o lock. Quem faz push primeiro fala primeiro; quem perde a corrida tenta de novo de forma limpa (`lost_race`), nunca um reset forçado.
- **Governança humana embutida** — um Product Owner autoriza toda mudança em código de produção; os agentes debatem livremente, mas nunca pulam esse portão.

## Instalação

O único caminho suportado é o PyPI, mais a branch `stable` para plugins/extensões de editor (ver [ADR 0006](docs/arquitetura/decisoes/0006-distribuicao-segura-repositorio-publico-e-branch-stable.md) — a `stable` só avança por fast-forward a cada release publicado, nunca a partir de um commit de `main` em turno aberto):

```bash
pip install agloop
```

**Plugin do Claude Code** (marketplace self-hosted):
```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

**Extensão do Gemini CLI**:
```bash
gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
```

Ambos expõem o mesmo servidor MCP (`core/mcp_server.py`) e os slash commands da Sala de Guerra (`/vigia`, `/status`, `/debate`). O pacote do plugin vive em `plugin/`, então quem instala recebe só o pacote distribuído, não os arquivos de governança do próprio projeto.

## Primeiros passos

```bash
cd meu-projeto
agloop init          # cria war_room.md, docs de governança e arquivos de protocolo
```

Depois, diga ao seu agente: **"instalei o AgLoop"**. Ele conduz o onboarding — briefing, roster, entrevista de governança — até o Gate de Prontidão ficar verde:

```bash
agloop check         # determinístico, sem chamada de LLM — 🟢 ou 🔴 com o que falta
```

Com 🟢, abra seu primeiro turno (`/debate` no Claude Code, ou escreva a proposta à mão) e deixe os agentes debaterem até 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) até o `ACORDO`. Você, como PO, autoriza o que mexer em código de produção.

## Como funciona a Sala de Guerra

Um único arquivo Markdown, `war_room.md`, é o canal de IPC. Cada agente escreve sob o próprio cabeçalho, propõe um plano, e um Tech Lead revisa — tudo serializado via `git push`/`git pull` como lock. Turnos fechados são arquivados em `HISTORICO.md`. O protocolo completo — rotação de papéis, limite de 3 rodadas, roteamento por `PRÓXIMO-AGENTE:` e o Gate de PR+CI para código de produção — está documentado no [Manual de Uso](docs/manual/manual-de-uso.md) e na fonte canônica [`SKILL.md`](.claude/skills/vigilia/SKILL.md).

## Saiba mais

- 📘 [Manual de Uso](docs/manual/manual-de-uso.md) — da instalação ao primeiro debate fechado, em português, com uso do dia a dia e solução de problemas.
- 📘 [User Guide](docs/manual/user-guide.md) — o mesmo manual em inglês.
- 🏛️ [Governança e decisões](docs/gestao/) — roadmap, backlog, ADRs.
- 📜 [Turnos fechados (`HISTORICO.md`)](HISTORICO.md) — o changelog do próprio projeto, escrito pelos agentes que entregaram cada mudança.

## Suporte de plataforma

Testado em CI no Linux, macOS e Windows (Python 3.10, 3.11, 3.12).

*Originado do projeto Sysoft.*
