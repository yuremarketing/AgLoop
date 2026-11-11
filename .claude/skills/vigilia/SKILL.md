---
name: vigilia
description: "Protocolo canônico da Sala de Guerra do AgLoop (Claude ⇄ Gemini/Antigravity ⇄ N agentes): inversão de papéis por turno (Dev Especialista / Tech Lead / Observador), regra de silêncio, autoridade delegada vs. limites do PO (Yure Mark), debate travado em 3 rodadas (Proposta → Réplica → Tréplica), endereçamento explícito via PRÓXIMO-AGENTE, vigília híbrida one-shot e fechamento atômico."
metadata:
  author: yuremarketing
  version: "1.4.0"
---

# Vigília — Protocolo Canônico da Sala de Guerra (AgLoop)

Fonte Única da Verdade (SSOT) de governança operacional entre **Yure Mark (Product Owner)**, **Claude** e **Gemini/Antigravity** no projeto **AgLoop**.
O canal de comunicação entre agentes (IPC) é o arquivo `war_room.md` na raiz do repositório, sincronizado via `GitLock` (`core/git_lock.py`).

> **Primeira coisa a fazer:** se o Gate de Prontidão (Seção 8) ainda não está 🟢, conduza o Onboarding (Seção 7) antes de qualquer outra tarefa.

---

## 1. Papéis na Sala de Guerra (Inversão Turno a Turno)

Não existe papel fixo para nenhuma das LLMs. Em cada turno aberto no `war_room.md`:
- **Dev Especialista (quem abre o turno com `<!--INICIANDO_TURNO-->`):** Analisa a demanda, publica a `PROPOSTA` detalhada, aguarda a revisão, executa a implementação/documentação acordada e submete para auditoria.
- **Tech Lead (a LLM colega daquele turno):** Audita a proposta (máx. 3 rodadas: `PROPOSTA` → `RÉPLICA` → `TRÉPLICA`), revisa o diff real (`git diff`/`git show`), valida a suíte de testes (`pytest`) e aprova (`STATUS: ACORDO`) antes do fechamento (`<!--FIM_TURNO-->`).
- **Observador (Issue #15 — salas com N > 2 participantes):** Qualquer agente além do par ativo do turno. Herda a Regra de Silêncio abaixo e nunca abre `PROPOSTA`/`RÉPLICA`/`TRÉPLICA` nem vota em `STATUS: ACORDO` — só se manifesta se endereçado explicitamente em `PRÓXIMO-AGENTE:` (Seção 4) ou chamado diretamente pelo PO. Se discordar fortemente do rumo de um turno em andamento, levanta a mão para ser o Tech Lead do **próximo** turno — não reabre o turno corrente.

### Roster do Turno
Turnos em salas com 3+ participantes declaram o roster logo após o cabeçalho `<!--INICIANDO_TURNO-->`, deixando explícito quem está ativo e quem está observando:
```
Roster do Turno N: Claude (Dev Especialista) · Gemini (Tech Lead) · GPT, Llama (Observadores)
```
A rotação Dev Especialista/Tech Lead entre turnos segue round-robin simples, como já acontece hoje entre Claude/Gemini.

### Regra de Silêncio do Tech Lead (Economia de Tokens)
Quando seu papel no turno é **Tech Lead**, não narre na tela do usuário o passo a passo intermediário do turno do colega. Só se manifeste na tela por dois motivos:
1. Interação inevitável do PO Yure Mark (ex: aprovação de código de produção, credenciais ou permissão de ferramenta fora do sandbox).
2. Resumo executivo ao concluir ou aprovar o turno.

---

## 2. Autoridade Delegada vs. Limites Invioláveis do PO

### Autoridade Delegada (Executar sem Bloqueio Prévio)
- Escrever turnos de debate (`PROPOSTA`, `RÉPLICA`, `TRÉPLICA`, `ACORDO`) no `war_room.md` com commit e push restritos a `war_room.md`.
- Criar e atualizar artefatos puramente documentais e de governança em `docs/gestao/`, `docs/arquitetura/decisoes/` (ADRs), `CLAUDE.md`, `GEMINI.md` e `.claude/skills/`.
- Abrir/comentar issues e auditar PRs/diffs tecnicamente desde que a suíte `pytest` esteja 100% verde e sem segredos expostos.

### Sempre Exige Aprovação Explícita do Yure Mark (Sem Exceção)
- **Qualquer commit ou alteração em código de produção** (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`) ou infraestrutura/credenciais (`.env`) — e, a partir do Turno 7 (Issue #5 / Épico `E05`), passa obrigatoriamente pelo Gate de PR+CI da Seção 6 (branch de feature + PR real + CI verde + `gh pr review --approve`), nunca mais commit direto na `main`.
- Aprovar mudanças com testes falhando (`pytest` vermelho) ou com risco de regressão.
- Qualquer debate que ultrapasse a 3ª rodada (`TRÉPLICA`) sem convergência técnica — escale imediatamente ao Yure Mark.
- **Banner Visual de Autorização Formal (Issue #45):** Sempre que o orador for `PRÓXIMO-AGENTE: Yure Mark` solicitando aprovação da Cláusula Pétrea, é OBRIGATÓRIO renderizar na resposta ao PO o banner visual de alto impacto (via `core.banner.format_formal_auth_banner()` ou bloco ASCII sólido + callout `> [!CAUTION]`), destacando: (1) o motivo da solicitação, (2) arquivos/contexto afetados e (3) a instrução clara para responder apenas "ok" ou "autorizo".


---

## 3. Vigília Híbrida (Zero Custo de Tokens em Ociosidade)

- **Regra de Ouro:** Nunca utilize cron/schedule de LLM que dispare inferências periódicas em ociosidade.
- **Mecanismo Passivo One-Shot:** O monitor em background (`scripts/vigia.py --agent <Nome> --once`) observa o `mtime` local de `war_room.md` (a cada `2s`, custo zero) e realiza `git fetch` periódico (a cada `30s`).
- **Despertar por Evento:** O processo do monitor só encerra (`exit 0`) quando detecta que o último orador no `war_room.md` mudou para o agente colega, acordando a sessão automaticamente via conclusão da task em background.
- **Religar Sempre (Issue #44):** a vigília `--once` encerra ao acordar o agente. **Todo agente religa a vigília ao final de cada resposta** (`/vigia <Nome>`), salvo quando fecha o turno com `PRÓXIMO-AGENTE:` apontando para o PO. Esquecer de religar faz o loop morrer em silêncio (caso real: Turno 27, ~1 h parado).
- **Alarme de Travamento (Issue #44):** com `--stall-minutes N` (ou `$AGLOOP_STALL_MINUTES`), se a sala ficar N minutos sem atividade, a vigília grava `<!-- AGLOOP_STATE: WAITING_HUMAN -->` com o motivo, devolvendo a decisão ao PO. Desligado por padrão (`0`).
- **Branch da Sala:** a vigília acompanha a branch do clone. Mantenha o clone na branch onde a sala é escrita (`main`).
- **Endereçamento Explícito em Salas com N > 2 (Issue #15):** Quando o turno declara `PRÓXIMO-AGENTE: <Nome>` (Seção 4), só o agente citado desperta — os demais Observadores permanecem na Vigília sem gastar ciclo, mesmo vendo a mudança de orador. Na ausência do campo (turnos antigos ou salas de 2 agentes), o monitor cai no comportamento legado: desperta sempre que o último orador não é ele mesmo.

---

## 4. Formato de Turno e Sincronização Git (`GitLock`)

```markdown
<!--INICIANDO_TURNO-->
Início: AAAA-MM-DD HH:MM · Commit-base: <hash> · Agente: <Claude|Gemini> · <Título curto>

## Turno N — <Agente> (AAAA-MM-DD)
Roster do Turno N: <Dev Especialista> (Dev Especialista) · <Tech Lead> (Tech Lead) · <demais> (Observadores)

## <Agente>

**Proposta — <Agente> (Dev Especialista)**
...
STATUS: PROPOSTA | RÉPLICA | TRÉPLICA | ACORDO | FEITO | PR_ABERTO | CONCLUIDO
PRÓXIMO: <próximo passo claro>
PRÓXIMO-AGENTE: <Nome do agente endereçado>

<!--FIM_TURNO-->
Fim: AAAA-MM-DD HH:MM · Commit: <hash> · Agente: <Agente>
```

`PRÓXIMO-AGENTE:` (Issue #15) é o campo estruturado que a Vigília Híbrida (`core/runner.py`) parseia via `WarRoom.get_next_agent()` para decidir quem desperta — complementa o `PRÓXIMO:` em texto livre, não o substitui. Em salas de 2 agentes (Claude/Gemini) é opcional: na ausência, o despertar cai no comportamento legado (último orador diferente de mim). Em salas com 3+ participantes é obrigatório em todo turno, pra Observadores não acordarem por turnos que não são deles. A linha `Roster do Turno N:` é só documental (não parseada por código).

Quando o turno toca `core/`, `scripts/`, `main.py`, `pyproject.toml` ou `requirements.txt`, o `STATUS: FEITO` não comita direto na `main`: o Dev Especialista abre PR (ver Seção 6) e usa `STATUS: PR_ABERTO` referenciando o número do PR, aguardando `gh pr checks` verde + `STATUS: ACORDO` de fechamento do Tech Lead via `gh pr review --approve`.

### Regras de Segurança do `GitLock` (`core/git_lock.py`)
1. **Commits Escopados:** Apenas os caminhos da Sala de Guerra (`war_room.md`, `HISTORICO.md`) são adicionados/commitados pelo loop automático (`git commit -- <paths>`).
2. **Proibição Absoluta de `reset --hard`:** Em caso de perda de corrida de push (`lost_race`), a reversão é cirúrgica (`git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`), preservando qualquer trabalho não commitado na working tree.
3. **Autoria Isolada por Agente:** Cada commit registra `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` e `GIT_COMMITTER_NAME`/`GIT_COMMITTER_EMAIL` escopados ao subprocesso do agente ativo, sem vazar variáveis para o ambiente global.
4. **Fechamento e Arquivamento Atômico:** Ao fechar um turno (`<!--FIM_TURNO-->` / `CONSENSUS`), o arquivamento de turnos antigos em `HISTORICO.md` ocorre no mesmo commit/push atômico.
5. **Jitter de Backoff Ampliado (Issue #15):** Em `push()`, o backoff entre tentativas após rejeição usa `random.uniform(0.5, 2.0) * attempt` — faixa ampliada em relação à v1 (`0.2–1.0`) para diluir colisões à medida que o número de agentes escritores concorrentes cresce além de 2.

---

## 5. Painel de Gestão — Responsabilidade Portável entre Agentes (Issue #6)

O AgLoop se propõe heterogêneo (Claude ⇄ Gemini/Antigravity ⇄ outros via `LiteLlm`), então a governança visual não pode depender de uma única plataforma. O contrato é **"precisa ter um agente capaz de publicar e manter um painel ao vivo equivalente"**, não "precisa ser Claude".

1. **Fonte Única Versionada (`docs/gestao/painel-agloop.html`):** arquivo HTML autocontido (zero dependências externas além de Google Fonts, tema claro/escuro nativo). **Qualquer agente** (Claude, Gemini/Antigravity ou outro) atualiza esse arquivo ao fechar um turno relevante — isso nunca fica obsoleto, independe de quem está com sessão ativa.
2. **Publicação Ao Vivo — Claude-Exclusivo, *Best Effort*:** publicar/atualizar um Claude Artifact é ferramenta exclusiva da plataforma Claude — Gemini/Antigravity e outros LLMs não têm acesso a ela, de forma alguma. Quando uma sessão Claude estiver ativa no fechamento de um turno, republique `docs/gestao/painel-agloop.html` como Artifact, preservando a URL entre atualizações. Sem sessão Claude ativa, isso simplesmente não acontece — e está tudo bem, veja a regra 3.
3. **Regra de Fallback Explícita (Transparência Obrigatória):** todo fechamento de turno relevante declara o estado do painel na própria mensagem, nunca falhando silenciosamente:
   - `PAINEL: atualizado em docs/gestao/painel-agloop.html + publicado ao vivo` (sessão Claude ativa); ou
   - `PAINEL: atualizado localmente em docs/gestao/painel-agloop.html, sem publicação ao vivo nesta sessão` (nenhum agente da sessão tem ferramenta de publicação equivalente).
   Se outro LLM/agente quiser ocupar o papel de publicador sem ter Claude disponível, a obrigação é ativa: oferecer um mecanismo de publicação ao vivo similar, igual ou melhor — não deixar o painel cair pro fallback como comportamento padrão aceitável.

---

## 6. Gate de PR+CI antes do Merge na `main` (Issue #5 / Épico `E05`)

Port do padrão Sysoft: nenhuma mudança em `core/`, `scripts/`, `main.py`, `pyproject.toml` ou `requirements.txt` chega mais na `main` por commit direto — passa por branch de feature, PR real no GitHub e CI verde antes da aprovação do Tech Lead.

1. **Branch por Issue:** o Dev Especialista cria `feat/issue-N-<slug>` (ou `fix/issue-N-<slug>`) a partir da `main` antes de implementar. Todos os commits do turno para aquela issue entram nessa mesma branch — sem fragmentar em múltiplas PRs.
2. **CI (`.github/workflows/ci.yml`):** GitHub Actions roda `pytest` em matriz `python-version: ["3.10", "3.11", "3.12"]` a cada push na branch/PR contra `main`, com permissões `contents: read`, `pull-requests: write`, `statuses: write`.
3. **Abertura do PR:** ao concluir a implementação (equivalente ao antigo `STATUS: FEITO`), o Dev Especialista abre o PR (`gh pr create`) referenciando a Issue e o turno, e registra `STATUS: PR_ABERTO` no `war_room.md` com o número do PR.
4. **Aprovação do Tech Lead:** só depois de `gh pr checks` 100% verde, o Tech Lead revisa o diff real (`gh pr diff`) e aprova via `gh pr review --approve` — essa aprovação no GitHub substitui/complementa o `STATUS: ACORDO` textual, que passa a citar o número do PR e o resultado do `gh pr checks`.
5. **Merge:** só após `--approve` + CI verde, `gh pr merge --squash --delete-branch --auto`, preservando o changelog linear da `main`.
6. **`war_room.md`/`HISTORICO.md` seguem fora do gate:** continuam indo direto na `main` via `GitLock` (camada de governança/debate, não código de produção).

---

## 7. Onboarding (primeira sessão após o `agloop init` num projeto novo)

Gatilho: o humano diz algo como *"instalei o AgLoop"*, ou você encontra o Gate de Prontidão (Seção 8) com itens pendentes (arquivos com `<!-- AGLOOP_TODO: ... -->`). Conduza nesta ordem, **em conversa com o PO (Yure Mark)**:

1. **Briefing do repositório.** Leia a estrutura, os manifestos de stack, os testes, o CI e o remoto Git. Responda em poucas linhas: o que você viu e o que falta para o projeto atender o framework.
2. **Apresentação.** Explique o AgLoop em até 5 linhas: Sala de Guerra (`war_room.md`), turnos com papéis, limite de 3 rodadas, PO com a palavra final sobre código de produção.
3. **Plano e permissão.** Liste o que precisa ser feito agora (os itens pendentes do Gate) e pergunte: *"Posso começar?"*. Só siga com o "sim" do PO.
4. **Roster e capacidades.** Pergunte quais agentes vão participar e com quais nomes distintos (ex.: `Claude`, `Claude-Cloud`, `Gemini`). Registre em `docs/gestao/roster-agentes.md` o que cada um consegue produzir e com qual ferramenta (ex.: páginas e wireframes, pesquisa aprofundada, protótipo visual, painel). Cada agente atualiza a própria linha ao entrar na sala.
5. **Preenchimento da governança.** Item a item, pergunte, proponha um rascunho e escreva o arquivo depois da confirmação do PO. Remova o marcador `AGLOOP_TODO` só quando o item estiver de fato preenchido.
6. **Ferramentas de apoio.** Para cada artefato, atribua o trabalho ao agente que tem a ferramenta (consultando o roster). Se ninguém na sala tiver, sugira uma ferramenta externa com **instrução explícita**: qual ferramenta, quais fontes subir, qual artefato gerar (relatório, pesquisa com fontes, mapa mental, resumo em áudio, FAQ etc.), o **prompt pronto para colar** e o **caminho de destino** no repositório (ex.: `docs/gestao/estudo-mercado.md`). O artefato volta e passa pela Sala de Guerra como qualquer documento.
7. **Fechamento.** Faça commit da governança, confira o Gate e diga: *"Gate de Prontidão 🟢. Sala ativa. Qual é a primeira demanda?"*

---

## 8. Gate de Prontidão

**Nenhuma linha de código de produção antes do Gate 🟢.** Não abra turno de código, não implemente e **nunca ofereça pular o protocolo** ("codar direto", "sem o ritual" e equivalentes). Pular o Gate só por ordem explícita do PO (Yure Mark), registrada no `war_room.md` com o motivo.

🔒 = obrigatório para codar · 📌 = recomendado

**Ambiente**
- 🔒 Git instalado; 🔒 Python 3.10+ e o pacote `agloop`; 🔒 remoto `origin` configurado
- 📌 Chave de API das LLMs configurada (só o nome da variável no `.env`, nunca o valor)

**Acesso e autonomia**
- 🔒 Push no repositório; 🔒 permissão para criar issues e PRs
- 📌 Permissão para gerenciar o Kanban (ex.: GitHub Projects); 📌 proteção da branch principal

**Produto**
- 🔒 Visão / termo de abertura (problema, público, como medir sucesso); 🔒 PO definido
- 🔒 Backlog com pelo menos 1 user story (*"Como X, quero Y, para Z"*) e 🔒 critérios de aceite em cada story
- 📌 Personas; 📌 wireframes (se houver interface); 📌 roadmap com marcos

**Técnica**
- 🔒 Pastas de código de produção definidas; 🔒 comando para rodar os testes
- 📌 CI; 📌 ADRs das decisões já tomadas (stack, banco, deploy); 📌 convenção de branch e commit; 📌 Definição de Pronto (DoD)

**Riscos e segurança**
- 🔒 `.env` no `.gitignore` e nenhum segredo commitado; 🔒 matriz de riscos revisada
- 📌 Mapa de dados pessoais (LGPD/GDPR), se o projeto lida com dados de pessoas; 📌 licença

**Operação da sala**
- 🔒 Agentes com nomes distintos, registrados no roster
- 🔒 `AGENTS.md` (e `CLAUDE.md`/`GEMINI.md`, se usados) apontando para este arquivo
- 📌 Painel de acompanhamento

Se algum 🔒 estiver pendente quando o PO pedir código, responda que o Gate ainda está 🔴, liste o que falta e ofereça resolver agora, nunca contornar.
