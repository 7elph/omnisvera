from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path

from .contract_play import (
    accept_contract,
    add_assignment,
    create_contract,
    create_objective,
    set_objective_status,
    transition_contract,
)
from .character_play import apply_character_action
from .session_workspace import list_session_items, save_session_item


def _session_id(database_path: Path, request_id: str) -> int | None:
    with closing(sqlite3.connect(database_path)) as connection:
        row = connection.execute("SELECT id FROM game_sessions WHERE request_id=?", (request_id,)).fetchone()
    return int(row[0]) if row else None


def seed_companion_contracts(database_path: Path) -> dict[str, int]:
    """Create the two confirmed Conclave missions once and never overwrite later GM edits."""
    counters = {"created": 0, "unchanged": 0}

    dragon, created = create_contract(
        database_path,
        request_id="campaign-contract-dragon-sightings-v1",
        campaign_id="omnisvera",
        actor_id="historical-import",
        fields={
            "session_id": _session_id(database_path, "historical-session-004-v1"),
            "title": "Investigar Avistamentos de Dragões",
            "slug": "investigar-avistamentos-de-dragoes",
            "contract_type": "investigação",
            "issuer_name": "Conclave dos Errantes",
            "issuer_type": "facção",
            "issuer_source": "CAMPANHA/Quests/01 - Investigar Avistamentos de Dragões.md",
            "location_name": "Sul de Nimalia",
            "public_summary": "Confirmar se os relatos de dragões eram reais e retornar com informação confiável.",
            "public_briefing": "Vezemir e Raziel encontraram equipamentos de captura, recuperaram uma escama e observaram dragões vivos. A investigação foi concluída com prova material.",
            "private_briefing": "A identidade dos responsáveis pelos equipamentos de captura continua desconhecida.",
            "risk_label": "C",
            "recommended_level": "1",
            "visibility": "table",
        },
    )
    if created:
        counters["created"] += 1
        objective, _ = create_objective(
            database_path,
            int(dragon["id"]),
            request_id="campaign-objective-dragon-proof-v1",
            actor_id="historical-import",
            fields={
                "title": "Confirmar os avistamentos e trazer provas",
                "public_description": "Verificar a presença de criaturas dracônicas e retornar ao Conclave com evidência confiável.",
                "private_description": "A escama foi recuperada, mas ainda não foi entregue ao Conclave.",
                "objective_type": "narrative",
                "status": "active",
                "required": True,
                "revealed_to_players": True,
            },
        )
        for character_id in ("vezemir", "raziel"):
            add_assignment(
                database_path,
                int(dragon["id"]),
                request_id=f"campaign-assignment-dragon-{character_id}-v1",
                character_id=character_id,
                assigned_by="historical-import",
                public_role="Investigador",
            )
        transition_contract(database_path, int(dragon["id"]), status="published", actor_id="historical-import", actor_role="gm", request_id="campaign-dragon-publish-v1")
        accept_contract(database_path, int(dragon["id"]), request_id="campaign-dragon-accept-v1", actor_id="historical-import", actor_role="gm")
        transition_contract(database_path, int(dragon["id"]), status="active", actor_id="historical-import", actor_role="gm", request_id="campaign-dragon-start-v1")
        set_objective_status(database_path, int(objective["id"]), status="completed", request_id="campaign-dragon-objective-complete-v1", actor_id="historical-import")
        transition_contract(database_path, int(dragon["id"]), status="completed", actor_id="historical-import", actor_role="gm", request_id="campaign-dragon-complete-v1", reason="Avistamentos confirmados e prova material recuperada.")
    else:
        counters["unchanged"] += 1

    medicine, created = create_contract(
        database_path,
        request_id="campaign-contract-false-medicines-v1",
        campaign_id="omnisvera",
        actor_id="historical-import",
        fields={
            "title": "Investigar Remédios Falsos de Maré Baixa",
            "slug": "investigar-remedios-falsos-de-mare-baixa",
            "contract_type": "investigação",
            "issuer_name": "Conclave dos Errantes",
            "issuer_type": "facção",
            "issuer_source": "CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md",
            "location_name": "Maré Baixa",
            "public_summary": "Rastrear a origem dos remédios falsos e descobrir quem está usando símbolos ligados a Odran.",
            "public_briefing": "Frascos adulterados circulam por Nimalia. As marcas lembram os métodos de Mestre Odran Veyl, mas há sinais claros de falsificação.",
            "private_briefing": "Não tratar Odran, a Guilda ou a Coroa como culpados sem prova. A verdade completa permanece no Cofre do Mestre.",
            "risk_label": "D",
            "recommended_level": "1",
            "visibility": "table",
        },
    )
    if created:
        counters["created"] += 1
        create_objective(
            database_path,
            int(medicine["id"]),
            request_id="campaign-objective-false-medicines-origin-v1",
            actor_id="historical-import",
            fields={
                "title": "Rastrear a origem e a distribuição",
                "public_description": "Descobrir de onde vêm os frascos, quem os distribui e por que o nome de Odran está ligado ao caso.",
                "private_description": "Preservar suspeitos e conexões ainda não revelados aos jogadores.",
                "objective_type": "narrative",
                "status": "available",
                "required": True,
                "revealed_to_players": True,
            },
        )
        transition_contract(database_path, int(medicine["id"]), status="published", actor_id="historical-import", actor_role="gm", request_id="campaign-medicine-publish-v1")
    else:
        counters["unchanged"] += 1

    return counters


def apply_confirmed_session_four_inventory(database_path: Path) -> dict[str, str | bool]:
    """Record the recovered scale once; never duplicate coins or inventory rows."""
    item = next(
        (row for row in list_session_items(database_path) if str(row.get("name") or "").strip().casefold() == "escama dracônica"),
        None,
    )
    created = item is None
    if item is None:
        item = save_session_item(
            database_path,
            name="Escama Dracônica",
            item_type="Material",
            description="Prova material recuperada durante a investigação dos avistamentos de dragões na Sessão 4.",
            effects=[],
            mechanics={},
            usable=False,
        )
    item_path = f"session-item:{int(item['id'])}"
    with closing(sqlite3.connect(database_path)) as connection:
        held = connection.execute(
            "SELECT quantity FROM player_inventory WHERE profile_id=? AND item_path=? AND quantity>0",
            ("vezemir", item_path),
        ).fetchone()
    if not held:
        apply_character_action(
            database_path,
            character_id="vezemir",
            actor_id="historical-import",
            actor_role="gm",
            action="grant_item",
            payload={"item_path": item_path, "item_title": "Escama Dracônica", "quantity": 1},
            reason="Prova material recuperada na Sessão 4; nenhuma moeda adicional foi aplicada.",
            session_id="historical-session-004-v1",
        )
    return {"item_path": item_path, "created": created, "granted": not bool(held)}
