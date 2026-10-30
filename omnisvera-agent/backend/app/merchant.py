"""Mercadores: compra/venda com preços do compêndio e pechincha no Carisma.

 Fluxo mediado pelo Mestre (rotas GM): a mesa negocia na fala, o Mestre rola
 a pechincha, confirma o preço final e executa. Tudo auditado no ledger.
 Moedas: cobre=1, prata=10, ouro=100, platina=10000 (T5-1). Preços do
 compêndio em PO; itens sem preço exigem preço do Mestre no estoque.
"""
from __future__ import annotations

import json
import sqlite3
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from .dice_rolls import roll_formula
from .item_catalog import get_catalog_item, is_catalog_reference, require_offerable_item
from .session_ledger import append_session_ledger_event

COIN_FIELDS = ("copper_coins", "silver_coins", "coins", "platinum_coins")
COPPER_PER = {"copper_coins": 1, "silver_coins": 10, "coins": 100, "platinum_coins": 10000}

# Resultado da pechincha (1d20 + mod Carisma): (piso, multiplicador)
HAGGLE_TIERS = [(18, 0.8, "-20%"), (14, 0.9, "-10%"), (6, 1.0, "preço cheio")]


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path), timeout=30)
    connection.row_factory = sqlite3.Row
    return connection


def init_merchants(database_path: Path | None = None) -> None:
    from .config import get_settings
    from .player_inventory import init_player_inventory
    database_path = Path(database_path or get_settings().database_path)
    init_player_inventory(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """CREATE TABLE IF NOT EXISTS merchants(
            id TEXT PRIMARY KEY, name TEXT NOT NULL, location TEXT NOT NULL DEFAULT '',
            buy_pct INTEGER NOT NULL DEFAULT 50, created_at TEXT NOT NULL)""")
        connection.execute(
            """CREATE TABLE IF NOT EXISTS merchant_stock(
            id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL REFERENCES merchants(id) ON DELETE CASCADE,
            compendium_item_id TEXT NOT NULL, name TEXT NOT NULL, quantity INTEGER NOT NULL DEFAULT 1,
            price_override_po REAL, notes TEXT NOT NULL DEFAULT '', created_at TEXT NOT NULL)""")


def _character_state(connection: sqlite3.Connection, character_id: str) -> dict[str, Any]:
    row = connection.execute("SELECT state_json FROM character_states WHERE profile_id=?", (character_id,)).fetchone()
    if not row:
        raise ValueError("Personagem sem ficha")
    return json.loads(row[0])


def _character_sheet(connection: sqlite3.Connection, character_id: str) -> dict[str, Any]:
    row = connection.execute("SELECT data_json FROM character_sheets WHERE profile_id=?", (character_id,)).fetchone()
    if not row:
        raise ValueError("Personagem sem ficha")
    sheet = json.loads(row[0])
    override = connection.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id=?", (character_id,)).fetchone()
    overrides = json.loads(override[0]) if override else {}
    return {"sheet": sheet, "overrides": overrides}


def purse_copper(state: dict[str, Any]) -> int:
    return sum(int(state.get(field) or 0) * COPPER_PER[field] for field in COIN_FIELDS)


def split_copper(total: int) -> dict[str, int]:
    remaining = int(total)
    if remaining < 0:
        raise ValueError("Saldo negativo")
    out: dict[str, int] = {}
    for field in ("platinum_coins", "coins", "silver_coins", "copper_coins"):
        rate = COPPER_PER[field]
        out[field], remaining = divmod(remaining, rate)
    return out


def _check_purse(state: dict[str, Any], expected: dict[str, Any] | None) -> None:
    if expected is None:
        return
    for field in COIN_FIELDS:
        if int(expected.get(field, 0)) != int(state.get(field) or 0):
            raise ValueError("O saldo mudou. Atualize a ficha antes de aplicar novamente")


def _save_purse(connection: sqlite3.Connection, character_id: str, total_copper: int) -> dict[str, int]:
    state = _character_state(connection, character_id)
    state.update(transaction_purse(state, total_copper))
    connection.execute("UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?",
                       (json.dumps(state, ensure_ascii=False), _now(), character_id))
    return {field: int(state.get(field) or 0) for field in COIN_FIELDS}


def transaction_purse(state: dict[str, Any], total_copper: int) -> dict[str, int]:
    """Pay with smaller coins first; make change only when necessary.

    Trading is not a currency exchange: never consolidate the whole wallet or
    mint platinum on receipt. Explicit conversion keeps using split_copper.
    """
    if total_copper < 0:
        raise ValueError("Saldo negativo")
    result = {field: int(state.get(field) or 0) for field in COIN_FIELDS}
    delta = total_copper - purse_copper(state)
    if delta >= 0:
        for field in ('coins', 'silver_coins', 'copper_coins'):
            count, delta = divmod(delta, COPPER_PER[field])
            result[field] += count
        return result
    remaining = -delta
    for index, field in enumerate(COIN_FIELDS):
        rate = COPPER_PER[field]
        spent = min(result[field], (remaining + rate - 1) // rate)
        result[field] -= spent
        remaining -= spent * rate
        if remaining <= 0:
            change = -remaining
            for smaller in reversed(COIN_FIELDS[:index]):
                count, change = divmod(change, COPPER_PER[smaller])
                result[smaller] += count
            break
    return result


def _inventory_upsert(connection: sqlite3.Connection, *, profile_id: str, item_path: str, item_title: str,
                      quantity: int, equipped: bool = False, notes: str | None = None,
                      equipment_slot: str | None = None, charges_current: int | None = None,
                      charges_max: int | None = None, recharge: str | None = None) -> None:
    from datetime import datetime, timezone
    now = datetime.now(timezone.utc).isoformat()
    connection.execute(
        """INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,equipment_slot,charges_current,charges_max,recharge,notes,updated_at)
        VALUES(?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
          item_title=excluded.item_title, quantity=excluded.quantity, equipped=excluded.equipped,
          equipment_slot=excluded.equipment_slot,
          charges_current=COALESCE(excluded.charges_current,player_inventory.charges_current),
          charges_max=COALESCE(excluded.charges_max,player_inventory.charges_max),
          recharge=COALESCE(excluded.recharge,player_inventory.recharge),
          notes=excluded.notes, updated_at=excluded.updated_at""",
        (profile_id, item_path, item_title, max(0, quantity), int(equipped), (equipment_slot or "").strip() or None,
         charges_current, charges_max, (recharge or "").strip() or None, (notes or "").strip() or None, now))


def _inventory_get(connection: sqlite3.Connection, profile_id: str, item_path: str) -> dict[str, Any] | None:
    row = connection.execute("SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?", (profile_id, item_path)).fetchone()
    if row is None:
        return None
    result = dict(row)
    result["equipped"] = bool(result.get("equipped"))
    return result


def create_merchant(database_path: Path, *, name: str, location: str = "") -> dict[str, Any]:
    name = (name or "").strip()
    if not name:
        raise ValueError("Dê um nome ao mercador")
    init_merchants(database_path)
    merchant = {"id": f"merc-{uuid.uuid4().hex[:10]}", "name": name, "location": location.strip()}
    with closing(_connect(Path(database_path))) as connection, connection:
        connection.execute("INSERT INTO merchants(id,name,location,created_at) VALUES(?,?,?,?)",
                           (merchant["id"], merchant["name"], merchant["location"], _now()))
        append_session_ledger_event(connection, source_type="merchant", source_id=merchant["id"], event_kind="state",
                                    actor_id="master", actor_name="Mestre", actor_role="gm", character_id=None,
                                    title=f"Mercador {name} abriu as portas", detail={"location": merchant["location"]},
                                    visibility="gm", created_at=_now())
    return merchant


def list_merchants(database_path: Path) -> list[dict[str, Any]]:
    init_merchants(database_path)
    with closing(_connect(Path(database_path))) as connection:
        merchants = [dict(row) for row in connection.execute("SELECT * FROM merchants ORDER BY name")]
        for merchant in merchants:
            merchant["stock"] = [dict(row) for row in connection.execute(
                "SELECT * FROM merchant_stock WHERE merchant_id=? ORDER BY name", (merchant["id"],))]
            for line in merchant["stock"]:
                item = get_catalog_item(line["compendium_item_id"]) or {}
                line["book_price_po"] = item.get("preco_po")
                line["price_po"] = line["price_override_po"] if line["price_override_po"] is not None else item.get("preco_po")
    return merchants


def add_stock(database_path: Path, *, merchant_id: str, compendium_item_id: str, quantity: int = 1,
              price_override_po: float | None = None, notes: str = "") -> dict[str, Any]:
    item = get_catalog_item(compendium_item_id)
    if item is None:
        from .item_registry import registry,resolve_item,catalog_item
        with closing(_connect(database_path)) as db:item=catalog_item(resolve_item(registry(db),compendium_item_id))
    if item is None:
        raise ValueError("Item do compêndio não encontrado")
    if is_catalog_reference(item):
        raise ValueError('Entrada de referência do livro; escolha um item concreto')
    if quantity != -1 and quantity < 1:
        raise ValueError("Quantidade inválida (-1 = infinito)")
    if price_override_po is not None and price_override_po < 0:
        raise ValueError("Preço inválido")
    if price_override_po is None and item.get("preco_po") is None:
        raise ValueError(f"{item['name']} não tem preço no livro — defina o preço do Mestre")
    require_offerable_item(item,price_override_po=price_override_po)
    init_merchants(database_path)
    line = {"id": f"stock-{uuid.uuid4().hex[:10]}", "merchant_id": merchant_id,
            "compendium_item_id": compendium_item_id, "name": item["name"]}
    with closing(_connect(Path(database_path))) as connection, connection:
        if not connection.execute("SELECT 1 FROM merchants WHERE id=?", (merchant_id,)).fetchone():
            raise ValueError("Mercador não encontrado")
        connection.execute("INSERT INTO merchant_stock(id,merchant_id,compendium_item_id,name,quantity,price_override_po,notes,created_at) VALUES(?,?,?,?,?,?,?,?)",
                           (line["id"], merchant_id, compendium_item_id, item["name"], quantity,
                            price_override_po, notes.strip(), _now()))
        append_session_ledger_event(connection, source_type="merchant_stock", source_id=line["id"],
            event_kind="state", actor_id="master", actor_name="Mestre", actor_role="gm", character_id=None,
            title="Estoque do estabelecimento atualizado", detail={"merchant_id": merchant_id}, visibility="gm", created_at=_now())
    line.update({"quantity": quantity, "price_override_po": price_override_po, "price_po": price_override_po if price_override_po is not None else item.get("preco_po")})
    return line


def remove_stock(database_path: Path, *, stock_id: str) -> None:
    init_merchants(database_path)
    with closing(_connect(Path(database_path))) as connection, connection:
        if not connection.execute("SELECT 1 FROM merchant_stock WHERE id=?", (stock_id,)).fetchone():
            raise ValueError("Item do estoque não encontrado")
        connection.execute("DELETE FROM merchant_stock WHERE id=?", (stock_id,))
        append_session_ledger_event(connection, source_type="merchant_stock_remove", source_id=stock_id,
            event_kind="state", actor_id="master", actor_name="Mestre", actor_role="gm", character_id=None,
            title="Oferta retirada do estabelecimento", detail={}, visibility="gm", created_at=_now())


def haggle(database_path: Path, *, character_id: str, base_price_po: float, roll_mode: str = "digital",
           d20: int | None = None) -> dict[str, Any]:
    from .character_play import attribute_modifier
    if base_price_po <= 0:
        raise ValueError("Preço inválido para pechinchar")
    with closing(_connect(Path(database_path))) as connection:
        data = _character_sheet(connection, character_id)
    attributes = {**(data["sheet"].get("attributes") or {}), **(data["overrides"].get("attributes") or {})}
    charisma = next((value for key, value in attributes.items() if str(key).lower() in ("charisma", "carisma")), 10)
    modifier = attribute_modifier(charisma) or 0
    if roll_mode == "physical":
        if d20 is None or not 1 <= int(d20) <= 20:
            raise ValueError("Informe o d20 físico (1-20)")
        rolled = int(d20)
    elif roll_mode == "digital":
        rolled = int(roll_formula("1d20")["total"])
    else:
        raise ValueError("Modo de rolagem inválido")
    total = rolled + int(modifier)
    multiplier, label = 1.0, "preço cheio"
    for floor, mult, tier_label in HAGGLE_TIERS:
        if total >= floor:
            multiplier, label = mult, tier_label
            break
    if total <= 5:
        multiplier, label = 1.1, "+10% (ofendeu o mercador)"
    return {"d20": rolled, "modifier": int(modifier), "total": total, "tier": label,
            "base_price_po": base_price_po, "adjusted_price_po": round(base_price_po * multiplier, 2)}


def buy(database_path: Path, *, merchant_id: str, stock_id: str, character_id: str, quantity: int = 1,
        final_price_po: float, expected_purse: dict[str, Any] | None = None) -> dict[str, Any]:
    if quantity < 1 or final_price_po < 0:
        raise ValueError("Compra inválida")
    database_path = Path(database_path)
    init_merchants(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        line = connection.execute("SELECT * FROM merchant_stock WHERE id=? AND merchant_id=?", (stock_id, merchant_id)).fetchone()
        if not line:
            raise ValueError("Item do estoque não encontrado")
        line = dict(line)
        if line.get('instance_json'):raise ValueError('Objeto usado: negociação individual; não pode ser comprado como novo')
        require_offerable_item(get_catalog_item(line['compendium_item_id']),price_override_po=final_price_po)
        if line["quantity"] != -1 and line["quantity"] < quantity:
            raise ValueError("Estoque insuficiente")
        state = _character_state(connection, character_id)
        _check_purse(state, expected_purse)
        cost_copper = int(round(final_price_po * quantity * 100))
        purse = purse_copper(state)
        if purse < cost_copper:
            raise ValueError(f"Saldo insuficiente: faltam {(cost_copper - purse) / 100:g} PO")
        purse_after = _save_purse(connection, character_id, purse - cost_copper)
        if line["quantity"] != -1:
            connection.execute("UPDATE merchant_stock SET quantity=quantity-? WHERE id=?", (quantity, stock_id))
        item_path = get_catalog_item(line['compendium_item_id']).get('native_item_path') or f"merchant:{merchant_id}:{line['compendium_item_id']}"
        owned = _inventory_get(connection, character_id, item_path)
        _inventory_upsert(connection, profile_id=character_id, item_path=item_path, item_title=line["name"],
                           quantity=int((owned or {}).get("quantity") or 0) + quantity, equipped=False,
                           notes=f"Comprado de {merchant_id} por {final_price_po:g} PO")
        append_session_ledger_event(connection, source_type="merchant_buy", source_id=f"{merchant_id}:{stock_id}",
                                    event_kind="state", actor_id="master", actor_name="Mestre", actor_role="gm",
                                    character_id=character_id, title=f"{character_id} comprou {quantity}× {line['name']}",
                                    detail={"merchant_id": merchant_id, "item": line["name"], "quantity": quantity,
                                            "price_po": final_price_po, "purse_after": purse_after},
                                    visibility="table", created_at=_now())
    return {"item": line["name"], "quantity": quantity, "paid_po": round(final_price_po * quantity, 2), "purse_after": purse_after}


def sell(database_path: Path, *, merchant_id: str, character_id: str, item_path: str, quantity: int = 1,
         unit_price_po: float, expected_purse: dict[str, Any] | None = None) -> dict[str, Any]:
    if quantity < 1 or unit_price_po < 0:
        raise ValueError("Venda inválida")
    database_path = Path(database_path)
    init_merchants(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        if not connection.execute("SELECT 1 FROM merchants WHERE id=?", (merchant_id,)).fetchone():
            raise ValueError("Mercador não encontrado")
        owned = _inventory_get(connection, character_id, item_path)
        if owned is None or int(owned.get("quantity") or 0) < quantity:
            raise ValueError("Personagem não tem essa quantidade")
        from .inventory_conditions import read_condition
        if read_condition(connection,owned['id']) or (owned.get('charges_max') is not None and owned.get('charges_current') is not None and owned['charges_current']<owned['charges_max']):
            raise ValueError('Objeto usado ou modificado exige avaliação individual no mercado do mapa')
        state = _character_state(connection, character_id)
        _check_purse(state, expected_purse)
        gain_copper = int(round(unit_price_po * quantity * 100))
        purse_after = _save_purse(connection, character_id, purse_copper(state) + gain_copper)
        _inventory_upsert(connection, profile_id=character_id, item_path=item_path, item_title=owned["item_title"],
                           quantity=int(owned["quantity"]) - quantity, equipped=bool(owned.get("equipped")),
                           notes=owned.get("notes"), equipment_slot=owned.get("equipment_slot"),
                           charges_current=owned.get("charges_current"), charges_max=owned.get("charges_max"), recharge=owned.get("recharge"))
        append_session_ledger_event(connection, source_type="merchant_sell", source_id=merchant_id,
                                    event_kind="state", actor_id="master", actor_name="Mestre", actor_role="gm",
                                    character_id=character_id, title=f"{character_id} vendeu {quantity}× {owned['item_title']}",
                                    detail={"merchant_id": merchant_id, "item": owned["item_title"], "quantity": quantity,
                                            "unit_price_po": unit_price_po, "purse_after": purse_after},
                                    visibility="table", created_at=_now())
    return {"item": owned["item_title"], "quantity": quantity, "received_po": round(unit_price_po * quantity, 2), "purse_after": purse_after}
