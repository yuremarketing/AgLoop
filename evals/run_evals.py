"""
AgLoop Evals (Issue #13).

Runs the real `Agent` (no `litellm.completion` mock) against fixed War Room
fixtures and checks:
  * deterministic  -- the expected tool is actually called (never `run_pytest`).
  * probabilistic  -- an LLM-judge checks the reply doesn't violate the War
                       Room protocol (no `## AgentName` header, no unjustified
                       `STATUS: CONSENSUS`).

Costs real API tokens and credits unless `--dry-run` is passed, in which case
`litellm.completion` is swapped for fixed fakes (same style as `tests/`), so
the harness itself can be iterated on for free. Never wired into `pytest`,
`main.py` or the PR+CI gate on purpose (Turno 11 ACORDO) -- run explicitly:

    python evals/run_evals.py [--dry-run] [--case all|deterministic|probabilistic]
"""

import argparse
import logging
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import List, Optional

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import litellm  # noqa: E402  (after sys.path fixup)

from core.agent import Agent  # noqa: E402

FIXTURES_DIR = Path(__file__).resolve().parent / "fixtures"
DEFAULT_AGENT_MODEL = os.getenv("EVAL_AGENT_MODEL", "gemini/gemini-1.5-pro-latest")
DEFAULT_JUDGE_MODEL = os.getenv("EVAL_JUDGE_MODEL", "gemini/gemini-1.5-flash")


class EvalResult:
    def __init__(self, name: str, passed: bool, detail: str = ""):
        self.name = name
        self.passed = passed
        self.detail = detail


class _ToolCallRecorder(logging.Handler):
    """Captures `agloop.agent`'s `tool_call` log events (added in Issue #11) —
    reuses the structured logging instead of adding a parallel introspection API."""

    def __init__(self):
        super().__init__(level=logging.INFO)
        self.tool_calls: List[str] = []

    def emit(self, record: logging.LogRecord) -> None:
        if getattr(record, "event", None) == "tool_call":
            self.tool_calls.append(getattr(record, "tool_calls", "?"))


def _tool_call_response(name: str, arguments: str):
    tc = SimpleNamespace(id="call_1", function=SimpleNamespace(name=name, arguments=arguments))
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="", tool_calls=[tc]))])


def _final_response(text: str):
    return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content=text, tool_calls=None))])


def _install_sequence_fake(responses: List) -> None:
    """Replaces `litellm.completion` with a fake that returns `responses` in
    order (one per call). Caller is responsible for restoring the original."""
    queue = list(responses)

    def fake(*_args, **_kwargs):
        if not queue:
            raise RuntimeError("dry-run fake exhausted: more litellm.completion calls than expected")
        return queue.pop(0)

    litellm.completion = fake


def run_deterministic_case(model: str, dry_run: bool) -> EvalResult:
    original_completion = litellm.completion
    if dry_run:
        _install_sequence_fake(
            [
                _tool_call_response("read_file", '{"filepath": "evals/fixtures/sample_notes.txt"}'),
                _final_response("The note warns that agent replies must never emit a '## AgentName' line."),
            ]
        )

    recorder = _ToolCallRecorder()
    agent_logger = logging.getLogger("agloop.agent")
    previous_level = agent_logger.level
    agent_logger.setLevel(logging.INFO)
    agent_logger.addHandler(recorder)
    try:
        agent = Agent(name="EvalAgent", role_prompt="You are a careful Dev Especialista.", model=model, use_adk=False)
        context = (FIXTURES_DIR / "war_room_deterministic.md").read_text(encoding="utf-8")
        response = agent.think_and_act(context)
    finally:
        agent_logger.removeHandler(recorder)
        agent_logger.setLevel(previous_level)
        litellm.completion = original_completion

    if response is None:
        return EvalResult("deterministic_tool_call", False, "agent inference failed (see logs)")

    passed = "read_file" in recorder.tool_calls and "run_pytest" not in recorder.tool_calls
    return EvalResult("deterministic_tool_call", passed, f"tool_calls={recorder.tool_calls}")


def _judge(reply: str, judge_model: str, dry_run: bool) -> str:
    if dry_run:
        violates = "\n## " in f"\n{reply}" or "STATUS: CONSENSUS" in reply
        return "FAIL" if violates else "PASS"

    prompt = (
        "You are a strict protocol linter for the AgLoop War Room. "
        "Answer with exactly one word: PASS or FAIL.\n"
        "FAIL if the message contains a line starting with '## ' (a speaker "
        "header, which would break turn-parsing) OR declares "
        "'STATUS: CONSENSUS' without a visible justification in the same message.\n\n"
        f"MESSAGE:\n{reply}"
    )
    result = litellm.completion(
        model=judge_model,
        messages=[{"role": "user", "content": prompt}],
        timeout=30,
    )
    verdict = (result.choices[0].message.content or "").strip().upper()
    return "PASS" if verdict.startswith("PASS") else "FAIL"


def run_probabilistic_case(model: str, judge_model: str, dry_run: bool) -> EvalResult:
    original_completion = litellm.completion
    if dry_run:
        _install_sequence_fake([_final_response("I agree with the plan, the risk looks well mitigated.")])

    try:
        agent = Agent(name="EvalAgent", role_prompt="You are a careful Sala de Guerra participant.", model=model, use_adk=False)
        context = (FIXTURES_DIR / "war_room_probabilistic.md").read_text(encoding="utf-8")
        response = agent.think_and_act(context)
    finally:
        litellm.completion = original_completion

    if response is None:
        return EvalResult("probabilistic_protocol_check", False, "agent inference failed (see logs)")

    verdict = _judge(response, judge_model, dry_run)
    return EvalResult("probabilistic_protocol_check", verdict == "PASS", f"judge verdict: {verdict}")


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dry-run", action="store_true", help="Use fixed fakes instead of real API calls (zero cost).")
    parser.add_argument("--case", choices=["all", "deterministic", "probabilistic"], default="all")
    parser.add_argument("--model", default=DEFAULT_AGENT_MODEL, help="Model for the agent under test.")
    parser.add_argument("--judge-model", default=DEFAULT_JUDGE_MODEL, help="Model used as the LLM-judge.")
    args = parser.parse_args(argv)

    if not args.dry_run:
        print(
            f"WARNING: running against the real API (agent={args.model}, judge={args.judge_model}). "
            "This consumes real tokens/credits.",
            file=sys.stderr,
        )

    results: List[EvalResult] = []
    if args.case in ("deterministic", "all"):
        results.append(run_deterministic_case(args.model, args.dry_run))
    if args.case in ("probabilistic", "all"):
        results.append(run_probabilistic_case(args.model, args.judge_model, args.dry_run))

    for r in results:
        print(f"[{'PASS' if r.passed else 'FAIL'}] {r.name}: {r.detail}")

    return 0 if all(r.passed for r in results) else 1


if __name__ == "__main__":
    sys.exit(main())
