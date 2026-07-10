from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class HealthResponse(BaseModel):
    backend: str
    vault_path: str
    database_path: str
    ollama_base_url: str
    ollama_model: str
    ollama_accessible: bool
    access_mode: str | None = None
    player_mode_available: bool = False


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


class ChatResponse(BaseModel):
    answer: str
    notes_used: list[NoteSummary]
    note_paths: list[str]
    insufficient_context: bool
    warning: str | None = None
    suggested_questions: list[str] = Field(default_factory=list)


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
