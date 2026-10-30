"""GM-private Scene Lab HTTP: versioned review only, never execute/publish/apply.

Evidence payload contains request_id/expected_version/run_id ONLY; the supplied
evidence_reader reads an existing terminal local run. That run exercises existing
code, NOT proposal JSON. Review approval is not activation or certification.
Factory callbacks: database_path_provider() -> Path; require_master -> access;
evidence_reader(run_id) -> server-verified allowlisted summary.

POST collection: {request_id,title,kind,content}; PUT item:
{request_id,expected_version,title,content}; POST evidence:
{request_id,expected_version,run_id}; POST decision:
{request_id,expected_version,decision,reason}. Content is a JSON object of at
most 50000 serialized characters; decisions never publish or execute content.
"""
from __future__ import annotations

from contextlib import closing
import json
from pathlib import Path
import sqlite3
from typing import Annotated, Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.routing import APIRoute
from pydantic import BaseModel, ConfigDict, Field, StringConstraints, field_validator

from . import scene_lab_store as store
from .test_run_evidence import SCOPE


RequestId = Annotated[str, StringConstraints(min_length=8, max_length=120, pattern=r"^[A-Za-z0-9._:-]+$")]
Title = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=180)]
Reason = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=2000)]


class StrictBody(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    request_id: RequestId


class ProposalContent(StrictBody):
    title: Title
    content: dict[str, Any]

    @field_validator("content")
    @classmethod
    def safe_content(cls, value: dict) -> dict:
        try:
            raw = json.dumps(value, ensure_ascii=False, allow_nan=False)
        except (ValueError, TypeError, RecursionError) as error:
            raise ValueError("Objeto JSON finito obrigatório") from error
        if len(raw) > 50000:
            raise ValueError("Conteúdo excede 50000 caracteres")
        return value


class ProposalCreate(ProposalContent):
    kind: Literal["action", "scene_bundle"]


class ProposalUpdate(ProposalContent):
    expected_version: Annotated[int, Field(ge=1)]


class EvidenceAttach(StrictBody):
    expected_version: Annotated[int, Field(ge=1)]
    run_id: Annotated[str, StringConstraints(pattern=r"^test-[0-9a-f]{32}$", max_length=37)]


class ProposalDecision(StrictBody):
    expected_version: Annotated[int, Field(ge=1)]
    decision: Literal["approved", "rejected"]
    reason: Reason


class _BadRequestRoute(APIRoute):
    def get_route_handler(self):
        handler = super().get_route_handler()

        async def checked(request: Request):
            try:
                return await handler(request)
            except RequestValidationError as error:
                # Never echo NaN, private proposal bodies or validation inputs.
                raise HTTPException(status_code=400, detail="Solicitação do laboratório inválida") from error
        return checked


def _storage_call(callback, *args, **kwargs):
    try:
        return callback(*args, **kwargs)
    except ValueError as error:
        message = str(error)
        status = 404 if "não encontrad" in message.lower() else (
            409 if "desatualizada" in message.lower() or "já utilizado" in message.lower() else 400)
        raise HTTPException(status_code=status, detail=message) from error


def _existing_scene(database: Path, scene_id: int) -> None:
    if scene_id < 1 or not database.is_file():
        raise HTTPException(status_code=404, detail="Cena não encontrada")
    with closing(sqlite3.connect(database.resolve().as_uri() + "?mode=ro", uri=True)) as connection:
        exists = connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='scenes'").fetchone()
        if not exists or connection.execute("SELECT 1 FROM scenes WHERE id=?", (scene_id,)).fetchone() is None:
            raise HTTPException(status_code=404, detail="Cena não encontrada")


def _author(access) -> str:
    return str((access.get("profile_id") if isinstance(access, dict) else getattr(access, "profile_id", None)) or "master")


def build_scene_lab_router(database_path_provider: Callable, require_master: Callable,
                           evidence_reader: Callable) -> APIRouter:
    router = APIRouter(tags=["GM Scene Lab"], route_class=_BadRequestRoute)

    @router.get("/gm/scenes/{scene_id}/lab/proposals")
    def list_scene_proposals(scene_id: int, access: Any = Depends(require_master)) -> list[dict]:
        database = Path(database_path_provider())
        _existing_scene(database, scene_id)
        return _storage_call(store.list_proposals, database, scene_id=scene_id)

    @router.post("/gm/scenes/{scene_id}/lab/proposals")
    def create(scene_id: int, body: ProposalCreate, access: Any = Depends(require_master)) -> dict:
        return _storage_call(store.create_proposal, Path(database_path_provider()), scene_id=scene_id,
            title=body.title, kind=body.kind, content=body.content, created_by=_author(access), request_id=body.request_id)

    @router.get("/gm/scene-lab/proposals/{proposal_id}")
    def get(proposal_id: int, access: Any = Depends(require_master)) -> dict:
        return _storage_call(store.get_proposal, Path(database_path_provider()), proposal_id)

    @router.put("/gm/scene-lab/proposals/{proposal_id}")
    def update(proposal_id: int, body: ProposalUpdate, access: Any = Depends(require_master)) -> dict:
        return _storage_call(store.update_proposal, Path(database_path_provider()), proposal_id,
            expected_version=body.expected_version, title=body.title, content=body.content, request_id=body.request_id)

    @router.post("/gm/scene-lab/proposals/{proposal_id}/evidence")
    def attach(proposal_id: int, body: EvidenceAttach, access: Any = Depends(require_master)) -> dict:
        database = Path(database_path_provider())
        replay = _storage_call(store.peek_evidence_receipt, database, proposal_id,
            expected_version=body.expected_version, run_id=body.run_id, request_id=body.request_id)
        if replay is not None:
            return replay
        try:
            summary = evidence_reader(body.run_id)
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail="Ensaio ou relatório não encontrado") from error
        except (ValueError, OSError) as error:
            raise HTTPException(status_code=400, detail="Evidência local inválida ou inconclusiva") from error
        if not isinstance(summary, dict) or summary.get("run_id") != body.run_id or summary.get("scope") != SCOPE:
            raise HTTPException(status_code=400, detail="Evidência local inválida")
        allowed = {key: summary[key] for key in ("run_id", "state", "verdict", "scenario_counts", "actors",
                   "ui_suite", "ui_status", "report_sha256") if key in summary}
        allowed.update(certification_ready=False, scope=SCOPE)
        return _storage_call(store.attach_evidence, database, proposal_id,
            expected_version=body.expected_version, run_id=body.run_id, summary=allowed, request_id=body.request_id)

    @router.post("/gm/scene-lab/proposals/{proposal_id}/decision")
    def decision(proposal_id: int, body: ProposalDecision, access: Any = Depends(require_master)) -> dict:
        return _storage_call(store.set_decision, Path(database_path_provider()), proposal_id,
            expected_version=body.expected_version, decision=body.decision, reason=body.reason, request_id=body.request_id)

    return router
