from __future__ import annotations

from pathlib import Path
import re
import unicodedata

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .access import AccessContext, is_player_safe_row, sanitize_player_summary
from .config import get_settings
from .ollama_client import check_ollama
from .rag import answer_question
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    NoteDetail,
    NoteSummary,
    PlayerDashboardResponse,
    RebuildResponse,
    SearchRequest,
    SearchResult,
)
from .search import search_notes
from .vault_index import all_notes_for_search, get_note, init_db, list_notes, rebuild_index, resolve_note, row_to_note
from .vault_reader import iter_markdown_notes


settings = get_settings()
app = FastAPI(title="Omnisvera Companion", version="0.2.0")
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
MEDIA_ALIASES = {
    "zz_media/characters/dukeofd.png": "zz_media/characters/augustus.png",
    "zz_media/thumbnails/th_dukeofd.png": "zz_media/thumbnails/th_augustus.png",
    "zz_media/characters/prop.png": "zz_media/characters/prop_augustus.png",
}

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def _provided_token(x_omnisvera_token: str | None, token: str | None) -> str | None:
    return x_omnisvera_token or token


def _media_lookup_key(value: str) -> str:
    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower().replace("\\", "/")
    value = re.sub(r"[_\-\s]+", "_", value)
    return value


def _resolve_media_file(media_path: str) -> Path | None:
    if not media_path.startswith("zz_media/"):
        return None

    media_path = MEDIA_ALIASES.get(media_path, media_path)
    media_root = (settings.vault_path / "zz_media").resolve()
    requested = (settings.vault_path / media_path).resolve()

    try:
        requested.relative_to(media_root)
    except ValueError:
        return None

    if requested.exists() and requested.is_file():
        return requested

    requested_name = Path(media_path).name
    requested_stem = Path(requested_name).stem
    wanted_keys = {
        _media_lookup_key(media_path),
        _media_lookup_key(requested_name),
        _media_lookup_key(requested_stem),
    }
    if requested_stem.startswith("th_"):
        wanted_keys.add(_media_lookup_key(requested_stem.removeprefix("th_")))
    else:
        wanted_keys.add(_media_lookup_key(f"th_{requested_stem}"))

    candidates: list[tuple[int, Path]] = []
    for candidate in media_root.rglob("*"):
        if not candidate.is_file():
            continue
        rel = candidate.relative_to(settings.vault_path).as_posix()
        name = candidate.name
        stem = candidate.stem
        candidate_keys = {
            _media_lookup_key(rel),
            _media_lookup_key(name),
            _media_lookup_key(stem),
        }
        if stem.startswith("th_"):
            candidate_keys.add(_media_lookup_key(stem.removeprefix("th_")))
        else:
            candidate_keys.add(_media_lookup_key(f"th_{stem}"))
        if not wanted_keys & candidate_keys:
            continue

        score = 0
        if _media_lookup_key(rel) == _media_lookup_key(media_path):
            score += 100
        if _media_lookup_key(name) == _media_lookup_key(requested_name):
            score += 80
        if _media_lookup_key(stem) == _media_lookup_key(requested_stem):
            score += 60
        if "/thumbnails/" in rel:
            score += 5 if requested_stem.startswith("th_") else 0
        if any(part in media_path for part in ("characters/", "locations/", "faction/", "items/", "class/", "races/")):
            requested_folder = media_path.split("/", 2)[1]
            if f"zz_media/{requested_folder}/" in rel:
                score += 15
        candidates.append((score, candidate))

    if not candidates:
        return None
    candidates.sort(key=lambda item: (item[0], -len(item[1].as_posix())), reverse=True)
    return candidates[0][1]


def require_master(
    x_omnisvera_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> AccessContext:
    if not settings.master_token:
        return AccessContext(mode="gm")
    if _provided_token(x_omnisvera_token, token) != settings.master_token:
        raise HTTPException(status_code=401, detail="Token de mestre inválido ou ausente.")
    return AccessContext(mode="gm")


def require_player(
    x_omnisvera_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> AccessContext:
    provided = _provided_token(x_omnisvera_token, token)
    if settings.master_token and provided == settings.master_token:
        return AccessContext(mode="gm")
    if settings.player_token and provided == settings.player_token:
        return AccessContext(mode="player")
    if not settings.master_token and not settings.player_token:
        return AccessContext(mode="player")
    raise HTTPException(status_code=401, detail="Token de jogador inválido ou ausente.")


def require_any(
    x_omnisvera_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> AccessContext:
    provided = _provided_token(x_omnisvera_token, token)
    if settings.master_token and provided == settings.master_token:
        return AccessContext(mode="gm")
    if settings.player_token and provided == settings.player_token:
        return AccessContext(mode="player")
    if not settings.master_token and not settings.player_token:
        return AccessContext(mode="gm")
    raise HTTPException(status_code=401, detail="Token de acesso inválido ou ausente.")


@app.on_event("startup")
def startup() -> None:
    init_db(settings.database_path)
    if settings.rebuild_on_startup:
        notes, _ = iter_markdown_notes(settings.vault_path)
        rebuild_index(settings.database_path, notes)


@app.get("/health", response_model=HealthResponse)
async def health(access: AccessContext = Depends(require_any)) -> HealthResponse:
    return HealthResponse(
        backend="ok",
        vault_path=str(settings.vault_path),
        database_path=str(settings.database_path),
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_accessible=await check_ollama(settings.ollama_base_url),
        access_mode=access.mode,
        player_mode_available=bool(settings.player_token),
    )


@app.post("/index/rebuild", response_model=RebuildResponse)
def rebuild(_: AccessContext = Depends(require_master)) -> RebuildResponse:
    notes, skipped = iter_markdown_notes(settings.vault_path)
    indexed = rebuild_index(settings.database_path, notes)
    return RebuildResponse(indexed_notes=indexed, skipped_files=skipped, vault_path=str(settings.vault_path))


# Legacy endpoints: kept as GM-only so old frontend/bookmarks do not bypass safety.
@app.get("/notes", response_model=list[NoteSummary])
def notes(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_notes(settings.database_path, access_mode="gm")


@app.get("/notes/{note_id}", response_model=NoteDetail)
def note(note_id: int, _: AccessContext = Depends(require_master)) -> dict:
    item = get_note(settings.database_path, note_id, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest, _: AccessContext = Depends(require_master)) -> list[dict]:
    return search_notes(settings.database_path, request.query, request.limit, access_mode="gm")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: AccessContext = Depends(require_master)) -> dict:
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        request.question,
        request.limit,
        access_mode="gm",
    )


@app.get("/gm/notes", response_model=list[NoteSummary])
def gm_notes(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_notes(settings.database_path, access_mode="gm")


@app.get("/gm/notes/{note_id}", response_model=NoteDetail)
def gm_note(note_id: int, _: AccessContext = Depends(require_master)) -> dict:
    item = get_note(settings.database_path, note_id, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/gm/search", response_model=list[SearchResult])
def gm_search(request: SearchRequest, _: AccessContext = Depends(require_master)) -> list[dict]:
    return search_notes(settings.database_path, request.query, request.limit, access_mode="gm")


@app.get("/gm/resolve", response_model=NoteSummary)
def gm_resolve(target: str, _: AccessContext = Depends(require_master)) -> dict:
    item = resolve_note(settings.database_path, target, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/gm/chat", response_model=ChatResponse)
async def gm_chat(request: ChatRequest, _: AccessContext = Depends(require_master)) -> dict:
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        request.question,
        request.limit,
        access_mode="gm",
    )


@app.get("/player/notes", response_model=list[NoteSummary])
def player_notes(_: AccessContext = Depends(require_player)) -> list[dict]:
    return list_notes(settings.database_path, access_mode="player")


@app.get("/player/notes/{note_id}", response_model=NoteDetail)
def player_note(note_id: int, _: AccessContext = Depends(require_player)) -> dict:
    item = get_note(settings.database_path, note_id, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/search", response_model=list[SearchResult])
def player_search(request: SearchRequest, _: AccessContext = Depends(require_player)) -> list[dict]:
    return search_notes(settings.database_path, request.query, request.limit, access_mode="player")


@app.get("/player/resolve", response_model=NoteSummary)
def player_resolve(target: str, _: AccessContext = Depends(require_player)) -> dict:
    item = resolve_note(settings.database_path, target, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/chat", response_model=ChatResponse)
async def player_chat(request: ChatRequest, _: AccessContext = Depends(require_player)) -> dict:
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        request.question,
        request.limit,
        access_mode="player",
    )


def _section(
    kind: str,
    title: str,
    description: str,
    rows: list,
    *,
    limit: int = 8,
    cover: str | None = None,
    prompt: str | None = None,
) -> dict:
    return {
        "kind": kind,
        "title": title,
        "description": description,
        "cover": cover,
        "prompt": prompt,
        "items": [sanitize_player_summary(row_to_note(row)) for row in rows[:limit]],
    }


@app.get("/player/dashboard", response_model=PlayerDashboardResponse)
def player_dashboard(_: AccessContext = Depends(require_player)) -> dict:
    rows = [row for row in all_notes_for_search(settings.database_path) if is_player_safe_row(row)]

    def is_active(row) -> bool:
        status = str(row_to_note(row).get("status") or "").strip().lower()
        return status not in {"arquivado", "deprecated", "non canon", "non-canon", "removido"}

    def sort_by_priority(items: list, priority: tuple[str, ...]) -> list:
        def rank(row) -> tuple[int, str]:
            text = f"{row['path']} {row['title']}".lower()
            for index, term in enumerate(priority):
                if term.lower() in text:
                    return (index, row["title"].lower())
            return (len(priority), row["title"].lower())

        return sorted(items, key=rank)

    def by_path(prefix: str) -> list:
        return sorted(
            [row for row in rows if row["path"].startswith(prefix) and "INDICE_" not in row["path"] and is_active(row)],
            key=lambda row: row["path"],
        )

    def by_type(*types: str) -> list:
        wanted = set(types)
        return sorted(
            [row for row in rows if row["type"] in wanted and "INDICE_" not in row["path"] and is_active(row)],
            key=lambda row: row["title"],
        )

    player_character_priority = ("Vezemir", "Varkh Nimalis", "Raziel", "Morthak")
    characters = [
        row
        for row in by_type("character")
        if any(tag in row["tags"].lower() for tag in ("jogador", "player", "personagem-jogador"))
        or any(name.lower() in f"{row['path']} {row['title']}".lower() for name in player_character_priority)
    ]
    characters = sort_by_priority(characters, player_character_priority)
    maps = sort_by_priority(by_type("map"), ("earthropo", "nimalia", "nimalis"))
    locations = sort_by_priority(
        [row for row in by_type("location", "territory") if row not in maps],
        (
            "O Frasco Afogado",
            "Maré Baixa",
            "Nimalis",
            "Porto de Nimalia",
            "Floresta de Avenor",
            "Vale Dourado",
            "Bosque Sussurrante",
        ),
    )
    diary = sort_by_priority(
        [
            row
            for row in rows
            if row["path"] == "LATEST_NEWS.md"
            or row["path"].startswith("EARTHROPO/")
            or (row["type"] == "story" and not row["path"].startswith("CAMPANHA/"))
            if "INDICE_" not in row["path"] and is_active(row)
        ],
        ("LATEST_NEWS", "01 - Ecos do Mundo Perdido"),
    )
    quests = by_path("CAMPANHA/Quests/")
    rumors = by_path("CAMPANHA/Rumors/")

    return {
        "mode": "player",
        "sections": [
            _section(
                "diary",
                "Diário da campanha",
                "Resumo público do que o grupo já pode consultar.",
                diary,
                limit=3,
                prompt="O que aconteceu até agora?",
            ),
            _section(
                "characters",
                "Personagens dos jogadores",
                "Os protagonistas atuais da mesa.",
                characters,
                limit=8,
                prompt="Quem são os personagens jogadores?",
            ),
            _section(
                "quests",
                "Missões conhecidas",
                "Objetivos e caminhos que já podem aparecer em jogo.",
                quests,
                limit=6,
                cover="zz_media/covers/cover_missoes_ativas.png",
                prompt="Quais missões estão ativas?",
            ),
            _section(
                "rumors",
                "Rumores liberados",
                "Boatos, pistas e fios soltos conhecidos pelos jogadores.",
                rumors,
                limit=6,
                cover="zz_media/covers/cover_rumores.png",
                prompt="Quais rumores estão ativos?",
            ),
            _section(
                "places",
                "Lugares conhecidos",
                "Locais e territórios que o grupo pode consultar sem spoiler.",
                locations,
                limit=10,
                prompt="Quais lugares conhecemos?",
            ),
        ],
    }


@app.get("/media/{media_path:path}", response_model=None)
def vault_media(media_path: str, _: AccessContext = Depends(require_any)):
    requested = _resolve_media_file(media_path)
    if requested is None:
        raise HTTPException(status_code=404, detail="Mídia não encontrada.")

    return FileResponse(requested)


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", response_model=None)
def frontend_root():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index, headers={"Cache-Control": "no-store"})
    return {
        "message": "Frontend ainda não foi buildado. Rode npm install e npm run build em omnisvera-agent/frontend."
    }


@app.get("/{full_path:path}", response_model=None)
def frontend_fallback(request: Request, full_path: str):
    if full_path.startswith(("health", "notes", "index", "search", "chat", "gm", "player", "media")):
        raise HTTPException(status_code=404, detail="Endpoint não encontrado.")
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index, headers={"Cache-Control": "no-store"})
    return {"message": "Omnisvera Companion backend ativo; frontend dist ausente."}
