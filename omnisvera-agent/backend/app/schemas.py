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
    quantity: int
    equipped: bool
    notes: str | None = None
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
