from __future__ import annotations

from pathlib import Path
from datetime import datetime, timezone
import re
import threading
import time
import unicodedata
import uuid

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from .access import (
    AccessContext,
    is_player_safe_row,
    player_profile_scope,
    sanitize_player_chat_transport,
    sanitize_player_summary,
)
from .character_creation import (
    get_or_create_sheet,
    init_character_creation,
    list_sheets,
    review_sheet,
    submit_sheet,
    update_sheet_step,
)
from .config import get_settings
from .ollama_client import check_ollama
from .note_editor import EditConflictError, read_editable_note, save_editable_note
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
from .player_progress import (
    QUEST_STATUSES,
    add_event,
    init_player_progress,
    list_events,
    list_quests,
    mark_events_read,
    upsert_quest,
)
from .player_inventory import init_player_inventory, list_inventory, upsert_inventory
from .player_ideas import create_idea, init_player_ideas, list_ideas, review_idea
from .rag import answer_question
from .training_curation import (
    approve_batch,
    approve_example,
    behavior_memory_stats,
    capture_interaction,
    delete_pending,
    duplicate_example,
    get_example as get_training_example,
    list_examples as list_training_examples,
    mark_flag,
    purge_unreviewed,
    record_unreviewed_interaction,
    reject_example,
    sanitized_report,
    stats as training_stats,
    update_example,
    validate_batch,
)
from .schemas import (
    ChatRequest,
    ChatResponse,
    CharacterSheetResponse,
    CharacterSheetReview,
    CharacterSheetStepUpdate,
    EditableNoteResponse,
    EditableNoteUpdate,
    HealthResponse,
    InventoryRecord,
    InventoryUpdate,
    NoteDetail,
    NoteSummary,
    PlayerActionCreate,
    PlayerActionRecord,
    PlayerActionUpdate,
    PlayerDashboardResponse,
    PlayerDiscoveryCreate,
    PlayerDiscoveryRecord,
    PlayerEventReadRequest,
    PlayerEventRecord,
    PlayerProfileResponse,
    PlayerIdeaCreate,
    PlayerIdeaRecord,
    PlayerIdeaReview,
    PlayerQuestRecord,
    PlayerQuestUpdate,
    RebuildResponse,
    SearchRequest,
    SearchResult,
    TrainingDecisionRequest,
    TrainingBatchRequest,
    TrainingExamplePatch,
    TrainingFlagRequest,
    TrainingInteractionCapture,
)
from .search import search_notes
from .vault_index import all_notes_for_search, get_note, index_signature, init_db, list_notes, rebuild_index, resolve_note, row_to_note
from .vault_reader import iter_markdown_notes, markdown_signature


settings = get_settings()
app = FastAPI(title="Omnisvera Companion", version="0.2.0")
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"
EDITOR_BACKUP_ROOT = Path(__file__).resolve().parents[1] / "data" / "editor_backups"
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


def _profile_id_for_character(character_path: str) -> str:
    for profile_id, profile in settings.player_profiles.items():
        if profile.get("character_path") == character_path:
            return profile_id
    return "group"


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


def _personal_player_answer(question: str, access: AccessContext) -> dict | None:
    if access.mode != "player" or not access.character_title:
        return None
    normalized = _media_lookup_key(question).replace("_", " ")
    personal_terms = (
        "o que devo fazer",
        "o que fazer agora",
        "minhas missoes",
        "minha missao",
        "qual pista recebi",
        "minhas pistas",
        "minhas novidades",
        "o que mudou",
        "resposta do mestre",
        "meu inventario",
        "o que eu carrego",
        "meus itens",
    )
    if not any(term in normalized for term in personal_terms):
        return None

    quests = list_quests(settings.database_path, profile_id=access.profile_id)
    events = list_events(settings.database_path, profile_id=access.profile_id, limit=12)
    actions = list_player_actions(settings.database_path, character_path=access.character_path, limit=12)
    inventory = list_inventory(settings.database_path, access.profile_id or "group")
    active_quests = [quest for quest in quests if quest["status"] in {"accepted", "in_progress", "available"}]
    unread = [event for event in events if not event.get("read_at")]
    pending = [action for action in actions if action["status"] in {"submitted", "in_review"}]

    paragraphs: list[str] = []
    if active_quests:
        lines = [f"- **{quest['note_title']}** — {(quest.get('progress') or quest['status']).strip()}" for quest in active_quests[:4]]
        paragraphs.append("### Seus caminhos atuais\n" + "\n".join(lines))
    if unread:
        lines = [f"- **{event['title']}**: {event['message']}" for event in unread[:4]]
        paragraphs.append("### Novidades\n" + "\n".join(lines))
    if pending:
        lines = [f"- **{action['target_title']}**: sua intenção ainda está {('em análise' if action['status'] == 'in_review' else 'aguardando o Mestre')}." for action in pending[:3]]
        paragraphs.append("### Ações pendentes\n" + "\n".join(lines))
    if inventory and any(term in normalized for term in ("inventario", "carrego", "itens")):
        lines = [f"- **{item['item_title']}** ×{item['quantity']}{' — equipado' if item['equipped'] else ''}" for item in inventory[:12]]
        paragraphs.append("### Seu inventário\n" + "\n".join(lines))
    if not paragraphs:
        paragraphs.append(
            f"{access.character_title} não possui uma nova resposta ou missão pessoal registrada agora. "
            "Você ainda pode consultar as missões e rumores públicos ou enviar uma nova intenção ao Mestre."
        )

    paths: list[str] = []
    for item in [*active_quests, *unread]:
        path = item.get("note_path")
        if path and path not in paths:
            paths.append(path)
    notes_used = []
    for path in paths[:6]:
        note = resolve_note(settings.database_path, path, access_mode="player")
        if note:
            notes_used.append(note)
    return {
        "answer": "\n\n".join(paragraphs),
        "notes_used": notes_used,
        "note_paths": [note["path"] for note in notes_used],
        "insufficient_context": not bool(active_quests or unread or pending),
        "warning": None,
        "suggested_questions": ["Quais missões estão ativas?", "Quais rumores estão ativos?", "Quem sou eu?"],
        "fatos_confirmados": [],
        "teorias": [],
        "informacoes_insuficientes": [],
        "fontes_usadas": [note["path"] for note in notes_used],
        "ollama_used": False,
        "ollama_attempted": False,
        "model": settings.ollama_model,
        "retrieval_mode": "personal_state",
    }


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


def require_training_admin(
    x_omnisvera_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> AccessContext:
    if not settings.master_token:
        raise HTTPException(
            status_code=503,
            detail="Configure OMNISVERA_MASTER_TOKEN para habilitar a curadoria administrativa.",
        )
    return require_master(x_omnisvera_token, token)


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
    init_player_progress(settings.database_path)
    init_player_inventory(settings.database_path)
    init_player_ideas(settings.database_path)
    init_character_creation(settings.database_path)
    if settings.training_capture_mode != "off":
        purge_unreviewed(settings.unreviewed_retention_days)
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
        candidate_model=settings.candidate_model,
        production_model=settings.production_model,
        model_mode=settings.model_mode,
        production_approved=settings.production_approved,
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
        training_capture_mode=settings.training_capture_mode if access.mode == "gm" else None,
        behavior_memory_enabled=settings.behavior_memory_enabled,
        behavior_memory_mode=settings.behavior_memory_mode if access.mode == "gm" else None,
        behavior_memory_ab_mode=settings.behavior_memory_ab_mode if access.mode == "gm" else None,
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


def _chat_context_paths(request: ChatRequest, access_mode: str) -> list[str]:
    paths = list(request.context_paths)
    for note_id in request.context_note_ids[-4:]:
        context_note = get_note(settings.database_path, note_id, access_mode=access_mode)
        if context_note and context_note["path"] not in paths:
            paths.append(context_note["path"])
    return paths


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    context_paths = _chat_context_paths(request, "gm")
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
        conversation_paths=context_paths,
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
    started = time.perf_counter()
    context_paths = _chat_context_paths(request, "gm")
    result = await answer_question(
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
        conversation_paths=context_paths,
    )
    trace = result.pop("_training_trace", {}) or {}
    interaction_id = str(uuid.uuid4())
    created_at = datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    response_time_ms = round((time.perf_counter() - started) * 1000)
    result.update(
        {
            "interaction_id": interaction_id,
            "created_at": created_at,
            "response_time_ms": response_time_ms,
            "raw_model_response": str(trace.get("raw_ollama") or "") or None,
            "validator_rejections": trace.get("rejected_claims") or [],
            "behavior_memory_used": bool(trace.get("behavior_memory_used")),
            "behavioral_trace": {
                "example_ids": trace.get("behavioral_example_ids") or [],
                "categories": trace.get("behavioral_categories") or [],
                "scores": trace.get("behavioral_scores") or [],
                "mode": trace.get("behavioral_mode"),
                "prompt_size_added": trace.get("behavioral_prompt_size_added") or 0,
                "retrieval_time_ms": trace.get("behavioral_retrieval_time_ms") or 0,
            },
        }
    )
    if settings.training_capture_mode == "master_session" and request.capture_for_training:
        record_unreviewed_interaction(
            {
                "interaction_id": interaction_id,
                "created_at": created_at,
                "session_id": request.session_id,
                "user_profile": "gm",
                "question": request.question,
                "raw_model_response": result.get("raw_model_response"),
                "final_response": result.get("answer") or "",
                "verified_facts": result.get("fatos_confirmados") or [],
                "theories": result.get("teorias") or [],
                "insufficient_information": result.get("informacoes_insuficientes") or [],
                "retrieved_sources": result.get("notes_used") or [],
                "retrieval_mode": result.get("retrieval_mode"),
                "model": result.get("model"),
                "ollama_used": result.get("ollama_used"),
                "response_time_ms": response_time_ms,
                "validator_rejections": result.get("validator_rejections") or [],
                "warning": result.get("warning"),
                "behavior_memory_used": result.get("behavior_memory_used"),
                "behavioral_trace": result.get("behavioral_trace"),
            },
            settings.vault_path,
        )
    return result


def _training_error(error: ValueError) -> HTTPException:
    message = str(error)
    status = 404 if "não encontrado" in message.casefold() else 400
    return HTTPException(status_code=status, detail=message)


@app.post("/gm/training/interactions/capture")
def gm_training_capture(
    request: TrainingInteractionCapture,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    if settings.training_capture_mode == "off":
        raise HTTPException(status_code=409, detail="A captura de treinamento está desativada.")
    try:
        return capture_interaction(request.model_dump(), settings.vault_path, actor="Sage")
    except ValueError as error:
        raise _training_error(error) from error


@app.get("/gm/training/examples")
def gm_training_examples(
    status: str | None = None,
    access_profile: str | None = None,
    category: str | None = None,
    flag: str | None = None,
    model: str | None = None,
    persona_id: str | None = None,
    quality: int | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
    _: AccessContext = Depends(require_training_admin),
) -> list[dict]:
    return list_training_examples(
        status=status,
        access_profile=access_profile,
        category=category,
        flag=flag,
        model=model,
        persona_id=persona_id,
        quality=quality,
        date_from=date_from,
        date_to=date_to,
    )


@app.get("/gm/training/examples/{example_id}")
def gm_training_example(example_id: str, _: AccessContext = Depends(require_training_admin)) -> dict:
    try:
        return get_training_example(example_id)
    except ValueError as error:
        raise _training_error(error) from error


@app.patch("/gm/training/examples/{example_id}")
def gm_training_example_update(
    example_id: str,
    request: TrainingExamplePatch,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    try:
        return update_example(example_id, request.model_dump(exclude_none=True), actor="Sage")
    except ValueError as error:
        raise _training_error(error) from error


@app.post("/gm/training/examples/{example_id}/approve")
def gm_training_example_approve(
    example_id: str,
    request: TrainingDecisionRequest,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    try:
        return approve_example(
            example_id,
            request.reviewer,
            request.reason,
            request.ideal_response,
            request.quality,
        )
    except ValueError as error:
        raise _training_error(error) from error


@app.post("/gm/training/examples/{example_id}/reject")
def gm_training_example_reject(
    example_id: str,
    request: TrainingDecisionRequest,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    try:
        return reject_example(example_id, request.reviewer, request.reason)
    except ValueError as error:
        raise _training_error(error) from error


@app.post("/gm/training/examples/{example_id}/mark-{flag}")
def gm_training_example_flag(
    example_id: str,
    flag: str,
    request: TrainingFlagRequest,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    try:
        return mark_flag(example_id, flag, request.reviewer, request.detail)
    except ValueError as error:
        raise _training_error(error) from error


@app.delete("/gm/training/examples/{example_id}", status_code=204)
def gm_training_example_delete(example_id: str, _: AccessContext = Depends(require_training_admin)) -> None:
    try:
        delete_pending(example_id, "Sage")
    except ValueError as error:
        raise _training_error(error) from error


@app.post("/gm/training/examples/{example_id}/duplicate")
def gm_training_example_duplicate(
    example_id: str, _: AccessContext = Depends(require_training_admin)
) -> dict:
    try:
        return duplicate_example(example_id, "Sage")
    except ValueError as error:
        raise _training_error(error) from error


@app.get("/gm/training/coverage")
@app.get("/gm/training/stats")
def gm_training_stats(_: AccessContext = Depends(require_training_admin)) -> dict:
    return training_stats()


@app.post("/gm/training/examples/batch/validate")
def gm_training_batch_validate(
    request: TrainingBatchRequest,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    return validate_batch(request.example_ids, minimum_quality=request.minimum_quality)


@app.post("/gm/training/examples/batch/approve")
def gm_training_batch_approve(
    request: TrainingBatchRequest,
    _: AccessContext = Depends(require_training_admin),
) -> dict:
    try:
        return approve_batch(
            request.example_ids,
            confirmation=request.confirmation,
            reviewed=request.reviewed,
            actor=request.reviewer,
            reason=request.reason,
            minimum_quality=request.minimum_quality,
        )
    except ValueError as error:
        raise _training_error(error) from error


@app.get("/gm/training/behavior-memory")
def gm_training_behavior_memory(_: AccessContext = Depends(require_training_admin)) -> dict:
    return behavior_memory_stats()


@app.get("/gm/training/export-sanitized")
def gm_training_export(_: AccessContext = Depends(require_training_admin)) -> dict:
    return sanitized_report()


@app.post("/gm/training/retention/purge")
def gm_training_retention(_: AccessContext = Depends(require_training_admin)) -> dict:
    removed = purge_unreviewed(settings.unreviewed_retention_days)
    return {"removed": removed, "retention_days": settings.unreviewed_retention_days}


@app.get("/gm/editor", response_model=EditableNoteResponse)
def gm_editor_read(path: str, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return read_editable_note(settings.vault_path, path)
    except (ValueError, FileNotFoundError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.put("/gm/editor", response_model=EditableNoteResponse)
def gm_editor_save(request: EditableNoteUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        result = save_editable_note(
            settings.vault_path,
            EDITOR_BACKUP_ROOT,
            request.path,
            request.content,
            request.expected_hash,
        )
    except EditConflictError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except (ValueError, FileNotFoundError, UnicodeError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    notes, _ = iter_markdown_notes(settings.vault_path)
    rebuild_index(settings.database_path, notes)
    return result


@app.get("/player/notes", response_model=list[NoteSummary])
def player_notes(access: AccessContext = Depends(require_player)) -> list[dict]:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        return list_notes(settings.database_path, access_mode="player")


@app.get("/player/notes/{note_id}", response_model=NoteDetail)
def player_note(note_id: int, access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        item = get_note(settings.database_path, note_id, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/search", response_model=list[SearchResult])
def player_search(request: SearchRequest, access: AccessContext = Depends(require_player)) -> list[dict]:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        return search_notes(settings.database_path, request.query, request.limit, access_mode="player")


@app.get("/player/resolve", response_model=NoteSummary)
def player_resolve(target: str, access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        item = resolve_note(settings.database_path, target, access_mode="player")
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada ou não liberada para jogadores")
    return item


@app.post("/player/chat", response_model=ChatResponse)
async def player_chat(request: ChatRequest, access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        question = _personalize_player_question(request.question, access)
        personal_answer = _personal_player_answer(question, access)
        if personal_answer is not None:
            return sanitize_player_chat_transport(personal_answer)
        # Player clients continue conversations with opaque note IDs. Incoming
        # IDs are resolved through the player access filter, so a guessed GM ID
        # can never become context. Legacy paths remain accepted temporarily.
        context_paths = _chat_context_paths(request, "player")
        priority_paths: list[str] = []
        if access.profile_id and access.character_title:
            personal_knowledge_path = (
                f"CAMPANHA/Player_Knowledge/CONHECIMENTO - {access.character_title}.md"
            )
            personal_knowledge = resolve_note(
                settings.database_path,
                personal_knowledge_path,
                access_mode="player",
            )
            if personal_knowledge:
                priority_paths.append(personal_knowledge_path)
                if personal_knowledge_path not in context_paths:
                    context_paths.insert(0, personal_knowledge_path)
        if access.character_path and access.character_path not in context_paths:
            context_paths.insert(0, access.character_path)
        if access.profile_id:
            for discovery in list_discoveries(settings.database_path, profile_id=access.profile_id):
                path = discovery["note_path"]
                if path not in context_paths:
                    context_paths.append(path)
            for quest in list_quests(settings.database_path, profile_id=access.profile_id):
                path = quest["note_path"]
                if path not in context_paths:
                    context_paths.append(path)
            for action in list_player_actions(settings.database_path, character_path=access.character_path, limit=8):
                if action["status"] in {"answered", "canonized"} and action["target_path"] not in context_paths:
                    context_paths.append(action["target_path"])
            for item in list_inventory(settings.database_path, access.profile_id):
                if item["item_path"] not in context_paths:
                    context_paths.append(item["item_path"])
        context_paths = context_paths[:10]
        result = await answer_question(
            settings.database_path, settings.ollama_base_url, settings.ollama_model,
            question, request.limit, access_mode="player", embedding_model=settings.embedding_model,
            semantic_index_path=settings.semantic_index_path, rag_mode=settings.rag_mode,
            context_limit=settings.rag_context_limit, context_chars=settings.rag_context_chars,
            response_mode=settings.response_mode, fallback_model=settings.fast_model,
            conversation_paths=context_paths,
            priority_paths=priority_paths,
        )
        return sanitize_player_chat_transport(result)


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


def _ensure_profile_sheet(profile_id: str) -> dict:
    profile = settings.player_profiles.get(profile_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Perfil de jogador não encontrado.")
    character_path = str(profile.get("character_path") or "")
    summary = resolve_note(settings.database_path, character_path, access_mode="player")
    if summary is None:
        raise HTTPException(status_code=404, detail="Nota do personagem não encontrada ou não liberada.")
    detail = get_note(settings.database_path, int(summary["id"]), access_mode="player")
    if detail is None:
        raise HTTPException(status_code=404, detail="Não foi possível ler a nota do personagem.")
    frontmatter = detail.get("frontmatter") or {}

    def reference_note(value: object, *, kind: str) -> dict | None:
        target = str(value or "").strip()
        if kind == "race" and "kenku" in target.lower():
            target = "Kenku"
        if not target:
            return None
        # Character creation may use the mechanical race/class source even when
        # the reference note itself is GM-only. Only the extracted form fields
        # are returned to the owner of that character.
        reference = resolve_note(settings.database_path, target, access_mode="gm")
        if reference is None:
            return None
        return get_note(settings.database_path, int(reference["id"]), access_mode="gm")

    return get_or_create_sheet(
        settings.database_path,
        profile_id=profile_id,
        character_path=character_path,
        character_title=str(profile.get("character_title") or summary["title"]),
        note=detail,
        race_note=reference_note(frontmatter.get("race"), kind="race"),
        class_note=reference_note(frontmatter.get("class"), kind="class"),
    )


@app.get("/player/character-sheet", response_model=CharacterSheetResponse)
def player_character_sheet(access: AccessContext = Depends(require_player)) -> dict:
    if not access.profile_id:
        raise HTTPException(status_code=403, detail="Use o token individual do seu personagem para preencher a ficha.")
    maybe_refresh_index()
    return _ensure_profile_sheet(access.profile_id)


@app.put("/player/character-sheet", response_model=CharacterSheetResponse)
def save_player_character_sheet_step(
    request: CharacterSheetStepUpdate,
    access: AccessContext = Depends(require_player),
) -> dict:
    if not access.profile_id:
        raise HTTPException(status_code=403, detail="Use o token individual do seu personagem para preencher a ficha.")
    _ensure_profile_sheet(access.profile_id)
    try:
        result = update_sheet_step(
            settings.database_path,
            profile_id=access.profile_id,
            step_key=request.step_key,
            fields=dict(request.fields),
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Ficha não encontrada.")
    return result


@app.post("/player/character-sheet/submit", response_model=CharacterSheetResponse)
def submit_player_character_sheet(access: AccessContext = Depends(require_player)) -> dict:
    if not access.profile_id:
        raise HTTPException(status_code=403, detail="Use o token individual do seu personagem para entregar a ficha.")
    _ensure_profile_sheet(access.profile_id)
    try:
        result = submit_sheet(settings.database_path, profile_id=access.profile_id)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Ficha não encontrada.")
    add_event(
        settings.database_path,
        profile_id=access.profile_id,
        kind="character_sheet_submitted",
        title="Ficha entregue ao Mestre",
        message="As dez etapas foram concluídas e a ficha aguarda revisão.",
        unread=False,
    )
    return result


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
    result = create_player_action(
        settings.database_path,
        character_path=character["path"],
        character_title=character["title"],
        action_type=request.action_type,
        target_path=target["path"],
        target_title=target["title"],
        intent=intent,
    )
    add_event(
        settings.database_path,
        profile_id=access.profile_id or _profile_id_for_character(character["path"]),
        kind="action_submitted",
        title=f"Ação enviada: {target['title']}",
        message=intent,
        note_path=target["path"],
        unread=False,
    )
    return result


@app.get("/player/discoveries", response_model=list[PlayerDiscoveryRecord])
def player_discoveries(access: AccessContext = Depends(require_player)) -> list[dict]:
    if access.profile_id is None:
        return []
    return list_discoveries(settings.database_path, profile_id=access.profile_id)


@app.get("/player/feed", response_model=list[PlayerEventRecord])
def player_feed(access: AccessContext = Depends(require_player)) -> list[dict]:
    return list_events(settings.database_path, profile_id=access.profile_id)


@app.post("/player/feed/read")
def player_feed_read(
    request: PlayerEventReadRequest,
    access: AccessContext = Depends(require_player),
) -> dict:
    return {
        "updated": mark_events_read(
            settings.database_path,
            profile_id=access.profile_id,
            event_ids=request.event_ids,
        )
    }


@app.get("/player/quests", response_model=list[PlayerQuestRecord])
def player_quests(access: AccessContext = Depends(require_player)) -> list[dict]:
    return list_quests(settings.database_path, profile_id=access.profile_id)


def _inventory_with_media(items: list[dict], *, access_mode: str) -> list[dict]:
    enriched: list[dict] = []
    for item in items:
        record = dict(item)
        note = resolve_note(settings.database_path, record["item_path"], access_mode=access_mode)
        if note:
            record["note_id"] = note.get("id")
            record["thumbnail"] = note.get("thumbnail")
            record["cover"] = note.get("cover")
        enriched.append(record)
    return enriched


@app.get("/player/inventory", response_model=list[InventoryRecord])
def player_inventory(access: AccessContext = Depends(require_player)) -> list[dict]:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
        return _inventory_with_media(
            list_inventory(settings.database_path, access.profile_id or "group"),
            access_mode="player",
        )


@app.post("/player/ideas", response_model=PlayerIdeaRecord)
def player_submit_idea(request: PlayerIdeaCreate, access: AccessContext = Depends(require_player)) -> dict:
    return create_idea(
        settings.database_path,
        author=access.character_title or access.profile_id or "Visitante",
        title=request.title,
        concept=request.concept,
        appearance=request.appearance,
        motivation=request.motivation,
        world_connection=request.world_connection,
    )


@app.get("/gm/character-sheets", response_model=list[CharacterSheetResponse])
def gm_character_sheets(_: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    for profile_id in settings.player_profiles:
        _ensure_profile_sheet(profile_id)
    return list_sheets(settings.database_path)


@app.patch("/gm/character-sheets/{profile_id}", response_model=CharacterSheetResponse)
def gm_review_character_sheet(
    profile_id: str,
    request: CharacterSheetReview,
    _: AccessContext = Depends(require_master),
) -> dict:
    _ensure_profile_sheet(profile_id)
    try:
        result = review_sheet(
            settings.database_path,
            profile_id=profile_id,
            status=request.status,
            feedback=request.feedback,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    if result is None:
        raise HTTPException(status_code=404, detail="Ficha não encontrada.")
    add_event(
        settings.database_path,
        profile_id=profile_id,
        kind=f"character_sheet_{request.status}",
        title="Ficha aprovada" if request.status == "approved" else "Ficha devolvida para ajustes",
        message=(request.feedback or "O Mestre revisou sua ficha.").strip(),
    )
    return result


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
    result = reveal_discovery(
        settings.database_path,
        profile_id=request.profile_id,
        note_path=note["path"],
        note_title=note["title"],
    )
    add_event(
        settings.database_path,
        profile_id=request.profile_id,
        kind="discovery",
        title="Nova descoberta",
        message=f"{note['title']} foi revelado para você.",
        note_path=note["path"],
    )
    return result


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
    profile_id = _profile_id_for_character(result["character_path"])
    if request.status in {"answered", "canonized", "rejected"}:
        status_label = {
            "answered": "Resposta do Mestre",
            "canonized": "Ação canonizada",
            "rejected": "Ação não realizada",
        }[request.status]
        add_event(
            settings.database_path,
            profile_id=profile_id,
            kind=f"action_{request.status}",
            title=status_label,
            message=(request.gm_response or f"Atualização sobre {result['target_title']}.").strip(),
            note_path=result["target_path"],
        )
    return result


@app.get("/gm/quests", response_model=list[PlayerQuestRecord])
def gm_quests(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_quests(settings.database_path)


@app.post("/gm/quests", response_model=PlayerQuestRecord)
def gm_update_quest(
    request: PlayerQuestUpdate,
    _: AccessContext = Depends(require_master),
) -> dict:
    if request.profile_id != "group" and request.profile_id not in settings.player_profiles:
        raise HTTPException(status_code=400, detail="Perfil de jogador inválido.")
    if request.status not in QUEST_STATUSES:
        raise HTTPException(status_code=400, detail="Estado de missão inválido.")
    note = get_note(settings.database_path, request.note_id, access_mode="player")
    if note is None or note.get("type") != "quest":
        raise HTTPException(status_code=400, detail="Escolha uma missão liberada aos jogadores.")
    result = upsert_quest(
        settings.database_path,
        profile_id=request.profile_id,
        note_path=note["path"],
        note_title=note["title"],
        status=request.status,
        progress=request.progress,
    )
    status_label = {
        "available": "Missão disponível",
        "accepted": "Missão aceita",
        "in_progress": "Missão atualizada",
        "completed": "Missão concluída",
        "failed": "Missão falhou",
        "archived": "Missão arquivada",
    }[request.status]
    add_event(
        settings.database_path,
        profile_id=request.profile_id,
        kind="quest_update",
        title=status_label,
        message=(request.progress or note["title"]).strip(),
        note_path=note["path"],
    )
    return result


@app.get("/gm/inventory", response_model=list[InventoryRecord])
def gm_inventory(_: AccessContext = Depends(require_master)) -> list[dict]:
    maybe_refresh_index()
    items: list[dict] = []
    for profile_id in settings.player_profiles:
        items.extend(list_inventory(settings.database_path, profile_id))
    return _inventory_with_media(items, access_mode="gm")


@app.get("/gm/ideas", response_model=list[PlayerIdeaRecord])
def gm_ideas(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_ideas(settings.database_path)


@app.patch("/gm/ideas/{idea_id}", response_model=PlayerIdeaRecord)
def gm_review_idea(idea_id: int, request: PlayerIdeaReview, _: AccessContext = Depends(require_master)) -> dict:
    try:
        result = review_idea(settings.database_path, idea_id, status=request.status, feedback=request.feedback)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    if not result:
        raise HTTPException(status_code=404, detail="Ideia não encontrada.")
    return result


@app.post("/gm/inventory", response_model=InventoryRecord)
def gm_update_inventory(request: InventoryUpdate, _: AccessContext = Depends(require_master)) -> dict:
    if request.profile_id not in settings.player_profiles:
        raise HTTPException(status_code=400, detail="Perfil de jogador inválido.")
    note = get_note(settings.database_path, request.note_id, access_mode="player")
    if note is None or note.get("type") != "item":
        raise HTTPException(status_code=400, detail="Escolha um item liberado aos jogadores.")
    result = upsert_inventory(
        settings.database_path,
        profile_id=request.profile_id,
        item_path=note["path"],
        item_title=note["title"],
        quantity=request.quantity,
        equipped=request.equipped,
        notes=request.notes,
    )
    add_event(
        settings.database_path,
        profile_id=request.profile_id,
        kind="inventory",
        title="Inventário atualizado",
        message=f"{note['title']} · quantidade {request.quantity}{' · equipado' if request.equipped else ''}.",
        note_path=note["path"],
    )
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
def player_dashboard(access: AccessContext = Depends(require_player)) -> dict:
    maybe_refresh_index()
    with player_profile_scope(access.profile_id):
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
