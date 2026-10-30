"""GM-only read-only adapters for action manifests and catalog provenance.

Factory callback contracts:
  require_master: FastAPI dependency returning the authorized access context.
  playable_character(character_id, access): effective {definition, state,
      inventory}, or None/HTTP 404. definition.id must match character_id.
  token_loader(token_id, access): authorized native token {id, name, sheet},
      or None/HTTP 404. id must match token_id.
  database_path_provider: reserved dependency injection compatibility; never
      invoked here. Callbacks must be read-only (no get-or-create migrations).

Response schemas:
  character: {character_id, source:"effective_sheet", execution_approved:false,
      actions:[native_action_manifest entries]}.
  token: {token_id, source:"native_token", execution_approved:false, actions:[...]}.
  provenance list: {kind:str|null, count:int, execution_approved:false,
      entries:[catalog_provenance entries with expanded source]}.
  provenance single: one expanded catalog_provenance entry; missing => HTTP 404.

All endpoints require the supplied GM dependency before invoking callbacks.
Only manifest allowlisted metadata is returned, never original DTOs, inventory,
notes or private state. Bindings do not authorize execution or certify mechanics.
"""
from __future__ import annotations

from typing import Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .catalog_provenance import get_catalog_provenance, list_catalog_provenance
from .native_action_manifest import sheet_action_manifest, token_action_manifest


class CharacterActionManifestResponse(BaseModel):
    character_id: str
    source: Literal["effective_sheet"] = "effective_sheet"
    execution_approved: Literal[False] = False
    actions: list[dict[str, Any]]


class TokenActionManifestResponse(BaseModel):
    token_id: str
    source: Literal["native_token"] = "native_token"
    execution_approved: Literal[False] = False
    actions: list[dict[str, Any]]


class CatalogProvenanceListResponse(BaseModel):
    kind: str | None
    count: int = Field(ge=0)
    execution_approved: Literal[False] = False
    entries: list[dict[str, Any]]


def build_action_audit_router(database_path_provider: Callable, require_master: Callable,
                              playable_character: Callable, token_loader: Callable) -> APIRouter:
    router = APIRouter(tags=["GM action audit"])

    @router.get("/gm/actions/manifest/{character_id}", response_model=CharacterActionManifestResponse,
                description="Inventário de ações da ficha efetiva; não executa nem concede permissões.")
    def character_manifest(character_id: str, access: Any = Depends(require_master)) -> dict:
        record = playable_character(character_id, access)
        if not isinstance(record, dict) or not isinstance(record.get("definition"), dict):
            raise HTTPException(status_code=404, detail="Personagem não encontrado")
        definition = record["definition"]
        if definition.get("id") != character_id:
            raise HTTPException(status_code=404, detail="Personagem não encontrado")
        actions = sheet_action_manifest(character_id, definition, record.get("state") or {},
                                        record.get("inventory") or [])
        return {"character_id": character_id, "source": "effective_sheet",
                "execution_approved": False, "actions": actions}

    @router.get("/gm/workspace/tokens/{token_id}/action-manifest", response_model=TokenActionManifestResponse,
                description="Inventário de ataques/ações do token autorizado; não executa efeitos.")
    def native_token_manifest(token_id: str, access: Any = Depends(require_master)) -> dict:
        token = token_loader(token_id, access)
        if not isinstance(token, dict) or token.get("id") != token_id:
            raise HTTPException(status_code=404, detail="Entidade não encontrada")
        return {"token_id": token_id, "source": "native_token", "execution_approved": False,
                "actions": token_action_manifest(token)}

    @router.get("/gm/compendium/provenance", response_model=CatalogProvenanceListResponse,
                description="Fontes verificadas; source_verified não significa execução aprovada.")
    def provenance_list(kind: str | None = None, access: Any = Depends(require_master)) -> dict:
        entries = list_catalog_provenance(kind)
        return {"kind": kind, "count": len(entries), "execution_approved": False, "entries": entries}

    @router.get("/gm/compendium/provenance/{kind}/{catalog_id}", response_model=dict[str, Any],
                description="Fonte de uma entrada revisada; não habilita regras ou habilidades.")
    def provenance_single(kind: str, catalog_id: str, access: Any = Depends(require_master)) -> dict:
        entry = get_catalog_provenance(kind, catalog_id)
        if entry is None:
            raise HTTPException(status_code=404, detail="Proveniência não encontrada")
        return entry

    return router
