# Roster e Capacidades — AgLoop

Inventário de agentes ativos na Sala de Guerra (`war_room.md`) e o que cada um consegue produzir. Atualizado por qualquer agente ao entrar na sala ou ganhar uma ferramenta nova (Seção 7 do `.claude/skills/vigilia/SKILL.md`).

| Agente | Ferramentas / Capacidades | Observações |
| :--- | :--- | :--- |
| **Claude** | Claude Artifacts (painel de gestão, páginas, wireframes), publicação ao vivo do painel (`docs/gestao/painel-agloop.html`), pesquisa documental, execução de testes/CI local | Sessão interativa local (Claude Code), vigília via `scripts/vigia.py --agent Claude --once` rastreada pelo harness |
| **Gemini** | Google Antigravity, Canvas, Deep Research | Sessão local/cloud, Tech Lead e Dev Especialista alternados por turno |
| **Claude-Cloud** | Mesmas capacidades do Claude (Artifacts, pesquisa), execução em container cloud | Papel recorrente: documentação e achados de campo (ex.: casos reais em outros projetos como `portfolio`); limite de ~2h por tarefa em segundo plano |

<!-- AGLOOP_TODO: ao adicionar um novo agente à sala (ex.: Codex, Cursor, modelo local via agloop run), inclua uma linha nesta tabela antes de atribuir artefatos a ele. -->
