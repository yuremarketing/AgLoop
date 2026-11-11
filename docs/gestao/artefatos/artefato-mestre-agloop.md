# AgLoop — Visão Geral, Governança e Status do Projeto (Artefato Mestre)

> # 🛑 REGRA MÁXIMA E ABSOLUTA: GOVERNANÇA E APROVAÇÃO HUMANA NO COMANDO
> **NENHUMA ALTERAÇÃO EM CÓDIGO DE PRODUÇÃO (`core/`, `scripts/`, `main.py`) PODE SER COMMITADA SEM: (1) DOCUMENTAÇÃO GERENCIAL E ARQUITETURAL (ADRs / MATRIZ DE RISCOS) ATUALIZADA E (2) APROVAÇÃO EXPLÍCITA DO PRODUCT OWNER (YURE MARK).**

---

## 📄 Sobre este Documento

Este é o **índice vivo (Single Source of Truth gerencial)** do projeto **AgLoop**. Enquanto as ADRs e o Termo de Abertura registram fotografias de decisão, este documento reflete continuamente o estado atual do repositório, o progresso dos marcos, os riscos monitorados e o histórico de alinhamentos da Sala de Guerra (`war_room.md`).

- **Nome do Projeto:** AgLoop
- **Origem:** Spin-off oficial da arquitetura de orquestração multi-agente criada no projeto **Sysoft**
- **Product Owner (PO) & Líder de Engenharia de IA:** Yure Mark
- **Agentes Orquestrados:** Claude (Anthropic) ⇄ Gemini / Antigravity (Google DeepMind)
- **Repositório:** [`yuremarketing/AgLoop`](https://github.com/yuremarketing/AgLoop)
- **Última atualização:** 2026-11-01 (Turno 1)

---

## 1. Visão Geral do Produto

O **AgLoop** é um framework leve e *serverless* de orquestração multi-agente baseado em **Git** (para controle de concorrência e transporte distribuído) e **Markdown** (para comunicação entre processos — IPC). Ele permite que agentes autônomos (como Claude e Gemini) debatam arquiteturas, revisem código em papéis alternados (**Dev Especialista** e **Tech Lead**) e executem tarefas por turnos sem conflitos destrutivos de Git e sem desperdício de tokens em espera ociosa.

---

## 2. Status Atual do Projeto

### 2.1 Histórico Consolidado
- **Fundação Core & Vigília Híbrida (Issue #1 — Concluída no commit `2e5cc85`):**
  - Implementado lock local atômico (`.agloop.lock/`) com detecção de processo morto (`_pid_alive`) e recuperação de *stale lock* configurável (`AGLOOP_LOCK_TIMEOUT=300s`).
  - Substituído o antigo `git add -A` e `git reset --hard HEAD~1` por commits escopados apenas aos caminhos da Sala de Guerra e reversão cirúrgica em caso de `lost_race`, preservando arquivos sujos (*dirty working tree*) de outros processos.
  - Implementada a **Vigília Híbrida** no `core/runner.py` e `scripts/vigia.py`, separando checagem local de custo zero (`mtime`) de checagem remota espaçada (`git fetch` com backoff exponencial e jitter).
  - Suíte de testes automatizados (`tests/test_git_lock.py` e `tests/test_runner.py`) cobrindo concorrência e proteção de working tree.
- **Governança Padrão Sysoft & Saneamento DRY (Issue #3 — Em execução no Turno 1):**
  - Instituída toda a estrutura `docs/gestao/`, `docs/arquitetura/decisoes/` (ADRs 0001 a 0005), Matriz de Riscos (`R01` a `R07`), `CLAUDE.md`, `GEMINI.md` e `.claude/skills/vigilia/SKILL.md`.
  - Alinhamento técnico fechado entre Gemini e Claude para autoria isolada por agente (`GIT_AUTHOR_*`/`GIT_COMMITTER_*`), fechamento/arquivamento atômico (`HISTORICO.md`) e wrapper DRY em `scripts/vigia.py`.
- **Evolução Cognitiva Google ADK (Issue #4 — Em RFC):**
  - Proposta de integração do `google-adk` (`LlmAgent` + `LiteLlm`) em `core/agent.py` com ferramentas nativas seguras, janela deslizante de contexto e marcadores de consenso/pausa humana.
- **Empacotamento Plugin & MCP (Issue #2 — Em RFC):**
  - Proposta para transformar o AgLoop em plugin distribuível para Claude Code e Antigravity (`.claude-plugin/`, Slash Commands, Skills e servidor MCP).

### 2.2 Indicadores e Metas de Qualidade

| Indicador | Meta Oficial | Status Atual |
| :--- | :--- | :--- |
| **Proteção de Working Tree em `lost_race`** | 100% dos arquivos externos preservados (Zero `reset --hard`) | ✅ Atingido (`core/git_lock.py` + `tests/test_git_lock.py`) |
| **Consumo de Tokens em Ociosidade (Vigília)** | 0 tokens (polling 100% em nível de SO via `mtime`/`fetch`) | ✅ Atingido |
| **Latência de Detecção Local (`mtime`)** | $\le 2.0\text{s}$ | ✅ Atingido |
| **Limite de Rodadas por Debate** | Máx. 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`) | ✅ Formalizado em `SKILL.md` |
| **Suíte de Testes Automatizados (`pytest`)** | 100% verde antes de qualquer commit em `main` | ✅ Atingido |

---

## 3. Índice de Artefatos de Governança e Arquitetura

### 3.1 Gestão e Governança (`docs/gestao/`)
- [`termo-abertura.md`](../termo-abertura.md) — Project Charter (Business Case, Escopo, Stakeholders, Critérios de Sucesso e Restrições).
- [`matriz-riscos.md`](../matriz-riscos.md) — Matriz de Riscos técnicos, operacionais e financeiros (`R01` a `R10`) com planos de mitigação e contingência.
- [`roadmap.md`](../roadmap.md) — Marcos estratégicos do projeto (`M1` a `M4`).
- [`backlog-produto.md`](../backlog-produto.md) — Épicos e itens de backlog rastreados contra as Issues do GitHub.
- [`glossario.md`](../glossario.md) — Definições das siglas e nomenclaturas usadas nos demais artefatos (M1–M4, R01–R10, ADR, SSOT, Vigília Híbrida, etc.).
- [`concepcao-e-elicitacao-requisitos.md`](../concepcao-e-elicitacao-requisitos.md) — Origem real dos requisitos (derivação de incidentes do Sysoft + decisão direta do PO), requisitos funcionais e não-funcionais rastreados aos épicos.
- [`estudo-campo-e-governanca-agloop.md`](../estudo-campo-e-governanca-agloop.md) — Estudo de Campo, Benchmarking Competitivo (Iguais, Parecidos e Melhores) e Matriz Comparativa Estrutural.
- [`auditoria-governanca-agloop.md`](../auditoria-governanca-agloop.md) — Diagnóstico Estrutural de Maturidade de Governança (Nível 3.8 / 5.0), análise de *blind spots* e plano de hardening para M3/M4.
- [`lgpd-conformidade-agloop.md`](../lgpd-conformidade-agloop.md) — Relatório de Mapeamento de Conformidade LGPD (Lei nº 13.709/2018), governança de dados, privacidade (`R06`, `R09`, `R10`) e requisitos `LGPD-01` a `LGPD-04`.
- [`gdpr-conformidade-agloop.md`](../gdpr-conformidade-agloop.md) — Relatório de Mapeamento de Conformidade GDPR (Regulamento (UE) 2016/679), bases legais (Art. 6º), transferência internacional (Art. 44–49), direitos em Git e Privacy by Design.
- [`painel-agloop.html`](../painel-agloop.html) — Painel visual de gestão autocontido e portável entre agentes (Marcos, Issues, Riscos, KPIs e status da Sala de Guerra — Issue #6 / Épico `E06`).
- [`docs/manual/manual-de-uso.md`](../../manual/manual-de-uso.md) — Manual de Uso para o usuário final: instalação, conceitos, uso diário, cenários com N agentes, governança e solução de problemas (Issue #37 / Épico `E12`).

### 3.2 Decisões de Arquitetura (`docs/arquitetura/decisoes/`)
- [`0001-ipc-markdown-e-git-serverless-broker.md`](../../arquitetura/decisoes/0001-ipc-markdown-e-git-serverless-broker.md) — Uso de `war_room.md` e Git como broker serverless.
- [`0002-lock-hibrido-atomico-e-reversao-cirurgica-lost-race.md`](../../arquitetura/decisoes/0002-lock-hibrido-atomico-e-reversao-cirurgica-lost-race.md) — Lock local atômico (`.agloop.lock`), recuperação de stale lock e abolição de `reset --hard`.
- [`0003-vigilia-hibrida-mtime-local-e-fetch-remoto.md`](../../arquitetura/decisoes/0003-vigilia-hibrida-mtime-local-e-fetch-remoto.md) — Arquitetura da Vigília Híbrida (`mtime` 2s + `git fetch` com backoff/jitter e despertar one-shot).
- [`0004-governanca-dry-ssot-autoria-e-fechamento-atomico.md`](../../arquitetura/decisoes/0004-governanca-dry-ssot-autoria-e-fechamento-atomico.md) — Port do Turno 72 do Sysoft (Issue #3): SSOT em `SKILL.md`, autoria Git isolada e arquivamento atômico.
- [`0005-motor-cognitivo-google-adk-e-plugin-mcp.md`](../../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md) — Arquitetura alvo para Google ADK, controle de consenso e distribuição via Plugin/MCP (Issues #2 e #4).

### 3.3 Governança Operacional de Sessão (Raiz & Skills)
- [`.claude/skills/vigilia/SKILL.md`](../../../.claude/skills/vigilia/SKILL.md) — Protocolo canônico completo da Sala de Guerra.
- [`CLAUDE.md`](../../../CLAUDE.md) & [`GEMINI.md`](../../../GEMINI.md) — Resumos executivos DRY por agente.

---

## 4. Log de Decisões e Alinhamentos

| Data | Referência | Decisão Registrada |
| :--- | :--- | :--- |
| 2026-10-22 | [Issue #1](https://github.com/yuremarketing/AgLoop/issues/1) / Commit `2e5cc85` | Aprovado pelo PO (Yure Mark) e consolidado por Claude & Gemini o endurecimento do `GitLock` (lock local atômico com stale recovery, commits escopados ao War Room, reversão cirúrgica sem `reset --hard`) e a Vigília Híbrida no `runner.py`. |
| 2026-10-22 | Commit `033bba7` | Adicionado `scripts/vigia.py` para monitoramento híbrido standalone da Sala de Guerra. |
| 2026-10-22 | [Issue #2](https://github.com/yuremarketing/AgLoop/issues/2) | Aberta RFC para empacotar o AgLoop como Plugin oficial para Claude Code e Antigravity (Slash Commands, Skills, MCP e Hooks). |
| 2026-10-22 | [Issue #3](https://github.com/yuremarketing/AgLoop/issues/3) | Aberta Issue de Governança & DRY trazendo as lições do Turno 72 do Sysoft (SSOT em `SKILL.md`, `GIT_AUTHOR_*`/`GIT_COMMITTER_*`, fallback `origin/main`, fechamento/arquivamento atômico e testes do harness). |
| 2026-11-01 | [Issue #4](https://github.com/yuremarketing/AgLoop/issues/4) | Aberta RFC para evoluir `core/agent.py` com Google ADK (`LlmAgent` + `LiteLlm`), tools nativas seguras, marcadores de consenso/pausa humana e janela deslizante. |
| 2026-11-01 | `war_room.md` (Turno 1) | Abertura formal do Turno 1 por ordem do PO Yure Mark para implantar toda a camada de governança padrão Sysoft (`docs/gestao/`, Matriz de Riscos, ADRs 0001–0005, `SKILL.md`, `CLAUDE.md`, `GEMINI.md`) antes de codificar as mudanças de `core/` das Issues #3, #4 e #2. |
| 2026-11-03 | `war_room.md` (Turno 2) / `docs/gestao/` | Conclusão e auditoria do Turno 2 (`E02.5`–`E02.8`) e incorporação dos 3 estudos gerados via NotebookLM (`estudo-campo-e-governanca-agloop.md`, `auditoria-governanca-agloop.md` e `lgpd-conformidade-agloop.md`) à governança oficial em `docs/gestao/`. |
| 2026-11-10 | [Issue #27](https://github.com/yuremarketing/AgLoop/issues/27) / `war_room.md` (Turno 18) | Formalização do Mapeamento de Conformidade GDPR (`gdpr-conformidade-agloop.md`), governança internacional de dados pessoais, transferência via SCCs/sanitização e SOP para direitos do titular em histórico Git. |
| 2026-11-10 | [Issue #28](https://github.com/yuremarketing/AgLoop/issues/28) / `war_room.md` (Turno 20) | PR #36 removeu hooks de comando para adequação técnica; constatada barreira de Verified Organization para servidores MCP stdio locais; PO decide pausar submissão ao Directory da Anthropic. |
| 2026-11-10 | [Issue #28](https://github.com/yuremarketing/AgLoop/issues/28) / `war_room.md` (Turno 21) | Foco na realidade do PO: Consolidação do Marketplace Self-Hosted no GitHub (`yuremarketing/AgLoop`) como canal oficial de distribuição, polimento de onboarding nos READMEs e fechamento formal da Issue #28. |
| 2026-11-11 | [Issue #33](https://github.com/yuremarketing/AgLoop/issues/33) / `war_room.md` (Turno 22) | Triagem formal: o AgLoop permanece **local-first por design** (soberania de dados, simplicidade de deploy e superfície mínima de ataque). Issue #33 (avaliação de servidor MCP remoto para Claude apps web/desktop/mobile) mantida aberta como backlog de longo prazo, sem compromisso de prazo nem RFC de arquitetura neste momento — qualquer implementação futura exigirá turno dedicado e aprovação explícita do PO. |
| 2026-11-11 | [Issue #28](https://github.com/yuremarketing/AgLoop/issues/28) / Ticket Anthropic `#154537355` | PO Yure Mark enviou consulta formal a `directory@anthropic.com` sobre critérios e caminho de verificação (*Verified Organization*) para desenvolvedor independente; ticket `#154537355` aberto pelo suporte da Anthropic (status: *Submitted*). Listagem no Directory segue pausada até a resposta; canal oficial continua sendo o Marketplace Self-Hosted. |
| 2026-11-11 | [PR #38](https://github.com/yuremarketing/AgLoop/pull/38) / `war_room.md` (Turno 24) | Atualização de dependência do `litellm`: substituído o pin estrito `litellm==1.44.0` (ausente em índices de containers modernos) pela faixa `litellm>=1.53,<2` em `requirements.txt` e `pyproject.toml`. Autorizado explicitamente pelo PO e auditado pelo Tech Lead via Gate de PR+CI (9/9 checks verdes em Linux, macOS e Windows). Suíte com 115 testes verdes. |
| 2026-11-11 | [PR #40](https://github.com/yuremarketing/AgLoop/pull/40) / [Issue #39](https://github.com/yuremarketing/AgLoop/issues/39) / `war_room.md` (Turno 26) | Scaffold do protocolo: `agloop init` atualizado para instalar automaticamente o template genérico de vigília em `.claude/skills/vigilia/SKILL.md` nos novos repositórios, sem dados internos do AgLoop e preservando arquivos existentes. PR #40 mergeado via Gate de PR+CI com 9/9 checks verdes. Suíte com 116 testes verdes. |
| 2026-11-11 | [PR #43](https://github.com/yuremarketing/AgLoop/pull/43) / [Issue #41](https://github.com/yuremarketing/AgLoop/issues/41) / `war_room.md` (Turno 27) | Experiência do desenvolvedor no `agloop init`: adicionado bloco com 4 passos canônicos imediatos, gancho para o onboarding guiado pelo agente (`Diga ao seu agente: "instalei o AgLoop"`) e link para o Manual de Uso. Implementada flag `-q`/`--quiet` e testes cobrindo o output e parsing CLI. PR #43 mergeado via Gate de PR+CI com 9/9 checks verdes. Suíte com 117 testes verdes. |
