#!/usr/bin/env python3
"""Aplica, de forma conservadora, tags oficiais Omnisvera de baixo risco.

Por padrao, roda em dry-run. Use ``--apply`` para gravar alteracoes.

Regras:
- nunca remove tags;
- nunca renomeia tags;
- nunca altera corpo da nota;
- so edita frontmatter com ``tags`` em lista YAML simples;
- pula casos ambiguos, historicos, auditorias e formatos complexos.
"""

from __future__ import annotations

import argparse
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


LOW_RISK_ALWAYS = {
    "local": "location",
    "faccao": "faction",
    "raca": "race",
    "religiao": "religion",
    "territorio": "territory",
    "classe": "class",
    "Category/Location": "location",
    "Category/Lore": "lore",
    "Category/Character": "character",
}

LOW_RISK_CHARACTER_CONTEXT_ONLY = {
    "personagem": "character",
    "npc": "character",
    "jogador": "character",
    "antagonista": "character",
    "criatura": "character",
}

NEVER_APPLY_TAGS = {
    "Category/Settlement",
    "story",
    "bside",
    "old-dragon",
}

SKIP_PREFIXES = (
    "Workflow/_audit/",
    "Workflow/_archive/",
    "Workflow/Legacy/",
)


@dataclass
class PlanRow:
    path: str
    relevant_tags: list[str]
    official_tags: list[str]
    preserved_tags: list[str]
    risk: str
    observation: str


@dataclass
class ApplyResult:
    path: str
    relevant_tags: list[str] = field(default_factory=list)
    added_tags: list[str] = field(default_factory=list)
    preserved_tags: list[str] = field(default_factory=list)
    risk: str = "low"
    observation: str = ""
    skipped: bool = False
    skip_reason: str = ""


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


def read_map_actions(map_path: Path) -> dict[tuple[str, str], tuple[str, str]]:
    """Retorna (tag_atual, tag_oficial) -> (acao, risco)."""
    actions: dict[tuple[str, str], tuple[str, str]] = {}
    if not map_path.exists():
        return actions
    for line in map_path.read_text(encoding="utf-8", errors="replace").splitlines():
        cells = split_markdown_row(line)
        if len(cells) != 6 or cells[0] in {"Tag encontrada", "---"}:
            continue
        found = extract_backtick_values(cells[0])
        official = extract_backtick_values(cells[2])
        if not found or not official:
            continue
        actions[(found[0], official[0])] = (cells[3], cells[4])
    return actions


def read_low_risk_plan(plan_path: Path) -> list[PlanRow]:
    rows: list[PlanRow] = []
    if not plan_path.exists():
        return rows
    in_low_section = False
    for line in plan_path.read_text(encoding="utf-8", errors="replace").splitlines():
        if line.startswith("## Baixo risco"):
            in_low_section = True
            continue
        if line.startswith("## Medio risco") or line.startswith("## Médio risco"):
            break
        if not in_low_section:
            continue
        cells = split_markdown_row(line)
        if len(cells) != 6 or cells[0] in {"Arquivo", "---"}:
            continue
        path_values = extract_backtick_values(cells[0])
        if not path_values:
            continue
        rows.append(
            PlanRow(
                path=path_values[0],
                relevant_tags=extract_backtick_values(cells[1]),
                official_tags=extract_backtick_values(cells[2]),
                preserved_tags=extract_backtick_values(cells[3]),
                risk=cells[4],
                observation=cells[5],
            )
        )
    return rows


def is_character_context(path: str) -> bool:
    return path.startswith("Characters/") or path.startswith("Templates/Characters/")


def is_skipped_path(path: str) -> bool:
    return path.startswith(SKIP_PREFIXES)


def allowed_additions(row: PlanRow, map_actions: dict[tuple[str, str], tuple[str, str]]) -> tuple[dict[str, str], list[str]]:
    additions: dict[str, str] = {}
    reasons: list[str] = []
    if row.risk != "low":
        return additions, [f"risco `{row.risk}` nao e baixo"]
    for tag in row.relevant_tags:
        if tag in NEVER_APPLY_TAGS:
            reasons.append(f"`{tag}` e tag preservada/ambigua")
            continue
        official = LOW_RISK_ALWAYS.get(tag)
        if official is None and tag in LOW_RISK_CHARACTER_CONTEXT_ONLY:
            if is_character_context(row.path):
                official = LOW_RISK_CHARACTER_CONTEXT_ONLY[tag]
            else:
                reasons.append(f"`{tag}` so e seguro em contexto de personagem")
                continue
        if official is None:
            reasons.append(f"`{tag}` nao esta na lista conservadora de aplicacao")
            continue
        action, risk = map_actions.get((tag, official), ("", ""))
        if action != "add_official_tag" or risk != "low":
            reasons.append(f"`{tag}` -> `{official}` nao esta como add_official_tag/low no mapa")
            continue
        if official not in row.official_tags:
            reasons.append(f"`{official}` nao aparece no plano para `{tag}`")
            continue
        additions[tag] = official
    return additions, reasons


def extract_frontmatter(text: str) -> tuple[list[str], list[str], list[str]] | None:
    lines = text.splitlines(keepends=True)
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return lines[: idx + 1], lines[1:idx], lines[idx + 1 :]
    return None


def yaml_is_valid(fm_lines: list[str]) -> tuple[bool, str]:
    raw = "".join(fm_lines)
    if yaml is None:
        return True, "PyYAML indisponivel; validacao estrutural simples"
    try:
        parsed = yaml.safe_load(raw) or {}
    except Exception as exc:  # noqa: BLE001
        return False, f"YAML invalido: {exc}"
    if not isinstance(parsed, dict):
        return False, "frontmatter nao e mapa YAML"
    return True, ""


def find_simple_tags_block(fm_lines: list[str]) -> tuple[int, int, str, list[str]] | None:
    tags_key_idx: int | None = None
    for idx, line in enumerate(fm_lines):
        if re.match(r"^tags:\s*$", line):
            tags_key_idx = idx
            break
        if re.match(r"^tags:\s*\S+", line):
            return None
    if tags_key_idx is None:
        return None

    item_indices: list[int] = []
    tags: list[str] = []
    indent = "  "
    for idx in range(tags_key_idx + 1, len(fm_lines)):
        line = fm_lines[idx]
        if re.match(r"^[A-Za-z0-9_./'-]+:", line):
            break
        match = re.match(r"^(\s*)-\s+(.+?)\s*$", line)
        if match:
            indent = match.group(1)
            value = match.group(2).strip().strip('"').strip("'")
            tags.append(value)
            item_indices.append(idx)
            continue
        if line.strip() == "":
            continue
        if line.startswith(" "):
            return None
        break
    if not item_indices:
        return None
    return tags_key_idx, item_indices[-1], indent, tags


def apply_to_file(root: Path, row: PlanRow, additions: dict[str, str], do_apply: bool) -> ApplyResult:
    path = root / row.path
    result = ApplyResult(
        path=row.path,
        relevant_tags=sorted(additions.keys()),
        preserved_tags=sorted(additions.keys()),
        risk=row.risk,
        observation=row.observation,
    )
    if not path.exists():
        result.skipped = True
        result.skip_reason = "arquivo nao encontrado"
        return result
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    extracted = extract_frontmatter(text)
    if extracted is None:
        result.skipped = True
        result.skip_reason = "frontmatter ausente ou sem fechamento"
        return result
    full_fm, inner_fm, body = extracted
    valid, reason = yaml_is_valid(inner_fm)
    if not valid:
        result.skipped = True
        result.skip_reason = reason
        return result
    block = find_simple_tags_block(inner_fm)
    if block is None:
        result.skipped = True
        result.skip_reason = "campo tags ausente, inline ou complexo"
        return result
    _tags_key_idx, last_item_idx, indent, current_tags = block
    current = set(current_tags)
    to_add = sorted({official for official in additions.values() if official not in current})
    if not to_add:
        result.skipped = True
        result.skip_reason = "tags oficiais ja presentes"
        return result
    result.added_tags = to_add
    if do_apply:
        newline = "\n"
        if inner_fm[last_item_idx].endswith("\r\n"):
            newline = "\r\n"
        insert_at_full_fm = last_item_idx + 1 + 1  # + abertura ---
        new_lines = full_fm[:insert_at_full_fm]
        new_lines.extend(f"{indent}- {tag}{newline}" for tag in to_add)
        new_lines.extend(full_fm[insert_at_full_fm:])
        path.write_text("".join(new_lines + body), encoding="utf-8")
    return result


def render_report(mode: str, total_plan_rows: int, results: list[ApplyResult], skipped_reasons: list[str]) -> str:
    applied = [result for result in results if not result.skipped and result.added_tags]
    skipped = [result for result in results if result.skipped]
    added_count = sum(len(result.added_tags) for result in applied)
    official_added = sorted({tag for result in applied for tag in result.added_tags})

    lines = [
        "# Omnisvera — Tags Oficiais Aplicadas com Segurança",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        f"Modo executado: `{mode}`",
        "",
        "> [!IMPORTANT]",
        "> Esta etapa apenas adiciona tags oficiais. Nenhuma tag legacy deve ser removida.",
        "",
        "## Resumo",
        "",
        "| metrica | valor |",
        "|---|---:|",
        f"| linhas de plano analisadas | {total_plan_rows} |",
        f"| arquivos alterados/aplicaveis | {len(applied)} |",
        f"| tags oficiais adicionadas/aplicaveis | {added_count} |",
        f"| arquivos pulados | {len(skipped)} |",
        "",
        "Tags oficiais adicionadas/aplicaveis:",
        "",
        *(f"- `{tag}`" for tag in official_added),
        "",
        "## Arquivos alterados/aplicaveis",
        "",
        "| arquivo | tags antigas relevantes | tags oficiais adicionadas | tags preservadas | risco | observacao |",
        "|---|---|---|---|---|---|",
    ]
    if applied:
        for result in applied:
            lines.append(
                "| "
                + " | ".join(
                    [
                        f"`{result.path}`",
                        ", ".join(f"`{tag}`" for tag in result.relevant_tags),
                        ", ".join(f"`{tag}`" for tag in result.added_tags),
                        ", ".join(f"`{tag}`" for tag in result.preserved_tags),
                        result.risk,
                        result.observation.replace("|", "\\|"),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| _nenhum_ |  |  |  |  |  |")
    lines.extend(
        [
            "",
            "## Arquivos pulados",
            "",
            "| arquivo | motivo |",
            "|---|---|",
        ]
    )
    if skipped:
        for result in skipped:
            lines.append(f"| `{result.path}` | {result.skip_reason.replace('|', '\\|')} |")
    else:
        lines.append("| _nenhum_ |  |")
    if skipped_reasons:
        lines.extend(["", "## Motivos gerais de pulo", ""])
        for reason in skipped_reasons:
            lines.append(f"- {reason}")
    lines.extend(
        [
            "",
            "## Proximos passos",
            "",
            "- Revisar o diff das notas alteradas.",
            "- Rodar auditoria global e plano dry-run novamente.",
            "- Confirmar que a quantidade de candidatas diminuiu.",
            "- Nao remover tags legacy nesta fase.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Aplica tags oficiais Omnisvera de baixo risco.")
    parser.add_argument("--root", default=".", help="Raiz do vault/repositorio.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_APPLIED.md",
        help="Relatorio Markdown de saida.",
    )
    parser.add_argument("--apply", action="store_true", help="Grava alteracoes nas notas.")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = root / args.output
    map_path = root / "Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_MAP.md"
    plan_path = root / "Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_PLAN.md"
    map_actions = read_map_actions(map_path)
    rows = read_low_risk_plan(plan_path)

    results: list[ApplyResult] = []
    general_skip_reasons: list[str] = []
    for row in rows:
        if is_skipped_path(row.path):
            results.append(
                ApplyResult(
                    path=row.path,
                    relevant_tags=row.relevant_tags,
                    preserved_tags=row.preserved_tags,
                    risk=row.risk,
                    observation=row.observation,
                    skipped=True,
                    skip_reason="arquivo em area de auditoria, archive ou legacy",
                )
            )
            continue
        additions, reasons = allowed_additions(row, map_actions)
        if reasons:
            general_skip_reasons.extend(f"{row.path}: {reason}" for reason in reasons)
        if not additions:
            results.append(
                ApplyResult(
                    path=row.path,
                    relevant_tags=row.relevant_tags,
                    preserved_tags=row.preserved_tags,
                    risk=row.risk,
                    observation=row.observation,
                    skipped=True,
                    skip_reason="nenhuma adicao segura autorizada",
                )
            )
            continue
        results.append(apply_to_file(root, row, additions, args.apply))

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        render_report("apply" if args.apply else "dry-run", len(rows), results, sorted(set(general_skip_reasons))),
        encoding="utf-8",
    )
    applied = [result for result in results if not result.skipped and result.added_tags]
    added = sum(len(result.added_tags) for result in applied)
    print(f"Modo: {'apply' if args.apply else 'dry-run'}")
    print(f"Linhas de plano: {len(rows)}")
    print(f"Arquivos aplicaveis/alterados: {len(applied)}")
    print(f"Tags oficiais aplicaveis/adicionadas: {added}")
    print(f"Relatorio: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
