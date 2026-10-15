import os
import random
import time
from typing import Optional

from core.git_lock import GitLock
from core.war_room import WarRoom


def _mtime(path: str) -> float:
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


def run_agent_loop(
    agent,
    war_room_file: str = "war_room.md",
    sleep_time: Optional[float] = None,
    local_poll: float = 3.0,
    remote_poll: float = 30.0,
    jitter: float = 2.0,
    max_backoff: float = 60.0,
):
    """
    Hybrid Watcher (Vigília Híbrida). The LLM is only invoked when something changed:
      * local_poll  -> os.path.getmtime() on the War Room (free, catches same-disk agents)
      * remote_poll -> git fetch + "is origin ahead of me?" (network, catches other machines)
    Idle iterations cost zero tokens and never parse the Markdown.

    `sleep_time` is kept for backward compatibility and maps to `local_poll`.
    """
    if sleep_time is not None:
        local_poll = float(sleep_time)

    git_lock = GitLock(repo_path=".")
    war_room = WarRoom(filepath=war_room_file)
    room_paths = [war_room_file]

    print(f"Starting AgLoop for Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"War Room File: {war_room_file}")
    print(f"Hybrid Watcher: local every ~{local_poll}s, remote every ~{remote_poll}s"
          f"{'' if git_lock.origin else ' (no origin: local-only)'}")

    # mtime observed at the END of our critical section (inside the lock). Reading it
    # after releasing the lock could swallow a write made by another local agent.
    observed = {"mtime": None}

    def agent_action_callback():
        try:
            context = war_room.read_all()
            last_speaker = war_room.get_last_speaker()

            # If I am the last speaker, I should wait for others.
            if last_speaker == agent.name:
                print(f"[{agent.name}] I was the last speaker. Waiting for others...")
                return

            # It's my turn (or no one has spoken)
            print(f"[{agent.name}] My turn to speak!")
            response = agent.think_and_act(context)
            war_room.append_message(agent.name, response)
            print(f"[{agent.name}] Appended response to War Room.")
        finally:
            observed["mtime"] = _mtime(war_room_file)

    def nap(seconds: float):
        time.sleep(seconds + random.uniform(0, jitter))

    last_mod_time: Optional[float] = None  # None forces a first check on startup
    next_remote_check = 0.0
    pending_retry = False
    failures = 0

    while True:
        try:
            # ---- 1. Cheap trigger checks (no tokens, no Markdown parsing) ----
            reason = None
            current_mod_time = _mtime(war_room_file)
            if pending_retry:
                reason = "retry"
            elif current_mod_time != last_mod_time:
                reason = "local change"
            elif git_lock.origin and time.monotonic() >= next_remote_check:
                next_remote_check = time.monotonic() + remote_poll
                if git_lock.has_remote_updates():
                    reason = "remote update"

            if reason is None:
                nap(local_poll)
                continue

            # ---- 2. Something happened: take the lock and let the agent act ----
            print(f"\n--- Loop Iteration for {agent.name} ({reason}) ---")
            observed["mtime"] = None
            success = git_lock.acquire_lock_and_push(
                action_callback=agent_action_callback,
                message=f"AgLoop: {agent.name} update in {war_room_file}",
                paths=room_paths,
            )

            if success:
                pending_retry = False
                failures = 0
                last_mod_time = observed["mtime"] if observed["mtime"] is not None else _mtime(war_room_file)
                nap(local_poll)
                continue

            # ---- 3. Failure: keep the trigger armed (no lost wake-ups) ----
            pending_retry = True
            status = git_lock.last_status
            if status == "locked":
                # Another local agent holds the lock: not an error, just wait a bit.
                print(f"[{agent.name}] Local lock busy, another agent is acting. Retrying soon.")
                nap(local_poll)
                continue
            if status == "lost_race":
                # Someone pushed first: re-read immediately with fresh context.
                print(f"[{agent.name}] Lost the race to another agent. Re-reading the War Room.")
                failures = 0
                nap(1.0)
                continue

            failures += 1
            backoff = min(2 ** failures, max_backoff) + random.uniform(1, 5)
            print(f"[{agent.name}] Sync failed ({status}). Backing off {backoff:.1f}s.")
            time.sleep(backoff)

        except KeyboardInterrupt:
            print("\nExiting AgLoop.")
            break
        except Exception as e:
            pending_retry = True
            failures += 1
            backoff = min(2 ** failures, max_backoff) + random.uniform(1, 5)
            print(f"Unexpected error in loop: {e}. Backing off {backoff:.1f}s.")
            time.sleep(backoff)
