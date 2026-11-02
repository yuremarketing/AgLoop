# ADR 0005: Evolução para Motor Cognitivo Google ADK, Controle de Consenso e Distribuição Plugin/MCP

- **Status:** Proposta (Em RFC — [Issue #2](https://github.com/yuremarketing/AgLoop/issues/2) e [Issue #4](https://github.com/yuremarketing/AgLoop/issues/4))
- **Data:** 2026-11-01 (Turno 1)
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

Atualmente, `core/agent.py` realiza apenas uma chamada direta a `litellm.completion()` passando o texto bruto de `war_room.md`:
1. **Agentes "cegos" no modo standalone:** Fora das sessões interativas do Claude Code / Antigravity, o agente invocado via `main.py` não possui ferramentas (Tools) para ler arquivos do repositório, inspecionar `git diff` ou rodar `pytest` antes de opinar.
2. **Ausência de freio automático de consenso:** O `core/runner.py` não distingue quando os agentes já chegaram a um acordo (`CONSENSUS`) ou quando precisam de decisão humana (`WAITING_HUMAN`), podendo continuar gerando turnos desnecessários.
3. **Distribuição e Integração Nativa:** Para que qualquer projeto adote o AgLoop rapidamente no Claude Code ou no Antigravity, o framework precisa ser empacotável via `pyproject.toml`, expor ferramentas via protocolo **MCP (Model Context Protocol)** e fornecer **Slash Commands / Skills** prontos.

## Decisão Proposta (Sequenciada nos Marcos M3 e M4)

1. **Controle de Contexto e Consenso (`core/war_room.py` e `core/runner.py` — Marco M3):**
   - Adicionar `WarRoom.read_recent(max_turns=6)` para janela deslizante de contexto, preservando `read_all()` para retrocompatibilidade com a suíte de testes existente.
   - Reconhecer marcadores estruturados `<!-- AGLOOP_STATE: WAITING_HUMAN -->` e `<!-- AGLOOP_STATE: CONSENSUS -->` no `Runner`, pausando o loop de inferência até intervenção humana ou novo turno.
2. **Motor Cognitivo Google ADK (`core/agent.py` — Marco M3):**
   - Substituir a chamada crua ao LiteLLM por `google.adk.agents.LlmAgent` encapsulando `LiteLlm(model=...)` para manter suporte multi-provedor (Gemini, Claude, OpenAI).
   - Equipar o agente com um conjunto estrito de **Tools seguras somente-leitura e diagnóstico** (`read_file`, `list_dir`, `git_diff`, `run_pytest`), bloqueando acesso a `.env`/credenciais e mantendo a assinatura pública `agent.generate_response(context)` 100% compatível com `tests/test_runner.py`.
3. **Empacotamento Python, Plugin e MCP (`pyproject.toml`, `.claude-plugin/`, `.mcp.json` — Marcos M3/M4):**
   - Criar `pyproject.toml` expondo o entry point CLI `agloop`.
   - Expor servidor MCP (`read_war_room`, `post_war_room_message`, `get_lock_status`) e manifesto `.claude-plugin/plugin.json` com Slash Commands (`/agloop:vigia`, `/agloop:status`, `/agloop:debate`).

## Consequências

### Positivas
- Transforma os agentes do AgLoop em engenheiros autônomos capazes de verificar código e testes reais antes de debater.
- Elimina o risco financeiro de ping-pong infinito de tokens (Risco `R01` mitigado).
- Permite instalação padronizada (`pip install -e .`) e uso nativo via MCP e `adk web`.

### Restrições de Segurança
- Nenhuma tool de escrita/modificação de código de produção será habilitada por padrão nos agentes sem gate explícito de aprovação do PO (Risco `R06` mitigado).
