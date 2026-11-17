# Projetos que usam o AgLoop

Lista usada pelo Checklist Pós-Release (Seção 9 do `SKILL.md`): depois de cada Release, todos estes projetos são atualizados (`pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`).

| Projeto | Repositório | Instalado em | Versão do AgLoop | Última atualização |
| :--- | :--- | :--- | :--- | :--- |
| AgLoop (o próprio framework) | `yuremarketing/AgLoop` | — | fonte | contínua |
| Portfolio | `yuremarketing/yuremarketing.github.io` | 2026-11-11 | `0.9.1` (protocolo `SKILL.md` local v1.4.0 → v1.7.0 via `agloop update`) | 2026-11-17 |

Ao instalar o AgLoop em um projeto novo, acrescente uma linha aqui.

## Checklist Pós-Release 0.9.1

O Release 0.9.1 (2026-11-17) foi publicado no PyPI e a branch `stable` avançada (Turno 50, Issue #78 — corrige a brecha de vigília desligada nos templates empacotados). Itens executados fora do working directory do AgLoop:
- **Portfolio** (`yuremarketing/yuremarketing.github.io`): `agloop update --dry-run` revisado, `agloop update --yes` aplicado (commit `ce9933c`) — `.claude/skills/vigilia/SKILL.md` local atualizado de `v1.4.0` para `v1.7.0` (backup em `.bak`), `docs/gestao/roster-agentes.md` preservado intacto (já preenchido). `agloop check` nessa máquina: 🔴, mas por um item pré-existente e não relacionado (`termo-abertura.md`/`visao.md` ausente) — fora do escopo desta atualização.
- **Plugin/extensão nas máquinas do PO:** ainda pendente — atualizar `/plugin` (Claude Code) e a extensão do Gemini/Antigravity para `v0.9.1`/`stable`.
- **CLI local nesta máquina:** reinstalado e confirmado em `0.9.1` (Turno 50, após o merge do PR #79).

### Achado de UX no `agloop update --dry-run` (não corrigido, registrar para turno futuro)
O diff do `--dry-run` lista `docs/gestao/roster-agentes.md` como `[CUSTOMIZADO/DEFASADO]` com um diff completo de substituição — mas `run_update` (linha 226-229 de `core/update_scaffold.py`) sempre pula esse arquivo quando já existe localmente, preservando-o. O dry-run não reflete essa proteção: alarmou (a mim) a possibilidade de perda de dados de governança preenchida, quando na prática `--yes` nunca sobrescreve o arquivo. Sugestão: excluir `roster-agentes.md` da lista de diffs do dry-run (ou anotar "(preservado, nunca sobrescrito)") quando já existir localmente.
