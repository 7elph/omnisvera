"""Compatibilidade: executa o auditor atual do vault."""

from __future__ import annotations

import subprocess
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON = ROOT / ".omnisvera-tools" / "Scripts" / "python.exe"
AUDITOR = ROOT / ".local-tools" / "vault_tools.py"


raise SystemExit(
    subprocess.call([str(PYTHON), str(AUDITOR), "audit"], cwd=ROOT)
)
