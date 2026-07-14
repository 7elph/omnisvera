from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    backend: str
    vault_path: str
    database_path: str
    ollama_base_url: str
    ollama_model: str
    fast_model: str | None = None
    quality_model: str | None = None
    candidate_model: str | None = None
    production_model: str | None = None
    model_mode: str | None = None
    production_approved: bool = False
    embedding_model: str | None = None
    response_mode: str | None = None
    rag_mode: str | None = None
    semantic_index_path: str | None = None
    auto_refresh_index: bool = False
    auto_refresh_interval_seconds: int | None = None
    ollama_accessible: bool
    access_mode: str | None = None
    player_mode_available: bool = False
    player_profile_id: str | None = None
    player_character_path: str | None = None
    player_character_title: str | None = None
    training_capture_mode: str | None = None
    behavior_memory_enabled: bool = False
    behavior_memory_mode: str | None = None
    behavior_memory_ab_mode: str | None = None


class RebuildResponse(BaseModel):
    indexed_notes: int
    skipped_files: int
    vault_path: str


class NoteSummary(BaseModel):
    id: int
    path: str
    title: str
    aliases: list[str] = Field(default_factory=list)
    type: str | None = None
    visibility: str | None = None
    tags: list[str] = Field(default_factory=list)
    cover: str | None = None
    thumbnail: str | None = None
    status: str | None = None
    description: str | None = None
    updated_at: str


class NoteDetail(NoteSummary):
    content: str
    frontmatter: dict[str, Any] = Field(default_factory=dict)


class SearchRequest(BaseModel):
    query: str
    limit: int = 10


class SearchResult(NoteSummary):
    score: int
    excerpt: str


class ChatRequest(BaseModel):
    question: str
    limit: int = 4
    context_paths: list[str] = Field(default_factory=list)
    session_id: str | None = Field(default=None, max_length=160)


class ChatResponse(BaseModel):
    answer: str
    notes_used: list[NoteSummary]
    note_paths: list[str]
    insufficient_context: bool
    warning: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)
    fatos_confirmados: list[dict[str, Any]] = Field(default_factory=list)
    teorias: list[dict[str, Any]] = Field(default_factory=list)
    informacoes_insuficientes: list[str] = Field(default_factory=list)
    fontes_usadas: list[str] = Field(default_factory=list)
    ollama_used: bool = False
    ollama_attempted: bool = False
    model: str | None = None
    retrieval_mode: str | None = None
    interaction_id: str | None = None
    created_at: str | None = None
    response_time_ms: int | None = None
    raw_model_response: str | None = None
    validator_rejections: list[dict[str, Any]] = Field(default_factory=list)
    behavior_memory_used: bool = False
    behavioral_trace: dict[str, Any] | None = None


class TrainingInteractionCapture(BaseModel):
    interaction_id: str | None = None
    session_id: str | None = None
    user_profile: str = "gm"
    player_id: str | None = None
    character_id: str | None = None
    persona_id: str | None = None
    question: str = Field(min_length=2, max_length=5000)
    raw_model_response: str | None = Field(default=None, max_length=20_000)
    final_response: str = Field(max_length=20_000)
    verified_facts: list[dict[str, Any]] = Field(default_factory=list)
    theories: list[dict[str, Any]] = Field(default_factory=list)
    insufficient_information: list[str] = Field(default_factory=list)
    retrieved_sources: list[dict[str, Any]] = Field(default_factory=list)
    retrieval_mode: str | None = None
    model: str | None = None
    ollama_used: bool = False
    response_time_ms: int = Field(default=0, ge=0)
    validator_rejections: list[dict[str, Any]] = Field(default_factory=list)
    warning: str | None = Field(default=None, max_length=2000)
    behavior_memory_used: bool = False
    behavioral_trace: dict[str, Any] | None = None
    feedback_action: str
    reason: str | None = Field(default=None, max_length=3000)
    category: str | None = None
    persona_id_override: str | None = None


class TrainingExamplePatch(BaseModel):
    category: str | None = None
    source_type: str | None = None
    persona_id: str | None = None
    ideal_response: str | None = Field(default=None, max_length=20_000)
    facts_expected: list[str] | None = None
    theories_allowed: list[str] | None = None
    insufficient_information_expected: bool | None = None
    requires_rag: bool | None = None
    contains_canon: bool | None = None
    contains_secret: bool | None = None
    notes: str | None = Field(default=None, max_length=5000)
    quality: int | None = Field(default=None, ge=1, le=5)
    hallucination_detected: bool | None = None
    leak_detected: bool | None = None
    incomplete_detected: bool | None = None
    artificial_detected: bool | None = None
    incorrect_source_detected: bool | None = None
    reason: str | None = Field(default=None, max_length=3000)


class TrainingDecisionRequest(BaseModel):
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    reason: str | None = Field(default=None, max_length=3000)
    ideal_response: str | None = Field(default=None, max_length=20_000)
    quality: int | None = Field(default=None, ge=1, le=5)


class TrainingFlagRequest(BaseModel):
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    detail: str | None = Field(default=None, max_length=3000)


class TrainingBatchRequest(BaseModel):
    example_ids: list[str] = Field(min_length=1, max_length=100)
    reviewer: str = Field(default="Sage", min_length=2, max_length=120)
    reviewed: bool = False
    confirmation: str = Field(default="", max_length=80)
    reason: str | None = Field(default=None, max_length=3000)
    minimum_quality: int = Field(default=4, ge=1, le=5)


class DashboardSection(BaseModel):
    kind: str | None = None
    title: str
    description: str | None = None
    cover: str | None = None
    prompt: str | None = None
    items: list[NoteSummary] = Field(default_factory=list)


class PlayerDashboardResponse(BaseModel):
    mode: str = "player"
    sections: list[DashboardSection] = Field(default_factory=list)


class PlayerActionCreate(BaseModel):
    character_note_id: int
    action_type: str
    target_note_id: int
    intent: str = Field(min_length=3, max_length=1200)


class PlayerActionUpdate(BaseModel):
    status: str
    gm_response: str | None = Field(default=None, max_length=2400)


class PlayerActionRecord(BaseModel):
    id: int
    character_path: str
    character_title: str
    action_type: str
    target_path: str
    target_title: str
    intent: str
    status: str
    gm_response: str | None = None
    created_at: str
    updated_at: str


class PlayerProfileResponse(BaseModel):
    profile_id: str | None = None
    character_path: str | None = None
    character_title: str | None = None
    character_note_id: int | None = None
    thumbnail: str | None = None
    cover: str | None = None
    character_class: str | None = None
    race: str | None = None
    level: str | int | None = None
    status: str | None = None
    location: str | None = None
    faction: str | None = None
    shared_access: bool = False


class PlayerDiscoveryCreate(BaseModel):
    profile_id: str
    note_id: int


class PlayerDiscoveryRecord(BaseModel):
    id: int
    profile_id: str
    note_path: str
    note_title: str
    created_at: str


class PlayerEventRecord(BaseModel):
    id: int
    profile_id: str
    kind: str
    title: str
    message: str
    note_path: str | None = None
    created_at: str
    read_at: str | None = None


class PlayerEventReadRequest(BaseModel):
    event_ids: list[int] = Field(default_factory=list)


class PlayerQuestUpdate(BaseModel):
    profile_id: str = "group"
    note_id: int
    status: str
    progress: str | None = Field(default=None, max_length=1200)


class PlayerQuestRecord(BaseModel):
    id: int
    profile_id: str
    note_path: str
    note_title: str
    status: str
    progress: str | None = None
    updated_at: str


class EditableNoteResponse(BaseModel):
    path: str
    content: str
    content_hash: str
    updated_at: str


class EditableNoteUpdate(BaseModel):
    path: str
    content: str = Field(max_length=500_000)
    expected_hash: str


class InventoryUpdate(BaseModel):
    profile_id: str
    note_id: int
    quantity: int = Field(default=1, ge=0, le=999)
    equipped: bool = False
    notes: str | None = Field(default=None, max_length=500)


class InventoryRecord(BaseModel):
    id: int
    profile_id: str
    item_path: str
    item_title: str
    note_id: int | None = None
    thumbnail: str | None = None
    cover: str | None = None
    quantity: int
    equipped: bool
    notes: str | None = None
    updated_at: str


class PlayerIdeaCreate(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    concept: str = Field(min_length=10, max_length=1800)
    appearance: str | None = Field(default=None, max_length=1000)
    motivation: str | None = Field(default=None, max_length=1000)
    world_connection: str | None = Field(default=None, max_length=1000)


class PlayerIdeaReview(BaseModel):
    status: str
    feedback: str | None = Field(default=None, max_length=1800)


class PlayerIdeaRecord(PlayerIdeaCreate):
    id: int
    author: str
    status: str
    gm_feedback: str | None = None
    created_at: str
    updated_at: str


class CharacterSheetStep(BaseModel):
    key: str
    title: str
    summary: str
    status: str
    fields: dict[str, Any] = Field(default_factory=dict)
    missing_fields: list[str] = Field(default_factory=list)


class CharacterSheetResponse(BaseModel):
    profile_id: str
    character_path: str
    character_title: str
    status: str
    completion_count: int
    total_steps: int
    steps: list[CharacterSheetStep] = Field(default_factory=list)
    submitted_at: str | None = None
    reviewed_at: str | None = None
    gm_feedback: str | None = None
    updated_at: str


class CharacterSheetStepUpdate(BaseModel):
    step_key: str
    fields: dict[str, Any] = Field(default_factory=dict)


class CharacterSheetReview(BaseModel):
    status: str
    feedback: str | None = Field(default=None, max_length=2400)
