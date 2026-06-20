from __future__ import annotations

import subprocess
from pathlib import Path

from mcp.server.fastmcp import FastMCP

import assistant_bridge
import vault_tools


ROOT = Path(__file__).resolve().parents[1]
mcp = FastMCP("omnisvera-local")


@mcp.tool()
def get_handoff() -> str:
    """Retorna o objetivo, regras e próximo passo compartilhados entre Codex e Ollama."""
    return (ROOT / "Workflow" / "ASSISTANT_HANDOFF.md").read_text(encoding="utf-8-sig")


@mcp.tool()
def get_migration_status() -> str:
    """Retorna o registro versionado da migração de Disgraceland para Omnisvera."""
    return (ROOT / "Workflow" / "MIGRATION_LEDGER.md").read_text(encoding="utf-8-sig")


@mcp.tool()
def semantic_search(query: str, limit: int = 8) -> str:
    """Pesquisa o índice semântico local e retorna trechos com caminhos de origem."""
    rows = assistant_bridge.semantic_context(query, limit=limit)
    return "\n\n".join(
        f"{item['score']:.4f} | {item['path']}\n{item['text']}" for item in rows
    )


@mcp.tool()
def assistant_status() -> str:
    """Retorna estado Git e handoff atual sem modificar arquivos."""
    return assistant_bridge.status()


@mcp.tool()
def create_local_proposal(task: str, source_files: list[str]) -> str:
    """Gera proposta somente a partir de fontes explícitas, sem editar notas canônicas."""
    return str(assistant_bridge.propose(task, source_files))


@mcp.tool()
def audit_changed_notes() -> str:
    """Executa auditoria de YAML e wikilinks apenas nas notas modificadas."""
    result = subprocess.run(
        [
            str(ROOT / ".omnisvera-tools" / "Scripts" / "python.exe"),
            str(ROOT / ".local-tools" / "vault_tools.py"),
            "audit",
            "--changed",
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        check=False,
    )
    return result.stdout or result.stderr


if __name__ == "__main__":
    mcp.run(transport="stdio")
