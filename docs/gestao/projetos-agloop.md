# Projetos que usam o AgLoop

Lista usada pelo Checklist Pós-Release (Seção 9 do `SKILL.md`): depois de cada Release, todos estes projetos são atualizados (`pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`).

| Projeto | Repositório | Instalado em | Versão do AgLoop | Última atualização |
| :--- | :--- | :--- | :--- | :--- |
| AgLoop (o próprio framework) | `yuremarketing/AgLoop` | — | fonte | contínua |
| Portfolio | `yuremarketing/yuremarketing.github.io` | 2026-11-11 | `0.9.2` (protocolo `SKILL.md` local v1.4.0 → v1.7.0 via `agloop update`) | 2026-11-17 |

Ao instalar o AgLoop em um projeto novo, acrescente uma linha aqui.

## Checklist Pós-Release 0.9.2

O Release 0.9.2 (2026-11-17) foi publicado no PyPI e a branch `stable` avançada (Turno 52, Issue #82 — empacota a correção da Issue #80/PR #81). Itens executados fora do working directory do AgLoop:
- **Portfolio** (`yuremarketing/yuremarketing.github.io`): protocolo já estava em `v1.7.0` (atualizado no Turno 50); `pip install --upgrade agloop` reaplicado para `0.9.2`. `agloop check` nessa máquina: 🔴, por um item pré-existente e não relacionado (`termo-abertura.md`/`visao.md` ausente) — fora do escopo desta atualização.
- **Plugin/extensão nas máquinas do PO:** ainda pendente — atualizar `/plugin` (Claude Code) e a extensão do Gemini/Antigravity para `v0.9.2`/`stable`.
- **CLI local nesta máquina:** reinstalado e confirmado em `0.9.2` (Turno 52, após o merge do PR #83).

### Achado de UX no `agloop update --dry-run` — RESOLVIDO (Issue #80, PR #81, Release v0.9.2)
O diff do `--dry-run` listava `docs/gestao/roster-agentes.md` como `[CUSTOMIZADO/DEFASADO]` com diff completo de substituição, mesmo `run_update` sempre preservando o arquivo na prática. Corrigido na raiz: `core/update_scaffold.py` agora marca arquivos em `PROTECTED_ONCE_CREATED` com `needs_update = False` e `diff = ""`, reportando `[PRESERVADO]` no sumário. Já publicado no PyPI (`0.9.2`).
