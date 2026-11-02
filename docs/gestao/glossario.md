# Glossário — AgLoop

Definições das siglas, nomenclaturas e termos usados nos demais artefatos de governança e arquitetura do projeto. Criado para eliminar ambiguidade de leitura — humana ou automatizada — sobre notações como `M1`, `R01`, `E01` e termos operacionais da Sala de Guerra.

---

## 1. Papéis e Processo

| Termo | Significado |
| :--- | :--- |
| **PO** | Product Owner. No AgLoop, Yure Mark — dono da visão de produto, priorização e aprovação final de código de produção. |
| **Dev Especialista** | Papel assumido por quem abre o turno (`<!--INICIANDO_TURNO-->`) no `war_room.md`: propõe o plano, aguarda revisão, executa após acordo. |
| **Tech Lead** | Papel assumido pelo agente colega naquele turno: audita a proposta em até 3 rodadas e aprova com `STATUS: ACORDO`. Mantém a Regra de Silêncio (economia de tokens). |
| **Proposta / Réplica / Tréplica** | As 3 rodadas permitidas de debate técnico por turno, nessa ordem. Sem consenso até a Tréplica, o turno pausa e escala ao PO. |
| **Regra de Silêncio** | Convenção pela qual o Tech Lead não narra na tela o passo a passo do colega durante o turno, só se manifesta em interação inevitável com o PO ou no resumo final. |
| **Cláusula Pétrea** | Regra inegociável do Termo de Abertura: nenhuma alteração em código de produção (`core/`, `scripts/`, `main.py`) sem aprovação explícita do PO. |
| **Autoridade Delegada** | Conjunto de ações que Claude e Gemini podem executar sem aprovação prévia do PO (debater no `war_room.md`, criar/atualizar `docs/gestao/`, ADRs e skills, abrir/comentar issues). |

## 2. Artefatos e Nomenclatura

| Termo | Significado |
| :--- | :--- |
| **Marco (M1, M2, M3, M4)** | Cada marco estratégico do roadmap é identificado pela letra **M** seguida de um número sequencial. M1–M4 não têm significado próprio na sigla; é só a numeração dos marcos do `roadmap.md`. |
| **Risco (R01–R08)** | Cada risco catalogado na `matriz-riscos.md` é identificado pela letra **R** seguida de um número sequencial de 2 dígitos. |
| **Épico (E01–E04)** | Cada épico do `backlog-produto.md` é identificado pela letra **E** seguida de um número sequencial, rastreado 1:1 contra as Issues do GitHub. |
| **ADR** | *Architecture Decision Record* — registro formal de uma decisão de arquitetura (contexto, decisão, consequências), numerado sequencialmente (`0001`–`0005`) em `docs/arquitetura/decisoes/`. |
| **SSOT** | *Single Source of Truth* — fonte única da verdade. No AgLoop, o protocolo completo da Sala de Guerra vive só em `.claude/skills/vigilia/SKILL.md`; `CLAUDE.md`/`GEMINI.md` são resumos que apontam pra ela, evitando duplicar regras. |
| **DRY** | *Don't Repeat Yourself* — princípio de não duplicar a mesma informação/regra em múltiplos lugares (motivação da ADR 0004). |
| **Artefato Mestre** | O `docs/gestao/artefatos/artefato-mestre-agloop.md` — índice vivo que reflete o estado atual do projeto, diferente das ADRs/Termo de Abertura, que são fotografias fixas de uma decisão. |

## 3. Arquitetura Técnica

| Termo | Significado |
| :--- | :--- |
| **war_room.md** | Arquivo Markdown na raiz do repositório que serve como canal de IPC (comunicação entre processos) entre Claude e Gemini — cada turno é um bloco sequencial no arquivo. |
| **IPC** | *Inter-Process Communication* — comunicação entre processos/agentes independentes. No AgLoop, feita via Git + Markdown em vez de infraestrutura de mensageria dedicada. |
| **GitLock** | Classe em `core/git_lock.py` que implementa o lock híbrido: trava local atômica (`.agloop.lock/`) + commit/push escopado ao War Room. |
| **Stale Lock** | Trava órfã: quando um agente trava o `.agloop.lock` e seu processo morre antes de liberá-la. Resolvida checando se o PID ainda existe (mesma máquina) ou expirando por timeout (`AGLOOP_LOCK_TIMEOUT`, default 300s). |
| **lost_race** | Condição em que um agente perde a corrida de `git push` porque o colega empurrou primeiro. Resolvida com reversão cirúrgica (`git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`), nunca com `reset --hard`. |
| **Vigília Híbrida** | Mecanismo de espera passiva em dois níveis: checagem local de `mtime` do `war_room.md` (2s, custo zero) + `git fetch` remoto espaçado (30s, com jitter e backoff). Desperta a sessão via `exit 0` quando o orador muda, sem custo de tokens em ociosidade. |
| **mtime** | *Modification time* — timestamp de última modificação de um arquivo no sistema operacional; usado pela Vigília para detectar mudanças no `war_room.md` sem precisar ler o conteúdo. |
| **Jitter / Backoff exponencial** | Jitter: variação aleatória (±20%) aplicada ao intervalo de checagem remota, pra evitar que múltiplos agentes sincronizem exatamente ao mesmo tempo. Backoff exponencial: ao falhar uma tentativa de rede, o intervalo até a próxima tentativa aumenta progressivamente. |
| **WarRoom / Runner** | Classes propostas em `core/war_room.py` e `core/runner.py`: leitura/escrita estruturada do `war_room.md` e orquestração do loop de vigília e turnos, respectivamente. |
| **HISTORICO.md** | Arquivo de arquivamento onde turnos antigos e já concluídos do `war_room.md` são movidos, mantendo o arquivo principal curto (mitigação do Risco R07). |
| **close_turn_and_archive** | Função proposta que acopla o fechamento de um turno (`<!--FIM_TURNO-->`) ao arquivamento em `HISTORICO.md`, em um único commit atômico. |
| **CONSENSUS / WAITING_HUMAN** | Marcadores de estado (`<!-- AGLOOP_STATE: ... -->`) que o `Runner` reconhecerá para pausar o loop automático quando os agentes chegarem a acordo ou precisarem de decisão humana (Issue #4). |
| **Google ADK** | *Agent Development Kit* do Google — framework que `core/agent.py` passará a usar (via `LlmAgent` + `LiteLlm`) para dar ferramentas nativas de leitura/diagnóstico ao agente, em vez de uma chamada crua ao LiteLLM. |
| **MCP** | *Model Context Protocol* — protocolo padrão para expor ferramentas/dados a um agente de IA. O AgLoop planeja expor um servidor MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`) na Issue #2. |

## 4. Governança e Qualidade

| Termo | Significado |
| :--- | :--- |
| **GIT_AUTHOR_\* / GIT_COMMITTER_\*** | Variáveis de ambiente Git que definem quem assina um commit (nome/e-mail de autor e de committer). Propõe-se injetá-las isoladamente por agente, só no subprocesso Git, sem mutar o ambiente global. |
| **Working Tree** | O conjunto de arquivos no diretório de trabalho de um repositório Git, incluindo os ainda não commitados — é o que o GitLock protege de ser destruído em colisões de push. |
| **pytest 100% verde** | Critério de qualidade: toda a suíte de testes automatizados deve passar antes de qualquer commit na branch `main`. |

---

## Histórico

| Data | Alteração |
| :--- | :--- |
| 2026-11-02 | Criação do glossário, motivada por uma pergunta real não respondida pelo assistente do Mission Control sobre o significado de "M1/M2" — integrado também ao contexto do chat embutido no painel. |
