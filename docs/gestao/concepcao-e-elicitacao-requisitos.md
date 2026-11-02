# Concepção e Elicitação de Requisitos — AgLoop

Este documento registra **de onde vieram** os requisitos do AgLoop e **como** foram levantados — de forma honesta sobre o processo real, sem simular uma elicitação formal (entrevistas, workshops, pesquisa de usuário) que não ocorreu. Complementa o [`termo-abertura.md`](termo-abertura.md) (que registra o *business case* e o escopo) com o *como* e o *de onde* por trás desse escopo.

---

## 1. Natureza real do processo

O AgLoop **não teve** um processo clássico de elicitação de requisitos (entrevista com usuários, questionário, workshop de levantamento, pesquisa de mercado). Isso acontece porque:

- O projeto tem **um único stakeholder de negócio**: o Product Owner, Yure Mark, que é simultaneamente o especialista de domínio, o usuário primário e quem aprova o escopo.
- Não existe uma base de usuários externa a ser entrevistada — os "usuários" do sistema são os próprios agentes de IA (Claude e Gemini) operando sob supervisão do PO.

Os requisitos nasceram de **duas fontes reais**, descritas abaixo, e continuam sendo refinados por um **terceiro mecanismo contínuo**: o debate estruturado no `war_room.md`.

---

## 2. Fonte primária — Derivação de incidentes reais do Sysoft

O AgLoop é um spin-off generalizado do harness da Sala de Guerra do projeto **Sysoft**. A maior parte dos requisitos técnicos não foi "imaginada" — foi **extraída de post-mortems de falhas reais** observadas em produção naquele projeto-mãe, principalmente no **Turno 72 / PR #39**. Essa é, na prática, a técnica de elicitação dominante aqui: **análise de causa raiz de incidentes anteriores**, não entrevista prospectiva.

Exemplos diretos de requisito nascido de incidente (rastreados na [Matriz de Riscos](matriz-riscos.md)):

| Incidente observado no Sysoft | Requisito derivado | Risco associado |
| :--- | :--- | :--- |
| `git reset --hard` destruiu trabalho não commitado de outro agente durante colisão de push | Reversão cirúrgica obrigatória em `lost_race`, proibição de `reset --hard` | R02 |
| Regras operacionais triplicadas em 3 arquivos, gerando divergência e inflação de prompt | Fonte única da verdade (SSOT) centralizada em `SKILL.md` | R05 |
| `war_room.md` crescendo sem limite, estourando contexto | Fechamento e arquivamento atômico em `HISTORICO.md` | R07 |
| Debates sem critério de parada drenando tokens/API | Limite rígido de 3 rodadas (Proposta → Réplica → Tréplica) | R01 |

## 3. Fonte secundária — Decisão direta do Product Owner

Onde não havia um incidente concreto do Sysoft para derivar, o requisito foi definido **diretamente pelo PO**, com base em sua experiência de engenharia, sem validação externa adicional. Exemplos:

- A escolha de Git + Markdown como broker serverless (em vez de Redis/RabbitMQ) — decisão de arquitetura do PO, registrada na [ADR 0001](../arquitetura/decisoes/0001-ipc-markdown-e-git-serverless-broker.md).
- A adoção futura do Google ADK e do protocolo MCP (Issues #2 e #4) — direção estratégica definida pelo PO, ainda em fase de RFC ([ADR 0005](../arquitetura/decisoes/0005-motor-cognitivo-google-adk-e-plugin-mcp.md)).
- A Cláusula Pétrea de proteção de código de produção — requisito de governança imposto pelo PO, não derivado de incidente técnico específico.

## 4. Mecanismo contínuo — O `war_room.md` como elicitação viva

Diferente de um levantamento de requisitos feito uma vez no início, o AgLoop **continua elicitando e refinando requisitos durante a execução**, através do próprio protocolo de turnos: quando Claude e Gemini debatem uma Proposta em até 3 rodadas, esse debate frequentemente expõe requisitos implícitos, ambiguidades ou riscos que nenhum dos dois tinha formalizado antes de abrir o turno (ver, por exemplo, os 3 pontos técnicos alinhados entre Claude e Gemini no Turno 1 antes da Issue #3 avançar para código). Esse mecanismo é parte deliberada do desenho do processo, não um substituto formal de pesquisa de usuário.

---

## 5. Requisitos Funcionais (RF)

| ID | Requisito | Épico | Status |
| :--- | :--- | :---: | :---: |
| RF01 | Permitir que dois agentes troquem mensagens estruturadas via arquivo Markdown versionado em Git. | E01 | ✅ |
| RF02 | Registrar turnos sequenciais com papéis invertidos (Dev Especialista / Tech Lead). | E01 | ✅ |
| RF03 | Impedir que um agente destrua trabalho não commitado de outro processo em colisão de push. | E01 | ✅ |
| RF04 | Recuperar automaticamente uma trava (lock) órfã deixada por processo morto. | E01 | ✅ |
| RF05 | Despertar automaticamente a sessão do agente quando for sua vez de falar, sem polling ativo de LLM. | E01 | ✅ |
| RF06 | Arquivar turnos antigos do `war_room.md` para controlar seu tamanho. | E02 | 📋 Planejado |
| RF07 | Registrar autoria Git isolada por agente em cada commit da Sala de Guerra. | E02 | 📋 Planejado |
| RF08 | Equipar o agente com ferramentas seguras de leitura/diagnóstico (Google ADK) antes de opinar. | E03 | 📋 Planejado |
| RF09 | Reconhecer marcadores de consenso/pausa humana para parar o loop automaticamente. | E03 | 📋 Planejado |
| RF10 | Distribuir o AgLoop como plugin instalável (Claude Code / Antigravity) com Slash Commands. | E04 | 📋 Planejado |
| RF11 | Expor operações da Sala de Guerra via servidor MCP. | E04 | 📋 Planejado |

## 6. Requisitos Não-Funcionais (RNF)

| ID | Requisito | Categoria | Métrica / Critério |
| :--- | :--- | :--- | :--- |
| RNF01 | Latência de detecção de novo turno | Performance | ≤ 2.0s local, ≤ 30.0s remoto |
| RNF02 | Custo de tokens em ociosidade | Custo | 0 tokens |
| RNF03 | Integridade da working tree em colisão de push | Confiabilidade | 0% de perda de arquivos de terceiros |
| RNF04 | Cobertura de testes antes de commit em `main` | Qualidade | 100% da suíte `pytest` verde |
| RNF05 | Centralização do protocolo operacional | Manutenibilidade | Fonte única em `SKILL.md` (sem duplicação) |
| RNF06 | Restrição de escrita em produção | Segurança | Nenhum commit em `core/`/`scripts/` sem aprovação explícita do PO |
| RNF07 | Independência de infraestrutura externa | Portabilidade | Funciona em qualquer repositório Git com remoto configurado |

---

## 7. Limitações conhecidas deste levantamento

- **Stakeholder único:** todo requisito passa pelo crivo de uma só pessoa (o PO). Não há verificação cruzada com outros usuários ou times.
- **Sem pesquisa de usuário:** nenhuma técnica como entrevista, survey, shadowing ou teste de usabilidade foi aplicada — nem está planejada no momento.
- **Viés de origem:** por herdar a maior parte dos requisitos do Sysoft, o AgLoop pode estar resolvendo problemas específicos daquele contexto que não se generalizam para todo uso multi-agente.
- **Requisitos futuros (E03/E04) ainda não passaram por incidente real:** diferente dos requisitos de E01/E02 (derivados de falhas observadas), os requisitos ligados ao Google ADK e ao Plugin/MCP são prospectivos — definidos por decisão do PO antes de qualquer uso real, com risco maior de retrabalho.

---

## 8. Histórico

| Data | Alteração |
| :--- | :--- |
| 2026-11-02 | Criação do documento, a pedido explícito do PO, registrando a origem real dos requisitos (derivação de incidentes do Sysoft + decisão direta do PO) em vez de uma elicitação formal inexistente. |
