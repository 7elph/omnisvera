"""Derived UI previews only. Originals and logical map coordinates are untouched."""
import hashlib
import os
import tempfile
import threading
from pathlib import Path

from PIL import Image, ImageOps, UnidentifiedImageError

_CACHE = Path(tempfile.gettempdir()) / 'omnisvera-media-previews-v1'
_LOCK = threading.Lock()
_RASTER = {'.png', '.jpg', '.jpeg', '.webp', '.gif'}


def resolve_app_art(media_path: str, root: Path) -> Path | None:
    if not media_path.startswith('companion-assets/'):
        return None
    root = root.resolve()
    requested = (root / media_path.removeprefix('companion-assets/')).resolve()
    if not requested.is_relative_to(root) or not requested.is_file():
        return None
    return requested


def preview_file(source: Path, edge: int, *, cache_root: Path | None = None) -> Path:
    if edge not in {128, 768}:
        raise ValueError('Tamanho de prévia inválido')
    if source.suffix.lower() not in _RASTER:
        return source
    stat = source.stat()
    key = hashlib.sha256(f'{source.resolve()}:{stat.st_mtime_ns}:{stat.st_size}:{edge}:1'.encode()).hexdigest()
    cache = (cache_root or _CACHE).resolve()
    target = cache / (key + '.webp')
    with _LOCK:
        if target.is_file():
            return target
        cache.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            with Image.open(source) as original, ImageOps.exif_transpose(original) as picture:
                picture.thumbnail((edge, edge), Image.Resampling.LANCZOS)
                mode = 'RGBA' if 'A' in picture.getbands() or 'transparency' in picture.info else 'RGB'
                with picture.convert(mode) as converted:
                    with tempfile.NamedTemporaryFile(dir=cache, suffix='.tmp', delete=False) as handle:
                        temporary = Path(handle.name)
                    converted.save(temporary, format='WEBP', quality=78, method=4)
            os.replace(temporary, target)
            # Only generated hash-named cache files, never sources or recursion.
            entries = [p for p in cache.glob('*.webp') if len(p.stem) == 64 and all(c in '0123456789abcdef' for c in p.stem)]
            for old in sorted(entries, key=lambda p: p.stat().st_mtime)[:-256]:
                if old != target and old.resolve().parent == cache:
                    old.unlink(missing_ok=True)
            return target
        except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
            return source
        finally:
            if temporary is not None and temporary.resolve().parent == cache:
                temporary.unlink(missing_ok=True)
