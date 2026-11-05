import argparse
import sys

from dotenv import load_dotenv
from core.agent import Agent
from core.init_scaffold import run_init
from core.privacy_audit import run_privacy_audit
from core.runner import run_agent_loop
from core.scan import run_scan

# Load environment variables
load_dotenv()

# Define roles for our agents
ROLES = {
    "Alice": "You are a senior software architect. You focus on structure, scalability, and robust design. You like to propose high-level ideas.",
    "Bob": "You are a pragmatic developer. You focus on implementation details, edge cases, and code simplicity. You like to challenge complex architectures."
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run or audit an AgLoop agent")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an AgLoop agent loop (default).")
    run_parser.add_argument("--name", type=str, required=True, help="Name of the agent (e.g., Alice or Bob)")
    run_parser.add_argument("--model", type=str, default="gemini/gemini-1.5-pro-latest", help="LLM model to use")
    run_parser.add_argument("--sleep", type=int, default=10, help="Seconds to sleep between loop iterations")
    run_parser.add_argument("--room", type=str, default="war_room.md", help="The markdown file for IPC")

    audit_parser = subparsers.add_parser("audit", help="Run local diagnostics (no LLM calls).")
    audit_parser.add_argument("--privacy", action="store_true", help="Run the LGPD-04 privacy diagnostic report.")

    subparsers.add_parser("init", help="Scaffold a clean war_room.md and governance templates in this repo.")

    subparsers.add_parser("scan", help="Read-only scan of the repository structure and known stack manifests.")

    return parser


def parse_cli_args(argv=None):
    """
    Parses `run`/`audit` subcommands, defaulting to `run` for backward compatibility:
    `python3 main.py --name Alice` keeps working exactly like before E04 added subcommands.
    """
    argv = sys.argv[1:] if argv is None else list(argv)
    if not argv or argv[0].startswith("-"):
        argv = ["run", *argv]
    return _build_parser().parse_args(argv)


def main():
    args = parse_cli_args()

    if args.command == "audit":
        if args.privacy:
            print(run_privacy_audit(repo_root="."))
        else:
            print("Nothing to audit: pass --privacy.")
        return

    if args.command == "init":
        print(run_init(repo_root="."))
        return

    if args.command == "scan":
        print(run_scan(repo_root="."))
        return

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "You are a helpful AI assistant.")

    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)

    run_agent_loop(agent=agent, war_room_file=args.room, sleep_time=args.sleep)


if __name__ == "__main__":
    main()
