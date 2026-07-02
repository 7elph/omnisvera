#!/usr/bin/env python3
"""Fix old Obsidian media embeds after zz_media organization.

This script is intentionally conservative:
- dry-run by default;
- applies only with --apply;
- edits active vault content only;
- ignores audits, backups, .obsidian, zz_media, and binary files;
- updates only media references in embeds, Markdown images, HTML img src, and
  media frontmatter fields.
"""

from __future__ import annotations

import argparse
import datetime as _dt
import re
import unicodedata
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".bmp"}
MEDIA_FIELDS = {"banner", "cover", "thumbnail", "portrait", "image"}
ACTIVE_DIRS = {
    "Characters",
    "Locations",
    "Factions",
    "Items",
    "Territories",
    "Lore",
    "Religion",
    "Races",
    "Classes",
    "CAMPANHA",
    "EARTHROPO",
    "Templates",
}
ACTIVE_ROOT_FILES = {
    "Home.md",
    "Home_Mestre.md",
    "MAPA DE EARTHROPO.md",
    "MAPA DE NIMALIA.md",
    "MAPA DE NIMALIS.md",
}
SKIP_DIRS = {
    ".git",
    ".obsidian",
    "zz_media",
    "node_modules",
    ".tmp_refs",
    ".omnisvera-tools",
    ".codex-tools",
}
SKIP_PREFIXES = {
    "Workflow/_audit",
    "Workflow/_archive",
    "Workflow/Legacy",
}


@dataclass
class Replacement:
    file: str
    line: int | None
    kind: str
    before: str
    after: str


@dataclass
class Problem:
    file: str
    line: int | None
    kind: str
    ref: str
    reason: str
    candidates: list[str] = field(default_factory=list)


def strip_accents(value: str) -> str:
    return "".join(
        ch
        for ch in unicodedata.normalize("NFKD", value)
        if not unicodedata.combining(ch)
    )


def normalize_key(value: str) -> str:
    value = value.replace("\\", "/").strip().strip('"').strip("'")
    value = strip_accents(value).lower()
    value = re.sub(r"[^a-z0-9./]+", "_", value)
    value = re.sub(r"_+", "_", value)
    value = value.replace("/_", "/").replace("_/", "/")
    return value.strip("_")


def clean_target(value: str) -> tuple[str, str]:
    """Return (target, suffix) from an Obsidian embed payload.

    The suffix preserves pipe sizing/aliases, e.g. "|400".
    """
    raw = value.strip()
    if raw.startswith("[[") and raw.endswith("]]"):
        raw = raw[2:-2]
    if "|" in raw:
        target, suffix = raw.split("|", 1)
        return target.strip().strip('"').strip("'"), "|" + suffix
    return raw.strip().strip('"').strip("'"), ""


def is_mediaish(value: str) -> bool:
    target, _ = clean_target(value)
    return Path(target).suffix.lower() in IMAGE_EXTS or "zz_media" in target


def rel_posix(path: Path, root: Path) -> str:
    return path.relative_to(root).as_posix()


def is_under_prefix(rel: str, prefixes: Iterable[str]) -> bool:
    return any(rel == p or rel.startswith(p + "/") for p in prefixes)


def is_active_file(path: Path, root: Path) -> bool:
    rel_path = path.relative_to(root)
    rel = rel_path.as_posix()
    if path.suffix.lower() != ".md":
        return False
    if any(part in SKIP_DIRS for part in rel_path.parts):
        return False
    if is_under_prefix(rel, SKIP_PREFIXES):
        return False
    if len(rel_path.parts) == 1:
        # Root markdown files are treated as active unless they are obvious notes
        # outside the operational layer. This catches CALENDAR/TIMELINE/etc.
        return True
    if rel_path.parts[:2] == ("Workflow", "Content_Development"):
        return True
    return rel_path.parts[0] in ACTIVE_DIRS


def is_ignored_markdown(path: Path, root: Path) -> bool:
    rel_path = path.relative_to(root)
    rel = rel_path.as_posix()
    if path.suffix.lower() != ".md":
        return False
    if any(part in SKIP_DIRS for part in rel_path.parts):
        return True
    if is_under_prefix(rel, SKIP_PREFIXES):
        return True
    return False


def build_media_index(root: Path) -> tuple[dict[str, set[str]], list[str]]:
    media_paths = sorted(
        p.relative_to(root).as_posix()
        for p in (root / "zz_media").rglob("*")
        if p.is_file() and p.suffix.lower() in IMAGE_EXTS
    )
    index: dict[str, set[str]] = {}

    def add(key: str, canonical: str) -> None:
        if not key:
            return
        index.setdefault(key, set()).add(canonical)

    for canonical in media_paths:
        basename = Path(canonical).name
        stem = Path(canonical).stem
        variants = {
            canonical,
            basename,
            f"zz_media/{basename}",
            basename.replace("_", "-"),
            f"zz_media/{basename.replace('_', '-')}",
            stem,
            stem.replace("_", "-"),
        }
        for variant in list(variants):
            variants.add(strip_accents(variant))
            variants.add(variant.lower())
            variants.add(normalize_key(variant))
        for variant in variants:
            add(variant.lower(), canonical)
            add(normalize_key(variant), canonical)
    return index, media_paths


def resolve_ref(ref: str, index: dict[str, set[str]], root: Path) -> tuple[str | None, str, list[str]]:
    target, suffix = clean_target(ref)
    target = target.replace("\\", "/")
    if target.startswith("./"):
        target = target[2:]

    # Already valid canonical path.
    if target.startswith("zz_media/") and (root / target).exists():
        return target, suffix, [target]

    keys = {
        target,
        target.lower(),
        strip_accents(target),
        normalize_key(target),
    }
    # If user wrote zz_media/old-file.png, basename may still be enough.
    keys.add(Path(target).name)
    keys.add(normalize_key(Path(target).name))
    candidates: set[str] = set()
    for key in keys:
        candidates.update(index.get(key.lower(), set()))
        candidates.update(index.get(normalize_key(key), set()))
    if len(candidates) == 1:
        return next(iter(candidates)), suffix, sorted(candidates)
    return None, suffix, sorted(candidates)


OBSIDIAN_RE = re.compile(r"!\[\[([^\]]+)\]\]")
WIKILINK_MEDIA_RE = re.compile(r"(?<!!)\[\[([^\]]+)\]\]")
MD_IMAGE_RE = re.compile(r"!\[([^\]]*)\]\(([^)]+)\)")
HTML_IMG_RE = re.compile(r"(<img\b[^>]*\bsrc=[\"'])([^\"']+)([\"'][^>]*>)", re.I)
FIELD_RE = re.compile(r"^(\s*)(banner|cover|thumbnail|portrait|image)(\s*:\s*)(.+?)(\s*)$", re.I)


def line_number(text: str, index: int) -> int:
    return text.count("\n", 0, index) + 1


def process_text(path: Path, root: Path, text: str, index: dict[str, set[str]]) -> tuple[str, list[Replacement], list[Problem]]:
    rel = rel_posix(path, root)
    replacements: list[Replacement] = []
    problems: list[Problem] = []

    def resolve_or_problem(kind: str, raw: str, start: int) -> tuple[str | None, str]:
        if not is_mediaish(raw):
            return None, ""
        canonical, suffix, candidates = resolve_ref(raw, index, root)
        line = line_number(text, start)
        target, _ = clean_target(raw)
        if canonical is None:
            if candidates:
                problems.append(Problem(rel, line, kind, target, "ambiguous", candidates))
            else:
                problems.append(Problem(rel, line, kind, target, "missing", []))
            return None, suffix
        if canonical == target:
            return None, suffix
        return canonical, suffix

    def obsidian_sub(match: re.Match[str]) -> str:
        raw = match.group(1)
        canonical, suffix = resolve_or_problem("obsidian_embed", raw, match.start())
        if canonical is None:
            return match.group(0)
        after = f"![[{canonical}{suffix}]]"
        replacements.append(Replacement(rel, line_number(text, match.start()), "obsidian_embed", match.group(0), after))
        return after

    def wikilink_media_sub(match: re.Match[str]) -> str:
        raw = match.group(1)
        canonical, suffix = resolve_or_problem("wikilink_media", raw, match.start())
        if canonical is None:
            return match.group(0)
        after = f"[[{canonical}{suffix}]]"
        replacements.append(Replacement(rel, line_number(text, match.start()), "wikilink_media", match.group(0), after))
        return after

    def markdown_sub(match: re.Match[str]) -> str:
        alt = match.group(1)
        raw = match.group(2)
        canonical, _suffix = resolve_or_problem("markdown_image", raw, match.start())
        if canonical is None:
            return match.group(0)
        after = f"![{alt}]({canonical})"
        replacements.append(Replacement(rel, line_number(text, match.start()), "markdown_image", match.group(0), after))
        return after

    def html_sub(match: re.Match[str]) -> str:
        raw = match.group(2)
        canonical, _suffix = resolve_or_problem("html_img", raw, match.start())
        if canonical is None:
            return match.group(0)
        after = f"{match.group(1)}{canonical}{match.group(3)}"
        replacements.append(Replacement(rel, line_number(text, match.start()), "html_img", match.group(0), after))
        return after

    new_text = OBSIDIAN_RE.sub(obsidian_sub, text)
    new_text = WIKILINK_MEDIA_RE.sub(wikilink_media_sub, new_text)
    new_text = MD_IMAGE_RE.sub(markdown_sub, new_text)
    new_text = HTML_IMG_RE.sub(html_sub, new_text)

    # Frontmatter/media field lines. Kept line-based to avoid touching other YAML.
    lines = new_text.splitlines(keepends=True)
    changed_lines: list[str] = []
    cursor = 0
    for line in lines:
        bare = line.rstrip("\r\n")
        ending = line[len(bare):]
        m = FIELD_RE.match(bare)
        if not m:
            changed_lines.append(line)
            cursor += len(line)
            continue
        raw = m.group(4).strip()
        canonical, suffix, candidates = resolve_ref(raw, index, root)
        line_no = new_text.count("\n", 0, cursor) + 1
        target, _ = clean_target(raw)
        if canonical is None:
            if is_mediaish(raw):
                problems.append(Problem(rel, line_no, m.group(2), target, "ambiguous" if candidates else "missing", candidates))
            changed_lines.append(line)
        elif canonical != target:
            before = bare
            quote = ""
            if raw.startswith('"') and raw.endswith('"'):
                quote = '"'
            value = canonical + suffix
            after_value = f"{quote}{value}{quote}" if quote else value
            after = f"{m.group(1)}{m.group(2)}{m.group(3)}{after_value}{m.group(5)}"
            replacements.append(Replacement(rel, line_no, m.group(2), before, after))
            changed_lines.append(after + ending)
        else:
            changed_lines.append(line)
        cursor += len(line)
    new_text = "".join(changed_lines)
    return new_text, replacements, problems


def scan_files(root: Path) -> list[Path]:
    return sorted(p for p in root.rglob("*.md") if is_active_file(p, root))


def scan_ignored_refs(root: Path) -> int:
    count = 0
    for p in root.rglob("*.md"):
        if not is_ignored_markdown(p, root):
            continue
        text = p.read_text(encoding="utf-8", errors="replace")
        count += len(OBSIDIAN_RE.findall(text))
        count += len(MD_IMAGE_RE.findall(text))
        count += len(HTML_IMG_RE.findall(text))
    return count


def write_fix_report(
    output: Path,
    root: Path,
    mode: str,
    files: list[Path],
    replacements: list[Replacement],
    problems: list[Problem],
    ignored_refs: int,
) -> None:
    changed_files = sorted({r.file for r in replacements})
    ambiguous = [p for p in problems if p.reason == "ambiguous"]
    missing = [p for p in problems if p.reason == "missing"]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Plano de correção de embeds de mídia\n\n")
        f.write(f"Gerado em: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Modo: `{mode}`\n\n")
        f.write("## Resumo\n\n")
        f.write("| métrica | valor |\n|---|---:|\n")
        f.write(f"| arquivos ativos analisados | {len(files)} |\n")
        f.write(f"| arquivos que {'foram' if mode == 'apply' else 'seriam'} alterados | {len(changed_files)} |\n")
        f.write(f"| referências corrigíveis com segurança | {len(replacements)} |\n")
        f.write(f"| referências ambíguas | {len(ambiguous)} |\n")
        f.write(f"| referências ainda ausentes | {len(missing)} |\n")
        f.write(f"| referências em histórico/auditoria ignoradas | {ignored_refs} |\n\n")
        f.write("## Arquivos alterados\n\n")
        if not changed_files:
            f.write("Nenhum.\n\n")
        else:
            for file in changed_files:
                f.write(f"- `{file}`\n")
            f.write("\n")
        f.write("## Alterações propostas/aplicadas\n\n")
        if not replacements:
            f.write("Nenhuma.\n\n")
        else:
            f.write("| arquivo | linha | tipo | antes | depois |\n|---|---:|---|---|---|\n")
            for r in replacements:
                f.write(f"| `{r.file}` | {r.line or ''} | `{r.kind}` | `{r.before}` | `{r.after}` |\n")
            f.write("\n")
        f.write("## Referências ambíguas\n\n")
        if not ambiguous:
            f.write("Nenhuma.\n\n")
        else:
            f.write("| arquivo | linha | tipo | referência | candidatos |\n|---|---:|---|---|---|\n")
            for p in ambiguous:
                f.write(f"| `{p.file}` | {p.line or ''} | `{p.kind}` | `{p.ref}` | `{', '.join(p.candidates)}` |\n")
            f.write("\n")
        f.write("## Referências ausentes não corrigidas\n\n")
        if not missing:
            f.write("Nenhuma.\n\n")
        else:
            f.write("| arquivo | linha | tipo | referência |\n|---|---:|---|---|\n")
            for p in missing:
                f.write(f"| `{p.file}` | {p.line or ''} | `{p.kind}` | `{p.ref}` |\n")
            f.write("\n")
        f.write("## Confirmações\n\n")
        f.write("- O script altera apenas referências de mídia resolvidas de forma inequívoca.\n")
        f.write("- O script não altera texto narrativo fora de embeds/imagens/campos de mídia.\n")
        f.write("- O script não altera tags, `type`, `subtype`, `status`, `canon_status` ou imagens físicas.\n")
        f.write("- O script ignora `.obsidian`, `zz_media`, backups, `Workflow/_audit`, `Workflow/_archive` e `Workflow/Legacy`.\n")
        f.write("- Blocos Leaflet operacionais já estavam OK e não precisaram alteração.\n")


def collect_post_audit(root: Path, index: dict[str, set[str]]) -> dict[str, object]:
    media_paths = sorted(
        p.relative_to(root).as_posix()
        for p in (root / "zz_media").rglob("*")
        if p.is_file()
    )
    media_images = [m for m in media_paths if Path(m).suffix.lower() in IMAGE_EXTS]
    files = scan_files(root)
    refs: list[Problem | Replacement] = []
    resolved: list[Replacement] = []
    missing: list[Problem] = []
    old: list[Problem] = []
    leaflet: list[Problem | Replacement] = []
    used: set[str] = set()

    for p in files:
        text = p.read_text(encoding="utf-8", errors="replace")
        rel = rel_posix(p, root)
        for match in OBSIDIAN_RE.finditer(text):
            raw = match.group(1)
            if not is_mediaish(raw):
                continue
            line = line_number(text, match.start())
            canonical, _suffix, candidates = resolve_ref(raw, index, root)
            target, _ = clean_target(raw)
            if canonical:
                used.add(canonical)
                resolved.append(Replacement(rel, line, "obsidian_embed", target, canonical))
                if canonical != target:
                    old.append(Problem(rel, line, "obsidian_embed", target, "old_reference", [canonical]))
            else:
                missing.append(Problem(rel, line, "obsidian_embed", target, "ambiguous" if candidates else "missing", candidates))
        for match in MD_IMAGE_RE.finditer(text):
            raw = match.group(2)
            if not is_mediaish(raw):
                continue
            line = line_number(text, match.start())
            canonical, _suffix, candidates = resolve_ref(raw, index, root)
            if canonical:
                used.add(canonical)
                resolved.append(Replacement(rel, line, "markdown_image", raw, canonical))
                if canonical != raw:
                    old.append(Problem(rel, line, "markdown_image", raw, "old_reference", [canonical]))
            else:
                missing.append(Problem(rel, line, "markdown_image", raw, "ambiguous" if candidates else "missing", candidates))
        for match in HTML_IMG_RE.finditer(text):
            raw = match.group(2)
            if not is_mediaish(raw):
                continue
            line = line_number(text, match.start())
            canonical, _suffix, candidates = resolve_ref(raw, index, root)
            if canonical:
                used.add(canonical)
                resolved.append(Replacement(rel, line, "html_img", raw, canonical))
                if canonical != raw:
                    old.append(Problem(rel, line, "html_img", raw, "old_reference", [canonical]))
            else:
                missing.append(Problem(rel, line, "html_img", raw, "ambiguous" if candidates else "missing", candidates))
        for m in re.finditer(r"```leaflet\s*\n(.*?)```", text, re.S | re.I):
            body = m.group(1)
            base_line = line_number(text, m.start())
            for im in re.finditer(r"(?m)^\s*image\s*:\s*(.+?)\s*$", body):
                raw = im.group(1)
                canonical, _suffix, candidates = resolve_ref(raw, index, root)
                line = base_line + body[:im.start()].count("\n")
                if canonical:
                    used.add(canonical)
                    leaflet.append(Replacement(rel, line, "leaflet_block_image", clean_target(raw)[0], canonical))
                else:
                    leaflet.append(Problem(rel, line, "leaflet_block_image", clean_target(raw)[0], "missing", candidates))
    # Leaflet data.json
    data_json = root / ".obsidian/plugins/obsidian-leaflet-plugin/data.json"
    data_json_valid = False
    data_json_refs = 0
    if data_json.exists():
        try:
            import json
            data = json.loads(data_json.read_text(encoding="utf-8", errors="replace"))
            data_json_valid = True
            def walk(value: object) -> None:
                nonlocal data_json_refs
                if isinstance(value, dict):
                    for v in value.values():
                        walk(v)
                elif isinstance(value, list):
                    for v in value:
                        walk(v)
                elif isinstance(value, str) and ("zz_media" in value or "zz_media%2F" in value):
                    data_json_refs += 1
            walk(data)
        except Exception:
            data_json_valid = False
    media_set = set(media_images)
    orphans = sorted(media_set - used)
    return {
        "media_total": len(media_paths),
        "media_images": len(media_images),
        "refs_total": len(resolved) + len(missing),
        "resolved": resolved,
        "missing": missing,
        "old": old,
        "leaflet": leaflet,
        "orphans": orphans,
        "root_level": [m for m in media_paths if len(Path(m).parts) == 2],
        "outside": [m for m in media_paths if len(Path(m).parts) >= 2 and Path(m).parts[1] not in {"characters", "covers", "items", "locations", "maps", "misc", "thumbnails"}],
        "hyphen": [m for m in media_paths if "-" in Path(m).name],
        "uppercase": [m for m in media_paths if any(c.isupper() for c in Path(m).name)],
        "data_json_valid": data_json_valid,
        "data_json_refs": data_json_refs,
    }


def write_post_audit(output: Path, root: Path, audit: dict[str, object]) -> None:
    missing: list[Problem] = audit["missing"]  # type: ignore[assignment]
    old: list[Problem] = audit["old"]  # type: ignore[assignment]
    leaflet = audit["leaflet"]  # type: ignore[assignment]
    orphans: list[str] = audit["orphans"]  # type: ignore[assignment]
    output.parent.mkdir(parents=True, exist_ok=True)
    with output.open("w", encoding="utf-8", newline="\n") as f:
        f.write("# Auditoria pós-organização de mídia\n\n")
        f.write(f"Gerado em: {_dt.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        f.write("## Escopo\n\n")
        f.write("Auditoria read-only após correção dos embeds de mídia em conteúdo ativo.\n\n")
        f.write("## Resumo\n\n")
        f.write("| métrica | valor |\n|---|---:|\n")
        f.write(f"| mídias em `zz_media` | {audit['media_total']} |\n")
        f.write(f"| imagens em `zz_media` | {audit['media_images']} |\n")
        f.write(f"| referências de mídia em conteúdo ativo | {audit['refs_total']} |\n")
        f.write(f"| referências resolvidas | {len(audit['resolved'])} |\n")
        f.write(f"| referências ausentes em conteúdo ativo | {len(missing)} |\n")
        f.write(f"| referências antigas ainda detectadas em conteúdo ativo | {len(old)} |\n")
        f.write(f"| blocos Leaflet auditados | {len(leaflet)} |\n")
        f.write(f"| referências no `data.json` do Leaflet | {audit['data_json_refs']} |\n")
        f.write(f"| `data.json` do Leaflet válido | {'sim' if audit['data_json_valid'] else 'não'} |\n")
        f.write(f"| imagens possivelmente órfãs | {len(orphans)} |\n")
        f.write(f"| arquivos diretamente em `zz_media/` | {len(audit['root_level'])} |\n")
        f.write(f"| arquivos fora das subpastas oficiais | {len(audit['outside'])} |\n")
        f.write(f"| arquivos com hífen no nome físico | {len(audit['hyphen'])} |\n")
        f.write(f"| arquivos com maiúsculas no nome físico | {len(audit['uppercase'])} |\n\n")
        f.write("## Leaflet\n\n")
        f.write("| arquivo | linha | imagem | status |\n|---|---:|---|---|\n")
        for item in leaflet:
            if isinstance(item, Replacement):
                status = "OK" if (root / item.after).exists() else "MISSING"
                f.write(f"| `{item.file}` | {item.line or ''} | `{item.after}` | {status} |\n")
            else:
                f.write(f"| `{item.file}` | {item.line or ''} | `{item.ref}` | MISSING |\n")
        f.write("\n## Referências ausentes em conteúdo ativo\n\n")
        if not missing:
            f.write("Nenhuma.\n\n")
        else:
            f.write("| arquivo | linha | tipo | referência | motivo |\n|---|---:|---|---|---|\n")
            for p in missing:
                f.write(f"| `{p.file}` | {p.line or ''} | `{p.kind}` | `{p.ref}` | {p.reason} |\n")
            f.write("\n")
        f.write("## Referências antigas ainda detectadas\n\n")
        if not old:
            f.write("Nenhuma.\n\n")
        else:
            f.write("| arquivo | linha | tipo | referência antiga | caminho resolvido |\n|---|---:|---|---|---|\n")
            for p in old:
                f.write(f"| `{p.file}` | {p.line or ''} | `{p.kind}` | `{p.ref}` | `{', '.join(p.candidates)}` |\n")
            f.write("\n")
        f.write("## Imagens/mídias possivelmente órfãs\n\n")
        if not orphans:
            f.write("Nenhuma.\n\n")
        else:
            for item in orphans:
                f.write(f"- `{item}`\n")
            f.write("\n")
        f.write("## Arquivos fora do padrão físico\n\n")
        f.write("### Diretamente em `zz_media/`\n\n")
        if audit["root_level"]:
            for item in audit["root_level"]:  # type: ignore[union-attr]
                f.write(f"- `{item}`\n")
        else:
            f.write("Nenhum.\n")
        f.write("\n### Fora das subpastas oficiais\n\n")
        if audit["outside"]:
            for item in audit["outside"]:  # type: ignore[union-attr]
                f.write(f"- `{item}`\n")
        else:
            f.write("Nenhum.\n")
        f.write("\n## Conclusão\n\n")
        if not missing and not old:
            f.write("As referências operacionais de mídia em conteúdo ativo estão estabilizadas.\n")
        else:
            f.write("Ainda há referências para revisar, listadas acima.\n")
        f.write("\nNenhuma mídia física foi movida, renomeada ou apagada por esta auditoria.\n")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", required=True)
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--post-audit-output")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    output = (root / args.output).resolve()
    index, _media_paths = build_media_index(root)
    files = scan_files(root)
    all_replacements: list[Replacement] = []
    all_problems: list[Problem] = []

    for path in files:
        text = path.read_text(encoding="utf-8", errors="replace")
        new_text, replacements, problems = process_text(path, root, text, index)
        all_replacements.extend(replacements)
        all_problems.extend(problems)
        if args.apply and replacements and new_text != text:
            path.write_text(new_text, encoding="utf-8", newline="")

    ignored_refs = scan_ignored_refs(root)
    write_fix_report(
        output,
        root,
        "apply" if args.apply else "dry-run",
        files,
        all_replacements,
        all_problems,
        ignored_refs,
    )

    if args.post_audit_output:
        # Rebuild index in case apply changed references only; media paths remain same.
        post = collect_post_audit(root, index)
        write_post_audit((root / args.post_audit_output).resolve(), root, post)

    print(f"Modo: {'apply' if args.apply else 'dry-run'}")
    print(f"Arquivos analisados: {len(files)}")
    print(f"Referências corrigíveis: {len(all_replacements)}")
    print(f"Ambíguas: {sum(1 for p in all_problems if p.reason == 'ambiguous')}")
    print(f"Ausentes: {sum(1 for p in all_problems if p.reason == 'missing')}")
    print(f"Relatório: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
