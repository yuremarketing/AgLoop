---
description: Mostra o estado atual da Sala de Guerra do AgLoop — último orador, estado (ACTIVE/WAITING_HUMAN/CONSENSUS) e resumo de Marcos/Issues.
---

Rode o seguinte para inspecionar o estado atual da Sala de Guerra sem consumir tokens de LLM:

```bash
python3 -c "
from core.war_room import WarRoom
wr = WarRoom()
print('Estado:', wr.get_state())
print('Último orador:', wr.get_last_speaker())
"
```

Em seguida, leia as últimas linhas de `war_room.md` (ou use a ferramenta MCP `read_war_room`/`get_lock_status` se o servidor `agloop` estiver conectado) para resumir o turno aberto, e consulte `docs/gestao/backlog-produto.md` para o resumo de Marcos/Issues/Épicos em andamento.
