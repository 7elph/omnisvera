#!/usr/bin/env python3
"""Gera plano dry-run de normalizacao de tags do vault Omnisvera.

Este script nao altera notas. Ele apenas identifica onde uma tag oficial
Omnisvera poderia ser adicionada mantendo a tag legacy/hibrida existente.
"""

from __future__ import annotations

import argparse
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

try:
    import yaml  # type: ignore
except Exception:  # pragma: no cover
    yaml = None


IGNORE_DIRS = {
    ".git",
    "zz_media",
    "node_modules",
    ".local-index",
    ".smtcmp_json_db",
    ".tmp_refs",
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

TAG_EQUIVALENTS = {
    "local": "location",
    "faccao": "faction",
    "raca": "race",
    "religiao": "religion",
    "territorio": "territory",
    "personagem": "character",
    "classe": "class",
    "Category/Location": "location",
    "Category/Lore": "lore",
    "Category/Character": "character",
    "npc": "character",
    "jogador": "character",
    "antagonista": "character",
    "criatura": "character",
}

TAG_REVIEW_EQUIVALENTS = {
    "Category/Settlement": "location ou territory",
    "settlement": "location ou territory",
}

LEGACY_ALLOWED_TAGS = {
    "Category/Location",
    "Category/Settlement",
    "Category/Lore",
    "Category/Character",
    "story",
    "bside",
    "old-dragon",
    "loyalist",
    "rancher",
    "pirate",
    "widow",
    "third",
    "murray",
    "steeltown",
    "water",
}

CAMPAIGN_SPECIFIC_TAGS = {
    "story",
    "bside",
    "old-dragon",
    "capitulo",
    "origem",
    "campanha",
    "earthropo",
    "nimalia",
    "nimalis",
    "raziel",
    "varkh",
    "vezemir",
    "sanguinallis",
    "avenor",
    "lethvalora",
    "criadores",
    "coroa",
    "nobreza",
    "vampiro",
    "antropo",
    "elfo",
    "humano",
    "humana",
    "anao",
    "kenku",
    "dragonborn",
    "paladino",
    "guerreiro",
    "alquimista",
    "clerigo",
    "ladrao",
    "mago",
    "misterio",
    "desaparecido",
    "artefato",
    "arma",
    "escudo",
    "medalhao",
    "monstro",
    "quest",
    "rumor",
    "distrito",
    "bairro",
    "cidade",
    "vila",
    "ruinas",
    "fortaleza",
    "porto",
    "capital",
    "floresta",
    "reino",
    "valthor",
    "gharok",
    "comercio",
    "economia",
    "guilda",
    "militar",
    "monarquia",
    "culto",
    "guarda",
    "aventureiros",
    "errantes",
    "exploradores",
    "cosmologia",
    "historia",
    "fenomeno",
    "magia",
    "cataclisma",
    "fraturamento",
    "investigacao",
    "estabelecimento",
    "alquimia",
    "forasteiros",
}

SYSTEM_TAGS = {
    "workflow",
    "audit",
    "report",
    "dashboard",
    "home",
    "map",
    "calendar",
    "world",
    "vault-standard",
    "rules-reference",
    "padronizacao",
    "indice",
    "omnisvera",
    "title",
    "legacy",
    "culture",
    "cultura",
    "notes",
    "classes",
    "regras",
    "assistant",
    "frontmatter",
    "cleanup",
    "personagens",
    "faccoes",
    "geografia",
    "itens",
    "locations",
    "locais",
    "territories",
    "mapas",
    "handoff",
    "backup",
    "canon",
    "chart",
    "geography",
    "archive",
    "ollama",
    "protocol",
    "tooling",
    "migration",
    "placeholder",
}


@dataclass(frozen=True)
class NoteTags:
    path: Path
    tags: tuple[str, ...]


def iter_markdown_files(root: Path) -> list[Path]:
    files: list[Path] = []
    for path in root.rglob("*.md"):
        rel_parts = set(path.relative_to(root).parts)
        if rel_parts & IGNORE_DIRS:
            continue
        files.append(path)
    return sorted(files)


def extract_frontmatter(text: str) -> str | None:
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return None
    for idx in range(1, len(lines)):
        if lines[idx].strip() == "---":
            return "\n".join(lines[1:idx])
    return None


def parse_simple_tags(raw: str) -> list[str]:
    tags: list[str] = []
    lines = raw.splitlines()
    current_key: str | None = None
    for line in lines:
        if re.match(r"^[A-Za-z0-9_./'-]+:", line):
            key, value = line.split(":", 1)
            current_key = key.strip()
            if current_key == "tags":
                value = value.strip()
                if value.startswith("[") and value.endswith("]"):
                    inner = value[1:-1].strip()
                    if inner:
                        tags.extend(part.strip().strip('"').strip("'") for part in inner.split(","))
                elif value:
                    tags.append(value.strip().strip('"').strip("'"))
            continue
        if current_key == "tags" and line.startswith("  - "):
            tags.append(line[4:].strip().strip('"').strip("'"))
    return [tag for tag in tags if tag]


def parse_tags(raw: str | None) -> list[str]:
    if raw is None:
        return []
    if yaml is not None:
        try:
            data = yaml.safe_load(raw) or {}
            if isinstance(data, dict):
                tags = data.get("tags") or []
                if isinstance(tags, str):
                    return [tags]
                if isinstance(tags, list):
                    return [str(tag) for tag in tags if tag is not None]
        except Exception:
            pass
    return parse_simple_tags(raw)


def collect_notes(root: Path) -> list[NoteTags]:
    notes: list[NoteTags] = []
    for path in iter_markdown_files(root):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        tags = tuple(parse_tags(extract_frontmatter(text)))
        notes.append(NoteTags(path=path.relative_to(root), tags=tags))
    return notes


def classify_tag(tag: str) -> str:
    if tag in OFFICIAL_TAGS:
        return "official"
    if tag in TAG_EQUIVALENTS:
        return "hybrid"
    if tag in TAG_REVIEW_EQUIVALENTS:
        return "needs_sage_review"
    if tag.startswith("Category/"):
        return "category_tag"
    if tag in LEGACY_ALLOWED_TAGS:
        return "legacy_allowed"
    if tag in CAMPAIGN_SPECIFIC_TAGS or re.match(r"^(chapter|capitulo|bside)[-_]?\d+", tag):
        return "campaign_specific"
    if tag in SYSTEM_TAGS:
        return "system"
    if re.match(r"^[a-z0-9]+(?:-[a-z0-9]+)+$", tag):
        return "campaign_specific"
    return "unknown"


def recommendation_for_tag(tag: str) -> tuple[str, str, str, str]:
    category = classify_tag(tag)
    if category == "official":
        return category, tag, "keep", "low"
    if tag in TAG_EQUIVALENTS:
        risk = "medium" if tag.startswith("Category/") else "low"
        return category, TAG_EQUIVALENTS[tag], "add_official_tag", risk
    if tag in TAG_REVIEW_EQUIVALENTS:
        return category, TAG_REVIEW_EQUIVALENTS[tag], "review_with_sage", "medium"
    if category in {"legacy_allowed", "category_tag"}:
        return category, "", "keep_as_legacy", "medium"
    if category in {"campaign_specific", "system"}:
        return category, tag, "keep", "low"
    return category, "", "review_with_sage", "medium"


def tag_observation(tag: str) -> str:
    if tag in OFFICIAL_TAGS:
        return "Tag oficial Omnisvera."
    if tag in TAG_EQUIVALENTS:
        return "Adicionar a tag oficial futuramente; preservar a tag atual nesta fase."
    if tag in TAG_REVIEW_EQUIVALENTS:
        return "Equivalencia ambigua; revisar com Sage antes de alterar."
    if tag.startswith("Category/"):
        return "Tag legacy/categoria; pode alimentar Dataview, DataCards ou visual antigo."
    if tag in {"story", "bside"}:
        return "Tag narrativa herdada preservada conscientemente."
    if tag == "old-dragon":
        return "Tag de sistema/campanha."
    if classify_tag(tag) == "campaign_specific":
        return "Tag especifica de campanha/lore; nao remover automaticamente."
    if classify_tag(tag) == "system":
        return "Tag tecnica/sistema."
    return "Precisa revisao antes de qualquer acao."


def inventory(notes: list[NoteTags]) -> tuple[Counter[str], dict[str, list[str]]]:
    counter: Counter[str] = Counter()
    examples: dict[str, list[str]] = defaultdict(list)
    for note in notes:
        counter.update(note.tags)
        for tag in note.tags:
            if len(examples[tag]) < 5:
                examples[tag].append(str(note.path).replace("\\", "/"))
    return counter, examples


def candidate_rows(notes: list[NoteTags]) -> list[tuple[str, list[str], list[str], list[str], str, str]]:
    rows: list[tuple[str, list[str], list[str], list[str], str, str]] = []
    for note in notes:
        current = set(note.tags)
        relevant: list[str] = []
        add: list[str] = []
        preserved: list[str] = []
        risks: list[str] = []
        observations: list[str] = []
        for tag, official in sorted(TAG_EQUIVALENTS.items()):
            if tag in current and official not in current:
                relevant.append(tag)
                add.append(official)
                preserved.append(tag)
                risks.append("medium" if tag.startswith("Category/") else "low")
                observations.append(f"Adicionar `{official}` preservando `{tag}`.")
        for tag, official in sorted(TAG_REVIEW_EQUIVALENTS.items()):
            if tag in current:
                relevant.append(tag)
                preserved.append(tag)
                risks.append("medium")
                observations.append(f"Revisar se equivale a `{official}` antes de aplicar.")
        if relevant:
            risk = "high" if "high" in risks else "medium" if "medium" in risks else "low"
            rows.append(
                (
                    str(note.path).replace("\\", "/"),
                    sorted(set(relevant)),
                    sorted(set(add)),
                    sorted(set(preserved)),
                    risk,
                    " ".join(observations),
                )
            )
    return rows


def table_row(values: list[str]) -> str:
    escaped = [value.replace("|", "\\|").replace("\n", "<br>") for value in values]
    return "| " + " | ".join(escaped) + " |"


def render_tag_map(root: Path) -> str:
    notes = collect_notes(root)
    counter, _examples = inventory(notes)
    lines = [
        "# Omnisvera — Mapa de Normalizacao de Tags",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "> [!IMPORTANT]",
        "> Este mapa e dry-run conceitual. Ele nao autoriza remocao de tags legacy.",
        "> A acao segura futura e adicionar tags oficiais preservando as antigas.",
        "",
        "| Tag encontrada | Categoria | Tag oficial recomendada | Acao recomendada | Risco | Observacao |",
        "|---|---|---|---|---|---|",
    ]
    for tag, _count in counter.most_common():
        category, official, action, risk = recommendation_for_tag(tag)
        lines.append(
            table_row(
                [
                    f"`{tag}`",
                    category,
                    f"`{official}`" if official else "",
                    action,
                    risk,
                    tag_observation(tag),
                ]
            )
        )
    return "\n".join(lines) + "\n"


def render_impact(root: Path) -> str:
    notes = collect_notes(root)
    counter, examples = inventory(notes)
    categories: Counter[str] = Counter(classify_tag(tag) for tag in counter)
    rows = candidate_rows(notes)
    equivalences = [
        ("local", "location"),
        ("faccao", "faction"),
        ("raca", "race"),
        ("religiao", "religion"),
        ("item/itens", "item"),
        ("territorio", "territory"),
        ("personagem", "character"),
        ("classe", "class"),
        ("Category/Location", "location"),
        ("Category/Lore", "lore"),
        ("Category/Character", "character"),
    ]
    lines = [
        "# Omnisvera — Impacto da Normalizacao de Tags",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "## Resumo geral",
        "",
        "| metrica | valor |",
        "|---|---:|",
        f"| tags distintas | {len(counter)} |",
        f"| tags oficiais ja usadas | {categories.get('official', 0)} |",
        f"| tags legacy/category aceitas | {categories.get('legacy_allowed', 0) + categories.get('category_tag', 0)} |",
        f"| tags hibridas | {categories.get('hybrid', 0)} |",
        f"| tags desconhecidas | {categories.get('unknown', 0)} |",
        f"| tags que exigem revisao do Sage | {categories.get('needs_sage_review', 0)} |",
        f"| notas candidatas a receber tag oficial | {len(rows)} |",
        "",
        "## Tags por frequencia",
        "",
        "| tag | notas | exemplos |",
        "|---|---:|---|",
    ]
    for tag, count in counter.most_common():
        lines.append(
            table_row(
                [
                    f"`{tag}`",
                    str(count),
                    ", ".join(f"`{example}`" for example in examples[tag][:3]),
                ]
            )
        )
    lines.extend(
        [
            "",
            "## Possiveis equivalencias",
            "",
            "| tag atual | tag oficial sugerida | observacao |",
            "|---|---|---|",
        ]
    )
    for old, new in equivalences:
        lines.append(table_row([f"`{old}`", f"`{new}`", "Adicionar a oficial no futuro; preservar a atual."]))
    lines.extend(
        [
            "",
            "## Ambiguidades",
            "",
            "- `Category/Settlement` pode ser `location` ou `territory`, dependendo da nota.",
            "- `settlement` pode significar cidade, vila, reino ou localidade; precisa contexto.",
            "- `story` e `bside` sao eixos narrativos herdados; preservar nesta fase.",
            "- Tags de faccao/lore em formato slug podem ser semanticas de mundo, nao problema tecnico.",
            "",
            "## Riscos",
            "",
            "- Tags `Category/*` podem alimentar Dataview, DataCards ou dashboards.",
            "- Remover tags legacy pode quebrar consultas, cores de links ou agrupamentos visuais.",
            "- Adicionar tags oficiais e mais seguro que substituir tags existentes.",
            "- Tags de campanha como `old-dragon`, `story` e `bside` devem ser preservadas.",
            "",
            "## Recomendacao final",
            "",
            "Nesta fase, nao remover tags antigas. A proxima fase segura e revisar o plano dry-run,",
            "aprovar os casos de baixo risco e adicionar tags oficiais em lote pequeno, mantendo as tags legacy.",
            "",
        ]
    )
    return "\n".join(lines)


def render_plan(root: Path) -> str:
    notes = collect_notes(root)
    rows = candidate_rows(notes)
    low = [row for row in rows if row[4] == "low"]
    medium = [row for row in rows if row[4] == "medium"]
    high = [row for row in rows if row[4] == "high"]

    def render_rows(section_rows: list[tuple[str, list[str], list[str], list[str], str, str]]) -> list[str]:
        if not section_rows:
            return ["- Nenhum caso identificado."]
        section = [
            "| Arquivo | Tags atuais relevantes | Tags oficiais a adicionar | Tags preservadas | Risco | Observacao |",
            "|---|---|---|---|---|---|",
        ]
        for path, relevant, add, preserved, risk, observation in section_rows:
            section.append(
                table_row(
                    [
                        f"`{path}`",
                        ", ".join(f"`{tag}`" for tag in relevant),
                        ", ".join(f"`{tag}`" for tag in add) if add else "revisar",
                        ", ".join(f"`{tag}`" for tag in preserved),
                        risk,
                        observation,
                    ]
                )
            )
        return section

    lines = [
        "# Omnisvera — Plano Dry-Run de Normalizacao de Tags",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        "",
        "> [!IMPORTANT]",
        "> Este plano nao alterou nenhuma nota.",
        "> A estrategia segura e adicionar tags oficiais e preservar tags legacy/hibridas.",
        "",
        "## Resumo",
        "",
        "| metrica | valor |",
        "|---|---:|",
        f"| notas analisadas | {len(notes)} |",
        f"| notas candidatas | {len(rows)} |",
        f"| baixo risco | {len(low)} |",
        f"| medio risco | {len(medium)} |",
        f"| alto risco | {len(high)} |",
        "",
        "## Baixo risco",
        "",
        "Casos simples como `local` -> adicionar `location`, `faccao` -> adicionar `faction`, `raca` -> adicionar `race`.",
        "",
        *render_rows(low),
        "",
        "## Medio risco",
        "",
        "Casos que envolvem `Category/*`, `settlement` ou interpretacao de tipo real da nota.",
        "",
        *render_rows(medium),
        "",
        "## Alto risco",
        "",
        "Reservado para casos que afetem diretamente Dataview/DataCards/Home ou tags de semantica ambigua severa.",
        "",
        *render_rows(high),
        "",
        "## Tags preservadas sem migracao automatica",
        "",
        "- `story`: manter como eixo narrativo/capitulo por enquanto.",
        "- `bside`: manter como tag narrativa especial.",
        "- `old-dragon`: manter como tag de sistema/campanha.",
        "- `Category/*`: preservar ate revisar consultas Dataview/DataCards.",
        "",
        "## Proxima etapa recomendada",
        "",
        "Revisar este plano com o Sage e aplicar apenas os casos de baixo risco em uma Fase B2,",
        "com commit proprio e validacao de Dataview/DataCards depois.",
        "",
    ]
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera plano dry-run de normalizacao de tags.")
    parser.add_argument("--root", default=".", help="Raiz do vault/repositorio.")
    parser.add_argument(
        "--output",
        default="Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_PLAN.md",
        help="Arquivo Markdown de saida.",
    )
    args = parser.parse_args()
    root = Path(args.root).resolve()
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(render_plan(root), encoding="utf-8")
    print(f"Plano dry-run gerado: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
