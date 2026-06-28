#!/usr/bin/env python
"""Passive environment check for the Omnisvera vault.

This script does not install, remove, or configure anything. It only reports
whether common local tools are available on PATH.
"""

from __future__ import annotations

import shutil
import subprocess
from dataclasses import dataclass


@dataclass(frozen=True)
class Tool:
    name: str
    command: str
    version_args: tuple[str, ...]
    required: bool = False


TOOLS = [
    Tool("Python", "python", ("--version",), True),
    Tool("Git", "git", ("--version",), True),
    Tool("PowerShell", "powershell", ("-NoProfile", "-Command", "$PSVersionTable.PSVersion.ToString()"), True),
    Tool("Ollama", "ollama", ("--version",), False),
    Tool("VS Code", "code", ("--version",), False),
    Tool("GitHub CLI", "gh", ("--version",), False),
    Tool("Git LFS", "git-lfs", ("version",), False),
    Tool("Tesseract", "tesseract", ("--version",), False),
    Tool("ImageMagick", "magick", ("--version",), False),
    Tool("FFmpeg", "ffmpeg", ("-version",), False),
    Tool("ExifTool", "exiftool", ("-ver",), False),
    Tool("jq", "jq", ("--version",), False),
    Tool("yq", "yq", ("--version",), False),
    Tool("ripgrep", "rg", ("--version",), False),
]


def version_line(tool: Tool) -> str:
    path = shutil.which(tool.command)
    if not path:
        return "MISSING"
    try:
        completed = subprocess.run(
            [path, *tool.version_args],
            check=False,
            capture_output=True,
            text=True,
            timeout=8,
        )
    except Exception as exc:  # pragma: no cover - diagnostic script
        return f"FOUND ({path}) but version check failed: {exc}"

    output = (completed.stdout or completed.stderr).strip().splitlines()
    first = output[0].strip() if output else "version unavailable"
    return f"FOUND ({path}) :: {first}"


def main() -> int:
    missing_required = []

    print("Omnisvera local environment check")
    print("No installation or configuration is performed.\n")

    for tool in TOOLS:
        status = version_line(tool)
        required = "required" if tool.required else "optional"
        print(f"[{required}] {tool.name}: {status}")
        if tool.required and status == "MISSING":
            missing_required.append(tool.name)

    if missing_required:
        print("\nMissing required tools:")
        for name in missing_required:
            print(f"- {name}")
        return 1

    print("\nRequired tools are available.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
