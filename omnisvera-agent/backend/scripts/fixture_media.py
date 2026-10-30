"""Copy only referenced image files into an existing isolated TEMP rehearsal.

The source Vault is read-only. This helper never reads notes, copies a database,
fetches a URL or generates missing art. A report of missing/skipped references is
evidence of incomplete media, not visual acceptance.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path, PurePosixPath
import sqlite3
from typing import Any

try:
    from .cf01_probe import checked_database
except ImportError:
    from cf01_probe import checked_database


_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".svg", ".avif"}
_COLUMNS = {
    "scenes": ("image_path",),
    "npc_definitions": ("portrait_path",),
    "session_workspace_maps": ("image_path",),
    "session_workspace_state": ("map_image_path",),
    "session_workspace_tokens": ("image_path",),
    "session_custom_items": ("image_path",),
    "player_inventory": ("image_path",),
}
_JSON_COLUMNS = {
    "session_workspace_tokens": ("sheet_json",),
    "character_sheets": ("data_json",),
    "character_definition_overrides": ("data_json",),
}
_IGNORE_CONTAINERS = {"notes", "note", "annotations", "anotacoes", "description",
                      "private", "gm_notes", "hidden_objectives", "token", "tokens",
                      "access_token", "credentials", "environment"}
_FRONTMATTER_MEDIA = ("image_path", "portrait", "thumbnail", "cover")
# The frontend projects these packaged UI assets without storing a database
# reference. Copy only this audited fallback set, never the whole catalogue.
_PACKAGED_ICON_FILES = (
    "zz_media/ui/icons/items/adaga.png",
    "zz_media/ui/icons/items/armadura-de-couro.png",
    "zz_media/ui/icons/items/dados.jpg",
    "zz_media/ui/icons/items/inventario.jpg",
    "zz_media/ui/icons/uploads/protocolo_guarda_e51a549b42.jpg",
    "zz_media/ui/icons/uploads/protocolo_vanguarda_2c8a61c1c8.jpg",
    "zz_media/ui/icons/uploads/raziel_coruja_969cca62e9.jpg",
    "zz_media/ui/icons/uploads/raziel_morcego_82a3c8733e.jpg",
    "zz_media/ui/icons/uploads/raziel_corvo_ae9c2df01e.jpg",
)


def _dto_images(value: Any, depth: int = 0):
    if depth > 20:
        return
    if isinstance(value, dict):
        for key, child in value.items():
            if key in {"image_path", "portrait"} and isinstance(child, str):
                yield child
            elif key not in _IGNORE_CONTAINERS and isinstance(child, (dict, list)):
                yield from _dto_images(child, depth + 1)
    elif isinstance(value, list):
        for child in value:
            yield from _dto_images(child, depth + 1)


def _references(database: Path) -> list[str]:
    references = set()
    with closing(sqlite3.connect(database.as_uri() + "?mode=ro", uri=True)) as connection:
        connection.execute("PRAGMA query_only=ON")
        for table in sorted(set(_COLUMNS) | set(_JSON_COLUMNS)):
            # SQL identifiers come exclusively from this module's static whitelist.
            columns = {row[1] for row in connection.execute(f'PRAGMA table_info("{table}")')}
            for column in _COLUMNS.get(table, ()):
                if column in columns:
                    for row in connection.execute(f'SELECT "{column}" FROM "{table}"'):
                        if isinstance(row[0], str) and row[0].strip():
                            references.add(row[0])
            for column in _JSON_COLUMNS.get(table, ()):
                if column in columns:
                    for row in connection.execute(f'SELECT "{column}" FROM "{table}"'):
                        if not isinstance(row[0], str) or len(row[0]) > 2_000_000:
                            continue
                        try:
                            references.update(_dto_images(json.loads(row[0])))
                        except (ValueError, RecursionError):
                            continue
        note_columns = {row[1] for row in connection.execute('PRAGMA table_info(notes)')}
        sheet_columns = {row[1] for row in connection.execute('PRAGMA table_info(character_sheets)')}
        if 'profile_id' in sheet_columns:
            # These icons are projected from the packaged catalogue at runtime,
            # not necessarily stored as image_path in the copied database.
            # Restrict to audited actors actually present; never read note text.
            from app.character_play import load_session_abilities
            present={row[0] for row in connection.execute('SELECT DISTINCT profile_id FROM character_sheets')}
            for actor in ('vezemir','morthak','raziel','dorn7'):
                if actor in present:
                    references.update(_dto_images(load_session_abilities(actor)))
            if 'dorn7' in present:
                # Dorn's mage spells are projected from packaged definitions,
                # not load_session_abilities (which returns its protocols).
                # Read presentation data only: never apply/reconcile the build.
                from app.character_play import attach_spell_images
                from app.dorn_mage import SPEC
                from app.approved_spell_pack import dorn_abilities
                references.update(_dto_images(attach_spell_images([
                    *SPEC['abilities'], *dorn_abilities()])))
        if {'path','frontmatter'} <= note_columns and {'profile_id','character_path'} <= sheet_columns:
            # Only identity media of the four audited actors, never note text,
            # nested private metadata or covers of unrelated Vault notes.
            rows = connection.execute('SELECT n.frontmatter FROM notes n JOIN character_sheets s '
                'ON s.character_path=n.path WHERE s.profile_id IN (?,?,?,?)',
                ('vezemir','morthak','raziel','dorn7'))
            references.update(_frontmatter_images(rows))
        inventory_columns = {row[1] for row in connection.execute('PRAGMA table_info(player_inventory)')}
        if {'path','frontmatter'} <= note_columns and {'profile_id','item_path'} <= inventory_columns:
            # Magic-item art lives in the referenced note, not in the inventory
            # row, so the runtime projection needs those note covers copied too.
            rows = connection.execute('SELECT n.frontmatter FROM notes n JOIN player_inventory i '
                'ON i.item_path=n.path WHERE i.profile_id IN (?,?,?,?)',
                ('vezemir','morthak','raziel','dorn7'))
            references.update(_frontmatter_images(rows))
    return sorted(references)


def _frontmatter_images(rows):
    for row in rows:
        if not isinstance(row[0],str) or len(row[0]) > 2_000_000:
            continue
        try:
            frontmatter = json.loads(row[0])
        except (ValueError,RecursionError):
            continue
        if isinstance(frontmatter,dict):
            yield from (frontmatter[key] for key in _FRONTMATTER_MEDIA
                        if isinstance(frontmatter.get(key),str) and frontmatter[key].strip())


def _packaged_references(source: Path) -> list[str]:
    return [raw for raw in _PACKAGED_ICON_FILES if (source / Path(raw)).is_file()]


def _shop_icon_references(database: Path, source: Path) -> set[str]:
    """Only stocked catalogue items and their uploaded icons; never note content."""
    from app.item_catalog import load_item_catalog
    from app.item_registry import key
    with closing(sqlite3.connect(database.as_uri()+'?mode=ro',uri=True)) as db:
        db.execute('PRAGMA query_only=ON')
        columns={row[1] for row in db.execute('PRAGMA table_info(merchant_stock)')}
        if 'compendium_item_id' not in columns:return set()
        identities={row[0] for row in db.execute('SELECT DISTINCT compendium_item_id FROM merchant_stock')}
        names={key(item['name']) for item in load_item_catalog()['items'] if item['id'] in identities}
        result={f'zz_media/ui/icons/items/{name}.{ext}' for name in names for ext in ('png','jpg','webp')
                if (source/f'zz_media/ui/icons/items/{name}.{ext}').is_file()}
        columns={row[1] for row in db.execute('PRAGMA table_info(session_workspace_icons)')}
        if {'label','path','category'}<=columns:
            result.update(row[1] for row in db.execute("SELECT label,path FROM session_workspace_icons WHERE category='items'") if key(row[0]) in names)
        return result


def _relative_image(raw: str) -> Path | None:
    # Do not decode URLs, normalize dot segments, or accept Windows ADS/drive paths.
    if (not raw.startswith("zz_media/") or any(character in raw for character in ("\\", ":", "%", "?", "#", "\x00"))
            or any(part in {"", ".", ".."} for part in raw.split("/"))):
        return None
    path = PurePosixPath(raw)
    if path.suffix.lower() not in _EXTENSIONS:
        return None
    return Path(*path.parts)


def _safe_path(root: Path, relative: Path) -> Path | None:
    cursor = root
    for part in relative.parts:
        cursor = cursor / part
        if cursor.is_symlink() or (hasattr(cursor, "is_junction") and cursor.is_junction()):
            return None
    resolved = cursor.resolve()
    media_root = root / "zz_media"
    if not resolved.is_relative_to(media_root) or resolved == media_root:
        return None
    return resolved


def copy_fixture_media(database_path: Path, source_vault: Path, target_vault: Path, *,
                       max_files: int = 300, max_bytes: int = 96_000_000) -> dict:
    database = checked_database(database_path)
    target = checked_database(target_vault)
    source = Path(source_vault).resolve()
    if target == source or target.is_relative_to(source):
        raise ValueError("Fixture media target must not be inside the source Vault")
    if not database.is_file():
        raise FileNotFoundError("Existing temporary fixture database is required")
    if any(type(limit) is not int or limit < 0 for limit in (max_files, max_bytes)):
        raise ValueError("Media limits must be non-negative integers")
    result = {"copied": [], "missing": [], "skipped": [], "bytes": 0}
    references = set(_references(database))
    references.update(_packaged_references(source))
    references.update(_shop_icon_references(database,source))
    for raw in sorted(references):
        relative = _relative_image(raw)
        origin = _safe_path(source, relative) if relative else None
        destination = _safe_path(target, relative) if relative else None
        if origin is None or destination is None or destination.is_relative_to(source):
            result["skipped"].append({"path": raw, "reason": "unsafe_path"})
            continue
        if not origin.is_file():
            result["missing"].append(raw)
            continue
        if destination.exists():
            result["skipped"].append({"path": raw, "reason": "exists"})
            continue
        if len(result["copied"]) >= max_files:
            result["skipped"].append({"path": raw, "reason": "file_limit"})
            continue
        remaining = max_bytes - result["bytes"]
        if origin.stat().st_size > remaining:
            result["skipped"].append({"path": raw, "reason": "byte_limit"})
            continue
        created = False
        try:
            destination.parent.mkdir(parents=True, exist_ok=True)
            # Recheck after directory creation and never replace an existing file.
            if _safe_path(target, relative) != destination or _safe_path(source, relative) != origin:
                raise ValueError("unsafe_path")
            copied_bytes = 0
            with origin.open("rb") as reader, destination.open("xb") as writer:
                created = True
                while chunk := reader.read(64 * 1024):
                    if copied_bytes + len(chunk) > remaining:
                        raise ValueError("byte_limit")
                    writer.write(chunk)
                    copied_bytes += len(chunk)
            result["copied"].append(raw)
            result["bytes"] += copied_bytes
        except (OSError, ValueError) as error:
            if created:
                destination.unlink(missing_ok=True)
            reason = str(error) if isinstance(error, ValueError) else "copy_error"
            result["skipped"].append({"path": raw, "reason": reason})
    return result
