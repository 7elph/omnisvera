#!/usr/bin/env python3
"""Aplica frontmatter mínimo Omnisvera em lote seguro.

Por padrão roda em dry-run. Use `--apply` para gravar alterações.
O script é conservador: não remove campos, não altera tags, não altera corpo e
pula qualquer arquivo que já esteja modificado no `git status`.
"""

from __future__ import annotations

import argparse
import re
import subprocess
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


MINIMUM_FIELDS = [
    "type",
    "subtype",
    "work_status",
    "canon_status",
    "visibility",
    "created_by",
    "requires_review",
]

CHARACTER_SUBTYPES = {
    "player_character",
    "major_npc",
    "minor_npc",
    "antagonist",
    "creature",
}

LOCATION_SUBTYPES = {
    "city",
    "district",
    "shop",
    "port",
    "ruin",
    "temple",
    "wilderness",
    "dungeon",
    "settlement",
}

FACTION_SUBTYPES = {
    "military",
    "religious",
    "criminal",
    "guild",
    "noble_house",
    "mercantile",
    "rebel",
    "political",
}

ALLOWED_SUBTYPES_BY_TYPE = {
    "character": CHARACTER_SUBTYPES,
    "location": LOCATION_SUBTYPES,
    "faction": FACTION_SUBTYPES,
}


@dataclass
class PlanRow:
    path: str
    current_type: str
    suggested_type: str
    current_subtype: str
    suggested_subtype: str
    missing_fields: list[str]
    risk: str
    action: str
    observation: str


@dataclass
class ApplyResult:
    path: str
    eligible: bool = False
    changed: bool = False
    skipped: bool = False
    skip_reason: str = ""
    added_fields: dict[str, str] = field(default_factory=dict)
    preserved_legacy_fields: list[str] = field(default_factory=list)
    body_changed: bool = False
    tags_changed: bool = False
    fields_removed: bool = False


def split_markdown_row(line: str) -> list[str]:
    line = line.strip()
    if not line.startswith("|") or not line.endswith("|"):
        return []
    cells: list[str] = []
    current: list[str] = []
    escaped = False
    for char in line[1:-1]:
        if escaped:
            current.append(char)
            escaped = False
            continue
        if char == "\\":
            escaped = True
            current.append(char)
            continue
        if char == "|":
            cells.append("".join(current).strip())
            current = []
            continue
        current.append(char)
    cells.append("".join(current).strip())
    return cells


def extract_backtick_values(cell: str) -> list[str]:
    return [value.strip() for value in re.findall(r"`([^`]+)`", cell)]


def read_plan(plan_path: Path) -> list[PlanRow]:
    rows: list[PlanRow] = []
    if not plan_path.exists():
        return rows
    for line in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = split_markdown_row(line)
        if len(cells) != 9 or cells[0] in {"Arquivo", "---"}:
            continue
        path_values = extract_backtick_values(cells[0])
        if not path_values:
            continue
        current_type = (extract_backtick_values(cells[1]) or [""])[0]
        suggested_type = (extract_backtick_values(cells[2]) or [""])[0]
        current_subtype = (extract_backtick_values(cells[3]) or [""])[0]
        suggested_subtype = (extract_backtick_values(cells[4]) or [""])[0]
        rows.append(
            PlanRow(
                path=path_values[0].replace("\\", "/"),
                current_type=current_type,
                suggested_type=suggested_type,
                current_subtype=current_subtype,
                suggested_subtype=suggested_subtype,
                missing_fields=extract_backtick_values(cells[5]),
                risk=cells[6],
                action=cells[7],
                observation=cells[8],
            )
        )
    return rows


def git_dirty_paths(root: Path) -> set[str]:
    try:
        raw = subprocess.check_output(
            ["git", "status", "--porcelain=v1", "-z"],
            cwd=root,
        )
    except Exception:  # noqa: BLE001
        return set()
    dirty: set[str] = set()
    entries = raw.decode("utf-8", errors="replace").split("\0")
    idx = 0
    while idx < len(entries):
        entry = entries[idx]
        idx += 1
        if not entry:
            continue
        status = entry[:2]
        path = entry[3:].replace("\\", "/")
        if not path:
            continue
        if status.startswith("R") or status.startswith("C"):
            # Porcelain -z usa dois caminhos para rename/copy. Pula o destino extra.
            if idx < len(entries):
                idx += 1
        dirty.add(path)
    return dirty


def extract_frontmatter_with_body(text: str) -> tuple[list[str], list[str], list[str]] | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[: idx + 1], lines[1:idx], lines[idx + 1 :]
    return None


def parse_frontmatter(fm_lines: list[str]) -> tuple[dict[str, Any], bool, str]:
    raw = "".join(fm_lines)
    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw) or {}
            if not isinstance(parsed, dict):
                return {}, False, "frontmatter não é mapa YAML"
            return parsed, True, ""
        except Exception as exc:  # noqa: BLE001
            return {}, False, f"YAML inválido: {exc}"
    # Fallback simples só para presença de campos top-level.
    data: dict[str, Any] = {}
    for line in raw.splitlines():
        if re.match(r"^[A-Za-z0-9_./'-]+:", line):
            key, value = line.split(":", 1)
            data[key.strip()] = value.strip() or None
    return data, True, ""


def tags_from_fields(fields: dict[str, Any]) -> list[str]:
    tags = fields.get("tags") or []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [str(tag) for tag in tags if tag is not None]
    return []


def note_status_value(fields: dict[str, Any]) -> str:
    return str(fields.get("NoteStatus") or "").strip().lower()


def safe_suggested_subtype(row: PlanRow) -> str:
    if row.suggested_type == "faction" and row.suggested_subtype == "cult":
        return "religious"
    return row.suggested_subtype


def field_value(field: str, row: PlanRow, fields: dict[str, Any]) -> str | None:
    status = note_status_value(fields)
    if field == "type":
        if row.suggested_type in ALLOWED_SUBTYPES_BY_TYPE:
            return row.suggested_type
        return None
    if field == "subtype":
        suggested_subtype = safe_suggested_subtype(row)
        if suggested_subtype in ALLOWED_SUBTYPES_BY_TYPE.get(row.suggested_type, set()):
            return suggested_subtype
        return None
    if field == "work_status":
        if status in {"draft", "placeholder", "active"}:
            return "Em desenvolvimento"
        return "Em desenvolvimento"
    if field == "canon_status":
        if status == "active":
            return "Working Canon"
        if status in {"draft", "placeholder"}:
            return "Draft"
        return "Draft"
    if field == "visibility":
        return "Mestre"
    if field == "created_by":
        return "Sage"
    if field == "requires_review":
        return "true"
    return None


def insertion_index(full_fm: list[str]) -> int:
    """Retorna índice no frontmatter completo, antes de tags se possível."""
    for idx, line in enumerate(full_fm):
        if re.match(r"^tags:\s*$", line):
            return idx
    # Antes do delimitador final.
    return max(1, len(full_fm) - 1)


def detect_newline(lines: list[str]) -> str:
    for line in lines:
        if line.endswith("\r\n"):
            return "\r\n"
    return "\n"


def apply_row(root: Path, row: PlanRow, do_apply: bool, dirty: set[str]) -> ApplyResult:
    result = ApplyResult(path=row.path)
    path = root / row.path
    if row.path in dirty:
        result.skipped = True
        result.skip_reason = "DIRTY_PREEXISTING"
        return result
    if not path.exists():
        result.skipped = True
        result.skip_reason = "arquivo não encontrado"
        return result
    if row.risk != "low":
        result.skipped = True
        result.skip_reason = f"risco {row.risk}; somente low permitido"
        return result
    if row.action != "plan_add_missing_fields":
        result.skipped = True
        result.skip_reason = f"ação `{row.action}` não é aplicação segura"
        return result
    if row.suggested_type not in ALLOWED_SUBTYPES_BY_TYPE:
        result.skipped = True
        result.skip_reason = f"type sugerido `{row.suggested_type}` não é suportado por este aplicador"
        return result
    if row.current_type and row.current_type != row.suggested_type:
        result.skipped = True
        result.skip_reason = f"type atual conflita com `{row.suggested_type}`"
        return result
    if row.path == "Locations/Nimalis.md" and row.suggested_subtype == "settlement":
        result.skipped = True
        result.skip_reason = "Nimalis é capital; sugestão `settlement` precisa revisão antes de aplicar"
        return result
    suggested_subtype = safe_suggested_subtype(row)
    if not suggested_subtype or suggested_subtype not in ALLOWED_SUBTYPES_BY_TYPE.get(row.suggested_type, set()):
        result.skipped = True
        result.skip_reason = "subtype ausente, ambíguo ou fora da lista permitida"
        return result

    text = path.read_text(encoding="utf-8-sig", errors="replace")
    extracted = extract_frontmatter_with_body(text)
    if extracted is None:
        result.skipped = True
        result.skip_reason = "sem frontmatter válido"
        return result
    full_fm, inner_fm, body = extracted
    fields, valid, reason = parse_frontmatter(inner_fm)
    if not valid:
        result.skipped = True
        result.skip_reason = reason
        return result

    before_fields = set(fields)
    before_tags = tags_from_fields(fields)
    additions: dict[str, str] = {}
    for field in MINIMUM_FIELDS:
        if field in fields:
            continue
        if field not in row.missing_fields:
            continue
        value = field_value(field, row, fields)
        if value is None:
            result.skipped = True
            result.skip_reason = f"sem valor seguro para `{field}`"
            return result
        additions[field] = value

    if not additions:
        result.skipped = True
        result.skip_reason = "nenhum campo ausente aplicável"
        return result

    result.eligible = True
    result.added_fields = additions
    result.preserved_legacy_fields = sorted(
        field
        for field in [
            "obsidianUIMode",
            "NoteIcon",
            "NoteStatus",
            "status",
            "cover",
            "thumbnail",
            "portrait",
            "tags",
            "cssclasses",
        ]
        if field in fields
    )

    if do_apply:
        newline = detect_newline(full_fm)
        insert_at = insertion_index(full_fm)
        new_lines = full_fm[:insert_at]
        for field in MINIMUM_FIELDS:
            if field in additions:
                new_lines.append(f"{field}: {additions[field]}{newline}")
        new_lines.extend(full_fm[insert_at:])
        new_text = "".join(new_lines + body)

        # Checagens contra alteração de corpo/tags/remoção de campos.
        new_extracted = extract_frontmatter_with_body(new_text)
        if new_extracted is None:
            result.skipped = True
            result.skip_reason = "nova montagem perdeu frontmatter"
            return result
        _new_full_fm, new_inner_fm, new_body = new_extracted
        new_fields, new_valid, new_reason = parse_frontmatter(new_inner_fm)
        if not new_valid:
            result.skipped = True
            result.skip_reason = f"nova montagem gerou YAML inválido: {new_reason}"
            return result
        result.body_changed = body != new_body
        result.tags_changed = before_tags != tags_from_fields(new_fields)
        result.fields_removed = not before_fields.issubset(set(new_fields))
        if result.body_changed or result.tags_changed or result.fields_removed:
            result.skipped = True
            result.skip_reason = "checagem de segurança falhou antes de gravar"
            return result
        path.write_text(new_text, encoding="utf-8")
        result.changed = True
    return result


def render_report(
    mode: str,
    folder: str,
    risk: str,
    total_in_folder: int,
    results: list[ApplyResult],
) -> str:
    changed_or_applicable = [r for r in results if r.eligible and r.added_fields]
    changed = [r for r in changed_or_applicable if r.changed or mode == "dry-run"]
    skipped = [r for r in results if r.skipped]
    added_field_counter: dict[str, int] = {}
    subtype_counter: dict[str, int] = {}
    for result in changed_or_applicable:
        for field, value in result.added_fields.items():
            added_field_counter[field] = added_field_counter.get(field, 0) + 1
            if field == "subtype":
                subtype_counter[value] = subtype_counter.get(value, 0) + 1
    lines = [
        "# Omnisvera — Frontmatter Mínimo Aplicado",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Modo: `{mode}`",
        f"Filtro: `{folder}` / risco `{risk}`",
        "",
        "> [!IMPORTANT]",
        "> Esta etapa só adiciona campos Omnisvera mínimos em notas limpas do filtro informado.",
        "> Campos legacy, tags e corpo das notas devem permanecer preservados.",
        "",
        "## Resumo",
        "",
        "| métrica | valor |",
        "|---|---:|",
        f"| arquivos do filtro no plano | {total_in_folder} |",
        f"| elegíveis | {len(changed_or_applicable)} |",
        f"| alterados/aplicáveis | {len(changed)} |",
        f"| pulados | {len(skipped)} |",
        "",
        "## Campos adicionados/aplicáveis",
        "",
        "| campo | ocorrências |",
        "|---|---:|",
    ]
    for field, count in sorted(added_field_counter.items()):
        lines.append(f"| `{field}` | {count} |")
    lines.extend(["", "## Subtypes adicionados/aplicáveis", "", "| subtype | ocorrências |", "|---|---:|"])
    for subtype, count in sorted(subtype_counter.items()):
        lines.append(f"| `{subtype}` | {count} |")
    lines.extend(
        [
            "",
            "## Arquivos alterados/aplicáveis",
            "",
            "| arquivo | campos adicionados | valores | campos legacy preservados |",
            "|---|---|---|---|",
        ]
    )
    if changed_or_applicable:
        for result in changed_or_applicable:
            fields = ", ".join(f"`{field}`" for field in result.added_fields)
            values = ", ".join(f"`{field}: {value}`" for field, value in result.added_fields.items())
            legacy = ", ".join(f"`{field}`" for field in result.preserved_legacy_fields)
            lines.append(f"| `{result.path}` | {fields} | {values} | {legacy} |")
    else:
        lines.append("| _nenhum_ |  |  |  |")
    lines.extend(["", "## Arquivos pulados", "", "| arquivo | motivo |", "|---|---|"])
    if skipped:
        for result in skipped:
            lines.append(f"| `{result.path}` | {result.skip_reason} |")
    else:
        lines.append("| _nenhum_ |  |")
    lines.extend(
        [
            "",
            "## Garantias verificadas",
            "",
            "- Nenhum campo existente deve ser removido.",
            "- Nenhuma tag deve ser removida ou alterada.",
            "- O corpo da nota deve permanecer inalterado.",
            "- Arquivos `DIRTY_PREEXISTING` são pulados.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica frontmatter mínimo Omnisvera de baixo risco.")
    parser.add_argument("--root", default=".", help="Raiz do vault/repositório.")
    parser.add_argument("--folder", required=True, help="Pasta alvo, ex.: Characters/Individual")
    parser.add_argument("--risk", default="low", help="Risco permitido.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_APPLIED_C1A.md",
        help="Relatório Markdown de saída.",
    )
    parser.add_argument("--apply", action="store_true", help="Grava alterações.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    folder = args.folder.replace("\\", "/").rstrip("/")
    plan_path = root / "Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_PLAN.md"
    output = root / args.output
    dirty = git_dirty_paths(root)
    rows = [
        row
        for row in read_plan(plan_path)
        if row.path.startswith(folder + "/") and row.risk == args.risk
    ]
    results = [apply_row(root, row, args.apply, dirty) for row in rows]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_report("apply" if args.apply else "dry-run", folder, args.risk, len(rows), results),
        encoding="utf-8",
    )
    applicable = [r for r in results if r.eligible and r.added_fields]
    skipped = [r for r in results if r.skipped]
    print(f"Modo: {'apply' if args.apply else 'dry-run'}")
    print(f"Arquivos no filtro/plano: {len(rows)}")
    print(f"Elegíveis: {len(applicable)}")
    print(f"Pulados: {len(skipped)}")
    print(f"Relatório: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
