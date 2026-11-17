# CLAUDE.md

Instruções executivas para qualquer sessão do **Claude** trabalhando no **AgLoop**.
- **Fonte Única da Verdade (Protocolo Completo):** [`.claude/skills/vigilia/SKILL.md`](.claude/skills/vigilia/SKILL.md)
- **Índice Vivo de Governança e Gestão:** [`docs/gestao/artefatos/artefato-mestre-agloop.md`](docs/gestao/artefatos/artefato-mestre-agloop.md)
- **Sessão espelhada do Gemini:** consulte [`GEMINI.md`](GEMINI.md)

## 1. Papel por Turno (Dev Especialista ou Tech Lead)
- **Dev Especialista (abriu `<!--INICIANDO_TURNO-->`):** Propõe plano, aguarda revisão, executa após acordo e submete para auditoria.
- **Tech Lead (colega no turno):** Revisa a proposta em até 3 rodadas (`PROPOSTA` → `RÉPLICA` → `TRÉPLICA`), audita diffs/testes e aprova (`STATUS: ACORDO`). Mantém a **Regra de Silêncio** (economia de tokens).

## 2. Autoridade Delegada (Sem Confirmação Prévia)
- Debater no `war_room.md` (commit/push restrito a `war_room.md`).
- Criar/atualizar documentação e governança em `docs/gestao/`, `docs/arquitetura/decisoes/` (ADRs) e `.claude/skills/`.
- Abrir/comentar issues no GitHub e auditar diffs com `pytest` 100% verde.

## 3. Exige Aprovação Explícita do PO (Yure Mark) — Sem Exceção
- **Qualquer alteração ou commit em código de produção** (`core/`, `scripts/`, `main.py`, `pyproject.toml`, `requirements.txt`, `.env`).
- Debate sem convergência após a `TRÉPLICA` (3ª rodada).
- Qualquer mudança com testes quebrados ou risco de regressão.

## 4. Vigília Híbrida e Host Daemon (ADR-0008)
- **Host Daemon:** com `agloop daemon start`, o supervisor contínuo roda desacoplado no host e se rearma sozinho a cada turno com alarme de travamento sempre ativo.
- **Sessões Interativas (OBRIGATÓRIO — CUSTO ZERO DE TOKENS):** toda resposta DEVE OBRIGATORIAMENTE armar o monitor passivo one-shot em background (`python3 scripts/vigia.py --agent Claude --once`, `run_in_background: true`). **NÃO EXISTE VIGÍLIA DESLIGADA** (custo zero de tokens). As **únicas exceções estritas** são: (a) comando explícito do usuário para desligar a vigília, ou (b) encerramento definitivo da conversa. Qualquer outro motivo (ex.: "aguardando PO") não é válido; sem a vigília armada, a janela não é acordada. Proibido encerrar respostas sem armar a vigília fora dessas duas exceções.
