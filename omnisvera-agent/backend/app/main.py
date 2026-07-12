from __future__ import annotations

from pathlib import Path
import re
import threading
import time
import unicodedata

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .access import AccessContext, is_player_safe_row, sanitize_player_summary
from .config import get_settings
from .ollama_client import check_ollama
from .player_actions import (
    ACTION_STATUSES,
    ACTION_TYPES,
    create_player_action,
    init_player_actions,
    list_player_actions,
    update_player_action,
)
from .player_discoveries import (
    init_player_discoveries,
    list_discoveries,
    reveal_discovery,
    revoke_discovery,
)
from .rag import answer_question
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    NoteDetail,
    NoteSummary,
    PlayerActionCreate,
    PlayerActionRecord,
    PlayerActionUpdate,
    PlayerDashboardResponse,
    PlayerDiscoveryCreate,
    PlayerDiscoveryRecord,
    PlayerProfileResponse,
    RebuildResponse,
    SearchRequest,
    SearchResult,
)
from .search import search_notes
from .vault_index import all_notes_for_search, get_note, index_signature, init_db, list_notes, rebuild_index, resolve_note, row_to_note
from .vault_reader import iter_markdown_notes, markdown_signature


settings = get_settings()
app = FastAPI(title="Omnisvera Companion", version="0.2.0")
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
_INDEX_REFRESH_LOCK = threading.Lock()
_LAST_INDEX_REFRESH_CHECK = 0.0
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


def _individual_player(provided: str | None) -> AccessContext | None:
    if not provided:
        return None
    for profile_id, profile in settings.player_profiles.items():
        if provided != profile.get("token"):
            continue
        return AccessContext(
            mode="player",
            profile_id=profile_id,
            character_path=profile.get("character_path") or None,
            character_title=profile.get("character_title") or profile_id,
        )
    return None


def _personalize_player_question(question: str, access: AccessContext) -> str:
    if not access.character_title:
        return question
    normalized = _media_lookup_key(question).replace("_", " ")
    identity_phrases = (
        "quem sou eu",
        "meu personagem",
        "minha historia",
        "minha origem",
        "o que sabemos sobre mim",
        "o que voce sabe sobre mim",
    )
    if any(phrase in normalized for phrase in identity_phrases):
        return f"Quem é {access.character_title}?"
    return question


def maybe_refresh_index() -> None:
    global _LAST_INDEX_REFRESH_CHECK
    if not settings.auto_refresh_index:
        return
    now = time.monotonic()
    if now - _LAST_INDEX_REFRESH_CHECK < settings.auto_refresh_interval_seconds:
        return
    with _INDEX_REFRESH_LOCK:
        now = time.monotonic()
        if now - _LAST_INDEX_REFRESH_CHECK < settings.auto_refresh_interval_seconds:
            return
        _LAST_INDEX_REFRESH_CHECK = now
        vault_sig = markdown_signature(settings.vault_path)
        db_sig = index_signature(settings.database_path)
        if vault_sig == db_sig:
            return
        notes, skipped = iter_markdown_notes(settings.vault_path)
        indexed = rebuild_index(settings.database_path, notes)
        print(
            f"[Omnisvera Companion] Índice atualizado automaticamente: "
            f"{indexed} notas, {skipped} arquivos ignorados."
        )


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
    individual = _individual_player(provided)
    if individual:
        return individual
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
    individual = _individual_player(provided)
    if individual:
        return individual
    if settings.player_token and provided == settings.player_token:
        return AccessContext(mode="player")
    if not settings.master_token and not settings.player_token:
        return AccessContext(mode="gm")
    raise HTTPException(status_code=401, detail="Token de acesso inválido ou ausente.")


@app.on_event("startup")
def startup() -> None:
    init_db(settings.database_path)
    init_player_actions(settings.database_path)
    init_player_discoveries(settings.database_path)
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
        fast_model=settings.fast_model,
        quality_model=settings.quality_model,
        embedding_model=settings.embedding_model,
        response_mode=settings.response_mode,
        rag_mode=settings.rag_mode,
        semantic_index_path=str(settings.semantic_index_path),
        auto_refresh_index=settings.auto_refresh_index,
        auto_refresh_interval_seconds=settings.auto_refresh_interval_seconds,
        ollama_accessible=await check_ollama(settings.ollama_base_url),
        access_mode=access.mode,
        player_mode_available=bool(settings.player_token or settings.player_profiles),
        player_profile_id=access.profile_id,
        player_character_path=access.character_path,
        player_character_title=access.character_title,
    )


@app.post("/index/rebuild", response_model=RebuildResponse)
def rebuild(_: AccessContext = Depends(require_master)) -> RebuildResponse:
    notes, skipped = iter_markdown_notes(settings.vault_path)
    indexed = rebuild_index(settings.database_path, notes)
    return RebuildResponse(indexed_notes=indexed, skipped_files=skipped, vault_path=str(settings.vault_path))


# Legacy endpoints: kept as GM-only so old frontend/bookmarks do not bypass safety.
@app.get("/notes", response_model=list[NoteSummary])
def notes(_: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    return list_notes(settings.database_path, access_mode="gm")


@app.get("/notes/{note_id}", response_model=NoteDetail)
def note(note_id: int, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    item = get_note(settings.database_path, note_id, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest, _: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    return search_notes(settings.database_path, request.query, request.limit, access_mode="gm")


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        request.question,
        request.limit,
        access_mode="gm",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode=settings.rag_mode,
        context_limit=settings.rag_context_limit,
        context_chars=settings.rag_context_chars,
        response_mode=settings.response_mode,
        fallback_model=settings.fast_model,
        conversation_paths=request.context_paths,
    )


@app.get("/gm/notes", response_model=list[NoteSummary])
def gm_notes(_: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    return list_notes(settings.database_path, access_mode="gm")


@app.get("/gm/notes/{note_id}", response_model=NoteDetail)
def gm_note(note_id: int, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    item = get_note(settings.database_path, note_id, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/gm/search", response_model=list[SearchResult])
def gm_search(request: SearchRequest, _: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    return search_notes(settings.database_path, request.query, request.limit, access_mode="gm")


@app.get("/gm/resolve", response_model=NoteSummary)
def gm_resolve(target: str, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    item = resolve_note(settings.database_path, target, access_mode="gm")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/gm/chat", response_model=ChatResponse)
async def gm_chat(request: ChatRequest, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        request.question,
        request.limit,
        access_mode="gm",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode=settings.rag_mode,
        context_limit=settings.rag_context_limit,
        context_chars=settings.rag_context_chars,
        response_mode=settings.response_mode,
        fallback_model=settings.fast_model,
        conversation_paths=request.context_paths,
    )


@app.get("/player/notes", response_model=list[NoteSummary])
def player_notes(_: AccessContext = Depends(require_player)) -> list[dict]:
    maybe_refresh_index()
    return list_notes(settings.database_path, access_mode="player")


@app.get("/player/notes/{note_id}", response_model=NoteDetail)
def player_note(note_id: int, _: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    item = get_note(settings.database_path, note_id, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/search", response_model=list[SearchResult])
def player_search(request: SearchRequest, _: AccessContext = Depends(require_player)) -> list[dict]:
    maybe_refresh_index()
    return search_notes(settings.database_path, request.query, request.limit, access_mode="player")


@app.get("/player/resolve", response_model=NoteSummary)
def player_resolve(target: str, _: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    item = resolve_note(settings.database_path, target, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/chat", response_model=ChatResponse)
async def player_chat(request: ChatRequest, access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    question = _personalize_player_question(request.question, access)
    context_paths = list(request.context_paths)
    if access.character_path and access.character_path not in context_paths:
        context_paths.insert(0, access.character_path)
    if access.profile_id:
        for discovery in list_discoveries(settings.database_path, profile_id=access.profile_id):
            path = discovery["note_path"]
            if path not in context_paths:
                context_paths.append(path)
    return await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.ollama_model,
        question,
        request.limit,
        access_mode="player",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode=settings.rag_mode,
        context_limit=settings.rag_context_limit,
        context_chars=settings.rag_context_chars,
        response_mode=settings.response_mode,
        fallback_model=settings.fast_model,
        conversation_paths=context_paths,
    )


def _is_player_character(note: dict) -> bool:
    frontmatter = note.get("frontmatter") or {}
    subtype = str(frontmatter.get("subtype") or "").strip().lower()
    role = str(frontmatter.get("role") or "").strip().lower()
    tags = {str(tag).strip().lower() for tag in note.get("tags") or []}
    return subtype == "player_character" or role == "player" or bool(
        tags & {"jogador", "player", "personagem-jogador"}
    )


@app.get("/player/profile", response_model=PlayerProfileResponse)
def player_profile(access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    payload = {
        "profile_id": access.profile_id,
        "character_path": access.character_path,
        "character_title": access.character_title,
        "shared_access": access.profile_id is None,
    }
    if not access.character_path:
        return payload
    summary = resolve_note(settings.database_path, access.character_path, access_mode="player")
    if summary is None:
        return payload
    detail = get_note(settings.database_path, int(summary["id"]), access_mode="player")
    frontmatter = (detail or {}).get("frontmatter") or {}
    payload.update(
        {
            "character_note_id": summary["id"],
            "thumbnail": summary.get("thumbnail"),
            "cover": summary.get("cover"),
            "character_class": frontmatter.get("class"),
            "race": frontmatter.get("race"),
            "level": frontmatter.get("level"),
            "status": frontmatter.get("status") or summary.get("status"),
            "location": frontmatter.get("location"),
            "faction": frontmatter.get("faction"),
        }
    )
    return payload


@app.get("/player/actions", response_model=list[PlayerActionRecord])
def player_actions(access: AccessContext = Depends(require_player)) -> list[dict]:
    return list_player_actions(settings.database_path, character_path=access.character_path)


@app.post("/player/actions", response_model=PlayerActionRecord)
def submit_player_action(
    request: PlayerActionCreate,
    access: AccessContext = Depends(require_player),
) -> dict:
    if request.action_type not in ACTION_TYPES:
        raise HTTPException(status_code=400, detail="Tipo de ação inválido.")
    character = get_note(settings.database_path, request.character_note_id, access_mode="player")
    if character is None or not _is_player_character(character):
        raise HTTPException(status_code=400, detail="Personagem jogador inválido ou não liberado.")
    if access.character_path and character["path"] != access.character_path:
        raise HTTPException(status_code=403, detail="Este acesso só pode agir pelo próprio personagem.")
    target = get_note(settings.database_path, request.target_note_id, access_mode="player")
    if target is None:
        raise HTTPException(status_code=400, detail="Alvo inválido ou não liberado aos jogadores.")
    intent = request.intent.strip()
    if len(intent) < 3:
        raise HTTPException(status_code=400, detail="Descreva melhor a intenção da ação.")
    return create_player_action(
        settings.database_path,
        character_path=character["path"],
        character_title=character["title"],
        action_type=request.action_type,
        target_path=target["path"],
        target_title=target["title"],
        intent=intent,
    )


@app.get("/player/discoveries", response_model=list[PlayerDiscoveryRecord])
def player_discoveries(access: AccessContext = Depends(require_player)) -> list[dict]:
    if access.profile_id is None:
        return []
    return list_discoveries(settings.database_path, profile_id=access.profile_id)


@app.get("/gm/actions", response_model=list[PlayerActionRecord])
def gm_actions(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_player_actions(settings.database_path, limit=250)


@app.get("/gm/discoveries", response_model=list[PlayerDiscoveryRecord])
def gm_discoveries(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_discoveries(settings.database_path)


@app.post("/gm/discoveries", response_model=PlayerDiscoveryRecord)
def gm_reveal_discovery(
    request: PlayerDiscoveryCreate,
    _: AccessContext = Depends(require_master),
) -> dict:
    if request.profile_id not in settings.player_profiles:
        raise HTTPException(status_code=400, detail="Perfil de jogador inválido.")
    note = get_note(settings.database_path, request.note_id, access_mode="player")
    if note is None:
        raise HTTPException(status_code=400, detail="A nota não está liberada para jogadores.")
    return reveal_discovery(
        settings.database_path,
        profile_id=request.profile_id,
        note_path=note["path"],
        note_title=note["title"],
    )


@app.delete("/gm/discoveries/{discovery_id}", status_code=204)
def gm_revoke_discovery(
    discovery_id: int,
    _: AccessContext = Depends(require_master),
) -> None:
    if not revoke_discovery(settings.database_path, discovery_id):
        raise HTTPException(status_code=404, detail="Descoberta não encontrada.")


@app.patch("/gm/actions/{action_id}", response_model=PlayerActionRecord)
def review_player_action(
    action_id: int,
    request: PlayerActionUpdate,
    _: AccessContext = Depends(require_master),
) -> dict:
    if request.status not in ACTION_STATUSES:
        raise HTTPException(status_code=400, detail="Estado de ação inválido.")
    if request.status in {"answered", "canonized"} and not (request.gm_response or "").strip():
        raise HTTPException(status_code=400, detail="Inclua uma resposta antes de concluir a ação.")
    result = update_player_action(
        settings.database_path,
        action_id,
        status=request.status,
        gm_response=request.gm_response,
    )
    if result is None:
        raise HTTPException(status_code=404, detail="Ação não encontrada.")
    return result


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
    maybe_refresh_index()
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
                cover="zz_media/covers/banner_ecos_do_mundo_perdido.png",
                prompt="O que aconteceu até agora?",
            ),
            _section(
                "characters",
                "Personagens dos jogadores",
                "Os protagonistas atuais da mesa.",
                characters,
                limit=8,
                cover="zz_media/covers/cover_personagens.png",
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
                cover="zz_media/maps/earthropo.png",
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
