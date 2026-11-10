#!/usr/bin/env python3
"""Thin entrypoint for .mcp.json: Claude Directory's validator rejects starting
a module by name (`-m core.mcp_server`), so this file is the literal path it follows.

Imports `core.mcp_server` as an installed package rather than reaching outside
this plugin folder via `sys.path` — the Claude Directory validator blocks any
component path that climbs above the plugin folder (Issue #28)."""

import sys

try:
    from core.mcp_server import main
except ModuleNotFoundError:
    print(
        "Erro: o pacote 'agloop' não foi encontrado. "
        "Instale com 'pip install agloop' ou 'pip install -e .'",
        file=sys.stderr,
    )
    sys.exit(1)

if __name__ == "__main__":
    main()
