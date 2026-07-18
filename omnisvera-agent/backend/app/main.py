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
from .character_play import (
    apply_character_action,
    build_character_definition,
    compose_character_view,
    get_or_create_state,
    init_character_play,
    list_character_events,
    load_definition_overrides,
    revert_character_event,
    update_definition_overrides,
)
from .config import get_settings
from .contract_play import (
    accept_contract,
    add_assignment,
    apply_reputation,
    approve_reward,
    create_contract,
    create_objective,
    create_reward,
    deliver_reward,
    get_contract,
    init_contract_play,
    link_scene as link_contract_scene,
    list_contracts,
    list_events as list_contract_events,
    list_reputation,
    record_scene_contract_event,
    remove_assignment,
    reorder_objectives,
    revert_reputation,
    scene_contract_links,
    set_objective_status,
    transition_contract,
    unlink_scene as unlink_contract_scene,
    update_contract,
    update_objective,
    update_reward,
    void_contract_event,
)
from .dice_rolls import (
    RollSpec,
    can_view_roll,
    complete_roll_request,
    create_roll,
    create_roll_request,
    get_roll,
    init_dice_rolls,
    list_roll_requests,
    list_rolls,
    parse_formula,
    resolve_character_roll,
    void_roll,
)
from .ollama_client import check_ollama
from .npc_memory import (
    contradict_memory as contradict_npc_memory,
    create_memory as create_npc_memory,
    create_npc,
    create_relationship as create_npc_relationship,
    get_npc,
    init_npc_memory,
    link_contract as link_npc_contract,
    list_contract_npcs,
    list_npcs,
    record_encounter as record_npc_encounter,
    structured_summary as npc_structured_summary,
    unlink_encounter as unlink_npc_encounter,
    update_memory as update_npc_memory,
    update_npc,
    update_npc_state,
    update_relationship as update_npc_relationship,
    void_event as void_npc_event,
)
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
from .scene_play import (
    active_scene,
    add_participant,
    cancel_action,
    change_scene_status,
    change_session_status,
    create_element,
    create_scene,
    create_session,
    declare_action,
    get_action,
    get_scene,
    init_scene_play,
    link_completed_roll,
    link_roll_request,
    list_scenes,
    list_sessions,
    record_consequence,
    record_manual_event,
    resolve_action,
    scene_view,
    update_element,
    update_participant,
    update_scene,
    void_event,
)
from .world_travel import (
    add_journey_participant,
    advance_journey,
    complete_journey,
    create_journey,
    create_location,
    create_map,
    create_route,
    discover_route,
    discover_location,
    get_journey,
    get_location,
    get_map,
    init_world_travel,
    link_journey_scene,
    link_location,
    list_journey_events,
    list_journeys,
    list_locations,
    list_maps,
    list_routes,
    remove_journey_participant,
    related_locations,
    transition_journey,
    update_location,
    update_location_state,
    update_map,
    update_planned_journey,
    update_route,
    void_journey_event,
)
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
    CharacterDefinitionUpdate,
    CharacterEventResponse,
    CharacterStateAction,
    CharacterSheetResponse,
    CharacterSheetReview,
    CharacterSheetStepUpdate,
    CharacterRollCreate,
    ContractAcceptRequest,
    ContractAssignmentCreate,
    ContractCreate,
    ContractEventVoidRequest,
    ContractLinkedSceneCreate,
    ContractObjectiveCreate,
    ContractRewardCreate,
    ContractSceneLinkCreate,
    ContractTransitionRequest,
    DiceRollCreate,
    DiceRollEventResponse,
    DiceRollRequestComplete,
    DiceRollRequestCreate,
    DiceRollRequestResponse,
    DiceRollVoidRequest,
    GameSessionCreate,
    GameSessionStatusUpdate,
    EditableNoteResponse,
    EditableNoteUpdate,
    HealthResponse,
    InventoryRecord,
    InventoryUpdate,
    NoteDetail,
    NoteSummary,
    NpcContractLinkCreate,
    NpcCreate,
    NpcEncounterCreate,
    NpcEventVoidRequest,
    NpcImportRequest,
    NpcMemoryContradict,
    NpcMemoryCreate,
    NpcRelationshipCreate,
    NpcVersionedUpdate,
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
    PlayableCharacterResponse,
    PlayableCharacterSummary,
    RebuildResponse,
    SearchRequest,
    SearchResult,
    SceneActionCreate,
    SceneActionResolution,
    SceneConsequenceCreate,
    SceneCreate,
    SceneElementCreate,
    SceneElementUpdate,
    SceneManualEventCreate,
    SceneParticipantCreate,
    SceneParticipantUpdate,
    SceneRollRequestCreate,
    SceneStatusUpdate,
    SceneUpdate,
    SceneVoidRequest,
    ObjectiveOrderRequest,
    ObjectiveStatusRequest,
    ReputationApplyRequest,
    RewardDeliveryRequest,
    TrainingDecisionRequest,
    TrainingBatchRequest,
    TrainingExamplePatch,
    TrainingFlagRequest,
    TrainingInteractionCapture,
    VersionedPatch,
    JourneyAdvanceRequest,
    JourneyCreate,
    JourneyParticipantCreate,
    JourneyParticipantRemove,
    JourneySceneLinkCreate,
    JourneyTransitionRequest,
    LocationDiscoveryCreate,
    LocationLinkCreate,
    TravelRouteCreate,
    WorldImportRequest,
    WorldLocationCreate,
    WorldMapCreate,
    WorldVersionedUpdate,
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
    init_character_play(settings.database_path)
    init_dice_rolls(settings.database_path)
    init_scene_play(settings.database_path)
    init_contract_play(settings.database_path)
    init_npc_memory(settings.database_path)
    init_world_travel(settings.database_path)
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
        fallback_model=settings.ollama_fallback_model,
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
        fallback_model=settings.ollama_fallback_model,
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
            response_mode=settings.response_mode, fallback_model=settings.ollama_fallback_model,
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
            detail = get_note(settings.database_path, int(note["id"]), access_mode=access_mode)
            frontmatter = dict((detail or {}).get("frontmatter") or {})
            candidate_formula = frontmatter.get("base_damage") or frontmatter.get("damage")
            if candidate_formula:
                try:
                    record["damage_formula"] = parse_formula(str(candidate_formula)).formula
                except ValueError:
                    record["damage_formula"] = None
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


def _sheet_for_character(profile_id: str) -> dict:
    if profile_id in settings.player_profiles:
        return _ensure_profile_sheet(profile_id)
    sheet = next((item for item in list_sheets(settings.database_path) if item["profile_id"] == profile_id), None)
    if sheet is None:
        raise HTTPException(status_code=404, detail="Ficha de personagem não encontrada.")
    return sheet


def _character_ids() -> list[str]:
    ids = list(settings.player_profiles)
    for sheet in list_sheets(settings.database_path):
        if sheet["profile_id"] not in ids:
            ids.append(sheet["profile_id"])
    return ids


def _character_access_level(access: AccessContext, profile_id: str) -> str:
    if access.mode == "gm":
        return "gm"
    if access.profile_id == profile_id:
        return "owner"
    return "public"


def _playable_character(profile_id: str, access: AccessContext) -> dict:
    sheet = _sheet_for_character(profile_id)
    summary = resolve_note(settings.database_path, sheet["character_path"], access_mode="gm")
    if summary is None:
        raise HTTPException(status_code=404, detail="Nota de origem do personagem não encontrada.")
    note = get_note(settings.database_path, int(summary["id"]), access_mode="gm")
    if note is None:
        raise HTTPException(status_code=404, detail="Não foi possível carregar a definição do personagem.")
    access_level = _character_access_level(access, profile_id)
    inventory = _inventory_with_media(
        list_inventory(settings.database_path, profile_id),
        access_mode="gm" if access_level == "gm" else "player",
    )
    definition = build_character_definition(
        profile_id=profile_id,
        note=note,
        sheet=sheet,
        inventory=inventory,
        overrides=load_definition_overrides(settings.database_path, profile_id),
        access_level=access_level,
    )
    state = None
    if access_level != "public":
        state = get_or_create_state(
            settings.database_path,
            profile_id=profile_id,
            sheet=sheet,
            definition=definition,
        )
    return compose_character_view(
        definition=definition,
        state=state,
        inventory=inventory if access_level != "public" else [],
        access_level=access_level,
    )


def _character_summary(record: dict) -> dict:
    definition = record["definition"]
    state = record.get("state") or {}
    defenses = definition.get("defenses") or {}
    return {
        "id": definition["id"],
        "name": definition["name"],
        "portrait": definition.get("portrait"),
        "epithet": definition.get("epithet"),
        "race": definition.get("race"),
        "class_name": definition.get("class_name"),
        "level": definition.get("level"),
        "current_hp": state.get("current_hp"),
        "maximum_hp": state.get("maximum_hp"),
        "armor_class": defenses.get("armor_class") if state else None,
        "initiative": defenses.get("initiative") if state else None,
        "movement": definition.get("movement") if state else None,
        "conditions": state.get("conditions") or [],
        "resources": state.get("resources") or [],
        "access_level": record["access_level"],
    }


@app.get("/characters", response_model=list[PlayableCharacterSummary])
def playable_characters(access: AccessContext = Depends(require_any)) -> list[dict]:
    maybe_refresh_index()
    return [_character_summary(_playable_character(profile_id, access)) for profile_id in _character_ids()]


@app.get("/characters/{profile_id}", response_model=PlayableCharacterResponse, response_model_exclude_none=True)
def playable_character(profile_id: str, access: AccessContext = Depends(require_any)) -> dict:
    maybe_refresh_index()
    return _playable_character(profile_id, access)


@app.post("/characters/{profile_id}/actions", response_model=PlayableCharacterResponse, response_model_exclude_none=True)
def playable_character_action(
    profile_id: str,
    request: CharacterStateAction,
    access: AccessContext = Depends(require_any),
) -> dict:
    access_level = _character_access_level(access, profile_id)
    if access_level == "public":
        raise HTTPException(status_code=403, detail="Você só pode alterar o próprio personagem.")
    _playable_character(profile_id, access)
    payload = dict(request.payload)
    if request.action == "grant_item":
        note_id = payload.get("note_id")
        if note_id is None:
            raise HTTPException(status_code=400, detail="Escolha um item do Arquivo.")
        try:
            note_id = int(note_id)
        except (TypeError, ValueError) as error:
            raise HTTPException(status_code=400, detail="Item inválido.") from error
        note = get_note(settings.database_path, note_id, access_mode="gm")
        if note is None or note.get("type") != "item":
            raise HTTPException(status_code=400, detail="Item inválido.")
        payload["item_path"] = note["path"]
        payload["item_title"] = note["title"]
    try:
        apply_character_action(
            settings.database_path,
            character_id=profile_id,
            actor_id="master" if access.mode == "gm" else str(access.profile_id),
            actor_role="gm" if access.mode == "gm" else "player",
            action=request.action,
            payload=payload,
            reason=request.reason,
            session_id=request.session_id,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _playable_character(profile_id, access)


@app.get("/characters/{profile_id}/events", response_model=list[CharacterEventResponse])
def playable_character_events(
    profile_id: str,
    access: AccessContext = Depends(require_any),
) -> list[dict]:
    access_level = _character_access_level(access, profile_id)
    if access_level == "public":
        raise HTTPException(status_code=403, detail="Eventos disponíveis apenas ao proprietário e ao Mestre.")
    events = list_character_events(settings.database_path, profile_id)
    if access_level == "owner":
        owner_visible_types = {
            "damage",
            "heal",
            "set_hp",
            "add_condition",
            "remove_condition",
            "consume_resource",
            "equip_item",
            "unequip_item",
            "change_quantity",
        }
        events = [event for event in events if event["event_type"] in owner_visible_types]
    return events


@app.patch("/gm/characters/{profile_id}/definition", response_model=PlayableCharacterResponse, response_model_exclude_none=True)
def gm_update_playable_character_definition(
    profile_id: str,
    request: CharacterDefinitionUpdate,
    access: AccessContext = Depends(require_master),
) -> dict:
    _playable_character(profile_id, access)
    try:
        update_definition_overrides(
            settings.database_path,
            character_id=profile_id,
            actor_id="master",
            fields=dict(request.fields),
            reason=request.reason,
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _playable_character(profile_id, access)


@app.post("/gm/characters/{profile_id}/events/{event_id}/revert", response_model=PlayableCharacterResponse, response_model_exclude_none=True)
def gm_revert_playable_character_event(
    profile_id: str,
    event_id: int,
    access: AccessContext = Depends(require_master),
) -> dict:
    try:
        revert_character_event(
            settings.database_path,
            character_id=profile_id,
            event_id=event_id,
            actor_id="master",
        )
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return _playable_character(profile_id, access)


def _roll_actor(access: AccessContext) -> tuple[str, str]:
    if access.mode == "gm":
        return "master", "gm"
    return access.profile_id or "shared-player", "player"


def _visible_roll(record: dict, access: AccessContext) -> dict | None:
    actor_id, _ = _roll_actor(access)
    if not can_view_roll(record, access_mode=access.mode, profile_id=access.profile_id, actor_id=actor_id):
        return None
    visible = dict(record)
    if access.mode != "gm" and visible.get("target_hidden"):
        visible["target_value"] = None
    return visible


def _validate_player_target(access: AccessContext, target_value: int | None, visibility: str) -> None:
    if access.mode != "gm" and target_value is not None and visibility != "private":
        raise HTTPException(
            status_code=403,
            detail="Jogadores só podem definir dificuldade em uma simulação privada.",
        )


@app.post("/rolls", response_model=DiceRollEventResponse)
def free_dice_roll(request: DiceRollCreate, access: AccessContext = Depends(require_any)) -> dict:
    actor_id, actor_role = _roll_actor(access)
    character_id = request.character_id
    if character_id:
        if _character_access_level(access, character_id) == "public":
            raise HTTPException(status_code=403, detail="Você não pode rolar por este personagem.")
        _playable_character(character_id, access)
    _validate_player_target(access, request.target_value, request.visibility)
    try:
        record, _created = create_roll(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            character_id=character_id,
            actor_id=actor_id,
            actor_role=actor_role,
            roll_type="free",
            label=request.label or "Rolagem livre",
            formula=request.formula,
            visibility=request.visibility,
            session_id=request.session_id,
            target_value=request.target_value,
            target_hidden=request.hide_target,
            source="free",
            scene_id=request.scene_id,
            action_id=request.action_id,
            reason=request.reason,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return record


@app.post("/characters/{profile_id}/rolls", response_model=DiceRollEventResponse)
def character_dice_roll(
    profile_id: str,
    request: CharacterRollCreate,
    access: AccessContext = Depends(require_any),
) -> dict:
    access_level = _character_access_level(access, profile_id)
    if access_level == "public":
        raise HTTPException(status_code=403, detail="Você não pode rolar por este personagem.")
    character = _playable_character(profile_id, access)
    _validate_player_target(access, request.target_value, request.visibility)
    try:
        spec = resolve_character_roll(
            character["definition"],
            character["inventory"],
            request.roll_type,
            request.source_id,
        )
        actor_id, actor_role = _roll_actor(access)
        target = request.target_value if request.target_value is not None else spec.target_value
        record, _created = create_roll(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            character_id=profile_id,
            actor_id=actor_id,
            actor_role=actor_role,
            roll_type=spec.roll_type,
            label=request.label or spec.label,
            formula=spec.formula,
            visibility=request.visibility,
            session_id=request.session_id,
            target_value=target,
            target_hidden=request.hide_target,
            source=spec.source,
            source_id=spec.source_id,
            scene_id=request.scene_id,
            action_id=request.action_id,
            reason=request.reason,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return record


@app.get("/rolls", response_model=list[DiceRollEventResponse])
def dice_roll_history(
    limit: int = Query(default=30, ge=1, le=100),
    access: AccessContext = Depends(require_any),
) -> list[dict]:
    visible: list[dict] = []
    for record in list_rolls(settings.database_path, limit=250):
        filtered = _visible_roll(record, access)
        if filtered is not None:
            visible.append(filtered)
        if len(visible) >= limit:
            break
    return visible


@app.get("/rolls/{roll_id}", response_model=DiceRollEventResponse)
def dice_roll_detail(roll_id: int, access: AccessContext = Depends(require_any)) -> dict:
    record = get_roll(settings.database_path, roll_id)
    visible = _visible_roll(record, access) if record else None
    if visible is None:
        raise HTTPException(status_code=404, detail="Rolagem não encontrada.")
    return visible


@app.post("/gm/rolls/{roll_id}/void", response_model=DiceRollEventResponse)
def gm_void_dice_roll(
    roll_id: int,
    request: DiceRollVoidRequest,
    _: AccessContext = Depends(require_master),
) -> dict:
    try:
        return void_roll(settings.database_path, roll_id=roll_id, actor_id="master", reason=request.reason)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/roll-requests", response_model=DiceRollRequestResponse)
def gm_create_roll_request(
    request: DiceRollRequestCreate,
    _: AccessContext = Depends(require_master),
) -> dict:
    character = _playable_character(request.character_id, AccessContext(mode="gm"))
    try:
        if request.roll_type == "free":
            if not request.formula:
                raise ValueError("Informe a fórmula da rolagem livre")
            parsed = parse_formula(request.formula)
            spec = RollSpec("free", request.label or f"{character['definition']['name']} — Rolagem solicitada", parsed.formula, "gm_request")
        else:
            spec = resolve_character_roll(
                character["definition"],
                character["inventory"],
                request.roll_type,
                request.source_id,
            )
            if request.label:
                spec = RollSpec(spec.roll_type, request.label, spec.formula, spec.source, spec.source_id, spec.target_value)
        record, _created = create_roll_request(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            character_id=request.character_id,
            requested_by="master",
            spec=spec,
            visibility=request.visibility,
            session_id=request.session_id,
            scene_id=request.scene_id,
            action_id=request.action_id,
            target_value=request.target_value,
            target_hidden=request.hide_target,
            reason=request.reason,
            expires_in_hours=request.expires_in_hours,
        )
    except (PermissionError, TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    return record


@app.get("/roll-requests", response_model=list[DiceRollRequestResponse])
def pending_roll_requests(access: AccessContext = Depends(require_any)) -> list[dict]:
    if access.mode == "gm":
        return list_roll_requests(settings.database_path)
    if not access.profile_id:
        return []
    requests = list_roll_requests(settings.database_path, character_id=access.profile_id)
    return [
        {**request, "target_value": None if request.get("target_hidden") else request.get("target_value")}
        for request in requests
        if request.get("visibility") != "gm"
    ]


@app.post("/roll-requests/{roll_request_id}/complete", response_model=DiceRollEventResponse)
def finish_roll_request(
    roll_request_id: int,
    request: DiceRollRequestComplete,
    access: AccessContext = Depends(require_any),
) -> dict:
    actor_id, actor_role = _roll_actor(access)
    try:
        record, _created = complete_roll_request(
            settings.database_path,
            request_id=roll_request_id,
            completion_request_id=request.request_id,
            actor_id=actor_id,
            actor_role=actor_role,
        )
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error
    visible = _visible_roll(record, access)
    if visible is None:
        raise HTTPException(status_code=403, detail="A rolagem foi registrada, mas seu resultado é reservado ao Mestre.")
    if record.get("scene_id"):
        link_completed_roll(
            settings.database_path,
            scene_id=int(record["scene_id"]),
            action_id=int(record["action_id"]) if record.get("action_id") else None,
            roll_id=int(record["id"]),
            actor_id=actor_id,
            actor_role=actor_role,
            public_text=f"{record['label']}: {record['total']}",
        )
    return visible


def _scene_payload(scene_id: int, access: AccessContext) -> dict | None:
    payload = scene_view(
        settings.database_path,
        scene_id,
        access_mode=access.mode,
        profile_id=access.profile_id,
    )
    if payload is None:
        return None
    enriched_participants: list[dict] = []
    for participant in payload.get("participants", []):
        record = dict(participant)
        character_id = record.get("character_id")
        if character_id:
            try:
                record["character"] = _character_summary(_playable_character(str(character_id), access))
            except (HTTPException, ValueError):
                record["character"] = None
        npc_source = str(record.get("npc_source") or "")
        if npc_source.startswith("npc:"):
            try:
                record["npc"] = get_npc(
                    settings.database_path,
                    int(npc_source.split(":", 1)[1]),
                    access_mode=access.mode,
                )
            except (TypeError, ValueError):
                record["npc"] = None
        enriched_participants.append(record)
    payload["participants"] = enriched_participants
    for event in payload.get("events", []):
        if event.get("roll_id"):
            roll = get_roll(settings.database_path, int(event["roll_id"]))
            event["roll"] = _visible_roll(roll, access) if roll else None
    payload["contract_links"] = scene_contract_links(
        settings.database_path,
        scene_id,
        access_mode=access.mode,
        profile_id=access.profile_id,
    )
    return payload


def _contract_http_error(error: Exception) -> HTTPException:
    detail = str(error)
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=detail)
    if isinstance(error, RuntimeError):
        return HTTPException(status_code=409, detail=detail)
    if "inexistente" in detail.casefold() or "não encontrado" in detail.casefold():
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


@app.get("/contracts")
def authorized_contracts(access: AccessContext = Depends(require_any)) -> list[dict]:
    return list_contracts(settings.database_path, access_mode=access.mode, profile_id=access.profile_id)


@app.get("/contracts/{contract_id}")
def authorized_contract(contract_id: int, access: AccessContext = Depends(require_any)) -> dict:
    payload = get_contract(settings.database_path, contract_id, access_mode=access.mode, profile_id=access.profile_id)
    if payload is None:
        raise HTTPException(status_code=404, detail="Contrato inexistente ou não publicado.")
    payload["npcs"] = list_contract_npcs(settings.database_path, contract_id, access_mode=access.mode)
    return payload


@app.get("/contracts/{contract_id}/events")
def authorized_contract_events(contract_id: int, access: AccessContext = Depends(require_any)) -> list[dict]:
    try:
        return list_contract_events(settings.database_path, contract_id, access_mode=access.mode, profile_id=access.profile_id)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/contracts/{contract_id}/accept")
def accept_authorized_contract(contract_id: int, request: ContractAcceptRequest, access: AccessContext = Depends(require_any)) -> dict:
    actor_id = "master" if access.mode == "gm" else access.profile_id
    actor_role = "gm" if access.mode == "gm" else "player"
    if not actor_id:
        raise HTTPException(status_code=403, detail="Use um acesso individual para aceitar contrato.")
    character_id = request.character_id
    if actor_role == "player":
        character_id = character_id or access.profile_id
        if character_id != access.profile_id:
            raise HTTPException(status_code=403, detail="Personagem não autorizado.")
    if character_id:
        _playable_character(character_id, access if access.mode == "gm" else AccessContext(mode="player", profile_id=character_id))
    try:
        return accept_contract(
            settings.database_path,
            contract_id,
            request_id=request.request_id,
            actor_id=str(actor_id),
            actor_role=actor_role,
            character_id=character_id,
            public_role=request.public_role,
        )
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts")
def gm_create_contract(request: ContractCreate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        contract, _created = create_contract(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            actor_id="master",
            fields=request.model_dump(exclude={"request_id"}),
        )
        return contract
    except Exception as error:
        raise _contract_http_error(error) from error


@app.patch("/gm/contracts/{contract_id}")
def gm_update_contract(contract_id: int, request: VersionedPatch, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_contract(settings.database_path, contract_id, expected_version=request.expected_version, fields=dict(request.fields), actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


def _gm_contract_transition(contract_id: int, status: str, request: ContractTransitionRequest) -> dict:
    return transition_contract(
        settings.database_path,
        contract_id,
        status=status,
        actor_id="master",
        actor_role="gm",
        request_id=request.request_id,
        reason=request.reason,
    )


@app.post("/gm/contracts/{contract_id}/publish")
def gm_publish_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "published", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/accept")
def gm_accept_contract(contract_id: int, request: ContractAcceptRequest, access: AccessContext = Depends(require_master)) -> dict:
    if request.character_id:
        _playable_character(request.character_id, access)
    try:
        return accept_contract(settings.database_path, contract_id, request_id=request.request_id, actor_id="master", actor_role="gm", character_id=request.character_id, public_role=request.public_role)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/start")
def gm_start_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "active", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/complete")
def gm_complete_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "completed", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/fail")
def gm_fail_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "failed", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/abandon")
def gm_abandon_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "abandoned", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/cancel")
def gm_cancel_contract(contract_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return _gm_contract_transition(contract_id, "cancelled", request)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/objectives")
def gm_create_contract_objective(contract_id: int, request: ContractObjectiveCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        objective, _created = create_objective(settings.database_path, contract_id, request_id=request.request_id, actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return objective
    except Exception as error:
        raise _contract_http_error(error) from error


@app.patch("/gm/contract-objectives/{objective_id}")
def gm_update_contract_objective(objective_id: int, request: VersionedPatch, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_objective(settings.database_path, objective_id, expected_version=request.expected_version, fields=dict(request.fields), actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contract-objectives/{objective_id}/status")
def gm_set_contract_objective_status(objective_id: int, request: ObjectiveStatusRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return set_objective_status(settings.database_path, objective_id, status=request.status, request_id=request.request_id, actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/objectives/order")
def gm_reorder_contract_objectives(contract_id: int, request: ObjectiveOrderRequest, _: AccessContext = Depends(require_master)) -> list[dict]:
    try:
        return reorder_objectives(settings.database_path, contract_id, request.order, actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/assignments")
def gm_add_contract_assignment(contract_id: int, request: ContractAssignmentCreate, access: AccessContext = Depends(require_master)) -> dict:
    _playable_character(request.character_id, access)
    try:
        return add_assignment(settings.database_path, contract_id, request_id=request.request_id, character_id=request.character_id, assigned_by="master", public_role=request.public_role)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.delete("/gm/contract-assignments/{assignment_id}")
def gm_remove_contract_assignment(assignment_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return remove_assignment(settings.database_path, assignment_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/scene-links")
def gm_link_contract_scene(contract_id: int, request: ContractSceneLinkCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        link, _created = link_contract_scene(settings.database_path, contract_id, request_id=request.request_id, scene_id=request.scene_id, objective_id=request.objective_id, link_type=request.link_type, created_by="master")
        return link
    except Exception as error:
        raise _contract_http_error(error) from error


@app.delete("/gm/contract-scene-links/{link_id}")
def gm_unlink_contract_scene(link_id: int, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return unlink_contract_scene(settings.database_path, link_id, actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/scenes")
def gm_create_contract_scene(contract_id: int, request: ContractLinkedSceneCreate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        scene, _created = create_scene(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            session_id=request.session_id,
            title=request.title,
            location_name=request.location_name,
            location_source=request.location_source,
            public_description=request.public_description,
            objective=request.objective,
            private_notes=request.private_notes,
            visibility=request.visibility,
            created_by="master",
        )
        link_contract_scene(settings.database_path, contract_id, request_id=f"{request.request_id}:contract-link", scene_id=int(scene["id"]), objective_id=request.objective_id, link_type=request.link_type, created_by="master")
        return _scene_payload(int(scene["id"]), access) or scene
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contracts/{contract_id}/rewards")
def gm_create_contract_reward(contract_id: int, request: ContractRewardCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        reward, _created = create_reward(settings.database_path, contract_id, request_id=request.request_id, actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return reward
    except Exception as error:
        raise _contract_http_error(error) from error


@app.patch("/gm/contract-rewards/{reward_id}")
def gm_update_contract_reward(reward_id: int, request: VersionedPatch, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_reward(settings.database_path, reward_id, expected_version=request.expected_version, fields=dict(request.fields), actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contract-rewards/{reward_id}/approve")
def gm_approve_contract_reward(reward_id: int, request: ContractTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return approve_reward(settings.database_path, reward_id, request_id=request.request_id, actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contract-rewards/{reward_id}/deliver")
def gm_deliver_contract_reward(reward_id: int, request: RewardDeliveryRequest, access: AccessContext = Depends(require_master)) -> dict:
    for character_id in request.character_ids:
        _playable_character(character_id, access)
    try:
        result = deliver_reward(settings.database_path, reward_id, request_id=request.request_id, actor_id="master", character_ids=request.character_ids)
        return result
    except Exception as error:
        raise _contract_http_error(error) from error


@app.get("/reputation")
def authorized_reputation(access: AccessContext = Depends(require_any), character_id: str | None = None, party_id: str | None = "group") -> list[dict]:
    if access.mode != "gm":
        character_id = access.profile_id
        party_id = None
    return list_reputation(settings.database_path, character_id=character_id, party_id=party_id)


@app.post("/gm/reputation")
def gm_apply_reputation(request: ReputationApplyRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return apply_reputation(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            faction_name=request.faction_name,
            delta=request.delta,
            reason=request.reason,
            actor_id="master",
            actor_role="gm",
            contract_id=request.contract_id,
            character_id=request.character_id,
            party_id=request.party_id,
        )
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/reputation/{ledger_id}/revert")
def gm_revert_reputation(ledger_id: int, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return revert_reputation(settings.database_path, ledger_id, actor_id="master")
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/contract-events/{event_id}/void")
def gm_void_contract_event(event_id: int, request: ContractEventVoidRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return void_contract_event(settings.database_path, event_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _contract_http_error(error) from error


@app.post("/gm/sessions")
def gm_create_game_session(request: GameSessionCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        record, _created = create_session(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            title=request.title,
            session_number=request.session_number,
            private_notes=request.private_notes,
            created_by="master",
        )
        return record
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/gm/sessions")
def gm_list_game_sessions(_: AccessContext = Depends(require_master)) -> list[dict]:
    return list_sessions(settings.database_path)


@app.post("/gm/sessions/{session_id}/status")
def gm_update_game_session_status(session_id: int, request: GameSessionStatusUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return change_session_status(settings.database_path, session_id, request.status)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes")
def gm_create_scene(request: SceneCreate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        scene, _created = create_scene(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            session_id=request.session_id,
            title=request.title,
            location_name=request.location_name,
            location_source=request.location_source,
            public_description=request.public_description,
            objective=request.objective,
            private_notes=request.private_notes,
            visibility=request.visibility,
            created_by="master",
        )
        return _scene_payload(int(scene["id"]), access) or scene
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.get("/scenes")
def authorized_scenes(access: AccessContext = Depends(require_any)) -> list[dict]:
    result: list[dict] = []
    for scene in list_scenes(settings.database_path):
        visible = _scene_payload(int(scene["id"]), access)
        if visible is not None:
            result.append(visible)
    return result


@app.get("/scenes/active")
def authorized_active_scene(access: AccessContext = Depends(require_any)) -> dict | None:
    scene = active_scene(settings.database_path)
    return _scene_payload(int(scene["id"]), access) if scene else None


@app.get("/scenes/{scene_id}")
def authorized_scene(scene_id: int, access: AccessContext = Depends(require_any)) -> dict:
    payload = _scene_payload(scene_id, access)
    if payload is None:
        raise HTTPException(status_code=404, detail="Cena não encontrada ou não revelada.")
    return payload


@app.patch("/gm/scenes/{scene_id}")
def gm_edit_scene(scene_id: int, request: SceneUpdate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        update_scene(settings.database_path, scene_id, expected_version=request.expected_version, fields=dict(request.fields))
        return _scene_payload(scene_id, access) or {}
    except RuntimeError as error:
        raise HTTPException(status_code=409, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/{scene_id}/status")
def gm_set_scene_status(scene_id: int, request: SceneStatusUpdate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        change_scene_status(settings.database_path, scene_id, request.status, summary=request.summary)
        if request.status in {"resolved", "abandoned"}:
            record_scene_contract_event(settings.database_path, scene_id=scene_id, actor_id="master", status=request.status, summary=request.summary)
        return _scene_payload(scene_id, access) or {}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/{scene_id}/participants")
def gm_add_scene_participant(scene_id: int, request: SceneParticipantCreate, access: AccessContext = Depends(require_master)) -> dict:
    if request.character_id:
        _playable_character(request.character_id, access)
    try:
        add_participant(
            settings.database_path,
            scene_id,
            participant_type=request.participant_type,
            character_id=request.character_id,
            npc_name=request.npc_name,
            npc_source=request.npc_source,
            public_label=request.public_label,
            public_status=request.public_status,
            private_status=request.private_status,
            visible_to_players=request.visible_to_players,
        )
        return _scene_payload(scene_id, access) or {}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.patch("/gm/scene-participants/{participant_id}")
def gm_edit_scene_participant(participant_id: int, request: SceneParticipantUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_participant(settings.database_path, participant_id, dict(request.fields))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.delete("/gm/scene-participants/{participant_id}")
def gm_remove_scene_participant(participant_id: int, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_participant(settings.database_path, participant_id, {"left_at": datetime.now(timezone.utc).isoformat()})
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/{scene_id}/elements")
def gm_create_scene_element(scene_id: int, request: SceneElementCreate, access: AccessContext = Depends(require_master)) -> dict:
    try:
        create_element(
            settings.database_path,
            scene_id,
            request_id=request.request_id,
            element_type=request.element_type,
            title=request.title,
            public_description=request.public_description,
            private_description=request.private_description,
            status=request.status,
            visibility=request.visibility,
            created_by="master",
        )
        return _scene_payload(scene_id, access) or {}
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.patch("/gm/scene-elements/{element_id}")
def gm_update_scene_element(element_id: int, request: SceneElementUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_element(settings.database_path, element_id, fields=dict(request.fields))
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scene-elements/{element_id}/reveal")
def gm_reveal_scene_element(element_id: int, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_element(settings.database_path, element_id, fields={}, reveal=True)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/scenes/{scene_id}/actions")
def create_scene_action(scene_id: int, request: SceneActionCreate, access: AccessContext = Depends(require_any)) -> dict:
    actor_id, actor_role = _roll_actor(access)
    character_id = request.character_id
    if actor_role != "gm":
        if not access.profile_id:
            raise HTTPException(status_code=403, detail="Use um acesso individual para declarar ações.")
        character_id = access.profile_id
    if character_id:
        _playable_character(character_id, access)
    try:
        action, _created = declare_action(
            settings.database_path,
            scene_id,
            request_id=request.request_id,
            character_id=character_id,
            actor_id=actor_id,
            actor_role=actor_role,
            action_type=request.action_type,
            description=request.description,
            target_label=request.target_label,
            visibility=request.visibility,
        )
        return action
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/scenes/actions/{action_id}/cancel")
def cancel_authorized_scene_action(action_id: int, access: AccessContext = Depends(require_any)) -> dict:
    actor_id, actor_role = _roll_actor(access)
    try:
        return cancel_action(settings.database_path, action_id, actor_id=actor_id, actor_role=actor_role)
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/actions/{action_id}/resolve")
def gm_resolve_scene_action(action_id: int, request: SceneActionResolution, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return resolve_action(settings.database_path, action_id, actor_id="master", resolution=request.resolution)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/actions/{action_id}/reject")
def gm_reject_scene_action(action_id: int, request: SceneActionResolution, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return resolve_action(settings.database_path, action_id, actor_id="master", resolution=request.resolution, reject=True)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/actions/{action_id}/request-roll")
def gm_request_scene_action_roll(action_id: int, request: SceneRollRequestCreate, _: AccessContext = Depends(require_master)) -> dict:
    action = get_action(settings.database_path, action_id)
    if not action:
        raise HTTPException(status_code=404, detail="Ação não encontrada")
    character_id = action.get("character_id")
    if not character_id:
        raise HTTPException(status_code=400, detail="A ação não possui personagem para a rolagem")
    character = _playable_character(str(character_id), AccessContext(mode="gm"))
    try:
        if request.roll_type == "free":
            if not request.formula:
                raise ValueError("Informe a fórmula")
            spec = RollSpec("free", request.label or "Rolagem da cena", parse_formula(request.formula).formula, "scene_action", str(action_id))
        else:
            spec = resolve_character_roll(character["definition"], character["inventory"], request.roll_type, request.source_id)
            if request.label:
                spec = RollSpec(spec.roll_type, request.label, spec.formula, spec.source, spec.source_id, spec.target_value)
        roll_request, _created = create_roll_request(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            character_id=str(character_id),
            requested_by="master",
            spec=spec,
            visibility=request.visibility,
            session_id=str(get_scene(settings.database_path, int(action["scene_id"])).get("session_id") or "") or None,
            scene_id=int(action["scene_id"]),
            action_id=action_id,
            target_value=request.target_value,
            target_hidden=request.hide_target,
            reason=request.reason,
        )
        link_roll_request(settings.database_path, action_id, int(roll_request["id"]))
        return roll_request
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/{scene_id}/consequences")
def gm_apply_scene_consequence(scene_id: int, request: SceneConsequenceCreate, access: AccessContext = Depends(require_master)) -> dict:
    _playable_character(request.character_id, access)
    payload = dict(request.payload)
    if request.action == "grant_item" and payload.get("note_id") is not None:
        note = get_note(settings.database_path, int(payload["note_id"]), access_mode="gm")
        if note is None or note.get("type") != "item":
            raise HTTPException(status_code=400, detail="Item inválido")
        payload["item_path"] = note["path"]
        payload["item_title"] = note["title"]
    try:
        result = apply_character_action(
            settings.database_path,
            character_id=request.character_id,
            actor_id="master",
            actor_role="gm",
            action=request.action,
            payload=payload,
            reason=request.public_text or request.private_text,
            session_id=str(scene_id),
        )
        event = record_consequence(
            settings.database_path,
            scene_id=scene_id,
            action_id=request.action_id,
            character_id=request.character_id,
            character_event_id=int(result["event_id"]),
            actor_id="master",
            title=request.title,
            public_text=request.public_text,
            private_text=request.private_text,
            visibility=request.visibility,
        )
        window_payload = _scene_payload(scene_id, access) or {}
        return {"character_event": result, "scene_event": event, "scene": window_payload}
    except PermissionError as error:
        raise HTTPException(status_code=403, detail=str(error)) from error
    except (TypeError, ValueError) as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scenes/{scene_id}/events")
def gm_create_scene_event(scene_id: int, request: SceneManualEventCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return record_manual_event(settings.database_path, scene_id=scene_id, actor_id="master", title=request.title, public_text=request.public_text, private_text=request.private_text, visibility=request.visibility)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


@app.post("/gm/scene-events/{event_id}/void")
def gm_void_scene_event(event_id: int, request: SceneVoidRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return void_event(settings.database_path, event_id, actor_id="master", reason=request.reason)
    except ValueError as error:
        raise HTTPException(status_code=400, detail=str(error)) from error


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


def _npc_http_error(error: Exception) -> HTTPException:
    detail = str(error)
    if isinstance(error, PermissionError):
        return HTTPException(status_code=403, detail=detail)
    if isinstance(error, RuntimeError):
        return HTTPException(status_code=409, detail=detail)
    if "inexistente" in detail.casefold() or "não encontrado" in detail.casefold():
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


def _frontmatter_list(value) -> list[str]:
    if isinstance(value, list):
        return [str(item).strip() for item in value if str(item).strip()]
    if isinstance(value, str) and value.strip():
        return [part.strip() for part in re.split(r"[,;]", value) if part.strip()]
    return []


@app.get("/npcs")
def authorized_npcs(
    query: str | None = None,
    faction: str | None = None,
    location: str | None = None,
    role: str | None = None,
    status: str | None = None,
    character_id: str | None = None,
    access: AccessContext = Depends(require_any),
) -> list[dict]:
    return list_npcs(
        settings.database_path,
        campaign_id="omnisvera",
        access_mode=access.mode,
        query=query,
        faction=faction,
        location=location,
        role=role,
        status=status,
        character_id=character_id,
    )


@app.get("/npcs/{npc_id}")
def authorized_npc(npc_id: int, access: AccessContext = Depends(require_any)) -> dict:
    payload = get_npc(settings.database_path, npc_id, access_mode=access.mode)
    if payload is None:
        raise HTTPException(status_code=404, detail="NPC inexistente ou ainda não revelado.")
    return payload


@app.get("/npcs/{npc_id}/summary")
def authorized_npc_summary(npc_id: int, access: AccessContext = Depends(require_any)) -> dict:
    payload = npc_structured_summary(
        settings.database_path,
        npc_id,
        access_mode=access.mode,
        character_id=access.profile_id,
    )
    if payload is None:
        raise HTTPException(status_code=404, detail="NPC inexistente ou ainda não revelado.")
    return payload


@app.post("/gm/npcs")
def gm_create_npc(request: NpcCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        npc, _created = create_npc(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            actor_id="master",
            fields=request.model_dump(exclude={"request_id"}),
        )
        return get_npc(settings.database_path, int(npc["id"]), access_mode="gm") or npc
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npcs/import")
def gm_import_npc(request: NpcImportRequest, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    source = resolve_note(settings.database_path, request.source_path, access_mode="gm")
    if source is None:
        raise HTTPException(status_code=404, detail="Nota de NPC não encontrada no índice.")
    note = get_note(settings.database_path, int(source["id"]), access_mode="gm")
    if note is None or str(note.get("type") or "").casefold() != "character":
        raise HTTPException(status_code=400, detail="A importação explícita aceita somente notas de personagem.")
    frontmatter = dict(note.get("frontmatter") or {})
    player_visible = resolve_note(settings.database_path, str(note["path"]), access_mode="player") is not None
    aliases = list(dict.fromkeys([*_frontmatter_list(note.get("aliases")), *_frontmatter_list(frontmatter.get("aliases"))]))
    factions = list(dict.fromkeys([
        *_frontmatter_list(frontmatter.get("faction")),
        *_frontmatter_list(frontmatter.get("factions")),
        *_frontmatter_list(frontmatter.get("related_factions")),
    ]))
    fields = {
        "source_path": note["path"],
        "name": note.get("title") or Path(note["path"]).stem,
        "aliases": aliases,
        "portrait_path": frontmatter.get("thumbnail") or frontmatter.get("portrait") or frontmatter.get("cover"),
        "race": frontmatter.get("race") or frontmatter.get("raça"),
        "class_or_role": frontmatter.get("class") or frontmatter.get("function") or frontmatter.get("role"),
        "occupation": frontmatter.get("occupation") or frontmatter.get("profession"),
        "faction_names": factions,
        "public_description": frontmatter.get("description") or frontmatter.get("summary") or frontmatter.get("info"),
        "canonical_status": frontmatter.get("canon") or frontmatter.get("canonical_status"),
        "visible_to_players": player_visible if request.visible_to_players is None else request.visible_to_players,
        "current_location": frontmatter.get("current_location") or frontmatter.get("location"),
        "public_status": frontmatter.get("status"),
    }
    try:
        npc, _created = create_npc(
            settings.database_path,
            request_id=request.request_id,
            campaign_id="omnisvera",
            actor_id="master",
            fields=fields,
        )
        return get_npc(settings.database_path, int(npc["id"]), access_mode="gm") or npc
    except Exception as error:
        raise _npc_http_error(error) from error


@app.patch("/gm/npcs/{npc_id}")
def gm_update_npc(npc_id: int, request: NpcVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        update_npc(settings.database_path, npc_id, expected_version=request.expected_version, fields=request.fields, actor_id="master")
        return get_npc(settings.database_path, npc_id, access_mode="gm") or {}
    except Exception as error:
        raise _npc_http_error(error) from error


@app.patch("/gm/npcs/{npc_id}/state")
def gm_update_npc_state(npc_id: int, request: NpcVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        update_npc_state(settings.database_path, npc_id, expected_version=request.expected_version, fields=request.fields, actor_id="master")
        return get_npc(settings.database_path, npc_id, access_mode="gm") or {}
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npcs/{npc_id}/relationships")
def gm_create_npc_relationship(npc_id: int, request: NpcRelationshipCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        relationship, _created = create_npc_relationship(
            settings.database_path,
            npc_id,
            request_id=request.request_id,
            fields=request.model_dump(exclude={"request_id", "reason"}),
            actor_id="master",
            reason=request.reason,
        )
        return relationship
    except Exception as error:
        raise _npc_http_error(error) from error


@app.patch("/gm/npc-relationships/{relationship_id}")
def gm_update_npc_relationship(relationship_id: int, request: NpcVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_npc_relationship(settings.database_path, relationship_id, expected_version=request.expected_version, fields=request.fields, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npcs/{npc_id}/memories")
def gm_create_npc_memory(npc_id: int, request: NpcMemoryCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        memory, _created = create_npc_memory(settings.database_path, npc_id, request_id=request.request_id, fields=request.model_dump(exclude={"request_id"}), actor_id="master")
        return memory
    except Exception as error:
        raise _npc_http_error(error) from error


@app.patch("/gm/npc-memories/{memory_id}")
def gm_update_npc_memory(memory_id: int, request: NpcVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_npc_memory(settings.database_path, memory_id, expected_version=request.expected_version, fields=request.fields, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npc-memories/{memory_id}/contradict")
def gm_contradict_npc_memory(memory_id: int, request: NpcMemoryContradict, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return contradict_npc_memory(
            settings.database_path,
            memory_id,
            request_id=request.request_id,
            fields=request.model_dump(exclude={"request_id", "reason"}),
            actor_id="master",
            reason=request.reason,
        )
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npcs/{npc_id}/encounters")
def gm_record_npc_encounter(npc_id: int, request: NpcEncounterCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        encounter, _created = record_npc_encounter(settings.database_path, npc_id, request_id=request.request_id, fields=request.model_dump(exclude={"request_id"}), actor_id="master")
        return encounter
    except Exception as error:
        raise _npc_http_error(error) from error


@app.delete("/gm/npc-encounters/{encounter_id}")
def gm_unlink_npc_encounter(encounter_id: int, request: NpcEventVoidRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return unlink_npc_encounter(settings.database_path, encounter_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _npc_http_error(error) from error


@app.post("/gm/npcs/{npc_id}/contracts")
def gm_link_npc_contract(npc_id: int, request: NpcContractLinkCreate, _: AccessContext = Depends(require_master)) -> dict:
    if get_contract(settings.database_path, request.contract_id, access_mode="gm") is None:
        raise HTTPException(status_code=404, detail="Contrato inexistente.")
    try:
        link, _created = link_npc_contract(settings.database_path, npc_id, request_id=request.request_id, contract_id=request.contract_id, role=request.role, visible_to_players=request.visible_to_players, actor_id="master")
        return link
    except Exception as error:
        raise _npc_http_error(error) from error


@app.get("/contracts/{contract_id}/npcs")
def authorized_contract_npcs(contract_id: int, access: AccessContext = Depends(require_any)) -> list[dict]:
    if get_contract(settings.database_path, contract_id, access_mode=access.mode, profile_id=access.profile_id) is None:
        raise HTTPException(status_code=404, detail="Contrato inexistente ou ainda não revelado.")
    return list_contract_npcs(settings.database_path, contract_id, access_mode=access.mode)


@app.post("/gm/npc-events/{event_id}/void")
def gm_void_npc_event(event_id: int, request: NpcEventVoidRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return void_npc_event(settings.database_path, event_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _npc_http_error(error) from error


def _world_http_error(error: Exception) -> HTTPException:
    detail = str(error)
    if isinstance(error, RuntimeError) and "Versão" in detail:
        return HTTPException(status_code=409, detail=detail)
    if "inexistente" in detail or "não revelado" in detail:
        return HTTPException(status_code=404, detail=detail)
    return HTTPException(status_code=400, detail=detail)


def _leaflet_preview(note: dict) -> dict:
    frontmatter = dict(note.get("frontmatter") or {})
    content = str(note.get("content") or "")
    block_match = re.search(r"```leaflet\s*\n([\s\S]*?)```", content, re.IGNORECASE)
    block = block_match.group(1) if block_match else ""
    values: dict[str, str] = {}
    for line in block.splitlines():
        if ":" not in line:
            continue
        key, value = line.split(":", 1)
        if key.strip() in {"image", "width", "height", "lat", "long", "bounds", "unit"}:
            values[key.strip()] = value.strip()
    warnings: list[str] = []
    if not values.get("image") and not frontmatter.get("cover"):
        warnings.append("A nota não informa imagem de mapa.")
    if "marker" in block.casefold():
        warnings.append("Marcadores do plugin exigem revisão; nenhum foi importado automaticamente.")
    return {
        "source_path": note.get("path"),
        "title": note.get("title") or Path(str(note.get("path") or "Mapa")).stem,
        "image_path": values.get("image") or frontmatter.get("cover"),
        "width": frontmatter.get("width"),
        "height": frontmatter.get("height"),
        "map_type": frontmatter.get("map_scope") or "custom",
        "coordinate_system": "percentage",
        "visibility": "table" if str(frontmatter.get("visibility") or "").casefold() in {"jogadores", "public", "players"} else "gm",
        "warnings": warnings,
        "adapter": "obsidian_leaflet_image_v1" if block_match else "frontmatter_map_v1",
    }


@app.get("/world/maps")
def authorized_world_maps(access: AccessContext = Depends(require_any)) -> list[dict]:
    return list_maps(settings.database_path, campaign_id="omnisvera", access_mode=access.mode)


@app.get("/world/maps/{map_id}")
def authorized_world_map(map_id: int, access: AccessContext = Depends(require_any)) -> dict:
    item = get_map(settings.database_path, map_id, access_mode=access.mode)
    if item is None:
        raise HTTPException(status_code=404, detail="Mapa inexistente ou ainda não revelado.")
    return item


@app.post("/gm/world/maps")
def gm_create_world_map(request: WorldMapCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = create_map(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.patch("/gm/world/maps/{map_id}")
def gm_update_world_map(map_id: int, request: WorldVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_map(settings.database_path, map_id, expected_version=request.expected_version, fields=request.fields)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/maps/import-preview")
def gm_preview_world_map(request: WorldImportRequest, _: AccessContext = Depends(require_master)) -> dict:
    maybe_refresh_index()
    source = resolve_note(settings.database_path, request.source_path, access_mode="gm")
    if source is None:
        raise HTTPException(status_code=404, detail="Nota de mapa não encontrada.")
    note = get_note(settings.database_path, int(source["id"]), access_mode="gm")
    if note is None or str(note.get("type") or "").casefold() != "map":
        raise HTTPException(status_code=400, detail="A prévia aceita somente uma nota do tipo map.")
    return _leaflet_preview(note)


@app.post("/gm/world/maps/import")
def gm_import_world_map(request: WorldImportRequest, _: AccessContext = Depends(require_master)) -> dict:
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Revise a prévia e confirme a importação explicitamente.")
    preview = gm_preview_world_map(request)
    fields = {key: preview.get(key) for key in ("source_path", "title", "image_path", "width", "height", "coordinate_system")}
    map_type = str(preview.get("map_type") or "custom").casefold()
    fields["map_type"] = map_type if map_type in {"world", "continent", "territory", "region", "city", "district", "dungeon", "schematic", "custom"} else "custom"
    fields["visibility"] = request.visibility or preview.get("visibility") or "gm"
    try:
        item, _ = create_map(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=fields)
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.get("/world/locations")
def authorized_world_locations(map_id: int | None = None, query: str | None = None, access: AccessContext = Depends(require_any)) -> list[dict]:
    return list_locations(settings.database_path, campaign_id="omnisvera", access_mode=access.mode, profile_id=access.profile_id, map_id=map_id, query=query)


@app.get("/world/locations/{location_id}")
def authorized_world_location(location_id: int, access: AccessContext = Depends(require_any)) -> dict:
    item = get_location(settings.database_path, location_id, access_mode=access.mode, profile_id=access.profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Local inexistente ou ainda não descoberto.")
    return item


@app.post("/gm/world/locations")
def gm_create_world_location(request: WorldLocationCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = create_location(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/locations/import")
def gm_import_world_location(request: WorldImportRequest, map_id: int | None = None, _: AccessContext = Depends(require_master)) -> dict:
    if not request.confirm:
        raise HTTPException(status_code=400, detail="Revise a nota e confirme a importação explicitamente.")
    maybe_refresh_index()
    source = resolve_note(settings.database_path, request.source_path, access_mode="gm")
    if source is None:
        raise HTTPException(status_code=404, detail="Nota de local não encontrada.")
    note = get_note(settings.database_path, int(source["id"]), access_mode="gm")
    if note is None or str(note.get("type") or "").casefold() not in {"location", "territory"}:
        raise HTTPException(status_code=400, detail="A importação aceita somente notas de local ou território.")
    fm = dict(note.get("frontmatter") or {})
    location_type = str(fm.get("location_type") or fm.get("type") or "unknown").casefold()
    if location_type not in {"realm", "territory", "region", "city", "village", "port", "fortress", "forest", "mountain", "road", "ruin", "dungeon", "building", "district", "landmark", "unknown", "custom"}:
        location_type = "territory" if str(note.get("type")).casefold() == "territory" else "unknown"
    fields = {
        "map_id": map_id, "source_path": note["path"], "name": note.get("title") or Path(note["path"]).stem,
        "aliases": _frontmatter_list(note.get("aliases")) + _frontmatter_list(fm.get("aliases")),
        "location_type": location_type, "territory_name": fm.get("territory") or fm.get("region"),
        "public_description": fm.get("description") or fm.get("summary") or fm.get("info"),
        "portrait_or_cover_path": fm.get("cover") or fm.get("thumbnail"), "canon_status": fm.get("canon") or fm.get("canonical_status"),
        "visibility": request.visibility or ("table" if resolve_note(settings.database_path, note["path"], access_mode="player") else "gm"),
        "discovered_by_default": bool(request.discovered_by_default),
    }
    try:
        item, _ = create_location(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=fields)
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.patch("/gm/world/locations/{location_id}")
def gm_update_world_location(location_id: int, request: WorldVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_location(settings.database_path, location_id, expected_version=request.expected_version, fields=request.fields)
    except Exception as error:
        raise _world_http_error(error) from error


@app.patch("/gm/world/locations/{location_id}/state")
def gm_update_world_location_state(location_id: int, request: WorldVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_location_state(settings.database_path, location_id, expected_version=request.expected_version, fields=request.fields)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/locations/{location_id}/discoveries")
def gm_discover_world_location(location_id: int, request: LocationDiscoveryCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = discover_location(settings.database_path, location_id, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.get("/world/routes")
def authorized_world_routes(access: AccessContext = Depends(require_any)) -> list[dict]:
    return list_routes(settings.database_path, campaign_id="omnisvera", access_mode=access.mode, profile_id=access.profile_id)


@app.post("/gm/world/routes")
def gm_create_world_route(request: TravelRouteCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = create_route(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.patch("/gm/world/routes/{route_id}")
def gm_update_world_route(route_id: int, request: WorldVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_route(settings.database_path, route_id, expected_version=request.expected_version, fields=request.fields)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/routes/{route_id}/discoveries")
def gm_discover_world_route(route_id: int, request: LocationDiscoveryCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = discover_route(settings.database_path, route_id, request_id=request.request_id, fields=request.model_dump(exclude={"request_id", "public_name_override", "notes"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.get("/world/journeys")
def authorized_world_journeys(access: AccessContext = Depends(require_any)) -> list[dict]:
    return list_journeys(settings.database_path, campaign_id="omnisvera", access_mode=access.mode, profile_id=access.profile_id)


@app.get("/world/journeys/{journey_id}")
def authorized_world_journey(journey_id: int, access: AccessContext = Depends(require_any)) -> dict:
    item = get_journey(settings.database_path, journey_id, access_mode=access.mode, profile_id=access.profile_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Viagem inexistente ou privada.")
    item["events"] = list_journey_events(settings.database_path, journey_id, access_mode=access.mode)
    return item


@app.post("/gm/world/journeys")
def gm_create_world_journey(request: JourneyCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = create_journey(settings.database_path, request_id=request.request_id, campaign_id="omnisvera", actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.patch("/gm/world/journeys/{journey_id}")
def gm_update_world_journey(journey_id: int, request: WorldVersionedUpdate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return update_planned_journey(settings.database_path, journey_id, expected_version=request.expected_version, fields=request.fields)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/journeys/{journey_id}/participants")
def gm_add_world_journey_participant(journey_id: int, request: JourneyParticipantCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = add_journey_participant(settings.database_path, journey_id, request_id=request.request_id, actor_id="master", fields=request.model_dump(exclude={"request_id"}))
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.delete("/gm/world/journey-participants/{participant_id}")
def gm_remove_world_journey_participant(participant_id: int, request: JourneyParticipantRemove, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return remove_journey_participant(settings.database_path, participant_id, request_id=request.request_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/journeys/{journey_id}/transition/{action}")
def gm_transition_world_journey(journey_id: int, action: str, request: JourneyTransitionRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        if action == "complete":
            return complete_journey(settings.database_path, journey_id, request_id=request.request_id, actor_id="master", expected_version=request.expected_version)
        return transition_journey(settings.database_path, journey_id, request_id=request.request_id, actor_id="master", action=action, expected_version=request.expected_version, reason=request.reason)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/journeys/{journey_id}/advance")
def gm_advance_world_journey(journey_id: int, request: JourneyAdvanceRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return advance_journey(settings.database_path, journey_id, request_id=request.request_id, actor_id="master", expected_version=request.expected_version, amount=request.amount)
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/journeys/{journey_id}/scenes")
def gm_link_world_journey_scene(journey_id: int, request: JourneySceneLinkCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = link_journey_scene(settings.database_path, journey_id, request_id=request.request_id, actor_id="master", scene_id=request.scene_id, stage_label=request.stage_label, progress_value=request.progress_value)
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.post("/gm/world/scenes/{scene_id}/location")
def gm_link_world_scene_location(scene_id: int, request: LocationLinkCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = link_location(settings.database_path, kind="scene", owner_id=scene_id, location_id=request.location_id, request_id=request.request_id, actor_id="master")
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.get("/scenes/{scene_id}/locations")
def authorized_scene_locations(scene_id: int, access: AccessContext = Depends(require_any)) -> list[dict]:
    return related_locations(settings.database_path, kind="scene", owner_id=scene_id, access_mode=access.mode, profile_id=access.profile_id)


@app.post("/gm/world/contracts/{contract_id}/locations")
def gm_link_world_contract_location(contract_id: int, request: LocationLinkCreate, _: AccessContext = Depends(require_master)) -> dict:
    try:
        item, _ = link_location(settings.database_path, kind="contract", owner_id=contract_id, location_id=request.location_id, request_id=request.request_id, actor_id="master", role=request.role, public=request.public)
        return item
    except Exception as error:
        raise _world_http_error(error) from error


@app.get("/contracts/{contract_id}/locations")
def authorized_contract_locations(contract_id: int, access: AccessContext = Depends(require_any)) -> list[dict]:
    return related_locations(settings.database_path, kind="contract", owner_id=contract_id, access_mode=access.mode, profile_id=access.profile_id)


@app.post("/gm/world/journey-events/{event_id}/void")
def gm_void_world_journey_event(event_id: int, request: NpcEventVoidRequest, _: AccessContext = Depends(require_master)) -> dict:
    try:
        return void_journey_event(settings.database_path, event_id, actor_id="master", reason=request.reason)
    except Exception as error:
        raise _world_http_error(error) from error


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
    if full_path.startswith(("health", "notes", "index", "search", "chat", "gm", "player", "characters", "rolls", "roll-requests", "scenes", "sessions", "contracts", "npcs", "media")):
        raise HTTPException(status_code=404, detail="Endpoint não encontrado.")
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index, headers={"Cache-Control": "no-store"})
    return {"message": "Omnisvera Companion backend ativo; frontend dist ausente."}
