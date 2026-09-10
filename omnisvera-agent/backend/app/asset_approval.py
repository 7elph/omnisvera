"""Private drafts and explicit, idempotent GM publication."""
import hashlib
from contextlib import closing
from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .asset_generation import _connect, _now


def image_file(settings, job):
    value = job.get("image_path") or ""
    if value.startswith("draft:"):
        root = (settings.database_path.parent / "asset_drafts").resolve()
        path = (root / value[6:]).resolve()
    elif value.startswith("zz_media/"):
        root = (settings.vault_path / "zz_media").resolve()
        path = (settings.vault_path / value).resolve()
    else:
        raise ValueError("Imagem indisponível")
    if not path.is_relative_to(root) or not path.is_file():
        raise ValueError("Imagem indisponível")
    return path


def validate_image(path):
    try:
        with Image.open(path) as image:
            if min(image.size) <= 1:
                raise ValueError("Placeholder de teste não pode ser aprovado. Gere uma imagem real.")
            image.verify()
    except (UnidentifiedImageError, OSError) as exc:
        raise ValueError("Arquivo de imagem inválido. Gere novamente.") from exc


def approve_job(settings, job_id, expected_image_path):
    # Catalogue and approval share one transaction; stable IDs make retries safe.
    from .session_workspace import init_session_workspace
    init_session_workspace(settings.database_path)
    with closing(_connect(settings.database_path)) as conn, conn:
        conn.execute("BEGIN IMMEDIATE")
        row = conn.execute("SELECT * FROM asset_generation_jobs WHERE id=?", (job_id,)).fetchone()
        if not row:
            raise ValueError("Job inexistente")
        job = dict(row)
        if job["status"] == "approved":
            return job
        if job["status"] not in ("ready", "awaiting_approval") or job["image_path"] != expected_image_path:
            raise ValueError("A imagem mudou ou não está pronta para aprovação. Atualize a visualização.")
        source = image_file(settings, job)
        validate_image(source)
        digest = hashlib.sha256(source.read_bytes()).hexdigest()[:24]
        relative = f"zz_media/ui/icons/approved/asset_{job_id}_{digest}.png"
        target = settings.vault_path / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.exists():
            with Image.open(source) as image:
                image.convert("RGBA").save(target, format="PNG")
        label = {"potion_hp": "Poção HP", "potion_mp": "Poção MP"}.get(job["asset_type"], f"{job['asset_type']} · {job['entity_id']}")
        category = "items" if job["asset_type"] in ("item_art", "potion_hp", "potion_mp") else "map"
        conn.execute("INSERT OR IGNORE INTO session_workspace_icons(id,label,category,path,created_at) VALUES(?,?,?,?,?)",
                     (f"approved-asset:{job_id}:{digest}", label, category, relative, _now()))
        table = {"scene": "scenes", "game_session": "game_sessions", "session_custom_item": "session_custom_items"}.get(job["entity_type"])
        if table:
            # An existing chosen image is never overwritten by approving a new option.
            conn.execute(f"UPDATE {table} SET image_path=? WHERE id=? AND (image_path IS NULL OR image_path='')", (relative, int(job["entity_id"])))
        conn.execute("UPDATE asset_generation_jobs SET status='approved',image_path=?,error=NULL,updated_at=? WHERE id=?", (relative, _now(), job_id))
        return dict(conn.execute("SELECT * FROM asset_generation_jobs WHERE id=?", (job_id,)).fetchone())
