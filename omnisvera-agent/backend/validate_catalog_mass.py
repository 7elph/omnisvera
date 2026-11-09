"""Validador de catálogo em massa para os 1452+ itens do Companion.

Processa TODAS as entradas de magias, habilidades, itens e monstros e gera
um relatório de exceções para o Mestre revisar apenas o que falhou.

Abordagem (tudo automático, sem revisão item a item):
1. Schema: campos obrigatórios preenchidos
2. Referências cruzadas: magias/itens nomeados entre aspas existem no catálogo

Saída: relatório JSON + console com apenas exceções.
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any


DATA_DIR = Path(r"C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent\backend\app\data")


def load_catalog(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    for key in ("spells", "abilities", "items", "monsters"):
        if isinstance(data.get(key), list):
            return data[key]
    if isinstance(data, list):
        return data
    raise ValueError(f"Não encontrei lista em {path}")


REQUIRED_FIELDS: dict[str, list[str]] = {
    "spell": ["id", "name", "circle", "tradition", "school", "description"],
    "ability": ["id", "title", "spec", "description"],
    "item": ["id", "category", "name", "description"],
    "monster": ["id", "name"],
}


def _has_meaningful_text(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, (int, float, bool)):
        return True
    if isinstance(value, str):
        return len(value.strip()) > 0
    if isinstance(value, (list, dict)):
        return len(value) > 0
    return True


def validate_schema(entry: dict, etype: str) -> list[str]:
    errors: list[str] = []
    required = REQUIRED_FIELDS.get(etype, [])
    for field in required:
        if field not in entry or entry[field] is None:
            errors.append(f"campo obrigatório ausente: {field}")
        elif not _has_meaningful_text(entry[field]):
            errors.append(f"campo vazio: {field}")
    return errors


def build_index(entries: list[dict]) -> dict[str, dict]:
    idx: dict[str, dict] = {}
    for e in entries:
        key = e.get("id") or e.get("name", "")
        if key:
            idx[str(key).lower()] = e
    return idx


# Referências só entre aspas duplas após "magia X", "conjurar X", "efeito de X"
# ou "item X", "objeto X", "artefato X". Evita capturar texto descritivo.
SPELL_REF_RE = re.compile(r'(?:magia|conjurar|efeito de)\s+"([^"]{3,40})"', re.IGNORECASE)
ITEM_REF_RE = re.compile(r'(?:item|objeto|artefato)\s+"([^"]{3,40})"', re.IGNORECASE)


def validate_spell_references(spell: dict, spell_index: dict) -> list[str]:
    errors: list[str] = []
    desc = spell.get("description", "") or ""
    for m in SPELL_REF_RE.finditer(desc):
        name = m.group(1).strip()
        if name.lower() not in spell_index:
            errors.append(f"magia referenciada não encontrada: {name}")
    return errors


def validate_item_references(item: dict, item_index: dict) -> list[str]:
    errors: list[str] = []
    desc = item.get("description", "") or ""
    for m in ITEM_REF_RE.finditer(desc):
        name = m.group(1).strip()
        if name.lower() not in item_index:
            errors.append(f"item referenciado não encontrado: {name}")
    return errors


def validate_all() -> dict[str, Any]:
    results: dict[str, Any] = {
        "total": 0,
        "by_type": {},
        "errors": [],
        "warnings": [],
    }

    catalogs = [
        ("spell", DATA_DIR / "old_dragon_spells.json"),
        ("ability", DATA_DIR / "old_dragon_abilities.json"),
        ("item", DATA_DIR / "old_dragon_items.json"),
        ("monster", DATA_DIR / "old_dragon_srd_monsters.json"),
    ]

    loaded: dict[str, list[dict]] = {}
    for etype, path in catalogs:
        try:
            loaded[etype] = load_catalog(path)
        except Exception as exc:
            results["errors"].append(f"não foi possível carregar {path.name}: {exc}")
            loaded[etype] = []

    spell_index = build_index(loaded.get("spell", []))
    item_index = build_index(loaded.get("item", []))

    for etype, path in catalogs:
        entries = loaded.get(etype, [])
        type_errors: list[str] = []
        type_warnings: list[str] = []

        for entry in entries:
            entry_id = entry.get("id", entry.get("name", "desconhecido"))

            # 1. Schema
            for e in validate_schema(entry, etype):
                type_errors.append(f"{etype}:{entry_id} — {e}")

            # 2. Referências cruzadas
            if etype == "spell":
                for e in validate_spell_references(entry, spell_index):
                    type_warnings.append(f"{etype}:{entry_id} — {e}")
            elif etype == "item":
                for e in validate_item_references(entry, item_index):
                    type_warnings.append(f"{etype}:{entry_id} — {e}")

        results["by_type"][etype] = {
            "total": len(entries),
            "errors": len(type_errors),
            "warnings": len(type_warnings),
        }
        results["total"] += len(entries)
        results["errors"].extend(type_errors)
        results["warnings"].extend(type_warnings)

    return results


def main() -> None:
    print("=== Validador de Catálogo em Massa ===")
    print("Carregando catálogos...")

    results = validate_all()

    print(f"\nTotal de entradas validadas: {results['total']}")
    print("\nPor tipo:")
    for etype, info in results["by_type"].items():
        print(f"  {etype}: {info['total']} itens | {info['errors']} erros | {info['warnings']} avisos")

    print(f"\nTotal de erros (bloqueantes): {len(results['errors'])}")
    print(f"Total de avisos (revisar): {len(results['warnings'])}")

    if results["errors"]:
        print("\n--- ERROS ---")
        for e in results["errors"]:
            print(f"  {e}")

    if results["warnings"]:
        print(f"\n--- AVISOS (primeiros 50 de {len(results['warnings'])}) ---")
        for w in results["warnings"][:50]:
            print(f"  {w}")

    report_path = Path(r"C:\Users\delib\Desktop\OMNISVERA\omnisvera-agent\backend\catalog_validation_report.json")
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\nRelatório salvo em: {report_path}")


if __name__ == "__main__":
    main()
