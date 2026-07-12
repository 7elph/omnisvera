from __future__ import annotations

import asyncio
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "omnisvera-agent" / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from app.access import PLAYER_BLOCKED_LOOKUP_TERMS, is_player_safe, normalize_text, sanitize_player_text  # noqa: E402
from app.config import get_settings  # noqa: E402
from app.rag import (  # noqa: E402
    _decorate_player_action_answer,
    _player_action_kind,
    _player_action_target,
    answer_question,
)
from app.vault_index import get_note, resolve_note  # noqa: E402


def _access_rules() -> None:
    assert not is_player_safe("Secret.md", "gm", {"visibility": "gm"})
    assert not is_player_safe("Secret.md", "mestre", {"visibility": "mestre"})
    assert not is_player_safe("Secret.md", "Jogadores", {"visibility": "Jogadores", "gm_secret": True})
    assert not is_player_safe(
        "Secret.md",
        "Jogadores",
        {"visibility": "Jogadores", "spoiler_level": "heavy"},
    )
    assert is_player_safe("Public.md", "Público", {"visibility": "Público", "gm_secret": False})


def _section_sanitization() -> None:
    text = "# Pessoa\n\nInformação pública.\n\n## Segredos do Mestre\n\nO nome secreto.\n\n## Relações\n\nContato público."
    sanitized = sanitize_player_text(text)
    assert "Informação pública" in sanitized
    assert "Contato público" in sanitized
    assert "O nome secreto" not in sanitized


def _player_action_rules() -> None:
    question = "Ação — Investigar pista: Remédios Falsos da Maré Baixa. O que já sabemos?"
    assert _player_action_kind(question) == "investigate"
    assert _player_action_target(question) == "Remédios Falsos da Maré Baixa"
    answer = _decorate_player_action_answer("Há uma pista confirmada.", "investigate")
    assert "Próximo passo possível" in answer
    assert "Nada foi tratado como acontecimento canônico" in answer


async def _runtime_checks() -> None:
    settings = get_settings()
    gm_state = resolve_note(settings.database_path, "Estado da Campanha", access_mode="gm")
    player_state = resolve_note(settings.database_path, "Estado da Campanha", access_mode="player")
    assert gm_state is not None
    assert player_state is None

    short = resolve_note(settings.database_path, "Maré Baixa", access_mode="player")
    assert short is not None
    detail = get_note(settings.database_path, short["id"], access_mode="player")
    assert detail is not None and detail.get("content") is not None
    assert resolve_note(settings.database_path, "Lugar Inexistente de Teste", access_mode="player") is None

    fallback = await answer_question(
        settings.database_path,
        "http://127.0.0.1:1",
        "modelo-inexistente",
        "Quem está relacionado aos remédios falsos?",
        access_mode="player",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode="lexical",
        response_mode="grounded",
        fallback_model="modelo-inexistente",
    )
    assert fallback.get("answer")
    assert all("Workflow/" not in path for path in fallback.get("note_paths") or [])
    assert all(
        not any(normalize_text(term) in normalize_text(question) for term in PLAYER_BLOCKED_LOOKUP_TERMS)
        for question in fallback.get("suggested_questions") or []
    )

    blocked = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "Qual é a verdadeira origem do Véu Cinzento?",
        access_mode="player",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode="hybrid",
        response_mode="fast",
        fallback_model=settings.fast_model,
    )
    assert blocked.get("note_paths") == []
    assert "protegida" in normalize_text(blocked.get("warning"))

    followup = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "E quantos anos ele tem?",
        access_mode="player",
        embedding_model=settings.embedding_model,
        semantic_index_path=settings.semantic_index_path,
        rag_mode="hybrid",
        response_mode="fast",
        fallback_model=settings.fast_model,
        conversation_paths=["Characters/Individual/Varkh Nimalis.md"],
    )
    assert followup.get("retrieval_mode") == "conversation_followup"
    assert "30 anos" in str(followup.get("answer"))
    assert followup.get("note_paths") == ["Characters/Individual/Varkh Nimalis.md"]

    where_followup = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "E onde ele está?",
        access_mode="player",
        response_mode="fast",
        conversation_paths=["Characters/Individual/Varkh Nimalis.md"],
    )
    assert "esta em viagem" in normalize_text(where_followup.get("answer"))

    orphan_followup = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "E ela?",
        access_mode="player",
        response_mode="fast",
    )
    assert orphan_followup.get("retrieval_mode") == "conversation_needs_context"
    assert orphan_followup.get("note_paths") == []

    mira = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "Quem é Mira Valen?",
        access_mode="player",
        response_mode="fast",
    )
    mira_answer = normalize_text(mira.get("answer"))
    assert "mira valen faleceu" in mira_answer
    assert "ultimo local conhecido" in mira_answer
    assert "local tambem foi destruido" in mira_answer
    assert "atualmente, mira valen" not in mira_answer

    borders = await answer_question(
        settings.database_path,
        settings.ollama_base_url,
        settings.fast_model,
        "Quais são as fronteiras de Nimalia?",
        access_mode="player",
        response_mode="fast",
    )
    border_answer = normalize_text(borders.get("answer"))
    assert borders.get("retrieval_mode") == "structured:nimalia_borders"
    assert "floresta de avenor" in border_answer
    assert "tracado exato permanece em aberto" in border_answer
    assert "ruinas de valthor" in border_answer
    assert "fortaleza de gharok" in border_answer
    assert "Factions/Coroa de Nimalia.md" not in borders.get("note_paths", [])


def main() -> None:
    _access_rules()
    _section_sanitization()
    _player_action_rules()
    asyncio.run(_runtime_checks())
    print("player safety and fallback: PASS")


if __name__ == "__main__":
    main()
