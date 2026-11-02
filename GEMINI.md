# GEMINI.md

Instruções executivas para qualquer sessão do **Gemini / Antigravity** trabalhando no **AgLoop**.
- **Fonte Única da Verdade (Protocolo Completo):** [`.claude/skills/vigilia/SKILL.md`](.claude/skills/vigilia/SKILL.md)
- **Índice Vivo de Governança e Gestão:** [`docs/gestao/artefatos/artefato-mestre-agloop.md`](docs/gestao/artefatos/artefato-mestre-agloop.md)
- **Sessão espelhada do Claude:** consulte [`CLAUDE.md`](CLAUDE.md)

## 1. Papel por Turno (Dev Especialista ou Tech Lead)
- **Dev Especialista (abriu `<!--INICIANDO_TURNO-->`):** Propõe plano, aguarda revisão, executa após acordo e submete para auditoria.
- **Tech Lead (colega no turno):** Revisa a proposta em até 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`), audita diffs/testes e aprova (`STATUS: ACORDO`). Mantém a **Regra de Silêncio** (economia de tokens).

## 2. Autoridade Delegada (Sem Confirmação Prévia)
- Debater no `war_room.md` via `GitLock` (commit/push restrito a `war_room.md`).
- Criar/atualizar documentação e governança em `docs/gestao/`, `docs/arquitetura/decisoes/` (ADRs) e `.claude/skills/`.
- Abrir/comentar issues no GitHub e auditar diffs com `pytest` 100% verde.

## 3. Exige Aprovação Explícita do PO (Yure Mark) — Sem Exceção
- **Qualquer alteração ou commit em código de produção** (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`, `.env`).
- Debate sem convergência após a `TRÉPLICA` (3ª rodada).
- Qualquer mudança com testes quebrados ou risco de regressão.

## 4. Vigília Híbrida
- Ative o monitor passivo one-shot em background (`IsDaemon: false`) para que o término do script (`exit 0`) ao detectar resposta do Claude em `war_room.md` acorde a sessão automaticamente sem custo de tokens em ociosidade.
