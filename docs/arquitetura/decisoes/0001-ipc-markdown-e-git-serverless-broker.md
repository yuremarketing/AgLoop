# ADR 0001: IPC via Markdown (`war_room.md`) e Git como Message Broker Serverless

- **Status:** Aceita
- **Data:** 2026-10-09 (Formalizada em 2026-11-01 no Turno 1)
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

Sistemas multi-agente tradicionais dependem de infraestrutura dedicada de mensageria (Redis, RabbitMQ, bancos de dados relacionais ou servidores WebSocket) para coordenar turnos e compartilhar contexto entre agentes autônomos como Claude e Gemini. Isso cria atrito de configuração, dificulta a auditoria humana do histórico de decisões e impede que o loop funcione de forma *plug-and-play* em qualquer repositório de código.

## Decisão

Adotar uma arquitetura **100% baseada no repositório Git**:
1. **Canal de IPC em Markdown (`war_room.md`):** Toda proposta, réplica, tréplica e decisão entre os agentes é registrada sequencialmente em um arquivo Markdown legível por humanos e versionado na branch principal (`main`).
2. **Git como Message Broker e Trava de Turno:** A sincronização entre sessões (locais ou em máquinas distintas) utiliza `git fetch`, `git pull --rebase` e `git push`. O turno atual é determinado deterministicamente pelo último cabeçalho de agente (`## <NomeDoAgente>`) registrado no arquivo.

## Consequências

### Positivas
- **Zero infraestrutura externa:** Funciona em qualquer repositório Git com remoto configurado (GitHub, GitLab, bare repo local).
- **Auditabilidade nativa:** Todo o racional arquitetural fica registrado no histórico do Git (`git log` / `git blame`) e pode ser inspecionado ou editado diretamente pelo Product Owner em qualquer editor de texto.
- **Portabilidade multi-host:** Agentes rodando na mesma máquina ou em máquinas separadas operam sob o mesmo protocolo.

### Negativas / Riscos Mitigados
- Exige disciplina no tamanho do arquivo Markdown ao longo do tempo (mitigado pelo arquivamento atômico em `HISTORICO.md` na [ADR 0004](0004-governanca-dry-ssot-autoria-e-fechamento-atomico.md) e janela deslizante na [ADR 0005](0005-motor-cognitivo-google-adk-e-plugin-mcp.md)).
- Exige tratamento rigoroso de condições de corrida em pushes simultâneos (resolvido na [ADR 0002](0002-lock-hibrido-atomico-e-reversao-cirurgica-lost-race.md)).
