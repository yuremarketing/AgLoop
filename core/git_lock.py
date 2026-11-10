import json
import logging
import os
import random
import shutil
import socket
import sys
import time
import warnings
from typing import Iterable, Optional

from git import Repo
from git.exc import GitCommandError

_logger = logging.getLogger("agloop.git_lock")

# Markers git prints when a push is rejected because the remote moved ahead
# (i.e. another agent won the race). Anything else (network, auth...) is
# treated as a transient failure and the local commit is kept for later.
_REJECTION_MARKERS = ("rejected", "non-fast-forward", "fetch first", "failed to push some refs")


class GitLock:
    """
    Hybrid lock for AgLoop.

    - Local agents (same disk / same working tree) are serialized by an atomic
      directory lock (`.agloop.lock/`), with stale-lock recovery.
    - Remote agents (other machines) are synchronized through Git, used as a
      serverless message broker (fetch / rebase / push).

    Safety rules (the working tree may be shared with other agents writing code):
      * Only the War Room paths are ever staged / committed.
      * Never `reset --hard`: other agents' uncommitted work must survive.
      * Never pull unless the remote actually has new commits.
    """

    def __init__(self, repo_path: str = ".", lock_timeout: Optional[float] = None, push_retries: int = 3):
        self.repo_path = repo_path
        self.repo = Repo(repo_path)
        try:
            self.origin = self.repo.remotes.origin
        except (IndexError, AttributeError):
            self.origin = None

        if os.getenv("AGENT_LOOP_LOCAL_MODE") is not None:
            warnings.warn(
                "AGENT_LOOP_LOCAL_MODE is deprecated and ignored: AgLoop now always runs in "
                "hybrid mode (local mtime + remote git fetch). You can remove it from .env.",
                FutureWarning,
                stacklevel=2,
            )

        self.lock_dir = os.path.join(repo_path, ".agloop.lock")
        self.lock_timeout = float(lock_timeout if lock_timeout is not None else os.getenv("AGLOOP_LOCK_TIMEOUT", 300))
        self.push_retries = push_retries
        # Status of the last acquire_lock_and_push() call, for the runner's logs:
        # ok | locked | sync_failed | commit_failed | push_failed | lost_race
        self.last_status = "ok"
        self._warned = set()

    # ------------------------------------------------------------------ #
    # Local lock (atomic mkdir) with stale-lock recovery
    # ------------------------------------------------------------------ #
    def _owner_file(self, lock_dir: Optional[str] = None) -> str:
        return os.path.join(lock_dir or self.lock_dir, "owner.json")

    def _read_owner(self, lock_dir: Optional[str] = None) -> Optional[dict]:
        try:
            with open(self._owner_file(lock_dir), "r", encoding="utf-8") as f:
                return json.load(f)
        except (OSError, ValueError):
            return None

    @staticmethod
    def _pid_alive(pid: int) -> bool:
        if sys.platform == "win32":
            # os.kill(pid, 0) is NOT a no-op liveness check on Windows: CPython's
            # implementation opens the process with full access and calls
            # TerminateProcess(handle, 0), i.e. it would actually kill the lock
            # owner instead of just probing it. Use a read-only WinAPI query instead.
            import ctypes

            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            ERROR_ACCESS_DENIED = 5
            STILL_ACTIVE = 259

            handle = ctypes.windll.kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
            if not handle:
                return ctypes.GetLastError() == ERROR_ACCESS_DENIED  # exists, owned by another user
            try:
                code = ctypes.c_ulong()
                ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
                return code.value == STILL_ACTIVE
            finally:
                ctypes.windll.kernel32.CloseHandle(handle)

        try:
            os.kill(pid, 0)
        except ProcessLookupError:
            return False
        except PermissionError:
            return True  # exists, owned by another user
        return True

    def _lock_is_stale(self) -> bool:
        owner = self._read_owner()
        if owner is None:
            # Owner file not written yet (or corrupted): fall back to the dir age,
            # so a process that died right after mkdir doesn't block forever.
            try:
                age = time.time() - os.path.getmtime(self.lock_dir)
            except OSError:
                return False  # lock vanished meanwhile
            return age > self.lock_timeout

        if time.time() - float(owner.get("ts", 0)) > self.lock_timeout:
            return True
        if owner.get("host") == socket.gethostname():
            pid = owner.get("pid")
            if isinstance(pid, int) and not self._pid_alive(pid):
                return True
        return False

    def _break_stale_lock(self):
        # Rename first (atomic) so concurrent breakers don't delete each other's
        # fresh locks with rmtree; then clean up the renamed directory.
        tomb = f"{self.lock_dir}.stale.{os.getpid()}.{random.randint(0, 1_000_000)}"
        try:
            os.rename(self.lock_dir, tomb)
        except OSError:
            return
        shutil.rmtree(tomb, ignore_errors=True)
        _logger.warning("stale local lock recovered", extra={"event": "stale_lock_recovered"})

    def _acquire_local_lock(self) -> bool:
        """Uses atomic directory creation as a local lock."""
        for _ in range(2):
            try:
                os.mkdir(self.lock_dir)
            except FileExistsError:
                if self._lock_is_stale():
                    self._break_stale_lock()
                    continue
                return False
            owner = {"pid": os.getpid(), "host": socket.gethostname(), "ts": time.time()}
            with open(self._owner_file(), "w", encoding="utf-8") as f:
                json.dump(owner, f)
            return True
        return False

    def _release_local_lock(self):
        """Releases the local lock, but only if we still own it."""
        owner = self._read_owner()
        if owner is not None and (owner.get("pid") != os.getpid() or owner.get("host") != socket.gethostname()):
            return  # our lock was considered stale and taken over; don't delete theirs
        shutil.rmtree(self.lock_dir, ignore_errors=True)

    # ------------------------------------------------------------------ #
    # Git helpers
    # ------------------------------------------------------------------ #
    def _warn_once(self, key: str, msg: str):
        if key not in self._warned:
            self._warned.add(key)
            _logger.warning(msg, extra={"event": f"git_{key}_warning"})

    def _branch(self) -> str:
        try:
            return self.repo.active_branch.name
        except (TypeError, ValueError):
            return "main"

    def _remote_ref(self) -> str:
        return f"origin/{self._branch()}"

    def _rev_count(self, range_spec: str) -> int:
        try:
            return int(self.repo.git.rev_list("--count", range_spec).strip() or 0)
        except (GitCommandError, ValueError):
            return 0

    def _commits_ahead(self) -> int:
        if not self.origin:
            return 0
        try:
            self.repo.git.rev_parse("--verify", "--quiet", self._remote_ref())
        except GitCommandError:
            # Branch doesn't exist on the remote yet: everything local is unpushed.
            return self._rev_count("HEAD")
        return self._rev_count(f"{self._remote_ref()}..HEAD")

    def _fetch(self) -> bool:
        if not self.origin:
            return False
        try:
            self.repo.git.fetch("--quiet", "origin", self._branch())
            self._warned.discard("fetch")
            return True
        except GitCommandError as e:
            # Ref-lock collision with another local fetch, or no network: just skip.
            self._warn_once("fetch", f"[AgLoop] git fetch failed (will keep trying silently): {e.stderr.strip() if e.stderr else e}")
            return False

    def has_remote_updates(self) -> bool:
        """
        Cheap remote check: fetch + count commits that exist on origin but not locally.
        Being *ahead* of origin (unpushed commits) does NOT count as an update.
        """
        if not self.origin:
            return False
        if not self._fetch():
            return False
        return self._rev_count(f"HEAD..{self._remote_ref()}") > 0

    def _rebase_onto_remote(self) -> bool:
        """Rebase local commits onto origin/<branch>, stashing others' dirty files around it."""
        try:
            self.repo.git.rebase("--autostash", self._remote_ref())
            return True
        except GitCommandError as e:
            _logger.warning(
                "rebase onto remote failed: %s",
                e.stderr.strip() if e.stderr else e,
                extra={"event": "rebase_failed"},
            )
            try:
                self.repo.git.rebase("--abort")
            except GitCommandError:
                pass
            return False

    def _path_in_tree(self, rev: str, path: str) -> bool:
        try:
            self.repo.git.cat_file("-e", f"{rev}:{path}")
            return True
        except GitCommandError:
            return False

    def _resolve_lost_race(self, paths: Iterable[str]) -> bool:
        """
        Another agent pushed a War Room update first. Drop OUR unpushed room changes
        (they were based on stale context), fast-forward to the remote and let the
        agent re-read and decide again. Only `paths` are reverted; everything else in
        the working tree (other agents' code) is preserved.
        """
        remote = self._remote_ref()
        try:
            base = self.repo.git.merge_base("HEAD", remote).strip()
            self.repo.git.reset("--soft", base)
            for p in paths:
                if self._path_in_tree(base, p):
                    self.repo.git.checkout(base, "--", p)
                else:
                    self.repo.git.rm("--cached", "--quiet", "--ignore-unmatch", "--", p)
                    if os.path.exists(os.path.join(self.repo_path, p)):
                        os.remove(os.path.join(self.repo_path, p))
        except GitCommandError as e:
            _logger.error("could not drop local room changes: %s", e, extra={"event": "lost_race_recovery_failed"})
            return False
        return self._rebase_onto_remote()

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #
    def sync_if_needed(self, paths: Iterable[str] = ()) -> bool:
        """
        Pull remote updates ONLY if they exist. In a shared working tree with no remote
        news, this never touches the disk (fixes 'cannot pull with rebase: You have
        unstaged changes').
        """
        if not self.origin:
            return True
        if not self.has_remote_updates():
            return True  # nothing new, or fetch failed (push will tell us later)
        if self._rebase_onto_remote():
            return True
        # Rebase conflicted: our pending room commit collides with a remote message.
        return self._resolve_lost_race(paths)

    def pull(self) -> bool:
        """Backward-compatible alias: syncs with the remote only when needed."""
        return self.sync_if_needed()

    def _existing_paths(self, paths: Iterable[str]) -> list:
        result = []
        for p in paths:
            full = os.path.join(self.repo_path, p) if not os.path.isabs(p) else p
            if os.path.exists(full) or self._path_in_tree("HEAD", p):
                result.append(p)
        return result

    def has_changes(self, paths: Iterable[str]) -> bool:
        """Checks if any of `paths` is modified, staged or untracked."""
        active = self._existing_paths(paths)
        if not active:
            return False
        return bool(self.repo.git.status("--porcelain", "--", *active).strip())

    def has_uncommitted_changes(self) -> bool:
        """Checks if there are any modified or untracked files (whole working tree)."""
        return self.repo.is_dirty(untracked_files=True)

    @staticmethod
    def _author_env(author_name: Optional[str], author_email: Optional[str]) -> dict:
        if not author_name:
            return {}
        slug = author_name.strip().lower().replace(" ", ".")
        email = author_email or f"{slug}@agloop.local"
        return {
            "GIT_AUTHOR_NAME": author_name,
            "GIT_AUTHOR_EMAIL": email,
            "GIT_COMMITTER_NAME": author_name,
            "GIT_COMMITTER_EMAIL": email,
        }

    def commit(
        self,
        message: str,
        paths: Iterable[str],
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> bool:
        """
        Stages and commits ONLY `paths`. `git commit -- <paths>` also ignores anything
        another agent may have staged in the shared index.
        When `author_name` is provided, sets `GIT_AUTHOR_*` and `GIT_COMMITTER_*`
        scoped strictly to the git commit subprocess (never mutates global os.environ).
        """
        active = self._existing_paths(paths)
        if not active:
            return True
        try:
            self.repo.git.add("--", *active)
            if not self.has_changes(active):
                return True
            env = self._author_env(author_name, author_email)
            with self.repo.git.custom_environment(**env):
                self.repo.git.commit("-m", message, "--", *active)
            return True
        except GitCommandError as e:
            _logger.error("git commit error: %s", e, extra={"event": "commit_failed"})
            return False

    def push(self, paths: Iterable[str] = ()) -> bool:
        """
        Pushes local commits. On rejection (another agent pushed first):
          - clean rebase (remote changed other files) -> retry push;
          - conflicting rebase (remote has a new room message) -> lost race:
            drop our room changes and fast-forward. Never touches other files.
        On network/auth errors the commit is kept and pushed on a later iteration.
        """
        if not self.origin:
            return True
        paths = list(paths)
        branch = self._branch()
        for attempt in range(1, self.push_retries + 1):
            try:
                self.repo.git.push("origin", branch)
                return True
            except GitCommandError as e:
                err = (e.stderr or str(e)).lower()
                if not any(m in err for m in _REJECTION_MARKERS):
                    _logger.warning(
                        "push failed (kept locally, will retry): %s",
                        e.stderr.strip() if e.stderr else e,
                        extra={"event": "push_failed"},
                    )
                    self.last_status = "push_failed"
                    return False
                _logger.info(
                    "push rejected, another agent pushed first (attempt %d/%d)",
                    attempt,
                    self.push_retries,
                    extra={"event": "push_rejected"},
                )
                if not self._fetch():
                    self.last_status = "push_failed"
                    return False
                if not self._rebase_onto_remote():
                    self._resolve_lost_race(paths)
                    self.last_status = "lost_race"
                    return False
                # Issue #15: wider jitter range to spread out collisions as the number
                # of concurrent writers (N > 2 War Room participants) grows.
                time.sleep(random.uniform(0.5, 2.0) * attempt)
        self.last_status = "push_failed"
        return False

    def acquire_lock_and_push(
        self,
        action_callback,
        message: str,
        paths: Iterable[str],
        author_name: Optional[str] = None,
        author_email: Optional[str] = None,
    ) -> bool:
        """
        1. acquire local lock (always)
        2. refuse if the working tree isn't on `main` (Issue #30: the working
           directory can be shared with a feature branch mid-implementation;
           committing War Room paths there would only reach `main` later, as
           a side effect of that branch's own PR merge, instead of landing
           directly as its own commit)
        3. sync with remote only if it has news
        4. action_callback() modifies the War Room
        5. commit only `paths` (with optional isolated per-agent Git author/committer)
        6. push any unpushed commit (including leftovers from earlier failures)
        7. release local lock
        Check `self.last_status` for the reason of a False return
        (`locked | wrong_branch | sync_failed | commit_failed | push_failed | lost_race`).
        """
        paths = list(paths)
        if not self._acquire_local_lock():
            self.last_status = "locked"
            return False

        try:
            if self._branch() != "main":
                self.last_status = "wrong_branch"
                return False

            if not self.sync_if_needed(paths):
                self.last_status = "sync_failed"
                return False

            action_callback()

            if self.has_changes(paths) and not self.commit(
                message, paths, author_name=author_name, author_email=author_email
            ):
                self.last_status = "commit_failed"
                return False

            if self._commits_ahead() > 0 and not self.push(paths):
                return False  # push() sets last_status

            self.last_status = "ok"
            return True
        finally:
            self._release_local_lock()
