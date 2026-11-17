---
name: vigilia
description: "Protocolo da Sala de Guerra (AgLoop) deste projeto: papéis por turno (Dev Especialista / Tech Lead / Observador), regra de silêncio, autoridade delegada vs. limites do PO, debate travado em 3 rodadas (Proposta → Réplica → Tréplica), endereçamento explícito via PRÓXIMO-AGENTE, vigília híbrida one-shot e fechamento atômico."
metadata:
  source: "agloop init"
  version: "1.7.0"
---

# Vigília — Protocolo da Sala de Guerra

Fonte Única da Verdade (SSOT) de governança entre o **PO do projeto** (o humano responsável pelas decisões) e os agentes de IA que participam da Sala de Guerra (por exemplo, Claude e Gemini).
O canal de comunicação entre agentes é o arquivo `war_room.md` na raiz do repositório, sincronizado via Git.

> **Primeira coisa a fazer:** se o Gate de Prontidão (Seção 7) ainda não está 🟢, conduza o Onboarding (Seção 6) antes de qualquer outra tarefa.

> Ajuste este arquivo à realidade do seu projeto: o nome do PO, quais pastas contam como código de produção e se há CI. O restante do protocolo funciona como está.

---

## 1. Papéis na Sala de Guerra (trocam a cada turno)

Nenhum agente tem papel fixo. Em cada turno aberto no `war_room.md`:
- **Dev Especialista** (quem abre o turno com `<!--INICIANDO_TURNO-->`): analisa a demanda, publica a `PROPOSTA`, aguarda a revisão, executa o que foi acordado e submete para auditoria.
- **Tech Lead** (o colega daquele turno): audita a proposta (máximo de 3 rodadas: `PROPOSTA` → `RÉPLICA` → `TRÉPLICA`), revisa o diff real (`git diff`) e os testes e aprova com `STATUS: ACORDO` antes do fechamento (`<!--FIM_TURNO-->`).
- **Observador** (salas com 3 ou mais agentes): qualquer agente fora do par ativo. Fica em silêncio, não abre `PROPOSTA`/`RÉPLICA`/`TRÉPLICA` nem vota em `ACORDO`. Só fala se for endereçado em `PRÓXIMO-AGENTE:` ou chamado pelo PO.

A rotação entre Dev Especialista e Tech Lead segue round-robin simples entre os agentes.

### Regra de Silêncio (economia de tokens)
Quem não está com a vez não narra o trabalho do colega na tela do usuário. Só se manifeste para:
1. uma interação inevitável com o PO (aprovação de código de produção, credenciais, permissão de ferramenta);
2. um resumo executivo ao concluir ou aprovar o turno.

---

## 2. Autoridade Delegada vs. Limites do PO

### Autoridade delegada (executar sem pedir antes)
- Escrever turnos de debate no `war_room.md`, com commit e push restritos a `war_room.md` e `HISTORICO.md`.
- Criar e atualizar documentação e governança (`docs/`, ADRs em `docs/arquitetura/decisoes/`, `.claude/skills/`).
- Abrir e comentar issues e auditar diffs, desde que os testes estejam verdes e não haja segredos expostos.

### Sempre exige aprovação explícita do PO
- **Qualquer alteração em código de produção**, ou seja, tudo que o projeto executa ou publica (código-fonte, dependências, configuração de build e deploy), e qualquer arquivo de credenciais (`.env`).
- Aprovar mudanças com testes falhando ou com risco de regressão.
- Debates que passem da 3ª rodada (`TRÉPLICA`) sem convergência: escale ao PO.
- **Banner Visual e Alerta Sonoro de Autorização Formal:** sempre que o orador for `PRÓXIMO-AGENTE: <PO>` solicitando aprovação da Cláusula Pétrea, renderize o banner visual de alto impacto (bloco ASCII sólido + callout `> [!CAUTION]`) com motivo, contexto e instrução clara para responder "ok" ou "autorizo", e dispare o alerta sonoro de alta visibilidade via `agloop-alert` (ou `core.banner.play_formal_auth_alert()`).

---

## 3. Vigília Híbrida e Host Daemon (ADR-0008)

- **Regra de Ouro:** Nunca utilize cron/schedule de LLM que dispare inferências periódicas em ociosidade.
- **Host Daemon Recomendado:** Para eliminar a fragilidade do modelo efêmero como watchdog da sua própria infraestrutura, o AgLoop fornece o `agloop daemon start` (`core/daemon.py`). Ele executa como supervisor contínuo no host, se rearmando automaticamente a cada turno e disparando alarme sonoro determinístico (`agloop-alert`) caso a sala fique estagnada por mais de 15 minutos (`--stall-minutes`).
- **Mecanismo Passivo One-Shot (Fallback para Sessões Interativas):** O monitor em background (`agloop-vigia --agent <Nome> --once` ou `scripts/vigia.py --agent <Nome> --once`) observa o `mtime` local de `war_room.md` (a cada `2s`, custo zero) e realiza `git fetch` periódico (a cada `30s`).
- **Despertar por Evento:** O processo do monitor só encerra (`exit 0`) quando detecta que o último orador no `war_room.md` mudou para o agente colega, acordando a sessão automaticamente via conclusão da task em background.
- **Religar Sempre Obrigatório (Custo Zero de Tokens):** O monitor passivo em background é um processo do sistema operacional que dorme em `time.sleep(2)` verificando `mtime` local e `git fetch` a cada 30s. Não faz inferência e **gasta ZERO tokens**. Portanto, **NÃO EXISTE VIGÍLIA DESLIGADA**. Mesmo quando o Host Daemon estiver rodando no host, a sessão interativa de chat precisa do seu próprio monitor passivo para ser despertada pelo harness. **Todo agente obrigatoriamente rearma a vigília em background (`--once`) ao final de TODA e QUALQUER resposta**, inclusive quando o turno fecha com `PRÓXIMO-AGENTE:` apontando para o PO, para o Tech Lead ou após merge. As **únicas exceções estritas** são: (a) comando explícito do usuário/PO para desligar a vigília nesta sessão, ou (b) o fim genuíno da sessão/conversa. Qualquer outro motivo (ex.: "achei que não ia disparar", "é a vez do PO", "o colega acabou de mergear") **não é exceção válida** — religue a vigília em vez de deixá-la parada.
- **Checklist Obrigatório de Fim-de-Resposta (Toda Resposta, Salvo as Duas Exceções Estritas):** antes de encerrar qualquer resposta nesta sala, confirme explicitamente que a vigília está rodando em background (`agloop-vigia --agent <Nome> --once`). Nunca encerre um turno ou resposta sem armar esse processo, a menos que o usuário tenha explicitamente ordenado o desligamento ou a conversa tenha chegado ao seu encerramento final definitivo.
- **Alarme de Travamento:** com `--stall-minutes N` (ou `$AGLOOP_STALL_MINUTES`), se a sala ficar N minutos sem atividade, a vigília grava `<!-- AGLOOP_STATE: WAITING_HUMAN -->` com o motivo, devolvendo a decisão ao PO. O Host Daemon mantém esse alarme sempre ativo por padrão (15 min).
- **Backstop Técnico (Heartbeat):** a vigília grava um heartbeat (`.agloop/vigia.heartbeat.json`: agente, pid, estado `running`/`stopped`, motivo, timestamp) a cada ciclo de poll local e, de forma garantida (`try/finally` + handler de `SIGTERM`), no momento de encerrar. `agloop check` lê esse heartbeat e flagra o processo morto sem rodar encerramento.
- **Branch da Sala:** a vigília acompanha a branch do clone. Mantenha o clone na branch onde a sala é escrita (`main`).
- **Endereçamento Explícito em Salas com N > 2:** Quando o turno declara `PRÓXIMO-AGENTE: <Nome>`, só o agente citado desperta. Sem o campo, desperta todo agente que não foi o último a falar.

---

## 4. Formato de Turno

```markdown
<!--INICIANDO_TURNO-->
Início: AAAA-MM-DD HH:MM · Commit-base: <hash> · Agente: <Nome> · <Título curto>
Roster do Turno N: <Dev> (Dev Especialista) · <TL> (Tech Lead) · <demais> (Observadores)

## Turno N — <Agente> (AAAA-MM-DD)

## <Agente>

**Proposta — <Agente> (Dev Especialista)**
...
STATUS: PROPOSTA | RÉPLICA | TRÉPLICA | ACORDO | FEITO | PR_ABERTO | CONCLUIDO
PRÓXIMO: <próximo passo em texto livre>
PRÓXIMO-AGENTE: <Nome de quem deve agir>

<!--FIM_TURNO-->
Fim: AAAA-MM-DD HH:MM · Commit: <hash> · Agente: <Agente>
```

- `PRÓXIMO-AGENTE:` é lido pelo código e decide quem acorda. É opcional com 2 agentes e **obrigatório com 3 ou mais**. Sessões do mesmo modelo precisam de nomes distintos (ex.: `Claude` e `Claude-Cloud`).
- A linha `Roster` é só documental e obrigatória com 3 ou mais agentes.
- `<!-- AGLOOP_STATE: WAITING_HUMAN -->` pausa a sala até o PO decidir; `<!-- AGLOOP_STATE: CONSENSUS -->` encerra o debate.

### Segurança do Git
1. **Commits escopados:** a sala só commita `war_room.md` e `HISTORICO.md`.
2. **Nunca `reset --hard`:** se outro agente escrever primeiro (`lost_race`), só a alteração da sala é desfeita, preservando o resto da working tree. Releia e responda de novo.
3. **Autoria por agente:** cada commit leva o nome do agente que escreveu.
4. **Fechamento atômico:** ao fechar um turno, os turnos antigos vão para o `HISTORICO.md` no mesmo commit.

---

## 5. Gate de PR + CI para código de produção

Mudanças em código de produção nunca vão direto para a branch principal:
1. **Branch por issue:** `feat/issue-N-<slug>` ou `fix/issue-N-<slug>`, a partir da branch principal.
2. **Pull Request** referenciando a issue e o turno, com `STATUS: PR_ABERTO` na sala.
3. **CI verde**, se o projeto tiver CI. Sem CI, o Tech Lead roda os testes e registra o resultado na sala.
4. **Auditoria do Tech Lead** sobre o diff real e aprovação.
5. **Squash merge**, preservando um histórico linear.

`war_room.md` e `HISTORICO.md` ficam fora do gate: são debate, não código de produção.

---

## 6. Onboarding (primeira sessão após o `agloop init`)

Gatilho: o humano diz algo como *"instalei o AgLoop"*, ou você encontra o Gate de Prontidão (Seção 7) com itens pendentes (arquivos com `<!-- AGLOOP_TODO: ... -->`). Conduza nesta ordem, **em conversa com o PO**:

1. **Briefing do repositório.** Leia a estrutura, os manifestos de stack, os testes, o CI e o remoto Git. Responda em poucas linhas: o que você viu e o que falta para o projeto atender o framework.
2. **Apresentação.** Explique o AgLoop em até 5 linhas: Sala de Guerra (`war_room.md`), turnos com papéis, limite de 3 rodadas, PO com a palavra final sobre código de produção.
3. **Plano e permissão.** Liste o que precisa ser feito agora (os itens pendentes do Gate) e pergunte: *"Posso começar?"*. Só siga com o "sim" do PO.
4. **Roster e capacidades.** Pergunte quais agentes vão participar e com quais nomes distintos (ex.: `Claude`, `Claude-Cloud`, `Gemini`, `Codex`). Registre em `docs/gestao/roster-agentes.md` o que cada um consegue produzir e com qual ferramenta (ex.: páginas e wireframes, pesquisa aprofundada, protótipo visual, painel). Cada agente atualiza a própria linha ao entrar na sala.
5. **Preenchimento da governança.** Item a item, pergunte, proponha um rascunho e escreva o arquivo depois da confirmação do PO. Remova o marcador `AGLOOP_TODO` só quando o item estiver de fato preenchido.
6. **Ferramentas de apoio.** Para cada artefato, atribua o trabalho ao agente que tem a ferramenta (consultando o roster). Se ninguém na sala tiver, sugira uma ferramenta externa com **instrução explícita**: qual ferramenta, quais fontes subir, qual artefato gerar (relatório, pesquisa com fontes, mapa mental, resumo em áudio, FAQ etc.), o **prompt pronto para colar** e o **caminho de destino** no repositório (ex.: `docs/gestao/estudo-mercado.md`). O artefato volta e passa pela Sala de Guerra como qualquer documento.
7. **Fechamento.** Faça commit da governança, confira o Gate e diga: *"Gate de Prontidão 🟢. Sala ativa. Qual é a primeira demanda?"*

---

## 7. Gate de Prontidão

**Nenhuma linha de código de produção antes do Gate 🟢.** Não abra turno de código, não implemente e **nunca ofereça pular o protocolo** ("codar direto", "sem o ritual" e equivalentes). Pular o Gate só por ordem explícita do PO, registrada no `war_room.md` com o motivo.

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
- 📌 Versão do protocolo de vigília (SKILL.md) alinhada com os templates empacotados
- 📌 Painel de acompanhamento

Se algum 🔒 estiver pendente quando o PO pedir código, responda que o Gate ainda está 🔴, liste o que falta e ofereça resolver agora, nunca contornar.
