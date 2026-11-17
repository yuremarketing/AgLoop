# ADR 0007: Arquitetura Local-First do MCP e Limite de Escopo Remoto

- **Status:** Aceita (Tréplica/Acordo de Claude e Gemini, Turno 45, [Issue #33](https://github.com/yuremarketing/AgLoop/issues/33))
- **Data:** 2026-11-17 (Turno 45)
- **Decisores:** Claude (Dev Especialista) e Gemini (Tech Lead), por Autoridade Delegada (Seção 2 do `SKILL.md`) — escopo puramente documental, sem código em `core/`

---

## Contexto e Problema

Durante a submissão ao Claude Directory (achado pós-Issue #28), o validador sinalizou que o servidor MCP `agloop` (`plugin/scripts/run_mcp_server.py` → `core/mcp_server.py`) é local (stdio): roda em Claude Code e Cowork, mas não existe nas superfícies **Claude apps (web, desktop, mobile)** do claude.ai.

O servidor depende 100% de filesystem/Git local via `core/war_room.py` e `core/git_lock.py` para implementar `read_war_room`, `post_war_room_message` e `get_lock_status`. Essas superfícies de claude.ai não têm acesso equivalente ao disco do desenvolvedor.

A Issue [#33](https://github.com/yuremarketing/AgLoop/issues/33) registrou o achado como investigação futura, sem compromisso de prazo, pedindo avaliação de arquitetura antes de qualquer implementação.

## Opções Consideradas

| Opção | Resolve o gap? | Custo / efeito colateral |
| :--- | :--- | :--- |
| **1. MCP remoto hospedado** (SaaS multi-tenant) | Sim | Serviço HTTP/SSE exposto à rede (ex.: Cloud Run, Fly.io) custodiando credenciais de escrita no GitHub de terceiros fora da máquina do desenvolvedor; novo modelo de concorrência substituindo `mtime`+`fetch` do `GitLock` local pelo optimistic locking por SHA da API de Contents do GitHub; custo de infra e manutenção contínuos para demanda ainda não validada por nenhum usuário real. Tensiona diretamente com o confinamento `LGPD-03` que o `mcp_server.py` já segue hoje. |
| **2. Documentar como limitação aceita** (recomendada) | Não fecha o gap, só o nomeia | Zero código, zero infra nova; formaliza "local-first por design" como decisão arquitetural, não omissão. |

## Decisão

**Opção 2.** O AgLoop permanece **local-first e serverless-by-design** em toda a sua superfície de MCP:

1. **Cláusula pétrea de segurança preservada.** Todo o desenho do AgLoop (Git como broker serverless, lock atômico em disco, confinamento `LGPD-03`) parte da premissa de que dados, repositório e credenciais jamais saem da máquina do desenvolvedor. Um MCP remoto hospedado por nós romperia essa premissa ao custodiar tokens de escrita no GitHub de terceiros em nuvem.
2. **Sem tração comprovada.** Não há demanda de usuário real pedindo acesso via claude.ai web/desktop/mobile; investir em infraestrutura nova sem validação é custo antecipado sem retorno demonstrado.
3. **Diretriz para demanda futura (Self-Hosted, não SaaS):** se surgir demanda real, a rota arquitetural correta não é um SaaS multi-tenant mantido pelo projeto, e sim um padrão **Self-Hosted** em que o próprio usuário expõe seu servidor stdio (ex.: container Docker local, ou túnel privado WireGuard/Tailscale) com controle total das próprias chaves — preserva a cláusula pétrea ao transferir, e não eliminar, a responsabilidade pela credencial.

## Consequências

### Positivas
- Nenhuma superfície nova de ataque é aberta; nenhuma credencial de terceiro passa a residir fora da máquina do desenvolvedor.
- Zero custo de infraestrutura recorrente.
- A limitação passa a ser uma decisão documentada e rastreável, não um gap silencioso na submissão ao Claude Directory.

### Negativas / Riscos
- O AgLoop continua indisponível nas superfícies Claude apps (web/desktop/mobile) — o gap da Issue #33 não é fechado, apenas nomeado.
- Se a demanda real aparecer, a opção Self-Hosted (item 3) ainda exige desenho e implementação próprios, não é solução pronta.

## Decisão Registrada

Tréplica/Acordo entre Claude (Dev Especialista, Turno 45) e Gemini (Tech Lead): Opção 2 aceita por Autoridade Delegada, sem necessidade de aprovação do PO — escopo é 100% documental/arquitetural (`docs/`), sem alteração em `core/`, `scripts/`, `main.py` ou qualquer outro código de produção.
