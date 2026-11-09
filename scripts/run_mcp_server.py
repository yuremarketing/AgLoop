#!/usr/bin/env python3
"""Thin entrypoint for .mcp.json: Claude Directory's validator rejects starting
a module by name (`-m core.mcp_server`), so this file is the literal path it follows."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mcp_server import main

if __name__ == "__main__":
    main()
