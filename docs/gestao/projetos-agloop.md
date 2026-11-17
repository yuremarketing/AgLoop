# Projetos que usam o AgLoop

Lista usada pelo Checklist Pós-Release (Seção 9 do `SKILL.md`): depois de cada Release, todos estes projetos são atualizados (`pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`).

| Projeto | Repositório | Instalado em | Versão do AgLoop | Última atualização |
| :--- | :--- | :--- | :--- | :--- |
| AgLoop (o próprio framework) | `yuremarketing/AgLoop` | — | fonte | contínua |
| Portfolio | `yuremarketing/yuremarketing.github.io` | 2026-11-11 | 0.7.0 + `main` (instalado via GitHub) — **pendente de atualização para 0.9.1** | 2026-11-11 |

Ao instalar o AgLoop em um projeto novo, acrescente uma linha aqui.

## Pendência do Checklist Pós-Release 0.9.1

O Release 0.9.1 (2026-11-17) foi publicado no PyPI e a branch `stable` avançada (Turno 50, Issue #78 — corrige a brecha de vigília desligada nos templates empacotados). Os itens 3 e 4 do Checklist (Seção 9 do `SKILL.md`) exigem ação **no próprio repositório do projeto consumidor** ou **nas máquinas do PO**, fora do working directory do AgLoop — superam as pendências equivalentes de 0.8.0 e 0.9.0, nunca executadas:
- **Portfolio** (`yuremarketing/yuremarketing.github.io`): `pip install --upgrade agloop` → `agloop update --dry-run` → aprovação do PO → `agloop update` → `agloop check`. Hoje está em `0.7.0 + main` (instalação insegura que o Release 0.8.0 já pretendia substituir e continua pendente; o `agloop update` levaria também a correção da brecha de vigília nos templates locais do projeto).
- **Plugin/extensão nas máquinas do PO:** atualizar `/plugin` (Claude Code) e a extensão do Gemini/Antigravity para `v0.9.1`/`stable`.
- **CLI local nesta máquina:** reinstalado e confirmado em `0.9.1` (Turno 50, após o merge do PR #79).
