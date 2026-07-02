#!/usr/bin/env python3
"""Audita e organiza assets em zz_media.

Por padrão, roda em dry-run e gera relatório Markdown. Use --apply para mover
arquivos e atualizar referências, mas o script aborta se houver colisões ou
se uma referência necessária estiver em arquivo modificado antes da tarefa.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import unicodedata
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from urllib.parse import quote


IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".bmp"}
TEXT_EXTS = {".md", ".json", ".css", ".js", ".html", ".htm", ".yaml", ".yml"}
SKIP_DIRS = {
    ".git",
    "node_modules",
    ".tmp_refs",
    ".omnisvera-tools",
    ".codex-tools",
    "__pycache__",
}

FRONTMATTER_MEDIA_FIELDS = {"cover", "thumbnail", "portrait", "image", "banner", "map_image", "handout_image"}
MAX_TEXT_FILE_BYTES = 2_000_000


def should_skip_text_file(path: Path) -> bool:
    name = path.name.lower()
    rel = path.as_posix().lower()
    if "/workflow/_audit/" in rel or "\\workflow\\_audit\\" in rel:
        return True
    if "copilot-index" in name:
        return True
    if ".before" in name and path.suffix.lower() == ".json":
        return True
    if name.startswith("workspace") and path.suffix.lower() == ".json":
        return True
    if path.stat().st_size > MAX_TEXT_FILE_BYTES and "obsidian-leaflet-plugin/data.json" not in rel:
        return True
    return False


@dataclass
class ImageInfo:
    path: Path
    rel: str
    size: int
    ext: str
    has_hyphen: bool
    has_space: bool
    has_accent: bool
    has_upper: bool
    tracked: bool
    untracked: bool
    dirty: bool
    references: list["Reference"] = field(default_factory=list)
    target_rel: str = ""
    category: str = "misc"
    reason: str = ""


@dataclass
class Reference:
    file: str
    line: int
    kind: str
    text: str
    field: str = ""


@dataclass
class Plan:
    images: list[ImageInfo]
    collisions: dict[str, list[str]]
    dirty_reference_files: set[str]
    text_replacements: dict[str, list[tuple[str, str]]]
    ambiguous: list[str]
    created_dirs: set[str]
    changed_files: set[str]


def run_git(root: Path, args: list[str], check: bool = False) -> subprocess.CompletedProcess[str]:
    return subprocess.run(["git", *args], cwd=root, text=True, capture_output=True, check=check)


def git_status(root: Path) -> tuple[set[str], set[str], set[str], str]:
    proc = run_git(root, ["status", "--porcelain=v1"])
    modified: set[str] = set()
    untracked: set[str] = set()
    dirty: set[str] = set()
    for raw in proc.stdout.splitlines():
        if not raw:
            continue
        status = raw[:2]
        path = raw[3:].replace("\\", "/")
        if " -> " in path:
            path = path.split(" -> ", 1)[1]
        dirty.add(path)
        if status == "??":
            untracked.add(path)
        else:
            modified.add(path)
    return modified, untracked, dirty, proc.stdout


def git_tracked(root: Path) -> set[str]:
    proc = run_git(root, ["ls-files"])
    return {line.replace("\\", "/") for line in proc.stdout.splitlines() if line}


def has_accent(text: str) -> bool:
    return any(unicodedata.category(ch) == "Mn" for ch in unicodedata.normalize("NFD", text))


def normalize_stem(stem: str) -> str:
    value = unicodedata.normalize("NFD", stem)
    value = "".join(ch for ch in value if unicodedata.category(ch) != "Mn")
    value = value.lower()
    value = value.replace("-", "_").replace(" ", "_")
    value = re.sub(r"[^a-z0-9_]+", "_", value)
    value = re.sub(r"_+", "_", value).strip("_")
    return value or "media"


def iter_text_files(root: Path) -> list[Path]:
    result: list[Path] = []
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_DIRS]
        base = Path(current_root)
        for filename in files:
            path = base / filename
            if path.suffix.lower() in TEXT_EXTS and not should_skip_text_file(path):
                result.append(path)
    return result


def relpath(root: Path, path: Path) -> str:
    return path.relative_to(root).as_posix()


def collect_images(root: Path, tracked: set[str], untracked: set[str], dirty: set[str]) -> list[ImageInfo]:
    media_root = root / "zz_media"
    images: list[ImageInfo] = []
    if not media_root.exists():
        return images
    for path in media_root.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in IMAGE_EXTS:
            continue
        rel = relpath(root, path)
        name = path.name
        images.append(
            ImageInfo(
                path=path,
                rel=rel,
                size=path.stat().st_size,
                ext=path.suffix,
                has_hyphen="-" in name,
                has_space=" " in name,
                has_accent=has_accent(name),
                has_upper=any(ch.isupper() for ch in name),
                tracked=rel in tracked,
                untracked=rel in untracked,
                dirty=rel in dirty,
            )
        )
    return sorted(images, key=lambda item: item.rel.lower())


def basename_variants(image: ImageInfo) -> set[str]:
    rel = image.rel
    name = Path(rel).name
    encoded_rel = quote(rel, safe="")
    variants = {
        rel,
        rel.replace("/", "\\"),
        name,
        f"[[{rel}]]",
        f"[[{name}]]",
        f"![[{rel}]]",
        f"![[{name}]]",
        encoded_rel,
    }
    return variants


def find_references(root: Path, images: list[ImageInfo]) -> None:
    by_name = {Path(img.rel).name.lower(): img for img in images}
    by_rel = {img.rel.lower(): img for img in images}
    image_ext_pattern = re.compile(r"\.(png|jpe?g|webp|gif|svg|bmp)", re.IGNORECASE)
    text_files = iter_text_files(root)
    for path in text_files:
        rel_file = relpath(root, path)
        try:
            lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
        except Exception:
            continue
        for line_no, line in enumerate(lines, 1):
            if not image_ext_pattern.search(line):
                continue
            lower_line = line.lower()
            for key, image in by_rel.items():
                if key in lower_line or quote(image.rel, safe="").lower() in lower_line:
                    image.references.append(classify_reference(rel_file, line_no, line, image))
            for name, image in by_name.items():
                if name in lower_line and image.rel.lower() not in lower_line:
                    # Só considera basename quando aparece em sintaxes comuns de imagem.
                    if any(token in lower_line for token in ["[[", "src=", "](", "image:", "cover:", "thumbnail:", "portrait:", "banner:"]):
                        image.references.append(classify_reference(rel_file, line_no, line, image))


def classify_reference(file: str, line_no: int, line: str, image: ImageInfo) -> Reference:
    stripped = line.strip()
    kind = "text"
    field = ""
    if re.match(r"^[A-Za-z0-9_-]+:\s*", stripped):
        field = stripped.split(":", 1)[0].strip()
        if field in FRONTMATTER_MEDIA_FIELDS:
            kind = "frontmatter"
    if "```leaflet" in stripped or stripped.startswith("image:"):
        kind = "leaflet"
    if "<img" in stripped.lower():
        kind = "html"
    if "![[" in stripped or stripped.startswith("!["):
        kind = "markdown_image"
    if file.endswith(".json"):
        kind = "json"
    if file.endswith(".css"):
        kind = "css"
    return Reference(file=file, line=line_no, kind=kind, text=line.strip(), field=field)


def classify_image(image: ImageInfo) -> tuple[str, str]:
    name = Path(image.rel).name.lower()
    refs = image.references
    ref_files = {ref.file for ref in refs}
    fields = {ref.field for ref in refs if ref.field}
    if any(part in name for part in ["mapa", "earthropo", "nimalia", "nimalis"]) or any(
        ref.file.startswith("MAPA ") or ref.kind == "leaflet" for ref in refs
    ):
        return "maps", "mapa ou referência Leaflet detectada"
    if name.startswith("th_") or "thumbnail" in fields:
        return "thumbnails", "thumbnail detectado por nome/campo"
    if "portrait" in fields:
        return "portraits", "portrait detectado por campo"
    if any(file.startswith("Characters/") for file in ref_files):
        return "characters", "referenciado por nota de personagem"
    if any(file.startswith("Locations/") for file in ref_files):
        return "locations", "referenciado por nota de local"
    if any(file.startswith("Territories/") for file in ref_files):
        return "locations", "referenciado por nota de território/região"
    if any(file.startswith("Factions/") for file in ref_files):
        return "factions", "referenciado por nota de facção"
    if any(file.startswith("Items/") for file in ref_files):
        return "items", "referenciado por nota de item"
    if "cover" in fields or "banner" in fields:
        return "covers", "cover/banner detectado sem categoria mais específica"
    return "misc", "categoria incerta"


def build_plan(root: Path) -> Plan:
    modified, untracked, dirty, _status_text = git_status(root)
    tracked = git_tracked(root)
    images = collect_images(root, tracked, untracked, dirty)
    find_references(root, images)

    targets: dict[str, list[str]] = {}
    created_dirs: set[str] = set()
    for image in images:
        category, reason = classify_image(image)
        image.category = category
        image.reason = reason
        normalized = normalize_stem(Path(image.rel).stem) + image.path.suffix.lower()
        target = f"zz_media/{category}/{normalized}"
        image.target_rel = target
        created_dirs.add(f"zz_media/{category}")
        targets.setdefault(target.lower(), []).append(image.rel)

    collisions = {target: srcs for target, srcs in targets.items() if len(srcs) > 1}
    ambiguous = [image.rel for image in images if image.category == "misc" and not image.references]

    text_replacements: dict[str, list[tuple[str, str]]] = {}
    changed_files: set[str] = set()
    dirty_reference_files: set[str] = set()
    for image in images:
        if image.rel == image.target_rel:
            continue
        old_rel = image.rel
        new_rel = image.target_rel
        old_name = Path(old_rel).name
        new_name = Path(new_rel).name
        replacements = [
            (old_rel, new_rel),
            (old_rel.replace("/", "\\"), new_rel.replace("/", "\\")),
            (quote(old_rel, safe=""), quote(new_rel, safe="")),
            (f"[[{old_rel}]]", f"[[{new_rel}]]"),
            (f"![[{old_rel}]]", f"![[{new_rel}]]"),
            (f"[[{old_name}]]", f"[[{new_rel}]]"),
            (f"![[{old_name}]]", f"![[{new_rel}]]"),
        ]
        for ref in image.references:
            text_replacements.setdefault(ref.file, [])
            text_replacements[ref.file].extend(replacements)
            changed_files.add(ref.file)
            if ref.file in dirty:
                dirty_reference_files.add(ref.file)
    return Plan(
        images=images,
        collisions=collisions,
        dirty_reference_files=dirty_reference_files,
        text_replacements=text_replacements,
        ambiguous=ambiguous,
        created_dirs=created_dirs,
        changed_files=changed_files,
    )


def apply_replacements(root: Path, replacements: dict[str, list[tuple[str, str]]]) -> int:
    changed = 0
    for rel_file, pairs in sorted(replacements.items()):
        path = root / rel_file
        if not path.exists() or path.suffix.lower() not in TEXT_EXTS:
            continue
        text = path.read_text(encoding="utf-8", errors="replace")
        new_text = text
        seen: set[tuple[str, str]] = set()
        for old, new in pairs:
            if old == new or (old, new) in seen:
                continue
            seen.add((old, new))
            new_text = new_text.replace(old, new)
        if new_text != text:
            path.write_text(new_text, encoding="utf-8")
            changed += 1
    return changed


def move_images(root: Path, images: list[ImageInfo]) -> int:
    moved = 0
    for image in images:
        if image.rel == image.target_rel:
            continue
        src = root / image.rel
        dst = root / image.target_rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        if dst.exists():
            raise RuntimeError(f"Destino já existe: {image.target_rel}")
        if image.tracked:
            proc = run_git(root, ["mv", image.rel, image.target_rel])
            if proc.returncode != 0:
                # Fallback para arquivos tracked com mudanças de case/Windows.
                tmp = dst.parent / f"__tmp_{dst.name}"
                tmp_rel = relpath(root, tmp)
                run_git(root, ["mv", image.rel, tmp_rel], check=True)
                run_git(root, ["mv", tmp_rel, image.target_rel], check=True)
        else:
            shutil.move(str(src), str(dst))
        moved += 1
    return moved


def validate_json(root: Path) -> list[str]:
    problems: list[str] = []
    for current_root, dirs, files in os.walk(root):
        dirs[:] = [directory for directory in dirs if directory not in SKIP_DIRS]
        base = Path(current_root)
        for filename in files:
            path = base / filename
            if path.suffix.lower() != ".json":
                continue
            try:
                json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception as exc:
                problems.append(f"{relpath(root, path)}: {exc}")
    return problems


def render_report(root: Path, plan: Plan, mode: str, applied_moves: int = 0, applied_refs: int = 0, status_text: str = "") -> str:
    images = plan.images
    referenced = [img for img in images if img.references]
    orphan = [img for img in images if not img.references]
    rename_needed = [img for img in images if img.rel != img.target_rel]
    new_images = [img for img in images if img.untracked]
    dirty_images = [img for img in images if img.dirty]
    refs_to_update = sum(1 for img in images if img.rel != img.target_rel for _ in img.references)
    lines: list[str] = [
        "# Omnisvera — Organização de Mídia",
        "",
        f"Gerado em: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"Modo: `{mode}`",
        "",
        "## Estado inicial do Git",
        "",
        "```text",
        status_text.strip() or "(sem saída registrada)",
        "```",
        "",
        "## Resumo",
        "",
        "| métrica | valor |",
        "|---|---:|",
        f"| imagens encontradas | {len(images)} |",
        f"| imagens com hífen | {sum(img.has_hyphen for img in images)} |",
        f"| imagens com espaço | {sum(img.has_space for img in images)} |",
        f"| imagens com acento | {sum(img.has_accent for img in images)} |",
        f"| imagens com maiúsculas | {sum(img.has_upper for img in images)} |",
        f"| imagens novas/untracked | {len(new_images)} |",
        f"| imagens usadas | {len(referenced)} |",
        f"| imagens possivelmente órfãs | {len(orphan)} |",
        f"| imagens com renome/movimento planejado | {len(rename_needed)} |",
        f"| referências a atualizar | {refs_to_update} |",
        f"| arquivos com referências a atualizar | {len(plan.changed_files)} |",
        f"| colisões | {len(plan.collisions)} |",
        f"| referências em arquivos já sujos | {len(plan.dirty_reference_files)} |",
        f"| movimentos aplicados | {applied_moves} |",
        f"| arquivos de referência alterados | {applied_refs} |",
        "",
        "## Subpastas planejadas",
        "",
    ]
    for directory in sorted(plan.created_dirs):
        lines.append(f"- `{directory}`")

    lines.extend(["", "## Colisões", ""])
    if plan.collisions:
        for target, srcs in sorted(plan.collisions.items()):
            lines.append(f"- `{target}` <= {', '.join(f'`{src}`' for src in srcs)}")
    else:
        lines.append("- Nenhuma colisão detectada.")

    lines.extend(["", "## Bloqueadores por arquivo já sujo", ""])
    if plan.dirty_reference_files:
        lines.append("Estes arquivos precisariam de atualização de caminho de imagem, mas já estavam modificados antes da tarefa:")
        for rel in sorted(plan.dirty_reference_files):
            lines.append(f"- `{rel}`")
    else:
        lines.append("- Nenhum.")

    lines.extend(
        [
            "",
            "## Plano de renomeação/movimentação",
            "",
            "| atual | destino | categoria | tamanho | tracked | untracked | usado | motivo |",
            "|---|---|---|---:|---|---|---:|---|",
        ]
    )
    for img in images:
        lines.append(
            f"| `{img.rel}` | `{img.target_rel}` | `{img.category}` | {img.size} | "
            f"{'sim' if img.tracked else 'não'} | {'sim' if img.untracked else 'não'} | {len(img.references)} | {img.reason} |"
        )

    lines.extend(
        [
            "",
            "## Referências que seriam atualizadas",
            "",
            "| arquivo | referências |",
            "|---|---:|",
        ]
    )
    for rel_file, pairs in sorted(plan.text_replacements.items()):
        lines.append(f"| `{rel_file}` | {len(set(pairs))} |")

    lines.extend(["", "## Imagens novas/untracked", ""])
    if new_images:
        for img in new_images:
            lines.append(f"- `{img.rel}` -> `{img.target_rel}`")
    else:
        lines.append("- Nenhuma.")

    lines.extend(["", "## Imagens possivelmente órfãs", ""])
    if orphan:
        for img in orphan:
            lines.append(f"- `{img.rel}` -> `{img.target_rel}`")
    else:
        lines.append("- Nenhuma.")

    lines.extend(["", "## Casos ambíguos / revisão Sage", ""])
    if plan.ambiguous:
        for rel in sorted(plan.ambiguous):
            lines.append(f"- `{rel}`")
    else:
        lines.append("- Nenhum caso ambíguo crítico detectado.")

    lines.extend(
        [
            "",
            "## Política de aplicação",
            "",
            "- O script não apaga imagens.",
            "- O script aborta se houver colisões.",
            "- O script aborta se houver referências necessárias em arquivos já sujos antes da tarefa.",
            "- Campos e texto narrativo só são alterados quando o conteúdo é caminho de imagem.",
            "",
        ]
    )
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description="Audita e organiza zz_media.")
    parser.add_argument("--root", default=".")
    parser.add_argument("--output", default="Workflow/_audit/Media_Organization/MEDIA_ORGANIZATION_PLAN.md")
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()

    root = Path(args.root).resolve()
    _modified, _untracked, _dirty, status_text = git_status(root)
    plan = build_plan(root)
    output = root / args.output
    output.parent.mkdir(parents=True, exist_ok=True)

    applied_moves = 0
    applied_refs = 0
    mode = "apply" if args.apply else "dry-run"
    if args.apply:
        if plan.collisions:
            output.write_text(render_report(root, plan, "apply-aborted-collisions", 0, 0, status_text), encoding="utf-8")
            raise SystemExit("Abortado: colisões detectadas.")
        if plan.dirty_reference_files:
            output.write_text(render_report(root, plan, "apply-aborted-dirty-files", 0, 0, status_text), encoding="utf-8")
            raise SystemExit("Abortado: referências em arquivos já sujos antes da tarefa.")
        applied_refs = apply_replacements(root, plan.text_replacements)
        applied_moves = move_images(root, plan.images)
        json_problems = validate_json(root)
        if json_problems:
            raise SystemExit("JSON inválido após aplicação:\n" + "\n".join(json_problems))

    output.write_text(render_report(root, plan, mode, applied_moves, applied_refs, status_text), encoding="utf-8")
    print(f"Modo: {mode}")
    print(f"Imagens: {len(plan.images)}")
    print(f"Renomes/movimentos planejados: {sum(1 for img in plan.images if img.rel != img.target_rel)}")
    print(f"Colisões: {len(plan.collisions)}")
    print(f"Referências em arquivos sujos: {len(plan.dirty_reference_files)}")
    print(f"Relatório: {output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
