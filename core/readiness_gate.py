"""
Módulo determinístico de validação do Gate de Prontidão do AgLoop.

Issue #42 (Fase B): Verificação determinística (sem IA, 🟢/🔴) dos requisitos
obrigatórios (🔒) e recomendados (📌) antes de autorizar código de produção.
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass, field
from pathlib import Path

TODO_PATTERN = re.compile(r"<!--\s*AGLOOP_TODO:\s*(.*?)\s*-->", re.IGNORECASE)


@dataclass
class ReadinessItem:
    """Representa um item do checklist do Gate de Prontidão."""

    id: str
    name: str
    description: str
    required: bool
    passed: bool
    detail: str = ""


@dataclass
class ReadinessReport:
    """Relatório consolidado de verificação de prontidão."""

    items: list[ReadinessItem] = field(default_factory=list)

    @property
    def passed(self) -> bool:
        """Retorna True se todos os itens obrigatórios (🔒) forem atendidos."""
        return all(item.passed for item in self.items if item.required)

    @property
    def blocking_issues(self) -> list[ReadinessItem]:
        """Lista os itens obrigatórios pendentes."""
        return [item for item in self.items if item.required and not item.passed]

    @property
    def warnings(self) -> list[ReadinessItem]:
        """Lista os itens recomendados pendentes."""
        return [item for item in self.items if not item.required and not item.passed]


def _find_todo_markers(content: str) -> list[str]:
    """Retorna lista de descrições dos marcadores AGLOOP_TODO encontrados no texto."""
    return [match.strip() for match in TODO_PATTERN.findall(content)]


def check_readiness(repo_root: str = ".") -> ReadinessReport:
    """
    Executa a verificação determinística do Gate de Prontidão.

    :param repo_root: Raiz do repositório a ser verificado.
    :return: ReadinessReport com o status consolidado de cada item.
    """
    root = Path(repo_root)
    items: list[ReadinessItem] = []

    # 1. 🔒 Sala de Guerra (war_room.md)
    war_room_path = root / "war_room.md"
    war_room_exists = war_room_path.is_file() and war_room_path.stat().st_size > 0
    items.append(
        ReadinessItem(
            id="war_room",
            name="Sala de Guerra (war_room.md)",
            description="Arquivo central de comunicação e sincronização da Sala de Guerra",
            required=True,
            passed=war_room_exists,
            detail="Arquivo presente e ativo" if war_room_exists else "war_room.md ausente ou vazio",
        )
    )

    # 2. 🔒 Protocolo / Ponto de Entrada (AGENTS.md ou SKILL.md)
    agents_md = root / "AGENTS.md"
    skill_md = root / ".claude" / "skills" / "vigilia" / "SKILL.md"
    has_protocol = (agents_md.is_file() and agents_md.stat().st_size > 0) or (
        skill_md.is_file() and skill_md.stat().st_size > 0
    )
    items.append(
        ReadinessItem(
            id="protocol",
            name="Ponto de Entrada e Protocolo (AGENTS.md / SKILL.md)",
            description="Instruções canônicas de operação e vigília dos agentes",
            required=True,
            passed=has_protocol,
            detail="Protocolo configurado"
            if has_protocol
            else "Nem AGENTS.md nem .claude/skills/vigilia/SKILL.md foram encontrados",
        )
    )

    # 3. 🔒 Termo de Abertura ou Visão de Produto (docs/gestao/termo-abertura.md ou visao.md)
    termo_path = root / "docs" / "gestao" / "termo-abertura.md"
    visao_path = root / "docs" / "gestao" / "visao.md"
    has_termo = False
    termo_detail = "Termo de abertura ou visão ausente"
    for candidate in (termo_path, visao_path):
        if candidate.is_file() and candidate.stat().st_size > 20:
            has_termo = True
            termo_detail = f"Presente em {candidate.relative_to(root)}"
            break
    items.append(
        ReadinessItem(
            id="charter",
            name="Termo de Abertura / Visão (termo-abertura.md ou visao.md)",
            description="Definição do problema, público-alvo, critérios de sucesso e PO",
            required=True,
            passed=has_termo,
            detail=termo_detail,
        )
    )

    # 4. 🔒 Backlog de Produto (docs/gestao/backlog-produto.md)
    backlog_path = root / "docs" / "gestao" / "backlog-produto.md"
    if not backlog_path.is_file():
        backlog_passed = False
        backlog_detail = "docs/gestao/backlog-produto.md ausente"
    else:
        content = backlog_path.read_text(encoding="utf-8")
        todos = _find_todo_markers(content)
        if todos:
            backlog_passed = False
            backlog_detail = f"Contém {len(todos)} marcador(es) AGLOOP_TODO pendente(s)"
        elif len(content.strip()) < 20:
            backlog_passed = False
            backlog_detail = "Arquivo vazio ou sem conteúdo útil"
        else:
            backlog_passed = True
            backlog_detail = "Preenchido e sem marcadores pendentes"
    items.append(
        ReadinessItem(
            id="backlog",
            name="Backlog de Produto (backlog-produto.md)",
            description="Backlog inicial com user stories e critérios de aceite definidos",
            required=True,
            passed=backlog_passed,
            detail=backlog_detail,
        )
    )

    # 5. 🔒 Matriz de Riscos (docs/gestao/matriz-riscos.md)
    riscos_path = root / "docs" / "gestao" / "matriz-riscos.md"
    if not riscos_path.is_file():
        riscos_passed = False
        riscos_detail = "docs/gestao/matriz-riscos.md ausente"
    else:
        content = riscos_path.read_text(encoding="utf-8")
        todos = _find_todo_markers(content)
        if todos:
            riscos_passed = False
            riscos_detail = f"Contém {len(todos)} marcador(es) AGLOOP_TODO pendente(s)"
        elif len(content.strip()) < 20:
            riscos_passed = False
            riscos_detail = "Arquivo vazio ou sem conteúdo útil"
        else:
            riscos_passed = True
            riscos_detail = "Preenchido e sem marcadores pendentes"
    items.append(
        ReadinessItem(
            id="risks",
            name="Matriz de Riscos (matriz-riscos.md)",
            description="Identificação inicial de riscos, probabilidades e mitigações",
            required=True,
            passed=riscos_passed,
            detail=riscos_detail,
        )
    )

    # 6. 🔒 Roster e Capacidades (docs/gestao/roster-agentes.md)
    roster_path = root / "docs" / "gestao" / "roster-agentes.md"
    if not roster_path.is_file():
        roster_passed = False
        roster_detail = "docs/gestao/roster-agentes.md ausente"
    else:
        content = roster_path.read_text(encoding="utf-8")
        todos = _find_todo_markers(content)
        if todos:
            roster_passed = False
            roster_detail = f"Contém {len(todos)} marcador(es) AGLOOP_TODO pendente(s)"
        elif len(content.strip()) < 20:
            roster_passed = False
            roster_detail = "Arquivo vazio ou sem conteúdo útil"
        else:
            roster_passed = True
            roster_detail = "Preenchido e sem marcadores pendentes"
    items.append(
        ReadinessItem(
            id="roster",
            name="Roster e Capacidades (roster-agentes.md)",
            description="Inventário de agentes participantes e ferramentas atribuídas",
            required=True,
            passed=roster_passed,
            detail=roster_detail,
        )
    )

    # 7. 📌 Roadmap de Marcos (docs/gestao/roadmap.md)
    roadmap_path = root / "docs" / "gestao" / "roadmap.md"
    if not roadmap_path.is_file():
        roadmap_passed = False
        roadmap_detail = "docs/gestao/roadmap.md ausente (recomendado)"
    else:
        content = roadmap_path.read_text(encoding="utf-8")
        todos = _find_todo_markers(content)
        if todos:
            roadmap_passed = False
            roadmap_detail = f"Contém {len(todos)} marcador(es) AGLOOP_TODO pendente(s)"
        else:
            roadmap_passed = True
            roadmap_detail = "Preenchido e sem marcadores pendentes"
    items.append(
        ReadinessItem(
            id="roadmap",
            name="Roadmap de Marcos (roadmap.md)",
            description="Planejamento de entregas estruturado em marcos (M1, M2...)",
            required=False,
            passed=roadmap_passed,
            detail=roadmap_detail,
        )
    )

    # 8. 📌 Segurança de Segredos (.env vs .gitignore)
    env_file = root / ".env"
    gitignore_file = root / ".gitignore"
    env_safe = True
    env_detail = "Nenhum .env exposto"
    if env_file.is_file():
        if not gitignore_file.is_file():
            env_safe = False
            env_detail = ".env existe mas .gitignore não foi encontrado"
        else:
            gitignore_content = gitignore_file.read_text(encoding="utf-8")
            if ".env" not in gitignore_content:
                env_safe = False
                env_detail = ".env existe mas não está listado no .gitignore"
            else:
                env_detail = ".env devidamente protegido no .gitignore"
    items.append(
        ReadinessItem(
            id="env_security",
            name="Proteção de Credenciais (.gitignore)",
            description="Garante que arquivos .env e segredos locais não sejam commitados",
            required=False,
            passed=env_safe,
            detail=env_detail,
        )
    )

    # 9. 📌 Versão do Protocolo de Vigília (.claude/skills/vigilia/SKILL.md)
    protocol_skill = root / ".claude" / "skills" / "vigilia" / "SKILL.md"
    proto_up_to_date = True
    proto_detail = "Protocolo alinhado com a versão empacotada"
    if protocol_skill.is_file():
        from core.init_scaffold import get_templates_dir
        from core.update_scaffold import extract_protocol_version
        from core.version_check import is_version_newer

        local_v = extract_protocol_version(protocol_skill.read_text(encoding="utf-8"))
        tmpl_file = get_templates_dir() / "skills" / "vigilia" / "SKILL.md"
        if tmpl_file.is_file():
            tmpl_v = extract_protocol_version(tmpl_file.read_text(encoding="utf-8"))
            if local_v and tmpl_v and is_version_newer(tmpl_v, local_v):
                proto_up_to_date = False
                proto_detail = f"Protocolo local v{local_v} defasado (template v{tmpl_v}). Execute: agloop update"
            elif local_v:
                proto_detail = f"Protocolo local v{local_v} alinhado"
    items.append(
        ReadinessItem(
            id="protocol_version",
            name="Versão do Protocolo de Vigília (SKILL.md)",
            description="Verifica se o protocolo do projeto está alinhado com a versão mais recente",
            required=False,
            passed=proto_up_to_date,
            detail=proto_detail,
        )
    )

    return ReadinessReport(items=items)


def format_report_text(report: ReadinessReport, quiet: bool = False, use_color: bool = True) -> str:
    """
    Formata o resultado do Gate de Prontidão para exibição no terminal.

    :param report: Objeto ReadinessReport gerado por check_readiness.
    :param quiet: Se True, emite apenas a linha de status 🟢/🔴.
    :param use_color: Se True e NO_COLOR não estiver ativo, aplica cores ANSI.
    :return: String pronta para impressão.
    """
    if os.getenv("NO_COLOR"):
        use_color = False

    green = "\033[1;32m" if use_color else ""
    red = "\033[1;31m" if use_color else ""
    yellow = "\033[1;33m" if use_color else ""
    bold = "\033[1m" if use_color else ""
    reset = "\033[0m" if use_color else ""

    from core.version_check import check_pypi_update

    update_notice = check_pypi_update()

    if quiet:
        base_line = (
            f"{green}Gate de Prontidão: 🟢 (Aprovado){reset}"
            if report.passed
            else f"{red}Gate de Prontidão: 🔴 ({len(report.blocking_issues)} pendência(s) bloqueante(s)){reset}"
        )
        if update_notice:
            return f"{base_line}\n💡 {update_notice}"
        return base_line

    lines = [
        f"{bold}============================================================{reset}",
        f"{bold}           GATE DE PRONTIDÃO DE GOVERNANÇA (AGLOOP)         {reset}",
        f"{bold}============================================================{reset}",
        "",
        "Status dos itens para autorizar código de produção:",
        "",
    ]

    for item in report.items:
        prefix = "🔒" if item.required else "📌"
        if item.passed:
            tag = f"{green}[OK]{reset}"
        elif item.required:
            tag = f"{red}[BLOQUEIO]{reset}"
        else:
            tag = f"{yellow}[AVISO]{reset}"

        lines.append(f"  {prefix} {tag} {bold}{item.name}{reset}")
        if item.detail:
            lines.append(f"       └── {item.detail}")

    lines.append("")
    lines.append(f"{bold}------------------------------------------------------------{reset}")

    if report.passed:
        lines.append(f"{green}{bold}RESULTADO: 🟢 GATE DE PRONTIDÃO APROVADO!{reset}")
        lines.append("Sala ativa. Todos os pré-requisitos de governança atendidos.")
        lines.append("Pronto para receber demandas e executar código de produção.")
    else:
        lines.append(f"{red}{bold}RESULTADO: 🔴 GATE DE PRONTIDÃO BLOQUEADO!{reset}")
        lines.append(
            f"Existem {red}{len(report.blocking_issues)} item(ns) obrigatório(s) pendente(s){reset}."
        )
    if update_notice:
        lines.append("")
        lines.append(f"{yellow}💡 {update_notice}{reset}")

    lines.append(f"{bold}============================================================{reset}")
    return "\n".join(lines)
