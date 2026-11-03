# Relatório de Mapeamento de Conformidade LGPD, Governança de Dados e Privacidade no Projeto AgLoop

## 1. Visão Geral da Arquitetura do AgLoop sob a Ótica da LGPD

O **AgLoop** é uma arquitetura de orquestração multi-agente heterogênea (como Claude Code, Gemini CLI e OpenAI) voltada para o desenvolvimento de software autônomo. Sua infraestrutura é caracterizada por ser 100% *serverless* e *zero-infra*, dispensando bancos de dados centralizados, servidores dedicados ou infraestrutura conteinerizada complexa. Toda a comunicação inter-agentes (IPC) ocorre por meio do padrão *Blackboard* utilizando o arquivo Markdown local `war_room.md`, com versionamento e controle de concorrência garantidos pelo Git e por locks atômicos no sistema operacional.

Sob a perspectiva da **Lei Geral de Proteção de Dados (LGPD — Lei nº 13.709/2018)**, a arquitetura descentralizada do AgLoop oferece vantagens estruturais relevantes em relação a frameworks corporativos tradicionais baseados em nuvem. Como o estado do sistema permanece confinado ao repositório Git local do desenvolvedor ou da organização, o risco de vazamentos em bancos de dados centralizados do orquestrador é nulo. Contudo, a interação entre agentes autônomos e APIs externas de Modelos de Linguagem (LLMs) introduz pontos de atenção críticos no tratamento de dados pessoais de desenvolvedores (como nomes e e-mails em metadados de commits) e no eventual tráfego indevido de dados pessoais contidos no código-fonte ou em arquivos de configuração.

| Componente Arquitetural | Armazenamento de Dados | Risco sob a Ótica da LGPD | Mecanismo de Controle do AgLoop |
| :--- | :--- | :--- | :--- |
| **Sala de Guerra (`war_room.md`)** | Markdown Local e Git | Exposição inadvertida de PII ou chaves em histórico | Fechamento atômico e migração para `HISTORICO.md` |
| **Arquivos de Configuração (`.env`)** | Sistema de Arquivos Local | Vazamento de credenciais e segredos de acesso | Risco R06 — Cláusula Pétrea e Sandbox no Marco M3 |
| **Metadados de Commit (Git)** | Log do Git (Local e Remoto) | Exposição de dados identificáveis de autores | Injeção isolada de `GIT_AUTHOR_*` por subprocesso |
| **Chamadas de API para LLMs** | Tráfego Externo (HTTPS) | Transferência internacional e retenção por provedores | Confinamento de escopo via `LiteLlm` e Google ADK |

---

## 2. Mapeamento de Riscos de Privacidade na Matriz de Riscos (R06, R09 e R10)

A governança do AgLoop mapeia e mitiga ativamente os riscos operacionais do sistema (Riscos R01 a R08). Para garantir total alinhamento com os pilares de segurança da informação e privacidade da LGPD, os aspectos de vazamento de credenciais e exposição de dados foram consolidados e expandidos na Matriz de Riscos.

### Ampliação do Risco R06: Execução Destrutiva ou Vazamento de Segredos (`.env`)
O Risco R06 foca na possibilidade de um agente autônomo, ao utilizar suas ferramentas (*tools*) de leitura ou execução de comandos, acessar e expor arquivos contendo chaves de API, tokens de autenticação ou credenciais de bancos de dados contendo dados pessoais. Atualmente enquadrado como **Em Mitigação**, a resposta ao Risco R06 exige o confinamento em nível de código no Marco M3, impedindo que ferramentas nativas leiam diretórios sensíveis ou arquivos `.env`.

### Inclusão dos Novos Riscos R09 e R10 no Escopo de Privacidade
Para abarcar com precisão as exigências dos Artigos 46 e 47 da LGPD (Segurança e Sigilo de Dados), dois novos riscos foram formalizados na matriz do projeto.

| ID | Risco de Privacidade / LGPD | Impacto / Probabilidade | Status Atual | Mecanismo de Mitigação no AgLoop |
| :--- | :--- | :--- | :--- | :--- |
| **R06** | Vazamento de `.env` ou segredos via *Tools* | Alto / Média | **Em Mitigação** | Sandbox *read-only* de *tools* e bloqueio de arquivos sensíveis no Marco M3 (Issue #4). |
| **R09** | Exposição não intencional de PII de desenvolvedores em logs e commits | Médio / Baixa | **Mitigado** | Isolamento de variáveis `GIT_AUTHOR_*` por subprocesso (E02.5) sem poluir o `os.environ` global. |
| **R10** | Transferência Internacional de Dados Pessoais via payload de LLM | Alto / Média | **Planejado (M3/M4)** | Sanitização prévia de *payloads* no `scripts/vigia.py` e mascaramento local antes do envio à API. |

---

## 3. Adequação aos Princípios Fundamentais da LGPD (Artigo 6º)

A conformidade do AgLoop é estruturada diretamente sobre os princípios dispostos no Artigo 6º da LGPD:

1. **Princípio da Minimização e Necessidade (Art. 6º, III):**
   O AgLoop adota o conceito de *Vigília Híbrida Zero-Token* (`scripts/vigia.py`). O sistema não envia o conteúdo completo do repositório continuamente para as LLMs em intervalos de espera. O monitoramento ocorre em nível de sistema de arquivos (`mtime` local a cada 2s), e o payload contendo o contexto da tarefa só é transmitido no exato instante em que a sessão do agente acorda.

2. **Princípio da Segurança e Prevenção (Art. 6º, VII e VIII):**
   A arquitetura impõe governança técnica diretamente em código (`core/`), abolindo comandos destrutivos da árvore de trabalho (como `git reset --hard`) e utilizando o mecanismo GitLock para garantir a integridade dos dados e impedir a corrupção do repositório em colisões de concorrência (*lost race*).

3. **Princípio da Transparência e Responsabilização (Art. 6º, VI e X):**
   A rastreabilidade é total. Cada decisão arquitetural é documentada em ADRs (ADR 0001 a ADR 0005), e o debate entre agentes é registrado no `war_room.md` e arquivado atomicamente no `HISTORICO.md`. Além disso, a **Cláusula Pétrea do Product Owner (Yure Mark)** garante que nenhum código alterando o comportamento do sistema seja enviado para produção sem autorização humana e validação por testes automatizados (`pytest` 100% verdes).

---

## 4. Plano de Ação e Requisitos no Backlog de Produto (Marcos M3 e M4)

Para consolidar a conformidade com a LGPD nas próximas entregas do projeto, foram definidos requisitos técnicos específicos para os Marcos M3 e M4 no backlog do AgLoop.

### Requisitos para o Marco M3 (Motor Cognitivo ADK & Confinamento)
* **Requisito LGPD-01 (Filtro de Arquivos Sensíveis):** Implementar no `LlmAgent` (Google ADK / `LiteLlm`) uma lista de bloqueio (*blacklisting*) automática para leitura de arquivos `.env`, `.pem`, `id_rsa` e arquivos de credenciais.
* **Requisito LGPD-02 (Sanitização de Prompts):** Adicionar um módulo de varredura prévia no `scripts/vigia.py` para mascarar CPFs, e-mails ou dados pessoais identificadores presentes em trechos de código submetidos à revisão do *Tech Lead*.

### Requisitos para o Marco M4 (Plugin Nativo & Servidor MCP)
* **Requisito LGPD-03 (Isolamento de Escopo MCP):** Garantir que o Servidor MCP do AgLoop limite as permissões das *tools* exclusivamente ao diretório do projeto ativo (*workspace sandboxing*).
* **Requisito LGPD-04 (Relatório de Auditoria de Dados):** Disponibilizar um comando CLI (`agloop audit --privacy`) que gera um diagnóstico local exibindo onde dados identificáveis ou metadados de agentes estão armazenados no histórico do repositório.

---

## 5. Diretrizes e Checklist de Conformidade para Desenvolvedores

Para equipes que utilizam o AgLoop em repositórios corporativos que lidam com dados pessoais de clientes ou usuários, aplicam-se as seguintes diretrizes operacionais:

> **Checklist de Segurança e Privacidade do AgLoop:**
> 1. **Verificação de Ignorados (`.gitignore`):** Confirmar que arquivos `.env`, bancos de dados locais (`.sqlite`, `.db`) e pastas de logs estão incluídos no `.gitignore` antes de iniciar a Sala de Guerra.
> 2. **Validação da Cláusula Pétrea:** Garantir que o *Product Owner* verifique se novos scripts de automação não contêm credenciais codificadas (*hardcoded secrets*).
> 3. **Execução de Testes de Sanidade:** Manter a suíte de testes `pytest` (26/26 testes) como pré-requisito bloqueante para qualquer commit em código de produção (`core/` e `scripts/`).
