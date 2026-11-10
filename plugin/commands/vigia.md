---
description: Inicia o monitor passivo one-shot da Sala de Guerra do AgLoop (vigia.py --once), acordando a sessão quando o agente colega responder.
---

Execute o monitor passivo da Sala de Guerra do AgLoop em background e aguarde a notificação de conclusão antes de continuar:

```bash
python3 scripts/vigia.py --agent "$ARGUMENTS" --once
```

Se nenhum argumento for informado, use o nome do agente ativo nesta sessão (ex.: `Claude` ou `Gemini`). O comando só retorna (`exit 0`) quando o agente colega responde no `war_room.md` — não consome tokens enquanto espera (vigília híbrida: `mtime` local a cada 2s, `git fetch` remoto a cada 30s). Depois que o comando finalizar, leia o `war_room.md` para ver a resposta nova e continue o protocolo descrito em `.claude/skills/vigilia/SKILL.md`.
