---
name: vigilia
description: "Protocolo canônico da Sala de Guerra do AgLoop (Claude ⇄ Gemini/Antigravity): inversão de papéis por turno (Dev Especialista / Tech Lead), regra de silêncio, autoridade delegada vs. limites do PO (Yure Mark), debate travado em 3 rodadas (Proposta → Réplica → Tréplica), vigília híbrida one-shot e fechamento atômico."
metadata:
  author: yuremarketing
  version: "1.1.0"
---

# Vigília — Protocolo Canônico da Sala de Guerra (AgLoop)

Fonte Única da Verdade (SSOT) de governança operacional entre **Yure Mark (Product Owner)**, **Claude** e **Gemini/Antigravity** no projeto **AgLoop**.
O canal de comunicação entre agentes (IPC) é o arquivo `war_room.md` na raiz do repositório, sincronizado via `GitLock` (`core/git_lock.py`).

---

## 1. Papéis na Sala de Guerra (Inversão Turno a Turno)

Não existe papel fixo para nenhuma das LLMs. Em cada turno aberto no `war_room.md`:
- **Dev Especialista (quem abre o turno com `<!--INICIANDO_TURNO-->`):** Analisa a demanda, publica a `PROPOSTA` detalhada, aguarda a revisão, executa a implementação/documentação acordada e submete para auditoria.
- **Tech Lead (a LLM colega daquele turno):** Audita a proposta (máx. 3 rodadas: `PROPOSTA` → `RÉPLICA` → `TRÉPLICA`), revisa o diff real (`git diff`/`git show`), valida a suíte de testes (`pytest`) e aprova (`STATUS: ACORDO`) antes do fechamento (`<!--FIM_TURNO-->`).

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
- **Qualquer commit ou alteração em código de produção** (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`) ou infraestrutura/credenciais (`.env`).
- Aprovar mudanças com testes falhando (`pytest` vermelho) ou com risco de regressão.
- Qualquer debate que ultrapasse a 3ª rodada (`TRÉPLICA`) sem convergência técnica — escale imediatamente ao Yure Mark.

---

## 3. Vigília Híbrida (Zero Custo de Tokens em Ociosidade)

- **Regra de Ouro:** Nunca utilize cron/schedule de LLM que dispare inferências periódicas em ociosidade.
- **Mecanismo Passivo One-Shot:** O monitor em background (`scripts/vigia.py --agent <Nome> --once`) observa o `mtime` local de `war_room.md` (a cada `2s`, custo zero) e realiza `git fetch` periódico (a cada `30s`).
- **Despertar por Evento:** O processo do monitor só encerra (`exit 0`) quando detecta que o último orador no `war_room.md` mudou para o agente colega, acordando a sessão automaticamente via conclusão da task em background.

---

## 4. Formato de Turno e Sincronização Git (`GitLock`)

```markdown
<!--INICIANDO_TURNO-->
Início: AAAA-MM-DD HH:MM · Commit-base: <hash> · Agente: <Claude|Gemini> · <Título curto>

## Turno N — <Agente> (AAAA-MM-DD)

## <Agente>

**Proposta — <Agente> (Dev Especialista)**
...
STATUS: PROPOSTA | RÉPLICA | TRÉPLICA | ACORDO | FEITO | CONCLUIDO
PRÓXIMO: <próximo passo claro>

<!--FIM_TURNO-->
Fim: AAAA-MM-DD HH:MM · Commit: <hash> · Agente: <Agente>
```

### Regras de Segurança do `GitLock` (`core/git_lock.py`)
1. **Commits Escopados:** Apenas os caminhos da Sala de Guerra (`war_room.md`, `HISTORICO.md`) são adicionados/commitados pelo loop automático (`git commit -- <paths>`).
2. **Proibição Absoluta de `reset --hard`:** Em caso de perda de corrida de push (`lost_race`), a reversão é cirúrgica (`git reset --soft HEAD~1` + `git checkout HEAD -- <paths>`), preservando qualquer trabalho não commitado na working tree.
3. **Autoria Isolada por Agente:** Cada commit registra `GIT_AUTHOR_NAME`/`GIT_AUTHOR_EMAIL` e `GIT_COMMITTER_NAME`/`GIT_COMMITTER_EMAIL` escopados ao subprocesso do agente ativo, sem vazar variáveis para o ambiente global.
4. **Fechamento e Arquivamento Atômico:** Ao fechar um turno (`<!--FIM_TURNO-->` / `CONSENSUS`), o arquivamento de turnos antigos em `HISTORICO.md` ocorre no mesmo commit/push atômico.

---

## 5. Painel de Gestão — Responsabilidade Portável entre Agentes (Issue #6)

O AgLoop se propõe heterogêneo (Claude ⇄ Gemini/Antigravity ⇄ outros via `LiteLlm`), então a governança visual não pode depender de uma única plataforma. O contrato é **"precisa ter um agente capaz de publicar e manter um painel ao vivo equivalente"**, não "precisa ser Claude".

1. **Fonte Única Versionada (`docs/gestao/painel-agloop.html`):** arquivo HTML autocontido (zero dependências externas além de Google Fonts, tema claro/escuro nativo). **Qualquer agente** (Claude, Gemini/Antigravity ou outro) atualiza esse arquivo ao fechar um turno relevante — isso nunca fica obsoleto, independe de quem está com sessão ativa.
2. **Publicação Ao Vivo — Claude-Exclusivo, *Best Effort*:** publicar/atualizar um Claude Artifact é ferramenta exclusiva da plataforma Claude — Gemini/Antigravity e outros LLMs não têm acesso a ela, de forma alguma. Quando uma sessão Claude estiver ativa no fechamento de um turno, republique `docs/gestao/painel-agloop.html` como Artifact, preservando a URL entre atualizações. Sem sessão Claude ativa, isso simplesmente não acontece — e está tudo bem, veja a regra 3.
3. **Regra de Fallback Explícita (Transparência Obrigatória):** todo fechamento de turno relevante declara o estado do painel na própria mensagem, nunca falhando silenciosamente:
   - `PAINEL: atualizado em docs/gestao/painel-agloop.html + publicado ao vivo` (sessão Claude ativa); ou
   - `PAINEL: atualizado localmente em docs/gestao/painel-agloop.html, sem publicação ao vivo nesta sessão` (nenhum agente da sessão tem ferramenta de publicação equivalente).
   Se outro LLM/agente quiser ocupar o papel de publicador sem ter Claude disponível, a obrigação é ativa: oferecer um mecanismo de publicação ao vivo similar, igual ou melhor — não deixar o painel cair pro fallback como comportamento padrão aceitável.
