# Relatório de Estudo de Campo, Benchmarking Competitivo e Auditoria de Governança do AgLoop

Este relatório estabelece o mapeamento competitivo e a auditoria técnica do **AgLoop**, um framework leve e *serverless* de orquestração multi-agente heterogênea projetado para regular a colaboração entre modelos de inteligência artificial no desenvolvimento de software. Derivado das lições práticas do projeto Sysoft em ambientes de produção (especificamente o port do Turno 72), o AgLoop substitui infraestruturas pesadas por uma arquitetura orientada a arquivos Markdown e controle de versão via Git, impondo travas rígidas de governança no código para garantir a integridade dos repositórios.

---

## 1. Visão Geral da Arquitetura e Pilares do AgLoop

O AgLoop foi concebido para resolver os gargalos de custo, concorrência e divergência operacional comuns em sistemas multi-agente. A arquitetura opera sob a integração de seis pilares centrais:

1. **Mecanismo IPC via Markdown (Padrão Blackboard):** A comunicação assíncrona e o debate arquitetural entre os agentes ocorrem exclusivamente através do arquivo `war_room.md`, versionado via Git, onde as propostas, revisões e vereditos são registrados de forma transparente.
2. **Git como Broker Serverless e Lock Híbrido Atômico (GitLock):** O controle de concorrência combina um arquivo de travamento local (`.agloop.lock`) — auditado por verificação de PID vivo via `os.kill(pid, 0)` e expiração automatizada por tempo limite configurável (`AGLOOP_LOCK_TIMEOUT=300s`) — com operações Git descentralizadas. Em caso de colisão de *push* (*lost race*), o sistema realiza reversão cirúrgica (`git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`) sem utilizar comandos destrutivos como `git reset --hard` ou `git add -A`.
3. **Execução por Turnos com Papéis Alternados (Actor-Critic):** O sistema impõe a alternância estrita de papéis entre o *Dev Especialista* (responsável por propor e implementar soluções) e o *Tech Lead* (responsável por auditar diffs, rodar testes `pytest` e emitir o acordo), operando sob uma trava anti-loop estrita.
4. **Vigília Híbrida Zero-Token:** O monitoramento do repositório é realizado pelo script `scripts/vigia.py` (assentado sobre a rotina `watch_war_room()`), combinando a verificação de modificações no sistema de arquivos local (`mtime` a cada 2 segundos) com buscas remotas via `git fetch` em intervalo fixo (a cada 30 segundos). *Correção de auditoria (Turno 3):* o **backoff exponencial com jitter existe apenas em `run_agent_loop()`** (retentativa de sincronização após falha), não no laço de `watch_war_room()` em si. Essa abordagem acorda a sessão da LLM apenas quando a vez do agente chega, garantindo consumo zero de tokens durante o tempo de espera ociosa.
5. **Cláusula Pétrea do Product Owner (Human-in-the-Loop):** Conforme definido pela liderança do projeto (Product Owner Yure Mark), nenhuma alteração no código de produção ou arquivos críticos (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`, `.env`) pode ser commitada sem:
   - Atualização prévia da documentação gerencial e arquitetural;
   - Suíte de testes automatizados (`pytest`) 100% verde (com 26 de 26 testes passando);
   - Auditoria cruzada do agente *Tech Lead* no `war_room.md`;
   - Autorização explícita do Product Owner Yure Mark.
6. **Evolução Cognitiva e Distribuição Planejada:** Conforme a ADR 0005, o roadmap prevê a estruturação do motor cognitivo baseado no Google ADK (`LlmAgent` + `LiteLlm`) e o empacotamento da solução como plugin nativo e servidor MCP (*Model Context Protocol*).

---

## 2. Estudo de Campo: Mapeamento em Três Categorias

O ecossistema *open-source* de agentes de codificação e orquestração multi-agente apresenta soluções com abordagens divergentes para os problemas de coordenação, estado e isolamento. A análise de mercado classifica essas iniciativas em três grandes grupos em relação ao AgLoop.

### Categoria A: Iguais e Concorrentes Diretos
Compreende as ferramentas de linha de comando (CLI) e orquestradores de sessões paralelas de codificação que compartilham a tese de integrar LLMs diretamente ao ambiente de trabalho local ou terminal (como Claude Code, Gemini CLI, Antigravity, Aider e Cursor). Embora atuem no mesmo domínio de execução de código, o AgLoop se diferencia ao introduzir uma camada formal de governança com alternância de papéis *Actor-Critic* e controle de sincronização serverless sobre a linha de comando.

### Categoria B: Parecidos e Adjacentes
Reúne os frameworks multi-agente de engenharia de software — tais como MetaGPT, ChatDev, CrewAI, LangGraph, AutoGen, OpenHands, SWE-agent e Claude Squad. Essas soluções abordam a colaboração entre agentes especializados em desenvolvimento, mas dependem de arquiteturas baseadas em estado mantido em memória, bancos de dados relacionais, barramentos de mensagens, containers Docker ou *git worktrees*. O AgLoop contrasta com este grupo ao eliminar a infraestrutura dedicada, confiando o estado ao repositório Git e a arquivos Markdown.

### Categoria C: Soluções Melhores em Requisitos Específicos
Engloba plataformas que superam a implementação atual do AgLoop em dimensões arquiteturais específicas:

* **Isolamento de Workspace:** Soluções baseadas em *git worktrees* ou containers dedicados fornecem isolamento físico entre os agentes, superando o compartilhamento da mesma *working tree* do AgLoop.
* **Integração MCP Nativa:** Frameworks com suporte completo ao *Model Context Protocol* oferecem interoperabilidade superior com ferramentas externas.
* **Observabilidade e Telemetria:** Ferramentas com painéis gráficos avançados e rastreamento de chamadas oferecem maior visibilidade do que a auditoria documental em Markdown.
* **Sandboxing e Segurança:** Ambientes altamente confinados (como OpenHands ou SWE-agent) garantem execução isolada de código contra efeitos colaterais no sistema hospedeiro.

---

## 3. Matriz Comparativa Estrutural de Arquitetura

A avaliação comparativa a seguir analisa o comportamento do AgLoop frente às principais abordagens do ecossistema *open-source* nos seis critérios fundamentais de arquitetura e governança.

| Critério de Avaliação | Abordagem do AgLoop | Frameworks em Memória / Container (MetaGPT, CrewAI, AutoGen) | Ferramentas CLI / Swarms (Aider, Claude Squad) |
| :--- | :--- | :--- | :--- |
| **Mecanismo IPC e Estado** | Arquivo Markdown compartilhado (`war_room.md`) sob padrão *Blackboard* e Git serverless | Memória RAM, APIs HTTP/gRPC, Redis ou bancos de dados relacionais | Arquivos temporários, *pipes* de sistema ou chamadas diretas de terminal |
| **Controle de Concorrência e Isolamento** | Lock atômico `.agloop.lock` com verificação de PID vivo e reversão cirúrgica via Git | Múltiplos containers Docker ou processos isolados em memória | *Git worktrees* separados ou execução sequencial de comandos |
| **Custo de Tokens em Ociosidade** | **Zero-Token:** Vigília passiva por `mtime` local (2s) e `git fetch` em backoff/jitter | **Variável/Elevado:** *Polling* ativo via API de LLM ou servidores sempre ativos | **Variável:** Depende do ciclo de invocação manual ou rotinas de *polling* |
| **Suporte Multi-Modelo Real** | Orquestração heterogênea nativa (Claude Code ⇄ Gemini/Antigravity) | Suporte a múltiplos provedores via código, mas com acoplamento em memória | Geralmente focado em um único provedor ou CLI proprietária |
| **Qualidade do Debate e Governança** | Trava anti-loop rígida de 3 rodadas + Cláusula Pétrea com aprovação humana obrigatória | Regras baseadas em prompts operacionais com risco de loops de reflexão | Dependente de comandos manuais do usuário ou políticas do editor |
| **Facilidade de Instalação** | **Zero-Infra:** Execução *serverless* direta no repositório, sem Docker ou Redis | **Complexa:** Exige provisionamento de infraestrutura, Docker e dependências | **Simples:** Instalação de pacote local ou extensão de ambiente |

---

## 4. Análise Crítica: Diferenciais Competitivos ("Moat") e Vulnerabilidades

### Diferenciais Competitivos Exclusivos
* **Vigília Híbrida Zero-Token:** A capacidade de manter agentes em estado de alerta via `scripts/vigia.py` sem realizar chamadas de API reduz custos operacionais em ciclos de espera prolongados.
* **GitLock Cirúrgico sem Comandos Destrutivos:** A abolição de `git add -A` e `git reset --hard` (conforme formalizado na ADR 0002) assegura que alterações não rastreadas ou códigos em desenvolvimento jamais sejam sobrescritos durante a resolução de conflitos de *push*.
* **Trava Anti-Loop de Três Rodadas:** A limitação numérica estrita (PROPOSTA → RÉPLICA → TRÉPLICA) impede o esgotamento de orçamento por discussões perpétuas entre agentes.
* **Governança Imposta no Código (`core/`):** A substituição de instruções de prompt por verificações em nível de sistema operacional (locks, autoria isolada e testes de integração) impede a evasão de regras por alucinação.
* **Arquitetura Documental DRY:** A centralização do protocolo operacional em uma única fonte de verdade (`.claude/skills/vigilia/SKILL.md`), acompanhada pelos resumos enxutos `CLAUDE.md` e `GEMINI.md`, mantém a coerência entre diferentes LLMs sem duplicar contextos (mitigando o Risco R05).
* **Estrutura de Gestão Completa:** Mantém o índice vivo gerencial (`artefato-mestre-agloop.md`), os artefatos de gestão (`termo-abertura.md`, `concepcao-e-elicitacao-requisitos.md`, `matriz-riscos.md`, `roadmap.md`, `backlog-produto.md`, `glossario.md`) e os registros formais de arquitetura (ADR 0001 a ADR 0005).

### Vulnerabilidades Arquiteturais e Pontos Cegos
* **Compartilhamento da Mesma Working Tree:** Agentes atuando simultaneamente no mesmo diretório de trabalho podem gerar interferências cruzadas em arquivos intermediários antes da fase de commit.
* **Gargalo de IPC em Arquivo Único:** A centralização do debate no `war_room.md` pode criar contenção de escrita durante execuções de alta frequência, aliviada pela rotina de arquivamento atômico em `HISTORICO.md`.
* **Ausência de Confinamento Nativo de Tools:** Atualmente, os agentes dependem da disciplina de papéis e da intervenção humana para evitar a leitura de arquivos sensíveis ou execução de comandos não autorizados.

---

## 5. Auditoria de Governança e Diagnóstico de Maturidade

A governança do AgLoop é avaliada em **Nível 3.8 em uma escala de 1.0 a 5.0** para sistemas multi-agente em produção. *Ressalva de auditoria (Turno 3):* esta é uma **autoavaliação qualitativa interna** do próprio projeto (sem citação de metodologia externa certificadora) — deve ser lida como diagnóstico de maturidade do AgLoop contra seus próprios marcos, não como benchmark validado por terceiros.

Essa pontuação fundamenta-se na conclusão bem-sucedida dos **Marcos M1 e M2**, nos quais as travas operacionais foram transpostas de prompts instrucionais para mecanismos executáveis no pacote `core/`, validados por uma suíte de testes com **26 de 26 testes `pytest` passando**.

```
[Nível 1: Prompts Soltos] ──► [Nível 2: Scripts Manuais] ──► [Nível 3.8: AgLoop Atual (M1/M2)] ──► [Nível 5: ADK Sandbox + MCP (M3/M4)]
```

### Mecanismos de Controle Impostos em Código
1. **Trava de Concorrência Local (`.agloop.lock`):** Gerenciada por diretório atômico contendo `owner.json`. Valida se o processo proprietário está ativo via `os.kill(pid, 0)` e aplica expiração automática por tempo limite configurável (`AGLOOP_LOCK_TIMEOUT=300s`), conforme estabelecido na ADR 0002.
2. **Isolamento de Autoria no Git:** Injeta as variáveis de ambiente `GIT_AUTHOR_NAME`, `GIT_AUTHOR_EMAIL`, `GIT_COMMITTER_NAME` e `GIT_COMMITTER_EMAIL` diretamente no subprocesso de execução do Git, prevenindo a poluição do ambiente global e garantindo a rastreabilidade exata do agente autor (Épico E02.5 / ADR 0004).
3. **Fechamento e Arquivamento Atômico:** A função `close_turn_and_archive()` move rodadas passadas da sala de guerra para o arquivo `HISTORICO.md` e realiza o commit unificado de ambos os arquivos em uma única transação atômica (Épico E02.6 / ADR 0004).
4. **Vigília Zero-Token (`scripts/vigia.py`):** Executa o monitoramento por verificação de atributos de arquivo (`mtime` local a cada 2 segundos) e atualizações remotas via `git fetch` (intervalo fixo de 30 segundos, sem backoff/jitter neste laço — ver correção de auditoria na Seção 6), encerrando a execução com código zero apenas quando a resposta do agente colega é detectada (Épico E02.7 / ADR 0003).

---

## 6. Matriz Consolidada de Riscos e Análise de Brechas (*Blind Spots*)

A gestão de riscos do AgLoop estrutura-se na Matriz Consolidada de Riscos (R01 a R08), que detalha o status operacional e as estratégias de mitigação técnica.

| ID | Descrição do Risco | Status Atual | Mecanismo de Mitigação Implementado / Planejado |
| :--- | :--- | :--- | :--- |
| **R01** | Ping-pong infinito de turnos e consumo descontrolado de tokens | **Em Mitigação** | Trava estrita de 3 rodadas definida no protocolo `SKILL.md` e marcadores de consenso (`CONSENSUS`) e espera humana (`WAITING_HUMAN`) |
| **R02** | Perda de código em alterações não salvas por comandos destrutivos | **Mitigado** | Commits restritos aos arquivos de estado e reversão cirúrgica via `git reset --soft` e `git checkout` |
| **R03** | Deadlock local por arquivo de trava órfão decorrente de falhas | **Mitigado** | Checagem de processo ativo via `os.kill` e timeout de expiração em 300 segundos no `.agloop.lock` |
| **R04** | Falha do monitor de vigília em acordar a sessão do agente | **Mitigado** | Script `vigia.py --once` unificado sobre `watch_war_room()` com encerramento em `exit 0` ao detectar resposta |
| **R05** | Triplicação de regras operacionais e inflação de prompt | **Mitigado** | Arquitetura DRY com SSOT em `SKILL.md` e resumos executivos enxutos na raiz (`CLAUDE.md`, `GEMINI.md`) |
| **R06** | Execução destrutiva ou vazamento de segredos (`.env`) via ferramentas | **Em Mitigação** | Cláusula Pétrea do PO e desenvolvimento do sandbox de ferramentas read-only no Marco M3 (Issue #4) |
| **R07** | Crescimento desmedido da sala de guerra estourando a janela de contexto | **Mitigado** | Arquivamento atômico automático de turnos passados para o arquivo `HISTORICO.md` via `close_turn_and_archive()` |
| **R08** | Inconsistência na identificação de autoria nos commits do Git | **Mitigado** | Injeção isolada de variáveis de autoria por subprocesso e commit final unificado de fechamento |

### Análise de Brechas Operacionais (*Blind Spots*)
Apesar da robustez dos Marcos M1 e M2, a auditoria identifica brechas que exigem atenção nas próximas fases:

* **Vulnerabilidade a Prompt Injection Indireto:** Um agente pode interpretar dados maliciosos presentes em arquivos de terceiros ou relatórios de erros e alterar o fluxo de debate no `war_room.md`.
* **Risco de Acesso a Variáveis de Ambiente (R06):** Sem um sandbox de execução no nível de ferramentas, agentes possuem capacidade técnica de ler arquivos confidenciais como `.env`.
* **Tratamento de Exceções no Observador:** A rotina do observador necessita de um tratamento abrangente de exceções no laço `watch_war_room()` para capturar falhas fora do escopo de erros nativos `GitCommandError`. *Nota de auditoria (Turno 3):* por este motivo `R04` foi revertido de `Mitigado` para `Em Mitigação` na `matriz-riscos.md` — este relatório e a `matriz-riscos.md` estavam em contradição entre si.

---

## 7. Roadmap de Evolução: Absorção de Melhores Práticas e Marcos M3/M4

Para manter a liderança em governança e eficiência sem comprometer a filosofia *serverless*, o AgLoop estabelece um plano de absorção técnica baseado nas cinco melhores práticas identificadas no mercado.

```
[Marco M1/M2: Core & Governança] ──► [Marco M3: Google ADK & Confinamento] ──► [Marco M4: Plugin Nativo & MCP Server]
```

### As Cinco Melhores Práticas a Absorver
1. **Adição de Isolamento por Git Worktrees:** Oferecer suporte opcional a *worktrees* separados para permitir que agentes trabalhem em ramificações paralelas sem colidir alterações pendentes na mesma *working tree*.
2. **Confinamento Rígido de Tools (Google ADK):** Restringir as permissões de escrita e bloquear o acesso a arquivos sensíveis (como `.env`) diretamente no manipulador de ferramentas do motor cognitivo (Issue #4).
3. **Distribuição via Protocolo MCP:** Empacotar a governança e o gerenciamento da sala de guerra como um servidor MCP reutilizável por qualquer cliente compatível (Issue #2).
4. **Resolução Assistida de Conflitos:** Implementar rotinas automáticas de mesclagem para lidar com discrepâncias simples de documentação no `war_room.md`.
5. **Telemetria e Métricas de Eficiência:** Adicionar relatórios de consumo de tempo e tokens por rodada para auditoria de desempenho.

### Diretrizes para os Próximos Marcos de Desenvolvimento
* **Marco M3 (Google ADK e Confinamento Cognitivo):** Estruturação do motor cognitivo utilizando `LlmAgent` e a biblioteca `LiteLlm` para viabilizar a interoperabilidade multi-modelo com confinamento estrito de permissões de ferramentas, solucionando o Risco R06 e a Issue #4.
* **Marco M4 (Empacotamento e Distribuição):** Transformação dos mecanismos de governança do AgLoop em um plugin nativo e servidor MCP, atendendo às Issues #2 e #4 para simplificar a adoção por times de engenharia e mantendo a garantia de custo zero em ociosidade.
