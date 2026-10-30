"""Reviewed source metadata; never an authorization to execute a catalog entry.

Only packaged JSON and the native catalog are read. PDF files, external paths,
databases and campaign state are deliberately outside this loader's contract.
Callers retain responsibility for endpoint authorization and campaign overrides.
"""
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache
import json
from pathlib import Path
import re
from typing import Any

from .spell_catalog import get_catalog_spell


PROVENANCE_PATH = Path(__file__).resolve().parent / "data" / "catalog_provenance.json"


def _pages(value: Any, maximum: int) -> bool:
    return (isinstance(value, list) and bool(value)
            and all(type(page) is int and 1 <= page <= maximum for page in value)
            and value == sorted(set(value)))


@lru_cache(maxsize=1)
def load_catalog_provenance() -> dict[str, Any]:
    payload = json.loads(PROVENANCE_PATH.read_text(encoding="utf-8"))
    if not isinstance(payload, dict) or payload.get("schema_version") != 1:
        raise ValueError("Versão inválida do manifesto de fontes")
    sources, entries = payload.get("sources"), payload.get("entries")
    if not isinstance(sources, dict) or not sources or not isinstance(entries, list):
        raise ValueError("Manifesto de fontes incompleto")
    for source_id, source in sources.items():
        if not isinstance(source_id, str) or not source_id or not isinstance(source, dict):
            raise ValueError("Fonte inválida")
        required = ("title", "file_name", "edition", "version", "license", "license_url", "attribution")
        if any(not isinstance(source.get(key), str) or not source[key].strip() for key in required):
            raise ValueError("Metadados obrigatórios ausentes na fonte")
        name = source["file_name"]
        if any(separator in name for separator in ("/", "\\", ":")) or not name.lower().endswith(".pdf"):
            raise ValueError("Somente o nome base do PDF é permitido")
        if not isinstance(source.get("sha256"), str) or not re.fullmatch(r"[0-9a-f]{64}", source["sha256"]):
            raise ValueError("Hash de fonte inválido")
        if type(source.get("page_count")) is not int or source["page_count"] < 1:
            raise ValueError("Contagem de páginas inválida")
        if not _pages(source.get("metadata_physical_pages"), source["page_count"]):
            raise ValueError("Páginas de créditos inválidas")
    seen = set()
    for entry in entries:
        if not isinstance(entry, dict):
            raise ValueError("Referência inválida")
        identity = (entry.get("kind"), entry.get("catalog_id"))
        if identity[0] != "spell" or not isinstance(identity[1], str) or get_catalog_spell(identity[1]) is None:
            raise ValueError("Referência não encontrada no catálogo nativo")
        if identity in seen:
            raise ValueError("Referência de catálogo duplicada")
        seen.add(identity)
        source_id = entry.get("source_id")
        if not isinstance(source_id, str) or source_id not in sources:
            raise ValueError("Fonte da referência não encontrada")
        maximum = sources[source_id]["page_count"]
        if (not _pages(entry.get("physical_pages"), maximum)
                or not _pages(entry.get("printed_pages"), maximum)
                or len(entry["physical_pages"]) != len(entry["printed_pages"])):
            raise ValueError("Páginas da referência inválidas")
        if entry.get("review_state") != "source_verified" or entry.get("execution_approved") is not False:
            raise ValueError("Proveniência não pode aprovar execução")
    return payload


def list_catalog_provenance(kind: str | None = None) -> list[dict[str, Any]]:
    payload = load_catalog_provenance()
    return [deepcopy({**entry, "source": payload["sources"][entry["source_id"]]})
            for entry in payload["entries"] if kind is None or entry["kind"] == kind]


def get_catalog_provenance(kind: str, catalog_id: str) -> dict[str, Any] | None:
    return next((entry for entry in list_catalog_provenance(kind)
                 if entry["catalog_id"] == catalog_id), None)
