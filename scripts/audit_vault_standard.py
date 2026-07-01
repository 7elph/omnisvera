#!/usr/bin/env python3
"""Audita o vault Omnisvera contra o padrão global seguro.

O script é propositalmente conservador:
- não altera notas;
- não move mídia;
- não renomeia arquivos;
- não exige dependências externas.

Se PyYAML estiver disponível, ele será usado para validar YAML.
Caso contrário, o script usa um parser simples suficiente para inventário
de campos/tags e marca o modo de validação no relatório.
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
except Exception:  # pragma: no cover - ambiente local pode não ter PyYAML
    yaml = None


IGNORE_DIRS = {
    ".git",
    "zz_media",
    "node_modules",
    ".local-index",
    ".smtcmp_json_db",
    ".tmp_refs",
}

LEGACY_FIELDS = {
    "obsidianUIMode",
    "NoteIcon",
    "NoteStatus",
    "cover",
    "thumbnail",
    "status",
    "tags",
    "cssclasses",
    "cssclass",
    "banner",
    "banner-x",
    "banner-y",
    "banner-height",
    "content-start",
    "banner-fade",
    "chapters",
    "chapter",
}

OMNISVERA_FIELDS = {
    "type",
    "subtype",
    "work_status",
    "canon_status",
    "visibility",
    "created_by",
    "requires_review",
    "name",
    "aliases",
    "origin",
    "location",
    "territory",
    "faction",
    "faith",
    "thumbnail",
    "portrait",
    "cover",
    "related_characters",
    "related_factions",
    "related_items",
    "arcs",
    "chapters",
}

MINIMUM_OMNISVERA_FIELDS = {
    "type",
    "visibility",
}

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

OFFICIAL_TAGS = {
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
    "workflow",
    "async_scene",
    "ai_npc",
}

LEGACY_ACCEPTED_TAGS = {
    "Category/Location",
    "Category/Settlement",
    "Category/Lore",
    "Category/Character",
    "story",
    "bside",
    "old-dragon",
    "personagem",
    "local",
    "territorio",
    "faccao",
    "religiao",
    "raca",
    "classe",
    "capitulo",
    "origem",
    "npc",
    "jogador",
    "antagonista",
    "criatura",
}

HYBRID_TAG_PAIRS = [
    ("location", "local"),
    ("territory", "territorio"),
    ("faction", "faccao"),
    ("religion", "religiao"),
    ("race", "raca"),
    ("class", "classe"),
    ("character", "personagem"),
]

MEDIA_KEYS = {"cover", "thumbnail", "portrait", "banner"}
MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".mp3",
    ".wav",
    ".ogg",
}


@dataclass
class NoteAudit:
    path: Path
    has_frontmatter: bool = False
    yaml_valid: bool = False
    yaml_mode: str = "simple"
    yaml_errors: list[str] = field(default_factory=list)
    fields: dict[str, Any] = field(default_factory=dict)
    tags: list[str] = field(default_factory=list)
    note_type: str | None = None
    subtype: str | None = None
    missing_minimum_fields: list[str] = field(default_factory=list)
    legacy_fields: list[str] = field(default_factory=list)
    omnisvera_fields: list[str] = field(default_factory=list)
    outside_standard_tags: list[str] = field(default_factory=list)
    media_refs: list[str] = field(default_factory=list)


def scalar(value: str) -> Any:
    value = value.strip()
    if value == "":
        return None
    if value == "[]":
        return []
    if value == "{}":
        return {}
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


def extract_frontmatter(text: str) -> tuple[str | None, str, list[str]]:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None, text, ["frontmatter ausente"]
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            fm = "\n".join(lines[1:idx])
            body = "\n".join(lines[idx + 1 :])
            return fm, body, []
    return None, text, ["frontmatter sem delimitador de fechamento"]


def parse_simple_yaml(raw: str) -> tuple[dict[str, Any], list[str]]:
    data: dict[str, Any] = {}
    errors: list[str] = []
    current_key: str | None = None
    seen: set[str] = set()
    for lineno, line in enumerate(raw.splitlines(), start=2):
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        if re.match(r"^[A-Za-z0-9_./'-]+:", line):
            key, value = line.split(":", 1)
            key = key.strip()
            if key in seen:
                errors.append(f"linha {lineno}: campo duplicado `{key}`")
            seen.add(key)
            data[key] = scalar(value)
            current_key = key
            continue
        if line.startswith("  - ") and current_key:
            if not isinstance(data.get(current_key), list):
                data[current_key] = []
            data[current_key].append(scalar(line[4:]))
            continue
        if line.startswith(" ") and current_key:
            # Continuação/nesting simples: preserva como parseável, mas não interpreta.
            continue
        errors.append(f"linha {lineno}: sintaxe YAML não reconhecida: {line[:80]}")
    return data, errors


def parse_frontmatter(raw: str) -> tuple[dict[str, Any], bool, str, list[str]]:
    if yaml is not None:
        try:
            parsed = yaml.safe_load(raw) or {}
            if not isinstance(parsed, dict):
                return {}, False, "pyyaml", ["frontmatter não é mapa YAML"]
            return parsed, True, "pyyaml", []
        except Exception as exc:  # noqa: BLE001
            simple, simple_errors = parse_simple_yaml(raw)
            return simple, False, "pyyaml", [str(exc), *simple_errors]
    parsed, errors = parse_simple_yaml(raw)
    return parsed, not errors, "simple", errors


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        parts = set(path.relative_to(root).parts)
        if parts & IGNORE_DIRS:
            continue
        files.append(path)
    return sorted(files)


def normalize_media_ref(ref: str) -> str | None:
    ref = ref.strip().strip('"').strip("'")
    if not ref or ref.startswith("http://") or ref.startswith("https://"):
        return None
    if ref.startswith("[[") and ref.endswith("]]"):
        ref = ref[2:-2]
    ref = ref.split("|", 1)[0].split("#", 1)[0].strip()
    suffix = Path(ref).suffix.lower()
    if suffix not in MEDIA_EXTENSIONS:
        return None
    return ref.replace("\\", "/")


def extract_media_refs(text: str, fields: dict[str, Any]) -> list[str]:
    refs: list[str] = []
    for key in MEDIA_KEYS:
        value = fields.get(key)
        if isinstance(value, str):
            normalized = normalize_media_ref(value)
            if normalized:
                refs.append(normalized)
    # Evita tratar exemplos em blocos cercados por ``` como mídia real.
    scan_text = re.sub(r"```.*?```", "", text, flags=re.DOTALL)
    for pattern in [
        r"!\[\[([^\]]+)\]\]",
        r"\[\[([^\]]+\.(?:png|jpg|jpeg|gif|webp|svg|mp3|wav|ogg)(?:\|[^\]]*)?)\]\]",
        r"!\[[^\]]*\]\(([^)]+)\)",
        r"<img[^>]+src=[\"']([^\"']+)[\"']",
    ]:
        for match in re.findall(pattern, scan_text, flags=re.IGNORECASE):
            normalized = normalize_media_ref(match)
            if normalized:
                refs.append(normalized)
    return sorted(set(refs))


def tag_format_issue(tag: str) -> bool:
    if tag.startswith("Category/"):
        return False
    # Aceita tags antigas PT-BR já existentes, mas marca espaços/maiúsculas.
    if " " in tag:
        return True
    if any(ch.isupper() for ch in tag):
        return True
    return False


def audit_note(path: Path, root: Path) -> NoteAudit:
    text = path.read_text(encoding="utf-8-sig", errors="replace")
    raw_fm, body, fm_errors = extract_frontmatter(text)
    audit = NoteAudit(path=path.relative_to(root))
    if raw_fm is None:
        audit.yaml_errors.extend(fm_errors)
        audit.media_refs = extract_media_refs(text, {})
        return audit
    audit.has_frontmatter = True
    fields, valid, mode, errors = parse_frontmatter(raw_fm)
    audit.fields = fields
    audit.yaml_valid = valid
    audit.yaml_mode = mode
    audit.yaml_errors.extend(errors)
    tags = fields.get("tags") or []
    if isinstance(tags, str):
        audit.tags = [tags]
    elif isinstance(tags, list):
        audit.tags = [str(tag) for tag in tags if tag is not None]
    audit.note_type = str(fields.get("type")) if fields.get("type") is not None else None
    audit.subtype = str(fields.get("subtype")) if fields.get("subtype") is not None else None
    audit.missing_minimum_fields = sorted(
        field for field in MINIMUM_OMNISVERA_FIELDS if field not in fields
    )
    audit.legacy_fields = sorted(k for k in fields if k in LEGACY_FIELDS)
    audit.omnisvera_fields = sorted(k for k in fields if k in OMNISVERA_FIELDS)
    audit.outside_standard_tags = sorted(tag for tag in audit.tags if tag_format_issue(tag))
    audit.media_refs = extract_media_refs(text, fields)
    return audit


def is_historical_path(path_text: str) -> bool:
    normalized = path_text.replace("\\", "/")
    return (
        normalized.startswith("Workflow/Legacy/")
        or normalized.startswith("Workflow/_archive/")
        or normalized.startswith("Workflow/_audit/")
        or normalized.startswith("Workflow/Reports/")
        or normalized.startswith("Workflow/RPG_SYSTEM_DESIGN/")
        or normalized.startswith("Workflow/COMPATIBILITY_LAYER/")
    )


def resolve_media(root: Path, ref: str, media_files: dict[str, Path]) -> tuple[str, str | None]:
    ref_path = Path(ref)
    candidates = []
    if ref.startswith("zz_media/"):
        candidates.append(root / ref)
    else:
        candidates.append(root / ref)
        candidates.append(root / "zz_media" / ref_path.name)
    for candidate in candidates:
        if candidate.exists():
            return "ok", None
    lower_name = ref_path.name.lower()
    for name, path in media_files.items():
        if name.lower() == lower_name:
            return "case_mismatch", str(path.relative_to(root))
    return "missing", None


def md_list(items: list[str], limit: int = 50) -> str:
    if not items:
        return "- Nenhum.\n"
    shown = items[:limit]
    text = "".join(f"- `{item}`\n" for item in shown)
    if len(items) > limit:
        text += f"- ... mais {len(items) - limit} itens.\n"
    return text


def counter_table(counter: Counter[str], limit: int = 50) -> str:
    if not counter:
        return "| item | ocorrências |\n|---|---:|\n"
    lines = ["| item | ocorrências |", "|---|---:|"]
    for item, count in counter.most_common(limit):
        lines.append(f"| `{item}` | {count} |")
    return "\n".join(lines) + "\n"


def build_report(root: Path, audits: list[NoteAudit]) -> str:
    field_counter: Counter[str] = Counter()
    tag_counter: Counter[str] = Counter()
    type_counter: Counter[str] = Counter()
    subtype_counter: Counter[str] = Counter()
    yaml_modes: Counter[str] = Counter()
    media_ref_counter: Counter[str] = Counter()
    notes_without_type: list[str] = []
    notes_without_subtype: list[str] = []
    notes_missing_minimum: list[str] = []
    notes_without_frontmatter: list[str] = []
    invalid_yaml: list[str] = []
    outside_tags: dict[str, list[str]] = {}
    hybrid_notes: dict[str, list[str]] = defaultdict(list)

    media_dir = root / "zz_media"
    media_files = {p.name: p for p in media_dir.iterdir() if p.is_file()} if media_dir.exists() else {}
    media_exact_refs: set[str] = set()
    broken_media: list[str] = []
    case_media: list[str] = []

    for audit in audits:
        field_counter.update(audit.fields.keys())
        tag_counter.update(audit.tags)
        if audit.note_type:
            type_counter[audit.note_type] += 1
        else:
            notes_without_type.append(str(audit.path))
        if not audit.has_frontmatter:
            notes_without_frontmatter.append(str(audit.path))
        if audit.subtype:
            subtype_counter[audit.subtype] += 1
        else:
            notes_without_subtype.append(str(audit.path))
        if audit.missing_minimum_fields:
            notes_missing_minimum.append(
                f"{audit.path} — faltando: {', '.join(audit.missing_minimum_fields)}"
            )
        yaml_modes[audit.yaml_mode] += 1
        if audit.has_frontmatter and not audit.yaml_valid:
            invalid_yaml.append(f"{audit.path} — {'; '.join(audit.yaml_errors)}")
        if audit.outside_standard_tags:
            outside_tags[str(audit.path)] = audit.outside_standard_tags
        for a, b in HYBRID_TAG_PAIRS:
            if a in audit.tags and b in audit.tags:
                hybrid_notes[f"{a}/{b}"].append(str(audit.path))
        for ref in audit.media_refs:
            media_ref_counter[ref] += 1
            media_exact_refs.add(Path(ref).name)
            status, match = resolve_media(root, ref, media_files)
            if status == "missing":
                broken_media.append(f"{audit.path} — `{ref}`")
            elif status == "case_mismatch":
                case_media.append(f"{audit.path} — `{ref}` → provável `{match}`")

    media_ref_lower = {name.lower() for name in media_exact_refs}
    orphan_media = sorted(
        name for name in media_files if name.lower() not in media_ref_lower
    )
    broken_operational = [
        item for item in broken_media if not is_historical_path(item.split(" — ", 1)[0])
    ]
    case_operational = [
        item for item in case_media if not is_historical_path(item.split(" — ", 1)[0])
    ]

    hybrid_lines: list[str] = []
    for pair, paths in sorted(hybrid_notes.items()):
        hybrid_lines.append(f"- `{pair}` em {len(paths)} nota(s). Exemplos:")
        for item in paths[:10]:
            hybrid_lines.append(f"  - `{item}`")

    outside_lines: list[str] = []
    for path, tags in sorted(outside_tags.items()):
        outside_lines.append(f"- `{path}`: {', '.join(f'`{tag}`' for tag in tags)}")

    generated = datetime.now().strftime("%Y-%m-%d %H:%M")
    text = f"""# Auditoria Global de Padronização do Vault

Gerado em: {generated}

Fonte de padrão: [[Workflow/OMNISVERA_VAULT_STANDARD|OMNISVERA_VAULT_STANDARD]]

> [!IMPORTANT]
> Esta auditoria não aplicou correções automáticas.
> Ela apenas inventaria frontmatter, tags, mídia e riscos para migração futura.

## Resumo geral

| métrica | valor |
|---|---:|
| notas Markdown auditadas | {len(audits)} |
| notas com frontmatter | {sum(1 for a in audits if a.has_frontmatter)} |
| notas sem frontmatter | {sum(1 for a in audits if not a.has_frontmatter)} |
| YAML/frontmatter parseável | {sum(1 for a in audits if a.has_frontmatter and a.yaml_valid)} |
| YAML/frontmatter com problema | {len(invalid_yaml)} |
| campos YAML distintos | {len(field_counter)} |
| tags distintas | {len(tag_counter)} |
| tipos detectados | {len(type_counter)} |
| subtipos detectados | {len(subtype_counter)} |
| referências de mídia distintas | {len(media_ref_counter)} |
| mídias em `zz_media` | {len(media_files)} |
| imagens/mídias quebradas | {len(broken_media)} |
| imagens/mídias quebradas fora de histórico/auditoria | {len(broken_operational)} |
| possíveis problemas de case-sensitive | {len(case_media)} |
| possíveis problemas de case-sensitive fora de histórico/auditoria | {len(case_operational)} |
| mídias possivelmente órfãs | {len(orphan_media)} |

Modo de validação YAML:

{counter_table(yaml_modes, 10)}

## Campos YAML encontrados

{counter_table(field_counter, 80)}

## Tags encontradas

{counter_table(tag_counter, 120)}

## Notas por `type`

{counter_table(type_counter, 40)}

## Notas por `subtype`

{counter_table(subtype_counter, 80)}

## Notas sem `type`

{md_list(notes_without_type, 100)}

## Notas sem frontmatter

> Nem toda documentação técnica precisa de frontmatter.
> Esta lista é inventário, não autorização para corrigir em massa.

{md_list(notes_without_frontmatter, 120)}

## Notas sem `subtype`

> `subtype` é recomendado para padronização futura, mas não deve ser adicionado em massa sem lote controlado.

{md_list(notes_without_subtype, 100)}

## Notas faltando campos Omnisvera mínimos

Campos mínimos auditados: `type`, `visibility`.

{md_list(notes_missing_minimum, 100)}

## YAML/frontmatter com problema

{md_list(invalid_yaml, 100)}

## Tags híbridas encontradas

{chr(10).join(hybrid_lines) if hybrid_lines else "- Nenhuma combinação híbrida detectada nas mesmas notas."}

## Tags possivelmente fora do padrão de formato

Critério: tag com espaço, maiúscula inesperada ou formato arriscado. Tags `Category/*` são aceitas como legacy.

{chr(10).join(outside_lines) if outside_lines else "- Nenhuma tag com formato arriscado detectada."}

## Referências de mídia quebradas

{md_list(sorted(set(broken_media)), 100)}

## Referências de mídia quebradas fora de histórico/auditoria

{md_list(sorted(set(broken_operational)), 100)}

## Possíveis problemas de case-sensitive em mídia

{md_list(sorted(set(case_media)), 100)}

## Possíveis problemas de case-sensitive fora de histórico/auditoria

{md_list(sorted(set(case_operational)), 100)}

## Mídias possivelmente órfãs em `zz_media`

> Não apagar automaticamente. Uma mídia pode ser usada por CSS, plugin, mapa, canvas, nota futura ou referência manual ainda não capturada.

{md_list(orphan_media, 120)}

## Reclassificações sugeridas

### 1. O Frasco Afogado

| campo | valor |
|---|---|
| estado atual provável | `Items/O Frasco Afogado.md` |
| classificação correta sugerida | `location/shop` |
| motivo | é a loja de alquimia do Mestre Odran em Maré Baixa, não um item portátil |

Ação recomendada futura:

- mover para `Locations/O Frasco Afogado.md` ou `Locations/Nimalis/Maré Baixa/O Frasco Afogado.md`;
- atualizar links internos;
- manter redirect/nota ponte se necessário;
- atualizar frontmatter para `type: location` e `subtype: shop`;
- vincular imagem gerada/aprovada do local;
- executar em commit próprio.

Não executar nesta auditoria.

## Recomendações por prioridade

### Prioridade alta

1. Resolver referências de mídia quebradas e problemas de case-sensitive.
2. Resolver primeiro referências quebradas fora de histórico/auditoria; referências em `Workflow/Legacy`, `_archive` e `_audit` devem ser tratadas como histórico até decisão do Sage.
3. Definir se tags técnicas oficiais serão aplicadas em inglês em notas novas, mantendo tags PT-BR/legacy como ponte.
4. Criar plano para `O Frasco Afogado` antes de padronizar Items e Locations em massa.

### Prioridade média

1. Adicionar `subtype`, `work_status` e `canon_status` por lote pequeno.
2. Padronizar corpo de `Factions`, `Territories`, `Locations`, `Lore` e `Items` por família.
3. Reduzir tags híbridas somente depois de confirmar DataCards, Dataview e Supercharged Links.

### Prioridade baixa

1. Planejar subpastas em `zz_media`.
2. Reavaliar mídia possivelmente órfã.
3. Criar camada App/IA após estabilizar vault operacional.

## Plano de migração futura

### Fase A — Somente documentação e templates

- Criar padrão global.
- Criar templates.
- Criar auditoria.

### Fase B — Tags globais

- Mapear tags híbridas.
- Definir tags oficiais.
- Adicionar tags oficiais sem remover legacy inicialmente.

### Fase C — Frontmatter mínimo

- Adicionar `type`, `subtype`, `work_status`, `canon_status` e `visibility` onde faltar.
- Preservar `NoteIcon` e `NoteStatus`.

### Fase D — Mídia

- Corrigir referências quebradas.
- Resolver problemas de case.
- Só depois considerar subpastas.

### Fase E — Corpo das notas

- Padronizar `Characters`, `Locations`, `Factions`, `Territories`, `Lore` e `Items` por lote.
- Não forçar corpo idêntico quando a nota precisar de estrutura narrativa própria.

### Fase F — App/IA

- Adicionar `app_enabled`, `player_visible` e `ai_access`.
- Criar `AI_NPCs` e cenas assíncronas.
- Criar fluxo `submitted → pending_review → canonized`.

## Como rodar novamente

```powershell
python scripts/audit_vault_standard.py --root . --output Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md
```
"""
    return text


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita o padrão global do vault Omnisvera.")
    parser.add_argument("--root", default=".", help="Raiz do vault/repositório.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md",
        help="Arquivo Markdown de saída.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = root / args.output
    audits = [audit_note(path, root) for path in iter_markdown_files(root)]
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(build_report(root, audits), encoding="utf-8")
    print(f"Auditado: {len(audits)} notas")
    print(f"Relatório: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
