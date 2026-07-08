from __future__ import annotations

from pathlib import Path

from fastapi import Depends, FastAPI, Header, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

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
FRONTEND_DIST = Path(__file__).resolve().parents[2] / "frontend" / "dist"

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


def require_access(
    x_omnisvera_token: str | None = Header(default=None),
    token: str | None = Query(default=None),
) -> None:
    if not settings.access_token:
        return
    provided = x_omnisvera_token or token
    if provided != settings.access_token:
        raise HTTPException(status_code=401, detail="Token de acesso inválido ou ausente.")


@app.on_event("startup")
def startup() -> None:
    init_db(settings.database_path)
    if settings.rebuild_on_startup:
        notes, _ = iter_markdown_notes(settings.vault_path)
        rebuild_index(settings.database_path, notes)


@app.get("/health", response_model=HealthResponse)
async def health(_: None = Depends(require_access)) -> HealthResponse:
    return HealthResponse(
        backend="ok",
        vault_path=str(settings.vault_path),
        database_path=str(settings.database_path),
        ollama_base_url=settings.ollama_base_url,
        ollama_model=settings.ollama_model,
        ollama_accessible=await check_ollama(settings.ollama_base_url),
    )


@app.post("/index/rebuild", response_model=RebuildResponse)
def rebuild(_: None = Depends(require_access)) -> RebuildResponse:
    notes, skipped = iter_markdown_notes(settings.vault_path)
    indexed = rebuild_index(settings.database_path, notes)
    return RebuildResponse(indexed_notes=indexed, skipped_files=skipped, vault_path=str(settings.vault_path))


@app.get("/notes", response_model=list[NoteSummary])
def notes(_: None = Depends(require_access)) -> list[dict]:
    return list_notes(settings.database_path)


@app.get("/notes/{note_id}", response_model=NoteDetail)
def note(note_id: int, _: None = Depends(require_access)) -> dict:
    item = get_note(settings.database_path, note_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Nota não encontrada")
    return item


@app.post("/search", response_model=list[SearchResult])
def search(request: SearchRequest, _: None = Depends(require_access)) -> list[dict]:
    return search_notes(settings.database_path, request.query, request.limit)


@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, _: None = Depends(require_access)) -> dict:
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


if FRONTEND_DIST.exists():
    app.mount("/assets", StaticFiles(directory=FRONTEND_DIST / "assets"), name="assets")


@app.get("/", response_model=None)
def frontend_root():
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {
        "message": "Frontend ainda não foi buildado. Rode npm install e npm run build em omnisvera-agent/frontend."
    }


@app.get("/{full_path:path}", response_model=None)
def frontend_fallback(request: Request, full_path: str):
    if full_path.startswith(("health", "notes", "index", "search", "chat")):
        raise HTTPException(status_code=404, detail="Endpoint não encontrado.")
    index = FRONTEND_DIST / "index.html"
    if index.exists():
        return FileResponse(index)
    return {"message": "Omnisvera Companion backend ativo; frontend dist ausente."}
