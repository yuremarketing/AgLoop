#!/usr/bin/env bash
# ==============================================================================
# AgLoop — Sala de Acompanhamento ao Vivo (tmux)
# Issue #66: Visibilidade em tempo real do debate entre agentes sem consumir tokens.
# Tema: Amigável (fundo roxo, detalhes e texto em laranja) — Requisito PO
# ==============================================================================

set -euo pipefail

SESSION="agloop-live"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPÇÕES]

Inicia uma sessão tmux de acompanhamento ao vivo da Sala de Guerra do AgLoop.

Opções:
  -a, --attach        Conecta-se imediatamente à sessão tmux
  -k, --kill          Encerra a sessão tmux '$SESSION'
  -s, --status        Exibe o resumo da sala e heartbeat (sem abrir tmux)
  -h, --help          Exibe esta mensagem de ajuda

Atalhos dentro do tmux:
  Ctrl+b, d           Desanexa da sessão mantendo o monitoramento em background
  Ctrl+b, setas       Navega entre os 3 painéis

Alternativa sem tmux:
  watch -n 2 'tail -n 40 war_room.md'
EOF
}

run_monitor_loop() {
    cd "$REPO_ROOT"
    python3 -c '
import os, sys, time, json, re
from datetime import datetime, timezone

ORANGE = "\033[38;5;208m"
PURPLE = "\033[38;5;55m"
BOLD = "\033[1m"
DIM = "\033[2m"
RESET = "\033[0m"

def render_once():
    war_room_path = "war_room.md"
    last_speaker = "Nenhum"
    next_agent = "Não definido"
    last_status = "Desconhecido"
    
    if os.path.exists(war_room_path):
        try:
            with open(war_room_path, encoding="utf-8", errors="ignore") as f:
                lines = f.readlines()
            for line in reversed(lines):
                line_s = line.strip()
                if line_s.startswith("PRÓXIMO-AGENTE:") and next_agent == "Não definido":
                    next_agent = line_s.split(":", 1)[1].strip()
                elif line_s.startswith("STATUS:") and last_status == "Desconhecido":
                    last_status = line_s.split(":", 1)[1].strip()
                elif line_s.startswith("## ") and not line_s.startswith("## Turno") and last_speaker == "Nenhum":
                    last_speaker = line_s[3:].strip()
                if last_speaker != "Nenhum" and next_agent != "Não definido" and last_status != "Desconhecido":
                    break
        except Exception as e:
            last_status = f"Erro ao ler: {e}"

    hb_path = os.path.join(".agloop", "vigia.heartbeat.json")
    hb_info = None
    if os.path.exists(hb_path):
        try:
            with open(hb_path, encoding="utf-8") as f:
                hb_info = json.load(f)
        except Exception:
            pass

    print(f"{ORANGE}{BOLD}========================================{RESET}")
    print(f"{ORANGE}{BOLD}   AGLOOP — OBSERVABILIDADE AO VIVO     {RESET}")
    print(f"{ORANGE}{BOLD}========================================{RESET}\n")

    print(f"{BOLD}Sala de Guerra (war_room.md):{RESET}")
    print(f"  • Último Orador : {ORANGE}{BOLD}{last_speaker}{RESET}")
    print(f"  • Próximo Agente: {ORANGE}{BOLD}{next_agent}{RESET}")
    print(f"  • Status Atual  : {BOLD}{last_status}{RESET}\n")

    print(f"{BOLD}Vigília Híbrida (.agloop/heartbeat):{RESET}")
    if hb_info:
        st = hb_info.get("state", "desconhecido")
        ag = hb_info.get("agent", "?")
        rs = hb_info.get("reason", "—")
        up = hb_info.get("updated_at", "")
        age_str = "?"
        if up:
            try:
                dt = datetime.fromisoformat(up)
                age_s = (datetime.now(timezone.utc) - dt).total_seconds()
                age_str = f"{age_s:.0f}s atrás"
            except Exception:
                age_str = up
        color_st = "\033[32m" if st == "running" else "\033[33m"
        print(f"  • Agente em Vigília: {BOLD}{ag}{RESET}")
        print(f"  • Estado           : {color_st}{BOLD}{st}{RESET}")
        print(f"  • Motivo           : {rs}")
        print(f"  • Atualização      : {age_str}")
    else:
        print(f"  {DIM}• Nenhum processo de vigília ativo no momento{RESET}")

    print(f"\n{ORANGE}{BOLD}----------------------------------------{RESET}")
    print(f"Atalhos tmux:")
    print(f"  • {BOLD}Ctrl+b, d{RESET}  : Desanexar (continua rodando)")
    print(f"  • {BOLD}Ctrl+b, setas{RESET} : Mudar de painel")
    print(f"Encerrar:")
    print(f"  • {BOLD}./scripts/acompanhar_sala.sh --kill{RESET}")
    print(f"{ORANGE}{BOLD}----------------------------------------{RESET}")

mode = sys.argv[1] if len(sys.argv) > 1 else "loop"
if mode == "once":
    render_once()
else:
    while True:
        os.system("clear")
        render_once()
        time.sleep(2)
' "$@"
}

ATTACH_AFTER=false

# Parser de argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        -a|--attach)
            ATTACH_AFTER=true
            shift
            ;;
        -k|--kill)
            if command -v tmux &>/dev/null && tmux has-session -t "$SESSION" 2>/dev/null; then
                tmux kill-session -t "$SESSION"
                echo "Sessão tmux '$SESSION' encerrada."
            else
                echo "Nenhuma sessão '$SESSION' ativa."
            fi
            exit 0
            ;;
        -s|--status)
            run_monitor_loop "once"
            exit 0
            ;;
        --monitor-loop)
            run_monitor_loop "loop"
            exit 0
            ;;
        -h|--help)
            usage
            exit 0
            ;;
        *)
            echo "Opção desconhecida: $1" >&2
            usage
            exit 1
            ;;
    esac
done

# Validação do tmux
if ! command -v tmux &>/dev/null; then
    echo "Erro: tmux não encontrado no sistema." >&2
    echo "Instale o tmux para usar a sala com 3 painéis:" >&2
    echo "  sudo apt install tmux   (Debian/Ubuntu)" >&2
    echo "  brew install tmux       (macOS)" >&2
    echo "" >&2
    echo "Alternativa leve sem tmux:" >&2
    echo "  watch -n 2 'tail -n 40 war_room.md'" >&2
    exit 1
fi

cd "$REPO_ROOT"

# Se já existe sessão ativa
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Sessão '$SESSION' já está em execução."
    if [ "$ATTACH_AFTER" = true ]; then
        exec tmux attach-session -t "$SESSION"
    else
        echo "Para conectar-se à sessão:"
        echo "  tmux attach-session -t $SESSION"
        echo "Ou execute:"
        echo "  $0 --attach"
        exit 0
    fi
fi

# Cria nova sessão desacoplada (detached) e captura o ID do painel principal
MAIN_PANE=$(tmux new-session -d -s "$SESSION" -n "AgLoopLive" -c "$REPO_ROOT" -P -F "#{pane_id}")

# Tema Visual Amigável: Fundo Roxo (colour55) + Letras/Destaques em Laranja (colour208)
tmux set-option -t "$SESSION" status on
tmux set-option -t "$SESSION" status-interval 2
tmux set-option -t "$SESSION" status-style "bg=colour55,fg=colour208,bold"
tmux set-option -t "$SESSION" status-left-length 40
tmux set-option -t "$SESSION" status-left "#[bg=colour208,fg=colour55,bold] AgLoop Live #[default] "
tmux set-option -t "$SESSION" status-right-length 50
tmux set-option -t "$SESSION" status-right "#[fg=colour208,bold] %H:%M:%S #[default]"
tmux set-option -t "$SESSION" pane-border-style "fg=colour55"
tmux set-option -t "$SESSION" pane-active-border-style "fg=colour208,bold"
tmux set-option -t "$SESSION" window-status-current-style "bg=colour55,fg=colour208,bold"
tmux set-option -t "$SESSION" message-style "bg=colour55,fg=colour208,bold"

# Divisão dos 3 painéis usando IDs únicos (compatível com base-index 0 ou 1):
# 1. Divide verticalmente (esquerda 62%, direita 38%)
RIGHT_PANE=$(tmux split-window -h -p 38 -t "$MAIN_PANE" -c "$REPO_ROOT" -P -F "#{pane_id}")

# 2. Divide a coluna da esquerda horizontalmente (topo 70%, rodapé 30%)
LOG_PANE=$(tmux split-window -v -p 30 -t "$MAIN_PANE" -c "$REPO_ROOT" -P -F "#{pane_id}")

# Envia comandos para cada painel:
# Painel Principal (Esquerda / Topo): Streaming do debate na Sala de Guerra
tmux send-keys -t "$MAIN_PANE" "tail -f -n 50 war_room.md" C-m

# Painel de Ritmo (Esquerda / Rodapé): Histórico recente de commits dos turnos
tmux send-keys -t "$LOG_PANE" "watch -n 5 'git log -n 10 --oneline war_room.md'" C-m

# Painel de Observabilidade (Direita): Status da sala e heartbeat em tempo real
tmux send-keys -t "$RIGHT_PANE" "\"$REPO_ROOT/scripts/acompanhar_sala.sh\" --monitor-loop" C-m

# Foca no painel principal
tmux select-pane -t "$MAIN_PANE"

echo "Sessão tmux '$SESSION' iniciada com sucesso!"
echo "Layout com 3 painéis (Debate, Histórico de Turnos e Observabilidade)."
echo "Tema: Fundo Roxo e Letras em Laranja."
echo ""
echo "Para conectar à sessão:"
echo "  tmux attach-session -t $SESSION"
echo "Ou:"
echo "  $0 --attach"
echo ""
echo "Para encerrar a sessão:"
echo "  $0 --kill"

if [ "$ATTACH_AFTER" = true ]; then
    exec tmux attach-session -t "$SESSION"
fi
