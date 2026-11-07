import asyncio
import fnmatch
import inspect
import json
import logging
import os
import re
import subprocess
import sys
from typing import Any, Callable, Dict, List, Optional, Sequence

import litellm

try:
    from google.adk.agents import LlmAgent  # type: ignore
    from google.adk.models.lite_llm import LiteLlm  # type: ignore
    from google.adk.runners import InMemoryRunner  # type: ignore

    ADK_AVAILABLE = True
except ImportError:
    LlmAgent = None  # type: ignore
    LiteLlm = None  # type: ignore
    InMemoryRunner = None  # type: ignore
    ADK_AVAILABLE = False

_logger = logging.getLogger("agloop.agent")

_STRUCTURED_LOG_FIELDS = ("event", "agent", "model", "tool_calls", "commit_sha", "usage")


class _JsonLogFormatter(logging.Formatter):
    """Renders one JSON object per line, carrying only the AgLoop structured fields present."""

    def format(self, record: logging.LogRecord) -> str:
        payload = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for field in _STRUCTURED_LOG_FIELDS:
            value = getattr(record, field, None)
            if value is not None:
                payload[field] = value
        return json.dumps(payload, ensure_ascii=False)


def configure_json_logging(level: int = logging.INFO) -> None:
    """
    Configures the `agloop` logger tree to emit one JSON object per line on stderr
    (never stdout, so it never corrupts the MCP server's JSON-RPC stdout stream).
    """
    handler = logging.StreamHandler()
    handler.setFormatter(_JsonLogFormatter())
    root = logging.getLogger("agloop")
    root.handlers = [handler]
    root.setLevel(level)
    root.propagate = False


def _accepts_kwarg(fn: Callable, name: str) -> bool:
    """True if `fn` declares `name` or accepts arbitrary `**kwargs`."""
    try:
        sig = inspect.signature(fn)
    except (TypeError, ValueError):
        return True
    return name in sig.parameters or any(
        p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values()
    )


SENSITIVE_PATTERNS = (
    ".env",
    ".env.*",
    "*.pem",
    "*.key",
    "id_rsa*",
    "*credentials*",
    "*secret*",
)

_CPF_RE = re.compile(r"\b\d{3}\.\d{3}\.\d{3}-\d{2}\b")
_SECRET_TOKEN_RE = re.compile(
    r"\b(?:sk-[A-Za-z0-9_-]{16,}|ghp_[A-Za-z0-9]{20,}|AIza[0-9A-Za-z_-]{20,})\b"
)
_EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@([A-Za-z0-9.-]+\.[A-Za-z]{2,})\b")


def sanitize_prompt_pii(text: str) -> str:
    """
    Masks personal/sensitive identifiers before sending context to an LLM API (LGPD-02 / Risco R09):
      * Brazilian CPF numbers (`NNN.NNN.NNN-NN`) -> `[CPF_REDACTED]`
      * Common API tokens (`sk-...`, `ghp_...`, `AIza...`) -> `[SECRET_REDACTED]`
      * All e-mail addresses except synthetic `@agloop.local` identities -> `[EMAIL_REDACTED]`
    """
    if not text:
        return text

    sanitized = _CPF_RE.sub("[CPF_REDACTED]", text)
    sanitized = _SECRET_TOKEN_RE.sub("[SECRET_REDACTED]", sanitized)

    def _mask_email(match: re.Match) -> str:
        domain = match.group(1).lower()
        if domain == "agloop.local":
            return match.group(0)
        return "[EMAIL_REDACTED]"

    return _EMAIL_RE.sub(_mask_email, sanitized)


def _is_within_workspace(repo_root: str, target_path: str) -> bool:
    """Checks strict workspace confinement using `os.path.commonpath` (prevents sibling prefix bypass)."""
    root_real = os.path.realpath(repo_root)
    target_real = os.path.realpath(target_path)
    try:
        return os.path.commonpath([root_real, target_real]) == root_real
    except ValueError:
        return False


def _is_sensitive_path(repo_root: str, target_path: str) -> bool:
    """Returns True if `target_path` matches LGPD-01 / Risco R06 sensitive file patterns."""
    root_real = os.path.realpath(repo_root)
    target_real = os.path.realpath(target_path)
    rel_path = os.path.relpath(target_real, root_real).replace("\\", "/")
    parts = [p for p in rel_path.split("/") if p and p != "."]

    if ".git" in parts:
        return True

    basename = os.path.basename(target_real).lower()
    for pattern in SENSITIVE_PATTERNS:
        if fnmatch.fnmatch(basename, pattern.lower()):
            return True
    return False


def read_file(filepath: str, max_lines: int = 200, repo_root: Optional[str] = None) -> str:
    """
    Safe read-only tool confined to the repository workspace with LGPD-01 / R06 blacklist.
    """
    root_real = os.path.realpath(repo_root or os.getcwd())
    target_real = os.path.realpath(os.path.join(root_real, filepath))

    if not _is_within_workspace(root_real, target_real):
        return "Access denied: path is outside the repository workspace."
    if _is_sensitive_path(root_real, target_real):
        return "Access denied: reading sensitive or credential files is blocked (LGPD-01)."
    if not os.path.isfile(target_real):
        return f"Error: file not found: {filepath}"

    with open(target_real, "r", encoding="utf-8", errors="replace") as f:
        lines = []
        for idx, line in enumerate(f):
            if idx >= max_lines:
                lines.append(f"... [truncated after {max_lines} lines]")
                break
            lines.append(line.rstrip("\n"))
    return sanitize_prompt_pii("\n".join(lines))


def list_dir(dirpath: str = ".", repo_root: Optional[str] = None) -> str:
    """
    Safe directory listing tool confined to the repository workspace (hides sensitive files).
    """
    root_real = os.path.realpath(repo_root or os.getcwd())
    target_real = os.path.realpath(os.path.join(root_real, dirpath))

    if not _is_within_workspace(root_real, target_real):
        return "Access denied: directory is outside the repository workspace."
    if _is_sensitive_path(root_real, target_real):
        return "Access denied: directory is restricted (LGPD-01)."
    if not os.path.isdir(target_real):
        return f"Error: directory not found: {dirpath}"

    entries: List[str] = []
    for entry in sorted(os.listdir(target_real)):
        full = os.path.join(target_real, entry)
        if _is_sensitive_path(root_real, full):
            continue
        suffix = "/" if os.path.isdir(full) else ""
        entries.append(f"{entry}{suffix}")
    return "\n".join(entries)


def git_diff(target: str = "HEAD", max_chars: int = 4000, repo_root: Optional[str] = None) -> str:
    """
    Safe read-only `git diff` inspection tool confined to the repository workspace.
    """
    if target.startswith("-"):
        return "Access denied: invalid git diff target."
    root_real = os.path.realpath(repo_root or os.getcwd())
    try:
        res = subprocess.run(
            ["git", "diff", target],
            cwd=root_real,
            capture_output=True,
            text=True,
            timeout=15,
            check=False,
        )
    except Exception as e:
        return f"Error running git diff: {e}"

    output = (res.stdout or "") + (res.stderr or "")
    if len(output) > max_chars:
        output = output[:max_chars] + f"\n... [truncated at {max_chars} chars]"
    return sanitize_prompt_pii(output.strip())


def run_pytest(target: str = "tests", timeout: int = 30, repo_root: Optional[str] = None) -> str:
    """
    Safe read-only test runner confined to the `tests/` directory.
    """
    if target.startswith("-"):
        return "Access denied: flags are not allowed in target."
    root_real = os.path.realpath(repo_root or os.getcwd())
    tests_root = os.path.realpath(os.path.join(root_real, "tests"))
    target_real = os.path.realpath(os.path.join(root_real, target))

    if not _is_within_workspace(tests_root, target_real):
        return "Access denied: pytest target must be inside the tests/ directory."

    try:
        res = subprocess.run(
            [sys.executable, "-m", "pytest", "-q", target_real],
            cwd=root_real,
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        output = (res.stdout or "") + (res.stderr or "")
        return sanitize_prompt_pii(output.strip())
    except Exception as e:
        return f"Error running pytest: {e}"


DEFAULT_SAFE_TOOLS: Sequence[Callable] = (read_file, list_dir, git_diff, run_pytest)

_TOOL_SCHEMAS: Dict[str, Dict[str, Any]] = {
    "read_file": {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a file inside the repository workspace (sensitive files blocked by LGPD-01).",
            "parameters": {
                "type": "object",
                "properties": {
                    "filepath": {"type": "string", "description": "Relative path to the file inside the repository."},
                    "max_lines": {"type": "integer", "description": "Maximum number of lines to read.", "default": 200},
                },
                "required": ["filepath"],
            },
        },
    },
    "list_dir": {
        "type": "function",
        "function": {
            "name": "list_dir",
            "description": "List files and directories inside the repository workspace.",
            "parameters": {
                "type": "object",
                "properties": {
                    "dirpath": {"type": "string", "description": "Relative directory path.", "default": "."},
                },
            },
        },
    },
    "git_diff": {
        "type": "function",
        "function": {
            "name": "git_diff",
            "description": "Inspect git diff for a commit or ref inside the repository.",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Git ref or commit to diff against.", "default": "HEAD"},
                },
            },
        },
    },
    "run_pytest": {
        "type": "function",
        "function": {
            "name": "run_pytest",
            "description": "Run pytest on the repository test suite (confined to tests/).",
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {"type": "string", "description": "Path inside tests/ to execute.", "default": "tests"},
                },
            },
        },
    },
}


class Agent:
    def __init__(
        self,
        name: str,
        role_prompt: str,
        model: str = "gemini/gemini-1.5-pro-latest",
        tools: Optional[Sequence[Callable]] = None,
        use_adk: bool = True,
        max_tool_rounds: int = 4,
        timeout: Optional[float] = None,
        max_retries: Optional[int] = None,
        fallbacks: Optional[Sequence[str]] = None,
    ):
        self.name = name
        self.role_prompt = role_prompt
        self.model = model
        self.tools: List[Callable] = list(DEFAULT_SAFE_TOOLS if tools is None else tools)
        self._tool_map: Dict[str, Callable] = {getattr(fn, "__name__", str(fn)): fn for fn in self.tools}
        self.max_tool_rounds = max_tool_rounds
        self.use_adk = bool(use_adk and ADK_AVAILABLE)
        self.adk_agent = self._build_adk_agent() if self.use_adk else None

        # Resilience defaults (Issue #11): read at construction time, not import
        # time, so `load_dotenv()` called by the CLI before building the Agent
        # is honored even though `core.agent` is imported earlier in main.py.
        self.timeout = float(timeout if timeout is not None else os.getenv("LLM_TIMEOUT", "60"))
        self.max_retries = int(max_retries if max_retries is not None else os.getenv("LLM_MAX_RETRIES", "3"))
        self.fallbacks: Optional[List[str]] = list(fallbacks) if fallbacks else None

    def _system_instruction(self) -> str:
        return (
            f"You are {self.name}.\n"
            f"{self.role_prompt}\n"
            "You are participating in a War Room debate via Markdown.\n"
            "Below is the current content of the War Room. Add your thoughts or actions.\n"
            "Do not output markdown headers like '## AgentName', just output your response text directly."
        )

    def _build_adk_agent(self):
        """Builds a Google ADK `LlmAgent` backed by `LiteLlm` and safe read-only tools."""
        if not ADK_AVAILABLE or LlmAgent is None or LiteLlm is None:
            return None
        safe_identifier = re.sub(r"\W+", "_", self.name).strip("_") or "agloop_agent"
        return LlmAgent(
            name=safe_identifier,
            model=LiteLlm(model=self.model),
            instruction=self._system_instruction(),
            tools=list(self.tools),
        )

    def _run_adk(self, user_prompt: str) -> str:
        """Executes `self.adk_agent` via Google ADK `InMemoryRunner` and returns the final text."""
        if InMemoryRunner is None or self.adk_agent is None:
            raise RuntimeError("Google ADK InMemoryRunner is not available.")

        runner = InMemoryRunner(agent=self.adk_agent, app_name="agloop")
        if hasattr(runner, "run_text"):
            return str(runner.run_text(user_prompt)).strip()

        async def _consume() -> str:
            session_service = getattr(runner, "session_service", None)
            user_id = "agloop_user"
            slug_name = re.sub(r"\W+", "_", self.name)
            session_id = f"session_{slug_name}"
            if session_service is not None and hasattr(session_service, "create_session"):
                maybe_coro = session_service.create_session(
                    app_name="agloop", user_id=user_id, session_id=session_id
                )
                if inspect.isawaitable(maybe_coro):
                    await maybe_coro

            from google.genai import types  # type: ignore

            new_msg = types.Content(role="user", parts=[types.Part.from_text(text=user_prompt)])
            chunks: List[str] = []
            async for event in runner.run_async(user_id=user_id, session_id=session_id, new_message=new_msg):
                content = getattr(event, "content", None)
                parts = getattr(content, "parts", None) if content else None
                if parts:
                    for part in parts:
                        txt = getattr(part, "text", None)
                        if txt:
                            chunks.append(txt)
            return "\n".join(chunks).strip()

        return asyncio.run(_consume())

    def _litellm_tool_schemas(self) -> List[Dict[str, Any]]:
        schemas: List[Dict[str, Any]] = []
        for fn in self.tools:
            name = getattr(fn, "__name__", "")
            if name in _TOOL_SCHEMAS:
                schemas.append(_TOOL_SCHEMAS[name])
        return schemas

    def _resilience_kwargs(self) -> Dict[str, Any]:
        """Timeout/retry/fallback kwargs for `litellm.completion`, added only if the
        installed `litellm` version (or a test fake) actually accepts them."""
        kwargs: Dict[str, Any] = {}
        if _accepts_kwarg(litellm.completion, "timeout"):
            kwargs["timeout"] = self.timeout
        if _accepts_kwarg(litellm.completion, "num_retries"):
            kwargs["num_retries"] = self.max_retries
        if self.fallbacks and _accepts_kwarg(litellm.completion, "fallbacks"):
            kwargs["fallbacks"] = self.fallbacks
        return kwargs

    def _log_usage(self, response: Any) -> None:
        usage = getattr(response, "usage", None)
        if usage is not None:
            _logger.info(
                "completion usage",
                extra={"event": "llm_usage", "agent": self.name, "model": self.model, "usage": str(usage)},
            )

    def _call_completion(self, messages: List[Dict[str, Any]]):
        schemas = self._litellm_tool_schemas()
        kwargs = self._resilience_kwargs()
        if schemas and _accepts_kwarg(litellm.completion, "tools"):
            kwargs["tools"] = schemas
        response = litellm.completion(model=self.model, messages=messages, **kwargs)
        self._log_usage(response)
        return response

    def _execute_tool_call(self, tool_name: str, raw_args: Any) -> str:
        _logger.info(
            "tool call",
            extra={"event": "tool_call", "agent": self.name, "model": self.model, "tool_calls": tool_name},
        )
        fn = self._tool_map.get(tool_name)
        if fn is None:
            return f"Error: unknown or unauthorized tool '{tool_name}'."
        try:
            if isinstance(raw_args, str):
                kwargs = json.loads(raw_args) if raw_args.strip() else {}
            elif isinstance(raw_args, dict):
                kwargs = raw_args
            else:
                kwargs = {}
            return sanitize_prompt_pii(str(fn(**kwargs)))
        except Exception as e:
            return f"Error executing tool '{tool_name}': {e}"

    def _run_litellm_with_tools(self, messages: List[Dict[str, Any]]) -> str:
        """Invokes `litellm.completion` and resolves any requested tool calls up to `max_tool_rounds`."""
        conversation = list(messages)
        for _ in range(max(1, self.max_tool_rounds)):
            response = self._call_completion(conversation)
            msg = response.choices[0].message
            tool_calls = getattr(msg, "tool_calls", None)
            if not tool_calls:
                return (msg.content or "").strip()

            assistant_entry: Dict[str, Any] = {
                "role": "assistant",
                "content": getattr(msg, "content", None) or "",
                "tool_calls": [],
            }
            for idx, tc in enumerate(tool_calls):
                tc_id = getattr(tc, "id", None) or f"call_{idx}"
                fn_obj = getattr(tc, "function", tc)
                fn_name = getattr(fn_obj, "name", "")
                fn_args = getattr(fn_obj, "arguments", "{}")
                assistant_entry["tool_calls"].append(
                    {
                        "id": tc_id,
                        "type": "function",
                        "function": {"name": fn_name, "arguments": fn_args if isinstance(fn_args, str) else json.dumps(fn_args)},
                    }
                )
            conversation.append(assistant_entry)

            for tc_item in assistant_entry["tool_calls"]:
                fn_name = tc_item["function"]["name"]
                fn_args = tc_item["function"]["arguments"]
                tool_output = self._execute_tool_call(fn_name, fn_args)
                conversation.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc_item["id"],
                        "name": fn_name,
                        "content": tool_output,
                    }
                )

        final_resp = litellm.completion(model=self.model, messages=conversation, **self._resilience_kwargs())
        self._log_usage(final_resp)
        return (final_resp.choices[0].message.content or "").strip()

    def think_and_act(self, war_room_context: str) -> Optional[str]:
        """
        Sanitizes the War Room context (LGPD-02) and invokes the cognitive engine:
          1. Google ADK (`self.adk_agent` via `InMemoryRunner`) when enabled and installed;
          2. Otherwise `litellm.completion` with multi-round safe tool execution (`read_file`,
             `list_dir`, `git_diff`, `run_pytest`).

        Returns `None` on inference failure (timeout, provider outage, etc.) instead of a
        placeholder string — the caller (`core.runner`) must not treat `None` as a real
        message to commit into `war_room.md` (Issue #11: a transient LLM error must not
        become a permanent entry in the governance history).
        """
        sanitized_context = sanitize_prompt_pii(war_room_context)
        user_prompt = f"WAR ROOM CONTEXT:\n{sanitized_context}\n\nWhat is your next message?"

        _logger.info("thinking", extra={"event": "thinking", "agent": self.name, "model": self.model})
        try:
            if self.use_adk and self.adk_agent is not None:
                return self._run_adk(user_prompt)

            messages = [
                {"role": "system", "content": self._system_instruction()},
                {"role": "user", "content": user_prompt},
            ]
            return self._run_litellm_with_tools(messages)
        except Exception as e:
            _logger.error(
                "inference failed",
                extra={"event": "inference_error", "agent": self.name, "model": self.model},
                exc_info=e,
            )
            return None

    def generate_response(self, war_room_context: str) -> Optional[str]:
        """Alias for `think_and_act` (ADR 0005 compatibility)."""
        return self.think_and_act(war_room_context)
