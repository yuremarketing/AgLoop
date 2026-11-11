import logging
import os
import random
import time
from typing import Optional

from core.git_lock import GitLock
from core.war_room import WarRoom

_logger = logging.getLogger("agloop.runner")


def _mtime(path: str) -> float:
    return os.path.getmtime(path) if os.path.exists(path) else 0.0


STALL_SENTINEL = "<AGLOOP_STALL>"


def _is_stalled(started_at: float, stall_minutes: Optional[float], now: Optional[float] = None) -> bool:
    """
    Pure, time-injectable check (Issue #44): True once `stall_minutes` have elapsed
    since `started_at` without any War Room activity. Disabled (`False`) whenever
    `stall_minutes` is `None` or `<= 0`, preserving the pre-#44 default behavior.
    """
    if not stall_minutes or stall_minutes <= 0:
        return False
    current = time.monotonic() if now is None else now
    return (current - started_at) >= (stall_minutes * 60.0)


def run_agent_loop(
    agent,
    war_room_file: str = "war_room.md",
    sleep_time: Optional[float] = None,
    local_poll: float = 3.0,
    remote_poll: float = 30.0,
    jitter: float = 2.0,
    max_backoff: float = 60.0,
    max_context_turns: int = 6,
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
    room_paths = war_room.paths

    _logger.info(
        "starting agloop",
        extra={
            "event": "loop_start",
            "agent": agent.name,
            "model": agent.model,
        },
    )
    print(f"Starting AgLoop for Agent: {agent.name}")
    print(f"Model: {agent.model}")
    print(f"War Room File: {war_room_file}")
    print(f"Hybrid Watcher: local every ~{local_poll}s, remote every ~{remote_poll}s"
          f"{'' if git_lock.origin else ' (no origin: local-only)'}")

    # mtime observed at the END of our critical section (inside the lock). Reading it
    # after releasing the lock could swallow a write made by another local agent.
    observed = {"mtime": None}
    # Set inside agent_action_callback when think_and_act() returns None (Issue #11):
    # the outer loop must retry without having committed/pushed anything.
    inference_failed = {"flag": False}
    # Set inside agent_action_callback only when a real message was appended, so the
    # outer loop's "turn_appended" log line isn't emitted for paused/no-op cycles.
    turn_outcome = {"spoke": False}

    def agent_action_callback():
        inference_failed["flag"] = False
        turn_outcome["spoke"] = False
        try:
            state = war_room.get_state()
            if state in ("WAITING_HUMAN", "CONSENSUS"):
                print(f"[{agent.name}] War Room state is {state}. Pausing inference until human/new turn.")
                return

            last_speaker = war_room.get_last_speaker()
            next_agent = war_room.get_next_agent()

            # Issue #15: with an explicit `PRÓXIMO-AGENTE:` field (N > 2 participants),
            # only the addressed agent acts; everyone else stays an Observer. Falls back
            # to the legacy last-speaker check when the field is absent (2-agent rooms,
            # or older turns archived before this field existed).
            if next_agent is not None:
                if next_agent.strip().lower() != agent.name.strip().lower():
                    print(f"[{agent.name}] PRÓXIMO-AGENTE is '{next_agent}'. Observing in silence...")
                    return
            elif last_speaker == agent.name:
                print(f"[{agent.name}] I was the last speaker. Waiting for others...")
                return

            # It's my turn (or no one has spoken)
            print(f"[{agent.name}] My turn to speak!")
            context = war_room.read_recent(max_turns=max_context_turns)
            response = agent.think_and_act(context)
            if response is None:
                _logger.warning(
                    "inference failed, skipping turn without writing to the War Room",
                    extra={"event": "turn_failed", "agent": agent.name, "model": agent.model},
                )
                inference_failed["flag"] = True
                return
            war_room.append_message(agent.name, response)
            turn_outcome["spoke"] = True
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
                author_name=agent.name,
            )

            if success:
                last_mod_time = observed["mtime"] if observed["mtime"] is not None else _mtime(war_room_file)

                if inference_failed["flag"]:
                    # Nothing was written/committed: back off like any other transient
                    # failure and let the next iteration retry think_and_act cleanly.
                    pending_retry = True
                    failures += 1
                    backoff = min(2 ** failures, max_backoff) + random.uniform(1, 5)
                    print(f"[{agent.name}] Inference failed. Retrying in {backoff:.1f}s.")
                    time.sleep(backoff)
                    continue

                pending_retry = False
                failures = 0
                if turn_outcome["spoke"]:
                    try:
                        commit_sha = git_lock.repo.head.commit.hexsha[:10]
                    except Exception:
                        commit_sha = None
                    _logger.info(
                        "turn cycle complete",
                        extra={
                            "event": "turn_appended",
                            "agent": agent.name,
                            "model": agent.model,
                            "commit_sha": commit_sha,
                        },
                    )
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
            if status == "wrong_branch":
                # Issue #30: the working tree is on a feature branch, not main.
                # Not a transient failure — an agent needs to check it out manually.
                print(f"[{agent.name}] Active branch is '{git_lock._branch()}' (must be 'main'). War Room commits blocked.")
                nap(local_poll)
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


def watch_war_room(
    war_room_file: str = "war_room.md",
    agent_name: str = "Gemini",
    local_poll: float = 2.0,
    remote_poll: float = 30.0,
    once: bool = False,
    repo_path: str = ".",
    jitter: float = 2.0,
    max_backoff: float = 60.0,
    stall_minutes: Optional[float] = None,
) -> Optional[str]:
    """
    Passive Hybrid Watcher (SSOT shared with `scripts/vigia.py`).
    Monitors `war_room_file` locally (`mtime`, zero cost) and remotely (`GitLock.sync_if_needed`).
    When `once=True`, returns the new speaker's name as soon as the War Room changes and
    the last speaker is not `agent_name` (allowing a background CLI task to exit 0 and wake the agent).

    `stall_minutes` (Issue #44, `once=True` only): if no activity is observed within this
    many minutes, writes a `WAITING_HUMAN` alert to the War Room (skipped if the room is
    already `WAITING_HUMAN`/`CONSENSUS`, and harmless if another watcher wins the race) and
    returns `STALL_SENTINEL` — so a silent room still exits the background task and notifies
    whoever is waiting on it. `None`/`<= 0` (the default) disables this and preserves the
    pre-#44 behavior exactly.

    Any exception outside the `GitCommandError` cases already handled inside `GitLock`
    (e.g. transient disk I/O, a file briefly missing mid-write) is caught per-iteration and
    retried with exponential backoff, so the watcher never dies silently (Risco R04).
    """
    git_lock = GitLock(repo_path=repo_path)
    room_path = os.path.join(repo_path, war_room_file) if not os.path.isabs(war_room_file) else war_room_file
    war_room = WarRoom(filepath=room_path)

    last_mtime = _mtime(room_path)
    last_speaker = war_room.get_last_speaker()
    print(
        f"[Vigia] Monitorando '{war_room_file}' (Agente: {agent_name}, modo: {'once' if once else 'contínuo'}, "
        f"último orador: '{last_speaker}')",
        flush=True,
    )

    next_remote_check = time.monotonic() + remote_poll
    started_at = time.monotonic()
    failures = 0

    while True:
        try:
            time.sleep(local_poll)

            changed = False
            current_mtime = _mtime(room_path)
            if current_mtime != last_mtime:
                last_mtime = current_mtime
                changed = True
                started_at = time.monotonic()
                print(f"\n[VIGIA ALERTA] Modificação local detectada em {war_room_file}!", flush=True)
            elif git_lock.origin and time.monotonic() >= next_remote_check:
                next_remote_check = time.monotonic() + remote_poll
                if git_lock.has_remote_updates():
                    print("\n[VIGIA ALERTA] Novos commits detectados em origin!", flush=True)
                    if git_lock.sync_if_needed(war_room.paths):
                        last_mtime = _mtime(room_path)
                        changed = True
                        started_at = time.monotonic()

            if changed:
                speaker = war_room.get_last_speaker()
                next_agent = war_room.get_next_agent()
                print(f"[Vigia] Novo orador: '{speaker}'", flush=True)
                # Issue #15: honor explicit PRÓXIMO-AGENTE addressing when present,
                # so Observers in N > 2 rooms don't wake up for turns that aren't theirs.
                if next_agent is not None:
                    addressed = next_agent.strip().lower() == agent_name.strip().lower()
                else:
                    addressed = bool(speaker) and speaker != agent_name
                if addressed:
                    print(f"[Vigia] >>> ATENÇÃO: {speaker} respondeu! Vez de {agent_name}.", flush=True)
                    if once:
                        return speaker
                else:
                    print(f"[Vigia] Não é a vez de {agent_name}. Aguardando...", flush=True)
            elif once and _is_stalled(started_at, stall_minutes):
                print(
                    f"\n[VIGIA ALERTA] Travamento: sem atividade em {war_room_file} "
                    f"nos últimos {stall_minutes:g} minuto(s).",
                    flush=True,
                )
                if war_room.get_state() not in ("WAITING_HUMAN", "CONSENSUS"):
                    alert = (
                        "**Alerta automático de travamento (vigília)**\n\n"
                        f"Nenhuma resposta em `{war_room_file}` nos últimos {stall_minutes:g} minuto(s). "
                        "PRÓXIMO-AGENTE pode ter ficado sem vigília religada.\n\n"
                        "<!-- AGLOOP_STATE: WAITING_HUMAN -->"
                    )
                    git_lock.acquire_lock_and_push(
                        action_callback=lambda: war_room.append_message(agent_name, alert),
                        message=f"AgLoop: {agent_name} stall alert in {war_room_file}",
                        paths=war_room.paths,
                        author_name=agent_name,
                    )
                return STALL_SENTINEL

            failures = 0
        except Exception as e:
            failures += 1
            backoff = min(2 ** failures, max_backoff) + random.uniform(0, jitter)
            print(f"[Vigia] Erro inesperado no laço de monitoramento: {e}. Tentando novamente em {backoff:.1f}s.", flush=True)
            time.sleep(backoff)

