import argparse
import sys
from pathlib import Path

from dotenv import load_dotenv
from core.agent import Agent, configure_json_logging
from core.init_scaffold import run_init
from core.privacy_audit import run_privacy_audit
from core.readiness_gate import check_readiness, format_report_text
from core.runner import run_agent_loop
from core.scan import run_scan
from core.update_scaffold import format_update_summary, run_update
from core.version_check import check_pypi_update

# Load environment variables
load_dotenv()

# Structured JSON logs on stderr (Issue #11) — never stdout, so `agloop-mcp` (which
# writes JSON-RPC replies to stdout) is never corrupted even if it imports this module.
configure_json_logging()

# Define roles for our agents
ROLES = {
    "Alice": "You are a senior software architect. You focus on structure, scalability, and robust design. You like to propose high-level ideas.",
    "Bob": "You are a pragmatic developer. You focus on implementation details, edge cases, and code simplicity. You like to challenge complex architectures."
}


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run, audit, or verify readiness of an AgLoop agent")
    subparsers = parser.add_subparsers(dest="command")

    run_parser = subparsers.add_parser("run", help="Run an AgLoop agent loop (default).")
    run_parser.add_argument("--name", type=str, required=True, help="Name of the agent (e.g., Alice or Bob)")
    run_parser.add_argument("--model", type=str, default="gemini/gemini-1.5-pro-latest", help="LLM model to use")
    run_parser.add_argument("--sleep", type=int, default=10, help="Seconds to sleep between loop iterations")
    run_parser.add_argument("--room", type=str, default="war_room.md", help="The markdown file for IPC")
    run_parser.add_argument(
        "--force-bypass-gate",
        action="store_true",
        help="Force run even if Readiness Gate is red (emergency only, PO explicit order).",
    )

    audit_parser = subparsers.add_parser("audit", help="Run local diagnostics (no LLM calls).")
    audit_parser.add_argument("--privacy", action="store_true", help="Run the LGPD-04 privacy diagnostic report.")

    init_parser = subparsers.add_parser("init", help="Scaffold a clean war_room.md and governance templates in this repo.")
    init_parser.add_argument("-q", "--quiet", action="store_true", help="Suppress onboarding message and next steps.")

    subparsers.add_parser("scan", help="Read-only scan of the repository structure and known stack manifests.")

    check_parser = subparsers.add_parser(
        "check",
        help="Deterministic Readiness Gate check (no LLM calls, exit 0 on pass, 1 on fail).",
    )
    check_parser.add_argument("-q", "--quiet", action="store_true", help="Print only summary pass/fail status.")
    check_parser.add_argument("--repo-root", type=str, default=".", help="Root directory of the repo to check.")

    update_parser = subparsers.add_parser(
        "update",
        help="Update AgLoop vigil protocol files (SKILL.md, AGENTS.md, etc.) preserving customizations.",
    )
    update_parser.add_argument("-y", "--yes", action="store_true", help="Apply updates without interactive confirmation.")
    update_parser.add_argument("--dry-run", action="store_true", help="Show unified diffs without modifying files.")
    update_parser.add_argument("--repo-root", type=str, default=".", help="Root directory of the repo to update.")

    report_parser = subparsers.add_parser(
        "report",
        help="Formaliza um achado de campo como issue em yuremarketing/AgLoop (confirmação humana obrigatória).",
    )
    report_parser.add_argument("--title", type=str, help="Título do issue. Omitido => modo interativo.")
    report_parser.add_argument("--body-file", type=str, help="Arquivo com a descrição do achado.")
    report_parser.add_argument("--body", "--description", dest="body_text", type=str, help="Descrição inline (alternativa a --body-file).")
    report_parser.add_argument("--severity", choices=["low", "medium", "high"], default="medium", help="Severidade do achado.")
    report_parser.add_argument("--force", action="store_true", help="Pula a checagem de issues duplicados.")
    report_parser.add_argument("-y", "--yes", action="store_true", help="Publica sem prompt de confirmação (modo não-interativo).")
    report_parser.add_argument("--repo-root", type=str, default=".", help="Diretório do projeto de origem (p/ detectar ambiente).")
    report_parser.add_argument("--repo", type=str, default="yuremarketing/AgLoop", help="Repositório de destino (owner/repo).")

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
        print(run_init(repo_root=".", quiet=getattr(args, "quiet", False)))
        notice = check_pypi_update()
        if notice:
            print(f"\n💡 {notice}")
        return

    if args.command == "scan":
        print(run_scan(repo_root="."))
        return

    if args.command == "check":
        report = check_readiness(repo_root=getattr(args, "repo_root", "."))
        print(format_report_text(report, quiet=getattr(args, "quiet", False)))
        if not report.passed:
            sys.exit(1)
        return

    if args.command == "update":
        report = run_update(
            repo_root=getattr(args, "repo_root", "."),
            dry_run=getattr(args, "dry_run", False),
            yes=getattr(args, "yes", False),
            interactive=not getattr(args, "yes", False),
        )
        print(format_update_summary(report, dry_run=getattr(args, "dry_run", False)))
        notice = check_pypi_update()
        if notice:
            print(f"\n💡 {notice}")
        return

    if args.command == "report":
        from core.report_bug import run_report

        title = args.title
        description = None
        if getattr(args, "body_text", None):
            description = args.body_text
        elif getattr(args, "body_file", None):
            description = Path(args.body_file).read_text(encoding="utf-8")

        interactive = title is None and description is None
        confirm = None
        if interactive:
            title = input("Título: ").strip()
            print("Descrição (finalize com uma linha vazia):")
            lines = []
            while True:
                try:
                    line = input()
                except EOFError:
                    break
                if line == "":
                    break
                lines.append(line)
            description = "\n".join(lines)

            def confirm(body: str) -> bool:
                print("\n" + "=" * 60 + f"\n{body}\n" + "=" * 60)
                answer = input(f"Publicar este issue em {getattr(args, 'repo', 'yuremarketing/AgLoop')}? [s/N] ").strip().lower()
                return answer in ("s", "sim", "y", "yes")
        elif title is None or description is None:
            print("Use --title junto com --body-file/--body, ou nenhum dos dois para o modo interativo.", file=sys.stderr)
            sys.exit(2)

        result = run_report(
            title=title,
            description=description,
            severity=getattr(args, "severity", "medium"),
            repo_root=getattr(args, "repo_root", "."),
            repo=getattr(args, "repo", "yuremarketing/AgLoop"),
            force=getattr(args, "force", False),
            yes=getattr(args, "yes", False),
            confirm=confirm,
        )
        print(result.message)
        if result.rendered_body and not result.submitted and not result.duplicate_url and not result.error:
            print("\n--- Rascunho do issue ---\n")
            print(result.rendered_body)
        sys.exit(1 if result.error else 0)

    notice = check_pypi_update()
    if notice:
        print(f"💡 {notice}\n")

    if not getattr(args, "force_bypass_gate", False):
        report = check_readiness(repo_root=".")
        if not report.passed:
            print(format_report_text(report, quiet=False), file=sys.stderr)
            print("\n[BLOQUEIO] Execução recusada pelo Gate de Prontidão 🔴.", file=sys.stderr)
            print("Regra pétrea: Nenhuma linha de código ou loop de produção antes do Gate 🟢.", file=sys.stderr)
            print("Para bypass de emergência com autorização expressa do PO, use --force-bypass-gate.\n", file=sys.stderr)
            sys.exit(1)

    agent_name = args.name
    role_prompt = ROLES.get(agent_name, "You are a helpful AI assistant.")

    agent = Agent(name=agent_name, role_prompt=role_prompt, model=args.model)

    run_agent_loop(agent=agent, war_room_file=args.room, sleep_time=args.sleep)


if __name__ == "__main__":
    main()
