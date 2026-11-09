from __future__ import annotations

import sqlite3
import re
import unicodedata
import json
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


_DAMAGE_FORMULA_PATTERN = re.compile(r"(?<![a-z0-9])(\d{1,2}\s*d\s*\d{1,4}(?:\s*[+-]\s*\d{1,4})?)(?![a-z0-9])", re.IGNORECASE)


def _normalized_item_text(value: Any) -> str:
    return "".join(
        character for character in unicodedata.normalize("NFD", str(value or "").casefold())
        if unicodedata.category(character) != "Mn"
    )


def normalize_inventory_item_mechanics(item: dict[str, Any]) -> dict[str, Any]:
    """Fill safe mechanics omitted by legacy/custom inventory records."""
    record = dict(item)
    from .hp_potions import is_compatible, normalize
    if is_compatible(record):
        return normalize(record)
    mechanics = dict(record.get("mechanics") or {})
    if mechanics.get('family_schema')==1 and mechanics.get('family')=='ammunition':
        return {**record,'damage_formula':None,'mechanics':mechanics}
    if currency_item_field(record):
        record['item_type'] = 'currency'
        record['mechanics'] = {**mechanics, 'equipment_slots': []}
        record['usable'] = False
        return record
    if mechanics.get('family_schema')==1 and mechanics.get('family') in {'magic_activation','magic_equipment'}:
        # A duration, save die or drinking table is not a weapon damage formula.
        record['damage_formula']=None
        mechanics.pop('damage_formula',None)
        record['mechanics']=mechanics
        from .inventory_conditions import project_condition
        return project_condition(record)
    text = _normalized_item_text(f"{record.get('item_title') or record.get('name') or ''} {record.get('item_type') or ''}")

    damage_formula = str(record.get("damage_formula") or mechanics.get("damage_formula") or "").strip()
    # Healing dice in a consumable's description are not weapon damage.
    if not damage_formula and not any(word in text for word in ('consumivel', 'kit de reparo', 'pocao', 'potion')):
        raw_effects = record.get("effects") or []
        effects = raw_effects if isinstance(raw_effects, list) else [raw_effects]
        candidates = [*effects, record.get("description") or ""]
        match = next((_DAMAGE_FORMULA_PATTERN.search(str(candidate)) for candidate in candidates if candidate), None)
        if match:
            damage_formula = re.sub(r"\s+", "", match.group(1)).lower()
    if damage_formula:
        record["damage_formula"] = damage_formula
        mechanics["damage_formula"] = damage_formula

    is_weapon = (
        "arma" in text
        or any(term in text for term in ("cajado", "bordao", "espada", "machado", "adaga", "lanca", "martelo", "maca", "mangual", "foice", "sabre", "tridente", "arco", "besta"))
        or (bool(damage_formula) and "escudo" not in text and "muralha" not in text)
    )
    if mechanics.get('family_schema')==1:
        mechanics['equipment_slots']=mechanics.get('approved_equipment_slots') or mechanics.get('equipment_slots') or []
    elif "escudo" in text or "muralha" in text:
        mechanics["equipment_slots"] = ["Mão secundária"]
    elif "manto primordial" in text:
        mechanics["equipment_slots"] = ["Acessório"]
    elif "armadura" in text or "manto" in text:
        mechanics["equipment_slots"] = ["Armadura"]
    elif is_weapon:
        # Weapon category describes what the item is; the player chooses how it
        # is being used in this loadout. Keep this rule identical for Vault and
        # session-created items so every character gets both combat slots.
        mechanics["equipment_slots"] = mechanics.get('approved_equipment_slots') or ["Corpo a corpo", "À distância"]

    if str(record.get('item_path') or '').replace('\\', '/') == 'Items/Adagas de Espectro Fantasma.md':
        # The existing relic explicitly uses the base dagger in both melee and
        # throwing. Equipment slot is a loadout choice, not loss of a mode.
        mechanics['attack_modes'] = ['melee', 'ranged']
        mechanics.setdefault('thrown_damage_formula', damage_formula)

    record["mechanics"] = mechanics
    from .inventory_conditions import project_condition
    return project_condition(record)


def currency_item_field(item: dict[str, Any]) -> str | None:
    """Only explicit denominations; relics, purses and valuables are not cash."""
    kind = _normalized_item_text(item.get('item_type') or item.get('kind')).strip()
    fields = {'pc': 'copper_coins', 'pp': 'silver_coins', 'po': 'coins', 'pl': 'platinum_coins'}
    if kind in fields:
        return fields[kind]
    name = _normalized_item_text(item.get('item_title') or item.get('name')).strip()
    for metal, field in [('cobre','copper_coins'), ('prata','silver_coins'), ('ouro','coins'), ('platina','platinum_coins')]:
        if re.fullmatch(rf'(?:pecas?|moedas?) de {metal}(?:\s*\([a-z]{{2}}\))?', name):
            return field
    return None


def _connect(path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    return connection


def init_player_inventory(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS player_inventory (
              id INTEGER PRIMARY KEY AUTOINCREMENT,
              profile_id TEXT NOT NULL,
              item_path TEXT NOT NULL,
              item_title TEXT NOT NULL,
              quantity INTEGER NOT NULL DEFAULT 1,
              equipped INTEGER NOT NULL DEFAULT 0,
              equipment_slot TEXT,
              charges_current INTEGER,
              charges_max INTEGER,
              recharge TEXT,
              notes TEXT,
              updated_at TEXT NOT NULL,
              UNIQUE(profile_id, item_path)
            )
            """
        )
        for column, definition in (
            ("equipment_slot", "TEXT"),
            ("charges_current", "INTEGER"),
            ("charges_max", "INTEGER"),
            ("recharge", "TEXT"),
        ):
            try:
                connection.execute(f"ALTER TABLE player_inventory ADD COLUMN {column} {definition}")
            except sqlite3.OperationalError as error:
                if "duplicate column" not in str(error).lower():
                    raise
        from .inventory_conditions import init_schema
        init_schema(connection)


def upsert_inventory(database_path: Path, *, profile_id: str, item_path: str, item_title: str, quantity: int, equipped: bool, notes: str | None, equipment_slot: str | None = None, charges_current: int | None = None, charges_max: int | None = None, recharge: str | None = None) -> dict[str, Any]:
    init_player_inventory(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        previous=connection.execute('SELECT id,quantity FROM player_inventory WHERE profile_id=? AND item_path=?',(profile_id,item_path)).fetchone()
        if previous:
            from .portable_hole import protect_quantity
            protect_quantity(connection,previous['id'],quantity)
        if previous and quantity>0:
            from .inventory_conditions import read_condition
            condition=read_condition(connection,previous['id'])
            if previous['quantity']<=0:
                # Replenishing a fully destroyed item creates a fresh physical
                # unit even though the native unique inventory row is reused.
                connection.execute('DELETE FROM inventory_item_conditions WHERE inventory_id=?',(previous['id'],))
            elif condition and condition.get('selection',{}).get('magical') and quantity>previous['quantity']:
                raise ValueError('Não mescle outra unidade com um item mágico corroído; separe as instâncias primeiro')
        connection.execute(
            """
            INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,charges_current,charges_max,recharge,notes,updated_at)
            VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
              item_title=excluded.item_title, quantity=excluded.quantity, equipped=excluded.equipped,
              equipment_slot=excluded.equipment_slot,
              charges_current=COALESCE(excluded.charges_current,player_inventory.charges_current),
              charges_max=COALESCE(excluded.charges_max,player_inventory.charges_max),
              recharge=COALESCE(excluded.recharge,player_inventory.recharge),
              notes=excluded.notes, updated_at=excluded.updated_at
            """,
            (profile_id, item_path, item_title, max(0, quantity), int(equipped), (equipment_slot or "").strip() or None, charges_current, charges_max, (recharge or "").strip() or None, (notes or "").strip() or None, now),
        )
        row = connection.execute("SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?", (profile_id, item_path)).fetchone()
    result = dict(row) if row else {}
    result["equipped"] = bool(result.get("equipped"))
    return result


def list_inventory(database_path: Path, profile_id: str, *, include_empty: bool = False) -> list[dict[str, Any]]:
    init_player_inventory(database_path)
    with closing(_connect(database_path)) as connection, connection:
        quantity_filter = '' if include_empty else ' AND i.quantity>0'
        from .magic_optics import suppressed
        optical_suppressed=suppressed(connection,'character',profile_id) or suppressed(connection,'token',profile_id)
        rows = connection.execute(f'''SELECT i.*,c.data_json AS condition_json,c.version AS condition_version
            FROM player_inventory i LEFT JOIN inventory_item_conditions c ON c.inventory_id=i.id
            WHERE i.profile_id=?{quantity_filter} ORDER BY i.equipped DESC,i.item_title''',(profile_id,)).fetchall()
    result = [dict(row) for row in rows]
    for item in result:
        if optical_suppressed:item['_optical_suppressed']=True
        item["equipped"] = bool(item["equipped"])
        raw=item.pop('condition_json');version=item.pop('condition_version')
        if raw:
            condition = json.loads(raw)
            condition.pop('field_item', None)  # Private GM configuration is served only by the field-item route.
            if condition:
                item['_instance_condition'] = {**condition, 'version': int(version)}
    return result


def recharge_inventory(database_path: Path, recharge: str, profile_id: str | None = None) -> int:
    init_player_inventory(database_path)
    if recharge not in {"inn_rest", "scene", "dawn"}:
        raise ValueError("Tipo de recarga inválido")
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        from .magic_passives import lifetime_inventory_ids
        excluded=lifetime_inventory_ids(connection,profile_id)
        exclusion=' AND id NOT IN ('+','.join('?' for _ in excluded)+')' if excluded else ''
        if profile_id:
            cursor = connection.execute("UPDATE player_inventory SET charges_current=charges_max,updated_at=? WHERE profile_id=? AND recharge=? AND charges_max IS NOT NULL"+exclusion, (now, profile_id, recharge,*excluded))
        else:
            cursor = connection.execute("UPDATE player_inventory SET charges_current=charges_max,updated_at=? WHERE recharge=? AND charges_max IS NOT NULL"+exclusion, (now, recharge,*excluded))
        from .magic_item_uses import recharge_active
        recharge_active(connection,recharge,profile_id,now)
        if recharge=='inn_rest':
            from .magic_containers import recharge_contents
            owners=[profile_id] if profile_id else [r[0] for r in connection.execute('SELECT DISTINCT profile_id FROM player_inventory')]
            for owner in owners:recharge_contents(connection,owner,now)
    return int(cursor.rowcount)
