"""Envio seletivo de preparações de cena à Mesa. Somente leitura/mutação restrita."""
from __future__ import annotations

import hashlib
import json
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from . import battle_mode
from . import scene_play
from . import session_context
from . import session_ledger
from . import session_workspace
from .combat_effects import effect_snapshot


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _intent_hash(
    scene_id: int,
    element_ids: list[int],
    token_ids: list[str],
    include_map: bool,
    map_id: str | None,
) -> str:
    payload = {
        "scene_id": int(scene_id),
        "element_ids": sorted(int(x) for x in element_ids),
        "token_ids": sorted(str(x) for x in token_ids),
        "include_map": bool(include_map),
        "map_id": map_id,
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True)
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def open_selection(
    database_path: Path,
    scene_id: int,
    *,
    request_id: str,
    element_ids: list[int] | None = None,
    token_ids: list[str] | None = None,
    include_map: bool = False,
    actor_id: str = "master",
) -> dict[str, Any]:
    scene_play.init_scene_play(database_path)
    session_workspace.init_session_workspace(database_path)
    from .character_play import init_character_play
    from .dice_rolls import init_dice_rolls
    init_character_play(database_path)
    init_dice_rolls(database_path)
    session_ledger.init_session_ledger(database_path)
    from .combat_effects import init_effects
    init_effects(database_path)

    req = str(request_id or "").strip()
    if not 8 <= len(req) <= 120 or not all(c.isalnum() or c in "._:-" for c in req):
        raise ValueError("request_id inválido")

    element_ids = sorted(set(element_ids or []))
    token_ids = sorted(set(token_ids or []))
    if len(element_ids)>200 or len(token_ids)>200:raise ValueError('Seleção grande demais')
    if not element_ids and not token_ids and not include_map:raise ValueError('Selecione ao menos um elemento ou mapa')
    for eid in element_ids:
        int(eid)
    for tid in token_ids:
        str(tid)

    intent_hash = _intent_hash(scene_id, element_ids, token_ids, include_map, None)

    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        event_key=f'scene-selection:{req}'
        existing_event=connection.execute('SELECT * FROM scene_events WHERE event_key=?',(event_key,)).fetchone()
        if existing_event:
            existing=scene_play._record(existing_event) or {}
            metadata=json.loads(existing.get('private_text') or '{}')
            if metadata.get('intent_hash')!=intent_hash:raise ValueError('request_id já utilizado com intenção diferente')
            return {'scene_id':scene_id,'map_id':metadata.get('map_id'),'event':existing,'created':False}

        scene_row = connection.execute("SELECT * FROM scenes WHERE id=?", (int(scene_id),)).fetchone()
        if not scene_row:
            raise ValueError("Cena não encontrada")
        scene = scene_play._record(scene_row) or {}

        if scene.get("status") == "resolved":
            raise ValueError("Cena encerrada não pode ser aberta")

        campaign_id = scene.get("campaign_id") or "omnisvera"
        active_session_id = session_context.active_game_session_id(connection, campaign_id)
        if active_session_id is None:
            raise ValueError("Sessão ativa necessária")
        if scene.get("session_id") is not None and int(scene["session_id"]) != int(active_session_id):
            raise ValueError("A cena pertence a outra sessão operacional")

        snapshot = effect_snapshot(connection)
        encounter = snapshot.get("encounter") or {}
        in_combat = bool(encounter.get("active"))

        selected_elements = []
        for eid in element_ids:
            erow = connection.execute("SELECT * FROM scene_elements WHERE id=? AND scene_id=?", (int(eid), int(scene["id"]))).fetchone()
            if not erow:
                raise ValueError("Elemento não pertence à cena")
            selected_elements.append(scene_play._record(erow) or {})

        scene_map_id = scene.get("map_id")
        for tid in token_ids:
            trow = connection.execute("SELECT * FROM session_workspace_tokens WHERE id=?", (str(tid),)).fetchone()
            if not trow:
                raise ValueError("Marcador não encontrado")
            tmap = trow["map_id"]
            if not scene_map_id or tmap != scene_map_id:
                raise ValueError("Marcador não pertence ao mapa da cena")

        target_map_id = scene_map_id
        if include_map:
            if not target_map_id:
                raise ValueError("Cena sem mapa para envio")
            if in_combat:
                current_encounter_map = encounter.get("map_id")
                if current_encounter_map and current_encounter_map != target_map_id:
                    raise ValueError("Não é possível trocar mapa durante combate ativo")
            battle_mode.switch_map(connection, target_map_id, _now())
            connection.execute('UPDATE session_workspace_maps SET visible_to_players=1 WHERE id=?',(target_map_id,))
        else:
            target_map_id = None

        others = connection.execute("SELECT * FROM scenes WHERE campaign_id=? AND status='active' AND id<>?", (campaign_id, scene["id"])).fetchall()
        for other_row in others:
            other = scene_play._record(other_row) or {}
            connection.execute("UPDATE scenes SET status='paused',version=version+1 WHERE id=?", (other["id"],))
            scene_play._event(
                    connection,
                    scene=other,
                    actor_id=actor_id,
                    actor_role="gm",
                    event_type="scene_paused",
                    title="Cena pausada por ativação de outra cena",
                    visibility="table",
                    event_key=f"auto-pause:{other['id']}:{scene['id']}",
            )

        now = _now()
        connection.execute(
            "UPDATE scenes SET session_id=COALESCE(session_id,?),status='active',visibility='table',activated_at=CASE WHEN activated_at IS NULL THEN ? ELSE activated_at END,version=version+1 WHERE id=?",
            (active_session_id,now, int(scene["id"])),
        )
        updated_scene_row = connection.execute("SELECT * FROM scenes WHERE id=?", (int(scene["id"]),)).fetchone()
        updated_scene = scene_play._record(updated_scene_row) or scene

        for elem in selected_elements:
            connection.execute(
                "UPDATE scene_elements SET visibility='table',status='revealed',discovered_at=COALESCE(discovered_at,?),discovered_by=COALESCE(discovered_by,?),version=version+1 WHERE id=? AND scene_id=?",
                (now,actor_id,int(elem["id"]), int(scene["id"])),
            )
        for identity in token_ids:
            connection.execute('UPDATE session_workspace_tokens SET visible_to_players=1,updated_at=? WHERE id=?',(now,identity))

        public_parts = []
        for elem in selected_elements:
            title = elem.get("title") or ""
            pdesc = elem.get("public_description") or ""
            if pdesc:
                public_parts.append(f"{title}: {pdesc}")
            elif title:
                public_parts.append(title)
        public_text = " | ".join(public_parts) if public_parts else "Preparação selecionada enviada à Mesa."

        private_intent = json.dumps({"intent_hash": intent_hash,'map_id':target_map_id if include_map else None}, ensure_ascii=False)

        event = scene_play._event(
            connection,
            scene=updated_scene,
            actor_id=actor_id,
            actor_role="gm",
            event_type="scene_selection_opened",
            title="Preparação de cena enviada à Mesa",
            visibility="table",
            public_text=public_text,
            private_text=private_intent,
            event_key=event_key,
        )

        session_ledger.append_session_ledger_event(
                connection,
                source_type="scene_selection",
                source_id=event_key,
                event_kind="action",
                actor_id=actor_id,
                actor_name="Mesa" if actor_id == "master" else actor_id,
                actor_role="gm",
                character_id=None,
                title="Preparação de cena enviada à Mesa (seleção)",
                detail={"scene_id": int(scene["id"]), "element_ids": sorted(element_ids), "token_ids": sorted(token_ids), "include_map": bool(include_map)},
                visibility="table",
                created_at=_now(),
                game_session_id=active_session_id,
        )

        map_id_result = target_map_id if include_map else None
        return {
            "scene_id": int(scene["id"]),
            "map_id": map_id_result,
            "event": event,
            "created": True,
        }
