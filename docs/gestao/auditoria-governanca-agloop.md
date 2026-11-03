# Auditoria Completa de Governança Técnica do AgLoop

Este relatório apresenta a auditoria técnica e o diagnóstico de governança do framework **AgLoop**, uma arquitetura *serverless* e zero-infraestrutura projetada para orquestrar agentes de codificação heterogêneos (como Claude Code e Gemini/Antigravity). Derivado das lições aprendidas no ambiente de produção do projeto Sysoft, o AgLoop substitui orquestradores baseados em servidores centrais por uma abordagem descentralizada ancorada no Git, em arquivos Markdown compartilhados e em travas impostas diretamente no código-fonte.

A auditoria a seguir examina o nível de maturidade do framework na escala internacional de governança agêntica, contrasta seus mecanismos de controle com as principais alternativas do mercado open-source, mapeia os pontos cegos (*blind spots*) e vetores de risco ainda existentes, e estabelece o plano de ação detalhado para os Marcos M3 e M4 do projeto.

---

## 1. Diagnóstico Estrutural de Maturidade de Governança (Nível 3.8 / 5.0)

Em uma avaliação padronizada para sistemas multi-agente operando em ambientes de desenvolvimento e engenharia de software, o **AgLoop atinge a marca de Maturidade Nível 3.8 em uma escala de 1.0 a 5.0**.

A classificação do AgLoop reflete a transição conclusiva de uma governança baseada em instruções de linguagem natural ("prompt engineering") para um modelo em que as regras operacionais são **impostas diretamente pelo código-fonte** no diretório `core/`.

| Nível de Maturidade | Classificação | Caracterização Arquitetural no AgLoop | Status no Projeto |
| :--- | :--- | :--- | :--- |
| **Nível 1.0** | *Ad-hoc / Prompt-only* | Regras operacionais dependem exclusivamente de instruções no prompt inicial dos agentes, sendo vulneráveis a desvios. | Superado |
| **Nível 2.0** | *Orquestração em Memória* | Controle de estado mantido em processos ativas de aplicação (ex.: LangGraph/CrewAI), mas sem proteção no nível do Git local. | Superado |
| **Nível 3.0** | *Governança Imposta em Código* | Travas atômicas de arquivo (`.agloop.lock`), controle de versão cirúrgico sem `git reset --hard`, e vigília zero-token ativada no SO. | **Concluído (Marcos M1/M2)** |
| **Nível 4.0** | *Confinamento Estrito & Sandbox* | Confinamento total de escopo e leitura de *tools* (impede leitura de `.env` e escrita não autorizada via Google ADK). | **Em Andamento (Marco M3)** |
| **Nível 5.0** | *Distribuição Padronizada (MCP)* | Governança encapsulada e distribuída nativamente como Plugin e Servidor MCP reutilizável em qualquer ecossistema. | **Planejado (Marco M4)** |

### Fundamentação do Score de Maturidade (3.8 / 5.0)

O avanço do AgLoop para a nota 3.8 baseia-se na entrega completa dos Marcos M1 e M2 do projeto, demonstrado pelos seguintes pilares:

* **Superação da Dependência de Prompt (Mitigação do Risco R05):** Ao centralizar o protocolo operacional na Fonte Única de Verdade (*Single Source of Truth* - SSOT) em `.claude/skills/vigilia/SKILL.md` e criar ponteiros enxutos (`CLAUDE.md` e `GEMINI.md`), o sistema reduziu a inflação de tokens e eliminou a divergência de comportamento entre LLMs de fornecedores diferentes.
* **Integridade Rígida da Suíte de Testes:** O sistema mantém uma suíte automatizada via `pytest` com **26 de 26 testes unitários e de integração passando com 100% de sucesso**, validando cenários de concorrência e manipulação do Git.
* **Mecanismos de Bloqueio em Nível de Sistema Operacional (Mitigação dos Riscos R02, R03 e R04):** O módulo `core/` impõe a trava atômica local via `.agloop.lock` com validação de PID ativo (`os.kill`) para evitar *deadlocks*, extingue comandos destrutivos no Git (banindo `git add -A` e `git reset --hard`) e fornece a vigília zero-token (`scripts/vigia.py`) que zera o consumo de API em estado de ociosidade.

A fração restante para atingir o Nível 5.0 decorre da necessidade de finalizar o confinamento de *tools* do motor cognitivo no Marco M3 (Risco R06) e implementar a abstração nativa via Servidor MCP no Marco M4.

---

## 2. Análise Comparativa de Mecanismos de Controle contra o Mercado

Os mecanismos de controle do AgLoop foram desenhados especificamente para contornar os gargalos de infraestrutura e os custos operacionais observados em frameworks tradicionais de agentes (como LangGraph, AutoGen, CrewAI e MetaGPT).

O quadro a seguir sintetiza a comparação entre os mecanismos do AgLoop e as abordagens convencionais do mercado.

| Dimensão de Governança | Abordagem do AgLoop | Abordagem Tradicional do Mercado | Vantagem Competitiva / Impacto Operacional |
| :--- | :--- | :--- | :--- |
| **Aprovação de Produção** | Cláusula Pétrea do PO com 4 pré-requisitos obrigatórios. | Aprovação manual ad-hoc ou ausente em fluxos autônomos. | Elimina o risco de commits prematuros ou não testados em produção. |
| **Controle de Debate** | Trava Anti-Loop estrita de 3 rodadas (PROPOSTA → RÉPLICA → TRÉPLICA). | Loops de conversação indeterminados entre agentes. | Mitiga o Risco R01, prevenindo custos descontrolados por divergência perpétua. |
| **Isolamento de Código** | GitLock com reversão cirúrgica (`reset --soft` + `checkout`). | Uso de múltiplos containers Docker ou *git worktrees*. | Garante *zero-infraestrutura* sem correr risco de perda de código na *working tree*. |
| **Consumo em Espera** | Vigília Híbrida Zero-Token (`mtime` local + `git fetch` com *backoff*). | *Polling* contínuo de chamadas a APIs de LLMs ou servidores ativos. | Reduz a zero o custo financeiro de tokens durante a espera do agente colega. |
| **Gestão de Regras** | SSOT DRY centralizada em `SKILL.md` com arquivos-ponte enxutos. | Duplicação de prompts extensos para cada agente do sistema. | Previne o Risco R05 de perda de contexto e desalinhamento comportamental. |

### Detalhamento dos Pilares de Governança do AgLoop

#### Cláusula Pétrea do Product Owner (Human-in-the-Loop)
Nenhuma alteração nos diretórios e arquivos críticos de produção (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`, `.env`) pode ser commitada sem atender a quatro exigências cumulativas:
1. Atualização prévia da documentação gerencial e arquitetural (ADRs e Matriz de Riscos);
2. Suíte de testes automatizados (`pytest`) 100% verde (26/26 testes passando);
3. Auditoria cruzada do agente atuando no papel de Tech Lead registrada na Sala de Guerra (`war_room.md`);
4. Aprovação explícita e inafastável do Product Owner (Yure Mark).

#### Protocolo Actor-Critic e Trava Anti-Loop de 3 Rodadas
O debate técnico entre os agentes no arquivo `war_room.md` segue a alternância de papéis sem atribuição fixa:
* **Dev Especialista:** Agente que inicia o turno (`<!--INICIANDO_TURNO-->`), elabora a proposta arquitetural, implementa o código após o alinhamento e submete o *diff*.
* **Tech Lead:** Agente colega que audita a proposta, inspeciona o `git diff` real, executa a suíte de testes e concede o parecer (`STATUS: ACORDO`).
* **Trava Rigorosa (Risco R01):** O debate é limitado a no máximo 3 trocas (PROPOSTA → RÉPLICA → TRÉPLICA). Caso os agentes não atinjam convergência na 3ª rodada, a execução entra em congelamento obrigatório até a mediação humana.

#### Proteção da Working Tree (GitLock)
Para mitigar o Risco R02 (perda de código não commitado), o AgLoop aboliu os comandos `git add -A` e `git reset --hard`. Commits automáticos são estritamente restritos a arquivos de governança (`war_room.md` e `HISTORICO.md`). Em situações de colisão de *push* no repositório remoto (*lost race*), o sistema aplica a reversão cirúrgica combinando `git reset --soft HEAD~1` com `git checkout HEAD -- <paths>`, preservando todas as modificações locais da árvore de trabalho.

---

## 3. Diagnóstico de Brechas Operacionais e Pontos Cegos (*Blind Spots*)

Apesar do avanço consolidado nos Marcos M1 e M2, a auditoria identificou quatro brechas operacionais e vetores de risco que demandam mitigação técnica no roadmap do projeto.

### 1. Compartilhamento da Mesma Working Tree Local
* **Vulnerabilidade:** Diferente de arquiteturas que isolam workspaces via *git worktrees* ou containers dedicados, o AgLoop permite que dois agentes operem sobre o mesmo diretório local.
* **Impacto:** Se dois agentes tentarem editar arquivos de código simultaneamente fora do protocolo de turnos do `war_room.md`, pode ocorrer contaminação cruzada de arquivos temporários ou condições de corrida na compilação.

### 2. Injeção Indireta de Prompt (*Prompt Injection*) via Markdown e Comentários
* **Vulnerabilidade:** A leitura do arquivo `war_room.md` ou de trechos de código/comentários contendo instruções maliciosas pode induzir um agente a violar o protocolo de papéis.
* **Impacto:** Um trecho de código auditado contendo instruções formatadas como tags de sistema (ex.: `<!--FIM_TURNO-->`) poderia forçar o encerramento prematuro do turno ou burlar a regra de silêncio do Tech Lead.

### 3. Risco R06 — Chamadas Não Confinadas de Ferramentas (*Tools*) do Agente
* **Vulnerabilidade:** No estágio atual, a execução de ferramentas nativas por agentes CLI depende da disciplina do modelo ou das permissões do sistema operacional do usuário.
* **Impacto:** Um agente operando como Dev Especialista pode tentar ler arquivos sensíveis de credenciais (como `.env`) ou executar comandos de escrita no sistema antes do aval do Product Owner.

### 4. Hardening de Exceções no Watcher de Vigília
* **Vulnerabilidade:** A função `watch_war_room()` no módulo `core/runner.py` trata nativamente exceções do tipo `GitCommandError`, mas pode interromper o laço de monitoramento caso ocorram falhas atípicas de E/S de disco ou erros de rede não previstos durante o `git fetch`.
* **Impacto:** O agente pode não ser acordado para o seu turno, gerando uma paralisação silenciosa do processo de vigília.

---

## 4. Plano de Ação e Hardening Técnica (Marcos M3 e M4)

Para sanar as brechas diagnosticadas e elevação do framework ao Nível 5.0 de maturidade, estabelece-se o seguinte plano de ação estruturado para as próximas etapas do projeto.

```
[ Diagnóstico Nível 3.8 ] ──► [ Marco M3: Confinamento ADK & Hardening ] ──► [ Marco M4: Plugin & Servidor MCP ] ──► [ Maturidade Nível 5.0 ]
```

### Ações para o Marco M3 (Motor Cognitivo & Confinamento)

1. **Implementação de Sandboxing de Tools via Google ADK (`Issue #4`):**
   * Configurar o motor cognitivo utilizando `LlmAgent` integrado ao `LiteLlm`.
   * Definir permissões de *tools* baseadas no papel ativo: o agente em papel de Tech Lead recebe *tools* em modo estritamente *read-only* (leitura de arquivos e execução de testes), enquanto ferramentas de modificação de código ficam bloqueadas para commit sem o sinalizador de aprovação.
2. **Bloqueio Nativo de Leitura de Segredos (Mitigação do Risco R06):**
   * Injetar filtros de caminho de arquivo no manipulador de E/S do agente para proibir a leitura ou exposição de `.env`, chaves SSH e certificados em qualquer etapa do debate.
3. **Resiliência do Laço de Vigília (*Watcher Hardening*):**
   * Adicionar um mecanismo de captura genérica de exceções (*catch-all*) no laço de monitoramento de `watch_war_room()`, garantindo que falhas transitórias de conexão de rede ou E/S entrem em modo de repetição (*retry*) com *backoff* exponencial em vez de encerrar o processo.

### Ações para o Marco M4 (Distribuição e Padronização)

1. **Empacotamento como Servidor MCP (*Model Context Protocol*):**
   * Abstrair os utilitários de lock (`.agloop.lock`), controle de turnos do `war_room.md` e verificação do Git em um Servidor MCP padronizado (ADR 0005).
   * Permitir que qualquer cliente compatível com a especificação MCP conecte-se à governança do AgLoop de forma transparente.
2. **Distribuição via Plugin Nativo:**
   * Disponibilizar o AgLoop como um plugin instalável para CLIs de mercado, eliminando a necessidade de cópia manual da pasta `core/` e scripts para dentro dos repositórios dos usuários.
