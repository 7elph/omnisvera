from __future__ import annotations

import argparse
from concurrent.futures import ThreadPoolExecutor
import json
import re
import unicodedata
from dataclasses import dataclass, field
from datetime import date
from html.parser import HTMLParser
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen


CHAPTER_URLS = (
    "https://olddragon.com.br/livros/srd/capitulos/monstros-a-d",
    "https://olddragon.com.br/livros/srd/capitulos/monstros-e-k",
    "https://olddragon.com.br/livros/srd/capitulos/monstros-l-z",
)
SRD_URL = "https://olddragon.com.br/livros/srd"
DEFAULT_OUTPUT = Path(__file__).resolve().parents[1] / "app" / "data" / "old_dragon_srd_monsters.json"


@dataclass(eq=False)
class Node:
    tag: str
    attrs: dict[str, str] = field(default_factory=dict)
    parent: "Node | None" = None
    children: list["Node | str"] = field(default_factory=list)

    def text(self) -> str:
        parts: list[str] = []

        def visit(node: Node | str) -> None:
            if isinstance(node, str):
                parts.append(node)
                return
            for child in node.children:
                visit(child)

        visit(self)
        return re.sub(r"\s+", " ", " ".join(parts)).strip()

    def descendants(self, tag: str | None = None) -> Iterable["Node"]:
        for child in self.children:
            if not isinstance(child, Node):
                continue
            if tag is None or child.tag == tag:
                yield child
            yield from child.descendants(tag)


class DOMParser(HTMLParser):
    VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "param", "source", "track", "wbr"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.root = Node("document")
        self.stack = [self.root]

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        node = Node(tag, {key: value or "" for key, value in attrs}, self.stack[-1])
        self.stack[-1].children.append(node)
        if tag not in self.VOID_TAGS:
            self.stack.append(node)

    def handle_startendtag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        self.handle_starttag(tag, attrs)
        if tag not in self.VOID_TAGS:
            self.stack.pop()

    def handle_endtag(self, tag: str) -> None:
        for index in range(len(self.stack) - 1, 0, -1):
            if self.stack[index].tag == tag:
                del self.stack[index:]
                return

    def handle_data(self, data: str) -> None:
        if data:
            self.stack[-1].children.append(data)


def slugify(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    return re.sub(r"[^a-z0-9]+", "-", normalized.lower()).strip("-")


def element_siblings_after(node: Node) -> Iterable[Node]:
    if node.parent is None:
        return
    found = False
    for sibling in node.parent.children:
        if sibling is node:
            found = True
            continue
        if found and isinstance(sibling, Node):
            yield sibling


def first_number(value: str) -> int | None:
    match = re.search(r"-?\d+", value)
    return int(match.group()) if match else None


def parse_attack(raw: str) -> dict:
    normalized = re.sub(r"\s+", " ", raw).strip()
    match = re.match(r"(?P<count>\d+)\s*[x×]\s*(?P<name>.*?)(?:\s+(?P<bonus>[+-]\d+))?\s*\((?P<damage>.*)\)\s*$", normalized, re.IGNORECASE)
    if not match:
        return {"raw": normalized, "count": None, "name": normalized, "bonus": None, "damage": ""}
    return {
        "raw": normalized,
        "count": int(match.group("count")),
        "name": match.group("name").strip(),
        "bonus": int(match.group("bonus")) if match.group("bonus") else None,
        "damage": match.group("damage").strip(),
    }


def parse_stat_block(heading: Node, block: Node, source_url: str) -> dict:
    name = heading.text()
    paragraphs = list(block.descendants("p"))
    classification = paragraphs[0].text() if paragraphs else ""
    classification_parts = [part.strip() for part in classification.split("◆", 1)]
    identity_match = re.match(
        r"^(?P<category>.*?),\s*(?P<size>Minúsculo|Pequeno|Médio|Grande|Imenso|Colossal)\s+e\s+(?P<alignment>.+)$",
        classification_parts[0],
        re.IGNORECASE,
    )

    stats: dict[str, str] = {}
    stat_labels = {"Encontro", "Experiência", "Tesouro", "Movimento", "DV [PV]", "DV", "CA", "JP", "MO"}
    for label_node in block.descendants():
        label = label_node.text()
        if label not in stat_labels or label_node.tag not in {"strong", "span", "button"}:
            continue
        current = label_node
        for _ in range(4):
            parent = current.parent
            if parent is None:
                break
            elements = [child for child in parent.children if isinstance(child, Node)]
            if current in elements:
                index = elements.index(current)
                values: list[str] = []
                for sibling in elements[index + 1:]:
                    value_nodes = [sibling] if sibling.tag in {"em", "span"} else [
                        candidate for candidate in sibling.descendants() if candidate.tag in {"em", "span"} and candidate.text()
                    ]
                    values.extend(value_node.text() for value_node in value_nodes if value_node.text() not in stat_labels)
                if values:
                    stats[label] = f"{values[0]} ({' '.join(values[1:])})" if label == "Encontro" and len(values) > 1 else " ".join(values)
            if label in stats:
                break
            current = parent

    dv_raw = stats.get("DV [PV]", stats.get("DV", ""))
    dv_match = re.match(r"(?P<dv>.*?)\s*\[(?P<hp>[^\]]+)\]", dv_raw)
    hit_points = dv_match.group("hp").strip() if dv_match else ""

    attacks: list[dict] = []
    for candidate_node in block.descendants():
        if candidate_node.tag not in {"div", "li"}:
            continue
        text = candidate_node.text()
        if re.match(r"^\d+\s*[x×]\s*.+\(.+\)$", text, re.IGNORECASE):
            candidate = parse_attack(text)
            if candidate["raw"] not in {attack["raw"] for attack in attacks}:
                attacks.append(candidate)

    abilities: list[dict[str, str]] = []
    for li in block.descendants("li"):
        if re.match(r"^\d+\s*[x×]\s*.+\(.+\)$", li.text(), re.IGNORECASE):
            continue
        strong = next(li.descendants("strong"), None)
        text = li.text()
        if strong is None or not text:
            continue
        ability_name = strong.text().rstrip(":").strip()
        description = re.sub(rf"^{re.escape(strong.text())}\s*:?\s*", "", text).strip()
        if ability_name and not any(item["name"] == ability_name and item["description"] == description for item in abilities):
            abilities.append({"name": ability_name, "description": description})

    anchor = heading.attrs.get("id", slugify(name))
    return {
        "id": anchor or slugify(name),
        "name": name,
        "source_url": f"{source_url}#{anchor}",
        "category": identity_match.group("category").strip() if identity_match else classification_parts[0],
        "size": identity_match.group("size").strip() if identity_match else "",
        "alignment": identity_match.group("alignment").strip() if identity_match else "",
        "habitat": classification_parts[1] if len(classification_parts) > 1 else "",
        "encounter": stats.get("Encontro", ""),
        "experience": stats.get("Experiência", ""),
        "experience_points": first_number(stats.get("Experiência", "")),
        "treasure": stats.get("Tesouro", ""),
        "movement": stats.get("Movimento", ""),
        "hit_dice": dv_match.group("dv").strip() if dv_match else dv_raw,
        "hit_points": hit_points,
        "average_hp": int(hit_points) if hit_points.isdigit() else None,
        "armor_class": first_number(stats.get("CA", "")),
        "saving_throw": first_number(stats.get("JP", "")),
        "morale": first_number(stats.get("MO", "")),
        "attacks": attacks,
        "abilities": abilities,
    }


def extract_monsters(html: str, source_url: str) -> list[dict]:
    parser = DOMParser()
    parser.feed(html)
    monsters: list[dict] = []
    for heading in parser.root.descendants():
        if heading.tag not in {"h2", "h3", "h4"} or not heading.text():
            continue
        block = next(element_siblings_after(heading), None)
        if block is None or block.tag != "div":
            continue
        classes = set(block.attrs.get("class", "").split())
        if not {"relative", "mx-auto", "p-4"}.issubset(classes):
            continue
        monster = parse_stat_block(heading, block, source_url)
        if monster["hit_dice"] or monster["armor_class"] is not None:
            monsters.append(monster)
    return monsters


def extract_srd_links(html: str) -> list[tuple[str, str]]:
    parser = DOMParser()
    parser.feed(html)
    links: list[tuple[str, str]] = []
    for anchor in parser.root.descendants("a"):
        href = anchor.attrs.get("href", "")
        name = anchor.text()
        if re.fullmatch(r"/monstros/[a-z0-9-]+", href) and name:
            links.append((f"https://olddragon.com.br{href}", name))
    return links


def extract_individual_monster(html: str, source_url: str, expected_name: str) -> dict:
    parser = DOMParser()
    parser.feed(html)
    heading = next((node for node in parser.root.descendants("h1") if node.text() == expected_name), None)
    if heading is None:
        raise ValueError(f"Cabeçalho de {expected_name!r} não encontrado em {source_url}.")
    block = heading.parent
    while block is not None and "clearfix" not in block.attrs.get("class", "").split():
        block = block.parent
    if block is None:
        raise ValueError(f"Ficha de {expected_name!r} não encontrada em {source_url}.")
    monster = parse_stat_block(heading, block, source_url)
    monster["id"] = source_url.rsplit("/", 1)[-1]
    monster["source_url"] = source_url
    return monster


def download(url: str) -> str:
    request = Request(url, headers={"User-Agent": "Omnisvera-Companion-SRD-Importer/1.0"})
    with urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8")


def build_catalog() -> dict:
    links = extract_srd_links(download(SRD_URL))
    if len(links) != 255:
        raise ValueError(f"O índice oficial deveria listar 255 monstros; foram encontrados {len(links)}.")

    def fetch_monster(link: tuple[str, str]) -> dict:
        url, name = link
        return extract_individual_monster(download(url), url, name)

    with ThreadPoolExecutor(max_workers=12) as executor:
        monsters = list(executor.map(fetch_monster, links))
    monsters.sort(key=lambda item: slugify(item["name"]))
    return {
        "schema_version": 1,
        "catalog": {
            "id": "old-dragon-2-srd",
            "title": "Old Dragon 2 - SRD",
            "edition": "2a edição",
            "source_url": SRD_URL,
            "license": "CC BY-SA 4.0",
            "license_url": "https://creativecommons.org/licenses/by-sa/4.0/",
            "attribution": "Old Dragon 2 - Documento de Referência do Sistema (SRD), Buró Brasil Jogos.",
            "retrieved_on": date.today().isoformat(),
        },
        "count": len(monsters),
        "monsters": monsters,
    }


def main() -> None:
    argument_parser = argparse.ArgumentParser(description="Importa os monstros da SRD oficial do Old Dragon 2.")
    argument_parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    arguments = argument_parser.parse_args()
    catalog = build_catalog()
    if catalog["count"] != 255:
        raise SystemExit(f"A SRD deveria produzir 255 monstros; foram encontrados {catalog['count']}.")
    arguments.output.parent.mkdir(parents=True, exist_ok=True)
    arguments.output.write_text(json.dumps(catalog, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"{catalog['count']} monstros gravados em {arguments.output}")


if __name__ == "__main__":
    main()
