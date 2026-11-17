"""
Orquestrador Supervisor Contínuo do AgLoop (Issue #74 / ADR-0008).

Desacopla o ciclo de vida da supervisão de processos da inferência efêmera das LLMs.
Executa como processo determinístico e contínuo no host (fora das janelas de chat),
rearmando-se automaticamente a cada turno e disparando alarmes ativos em caso de travamento.

Camada fina (DRY/SSOT) sobre `core.runner.watch_war_room` e `core.banner.play_formal_auth_alert`.
"""

import argparse
import json
import logging
import os
import signal
import subprocess
import sys
import time
from typing import Dict, Optional

from core.banner import play_formal_auth_alert
from core.git_lock import GitLock
from core.runner import STALL_SENTINEL, read_heartbeat, watch_war_room

_logger = logging.getLogger("agloop.daemon")

DEFAULT_DAEMON_PID_FILE = os.path.join(".agloop", "agloop_daemon.pid")
DEFAULT_STALL_MINUTES = 15.0
DEFAULT_LOCAL_POLL = 2.0
DEFAULT_REMOTE_POLL = 30.0


def _write_pid_file(pid_file: str) -> None:
    os.makedirs(os.path.dirname(os.path.abspath(pid_file)), exist_ok=True)
    with open(pid_file, "w", encoding="utf-8") as f:
        f.write(str(os.getpid()))


def _read_pid_file(pid_file: str) -> Optional[int]:
    if not os.path.isfile(pid_file):
        return None
    try:
        with open(pid_file, "r", encoding="utf-8") as f:
            content = f.read().strip()
            return int(content) if content else None
    except (ValueError, OSError):
        return None


def _remove_pid_file(pid_file: str) -> None:
    try:
        if os.path.isfile(pid_file):
            os.remove(pid_file)
    except OSError:
        pass


def is_daemon_running(pid_file: str = DEFAULT_DAEMON_PID_FILE) -> bool:
    """Verifica se o daemon do AgLoop está ativo e respondendo no PID registrado."""
    pid = _read_pid_file(pid_file)
    if pid is None:
        return False
    alive = GitLock._pid_alive(pid)
    if not alive:
        # Limpa PID stale se o processo já morreu
        _remove_pid_file(pid_file)
        return False
    return True


class AgLoopDaemon:
    """
    Supervisor contínuo do AgLoop que orquestra e vigia a Sala de Guerra.
    """

    def __init__(
        self,
        war_room_file: str = "war_room.md",
        agent_name: str = "AgLoopDaemon",
        local_poll: float = DEFAULT_LOCAL_POLL,
        remote_poll: float = DEFAULT_REMOTE_POLL,
        stall_minutes: float = DEFAULT_STALL_MINUTES,
        repo_path: str = ".",
        pid_file: Optional[str] = None,
        audio_alert: bool = True,
    ):
        self.war_room_file = war_room_file
        self.agent_name = agent_name
        self.local_poll = local_poll
        self.remote_poll = remote_poll
        self.stall_minutes = stall_minutes
        self.repo_path = repo_path
        self.pid_file = pid_file or os.path.join(repo_path, DEFAULT_DAEMON_PID_FILE)
        self.audio_alert = audio_alert
        self.running = False

    def handle_signal(self, signum, frame):
        print(f"\n[Daemon] Sinal recebido ({signum}). Encerrando supervisor graciosamente...", flush=True)
        self.running = False

    def run(self, max_iterations: Optional[int] = None) -> None:
        """
        Executa o loop supervisor do daemon.
        `max_iterations` permite testes determinísticos limitando o número de ciclos.
        """
        self.running = True
        _write_pid_file(self.pid_file)

        # Registra tratadores de sinais para encerramento gracioso
        for sig in (signal.SIGINT, signal.SIGTERM):
            try:
                signal.signal(sig, self.handle_signal)
            except (ValueError, OSError, AttributeError):
                pass

        print("=" * 60)
        print(" [AGLOOP DAEMON] Supervisor de Host Ativado (ADR-0008) ")
        print(f" PID               : {os.getpid()}")
        print(f" Arquivo monitorado: {self.war_room_file}")
        print(f" Alarme estagnação : {self.stall_minutes:g} min (sempre ativo por padrão)")
        print(f" Polling local/rem : {self.local_poll}s / {self.remote_poll}s")
        print("=" * 60, flush=True)

        iterations = 0
        try:
            while self.running:
                iterations += 1
                result = watch_war_room(
                    war_room_file=self.war_room_file,
                    agent_name=self.agent_name,
                    local_poll=self.local_poll,
                    remote_poll=self.remote_poll,
                    once=True,
                    repo_path=self.repo_path,
                    stall_minutes=self.stall_minutes,
                )

                if not self.running:
                    break

                if result == STALL_SENTINEL:
                    print("\n" + "=" * 60, flush=True)
                    print(f"[Daemon] ⚠️  ALERTA: Sala de Guerra estagnada por > {self.stall_minutes:g} min!", flush=True)
                    print("[Daemon] O estado da sala foi alterado para WAITING_HUMAN.", flush=True)
                    print("=" * 60, flush=True)
                    if self.audio_alert:
                        play_formal_auth_alert()
                elif result is not None:
                    print(f"[Daemon] Turno registrado com orador: '{result}'. Rearmando vigília do host imediatamente...", flush=True)

                if max_iterations is not None and iterations >= max_iterations:
                    break

                # Pequena pausa defensiva antes do próximo ciclo one-shot
                time.sleep(0.5)

        finally:
            _remove_pid_file(self.pid_file)
            print("[Daemon] Supervisor encerrado com sucesso.", flush=True)


def start_daemon_background(
    war_room_file: str = "war_room.md",
    agent_name: str = "AgLoopDaemon",
    local_poll: float = DEFAULT_LOCAL_POLL,
    remote_poll: float = DEFAULT_REMOTE_POLL,
    stall_minutes: float = DEFAULT_STALL_MINUTES,
    repo_path: str = ".",
    pid_file: Optional[str] = None,
    log_file: Optional[str] = None,
) -> int:
    """Inicia o daemon em segundo plano (background) e retorna seu PID."""
    target_pid_file = pid_file or os.path.join(repo_path, DEFAULT_DAEMON_PID_FILE)
    if is_daemon_running(target_pid_file):
        existing_pid = _read_pid_file(target_pid_file)
        raise RuntimeError(f"Daemon já está em execução (PID: {existing_pid}).")

    target_log_file = log_file or os.path.join(repo_path, ".agloop", "daemon.log")
    os.makedirs(os.path.dirname(os.path.abspath(target_log_file)), exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "core.daemon",
        "run",
        "--room",
        war_room_file,
        "--agent",
        agent_name,
        "--local-poll",
        str(local_poll),
        "--remote-poll",
        str(remote_poll),
        "--stall-minutes",
        str(stall_minutes),
        "--repo-path",
        repo_path,
        "--pid-file",
        target_pid_file,
    ]

    with open(target_log_file, "a", encoding="utf-8") as out:
        kwargs = {}
        if sys.platform != "win32":
            kwargs["start_new_session"] = True
        else:
            kwargs["creationflags"] = getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)

        proc = subprocess.Popen(cmd, stdout=out, stderr=out, cwd=repo_path, **kwargs)

    # Aguarda brevemente para confirmar que o processo subiu
    time.sleep(0.5)
    if proc.poll() is not None:
        raise RuntimeError(f"Falha ao iniciar daemon em background (exit code: {proc.returncode}). Verifique {target_log_file}.")

    return proc.pid


def stop_daemon(pid_file: str = DEFAULT_DAEMON_PID_FILE, timeout: float = 5.0) -> bool:
    """Encerra o daemon em execução enviando SIGTERM."""
    pid = _read_pid_file(pid_file)
    if pid is None or not GitLock._pid_alive(pid):
        _remove_pid_file(pid_file)
        return False

    try:
        os.kill(pid, signal.SIGTERM)
    except OSError:
        pass

    deadline = time.time() + timeout
    while time.time() < deadline:
        if not GitLock._pid_alive(pid):
            _remove_pid_file(pid_file)
            return True
        time.sleep(0.2)

    # Força encerramento se não respondeu ao SIGTERM
    try:
        if sys.platform != "win32":
            os.kill(pid, signal.SIGKILL)
        else:
            os.kill(pid, signal.SIGTERM)
    except OSError:
        pass
    _remove_pid_file(pid_file)
    return True


def get_daemon_status(repo_path: str = ".", pid_file: Optional[str] = None) -> Dict[str, object]:
    """Retorna o estado operacional e telemetria do daemon."""
    target_pid = pid_file or os.path.join(repo_path, DEFAULT_DAEMON_PID_FILE)
    running = is_daemon_running(target_pid)
    pid = _read_pid_file(target_pid) if running else None
    hb = read_heartbeat(repo_path)
    return {
        "running": running,
        "pid": pid,
        "heartbeat": hb,
    }


def main():
    parser = argparse.ArgumentParser(description="AgLoop Host Daemon / Process Supervisor")
    subparsers = parser.add_subparsers(dest="subcommand", help="Comando de controle")

    run_parser = subparsers.add_parser("run", help="Executa o daemon em primeiro plano (foreground)")
    run_parser.add_argument("--room", type=str, default="war_room.md", help="Arquivo da Sala de Guerra")
    run_parser.add_argument("--agent", type=str, default="AgLoopDaemon", help="Nome do supervisor")
    run_parser.add_argument("--local-poll", type=float, default=DEFAULT_LOCAL_POLL, help="Intervalo local (s)")
    run_parser.add_argument("--remote-poll", type=float, default=DEFAULT_REMOTE_POLL, help="Intervalo remoto (s)")
    run_parser.add_argument("--stall-minutes", type=float, default=DEFAULT_STALL_MINUTES, help="Minutos p/ alarme de travamento")
    run_parser.add_argument("--repo-path", type=str, default=".", help="Raiz do repositório")
    run_parser.add_argument("--pid-file", type=str, default=DEFAULT_DAEMON_PID_FILE, help="Arquivo de PID")
    run_parser.add_argument("--no-audio", action="store_true", help="Desativa alarme sonoro")

    start_parser = subparsers.add_parser("start", help="Inicia o daemon em segundo plano (background)")
    start_parser.add_argument("--room", type=str, default="war_room.md", help="Arquivo da Sala de Guerra")
    start_parser.add_argument("--agent", type=str, default="AgLoopDaemon", help="Nome do supervisor")
    start_parser.add_argument("--stall-minutes", type=float, default=DEFAULT_STALL_MINUTES, help="Minutos p/ alarme de travamento")
    start_parser.add_argument("--repo-path", type=str, default=".", help="Raiz do repositório")
    start_parser.add_argument("--pid-file", type=str, default=DEFAULT_DAEMON_PID_FILE, help="Arquivo de PID")
    start_parser.add_argument("--log-file", type=str, default=None, help="Arquivo de log")

    stop_parser = subparsers.add_parser("stop", help="Encerra o daemon em segundo plano")
    stop_parser.add_argument("--pid-file", type=str, default=DEFAULT_DAEMON_PID_FILE, help="Arquivo de PID")

    status_parser = subparsers.add_parser("status", help="Consulta o status operacional do daemon")
    status_parser.add_argument("--repo-path", type=str, default=".", help="Raiz do repositório")
    status_parser.add_argument("--pid-file", type=str, default=DEFAULT_DAEMON_PID_FILE, help="Arquivo de PID")

    args = parser.parse_args()

    if args.subcommand == "run":
        daemon = AgLoopDaemon(
            war_room_file=args.room,
            agent_name=args.agent,
            local_poll=args.local_poll,
            remote_poll=args.remote_poll,
            stall_minutes=args.stall_minutes,
            repo_path=args.repo_path,
            pid_file=args.pid_file,
            audio_alert=not args.no_audio,
        )
        daemon.run()
    elif args.subcommand == "start":
        try:
            pid = start_daemon_background(
                war_room_file=args.room,
                agent_name=args.agent,
                stall_minutes=args.stall_minutes,
                repo_path=args.repo_path,
                pid_file=args.pid_file,
                log_file=args.log_file,
            )
            print(f"AgLoop Daemon iniciado em background (PID: {pid}).")
        except RuntimeError as e:
            print(f"Erro: {e}", file=sys.stderr)
            sys.exit(1)
    elif args.subcommand == "stop":
        stopped = stop_daemon(args.pid_file)
        if stopped:
            print("AgLoop Daemon encerrado com sucesso.")
        else:
            print("AgLoop Daemon não estava em execução.")
    elif args.subcommand == "status":
        st = get_daemon_status(args.repo_path, args.pid_file)
        if st["running"]:
            print(f"AgLoop Daemon: EM EXECUÇÃO (PID: {st['pid']})")
        else:
            print("AgLoop Daemon: PARADO")
        if st["heartbeat"]:
            print(f"Último Heartbeat: {st['heartbeat']}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
