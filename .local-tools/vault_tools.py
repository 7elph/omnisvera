from __future__ import annotations

import argparse
import json
import math
import re
import subprocess
import sys
from pathlib import Path

import ollama
import yaml

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")


EXCLUDED_DIRS = {
    ".git",
    ".obsidian",
    ".codex-tools",
    ".tmp_refs",
    ".omnisvera-tools",
    ".local-tools",
    ".local-index",
    ".ollama",
    "zz_media",
    "z_Assets",
}
MEDIA_EXTENSIONS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".webp",
    ".svg",
    ".bmp",
    ".mp3",
    ".wav",
    ".ogg",
    ".mp4",
    ".webm",
    ".pdf",
}
WIKILINK = re.compile(r"!?\[\[([^\]|#]+)")
FRONTMATTER = re.compile(r"\A---\s*\n(.*?)\n---\s*(?:\n|\Z)", re.DOTALL)
HEADING = re.compile(r"(?m)^#{1,6}\s+.+$")


def is_legacy_note(path: Path) -> bool:
    return path.name.startswith("Legacy -") or (
        "Workflow" in path.parts and "Legacy" in path.parts
    )


class UniqueLoader(yaml.SafeLoader):
    pass


def unique_mapping(loader: UniqueLoader, node: yaml.Node, deep: bool = False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise ValueError(f"chave YAML duplicada: {key}")
        result[key] = loader.construct_object(value_node, deep=deep)
    return result


UniqueLoader.add_constructor(
    yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping
)


def markdown_files(root: Path, include_legacy: bool = False) -> list[Path]:
    files = []
    for path in root.rglob("*.md"):
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if not include_legacy and is_legacy_note(path):
            continue
        files.append(path)
    return sorted(files)


def changed_markdown_files(root: Path) -> list[Path]:
    result = subprocess.run(
        ["git", "diff", "--name-only", "--diff-filter=ACMR", "HEAD"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    untracked = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        cwd=root,
        check=False,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    return [
        root / line
        for line in dict.fromkeys(
            [*result.stdout.splitlines(), *untracked.stdout.splitlines()]
        )
        if line.lower().endswith(".md") and (root / line).exists()
    ]


def audit(root: Path, changed_only: bool, include_legacy: bool) -> int:
    files = (
        changed_markdown_files(root)
        if changed_only
        else markdown_files(root, include_legacy=include_legacy)
    )
    if not include_legacy:
        files = [path for path in files if not is_legacy_note(path)]
    all_notes = markdown_files(root, include_legacy=True)
    stems = {path.stem.casefold() for path in all_notes}
    yaml_errors: list[tuple[str, str]] = []
    unresolved: list[tuple[str, str]] = []
    empty: list[str] = []

    for path in files:
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        relative = str(path.relative_to(root))
        if not text.strip():
            empty.append(relative)
            continue

        match = FRONTMATTER.match(text)
        if text.startswith("---") and not match:
            yaml_errors.append((relative, "frontmatter sem fechamento"))
        elif match:
            try:
                yaml.load(match.group(1), Loader=UniqueLoader)
            except Exception as exc:
                yaml_errors.append((relative, str(exc).splitlines()[0]))

        for raw_target in WIKILINK.findall(text):
            target = raw_target.strip().replace("\\", "/")
            if not target or re.fullmatch(r"[-+]?\d+(?:\.\d+)?\s*,\s*[-+]?\d+(?:\.\d+)?", target):
                continue
            if Path(target).suffix.casefold() in MEDIA_EXTENSIONS:
                continue
            direct = root / (target if target.lower().endswith(".md") else f"{target}.md")
            if direct.exists() or Path(target).stem.casefold() in stems:
                continue
            unresolved.append((relative, raw_target))

    print(
        json.dumps(
            {
                "arquivos": len(files),
                "yaml_erros": yaml_errors,
                "wikilinks_nao_resolvidos": unresolved,
                "arquivos_vazios": empty,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 1 if yaml_errors else 0


def split_chunks(path: Path, text: str, max_chars: int = 1800) -> list[dict]:
    frontmatter = FRONTMATTER.match(text)
    if frontmatter:
        text = text[frontmatter.end() :]
    starts = [match.start() for match in HEADING.finditer(text)]
    starts = [0, *starts, len(text)]
    sections = []
    for start, end in zip(starts, starts[1:]):
        section = text[start:end].strip()
        if section:
            sections.append(section)

    chunks = []
    for section in sections:
        for offset in range(0, len(section), max_chars):
            body = section[offset : offset + max_chars].strip()
            if body:
                chunks.append(
                    {
                        "path": str(path),
                        "text": body,
                    }
                )
    return chunks


def build_index(root: Path, include_legacy: bool) -> int:
    chunks = []
    for path in markdown_files(root, include_legacy=include_legacy):
        text = path.read_text(encoding="utf-8-sig", errors="replace")
        chunks.extend(split_chunks(path.relative_to(root), text))

    batch_size = 16
    for offset in range(0, len(chunks), batch_size):
        batch = chunks[offset : offset + batch_size]
        response = ollama.embed(
            model="nomic-embed-text",
            input=[item["text"] for item in batch],
        )
        for item, embedding in zip(batch, response["embeddings"]):
            item["embedding"] = embedding
        print(f"indexados {min(offset + batch_size, len(chunks))}/{len(chunks)}", file=sys.stderr)

    target = root / ".local-index" / "vault.jsonl"
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("w", encoding="utf-8") as handle:
        for item in chunks:
            handle.write(json.dumps(item, ensure_ascii=False) + "\n")
    print(f"{len(chunks)} trechos gravados em {target}")
    return 0


def cosine(left: list[float], right: list[float]) -> float:
    numerator = sum(a * b for a, b in zip(left, right))
    left_norm = math.sqrt(sum(a * a for a in left))
    right_norm = math.sqrt(sum(b * b for b in right))
    return numerator / (left_norm * right_norm) if left_norm and right_norm else 0.0


def semantic_search(root: Path, query: str, limit: int) -> int:
    index_path = root / ".local-index" / "vault.jsonl"
    if not index_path.exists():
        print("Índice ausente. Execute primeiro: vault_tools.py index", file=sys.stderr)
        return 2
    query_vector = ollama.embed(model="nomic-embed-text", input=query)["embeddings"][0]
    rows = []
    with index_path.open(encoding="utf-8") as handle:
        for line in handle:
            item = json.loads(line)
            item["score"] = cosine(query_vector, item.pop("embedding"))
            rows.append(item)
    rows.sort(key=lambda item: item["score"], reverse=True)
    for item in rows[:limit]:
        preview = re.sub(r"\s+", " ", item["text"])[:350]
        print(f"{item['score']:.4f}\t{item['path']}\t{preview}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Ferramentas locais para o vault Omnisvera")
    parser.add_argument("--root", type=Path, default=Path.cwd())
    subparsers = parser.add_subparsers(dest="command", required=True)

    audit_parser = subparsers.add_parser("audit")
    audit_parser.add_argument("--changed", action="store_true")
    audit_parser.add_argument("--include-legacy", action="store_true")

    index_parser = subparsers.add_parser("index")
    index_parser.add_argument("--include-legacy", action="store_true")

    search_parser = subparsers.add_parser("search")
    search_parser.add_argument("query")
    search_parser.add_argument("--limit", type=int, default=8)

    args = parser.parse_args()
    root = args.root.resolve()
    if args.command == "audit":
        return audit(root, args.changed, args.include_legacy)
    if args.command == "index":
        return build_index(root, args.include_legacy)
    return semantic_search(root, args.query, args.limit)


if __name__ == "__main__":
    raise SystemExit(main())
