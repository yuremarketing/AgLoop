"""
Módulo de atualização segura de templates e protocolo do AgLoop.

Issue #54: Compara arquivos de protocolo (.claude/skills/vigilia/SKILL.md,
AGENTS.md, CLAUDE.md, GEMINI.md) com os templates empacotados, preserva
customizações do usuário e NUNCA toca em governança preenchida.
"""

from __future__ import annotations

import difflib
import os
import re
from dataclasses import dataclass, field
from pathlib import Path

from core.init_scaffold import get_templates_dir

VERSION_PATTERN = re.compile(r'version:\s*["\']?([^"\'\n]+)["\']?')


@dataclass
class ProtocolFileStatus:
    """Status de um arquivo de protocolo na verificação de atualização."""

    rel_path: str
    target_path: Path
    template_path: Path
    exists_locally: bool
    is_identical: bool
    local_version: str | None = None
    template_version: str | None = None
    diff: str = ""
    is_customized: bool = False

    @property
    def needs_update(self) -> bool:
        if not self.exists_locally:
            return True
        if self.local_version and self.template_version:
            from core.version_check import is_version_newer

            return is_version_newer(self.template_version, self.local_version)
        return not self.is_identical


@dataclass
class UpdateReport:
    """Relatório consolidado da operação de atualização."""

    statuses: list[ProtocolFileStatus] = field(default_factory=list)
    applied_files: list[str] = field(default_factory=list)
    created_files: list[str] = field(default_factory=list)
    backup_files: list[str] = field(default_factory=list)
    skipped_files: list[str] = field(default_factory=list)


def extract_protocol_version(content: str) -> str | None:
    """Extrai o campo version do frontmatter YAML de um arquivo SKILL.md."""
    match = VERSION_PATTERN.search(content)
    return match.group(1).strip() if match else None


def detect_customization(local_content: str, tmpl_content: str) -> bool:
    """
    Verifica se o arquivo local possui alterações substantivas além da versão no frontmatter.
    Útil para alertar sobre personalizações do usuário (nomes de PO, seções extras).
    """
    diff_lines = list(
        difflib.unified_diff(
            local_content.splitlines(),
            tmpl_content.splitlines(),
            n=0,
        )
    )
    changed = [
        line
        for line in diff_lines
        if (line.startswith("+") or line.startswith("-"))
        and not line.startswith("+++")
        and not line.startswith("---")
        and "version:" not in line
    ]
    return len(changed) > 0


def check_protocol_update_status(repo_root: str = ".") -> list[ProtocolFileStatus]:
    """
    Inspeciona os arquivos de protocolo do repositório e compara com os templates empacotados.
    """
    root = Path(repo_root).resolve()
    templates_dir = get_templates_dir()

    protocol_mapping = [
        (".claude/skills/vigilia/SKILL.md", templates_dir / "skills" / "vigilia" / "SKILL.md"),
        ("AGENTS.md", templates_dir / "AGENTS.md"),
        ("CLAUDE.md", templates_dir / "CLAUDE.md"),
        ("GEMINI.md", templates_dir / "GEMINI.md"),
        ("docs/gestao/roster-agentes.md", templates_dir / "gestao" / "roster-agentes.md"),
    ]

    statuses: list[ProtocolFileStatus] = []

    for rel_path, tmpl_path in protocol_mapping:
        if not tmpl_path.is_file():
            continue

        local_path = root / rel_path
        exists = local_path.is_file()
        tmpl_content = tmpl_path.read_text(encoding="utf-8")
        tmpl_version = extract_protocol_version(tmpl_content)

        if not exists:
            statuses.append(
                ProtocolFileStatus(
                    rel_path=rel_path,
                    target_path=local_path,
                    template_path=tmpl_path,
                    exists_locally=False,
                    is_identical=False,
                    local_version=None,
                    template_version=tmpl_version,
                    diff=f"+ Arquivo novo a ser criado: {rel_path}",
                    is_customized=False,
                )
            )
            continue

        local_content = local_path.read_text(encoding="utf-8")
        local_version = extract_protocol_version(local_content)
        is_ident = local_content == tmpl_content
        is_cust = detect_customization(local_content, tmpl_content) if not is_ident else False

        # Gera diff unificado
        diff_lines = list(
            difflib.unified_diff(
                local_content.splitlines(keepends=True),
                tmpl_content.splitlines(keepends=True),
                fromfile=f"a/{rel_path} (local v{local_version or '?'})",
                tofile=f"b/{rel_path} (template v{tmpl_version or '?'})",
                n=3,
            )
        )
        diff_str = "".join(diff_lines)

        statuses.append(
            ProtocolFileStatus(
                rel_path=rel_path,
                target_path=local_path,
                template_path=tmpl_path,
                exists_locally=True,
                is_identical=is_ident,
                local_version=local_version,
                template_version=tmpl_version,
                diff=diff_str,
                is_customized=is_cust,
            )
        )

    return statuses


def run_update(
    repo_root: str = ".",
    dry_run: bool = False,
    yes: bool = False,
    interactive: bool = False,
) -> UpdateReport:
    """
    Executa a verificação ou aplicação de atualizações do protocolo do AgLoop.

    :param repo_root: Raiz do repositório.
    :param dry_run: Se True, apenas calcula diffs sem alterar arquivos no disco.
    :param yes: Se True, aplica as alterações sem confirmação interativa.
    :param interactive: Se True e yes=False, solicita confirmação no terminal mostrando diffs.
    :return: UpdateReport consolidado.
    """
    statuses = check_protocol_update_status(repo_root=repo_root)
    report = UpdateReport(statuses=statuses)

    pending_updates = [s for s in statuses if s.needs_update]
    if not pending_updates or dry_run:
        return report

    # Em modo interativo sem --yes, solicita confirmação transparente exibindo os diffs
    if interactive and not yes:
        print("\n============================================================")
        print("          CONFIRMAÇÃO DE ATUALIZAÇÃO (AGLOOP UPDATE)         ")
        print("============================================================")
        print("⚠️  AVISO: agloop update realiza a SUBSTITUIÇÃO COMPLETA dos")
        print("   arquivos pelos templates empacotados na nova versão.")
        print("   Ele NÃO realiza mesclagem automática (merge de 3 vias).")
        print("   Cópias de segurança (.bak) serão criadas para permitir que")
        print("   personalizações locais sejam reincorporadas manualmente.\n")
        print("Arquivos de protocolo passíveis de atualização:")
        for s in pending_updates:
            cust_note = " [⚠️ PERSONALIZADO PELO USUÁRIO]" if s.is_customized else ""
            action = (
                "Criar novo arquivo"
                if not s.exists_locally
                else f"Substituir (v{s.local_version or '?'} -> v{s.template_version or '?'}){cust_note}"
            )
            print(f"  - {s.rel_path}: {action}")

        # Exibe os diffs reais antes de pedir confirmação
        for s in pending_updates:
            if s.diff:
                print(f"\n--- Diff proposto para {s.rel_path} ---")
                print(s.diff)

        try:
            resp = (
                input("\nDeseja aplicar a SUBSTITUIÇÃO desses arquivos com backup (.bak)? [s/N]: ")
                .strip()
                .lower()
            )
            if resp not in ("s", "sim", "y", "yes"):
                report.skipped_files = [s.rel_path for s in pending_updates]
                return report
        except (EOFError, KeyboardInterrupt):
            report.skipped_files = [s.rel_path for s in pending_updates]
            return report

    # Aplicação segura das alterações
    for s in pending_updates:
        # docs/gestao/roster-agentes.md só é criado se não existia; se já existia, nunca sobrescreve
        if s.rel_path == "docs/gestao/roster-agentes.md" and s.exists_locally:
            report.skipped_files.append(s.rel_path)
            continue

        tmpl_content = s.template_path.read_text(encoding="utf-8")
        s.target_path.parent.mkdir(parents=True, exist_ok=True)

        if s.exists_locally:
            # Cria backup com extensão .bak
            backup_path = s.target_path.with_name(s.target_path.name + ".bak")
            backup_path.write_text(s.target_path.read_text(encoding="utf-8"), encoding="utf-8")
            report.backup_files.append(str(backup_path))
            s.target_path.write_text(tmpl_content, encoding="utf-8")
            report.applied_files.append(s.rel_path)
        else:
            s.target_path.write_text(tmpl_content, encoding="utf-8")
            report.created_files.append(s.rel_path)

    return report


def format_update_summary(report: UpdateReport, dry_run: bool = False) -> str:
    """Formata o relatório de atualização para exibição amigável no terminal."""
    lines = [
        "============================================================",
        "             ATUALIZAÇÃO DE PROTOCOLO (AGLOOP UPDATE)        ",
        "============================================================",
        "",
    ]

    has_changes = any(s.needs_update for s in report.statuses)
    if not has_changes:
        lines.append("Protocolo do projeto já está 100% atualizado com os templates empacotados.")
        lines.append("Nenhuma alteração necessária.")
        lines.append("============================================================")
        return "\n".join(lines)

    lines.append("Status dos arquivos de protocolo:")
    for s in report.statuses:
        if not s.exists_locally:
            lines.append(f"  [NOVO]                 {s.rel_path} (template v{s.template_version or '?'})")
        elif s.needs_update:
            tag = "[CUSTOMIZADO/DEFASADO]" if s.is_customized else "[DEFASADO]"
            lines.append(
                f"  {tag:<22} {s.rel_path} (local v{s.local_version or '?'} < template v{s.template_version or '?'})"
            )
        else:
            lines.append(f"  [ATUALIZADO]           {s.rel_path} (v{s.local_version or '?'})")

    if dry_run:
        lines.append("")
        lines.append("--- Diffs estruturais (--dry-run) ---")
        for s in report.statuses:
            if s.needs_update and s.diff:
                lines.append(f"\n--- {s.rel_path} ---")
                lines.append(s.diff)
        lines.append("\nModo dry-run: nenhum arquivo foi modificado no disco.")
        lines.append("Para aplicar a substituição com backup automático: agloop update --yes")
    elif report.applied_files or report.created_files:
        lines.append("")
        lines.append("Resultados da atualização:")
        for f in report.created_files:
            lines.append(f"  ✓ Criado: {f}")
        for f in report.applied_files:
            lines.append(f"  ✓ Substituído: {f} (backup preservado em {f}.bak)")
        for f in report.skipped_files:
            lines.append(f"  - Preservado: {f}")
        lines.append("\nAtualização concluída com sucesso.")
        lines.append("Aviso: Caso você possuísse personalizações no arquivo original, elas estão preservadas no .bak.")
        lines.append("Documentos de governança preenchidos (roadmap, backlog, riscos) foram preservados intactos.")

    lines.append("============================================================")
    return "\n".join(lines)
