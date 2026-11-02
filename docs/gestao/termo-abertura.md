# Termo de Abertura do Projeto (Project Charter) — AgLoop

Documento de referência executiva inspirado no padrão de governança do projeto **Sysoft**: estabelece por que o **AgLoop** existe, quem decide o quê, quais são os limites operacionais e o que define sucesso. A execução contínua segue o protocolo de turnos documentado em [`.claude/skills/vigilia/SKILL.md`](../../.claude/skills/vigilia/SKILL.md) e no [`artefato-mestre-agloop.md`](artefatos/artefato-mestre-agloop.md).

---

## 1. Identificação

- **Projeto:** AgLoop — Framework de Orquestração Multi-Agente Baseado em Git Lock e IPC via Markdown
- **Origem:** Extraído e generalizado a partir do harness da Sala de Guerra do projeto **Sysoft**
- **Product Owner (PO) / Engenharia de IA e Desenvolvimento:** Yure Mark
- **Arquitetura Base & Metodologia Origem (Sysoft):** Vinícius Leônidas & Yure Mark
- **Agentes de Engenharia (Dev Team / Tech Lead):** Claude & Gemini (Antigravity)
- **Repositório Oficial:** `https://github.com/yuremarketing/AgLoop`
- **Data de abertura formal da governança:** 2026-11-01

---

## 2. Justificativa (Business Case)

Equipes de engenharia assistidas por múltiplos agentes de IA (como Claude Code e Gemini/Antigravity) enfrentam três problemas críticos ao tentar colocar agentes para colaborar no mesmo repositório:
1. **Condições de corrida e perda de trabalho:** Agentes editando e executando `git add -A` ou `git reset --hard` destroem modificações em andamento de outros agentes ou do desenvolvedor humano na mesma árvore de trabalho.
2. **Infraestrutura pesada ou lock-in:** Soluções tradicionais de mensageria multi-agente exigem servidores dedicados (Redis, RabbitMQ, bancos externos), dificultando o uso plug-and-play em repositórios Git comuns.
3. **Explosão de custos de tokens:** Loops de polling ativo ou debates infinitos sem critério de parada drenam cotas de API rapidamente.

O **AgLoop** resolve essas dores utilizando o próprio **Git como broker de mensagens serverless e trava distribuída (`GitLock`)**, um arquivo **Markdown (`war_room.md`) como barramento auditável de IPC**, e a **Vigília Híbrida** (checagem local `mtime` de custo zero + `git fetch` remoto espaçado) para coordenar agentes com desperdício zero de tokens em ociosidade.

---

## 3. Escopo Macro

### Dentro do Escopo
1. **Módulo Core (`core/`):**
   - `GitLock` (`core/git_lock.py`): Lock local atômico via diretório (`.agloop.lock`) com recuperação automática de lock órfão (*stale lock* por PID/host/timeout), sincronização remota inteligente e reversão cirúrgica em caso de corrida perdida (`lost_race`) sem jamais usar `reset --hard`.
   - `WarRoom` (`core/war_room.py`): Leitura/escrita estruturada do canal de IPC em Markdown, janela deslizante de contexto e fechamento atômico com arquivamento em `HISTORICO.md`.
   - `Runner` (`core/runner.py`) & `vigia.py`: Vigília Híbrida (`mtime` local + `git fetch` remoto com backoff e jitter) e controle de estados de consenso/pausa humana (`WAITING_HUMAN` / `CONSENSUS`).
   - `Agent` (`core/agent.py`): Integração com **Google ADK (`LlmAgent` + `LiteLlm`)** equipada com ferramentas nativas seguras de inspeção de repositório (Issue #4).
2. **Empacotamento como Plugin Oficial e Servidor MCP (Issue #2):**
   - Manifesto `.claude-plugin/plugin.json`, Slash Commands (`/agloop:vigia`, `/agloop:status`, `/agloop:debate`), Skill de orquestração e camada MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`).
3. **Governança e Qualidade (Issue #3):**
   - Documentação gerencial viva (`docs/gestao/`), ADRs (`docs/arquitetura/decisoes/`), Matriz de Riscos e suíte de testes automatizados (`tests/`) com 100% de aprovação.

### Fora do Escopo (Por Ora)
- Hospedagem de infraestrutura em nuvem proprietária ou banco de dados externo para estado de conversação (todo o estado deve residir no repositório Git).
- Execução autônoma de código de produção pelos agentes sem aprovação explícita do Product Owner (Yure Mark).

---

## 4. Stakeholders e Papéis

| Papel | Responsável | Responsabilidades |
| :--- | :--- | :--- |
| **Product Owner (PO) & Líder de Engenharia de IA** | Yure Mark | Visão do produto, priorização do backlog, aprovação exclusiva de mudanças em código de produção (`core/`, `scripts/`) e arbitragem final. |
| **Dev Especialista (Turno a Turno)** | Claude ou Gemini (quem abriu o turno) | Diagnóstico técnico, elaboração da Proposta, implementação após acordo e garantia de testes verdes. |
| **Tech Lead (Turno a Turno)** | Claude ou Gemini (colega revisor) | Revisão crítica da proposta (máx. 3 rodadas), auditoria de código/diffs, verificação da Matriz de Riscos e aprovação técnica. |

---

## 5. Critérios de Sucesso

- **Integridade absoluta da Working Tree:** 0% de perda de arquivos não commitados de terceiros durante colisões de push (`lost_race`), validado por testes automatizados em `tests/test_git_lock.py`.
- **Custo Zero de Tokens em Ociosidade:** Vigília Híbrida operando 100% via checagem de sistema operacional (`mtime` + `git fetch`) e despertando a LLM exclusivamente quando houver mudança real de turno.
- **Cobertura de Testes:** Suíte `pytest` 100% verde antes de qualquer commit na branch principal.
- **Governança DRY:** Protocolo centralizado em `.claude/skills/vigilia/SKILL.md`, evitando redundância de prompt e reduzindo o consumo de contexto por turno.

---

## 6. Restrições e Premissas

- **Cláusula Pétrea de Proteção de Código:** Nenhum agente (Claude ou Gemini) pode commitar alterações em código de produção (`core/`, `scripts/`, `main.py`) sem autorização explícita do PO (Yure Mark). Apenas arquivos da Sala de Guerra (`war_room.md`) e documentação autorizada (`docs/`) possuem delegação direta.
- **Debate Limitado a 3 Rodadas:** Todo alinhamento técnico segue `PROPOSTA` → `RÉPLICA` → `TRÉPLICA`. Caso não haja consenso na 3ª rodada, o turno pausa (`WAITING_HUMAN`) e escala para decisão do PO.

---

## 7. Registro de Mudanças

| Data | Versão | Descrição | Autor |
| :--- | :--- | :--- | :--- |
| 2026-11-01 | `1.0.0` | Criação do Termo de Abertura do Projeto AgLoop espelhando a governança do Sysoft (Turno 1 / Issue #3). | Gemini & Claude (Aprovação: Yure Mark) |
