"""Recharge logic for Dorn's approved combat resources.

No commit/internal transaction management; caller owns transaction/idempotency.
"""
from __future__ import annotations

import json

from .dice_rolls import roll_formula


def _ensure_resource(resources, key, label, maximum=1):
    resource = next((r for r in resources if r.get("key") == key), None)
    if resource is None:
        resource = {"key": key, "label": label, "current": 0, "maximum": maximum}
        resources.append(resource)
    if resource.get("maximum") is None:
        resource["maximum"] = maximum
    return resource


def turn_start(db, participant, encounter, now, request_id, starting=False):
    if not encounter or not encounter.get("active"):
        return {"recharged": False}
    if starting and not any(p.get('target_type')=='character' and p.get('target_id')=='dorn7' for p in encounter.get('participants',[])):
        return {'recharged':False}
    if not participant:
        return {"recharged": False}
    if participant.get("target_type") != "character" or participant.get("target_id") != "dorn7":
        return {"recharged": False}
    sequence=['start',encounter.get('started_at')] if starting else ['turn',encounter.get('started_at'),encounter.get('turn_sequence')]
    if encounter.get('dorn_recharge_sequence')==sequence:return {'recharged':False}
    encounter['dorn_recharge_sequence']=sequence

    row = db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
    if not row:
        return {"recharged": False}
    state = json.loads(row[0])
    resources = state.setdefault("resources", [])

    relampago = _ensure_resource(resources, "dorn_relampago", "Relampago", 1)
    guard = _ensure_resource(resources, "dorn_guard", "Protocolo de Guarda", 1)

    total = None
    recharged = False
    if starting:
        for res in (relampago,guard):res.update(current=1,maximum=1)
        recharged=True
    elif any(int(r.get('current') or 0)<1 for r in (relampago,guard)):
        total=int(roll_formula('1d6')['total'])
    if total is not None and total >= 5:
        changed = False
        for res in (relampago, guard):
            if int(res.get("current") or 0) < int(res.get("maximum") or 1):
                res["current"] = min(int(res.get("maximum") or 1), int(res.get("current") or 0) + 1)
                changed = True
        recharged = changed

    db.execute(
        "UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
        (json.dumps(state, ensure_ascii=False), now, "dorn7"),
    )
    if total is not None:
        from .session_ledger import append_session_ledger_event
        append_session_ledger_event(db,source_type='combat_recharge',source_id=request_id+':dorn:'+str(encounter.get('turn_sequence')),
            event_kind='action',actor_id='dorn7',actor_name='Dorn',actor_role='gm',character_id='dorn7',
            title=f"Dorn · recarga {total} em 1d6 · {'disponível' if recharged else 'aguardando'}",
            detail={'die':total,'recharged':recharged},visibility='table',created_at=now)
    return {"recharged": recharged, "roll": total, "resources": {"dorn_relampago": relampago.get("current"), "dorn_guard": guard.get("current")}}
