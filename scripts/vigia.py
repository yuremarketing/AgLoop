#!/usr/bin/env python3
"""
Vigia Híbrida do AgLoop.
Monitora localmente (mtime do war_room.md) e remotamente (git fetch).
Notifica instantaneamente quando o Claude ou outro agente atualiza o debate.
"""

import os
import re
import subprocess
import time
import sys

ROOM_FILE = "war_room.md"
LOCAL_POLL_INTERVAL = 2.0
REMOTE_POLL_INTERVAL = 30.0

def get_last_speaker():
    if not os.path.exists(ROOM_FILE):
        return None
    try:
        with open(ROOM_FILE, "r", encoding="utf-8") as f:
            content = f.read()
        matches = re.findall(r"^##\s+(.+)$", content, flags=re.MULTILINE)
        return matches[-1].strip() if matches else None
    except Exception as e:
        return f"Error: {e}"

def check_remote_ahead():
    try:
        subprocess.run(["git", "fetch", "--quiet", "origin", "main"], timeout=15, check=False)
        local_head = subprocess.check_output(["git", "rev-parse", "HEAD"], text=True).strip()
        remote_head = subprocess.check_output(["git", "rev-parse", "origin/main"], text=True).strip()
        return local_head != remote_head
    except Exception:
        return False

def main():
    print("=" * 60)
    print(" [VIGIA AG-LOOP] Modo Vigília Híbrida Ativado ")
    print(f" Arquivo monitorado : {ROOM_FILE}")
    print(f" Checagem local     : a cada {LOCAL_POLL_INTERVAL}s (mtime)")
    print(f" Checagem remota    : a cada {REMOTE_POLL_INTERVAL}s (git fetch)")
    print("=" * 60, flush=True)

    last_mtime = os.path.getmtime(ROOM_FILE) if os.path.exists(ROOM_FILE) else 0.0
    last_speaker = get_last_speaker()
    print(f"[Vigia] Status inicial -> Último orador no War Room: '{last_speaker}'", flush=True)

    next_remote_check = time.time() + REMOTE_POLL_INTERVAL

    while True:
        try:
            time.sleep(LOCAL_POLL_INTERVAL)

            # 1. Checagem local via mtime (custo zero)
            current_mtime = os.path.getmtime(ROOM_FILE) if os.path.exists(ROOM_FILE) else 0.0
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                current_speaker = get_last_speaker()
                print(f"\n[VIGIA ALERTA] Modificação local detectada em {ROOM_FILE}!", flush=True)
                print(f"[Vigia] Novo orador: '{current_speaker}'", flush=True)
                if current_speaker != "Gemini":
                    print(f"[Vigia] >>> ATENÇÃO: {current_speaker} respondeu! Vez do Gemini responder.", flush=True)
                else:
                    print(f"[Vigia] Gemini falou por último. Aguardando réplica de outro agente...", flush=True)

            # 2. Checagem remota periódica
            if time.time() >= next_remote_check:
                next_remote_check = time.time() + REMOTE_POLL_INTERVAL
                if check_remote_ahead():
                    print("\n[VIGIA ALERTA] Novos commits detectados no repositório remoto (origin/main)!", flush=True)
                    try:
                        subprocess.run(["git", "pull", "--rebase", "--quiet"], timeout=20, check=False)
                        last_mtime = os.path.getmtime(ROOM_FILE) if os.path.exists(ROOM_FILE) else 0.0
                        speaker = get_last_speaker()
                        print(f"[Vigia] Pull concluído. Último orador: '{speaker}'", flush=True)
                    except Exception as e:
                        print(f"[Vigia] Erro ao sincronizar com remote: {e}", flush=True)

        except KeyboardInterrupt:
            print("\n[Vigia] Vigília encerrada pelo usuário.", flush=True)
            sys.exit(0)
        except Exception as err:
            print(f"[Vigia] Erro inesperado no ciclo: {err}", flush=True)
            time.sleep(5)

if __name__ == "__main__":
    main()
