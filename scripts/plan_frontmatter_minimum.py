#!/usr/bin/env python3
"""Planeja a migração futura de frontmatter mínimo Omnisvera.

Fase C0: auditoria e dry-run apenas.

O script não altera notas. Ele detecta campos existentes, infere `type` e
`subtype` prováveis quando o risco é baixo, e gera um plano para revisão.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


IGNORE_DIRS = {
    ".git",
    ".obsidian",
    "zz_media",
    "node_modules",
    ".codex-tools",
    ".local-tools",
    ".ollama",
    ".omnisvera-tools",
    ".local-index",
    ".smtcmp_json_db",
    ".tmp_refs",
}

SKIP_PREFIXES = (
    "Workflow/_audit/",
    "Workflow/_archive/",
    "Workflow/Legacy/",
)

MINIMUM_FIELDS = [
    "type",
    "subtype",
    "work_status",
    "canon_status",
    "visibility",
    "created_by",
    "requires_review",
]

OFFICIAL_TYPES = {
    "character",
    "location",
    "territory",
    "faction",
    "item",
    "lore",
    "religion",
    "race",
    "class",
    "session",
    "async_scene",
    "ai_npc",
    "workflow",
}

SPECIAL_RECLASSIFICATIONS = {
    "Items/O Frasco Afogado.md": (
        "location",
        "shop",
        "Reclassificação futura: é a loja de alquimia do Mestre Odran em Maré Baixa, não item portátil.",
    ),
}


@dataclass
class NotePlan:
    path: str
    has_frontmatter: bool
    yaml_valid: bool
    fields: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    current_type: str = ""
    suggested_type: str = ""
    current_subtype: str = ""
    suggested_subtype: str = ""
    missing_fields: list[str] = field(default_factory=list)
    risk: str = "skip"
    action: str = "no_action"
    observation: str = ""


def scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value == "[]":
        return []
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]
    if value.startswith("[") and value.endswith("]"):
        inner = value[1:-1].strip()
        if not inner:
            return []
        return [part.strip().strip('"').strip("'") for part in inner.split(",")]
    return value


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & IGNORE_DIRS:
            continue
        files.append(path)
    return sorted(files)


def extract_frontmatter(text: str) -> tuple[str | None, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, ["frontmatter ausente"]
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx]), []
    return None, ["frontmatter sem delimitador de fechamento"]


def parse_simple_yaml(raw: str) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {}
    errors: list[str] = []
    current_key: str | None = None
    for lineno, line in enumerate(raw.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_./'-]+:", line):
            key, value = line.split(":", 1)
            key = key.strip()
            data[key] = scalar(value)
            current_key = key
            continue
        if line.startswith("  - ") and current_key:
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(scalar(line[4:]))
            continue
        if line.startswith(" ") and current_key:
            continue
        errors.append(f"linha {lineno}: sintaxe YAML não reconhecida: {line[:80]}")
    return data, errors


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], bool, list[str]]:
    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw) or {}
            if not isinstance(parsed, dict):
                return {}, False, ["frontmatter não é mapa YAML"]
            return parsed, True, []
        except Exception as exc:  # noqa: BLE001
            parsed, simple_errors = parse_simple_yaml(raw)
            return parsed, False, [str(exc), *simple_errors]
    parsed, errors = parse_simple_yaml(raw)
    return parsed, not errors, errors


def get_tags(fields: dict[str, Any]) -> list[str]:
    tags = fields.get("tags") or []
    if isinstance(tags, str):
        return [tags]
    if isinstance(tags, list):
        return [str(tag) for tag in tags if tag is not None]
    return []


def infer_type(path: str, fields: dict[str, Any], tags: list[str]) -> tuple[str, str]:
    noteicon = str(fields.get("NoteIcon") or "").lower()
    tagset = set(tags)
    if path in SPECIAL_RECLASSIFICATIONS:
        t, _subtype, reason = SPECIAL_RECLASSIFICATIONS[path]
        return t, reason
    if path.startswith("Characters/"):
        return "character", "inferido pela pasta Characters."
    if path.startswith("Factions/"):
        return "faction", "inferido pela pasta Factions."
    if path.startswith("Territories/"):
        return "territory", "inferido pela pasta Territories."
    if path.startswith("Locations/"):
        return "location", "inferido pela pasta Locations."
    if path.startswith("Items/"):
        return "item", "inferido pela pasta Items."
    if path.startswith("Lore/"):
        return "lore", "inferido pela pasta Lore."
    if path.startswith("Religion/"):
        return "religion", "inferido pela pasta Religion."
    if path.startswith("Races/"):
        return "race", "inferido pela pasta Races."
    if path.startswith("Classes/"):
        return "class", "inferido pela pasta Classes."
    if path.startswith("Templates/TEMPLATE - Async Scene"):
        return "async_scene", "inferido pelo template-base Async Scene."
    if path.startswith("Templates/TEMPLATE - AI NPC"):
        return "ai_npc", "inferido pelo template-base AI NPC."
    if path.startswith("Templates/"):
        if "character" in tagset or "personagem" in tagset or "npc" in tagset:
            return "character", "inferido por tags de template de personagem."
        if "location" in tagset or "local" in tagset:
            return "location", "inferido por tags de template de local."
        if "faction" in tagset or "faccao" in tagset:
            return "faction", "inferido por tags de template de facção."
        if "item" in tagset:
            return "item", "inferido por tags de template de item."
        if "lore" in tagset:
            return "lore", "inferido por tags de template de lore."
        if "race" in tagset or "raca" in tagset:
            return "race", "inferido por tags de template de raça."
        if "class" in tagset or "classe" in tagset:
            return "class", "inferido por tags de template de classe."
    if path.startswith("Workflow/") or path in {"NOTES.md"}:
        return "workflow", "inferido pela pasta Workflow/documentação."
    if "character" in tagset or "personagem" in tagset or noteicon == "character":
        return "character", "inferido por tag/NoteIcon."
    if "location" in tagset or "local" in tagset or noteicon == "location":
        return "location", "inferido por tag/NoteIcon."
    if "territory" in tagset or "territorio" in tagset or noteicon == "territory":
        return "territory", "inferido por tag/NoteIcon."
    if "faction" in tagset or "faccao" in tagset or noteicon == "faction":
        return "faction", "inferido por tag/NoteIcon."
    if "religion" in tagset or "religiao" in tagset:
        return "religion", "inferido por tag."
    if "race" in tagset or "raca" in tagset:
        return "race", "inferido por tag."
    if "class" in tagset or "classe" in tagset:
        return "class", "inferido por tag."
    if "item" in tagset or noteicon in {"magicitem", "item"}:
        return "item", "inferido por tag/NoteIcon."
    if "lore" in tagset:
        return "lore", "inferido por tag."
    if "story" in tagset or "capitulo" in tagset:
        return "session", "inferido por tag narrativa; revisar porque `story` é mantida como ponte."
    return "", "não inferido com segurança."


def infer_subtype(path: str, suggested_type: str, fields: dict[str, Any], tags: list[str]) -> tuple[str, str]:
    tagset = set(tags)
    name = Path(path).stem.lower()
    if path in SPECIAL_RECLASSIFICATIONS:
        _t, subtype, reason = SPECIAL_RECLASSIFICATIONS[path]
        return subtype, reason
    if suggested_type == "character":
        if "jogador" in tagset or "player" in tagset:
            return "player_character", "tag de personagem jogador."
        if "antagonista" in tagset:
            return "antagonist", "tag antagonista em contexto de personagem."
        if "criatura" in tagset or "monstro" in tagset:
            return "creature", "tag criatura/monstro em contexto de personagem."
        if "npc-importante" in tagset:
            return "major_npc", "tag npc-importante."
        if "npc-menor" in tagset:
            return "minor_npc", "tag npc-menor."
        return "", "subtype de personagem precisa revisão."
    if suggested_type == "location":
        if name == "nimalis":
            return "city", "capital/cidade detectada; plano futuro: `role: capital`; `territory: [[Nimalia]]`."
        if "bairro" in tagset or "distrito" in tagset or name.startswith("bairro"):
            return "district", "bairro/distrito detectado."
        if "porto" in tagset or "porto" in name:
            return "port", "porto detectado."
        if "loja" in tagset or "estabelecimento" in tagset or "comercio" in tagset:
            return "shop", "loja/comércio detectado."
        if "ruinas" in tagset or "ruína" in name or "ruinas" in name:
            return "ruin", "ruína detectada."
        if "templo" in tagset or "templo" in name:
            return "temple", "templo detectado."
        if "floresta" in tagset or "bosque" in name:
            return "wilderness", "área selvagem detectada."
        if "vila" in tagset or "cidade" in tagset:
            return "settlement", "assentamento detectado."
        return "", "subtype de local precisa revisão."
    if suggested_type == "faction":
        if "guilda" in tagset or "guilda" in name:
            return "guild", "guilda detectada."
        if "culto" in tagset or "culto" in name:
            return "cult", "culto detectado."
        if "nobreza" in tagset or "nobreza" in name:
            return "noble_house", "nobreza/casas nobres detectadas."
        if "guarda" in tagset or "sentinelas" in name:
            return "military", "força militar/guarda detectada."
        if "coroa" in tagset or "coroa" in name:
            return "political", "instituição política detectada."
        return "", "subtype de facção precisa revisão."
    if suggested_type == "item":
        noteicon = str(fields.get("NoteIcon") or "").lower()
        if "artefato" in tagset:
            return "artifact", "artefato detectado."
        if "arma" in tagset or "machado" in tagset:
            return "weapon", "arma detectada."
        if "escudo" in tagset:
            return "armor", "escudo/armadura detectado."
        if "caderno" in tagset or "documento" in tagset:
            return "document", "documento detectado."
        if noteicon == "magicitem":
            return "magic_item", "NoteIcon magicitem."
        return "", "subtype de item precisa revisão."
    if suggested_type == "lore":
        if "cosmologia" in tagset:
            return "cosmology", "cosmologia detectada."
        if "misterio" in tagset:
            return "mystery", "mistério detectado."
        if "fenomeno" in tagset:
            return "concept", "fenômeno/conceito detectado."
        return "", "subtype de lore precisa revisão."
    return "", f"subtype para `{suggested_type}` não tem regra de baixo risco."


def classify_risk(path: str, fields: dict[str, Any], current_type: str, suggested_type: str, current_subtype: str, suggested_subtype: str, missing: list[str], observation: str) -> tuple[str, str]:
    if path.startswith(SKIP_PREFIXES):
        return "skip", "histórico/auditoria/legacy; não migrar automaticamente."
    if not suggested_type:
        return "skip", "sem type sugerido com segurança."
    if current_type and current_type != suggested_type:
        return "high", "type atual conflita com sugestão; precisa revisão humana."
    if path in SPECIAL_RECLASSIFICATIONS:
        return "high", "reclassificação futura; não aplicar como item."
    if current_subtype and suggested_subtype and current_subtype != suggested_subtype:
        return "medium", "subtype atual difere da sugestão; revisar antes."
    if missing and suggested_type in {"workflow", "session"}:
        return "medium", "documento/sessão requer decisão de padrão antes de lote."
    if "subtype" in missing and not suggested_subtype:
        return "medium", "subtype ausente sem inferência de baixo risco."
    if missing:
        return "low", "campos mínimos ausentes podem ser adicionados em lote futuro."
    return "skip", "frontmatter já contém campos mínimos auditados."


def audit_file(path: Path, root: Path) -> NotePlan:
    rel = str(path.relative_to(root)).replace("\\", "/")
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    raw, fm_errors = extract_frontmatter(text)
    if raw is None:
        return NotePlan(
            path=rel,
            has_frontmatter=False,
            yaml_valid=False,
            risk="skip",
            action="no_action",
            observation="; ".join(fm_errors),
        )
    fields, valid, errors = parse_frontmatter(raw)
    tags = get_tags(fields)
    current_type = str(fields.get("type") or "")
    current_subtype = str(fields.get("subtype") or "")
    suggested_type, type_reason = infer_type(rel, fields, tags)
    suggested_subtype, subtype_reason = infer_subtype(rel, suggested_type or current_type, fields, tags)
    missing = [field for field in MINIMUM_FIELDS if field not in fields]
    if not valid:
        return NotePlan(
            path=rel,
            has_frontmatter=True,
            yaml_valid=False,
            fields=fields,
            tags=tags,
            current_type=current_type,
            suggested_type=suggested_type,
            current_subtype=current_subtype,
            suggested_subtype=suggested_subtype,
            missing_fields=missing,
            risk="skip",
            action="no_action",
            observation="YAML inválido: " + "; ".join(errors),
        )
    risk, risk_reason = classify_risk(
        rel,
        fields,
        current_type,
        suggested_type,
        current_subtype,
        suggested_subtype,
        missing,
        type_reason,
    )
    action = "plan_add_missing_fields" if risk == "low" and missing else "review_before_apply"
    if risk == "skip":
        action = "no_action"
    observation = " ".join(part for part in [type_reason, subtype_reason, risk_reason] if part)
    return NotePlan(
        path=rel,
        has_frontmatter=True,
        yaml_valid=True,
        fields=fields,
        tags=tags,
        current_type=current_type,
        suggested_type=suggested_type,
        current_subtype=current_subtype,
        suggested_subtype=suggested_subtype,
        missing_fields=missing,
        risk=risk,
        action=action,
        observation=observation,
    )


def md_cell(value: str) -> str:
    return value.replace("|", "\\|").replace("\n", "<br>")


def render_report(root: Path, plans: list[NotePlan]) -> str:
    risk_counter = Counter(plan.risk for plan in plans)
    missing_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    subtype_counter: Counter[str] = Counter()
    for plan in plans:
        missing_counter.update(plan.missing_fields)
        if plan.current_type:
            type_counter[plan.current_type] += 1
        if plan.current_subtype:
            subtype_counter[plan.current_subtype] += 1
    with_frontmatter = sum(1 for plan in plans if plan.has_frontmatter)
    valid_yaml = sum(1 for plan in plans if plan.has_frontmatter and plan.yaml_valid)
    without_type = sum(1 for plan in plans if plan.has_frontmatter and "type" not in plan.fields)
    without_subtype = sum(1 for plan in plans if plan.has_frontmatter and "subtype" not in plan.fields)

    lines = [
        "# Omnisvera — Plano C0 de Frontmatter Mínimo",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "> [!IMPORTANT]",
        "> Este relatório é dry-run. Nenhuma nota foi alterada.",
        "> A futura Fase C1 deve adicionar campos Omnisvera mínimos preservando todos os campos legacy.",
        "",
        "## Resumo geral",
        "",
        "| métrica | valor |",
        "|---|---:|",
        f"| notas Markdown analisadas | {len(plans)} |",
        f"| notas com frontmatter | {with_frontmatter} |",
        f"| notas sem frontmatter | {len(plans) - with_frontmatter} |",
        f"| YAML/frontmatter válido | {valid_yaml} |",
        f"| YAML/frontmatter inválido | {with_frontmatter - valid_yaml} |",
        f"| notas com type | {with_frontmatter - without_type} |",
        f"| notas sem type | {without_type} |",
        f"| notas com subtype | {with_frontmatter - without_subtype} |",
        f"| notas sem subtype | {without_subtype} |",
        f"| candidatos low | {risk_counter.get('low', 0)} |",
        f"| candidatos medium | {risk_counter.get('medium', 0)} |",
        f"| candidatos high | {risk_counter.get('high', 0)} |",
        f"| pulados/skip | {risk_counter.get('skip', 0)} |",
        "",
        "## Campos mínimos ausentes",
        "",
        "| campo | ocorrências |",
        "|---|---:|",
    ]
    for field, count in missing_counter.most_common():
        lines.append(f"| `{field}` | {count} |")
    lines.extend(
        [
            "",
            "## Distribuição de `type` atual",
            "",
            "| type | notas |",
            "|---|---:|",
        ]
    )
    for value, count in type_counter.most_common():
        lines.append(f"| `{value}` | {count} |")
    lines.extend(
        [
            "",
            "## Distribuição de `subtype` atual",
            "",
            "| subtype | notas |",
            "|---|---:|",
        ]
    )
    for value, count in subtype_counter.most_common():
        lines.append(f"| `{value}` | {count} |")
    lines.extend(
        [
            "",
            "## Matriz por arquivo",
            "",
            "| Arquivo | Type atual | Type sugerido | Subtype atual | Subtype sugerido | Campos ausentes | Risco | Ação recomendada | Observação |",
            "|---|---|---|---|---|---|---|---|---|",
        ]
    )
    for plan in plans:
        lines.append(
            "| "
            + " | ".join(
                md_cell(value)
                for value in [
                    f"`{plan.path}`",
                    f"`{plan.current_type}`" if plan.current_type else "",
                    f"`{plan.suggested_type}`" if plan.suggested_type else "",
                    f"`{plan.current_subtype}`" if plan.current_subtype else "",
                    f"`{plan.suggested_subtype}`" if plan.suggested_subtype else "",
                    ", ".join(f"`{field}`" for field in plan.missing_fields),
                    plan.risk,
                    plan.action,
                    plan.observation,
                ]
            )
            + " |"
        )
    lines.extend(
        [
            "",
            "## Casos especiais",
            "",
            "- `Items/O Frasco Afogado.md`: marcar como reclassificação futura para `location/shop`; não aplicar como item.",
            "- `Factions/Culto dos Sussurrantes.md`: manter como `faction`; não receber `character` automaticamente por causa da tag `antagonista`.",
            "- `Workflow/_audit/*`: tratado como histórico/auditoria; não migrar automaticamente.",
            "- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`: ignorado; não é Markdown e está fora do escopo.",
            "",
            "## Recomendação para Fase C1",
            "",
            "Aplicar primeiro apenas os casos `low`, em lote pequeno, adicionando campos ausentes sem remover campos legacy.",
            "Casos `medium` e `high` precisam revisão do Sage antes de qualquer alteração.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Planeja frontmatter mínimo Omnisvera sem alterar notas.")
    parser.add_argument("--root", default=".", help="Raiz do vault/repositório.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_PLAN.md",
        help="Arquivo Markdown de saída.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = root / args.output
    plans = [audit_file(path, root) for path in iter_markdown_files(root)]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_report(root, plans), encoding="utf-8")
    risk_counter = Counter(plan.risk for plan in plans)
    print(f"Notas analisadas: {len(plans)}")
    print(f"low={risk_counter.get('low', 0)} medium={risk_counter.get('medium', 0)} high={risk_counter.get('high', 0)} skip={risk_counter.get('skip', 0)}")
    print(f"Relatório: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
