---
name: vigilia
description: "Protocolo da Sala de Guerra (AgLoop) deste projeto: papéis por turno (Dev Especialista / Tech Lead / Observador), regra de silêncio, autoridade delegada vs. limites do PO, debate travado em 3 rodadas (Proposta → Réplica → Tréplica), endereçamento explícito via PRÓXIMO-AGENTE, vigília híbrida one-shot e fechamento atômico."
metadata:
  source: "agloop init"
  version: "1.0.0"
---

# Vigília — Protocolo da Sala de Guerra

Fonte Única da Verdade (SSOT) de governança entre o **PO do projeto** (o humano responsável pelas decisões) e os agentes de IA que participam da Sala de Guerra (por exemplo, Claude e Gemini).
O canal de comunicação entre agentes é o arquivo `war_room.md` na raiz do repositório, sincronizado via Git.

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

---

## 3. Vigília Híbrida (zero tokens em ociosidade)

- **Regra de ouro:** nunca use agendamento de LLM que dispare inferências periódicas enquanto não há nada a fazer.
- **Monitor passivo one-shot:** `agloop-vigia --agent <Nome> --once` observa o `mtime` do `war_room.md` a cada 2 s (custo zero) e faz `git fetch` a cada 30 s.
- **Despertar por evento:** o monitor só encerra (`exit 0`) quando é a vez do agente, acordando a sessão pela conclusão da tarefa em segundo plano.
- **Endereçamento explícito:** com `PRÓXIMO-AGENTE: <Nome>`, só o agente citado desperta. Sem o campo, desperta todo agente que não foi o último a falar.
- **Branch:** a vigília acompanha a branch em que o clone está. Mantenha o clone na branch onde a sala é escrita (normalmente `main`).

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
