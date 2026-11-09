#!/usr/bin/env python3
"""
SessionStart hook (Claude Code plugin). Prints a one-line status of the War
Room, if any. Never fails the session: any error is swallowed and the hook
always exits 0 (Claude Directory validator requirement).
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)


def main():
    from core.war_room import WarRoom

    if not os.path.isfile("war_room.md"):
        print(
            "AgLoop: novo repositorio detectado. Execute 'agloop init' para "
            "criar a governanca ou 'agloop scan' para inspecionar o projeto."
        )
        return

    wr = WarRoom()
    print(f"[AgLoop] war_room.md state={wr.get_state()} last_speaker={wr.get_last_speaker()}")


if __name__ == "__main__":
    try:
        main()
    except Exception:
        pass
    sys.exit(0)
