"""System health route with explicit configuration and privacy boundaries."""
from __future__ import annotations

import asyncio
from typing import Any, Callable

from fastapi import APIRouter, Depends

from .schemas import HealthResponse


def build_system_router(
    settings: Any,
    require_any: Callable,
    ollama_check: Callable,
    game_web_available: Callable[[], bool],
    game_web_url: Callable[[], str],
) -> APIRouter:
    router = APIRouter(tags=["System"])

    @router.get("/health", response_model=HealthResponse)
    async def health(access: Any = Depends(require_any)) -> HealthResponse:
        try:
            ollama_accessible = await asyncio.wait_for(
                ollama_check(settings.ollama_base_url), timeout=1.5
            )
        except (TimeoutError, OSError):
            ollama_accessible = False
        game_available = bool(game_web_available())
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
            ollama_accessible=ollama_accessible,
            access_mode=access.mode,
            player_mode_available=bool(settings.player_token or settings.player_profiles),
            player_profile_id=access.profile_id,
            player_character_path=access.character_path,
            player_character_title=access.character_title,
            game_web_available=game_available,
            game_web_url=game_web_url() if game_available else None,
            training_capture_mode=settings.training_capture_mode if access.mode == "gm" else None,
            behavior_memory_enabled=settings.behavior_memory_enabled,
            behavior_memory_mode=settings.behavior_memory_mode if access.mode == "gm" else None,
            behavior_memory_ab_mode=settings.behavior_memory_ab_mode if access.mode == "gm" else None,
        )

    return router
