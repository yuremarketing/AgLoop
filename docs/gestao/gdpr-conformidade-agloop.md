# Relatório de Mapeamento de Conformidade GDPR (Regulamento (UE) 2016/679) no Projeto AgLoop

## 1. Visão Geral e Contexto Internacional

O **AgLoop** é um framework heterogêneo de orquestração multi-agente (*serverless* e *zero-infra*) para inteligências artificiais autônomas (Claude Code, Gemini CLI, OpenAI, etc.), estruturado sobre o padrão *Blackboard* no arquivo `war_room.md` e sincronizado via Git (`GitLock`).

Enquanto o relatório [`docs/gestao/lgpd-conformidade-agloop.md`](lgpd-conformidade-agloop.md) mapeia a aderência à legislação brasileira (Lei nº 13.709/2018), este documento estabelece a conformidade formal com o **General Data Protection Regulation (GDPR — Regulamento (UE) 2016/679)** do Parlamento Europeu e do Conselho. Este mapeamento é indispensável para desenvolvedores e organizações situados no Espaço Econômico Europeu (EEE) ou que processem dados no contexto de atividades de estabelecimentos na UE (Art. 3º do GDPR).

A arquitetura local e descentralizada do AgLoop garante que não haja bancos de dados centralizados, armazenamento em nuvem proprietária ou servidores intermediários sob posse do orquestrador. Contudo, a interação com Modelos de Linguagem (LLMs) operados por terceiros e o versionamento em Git demandam formalização jurídica e técnica detalhada.

| Componente Arquitetural | Fluxo de Dados | Relevância sob o GDPR | Mecanismo de Controle do AgLoop |
| :--- | :--- | :--- | :--- |
| **Sala de Guerra (`war_room.md`)** | Markdown Local e Git | Exposição inadvertida de dados pessoais em histórico | Fechamento atômico, higienização e arquivamento em `HISTORICO.md` |
| **Metadados Git (`author`/`committer`)** | Log de commits (Local / Remoto) | Tratamento de dados identificáveis de desenvolvedores | Injeção isolada de `GIT_AUTHOR_*` e `GIT_COMMITTER_*` por subprocesso (`core/git_lock.py`) |
| **Ferramentas MCP (`core/mcp_server.py`)** | Leitura/Escrita local no projeto | Acesso indevido a dados pessoais do sistema hospedeiro | Sandboxing estrito de workspace via `_resolve_allowed_file` e blacklist de `.env` |
| **Payloads de Prompts para LLMs** | Chamadas de API externas (HTTPS) | Transferência internacional de dados pessoais (Art. 44–49) | Higienização em memória via `sanitize_prompt_pii()` (`core/agent.py`) antes do envio |

---

## 2. Bases Legais para o Tratamento de Dados (Artigo 6º do GDPR)

O GDPR exige que toda operação de tratamento (*processing*) de dados pessoais esteja fundamentada em pelo menos uma das bases legais do Artigo 6(1). No AgLoop, as operações mapeadas enquadram-se nas seguintes bases:

1. **Execução de Contrato ou Medidas Pré-contratuais (Art. 6(1)(b)):**
   - **Metadados de Commit:** O registro de nome e e-mail nos commits Git é intrínseco à atribuição de autoria e colaboração contratual no desenvolvimento de software.
2. **Interesse Legítimo do Controlador (Art. 6(1)(f)):**
   - **Rastreabilidade e Segurança de Código:** A manutenção do histórico na Sala de Guerra (`war_room.md` e `HISTORICO.md`) atende ao interesse legítimo da organização em auditoria técnica, controle de qualidade, prevenção de fraudes e integridade do código-fonte.
   - **Mitigação Técnica Obrigatória:** O teste de balanceamento (*balancing test*) é satisfeito pelo isolamento das variáveis de autoria (`_author_env` no `GitLock`) e pela sanitização ativa de dados confidenciais e PII de terceiros antes de qualquer transmissão externa.
3. **Consentimento e Políticas Organizacionais (Art. 6(1)(a)):**
   - **Uso de Chaves de API e Provedores de LLM:** O envio de contexto técnico para provedores de IA (Anthropic, Google, OpenAI) decorre da configuração deliberada e consentida pelo desenvolvedor/organização ao fornecer credenciais em variáveis de ambiente locais.

---

## 3. Transferência Internacional de Dados (Artigos 44 a 49 do GDPR)

A utilização de provedores globais de IA sediados fora do Espaço Econômico Europeu (principalmente nos Estados Unidos) caracteriza transferência internacional de dados pessoais caso o código ou os metadados contenham PII.

### Mecanismos de Conformidade e Salvaguardas:
- **Mitigação Primária por *Data Minimisation* (Art. 5(1)(c) e Art. 25):** O AgLoop aplica `core.agent.sanitize_prompt_pii()` diretamente no payload em memória antes da chamada ao `litellm.completion()`. CPFs, chaves de API e endereços de e-mail (exceto os do domínio mock `@agloop.local`) são substituídos por marcadores sintéticos (`[EMAIL_REDACTED]`, `[CPF_REDACTED]`). Dessa forma, minimiza-se na origem a transmissão de dados identificáveis para fora do EEE.
- **Instrumentos Jurídicos de Transferência (Art. 46):** Para os dados residuais de autoria ou desenvolvimento, as organizações utilizadoras contam com as **Cláusulas Contratuais Padrão (Standard Contractual Clauses — SCCs)** incorporadas nos Termos de Processamento de Dados (DPAs) dos respectivos provedores (OpenAI DPA, Anthropic Commercial Terms e Google Cloud Data Processing Addendum).
- **Risco R10 na Matriz de Riscos:** Classificado como **Mitigado** em [`docs/gestao/matriz-riscos.md`](matriz-riscos.md), dado que a sanitização em código elimina a transmissão de dados sensíveis na camada de transporte.

---

## 4. Direitos dos Titulares e Imutabilidade do Git (Artigos 15 a 22 do GDPR)

O exercício dos direitos do titular no contexto de sistemas versionados por Git apresenta particularidades decorrentes da criptografia e integridade da árvore de commits (DAG imutável).

### 4.1 Direito ao Acesso e Portabilidade (Art. 15 e 20)
Como o AgLoop opera 100% no repositório local e no repositório Git remoto do usuário:
- O titular tem acesso direto, imediato e irrestrito a todos os seus dados executando `git log` ou inspecionando `war_room.md` e `HISTORICO.md`.
- Os formatos utilizados (Markdown, JSON e Git) são abertos, interoperáveis e estruturados em conformidade com o Art. 20.

### 4.2 Direito ao Apagamento / "Direito ao Esquecimento" (Art. 17)
Em repositórios Git, a exclusão de um registro em um commit subsequente não elimina o dado do histórico anterior. Para atender ao Art. 17 em caso de inserção acidental de dados pessoais no repositório:
- **Procedimento Operacional Padrão (SOP):** A organização controladora deve realizar a reescrita cirúrgica do histórico utilizando ferramentas consolidadas como `git-filter-repo` ou `BFG Repo-Cleaner`, seguida de `force push` protegido e rotação de credenciais caso chaves tenham sido expostas.
- **Isolamento do AgLoop:** O orquestrador AgLoop **não armazena nem replica** cópias de histórico fora do workspace do repositório Git. Uma vez higienizado o repositório Git, nenhuma persistência residual permanece em infraestrutura do AgLoop.

---

## 5. Notificação de Violação de Dados Pessoais em até 72 Horas (Artigos 33 e 34 do GDPR)

Embora o AgLoop seja um componente de software cliente e não um prestador SaaS de armazenamento, estabelece-se a seguinte diretriz de governança para organizações usuárias em caso de incidente de segurança:

1. **Detecção e Confinamento:** Se dados pessoais forem inadvertidamente commitados em `war_room.md` ou enviados a um endpoint de LLM, o desenvolvedor ou agente deve pausar a sessão imediatamente (estado `WAITING_HUMAN` no War Room).
2. **Avaliação de Risco:** Avaliar o volume e a sensibilidade dos dados expostos. Caso envolva credenciais de bancos de produção com dados de titulares europeus, notificar o Encarregado de Proteção de Dados (DPO) da organização.
3. **Comunicação à Autoridade de Controle:** Se for provável que a violação resulte em risco aos direitos e liberdades dos titulares, a organização controladora deve notificar a Autoridade de Proteção de Dados (DPA) competente no prazo máximo de 72 horas após ter tomado conhecimento (Art. 33).

---

## 6. Privacidade por Concepção e por Padrão (*Privacy by Design & Default* — Artigo 25)

Os controles arquiteturais do AgLoop atendem nativamente às diretrizes de Privacy by Design:

1. **Minimização de Coleta (*Zero-Infra*):** Nenhum dado de telemetria, prompt ou metadado é transmitido aos mantenedores do projeto AgLoop. Toda comunicação de rede ocorre estritamente entre o terminal do usuário e os provedores de modelo contratados pelo usuário.
2. **Confinamento de Ferramentas (*Tool Sandboxing*):** O servidor MCP do AgLoop restringe leituras e escritas estritamente ao diretório do repositório ativo (`LGPD-03`), rejeitando qualquer caminho que suba além do workspace ou aponte para arquivos de credenciais (`.env`, `.pem`, `id_rsa`).
3. **Sanitização Pré-Voo (*Prompt Sanitization*):** O módulo `sanitize_prompt_pii` remove dados sensíveis antes de qualquer requisição de rede, funcionando como salvaguarda automatizada e ativa por padrão.
4. **Auditoria de Conformidade CLI (`core/privacy_audit.py`):** O comando `agloop audit --privacy` (`LGPD-04`) fornece diagnóstico local imediato sobre a presença de credenciais expostas ou descumprimento de políticas de privacidade no repositório.

---

## 7. Quadro Resumo de Correspondência Normativa (GDPR x LGPD x AgLoop)

| Princípio / Exigência | Artigo GDPR | Artigo LGPD | Implementação Técnica no AgLoop | Status |
| :--- | :---: | :---: | :--- | :---: |
| **Minimização de Dados** | Art. 5(1)(c) | Art. 6º, III | Janela deslizante (`read_recent`) e Vigília Híbrida local via `mtime` | ✅ Ativo |
| **Segurança e Sigilo** | Art. 5(1)(f) | Art. 6º, VII | GitLock com atomicidade, `_resolve_lost_race` sem `reset --hard` | ✅ Ativo |
| **Privacidade por Design** | Art. 25 | Art. 46 | Confinamento de workspace MCP e blacklist de `.env` | ✅ Ativo |
| **Sanitização de PII** | Art. 32 | Art. 46 | `core/agent.py::sanitize_prompt_pii()` para CPFs, e-mails e chaves | ✅ Ativo |
| **Transferência Internacional** | Art. 44–49 | Art. 33–36 | Mascaramento prévio em memória + SCCs contratuais dos provedores | ✅ Mitigado |
| **Auditoria e Rastreabilidade** | Art. 5(2) | Art. 6º, X | Rastreamento em `war_room.md`, `HISTORICO.md` e `agloop audit --privacy` | ✅ Ativo |
