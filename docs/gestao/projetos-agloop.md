# Projetos que usam o AgLoop

Lista usada pelo Checklist Pós-Release (Seção 9 do `SKILL.md`): depois de cada Release, todos estes projetos são atualizados (`pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`).

| Projeto | Repositório | Instalado em | Versão do AgLoop | Última atualização |
| :--- | :--- | :--- | :--- | :--- |
| AgLoop (o próprio framework) | `yuremarketing/AgLoop` | — | fonte | contínua |
| Portfolio | `yuremarketing/yuremarketing.github.io` | 2026-11-11 | 0.7.0 + `main` (instalado via GitHub) — **pendente de atualização para 0.8.0** | 2026-11-11 |

Ao instalar o AgLoop em um projeto novo, acrescente uma linha aqui.

## Pendência do Checklist Pós-Release 0.8.0

O Release 0.8.0 (2026-11-11) foi publicado no PyPI e a branch `stable` foi criada. Os itens 3 e 4 do Checklist (Seção 9 do `SKILL.md`) exigem ação **no próprio repositório do projeto consumidor**, fora do working directory do AgLoop:
- **Portfolio** (`yuremarketing/yuremarketing.github.io`): `pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`. Hoje está em `0.7.0 + main` (instalação insegura que o próprio Release 0.8.0 pretende substituir).
- **Plugin/extensão nas máquinas do PO:** atualizar `/plugin` (Claude Code) e a extensão do Gemini/Antigravity para a nova versão/`stable`.
