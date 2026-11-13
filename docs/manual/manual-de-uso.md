# Manual de Uso do AgLoop

Guia completo, da instalação até o primeiro debate entre agentes fechado em `ACORDO`.

> **Versão do manual:** 2026-11-11 · AgLoop `0.8.0`
> **Fonte canônica do protocolo:** [`.claude/skills/vigilia/SKILL.md`](../../.claude/skills/vigilia/SKILL.md). Se este manual e o `SKILL.md` divergirem, vale o `SKILL.md`.

> 🇬🇧 **[Read in English](user-guide.md)** — cobre instalação, primeiros passos e conceitos (fase 1); uso do dia a dia, cenários multi-agente, governança/segurança e solução de problemas (§5–§8) seguem só neste manual por enquanto.

---

## Sumário

1. [O que é o AgLoop](#1-o-que-é-o-agloop)
2. [Instalação](#2-instalação)
3. [Primeiros passos](#3-primeiros-passos)
4. [Conceitos](#4-conceitos)
5. [Uso no dia a dia](#5-uso-no-dia-a-dia)
6. [Cenários práticos](#6-cenários-práticos)
7. [Governança e segurança](#7-governança-e-segurança)
8. [Solução de problemas](#8-solução-de-problemas)
9. [FAQ](#9-faq)

---

## 1. O que é o AgLoop

O AgLoop coloca agentes de IA diferentes (Claude, Gemini e outros) para **debater e trabalhar em turnos** sobre o mesmo repositório, sem servidor:

- **Git** é o mecanismo de concorrência e transporte: quem dá push primeiro fala primeiro.
- **Markdown** é o canal de comunicação: um único arquivo, `war_room.md` (a **Sala de Guerra**), onde os agentes propõem, revisam e fecham acordos.
- **Um humano (o PO)** tem a palavra final sobre qualquer mudança em código de produção.

É **local-first** e **zero-infra**: não há banco de dados, Docker nem serviço hospedado. Tudo fica no seu repositório.

---

## 2. Instalação

### 2.1 Requisitos

- **Python** 3.10, 3.11 ou 3.12 (testado em CI no Linux, macOS e Windows)
- **Git**, com um remoto (`origin`) configurado se mais de uma máquina ou sessão for participar
- **Chave de API** do provedor de LLM que cada agente vai usar (veja a seção 2.4)

### 2.2 Como plugin do Claude Code (marketplace self-hosted)

Dentro de uma sessão do Claude Code:

```bash
/plugin marketplace add yuremarketing/AgLoop#stable
/plugin install agloop@agloop
```

Isso instala os slash commands `/vigia`, `/status` e `/debate` e o servidor MCP `agloop`. O servidor MCP importa o pacote Python, então instale-o também (seção 2.3). O `#stable` fixa a instalação na branch que só avança por fast-forward a cada Release publicado — nunca aponta pra um commit de `main` em turno aberto (ver [ADR 0006](../arquitetura/decisoes/0006-distribuicao-segura-repositorio-publico-e-branch-stable.md)).

> O AgLoop **não** está listado no diretório oficial de plugins do Claude: o diretório só aceita servidores MCP locais e scripts Python de organizações verificadas. O marketplace self-hosted entrega o plugin completo.

### 2.3 Como pacote Python (CLI)

```bash
pip install agloop
# ou, a partir de um clone do repositório:
pip install -e ".[dev]"
```

Comandos instalados: `agloop`, `agloop-vigia` e `agloop-mcp`.

### 2.4 Como extensão do Gemini CLI

```bash
gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
```

Expõe o mesmo servidor MCP (`core/mcp_server.py`). O `--ref=stable` aponta pra mesma branch `stable` do item 2.2, pelo mesmo motivo.

### 2.5 Chaves de API e variáveis de ambiente

O `agloop` carrega um arquivo `.env` na raiz do projeto (via `python-dotenv`). **Nunca** commite o `.env`: o agente já bloqueia a leitura de `.env`, `.env.*` e `*.pem` (requisito `LGPD-01`).

| Variável | Para quê | Padrão |
| :--- | :--- | :--- |
| Chave do provedor (ex.: `GEMINI_API_KEY`, `ANTHROPIC_API_KEY`) | Autenticar as chamadas ao modelo, feitas via [LiteLLM](https://docs.litellm.ai/) | — |
| `LLM_TIMEOUT` | Tempo máximo de uma chamada ao modelo (s) | `60` |
| `LLM_MAX_RETRIES` | Novas tentativas em falha transitória | `3` |
| `AGLOOP_LOCK_TIMEOUT` | Idade (s) a partir da qual um lock local é considerado abandonado | `300` |
| `AGLOOP_AGENT` | Nome padrão do agente para o `agloop-vigia` | `Gemini` |
| `AGLOOP_STALL_MINUTES` | Minutos sem atividade até a vigília gravar `WAITING_HUMAN` (alarme de travamento) | `0` (desligado) |

---

## 3. Primeiros passos

### 3.1 Inicializar a governança no seu repositório

```bash
cd meu-projeto
agloop init
```

Cria, **sem sobrescrever arquivos existentes**:

- `war_room.md`: a Sala de Guerra
- `HISTORICO.md`: o arquivo morto dos turnos fechados
- `docs/gestao/roadmap.md`, `docs/gestao/backlog-produto.md`, `docs/gestao/matriz-riscos.md`
- `docs/gestao/roster-agentes.md`: quem participa da sala e o que cada agente consegue produzir (inventário de capacidades)
- `AGENTS.md`: porta de entrada para **qualquer** agente (Claude, Gemini, Codex, Cursor, Copilot, modelos locais); aponta para o protocolo
- `CLAUDE.md` e `GEMINI.md`: mínimos, só apontam para o `AGENTS.md`
- `docs/arquitetura/decisoes/` (pasta vazia para ADRs)
- `.claude/skills/vigilia/SKILL.md`: o protocolo da Sala de Guerra (papéis, limite de 3 rodadas, `PRÓXIMO-AGENTE:`, limites do PO, Gate de PR+CI), em versão genérica para você ajustar ao seu projeto

Ao final, o `init` mostra os próximos passos:

```
AgLoop: Sala de Guerra criada.

Proximos passos:
  1. git add war_room.md HISTORICO.md docs/ .claude/ && git commit -m "chore: inicializa AgLoop" && git push
  2. Claude Code: /plugin marketplace add yuremarketing/AgLoop#stable && /plugin install agloop@agloop
     Gemini CLI:  gemini extensions install https://github.com/yuremarketing/AgLoop --ref=stable
  3. Ajuste .claude/skills/vigilia/SKILL.md (nome do PO e limites de codigo de producao).
  4. Diga ao seu agente: "instalei o AgLoop". Ele conduz o onboarding.

Manual de Uso: https://github.com/yuremarketing/AgLoop/blob/main/docs/manual/manual-de-uso.md
```

> **Pendência conhecida (pós-Release 0.8.0):** o texto acima é a saída literal atual do `agloop init` (`core/init_scaffold.py`), que ainda aponta pra `main` em vez de `#stable`/`--ref=stable`. É código em `core/`, então exige PR + Gate próprio — registrado para um turno futuro, não incluído neste ajuste de documentação.

- Se todos os arquivos já existiam, o `init` só mostra um lembrete curto com o link do manual.
- Para scripts e CI, use `agloop init -q` (ou `--quiet`): sai apenas a lista de arquivos.

### 3.2a Onboarding e Gate de Prontidão

Depois do `init`, diga ao seu agente: *"instalei o AgLoop"*. Ele segue o **Onboarding** do protocolo:

1. lê o repositório e traz um **briefing** (o que viu e o que falta);
2. apresenta o AgLoop em poucas linhas e pede permissão para começar;
3. pergunta quais agentes vão participar e registra o **roster e as capacidades** de cada um;
4. preenche a governança **em conversa com você** (visão, PO, backlog com user stories e critérios de aceite, riscos etc.);
5. sugere ferramentas de apoio para cada artefato, com instrução explícita (qual ferramenta, quais fontes, prompt pronto, onde salvar no repositório).

Enquanto o **Gate de Prontidão** não estiver 🟢, o agente não escreve código de produção e **não oferece pular o protocolo**. Itens pendentes ficam marcados nos arquivos com `<!-- AGLOOP_TODO: ... -->`. Para conferir o Gate a qualquer momento (sem IA, determinístico):

```bash
agloop check        # relatório completo: 🔒 obrigatórios e 📌 recomendados, com o que falta
agloop check -q     # só o resumo, ex.: "Gate de Prontidão: 🔴 (4 pendência(s) bloqueante(s))"
```

- Sai com código `0` quando o Gate está 🟢 e `1` quando está 🔴, então serve também para CI.
- O `agloop run` **se recusa a rodar** com o Gate 🔴. Bypass só em emergência e com autorização expressa do PO: `agloop run --force-bypass-gate ...`.
- Num repositório recém-inicializado o resultado é 🔴, como esperado: o Onboarding existe justamente para levá-lo a 🟢.

### 3.2b Atualização de Protocolo e Notificação de Versão (`agloop update`)

Quando uma nova versão do AgLoop traz evoluções para as instruções de protocolo (`SKILL.md`, `AGENTS.md`, `CLAUDE.md`, `GEMINI.md`), o Gate de Prontidão (`agloop check`) exibe um item recomendado 📌 apontando a defasagem.

Você pode inspecionar e atualizar os arquivos com segurança total:

```bash
agloop update --dry-run   # visualiza o diff unificado sem modificar arquivos
agloop update --yes       # aplica as atualizações criando backups (.bak) automáticos
```

- **Substituição com backup (.bak):** O `agloop update` atualiza os arquivos de protocolo substituindo-os pelos templates da nova versão e criando uma cópia `.bak` do arquivo original no mesmo diretório. Ele **não** faz mesclagem automática (merge 3-way). Se o seu `SKILL.md` ou protocolo contiver personalizações locais profundas (ex.: nomes do PO, seções exclusivas), use sempre `agloop update --dry-run` para inspecionar o diff antes de atualizar e reincorpore suas customizações a partir da cópia `.bak`.
- **Governança preenchida imutável:** Documentos de governança preenchidos (`roadmap.md`, `backlog-produto.md`, `matriz-riscos.md`) **nunca** são tocados pelo update. O `roster-agentes.md` só é criado se ainda não existia.
- **Transparência interativa:** Ao rodar `agloop update` sem `--yes`, o terminal exibe o diff unificado de cada arquivo antes de solicitar confirmação explícita.
- **Aviso não-intrusivo do PyPI:** Ao rodar comandos como `agloop init`, `agloop check` ou `agloop update`, se houver versão mais recente do pacote publicada no PyPI, uma linha informativa e fail-silent é exibida no final:
  `💡 AgLoop: versão X.Y.Z disponível (instalada: A.B.C). Atualize: pip install --upgrade agloop`
  *(Desativado automaticamente em ambientes CI ou via `AGLOOP_NO_UPDATE_CHECK=1`)*.

### 3.2 Conhecer o projeto (somente leitura)

```bash
agloop scan
```

Lista a estrutura do repositório e os manifestos de stack reconhecidos (`pyproject.toml`, `package.json`, `go.mod`, `Dockerfile` etc.). Não altera nada.

### 3.3 Fazer o primeiro debate

1. Faça commit e push do `war_room.md` gerado pelo `init`.
2. Em uma sessão (ex.: Claude Code), peça ao agente para abrir um turno com `/debate`, ou escreva a proposta no formato da seção 4.3.
3. Na sessão do outro agente, ligue a vigília (seção 5.3). Ela acorda o agente quando for a vez dele.
4. Os agentes trocam no máximo 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) até o `ACORDO`.
5. Você, como PO, autoriza o que mexer em código de produção.

---

## 4. Conceitos

### 4.1 Sala de Guerra (`war_room.md`)

Arquivo Markdown único onde acontece todo o debate. Cada participante escreve sob um cabeçalho com o próprio nome (`## Claude`, `## Gemini`). Turnos fechados vão para o `HISTORICO.md`.

### 4.2 Papéis (trocam a cada turno)

| Papel | O que faz |
| :--- | :--- |
| **Dev Especialista** | Abre o turno (`<!--INICIANDO_TURNO-->`), propõe, implementa após o acordo e submete para auditoria |
| **Tech Lead** | Revisa a proposta, audita o diff e os testes e aprova (`STATUS: ACORDO`) |
| **Observador** | Em salas com 3 ou mais agentes: fica em silêncio e só fala se for endereçado em `PRÓXIMO-AGENTE:` ou chamado pelo PO |
| **PO (humano)** | Autoriza mudanças em código de produção e desempata debates sem convergência |

### 4.3 Formato de um turno

```markdown
<!--INICIANDO_TURNO-->
Início: AAAA-MM-DD HH:MM · Commit-base: <hash> · Agente: <Nome> · <Título curto>
Roster do Turno N: <Dev> (Dev Especialista) · <TL> (Tech Lead) · <outros> (Observadores)

## Turno N — <Agente> (AAAA-MM-DD)

## <Agente>

**Proposta — <Agente> (Dev Especialista)**
...
STATUS: PROPOSTA
PRÓXIMO: <próximo passo em texto livre>
PRÓXIMO-AGENTE: <Nome de quem deve agir>
```

A linha `Roster` só é obrigatória com 3 ou mais participantes.

### 4.4 `STATUS`

| Valor | Significado |
| :--- | :--- |
| `PROPOSTA` / `RÉPLICA` / `TRÉPLICA` | Rodadas do debate (máximo 3) |
| `ACORDO` | Consenso fechado pelo Tech Lead |
| `FEITO` | Implementação documental concluída, aguardando auditoria |
| `PR_ABERTO` | Mudança em código de produção submetida via Pull Request |
| `CONCLUIDO` | Turno encerrado |
| `WAITING_HUMAN` | Pausa: aguarda decisão do PO |

Marcadores especiais lidos pelo código: `<!-- AGLOOP_STATE: CONSENSUS -->` e `<!-- AGLOOP_STATE: WAITING_HUMAN -->` pausam a inferência; `<!--FIM_TURNO-->` fecha o turno e dispara o arquivamento.

### 4.5 `PRÓXIMO:` × `PRÓXIMO-AGENTE:`

- `PRÓXIMO:` é **texto livre**, para humanos e LLMs entenderem o contexto.
- `PRÓXIMO-AGENTE:` é **lido pelo código** (`WarRoom.get_next_agent()`) e decide **quem acorda**. Só o agente citado desperta; os outros continuam dormindo, sem gastar tokens.
- Sem `PRÓXIMO-AGENTE:`, o comportamento legado acorda **qualquer agente que não foi o último a falar**. Em salas com 3 ou mais agentes isso faz dois agentes acordarem juntos, por isso o campo é **obrigatório** nelas.

### 4.6 Limite de 3 rodadas

Sem convergência após a `TRÉPLICA`, o debate é escalado ao PO. Isso evita loops infinitos e gasto descontrolado de tokens.

### 4.7 Múltiplas tarefas por turno (Issue #57)

Um turno pode conter **mais de uma tarefa**, desde que independentes (não toquem os mesmos arquivos/módulos). Cada tarefa ganha um identificador `T<turno>.<n>` (ex.: `T42.1`), citado em `TAREFA:` junto do `STATUS:`; com mais de uma tarefa aberta, `PRÓXIMO-AGENTE:` lista cada agente junto da tarefa correspondente (`Gemini (T42.1); Claude (T42.2)`). A autorização do PO (Seção 7.1) e o limite de 3 rodadas valem **por tarefa**, não pelo turno inteiro, e o turno só fecha quando todas as tarefas estiverem em `ACORDO` ou adiadas. O rastreio de qual issue/PR/arquivo pertence a qual turno/tarefa vive em [`docs/gestao/matriz-rastreabilidade.md`](../gestao/matriz-rastreabilidade.md), não mais espalhado entre backlog, Artefato Mestre e `HISTORICO.md`. Regra completa e atualizada: [`SKILL.md`](../../.claude/skills/vigilia/SKILL.md).

---

## 5. Uso no dia a dia

### 5.1 Loop autônomo de um agente (`agloop run`)

```bash
agloop run --name Alice --model gemini/gemini-1.5-pro-latest
```

| Flag | Descrição | Padrão |
| :--- | :--- | :--- |
| `--name` | Nome do agente (obrigatório; é o cabeçalho `## Nome` na sala) | — |
| `--model` | Modelo no formato do LiteLLM (`provedor/modelo`) | `gemini/gemini-1.5-pro-latest` |
| `--sleep` | Segundos entre iterações do loop | `10` |
| `--room` | Arquivo da Sala de Guerra | `war_room.md` |

O agente tem ferramentas **somente leitura** e confinadas ao repositório: `read_file`, `list_dir`, `git_diff` e `run_pytest`.

### 5.2 Slash commands (Claude Code)

| Comando | Para quê |
| :--- | :--- |
| `/status` | Mostra o estado da sala (`ACTIVE`, `WAITING_HUMAN` ou `CONSENSUS`) e o último orador, sem gastar tokens de LLM |
| `/debate` | Guia para abrir ou responder um turno no formato correto |
| `/vigia <Nome>` | Liga a vigília one-shot para o agente desta sessão (seção 5.3) |

### 5.3 Vigília Híbrida

Monitor passivo que **não gasta tokens enquanto espera**:

```bash
agloop-vigia --agent Gemini --once
# ou, dentro de um clone do repositório:
python3 scripts/vigia.py --agent Gemini --once
```

- Confere o `mtime` local do `war_room.md` a cada **2 s** (`--local-poll`) e faz `git fetch` a cada **30 s** (`--remote-poll`).
- Com `--once`, encerra com `exit 0` quando for a vez do agente. Rodando em segundo plano numa sessão do Claude Code, isso acorda a sessão.
- **Religue sempre:** com `--once`, a vigília encerra ao acordar o agente. O agente deve religá-la ao final de cada resposta; senão o loop para em silêncio.
- **Alarme de travamento:** `--stall-minutes 20` (ou `AGLOOP_STALL_MINUTES=20`) grava `WAITING_HUMAN` na sala se nada acontecer em 20 minutos, devolvendo a vez ao PO. Desligado por padrão.
- **Importante:** a vigília acompanha a branch em que o clone está. Deixe o clone na mesma branch onde a sala é escrita (normalmente `main`); senão ela nunca vê as respostas.

### 5.4 Ferramentas do servidor MCP (`agloop`)

| Ferramenta | O que faz |
| :--- | :--- |
| `read_war_room` | Lê os turnos recentes da sala |
| `post_war_room_message` | Escreve uma mensagem na sala com lock e commit escopado |
| `get_lock_status` | Mostra se há um lock local ativo e de quem é |
| `scan_repository` | Mesmo que `agloop scan` |

O servidor só lê e escreve `war_room.md` e `HISTORICO.md` dentro do projeto ativo (`LGPD-03`).

### 5.5 Diagnóstico de privacidade

```bash
agloop audit --privacy
```

Relatório local (sem chamar LLM) de onde há dados pessoais ou metadados de agentes no histórico do repositório (`LGPD-04`).

---

## 6. Cenários práticos

### 6.1 Dois agentes (Claude ⇄ Gemini)

O cenário clássico: os dois alternam entre Dev Especialista e Tech Lead a cada turno. `PRÓXIMO-AGENTE:` é opcional, porque sem ele cada um acorda quando o outro fala.

### 6.2 Três ou mais agentes (com Observador)

- Em cada turno, só **2** trabalham (Dev Especialista + Tech Lead); os demais são **Observadores**.
- Declare o `Roster do Turno N:` e use **sempre** `PRÓXIMO-AGENTE:`.
- **Um diretório por agente.** Agentes na mesma máquina não devem compartilhar a mesma pasta do repositório: quando um muda de branch para abrir um PR, a pasta inteira muda e a vigília do outro passa a ler a sala errada (Issue #52). Use `git worktree`:

  ```bash
  cd ~/AgLoop
  git worktree add ../AgLoop-gemini main   # pasta separada para o Gemini
  ```

- Dê **nomes distintos** a sessões do mesmo modelo (ex.: `Claude` e `Claude-Cloud`), senão o roteamento confunde as duas.
- Agentes em máquinas diferentes não compartilham o lock local: a proteção entre eles é o Git recusar o push de quem chegar depois (`lost_race`). Sempre atualize (`git pull`) antes de escrever.

### 6.3 PO operando pelo celular (sessão na nuvem)

Uma sessão do Claude Code na nuvem (claude.ai/code) pode participar da sala como mais um agente (ex.: `Claude-Cloud`) e servir de ponte entre o PO e os agentes locais: resume a sala, leva autorizações, abre issues e cuida de documentação.

Para funcionar:

1. O **Claude GitHub App** precisa estar instalado no repositório **com as permissões atualizadas** (veja a seção 8.3).
2. A sessão deve acompanhar a branch da sala (seção 5.3).
3. O container da nuvem é temporário. Se a sessão for encerrada, abra outra e ela retoma lendo a sala.

---

## 7. Governança e segurança

### 7.1 O que exige aprovação explícita do PO

- Qualquer alteração em `core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt` ou `.env`.
- Debates sem convergência após a `TRÉPLICA`.
- Qualquer mudança com testes falhando.

Documentação (`docs/`), ADRs e o próprio `war_room.md` estão na **autoridade delegada** dos agentes.

### 7.2 Gate de PR + CI

Mudanças em código de produção nunca vão direto para a `main`:

1. Branch `feat/...` ou `fix/...` a partir da `main`.
2. Pull Request + `STATUS: PR_ABERTO` na sala.
3. CI verde (`pytest` em Linux, macOS e Windows; Python 3.10, 3.11 e 3.12).
4. Auditoria do Tech Lead e squash merge.

### 7.3 Privacidade (LGPD e GDPR)

- **Local-first:** o AgLoop não envia dados a nenhum serviço próprio; o único tráfego externo é para a API de LLM que você já usa.
- **Sanitização:** e-mails e CPFs são mascarados antes de irem para o prompt (`LGPD-02`).
- **Bloqueio de segredos:** `.env`, `.env.*` e `*.pem` não são lidos pelo agente (`LGPD-01`).
- Detalhes em [`docs/gestao/lgpd-conformidade-agloop.md`](../gestao/lgpd-conformidade-agloop.md) e [`docs/gestao/gdpr-conformidade-agloop.md`](../gestao/gdpr-conformidade-agloop.md).

---

## 8. Solução de problemas

### 8.1 Lock preso (`.agloop.lock/`)

Um processo morreu segurando o lock. Na mesma máquina, ele é liberado automaticamente quando o processo dono não está mais vivo; em outra máquina, depois de `AGLOOP_LOCK_TIMEOUT` segundos (padrão 300). Se precisar liberar na mão, confirme que nenhum agente está rodando e apague a pasta `.agloop.lock/`.

### 8.2 `lost_race` (perdi a corrida do push)

Outro agente escreveu na sala primeiro. O AgLoop desfaz **só** a sua alteração na sala, sem `reset --hard` e sem tocar no resto da working tree. Releia a sala e responda de novo com o contexto novo. É o comportamento esperado.

### 8.3 `403` ao fazer push de uma sessão na nuvem

O Claude GitHub App não tem permissão de escrita no repositório. Em `github.com/settings/installations` → **Claude** → **Configure**:

1. Se houver o aviso "Claude está solicitando uma atualização de suas permissões", clique em **revisar** e **aceite**.
2. Em **Acesso ao repositório**, confirme que o repositório está selecionado.

### 8.4 A vigília não acordou

- Confira se a última mensagem tem `PRÓXIMO-AGENTE:` com o **nome exato** do seu agente.
- Confira se o clone está na **branch onde a sala é escrita** (seção 5.3).
- O `git fetch` roda a cada 30 s; espere pelo menos esse intervalo.
- Confira se o agente **religou a vigília** depois da última resposta dele (`/vigia <Nome>`).
- Use `--stall-minutes` para a sala avisar o PO quando travar.

### 8.5 Servidor MCP `agloop` não conecta

O servidor importa o pacote Python. Rode `pip install agloop` (ou `pip install -e .` no clone) no mesmo Python usado pelo Claude Code ou pelo Gemini CLI e reinicie a sessão.

### 8.6 `pip install` falha por versão inexistente

Use a versão mais recente do repositório: desde o PR #38, o `litellm` é declarado como faixa (`>=1.53,<2`), não mais como versão fixa.

---

## 9. FAQ

**A vigília gasta tokens?**
Não. Ela é um script comum que só olha datas de arquivo e faz `git fetch`. Tokens só são gastos quando o agente acorda para responder.

**Preciso de Docker?**
Não. O AgLoop é zero-infra por decisão de projeto.

**Posso usar outros modelos além de Claude e Gemini?**
Sim. Qualquer modelo suportado pelo LiteLLM, passando `--model provedor/modelo`.

**Quem decide no fim?**
O PO. Os agentes debatem e implementam; mudanças em código de produção só entram com a aprovação explícita dele.

**Onde vejo o que já foi decidido?**
No `HISTORICO.md` (turnos fechados) e no Log de Decisões de [`docs/gestao/artefatos/artefato-mestre-agloop.md`](../gestao/artefatos/artefato-mestre-agloop.md).
