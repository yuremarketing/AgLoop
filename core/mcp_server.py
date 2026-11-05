"""
AgLoop MCP Server (E04.2 / LGPD-03).

Lightweight MCP (Model Context Protocol) server over JSON-RPC 2.0 on stdio —
no external MCP SDK, reusing the existing `WarRoom`, `GitLock` and the
workspace-confinement primitives from `core.agent` (DRY, same safety model
already enforced for `read_file`/`list_dir`).

Exposes 3 tools, all confined to the War Room files only (never an arbitrary
path inside the repository — LGPD-03):
  * `read_war_room`         — read the recent transcript, PII-sanitized.
  * `post_war_room_message` — append a message to `war_room.md` (commit+push via GitLock).
  * `get_lock_status`       — inspect GitLock / War Room state.
"""

import json
import os
import sys
from typing import Any, Dict, Optional

from core.agent import _is_sensitive_path, _is_within_workspace, sanitize_prompt_pii
from core.git_lock import GitLock
from core.scan import run_scan
from core.war_room import WarRoom

MCP_PROTOCOL_VERSION = "2024-11-05"
SERVER_NAME = "agloop"
SERVER_VERSION = "0.5.0"

# Only these two files are ever reachable through the MCP tools — fixed by basename,
# so an attacker-supplied directory prefix (e.g. "../outside/war_room.md") is simply
# discarded rather than followed (LGPD-03: workspace sandboxing).
ALLOWED_WAR_ROOM_FILES = {"war_room.md", "HISTORICO.md"}


def _resolve_allowed_file(repo_root: str, filepath: str) -> str:
    """Resolves `filepath` to an absolute path inside `repo_root`, enforcing the allowlist."""
    basename = os.path.basename(filepath)
    if basename not in ALLOWED_WAR_ROOM_FILES:
        raise ValueError(
            f"Access denied: '{filepath}' is not a War Room file (allowed: {sorted(ALLOWED_WAR_ROOM_FILES)})."
        )
    target = os.path.join(repo_root, basename)
    if not _is_within_workspace(repo_root, target):
        raise ValueError("Access denied: path is outside the repository workspace.")
    if _is_sensitive_path(repo_root, target):
        raise ValueError("Access denied: sensitive path blocked.")
    return target


def read_war_room(max_turns: int = 6, filepath: str = "war_room.md", repo_root: Optional[str] = None) -> str:
    """Reads the recent War Room transcript (sliding window), PII-sanitized."""
    root = os.path.realpath(repo_root or os.getcwd())
    target = _resolve_allowed_file(root, filepath)
    war_room = WarRoom(filepath=target)
    return sanitize_prompt_pii(war_room.read_recent(max_turns=max_turns))


def post_war_room_message(
    agent_name: str, message: str, push: bool = True, repo_root: Optional[str] = None
) -> Dict[str, Any]:
    """Appends `message` to `war_room.md` as `agent_name`; commits+pushes via `GitLock` when `push`."""
    root = os.path.realpath(repo_root or os.getcwd())
    target = _resolve_allowed_file(root, "war_room.md")
    war_room = WarRoom(filepath=target)

    if not push:
        war_room.append_message(agent_name, message)
        return {"pushed": False, "status": "ok"}

    git_lock = GitLock(repo_path=root)
    ok = git_lock.acquire_lock_and_push(
        action_callback=lambda: war_room.append_message(agent_name, message),
        message=f"AgLoop: {agent_name} update in war_room.md (via MCP)",
        paths=war_room.paths,
        author_name=agent_name,
    )
    return {"pushed": ok, "status": git_lock.last_status}


def get_lock_status(filepath: str = "war_room.md", repo_root: Optional[str] = None) -> Dict[str, Any]:
    """Inspects the local lock and the War Room state for `filepath`."""
    root = os.path.realpath(repo_root or os.getcwd())
    target = _resolve_allowed_file(root, filepath)

    git_lock = GitLock(repo_path=root)
    lock_dir_real = os.path.realpath(git_lock.lock_dir)
    if not _is_within_workspace(root, lock_dir_real):
        raise ValueError("Access denied: lock directory is outside the repository workspace.")

    locked = os.path.isdir(git_lock.lock_dir)
    stale = locked and git_lock._lock_is_stale()
    war_room = WarRoom(filepath=target)
    return {
        "locked": locked,
        "stale": stale,
        "last_speaker": war_room.get_last_speaker(),
        "state": war_room.get_state(),
        "paths": war_room.paths,
    }


def scan_repository(repo_root: Optional[str] = None) -> str:
    """Read-only structure + stack scan of the repository, confined to the workspace (E07.3)."""
    root = os.path.realpath(repo_root or os.getcwd())
    return run_scan(repo_root=root)


TOOLS = [
    {
        "name": "read_war_room",
        "description": "Read the recent War Room transcript (war_room.md or HISTORICO.md), PII-sanitized.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "max_turns": {"type": "integer", "default": 6},
                "filepath": {"type": "string", "default": "war_room.md"},
            },
        },
    },
    {
        "name": "post_war_room_message",
        "description": "Append a message to war_room.md as agent_name, committing and pushing via GitLock.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "agent_name": {"type": "string"},
                "message": {"type": "string"},
                "push": {"type": "boolean", "default": True},
            },
            "required": ["agent_name", "message"],
        },
    },
    {
        "name": "get_lock_status",
        "description": "Inspect the War Room's GitLock state and last speaker.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "filepath": {"type": "string", "default": "war_room.md"},
            },
        },
    },
    {
        "name": "scan_repository",
        "description": "Read-only scan of the repository: directory structure (bounded) and known stack manifests.",
        "inputSchema": {"type": "object", "properties": {}},
    },
]

_TOOL_FUNCS = {
    "read_war_room": read_war_room,
    "post_war_room_message": post_war_room_message,
    "get_lock_status": get_lock_status,
    "scan_repository": scan_repository,
}


def _dispatch(method: str, params: Dict[str, Any]) -> Any:
    if method == "initialize":
        return {
            "protocolVersion": MCP_PROTOCOL_VERSION,
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
            "capabilities": {"tools": {}},
        }
    if method == "notifications/initialized":
        return None
    if method == "tools/list":
        return {"tools": TOOLS}
    if method == "tools/call":
        name = params.get("name")
        arguments = params.get("arguments") or {}
        fn = _TOOL_FUNCS.get(name)
        if fn is None:
            raise ValueError(f"Unknown tool: {name}")
        try:
            result = fn(**arguments)
        except TypeError as e:
            raise ValueError(f"Invalid arguments for '{name}': {e}")
        text = result if isinstance(result, str) else json.dumps(result, ensure_ascii=False)
        return {"content": [{"type": "text", "text": text}], "isError": False}
    raise ValueError(f"Unknown method: {method}")


def _handle_line(line: str) -> Optional[Dict[str, Any]]:
    """Parses one JSON-RPC 2.0 request/notification and returns the reply (or None for notifications)."""
    try:
        request = json.loads(line)
    except json.JSONDecodeError as e:
        return {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {e}"}}

    req_id = request.get("id")
    method = request.get("method", "")
    params = request.get("params") or {}
    is_notification = "id" not in request

    try:
        result = _dispatch(method, params)
    except ValueError as e:
        return None if is_notification else {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32602, "message": str(e)}}
    except Exception as e:
        return None if is_notification else {
            "jsonrpc": "2.0", "id": req_id, "error": {"code": -32603, "message": f"Internal error: {e}"}
        }

    if is_notification:
        return None
    return {"jsonrpc": "2.0", "id": req_id, "result": result}


def main():
    """Reads JSON-RPC requests from stdin (one per line) and writes replies to stdout."""
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        response = _handle_line(line)
        if response is not None:
            sys.stdout.write(json.dumps(response, ensure_ascii=False) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
