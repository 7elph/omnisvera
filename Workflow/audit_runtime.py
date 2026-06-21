"""Audita integrações do Obsidian que não são cobertas pelo auditor de links."""

from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path

import yaml


ROOT = Path(__file__).resolve().parents[1]
EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".codex-tools",
    ".omnisvera-tools",
    ".local-tools",
    ".local-index",
    ".ollama",
    "zz_media",
    "z_Assets",
}
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
CODE_BLOCK = re.compile(
    r"(?ms)^([ \t>]*?)```(dataview|datacards|dataviewjs|leaflet)\s*\n(.*?)^[ \t>]*```"
)
WIKILINK = re.compile(r"\[\[([^\]|#]+)")
MEDIA_KEYS = {"banner", "cover", "thumbnail"}
MEDIA_EXTENSIONS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}


def is_active_note(path: Path) -> bool:
    return not path.name.startswith("Legacy -") and not any(
        part in EXCLUDED_DIRS for part in path.parts
    )


def strip_quote_prefix(text: str) -> str:
    return "\n".join(re.sub(r"^[ \t]*>[ \t]?", "", line) for line in text.splitlines())


def load_notes() -> list[dict]:
    notes = []
    for path in sorted(ROOT.rglob("*.md")):
        if not is_active_note(path):
            continue
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        frontmatter = {}
        match = FRONTMATTER.match(text)
        if match:
            frontmatter = yaml.safe_load(match.group(1)) or {}
        tags = frontmatter.get("tags", [])
        if isinstance(tags, str):
            tags = [tags]
        notes.append(
            {
                "path": path,
                "relative": path.relative_to(ROOT).as_posix(),
                "text": text,
                "frontmatter": frontmatter,
                "tags": {str(tag).lstrip("#") for tag in tags},
            }
        )
    return notes


def media_index() -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for path in ROOT.rglob("*"):
        if not path.is_file() or path.suffix.casefold() not in MEDIA_EXTENSIONS:
            continue
        if any(part in {".git", ".codex-tools", ".omnisvera-tools"} for part in path.parts):
            continue
        index.setdefault(path.name.casefold(), []).append(path.relative_to(ROOT).as_posix())
    return index


def normalize_media_reference(raw: str) -> str:
    value = raw.strip().strip("\"'")
    wikilink = re.fullmatch(r"!?\[\[([^\]|]+)(?:\|[^\]]+)?\]\]", value)
    return wikilink.group(1) if wikilink else value


def source_candidates(source: str, notes: list[dict]) -> list[dict]:
    tags = re.findall(r"#([\wÀ-ÿ'-]+)", source)
    folders = re.findall(r'"([^"]*)"', source)
    candidates = notes
    for folder in folders:
        if folder == "/":
            continue
        prefix = folder.strip("/") + "/"
        candidates = [note for note in candidates if note["relative"].startswith(prefix)]
    for tag in tags:
        candidates = [note for note in candidates if tag in note["tags"]]
    return candidates


def audit_queries(notes: list[dict]) -> dict:
    queries = []
    counts = Counter()
    for note in notes:
        for match in CODE_BLOCK.finditer(note["text"]):
            kind = match.group(2)
            body = strip_quote_prefix(match.group(3))
            counts[kind] += 1
            if kind not in {"dataview", "datacards"}:
                continue
            source_match = re.search(r"(?im)\bFROM\s+(.+?)\s*$", body)
            source = source_match.group(1).strip() if source_match else None
            candidates = source_candidates(source, notes) if source else []
            line = note["text"].count("\n", 0, match.start()) + 1
            queries.append(
                {
                    "file": note["relative"],
                    "line": line,
                    "kind": kind,
                    "source": source,
                    "source_candidates": len(candidates) if source else None,
                }
            )
    return {
        "block_counts": dict(sorted(counts.items())),
        "queries": queries,
        "empty_sources": [
            query
            for query in queries
            if query["source"] is not None and query["source_candidates"] == 0
        ],
    }


def audit_media(notes: list[dict]) -> list[dict]:
    index = media_index()
    missing = []
    for note in notes:
        for key in MEDIA_KEYS:
            value = note["frontmatter"].get(key)
            values = value if isinstance(value, list) else [value]
            for item in values:
                if not isinstance(item, str) or not item.strip():
                    continue
                reference = normalize_media_reference(item)
                direct = ROOT / reference
                if direct.exists() or Path(reference).name.casefold() in index:
                    continue
                missing.append(
                    {
                        "file": note["relative"],
                        "property": key,
                        "reference": item,
                    }
                )
    return missing


def audit_characters(notes: list[dict]) -> dict:
    required = {"thumbnail", "status", "role", "location", "territory", "faction", "class", "race"}
    missing = []
    empty = []
    for note in notes:
        if "character" not in note["tags"]:
            continue
        frontmatter = note["frontmatter"]
        absent = sorted(required - set(frontmatter))
        blank = sorted(
            key
            for key in required & set(frontmatter)
            if frontmatter.get(key) in (None, "", [])
        )
        if absent:
            missing.append({"file": note["relative"], "properties": absent})
        if blank:
            empty.append({"file": note["relative"], "properties": blank})
    return {"missing_properties": missing, "empty_properties": empty}


def parse_leaflet_block(body: str) -> dict:
    clean = strip_quote_prefix(body)
    result: dict[str, object] = {"markers": []}
    for line in clean.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith("marker:"):
            result["markers"].append(stripped.removeprefix("marker:").strip())
            continue
        if ":" in stripped:
            key, value = stripped.split(":", 1)
            result[key.strip()] = value.strip()
    return result


def audit_leaflet(notes: list[dict], stems: set[str]) -> dict:
    maps = []
    for note in notes:
        for match in CODE_BLOCK.finditer(note["text"]):
            if match.group(2) != "leaflet":
                continue
            params = parse_leaflet_block(match.group(3))
            marker_links = []
            unresolved = []
            for marker in params.get("markers", []):
                links = WIKILINK.findall(str(marker))
                marker_links.extend(links)
                unresolved.extend(link for link in links if Path(link).stem.casefold() not in stems)
            image = str(params.get("image", ""))
            maps.append(
                {
                    "file": note["relative"],
                    "id": params.get("id"),
                    "image": image,
                    "image_exists": bool(image and (ROOT / image).exists()),
                    "static_markers": len(params.get("markers", [])),
                    "marker_links": marker_links,
                    "unresolved_marker_links": unresolved,
                }
            )

    data_path = ROOT / ".obsidian" / "plugins" / "obsidian-leaflet-plugin" / "data.json"
    persisted = []
    if data_path.exists():
        raw = json.loads(data_path.read_text(encoding="utf-8-sig"))
        for item in raw.get("mapMarkers", []):
            persisted.append(
                {
                    "id": item.get("id"),
                    "files": item.get("files", []),
                    "markers": len(item.get("markers", [])),
                    "unlinked_markers": sum(
                        1 for marker in item.get("markers", []) if not marker.get("link")
                    ),
                }
            )
    active_ids = {item["id"] for item in maps if item.get("id")}
    stale = [item for item in persisted if item["id"] not in active_ids]
    return {"active_maps": maps, "persisted_groups": persisted, "inactive_groups": stale}


def main() -> int:
    notes = load_notes()
    stems = {note["path"].stem.casefold() for note in notes}
    result = {
        "active_notes": len(notes),
        "unbalanced_code_fences": [
            note["relative"] for note in notes if note["text"].count("```") % 2
        ],
        "queries": audit_queries(notes),
        "missing_media": audit_media(notes),
        "characters": audit_characters(notes),
        "leaflet": audit_leaflet(notes, stems),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["unbalanced_code_fences"] or result["missing_media"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
