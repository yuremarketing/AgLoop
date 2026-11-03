#!/usr/bin/env python3
"""
Vigia Híbrida do AgLoop (Thin Wrapper DRY sobre `core.runner.watch_war_room`).
Monitora localmente (`mtime` do `war_room.md`) e remotamente (`GitLock.sync_if_needed`).
Suporta `--agent <Nome>` e `--once` (`exit 0` assim que outro agente responde,
acordando a sessão da LLM sem custo de tokens em ociosidade).
"""

import argparse
import os
import sys

# Garante que a raiz do repositório esteja no sys.path quando invocado via `python3 scripts/vigia.py`
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.runner import watch_war_room

ROOM_FILE = "war_room.md"
LOCAL_POLL_INTERVAL = 2.0
REMOTE_POLL_INTERVAL = 30.0


def parse_args(argv=None):
    parser = argparse.ArgumentParser(description="Vigia Híbrida Passiva do AgLoop")
    parser.add_argument(
        "--agent",
        type=str,
        default=os.getenv("AGLOOP_AGENT", "Gemini"),
        help="Nome do agente desta sessão (default: Gemini ou $AGLOOP_AGENT)",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="Encerra com exit 0 assim que o último orador mudar para outro agente",
    )
    parser.add_argument("--room", type=str, default=ROOM_FILE, help="Arquivo da Sala de Guerra")
    parser.add_argument("--local-poll", type=float, default=LOCAL_POLL_INTERVAL, help="Intervalo local (s)")
    parser.add_argument("--remote-poll", type=float, default=REMOTE_POLL_INTERVAL, help="Intervalo remoto (s)")
    return parser.parse_args(argv)


def main(argv=None):
    args = parse_args(argv)
    print("=" * 60)
    print(" [VIGIA AG-LOOP] Modo Vigília Híbrida Ativado (DRY core.runner) ")
    print(f" Agente local       : {args.agent}")
    print(f" Modo de execução   : {'one-shot (--once)' if args.once else 'contínuo'}")
    print(f" Arquivo monitorado : {args.room}")
    print(f" Checagem local     : a cada {args.local_poll}s (mtime)")
    print(f" Checagem remota    : a cada {args.remote_poll}s (git fetch)")
    print("=" * 60, flush=True)

    try:
        watch_war_room(
            war_room_file=args.room,
            agent_name=args.agent,
            local_poll=args.local_poll,
            remote_poll=args.remote_poll,
            once=args.once,
            repo_path=REPO_ROOT,
        )
        sys.exit(0)
    except KeyboardInterrupt:
        print("\n[Vigia] Vigília encerrada pelo usuário.", flush=True)
        sys.exit(0)


if __name__ == "__main__":
    main()

