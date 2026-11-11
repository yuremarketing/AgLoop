"""
Módulo de renderização de banners visuais de alta visibilidade do AgLoop.

Issue #45: Banner visual de alto impacto para solicitação de Autorização Formal do PO.
"""

from __future__ import annotations

import os

SOLID_BANNER_ASCII = """\
████████████████████████████████████████████████████████████████████
█                                                                  █
█               ⚠️   AUTORIZAÇÃO FORMAL DO PO   ⚠️                 █
█                   (CLÁUSULA PÉTREA AG-LOOP)                      █
█                                                                  █
████████████████████████████████████████████████████████████████████"""


def format_formal_auth_banner(
    reason: str = "",
    context: str = "",
    is_terminal: bool = False,
    blink: bool = True,
) -> str:
    """
    Formata o banner visual de alto impacto para autorização formal do PO.

    :param reason: Motivo conciso da solicitação de autorização.
    :param context: Contexto técnico opcional (ex: PR, arquivo ou branch).
    :param is_terminal: Se True e NO_COLOR não estiver ativo, aplica cores ANSI e blink.
                        Default False para Markdown seguro em chat, GitHub e logs.
    :param blink: Se True e is_terminal for True, aplica sequência ANSI de piscar (\\033[5m).
    :return: String pronta para renderização.
    """
    clean_reason = reason.strip() or "Aguardando confirmação explícita do PO."
    clean_context = context.strip()

    if is_terminal and not os.getenv("NO_COLOR"):
        red = "\033[1;31m"
        yellow = "\033[1;33m"
        blink_code = "\033[5m" if blink else ""
        reset = "\033[0m"
        bold = "\033[1m"

        header_lines = [
            f"{red}████████████████████████████████████████████████████████████████████{reset}",
            f"{red}█{reset}                                                                  {red}█{reset}",
            f"{red}█{reset}               {yellow}{blink_code}⚠️   AUTORIZAÇÃO FORMAL DO PO   ⚠️{reset}                 {red}█{reset}",
            f"{red}█{reset}                   {yellow}(CLÁUSULA PÉTREA AG-LOOP){reset}                      {red}█{reset}",
            f"{red}█{reset}                                                                  {red}█{reset}",
            f"{red}████████████████████████████████████████████████████████████████████{reset}",
        ]
        body = [
            f"\n{bold}⚠️  MOTIVO:{reset} {clean_reason}",
        ]
        if clean_context:
            body.append(f"{bold}📋 CONTEXTO:{reset} {clean_context}")
        body.append(f"{bold}👉 AÇÃO DO PO:{reset} Responda {yellow}'ok'{reset} ou {yellow}'autorizo'{reset} para prosseguir.\n")
        return "\n".join(header_lines + body)

    if is_terminal:
        # Terminal sem cores (NO_COLOR ativo)
        lines = [SOLID_BANNER_ASCII, f"\nMOTIVO: {clean_reason}"]
        if clean_context:
            lines.append(f"CONTEXTO: {clean_context}")
        lines.append("ACAO DO PO: Responda 'ok' ou 'autorizo' para prosseguir.\n")
        return "\n".join(lines)

    # Modo Markdown (padrão para chat, war_room.md e PRs)
    md_lines = [
        "```text",
        SOLID_BANNER_ASCII,
        "```",
        "> [!CAUTION]",
        "> **AUTORIZAÇÃO FORMAL DO PO NECESSÁRIA (CLÁUSULA PÉTREA)**",
        ">",
        f"> **Motivo:** {clean_reason}",
    ]
    if clean_context:
        md_lines.append(f"> **Contexto:** {clean_context}")
    md_lines.extend([
        ">",
        "> **Ação do PO:** responda **\"ok\"** ou **\"autorizo\"** para prosseguir.",
    ])
    return "\n".join(md_lines)
