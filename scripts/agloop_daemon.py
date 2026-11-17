#!/usr/bin/env python3
"""
CLI de gerenciamento do AgLoop Host Daemon (Issue #74 / ADR-0008).
Fornece comandos start, stop, status e run para o supervisor de processos no host.
"""

import os
import sys

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.daemon import main

if __name__ == "__main__":
    main()
