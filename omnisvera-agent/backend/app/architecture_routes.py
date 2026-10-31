"""GM-only read-only architecture contracts.

The router exposes the validated code component index and route ownership. It
never returns campaign data, character state, notes or operational paths.
"""
from __future__ import annotations

from typing import Any, Callable, Literal

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from .architecture import get_component, load_component_map, route_ownership


class ComponentRoute(BaseModel):
    method: str
    path: str


class ComponentManifest(BaseModel):
    id: str
    backend: list[str]
    frontend: list[str]
    storage: list[str]
    routes: list[ComponentRoute]
    contracts: list[str]
    scope_rule: str
    extension: str


class ComponentListResponse(BaseModel):
    schema_version: int
    kind: Literal["code_component_index"] = "code_component_index"
    campaign_data: Literal[False] = False
    scope: str
    count: int = Field(ge=0)
    approval_policy: str
    components: list[ComponentManifest]


class RouteOwner(BaseModel):
    method: str
    path: str
    component_ids: list[str]


class RouteOwnershipResponse(BaseModel):
    count: int = Field(ge=0)
    routes: list[RouteOwner]


def build_architecture_router(require_master: Callable) -> APIRouter:
    router = APIRouter(tags=["GM architecture"])

    @router.get("/gm/architecture/components", response_model=ComponentListResponse,
                description="Contrato de código por componente; não contém dados de campanha.")
    def component_list(access: Any = Depends(require_master)) -> dict[str, Any]:
        component_map = load_component_map()
        components = component_map["components"]
        return {
            "schema_version": component_map["schema_version"],
            "kind": component_map["kind"],
            "campaign_data": component_map["campaign_data"],
            "scope": component_map["scope"],
            "count": len(components),
            "approval_policy": component_map["approval_policy"],
            "components": components,
        }

    @router.get("/gm/architecture/components/{component_id}", response_model=ComponentManifest,
                description="Metadados de um componente de código; não autoriza execução.")
    def component_detail(component_id: str, access: Any = Depends(require_master)) -> dict[str, Any]:
        component = get_component(component_id)
        if component is None:
            raise HTTPException(status_code=404, detail="Componente não encontrado")
        return component

    @router.get("/gm/architecture/routes", response_model=RouteOwnershipResponse,
                description="Rotas declaradas e seus componentes; não executa handlers.")
    def ownership(access: Any = Depends(require_master)) -> dict[str, Any]:
        routes = route_ownership()
        return {"count": len(routes), "routes": routes}

    return router
