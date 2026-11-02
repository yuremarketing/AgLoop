# ADR 0003: Vigília Híbrida (`mtime` Local + `git fetch` Remoto com Backoff e Modo One-Shot)

- **Status:** Aceita
- **Data:** 2026-10-22 (Commit `2e5cc85` / Evoluída no Turno 1 em 2026-11-01)
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

Para que dois agentes conversem de forma fluida na Sala de Guerra (`war_room.md`), eles precisam detectar rapidamente quando o colega respondeu:
- Se o loop executar `git pull` a cada 2 segundos, causará sobrecarga de rede, rate-limiting no GitHub e lentidão de I/O.
- Se o loop esperar 60 segundos entre checagens, a colaboração local na mesma máquina fica artificialmente lenta.
- Se a checagem for feita por inferência periódica de LLM (cron de prompt), haverá queima contínua de tokens em ociosidade.
- Além disso, quando executado como tarefa em background de uma sessão interativa (Claude Code ou Antigravity), um script em `while True` infinito nunca encerra (`exit 0`), não disparando o evento de conclusão de tarefa que acorda o agente.

## Decisão

Adotar a arquitetura de **Vigília Híbrida em Dois Níveis com Suporte a Wake-up One-Shot**:
1. **Nível 1 — Polling Local de Custo Zero (`local_poll_interval = 2.0s`):**
   - Monitora `os.path.getmtime("war_room.md")` e o último cabeçalho `## <Orador>` diretamente no sistema de arquivos local, sem invocar subprocessos Git nem chamadas de rede.
2. **Nível 2 — Sincronização Remota Espaçada (`remote_poll_interval = 30.0s`):**
   - Executa `git fetch` apenas quando o intervalo remoto expira, aplicando **jitter aleatório (`±20%`)** para evitar *thundering herd* entre agentes e **backoff exponencial** em caso de falhas transitórias de rede.
3. **Unificação DRY e Modo One-Shot (`--once` / Exit-on-Speaker-Change):**
   - A lógica base de vigília reside em `core/runner.py`, e `scripts/vigia.py` atua como um *thin wrapper* CLI que adiciona os argumentos `--agent <Nome>` e `--once`.
   - No modo `--once`, assim que o último orador de `war_room.md` muda para um agente diferente de `--agent`, o script encerra imediatamente com `sys.exit(0)`, acordando a sessão da LLM sem gastar um único token durante toda a espera.

## Consequências

### Positivas
- Latência de detecção $\le 2\text{s}$ para agentes na mesma máquina e $\le 30\text{s}$ para agentes distribuídos.
- Custo de tokens em ociosidade estritamente igual a **zero**.
- Despertar reativo nativo em qualquer ambiente de agente que monitore término de processos em background (Risco `R04` mitigado).
