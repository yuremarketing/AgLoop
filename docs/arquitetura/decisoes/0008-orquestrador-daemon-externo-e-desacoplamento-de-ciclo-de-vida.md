# ADR 0008: Orquestrador Supervisor Externo no Host e Desacoplamento do Ciclo de Vida das LLMs

- **Status:** Aceita
- **Data:** 2026-11-17 (Turno 47 / Issue [#74](https://github.com/yuremarketing/AgLoop/issues/74))
- **Decisores:** Yure Mark (PO), Claude, Gemini

---

## Contexto e Problema

O protocolo original da Vigília Híbrida (ADR-0003) adotou o modo *one-shot* (`--once`) para permitir que os harnesses de terminal das LLMs (Claude Code e Antigravity) acordassem a sessão quando o subprocesso em background terminasse com `exit 0`.

Contudo, essa abordagem introduziu um **antipadrão arquitetural crítico**: **o ciclo de vida do próprio processo supervisor foi delegado para a janela de contexto efêmera e o prompt estocástico da LLM** (*stateless model as infrastructure watchdog*).

### Modos de Falha Reais (Silent Freezes)
1. **Interação com Humano:** Se o usuário envia uma mensagem ou tira uma dúvida pontual, o modelo responde em linguagem natural sem acionar a tool call de vigília. O processo morre e o loop congela em silêncio.
2. **Timeout de Inferência / Cota de API:** Se a conexão falha ou a API atinge teto de tokens, a chamada de sistema não é disparada.
3. **Estagnação Desapercebida:** Sem um processo sentinela independente no host, a sala dependia de cada agente invocar ativamente `--stall-minutes`. Se ninguém rearmar a vigília, o alarme de travamento nunca dispara.

Modelos cognitivos são efêmeros, probabilísticos e stateless; eles nunca devem ser o watchdog da sua própria infraestrutura.

---

## Decisão

Adotar uma arquitetura de **Supervisor Contínuo no Host (`AgLoop Host Daemon`)**, desacoplando a observabilidade e o monitoramento de processos da inferência das LLMs:

1. **Camada Fina e Reúso Estrito (DRY / ADR-0004):**
   - O daemon (`core/daemon.py`, `scripts/agloop_daemon.py`, `agloop daemon`) atua como uma camada fina sobre `core.runner.watch_war_room()`.
   - O loop supervisor roda contínuo no host (`while True`) chamando `watch_war_room(once=True)`. Ao detectar uma mudança de turno, ele registra o evento e **se rearma automaticamente no host**, sem depender de nenhuma ação, tool call ou lembrança do prompt das LLMs.

2. **Alarme de Travamento Sempre Ativo por Padrão:**
   - O daemon opera com `stall_minutes = 15.0` por padrão.
   - Ao detectar `STALL_SENTINEL` (inatividade prolongada), dispara alarme sonoro determinístico (`core.banner.play_formal_auth_alert()`), registra no log e notifica a transição para `WAITING_HUMAN`.

3. **Gerenciamento de Processo e Observabilidade:**
   - Controle via PID file `.agloop/agloop_daemon.pid` com detecção de processo zumbi via `GitLock._pid_alive()`.
   - Comandos de controle determinísticos: `agloop daemon start`, `agloop daemon stop`, `agloop daemon status`, `agloop daemon run`.

---

## Limites Explícitos do Escopo (O que o Daemon Resolve e o que NÃO Resolve)

Para clareza técnica e alinhamento de expectativas:

- **O que o Daemon Resolve de Fato:**
  1. A vigília nunca mais morre quando uma LLM fala com um humano, toma timeout ou alucina — o host mantém o monitoramento vivo e se rearma sozinho.
  2. A detecção de travamento é mandatória e contínua por padrão, alertando quando a sala parar.
  3. A sessão de acompanhamento ao vivo (`scripts/acompanhar_sala.sh`) pode se apoiar em um supervisor resiliente.

- **O que o Daemon NÃO Resolve:**
  1. O daemon **não** tem como injetar mensagens diretamente dentro de uma sessão interativa de chat aberta de um agente (essa API não existe nas ferramentas de CLI).
  2. O ciclo final continua necessitando de uma entidade consciente (um humano ou o agente acordado pelo evento do harness) para reagir e produzir a resposta técnica. A intervenção humana continua necessária ao soar o alarme.

---

## Riscos Conhecidos

- **Concorrência com Branch de Feature (Issue #52):**
  Se o daemon rodar no mesmo diretório compartilhado dos agentes, um `git fetch` em segundo plano pode esbarrar em branches de feature sem upstream remoto ainda criado. Mitigação: o daemon respeita as proteções existentes de `GitLock` e mantém retentativas com backoff sem interromper o serviço.

---

## Consequências

### Positivas
- Eliminação do ponto único de falha estocástico da vigília híbrida.
- A Sala de Guerra não congela mais silenciosamente caso uma LLM responda uma dúvida humana ou sofra timeout.
- Alarmes de estagnação passam a ser garantia de infraestrutura, não opcional de prompt.
