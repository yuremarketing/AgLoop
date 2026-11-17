#!/usr/bin/env bash
# ==============================================================================
# AgLoop — Sala de Acompanhamento ao Vivo (tmux)
# Issue #66: Visibilidade em tempo real do debate entre agentes sem consumir tokens.
# Tema: Amigável (fundo roxo, detalhes e texto em laranja) — Requisito do PO
# Governança: Posse explícita (--claim), liberação automática e bloqueio por padrão.
# ==============================================================================

set -euo pipefail

SESSION="agloop-live"
REPO_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OWNER_FILE="$REPO_ROOT/.agloop/tmux-session.owner.json"

usage() {
    cat <<EOF
Uso: $(basename "$0") [OPÇÕES]

Gerencia a sessão tmux de acompanhamento ao vivo da Sala de Guerra do AgLoop.
Por padrão, exige posse deliberada (--claim) para evitar ativações acidentais.

Opções:
  -c, --claim <NOME>  Registra a posse formal da sessão pelo responsável e a inicia
  -a, --attach        Conecta-se à sessão ativa (exige posse ativa prévia)
  -r, --release       Libera a posse e encerra a sessão ativa
  -k, --kill          Encerra a sessão tmux '$SESSION' e remove o registro de posse
  -s, --status        Exibe o resumo da sala, posse e heartbeat (sem abrir tmux)
  -h, --help          Exibe esta mensagem de ajuda

Atalhos dentro do tmux:
  Ctrl+b, d           Desanexa da sessão mantendo o monitoramento em background
  Ctrl+b, setas       Navega entre os 3 painéis

Alternativa sem tmux:
  watch -n 2 'tail -n 40 war_room.md'
EOF
}

get_owner() {
    if [ -f "$OWNER_FILE" ]; then
        python3 -c '
import json, sys
try:
    with open(sys.argv[1], encoding="utf-8") as f:
        data = json.load(f)
    print(data.get("owner", ""))
except Exception:
    pass
' "$OWNER_FILE" 2>/dev/null || true
    fi
}

set_owner() {
    local owner_name="$1"
    mkdir -p "$REPO_ROOT/.agloop"
    python3 -c '
import json, sys
from datetime import datetime, timezone
owner = sys.argv[1]
filepath = sys.argv[2]
data = {
    "owner": owner,
    "since": datetime.now(timezone.utc).isoformat()
}
with open(filepath, "w", encoding="utf-8") as f:
    json.dump(data, f, indent=2)
' "$owner_name" "$OWNER_FILE"
}

clear_owner() {
    rm -f "$OWNER_FILE"
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
    owner_path = os.path.join(".agloop", "tmux-session.owner.json")
    owner_info = None
    if os.path.exists(owner_path):
        try:
            with open(owner_path, encoding="utf-8") as f:
                owner_info = json.load(f)
        except Exception:
            pass

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

    print(f"{BOLD}Responsabilidade da Sessão:{RESET}")
    if owner_info and owner_info.get("owner"):
        ow = owner_info.get("owner")
        sc = owner_info.get("since", "")
        age_sc = ""
        if sc:
            try:
                dt_sc = datetime.fromisoformat(sc)
                age_sc = f" (desde {dt_sc.hour:02d}:{dt_sc.minute:02d}:{dt_sc.second:02d} UTC)"
            except Exception:
                age_sc = f" (desde {sc})"
        print(f"  • Dono Atual   : {ORANGE}{BOLD}{ow}{RESET}{age_sc}\n")
    else:
        print(f"  • Dono Atual   : {DIM}Nenhum (sessão desocupada){RESET}\n")

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
    print(f"Encerrar e liberar posse:")
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

CLAIM_OWNER=""
ATTACH_ONLY=false

# Parser de argumentos
while [[ $# -gt 0 ]]; do
    case "$1" in
        -c|--claim)
            if [ -z "${2:-}" ] || [[ "${2:-}" == -* ]]; then
                echo "Erro: --claim exige o nome do responsável. Exemplo: $0 --claim \"Yure Mark\"" >&2
                exit 1
            fi
            CLAIM_OWNER="$2"
            shift 2
            ;;
        -a|--attach)
            ATTACH_ONLY=true
            shift
            ;;
        -k|--kill|-r|--release)
            if command -v tmux &>/dev/null && tmux has-session -t "$SESSION" 2>/dev/null; then
                tmux kill-session -t "$SESSION"
            fi
            clear_owner
            echo "Sessão tmux '$SESSION' encerrada e posse liberada com sucesso."
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

# Validação do binário tmux
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

# Registra a posse se solicitado
if [ -n "$CLAIM_OWNER" ]; then
    set_owner "$CLAIM_OWNER"
    echo "Posse da sessão '$SESSION' registrada para: $CLAIM_OWNER"
fi

CURRENT_OWNER="$(get_owner)"

# Bloqueio por padrão: Sem posse registrada, recusa iniciar ou anexar
if [ -z "$CURRENT_OWNER" ]; then
    echo "Bloqueio: Nenhuma posse ativa registrada para a sessão de acompanhamento." >&2
    echo "Por padrão, o AgLoop não inicia sessões sem um responsável explicitamente declarado." >&2
    echo "" >&2
    echo "Para assumir a responsabilidade e iniciar a sessão no seu dia:" >&2
    echo "  $0 --claim \"Seu Nome\"" >&2
    echo "" >&2
    echo "Para apenas consultar o status sem criar a sessão:" >&2
    echo "  $0 --status" >&2
    exit 1
fi

# Se a sessão tmux já existe
if tmux has-session -t "$SESSION" 2>/dev/null; then
    echo "Sessão '$SESSION' já está em execução (Responsável: $CURRENT_OWNER)."
    if [ "$ATTACH_ONLY" = true ] || [ -n "$CLAIM_OWNER" ]; then
        exec tmux attach-session -t "$SESSION"
    else
        echo "Para conectar-se à sessão:"
        echo "  $0 --attach"
        echo "Ou:"
        echo "  tmux attach-session -t $SESSION"
        exit 0
    fi
fi

# Se foi solicitado apenas attach mas a sessão não existe
if [ "$ATTACH_ONLY" = true ] && [ -z "$CLAIM_OWNER" ]; then
    echo "Sessão '$SESSION' não está em execução." >&2
    echo "Para iniciar com posse ativa:" >&2
    echo "  $0 --claim \"$CURRENT_OWNER\"" >&2
    exit 1
fi

# Cria nova sessão desacoplada (detached) e captura o ID do painel principal
MAIN_PANE=$(tmux new-session -d -s "$SESSION" -n "AgLoopLive" -c "$REPO_ROOT" -P -F "#{pane_id}")

# Tema Visual Amigável: Fundo Roxo (colour55) + Letras/Destaques em Laranja (colour208)
tmux set-option -t "$SESSION" status on
tmux set-option -t "$SESSION" status-interval 2
tmux set-option -t "$SESSION" status-style "bg=colour55,fg=colour208,bold"
tmux set-option -t "$SESSION" status-left-length 50
tmux set-option -t "$SESSION" status-left "#[bg=colour208,fg=colour55,bold] AgLoop Live #[default]#[fg=colour208] [Resp: $CURRENT_OWNER] "
tmux set-option -t "$SESSION" status-right-length 50
tmux set-option -t "$SESSION" status-right "#[fg=colour208,bold] %H:%M:%S #[default]"
tmux set-option -t "$SESSION" pane-border-style "fg=colour55"
tmux set-option -t "$SESSION" pane-active-border-style "fg=colour208,bold"
tmux set-option -t "$SESSION" window-status-current-style "bg=colour55,fg=colour208,bold"
tmux set-option -t "$SESSION" message-style "bg=colour55,fg=colour208,bold"

# Divisão dos 3 painéis usando IDs únicos (compatível com qualquer base-index):
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
echo "Responsável registrado: $CURRENT_OWNER"
echo "Layout: 3 painéis (Debate, Histórico de Turnos e Observabilidade)."
echo "Tema: Fundo Roxo e Letras em Laranja."
echo ""
echo "Para conectar à sessão:"
echo "  $0 --attach"
echo "Ou:"
echo "  tmux attach-session -t $SESSION"
echo ""
echo "Para encerrar e liberar posse:"
echo "  $0 --kill"

if [ -n "$CLAIM_OWNER" ]; then
    # Se invocado em terminal interativo com --claim, orienta conexão
    echo ""
    echo "Dica: Execute '$0 --attach' para visualizar imediatamente."
fi
