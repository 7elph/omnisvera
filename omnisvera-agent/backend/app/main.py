from __future__ import annotations

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from .config import get_settings
from .ollama_client import check_ollama
from .rag import answer_question
from .schemas import (
    ChatRequest,
    ChatResponse,
    HealthResponse,
    NoteDetail,
    NoteSummary,
    RebuildResponse,
    SearchRequest,
    SearchResult,
)
from .search import search_notes
from .vault_index import get_note, init_db, list_notes, rebuild_index
from .vault_reader import iter_markdown_notes


settings = get_settings()
app = FastAPI(title="Omnisvera Companion", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    init_db(settings.database_path)


@app.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse(
        backend="ok",
        vault_path=str(settings.vault_path),
        database_path=str(settings.database_path),
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_accessible=await check_ollama(settings.ollama_base_url),
    )


@app.post("/index/rebuild", response_model=RebuildResponse)
def rebuild() -> RebuildResponse:
    notes, skipped = iter_markdown_notes(settings.vault_path)
    indexed = rebuild_index(settings.database_path, notes)
    return RebuildResponse(indexed_notes=indexed, skipped_files=skipped, vault_path=str(settings.vault_path))


@app.get("/notes", response_model=list[NoteSummary])
def notes() -> list[dict]:
    return list_notes(settings.database_path)


@app.get("/notes/{note_id}", response_model=NoteDetail)
def note(note_id: int) -> dict:
    item = get_note(settings.database_path, note_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest) -> list[dict]:
    return search_notes(settings.database_path, request.query, request.limit)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> dict:
    try:
        return await answer_question(
            settings.database_path,
            settings.ollama_base_url,
            settings.ollama_model,
            request.question,
            request.limit,
        )
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao consultar Ollama/modelo '{settings.ollama_model}': {exc}",
        ) from exc
