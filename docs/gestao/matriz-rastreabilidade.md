# Matriz de Rastreabilidade — AgLoop

Artefato único de rastreabilidade do projeto, criado pela Issue [#57](https://github.com/yuremarketing/AgLoop/issues/57) (Turno 42) para substituir o rastreamento hoje espalhado entre `docs/gestao/backlog-produto.md`, o Artefato Mestre e `HISTORICO.md`.

> **Fonte canônica da regra:** [`.claude/skills/vigilia/SKILL.md`](../../.claude/skills/vigilia/SKILL.md), seção "Múltiplas Tarefas por Turno" / "Matriz de Rastreabilidade Única".

## Como manter esta matriz

- **Quem atualiza:** o Dev Especialista do turno, a cada abertura e fechamento de tarefa (`T<turno>.<n>` ou turno de tarefa única).
- **Coluna "Arquivos tocados":** é a base para o Tech Lead conferir independência entre tarefas do mesmo turno — duas tarefas abertas tocando o mesmo arquivo violam a regra da Seção 4 do `SKILL.md`.
- **Linhas novas:** uma por entrega relevante (issue fechada, PR mergeado ou documentação entregue por Autoridade Delegada). Não é granular por commit.
- **Verificação automática** (`agloop check` apontando matriz desatualizada ou conflito de arquivos entre tarefas abertas) é Fase 3 da Issue #57 — código em `core/`, pendente de turno próprio com aprovação do PO.

## Template para nova linha

```markdown
| `<Épico>` | [#<issue>](https://github.com/yuremarketing/AgLoop/issues/<issue>) | Turno `<N>`<br>`T<N>.<n>` | PR #<n> / Commits diretos | `<arquivo1>`, `<arquivo2>` | `pytest` `<x>/<x>` | ✅ Concluído / 🔄 Em andamento / ⏸️ Adiado |
```

## Histórico consolidado (Issues #39–#69)

| Épico | Issue | Turno / Tarefa | PR | Arquivos tocados | Testes | Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| E07 (Templates de Governança) | [#39](https://github.com/yuremarketing/AgLoop/issues/39) | Turno 27 | PR #40 | `core/templates/skills/vigilia/SKILL.md` | `pytest` 120/120 | ✅ Concluído |
| E07 (Mensagem Próximos Passos) | [#41](https://github.com/yuremarketing/AgLoop/issues/41) | Turno 27 | PR #43 | `core/init_scaffold.py` | `pytest` 120/120 | ✅ Concluído |
| E07 (Gate de Prontidão / Check) | [#42](https://github.com/yuremarketing/AgLoop/issues/42) | Turno 29, 31 | PR #49, #51 | `core/readiness_gate.py`, `main.py` | `pytest` 158/158 | ✅ Concluído |
| E10 (Vigília 3 Agentes / Stall) | [#44](https://github.com/yuremarketing/AgLoop/issues/44) | Turno 28 | PR #46, #47 | `core/runner.py`, `scripts/vigia.py` | `pytest` 128/128 | ✅ Concluído |
| E08 (Banner Visual Autorização) | [#45](https://github.com/yuremarketing/AgLoop/issues/45) | Turno 29, 31 | PR #48, #50 | `core/banner.py` | `tests/test_banner.py` 143/143 | ✅ Concluído |
| E01 (Branch Polling no Lock) | [#52](https://github.com/yuremarketing/AgLoop/issues/52) | Turno 32 | PR #53 | `core/git_lock.py` | `tests/test_git_lock.py` 160/160 | ✅ Concluído |
| E07 (Subcomando `agloop update`) | [#54](https://github.com/yuremarketing/AgLoop/issues/54) | Turno 33 | PR #55 | `core/update_scaffold.py`, `core/version_check.py` | `tests/test_update_scaffold.py` 177/177 | ✅ Concluído |
| E11 (Release 0.8.0 / Branch Stable) | [#56](https://github.com/yuremarketing/AgLoop/issues/56) | Turno 34, 35 | PR #59 | `.github/workflows/publish.yml`, `docs/` | CI 9/9 verde | ✅ Concluído |
| E12.1–E12.2 (Manual de Uso PT-BR + link no README) | [#37](https://github.com/yuremarketing/AgLoop/issues/37) | Turno 25, 26 | Commits diretos | `docs/manual/manual-de-uso.md`, `README.md` | — | ✅ Concluído |
| E10 (Fix `repo_path` na vigília) | [#62](https://github.com/yuremarketing/AgLoop/issues/62) | Turno 37 | PR #64 | `scripts/vigia.py` | `pytest` 177/177 | ✅ Concluído |
| E08 (Entrypoint `agloop-alert`) | [#63](https://github.com/yuremarketing/AgLoop/issues/63) | Turno 38 | PR #65 | `core/banner.py`, `pyproject.toml`, `SKILL.md` | `tests/test_banner.py` 178/178 | ✅ Concluído |
| E07 (`init` aponta para `#stable`) | [#60](https://github.com/yuremarketing/AgLoop/issues/60) | Turno 39 | PR #67 | `core/init_scaffold.py`, `docs/manual/` | `tests/test_mcp_and_privacy.py` 179/179 | ✅ Concluído |
| E07 (Subcomando `agloop report`) | [#61](https://github.com/yuremarketing/AgLoop/issues/61) | Turno 40 | PR #68 | `core/report_bug.py`, `main.py` | `tests/test_report_bug.py` 201/201 | ✅ Concluído |
| E12.3 (README EN + User Guide bilíngue) | [#58](https://github.com/yuremarketing/AgLoop/issues/58) | Turno 41 | Commits diretos (`36b76f9`, `75e4f06`) | `README.md`, `README.pt-BR.md`, `docs/manual/user-guide.md`, `docs/manual/manual-de-uso.md`, `docs/gestao/backlog-produto.md` | `pytest` 201/201 | ✅ Concluído |
| Vigília autônoma (achado de campo) | [#69](https://github.com/yuremarketing/AgLoop/issues/69) | Turno 43 | PR #71 | `core/runner.py`, `core/readiness_gate.py`, `SKILL.md` | `pytest` 213/213 | ✅ Concluído |
| E? (Turnos com múltiplas tarefas + matriz única) | [#57](https://github.com/yuremarketing/AgLoop/issues/57) | Turno 42 | Commits diretos (`c8452ce`, `12a1722`) | `.claude/skills/vigilia/SKILL.md`, `docs/gestao/matriz-rastreabilidade.md` | `pytest` 201/201 | ✅ Concluído |

*Linhas anteriores à Issue #39 (Turnos 1–26) seguem disponíveis em `HISTORICO.md`; migração retroativa completa não é objetivo desta issue — o foco é parar de perder rastro a partir de agora.*
