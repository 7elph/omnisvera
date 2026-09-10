from __future__ import annotations

import json
import re
import secrets
import sqlite3
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

from .access import AccessContext
from .dice_rolls import RollSpec, create_roll_request
from .session_ledger import append_session_ledger_event
from .treasure_tables import EQUIPMENT_TABLE, GEM_TABLE, REWARD_LABELS, TREASURE_TABLES, VALUABLE_TABLE


Rng = Callable[[int, int], int]


class LootNotFoundError(ValueError):
    pass


class LootConflictError(ValueError):
    pass


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path, timeout=30)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def init_loot(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS loot_resolutions (
              resolution_id TEXT PRIMARY KEY,
              request_id TEXT NOT NULL UNIQUE,
              source_key TEXT NOT NULL UNIQUE,
              source_type TEXT NOT NULL CHECK(source_type IN ('token','lair')),
              source_id TEXT NOT NULL,
              source_name TEXT NOT NULL,
              treasure_code TEXT NOT NULL,
              treasure_scope TEXT NOT NULL CHECK(treasure_scope IN ('carried','lair')),
              roll_mode TEXT NOT NULL CHECK(roll_mode IN ('digital','quick')),
              rewards_json TEXT NOT NULL,
              rolls_json TEXT NOT NULL,
              status TEXT NOT NULL DEFAULT 'draft' CHECK(status IN ('draft','revealed','distributed')),
              created_at TEXT NOT NULL,
              revealed_at TEXT,
              distributed_at TEXT,
              reveal_ledger_id INTEGER,
              distribution_ledger_id INTEGER,
              distribution_request_id TEXT UNIQUE,
              allocations_json TEXT
            );
            CREATE INDEX IF NOT EXISTS idx_loot_status ON loot_resolutions(status,created_at);
            """
        )
        columns = {row[1] for row in connection.execute("PRAGMA table_info(loot_resolutions)")}
        if "pending_requests_json" not in columns:
            connection.execute("ALTER TABLE loot_resolutions ADD COLUMN pending_requests_json TEXT NOT NULL DEFAULT '[]'")
        if "finalized_at" not in columns:
            connection.execute("ALTER TABLE loot_resolutions ADD COLUMN finalized_at TEXT")
        if "input_mode" not in columns:
            connection.execute("ALTER TABLE loot_resolutions ADD COLUMN input_mode TEXT NOT NULL DEFAULT ''")


def parse_treasure_code(raw: str) -> list[dict[str, Any]]:
    """Parse OD2 codes such as ``Q (G)``, ``S (B+C)`` and ``Vx3``."""
    normalized = str(raw or "").upper().replace("×", "X")
    parenthetical_spans = [match.span() for match in re.finditer(r"\([^)]*\)", normalized)]
    entries: list[dict[str, Any]] = []
    for match in re.finditer(r"\b([A-V])(?:\s*X\s*(\d{1,2}))?\b", normalized):
        code = match.group(1)
        multiplier = int(match.group(2) or 1)
        table = TREASURE_TABLES[code]
        # In monster stat blocks, parentheses explicitly mark the hoard found
        # in the lair.  Outside them, the A-O/P-V ranges retain their SRD scope.
        inside_parentheses = any(start <= match.start() < end for start, end in parenthetical_spans)
        entries.append({"code": code, "scope": "lair" if inside_parentheses else table["scope"], "multiplier": multiplier})
    return entries


def _roll_formula(formula: str, rng: Rng) -> tuple[int, list[int]]:
    clean = str(formula).replace(" ", "").lower()
    if clean.isdigit():
        return int(clean), []
    match = re.fullmatch(r"(\d+)d(\d+)(?:\*(\d+))?", clean)
    if not match:
        raise ValueError(f"Fórmula de tesouro inválida: {formula}")
    count, sides, multiplier = (int(value or 1) for value in match.groups())
    results = [int(rng(1, sides)) for _ in range(count)]
    return sum(results) * multiplier, results


def _generate_rewards(entries: list[dict[str, Any]], roll_mode: str, rng: Rng) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    rewards: list[dict[str, Any]] = []
    rolls: list[dict[str, Any]] = []
    for entry in entries:
        table = TREASURE_TABLES[entry["code"]]
        for occurrence in range(entry["multiplier"]):
            if roll_mode == "quick":
                quick = str(table["quick"])
                if quick != "-":
                    rewards.append({
                        "id": f"reward:{len(rewards) + 1}", "kind": "quick", "name": f"Tesouro rápido {entry['code']}",
                        "quantity": 1, "description": quick, "source_code": entry["code"], "editable": True,
                    })
                continue
            for spec_index, specification in enumerate(table["rewards"]):
                chance = int(specification.get("chance") or 6)
                chance_result = int(rng(1, 6)) if chance < 6 else None
                if chance_result is not None:
                    rolls.append({"purpose": "existence", "code": entry["code"], "kind": specification["kind"], "formula": "1d6", "results": [chance_result], "total": chance_result, "success": chance_result <= chance})
                if chance_result is not None and chance_result > chance:
                    continue
                quantity, quantity_rolls = _roll_formula(specification["formula"], rng)
                rolls.append({"purpose": "quantity", "code": entry["code"], "kind": specification["kind"], "formula": specification["formula"], "results": quantity_rolls, "total": quantity})
                if quantity <= 0:
                    continue
                kind = str(specification["kind"])
                rewards.append({
                    "id": f"reward:{len(rewards) + 1}", "kind": kind,
                    "name": specification.get("label") or REWARD_LABELS[kind], "quantity": quantity,
                    "description": None, "source_code": entry["code"], "occurrence": occurrence + 1,
                    "editable": True, "requires_identification": kind in {"gem", "valuable", "magic"},
                })
    return rewards, rolls


def _two_d6(rng: Rng) -> tuple[int, list[int]]:
    results = [int(rng(1, 6)), int(rng(1, 6))]
    return sum(results), results


def _expand_digital_rewards(
    rewards: list[dict[str, Any]], rolls: list[dict[str, Any]], rng: Rng,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    expanded: list[dict[str, Any]] = []
    heavy_valuables = {
        "Peles de Animais Raros", "Sacas de Especiaria", "Sacas de Incenso", "Tecidos Nobres",
        "Metros de Fina Seda", "Móveis com Marchetaria", "Tapeçaria Fina", "Escultura",
        "Tela Pintada", "Estatueta em Bronze",
    }
    for reward_item in rewards:
        kind = reward_item["kind"]
        if kind not in {"equipment", "valuable", "gem"}:
            expanded.append(dict(reward_item))
            continue
        for unit in range(int(reward_item["quantity"])):
            if kind == "equipment":
                rarity_roll, rarity_results = _two_d6(rng)
                rarity = "rare" if rarity_roll in {2, 3, 12} else "uncommon" if rarity_roll in {4, 5, 10, 11} else "common"
                item_roll, item_results = _two_d6(rng)
                name = EQUIPMENT_TABLE[item_roll][rarity]
                rolls.extend([
                    {"purpose": "equipment_rarity", "formula": "2d6", "results": rarity_results, "total": rarity_roll, "result": rarity},
                    {"purpose": "equipment_item", "formula": "2d6", "results": item_results, "total": item_roll, "result": name},
                ])
                expanded.append({**reward_item, "id": f"expanded:{len(expanded) + 1}", "name": name, "quantity": 1, "requires_identification": False})
            elif kind == "valuable":
                type_roll, type_results = _two_d6(rng)
                valuable_type = "art" if type_roll <= 3 else "utensils" if type_roll <= 5 else "merchandise" if type_roll <= 9 else "dishes" if type_roll <= 11 else "jewelry"
                item_roll, item_results = _two_d6(rng)
                name = VALUABLE_TABLE[valuable_type][item_roll]
                value_roll, value_results = _two_d6(rng)
                value = value_roll * 100
                rolls.extend([
                    {"purpose": "valuable_type", "formula": "2d6", "results": type_results, "total": type_roll, "result": valuable_type},
                    {"purpose": "valuable_item", "formula": "2d6", "results": item_results, "total": item_roll, "result": name},
                    {"purpose": "valuable_value", "formula": "2d6*100", "results": value_results, "total": value, "hidden": True},
                ])
                expanded.append({
                    **reward_item, "id": f"expanded:{len(expanded) + 1}", "name": name, "quantity": 1,
                    "gm_notes": f"Valor de avaliação: {value} PO" + (" · acrescenta 1 à carga" if name in heavy_valuables else ""),
                    "requires_identification": True,
                })
            else:
                category_roll, category_results = _two_d6(rng)
                name, base_value = GEM_TABLE[category_roll]
                raw_roll = int(rng(1, 6))
                damaged_roll = int(rng(1, 6))
                raw = raw_roll <= 2
                damaged = damaged_roll == 1
                value = base_value * (0.75 if raw else 1) * (0.5 if damaged else 1)
                value = int(value) if float(value).is_integer() else value
                condition = ", ".join(label for enabled, label in ((raw, "bruta"), (damaged, "danificada")) if enabled) or "lapidada e íntegra"
                rolls.extend([
                    {"purpose": "gem_category", "formula": "2d6", "results": category_results, "total": category_roll, "result": name},
                    {"purpose": "gem_raw", "formula": "1d6", "results": [raw_roll], "total": raw_roll, "success": raw},
                    {"purpose": "gem_damaged", "formula": "1d6", "results": [damaged_roll], "total": damaged_roll, "success": damaged},
                ])
                expanded.append({
                    **reward_item, "id": f"expanded:{len(expanded) + 1}", "name": name, "quantity": 1,
                    "gm_notes": f"{condition.capitalize()} · valor de avaliação: {value} PO", "requires_identification": True,
                })
    return expanded, rolls


def _formula_parts(formula: str) -> tuple[str | None, int, int | None]:
    clean = str(formula).replace(" ", "").lower()
    if clean.isdigit():
        return None, 1, int(clean)
    match = re.fullmatch(r"(\d+d\d+)(?:\*(\d+))?", clean)
    if not match:
        raise ValueError(f"Fórmula de tesouro inválida: {formula}")
    return match.group(1), int(match.group(2) or 1), None


def _requested_plan(entries: list[dict[str, Any]]) -> list[dict[str, Any]]:
    plan: list[dict[str, Any]] = []
    for entry in entries:
        table = TREASURE_TABLES[entry["code"]]
        for occurrence in range(entry["multiplier"]):
            for spec_index, specification in enumerate(table["rewards"]):
                chance = int(specification.get("chance") or 6)
                formula, multiplier, constant = _formula_parts(specification["formula"])
                base = {
                    "code": entry["code"], "occurrence": occurrence + 1,
                    "kind": specification["kind"], "label": specification.get("label"), "spec_index": spec_index,
                    "chance_threshold": chance, "quantity_formula": specification["formula"],
                    "quantity_multiplier": multiplier, "constant_quantity": constant,
                }
                if chance < 6:
                    plan.append({**base, "task_id": f"task:{len(plan) + 1}", "purpose": "existence", "formula": "1d6"})
                if formula:
                    plan.append({**base, "task_id": f"task:{len(plan) + 1}", "purpose": "quantity", "formula": formula})
    return plan


def resolve_requested_token_loot(
    database_path: Path, *, request_id: str, token_id: str, scope: str,
    roller_character_id: str, lair_id: str | None = None,
) -> tuple[dict[str, Any], bool]:
    if scope not in {"carried", "lair"}:
        raise ValueError("Escopo de tesouro inválido")
    request_id = str(request_id or "").strip()
    if not 8 <= len(request_id) <= 120 or not re.fullmatch(r"[A-Za-z0-9._:-]+", request_id):
        raise ValueError("request_id inválido")
    init_loot(database_path)
    with closing(_connect(database_path)) as connection:
        existing = connection.execute("SELECT * FROM loot_resolutions WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing), False
        token = connection.execute("SELECT id,name,current_hp,sheet_json FROM session_workspace_tokens WHERE id=? AND token_type='monster'", (token_id,)).fetchone()
        if token is None:
            raise LootNotFoundError("Monstro ou NPC do mapa não encontrado")
        if token["current_hp"] is None or int(token["current_hp"]) > 0:
            raise LootConflictError("Confirme a derrota reduzindo os PV do token a zero antes de gerar o espólio")
        if connection.execute("SELECT 1 FROM character_states WHERE profile_id=?", (roller_character_id,)).fetchone() is None:
            raise ValueError("Personagem responsável pelas rolagens inválido")
        sheet = json.loads(token["sheet_json"] or "{}")
        raw_code = str(sheet.get("treasure") or "").strip()
        entries = [entry for entry in parse_treasure_code(raw_code) if entry["scope"] == scope]
        if not entries:
            raise LootConflictError("Este token não possui tesouro deste tipo")
        if scope == "lair" and not str(lair_id or "").strip():
            raise ValueError("Informe um identificador do covil")
        source_id = str(lair_id).strip() if scope == "lair" else str(token["id"])
        source_key = f"{scope}:{source_id}"
        duplicate = connection.execute("SELECT * FROM loot_resolutions WHERE source_key=?", (source_key,)).fetchone()
        if duplicate:
            return _record(duplicate), False
        source_name = str(token["name"])
    resolution_id = f"loot:{secrets.token_hex(16)}"
    plan = _requested_plan(entries)
    pending: list[dict[str, Any]] = []
    for index, task in enumerate(plan):
        roll_request, _created = create_roll_request(
            database_path,
            request_id=f"{resolution_id}:roll:{index + 1}", campaign_id="omnisvera",
            character_id=roller_character_id, requested_by="master",
            spec=RollSpec(
                "free", f"Tesouro de {source_name} · {task['code']} · {task['purpose']}",
                task["formula"], "loot", resolution_id,
            ),
            visibility="owner", reason="Rolagem solicitada para gerar o espólio", expires_in_hours=24,
        )
        pending.append({**task, "roll_request_id": roll_request["id"], "roller_character_id": roller_character_id})
    now = _now()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        duplicate = connection.execute("SELECT * FROM loot_resolutions WHERE source_key=? OR request_id=?", (source_key, request_id)).fetchone()
        if duplicate:
            return _record(duplicate), False
        connection.execute(
            """INSERT INTO loot_resolutions(
              resolution_id,request_id,source_key,source_type,source_id,source_name,treasure_code,
              treasure_scope,roll_mode,rewards_json,rolls_json,status,created_at,pending_requests_json,input_mode
            ) VALUES(?,?,?,?,?,?,?,?,?,'[]','[]','draft',?,?,?)""",
            (resolution_id, request_id, source_key, "lair" if scope == "lair" else "token", source_id,
             source_name, raw_code, scope, "digital", now, json.dumps(pending, ensure_ascii=False), "requested"),
        )
        row = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(row), True


def finalize_requested_loot(database_path: Path, resolution_id: str) -> tuple[dict[str, Any], bool]:
    init_loot(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
        if row is None:
            raise LootNotFoundError("Espólio não encontrado")
        item = _record(row)
        if item["roll_mode"] != "requested":
            raise LootConflictError("Este espólio não usa rolagens solicitadas")
        if item.get("finalized_at"):
            return item, False
        tasks = item["pending_requests"]
        request_rows: dict[int, sqlite3.Row] = {}
        for task in tasks:
            request_row = connection.execute(
                """SELECT r.*,e.total,e.individual_results_json FROM dice_roll_requests r
                   LEFT JOIN dice_roll_events e ON e.id=r.roll_event_id WHERE r.id=?""",
                (int(task["roll_request_id"]),),
            ).fetchone()
            if request_row is None or request_row["status"] != "completed" or request_row["total"] is None:
                raise LootConflictError("Ainda existem rolagens de tesouro pendentes para o jogador")
            request_rows[int(task["roll_request_id"])] = request_row
        rolls: list[dict[str, Any]] = []
        values: dict[tuple[str, int, int, str], int] = {}
        for task in tasks:
            request_row = request_rows[int(task["roll_request_id"])]
            total = int(request_row["total"])
            key = (task["code"], int(task["occurrence"]), int(task["spec_index"]), task["purpose"])
            values[key] = total
            rolls.append({
                "purpose": task["purpose"], "code": task["code"], "kind": task["kind"],
                "formula": task["formula"], "results": json.loads(request_row["individual_results_json"] or "[]"),
                "total": total, "roll_request_id": task["roll_request_id"],
                "success": total <= int(task["chance_threshold"]) if task["purpose"] == "existence" else None,
            })
        rewards: list[dict[str, Any]] = []
        grouped: dict[tuple[str, int, int, str, str | None, str, int, int | None], dict[str, Any]] = {}
        for task in tasks:
            group_key = (
                task["code"], int(task["occurrence"]), int(task["spec_index"]), task["kind"], task.get("label"),
                task["quantity_formula"], int(task["quantity_multiplier"]), task.get("constant_quantity"),
            )
            grouped[group_key] = task
        for (code, occurrence, spec_index, kind, label, _formula, multiplier, constant), task in grouped.items():
            chance_key = (code, occurrence, spec_index, "existence")
            if int(task["chance_threshold"]) < 6 and values.get(chance_key, 7) > int(task["chance_threshold"]):
                continue
            quantity = int(constant) if constant is not None else values[(code, occurrence, spec_index, "quantity")] * multiplier
            rewards.append({
                "id": f"reward:{len(rewards) + 1}", "kind": kind, "name": label or REWARD_LABELS[kind],
                "quantity": quantity, "description": None, "source_code": code, "occurrence": occurrence,
                "editable": True, "requires_identification": kind in {"gem", "valuable", "magic"},
            })
        now = _now()
        connection.execute(
            "UPDATE loot_resolutions SET rewards_json=?,rolls_json=?,finalized_at=? WHERE resolution_id=?",
            (json.dumps(rewards, ensure_ascii=False), json.dumps(rolls, ensure_ascii=False), now, resolution_id),
        )
        updated = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(updated), True


def _record(row: sqlite3.Row) -> dict[str, Any]:
    item = dict(row)
    item["rewards"] = json.loads(item.pop("rewards_json") or "[]")
    item["rolls"] = json.loads(item.pop("rolls_json") or "[]")
    item["allocations"] = json.loads(item.pop("allocations_json") or "[]")
    item["pending_requests"] = json.loads(item.pop("pending_requests_json") or "[]")
    if item.pop("input_mode", "") == "requested":
        item["roll_mode"] = "requested"
    return item


def resolve_token_loot(
    database_path: Path, *, request_id: str, token_id: str, scope: str, roll_mode: str,
    lair_id: str | None = None, rng: Rng | None = None,
) -> tuple[dict[str, Any], bool]:
    if scope not in {"carried", "lair"}:
        raise ValueError("Escopo de tesouro inválido")
    if roll_mode not in {"digital", "quick"}:
        raise ValueError("Modo de geração inválido")
    request_id = str(request_id or "").strip()
    if not 8 <= len(request_id) <= 120 or not re.fullmatch(r"[A-Za-z0-9._:-]+", request_id):
        raise ValueError("request_id inválido")
    init_loot(database_path)
    generator = rng or secrets.SystemRandom().randint
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        existing = connection.execute("SELECT * FROM loot_resolutions WHERE request_id=?", (request_id,)).fetchone()
        if existing:
            return _record(existing), False
        token = connection.execute("SELECT id,name,current_hp,sheet_json FROM session_workspace_tokens WHERE id=? AND token_type='monster'", (token_id,)).fetchone()
        if token is None:
            raise LootNotFoundError("Monstro ou NPC do mapa não encontrado")
        if token["current_hp"] is None or int(token["current_hp"]) > 0:
            raise LootConflictError("Confirme a derrota reduzindo os PV do token a zero antes de gerar o espólio")
        sheet = json.loads(token["sheet_json"] or "{}")
        raw_code = str(sheet.get("treasure") or "").strip()
        entries = [entry for entry in parse_treasure_code(raw_code) if entry["scope"] == scope]
        if not entries:
            raise LootConflictError("Este token não possui tesouro deste tipo")
        if scope == "lair" and not str(lair_id or "").strip():
            raise ValueError("Informe um identificador do covil")
        source_id = str(lair_id).strip() if scope == "lair" else str(token["id"])
        source_key = f"{scope}:{source_id}"
        duplicate = connection.execute("SELECT * FROM loot_resolutions WHERE source_key=?", (source_key,)).fetchone()
        if duplicate:
            return _record(duplicate), False
        rewards, rolls = _generate_rewards(entries, roll_mode, generator)
        if roll_mode == "digital":
            rewards, rolls = _expand_digital_rewards(rewards, rolls, generator)
        resolution_id = f"loot:{secrets.token_hex(16)}"
        now = _now()
        connection.execute(
            """INSERT INTO loot_resolutions(
              resolution_id,request_id,source_key,source_type,source_id,source_name,treasure_code,
              treasure_scope,roll_mode,rewards_json,rolls_json,status,created_at
            ) VALUES(?,?,?,?,?,?,?,?,?,?,?,'draft',?)""",
            (resolution_id, request_id, source_key, "lair" if scope == "lair" else "token", source_id,
             str(token["name"]), raw_code, scope, roll_mode, json.dumps(rewards, ensure_ascii=False),
             json.dumps(rolls, ensure_ascii=False), now),
        )
        row = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(row), True


def list_loot(database_path: Path, access: AccessContext) -> list[dict[str, Any]]:
    init_loot(database_path)
    where = "" if access.mode == "gm" else "WHERE status IN ('revealed','distributed')"
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(f"SELECT * FROM loot_resolutions {where} ORDER BY created_at,resolution_id").fetchall()
    records = [_record(row) for row in rows]
    if access.mode != "gm":
        for record in records:
            # Players receive the theatrical result, not the private audit
            # trail used by the Master to inspect table/chance rolls.
            record["rolls"] = []
            record["rewards"] = [
                {key: value for key, value in reward_item.items() if key != "gm_notes"}
                for reward_item in record["rewards"]
            ]
    return records


def update_loot_rewards(database_path: Path, resolution_id: str, rewards: list[dict[str, Any]]) -> dict[str, Any]:
    init_loot(database_path)
    cleaned = []
    for index, reward_item in enumerate(rewards):
        name = str(reward_item.get("name") or "").strip()
        quantity = int(reward_item.get("quantity") or 0)
        if not name or quantity < 1 or quantity > 999999:
            raise ValueError("Nome ou quantidade de recompensa inválida")
        cleaned.append({**reward_item, "id": str(reward_item.get("id") or f"reward:{index + 1}"), "name": name, "quantity": quantity})
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT status,input_mode,finalized_at FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
        if row is None:
            raise LootNotFoundError("Espólio não encontrado")
        if row["status"] != "draft":
            raise LootConflictError("Somente um rascunho pode ser editado")
        if row["input_mode"] == "requested" and not row["finalized_at"]:
            raise LootConflictError("Conclua as rolagens solicitadas antes de editar o espólio")
        connection.execute("UPDATE loot_resolutions SET rewards_json=? WHERE resolution_id=?", (json.dumps(cleaned, ensure_ascii=False), resolution_id))
        updated = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(updated)


def reveal_loot(database_path: Path, resolution_id: str) -> tuple[dict[str, Any], bool]:
    init_loot(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        row = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
        if row is None:
            raise LootNotFoundError("Espólio não encontrado")
        item = _record(row)
        if item["status"] in {"revealed", "distributed"}:
            return item, False
        if item["roll_mode"] == "requested" and not item.get("finalized_at"):
            raise LootConflictError("Conclua as rolagens solicitadas antes de revelar o espólio")
        now = _now()
        summary = ", ".join(f"{reward['quantity']}× {reward['name']}" for reward in item["rewards"]) or "Nenhum tesouro encontrado"
        public_rewards = [
            {key: value for key, value in reward_item.items() if key != "gm_notes"}
            for reward_item in item["rewards"]
        ]
        ledger_id = append_session_ledger_event(
            connection, source_type="loot_reveal", source_id=resolution_id, event_kind="treasure",
            actor_id="master", actor_name="Mestre", actor_role="gm", character_id=None,
            title=f"Espólio de {item['source_name']}: {summary}",
            detail={"loot_resolution_id": resolution_id, "source_name": item["source_name"], "rewards": public_rewards},
            visibility="table", created_at=now,
        )
        connection.execute("UPDATE loot_resolutions SET status='revealed',revealed_at=?,reveal_ledger_id=? WHERE resolution_id=?", (now, ledger_id, resolution_id))
        updated = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(updated), True


def distribute_loot(
    database_path: Path, *, resolution_id: str, request_id: str, allocations: list[dict[str, Any]],
) -> tuple[dict[str, Any], bool]:
    request_id = str(request_id or "").strip()
    if not 8 <= len(request_id) <= 120:
        raise ValueError("request_id inválido")
    init_loot(database_path)
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        repeated = connection.execute("SELECT * FROM loot_resolutions WHERE distribution_request_id=?", (request_id,)).fetchone()
        if repeated:
            return _record(repeated), False
        row = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
        if row is None:
            raise LootNotFoundError("Espólio não encontrado")
        item = _record(row)
        if item["status"] == "distributed":
            return item, False
        if item["status"] != "revealed":
            raise LootConflictError("Revele o espólio antes de distribuí-lo")
        reward_by_id = {reward["id"]: reward for reward in item["rewards"]}
        totals: dict[str, int] = {}
        for allocation in allocations:
            reward_id = str(allocation.get("reward_id") or "")
            character_id = str(allocation.get("character_id") or "")
            quantity = int(allocation.get("quantity") or 0)
            if reward_id not in reward_by_id or quantity < 1:
                raise ValueError("Distribuição inválida")
            if connection.execute("SELECT 1 FROM character_states WHERE profile_id=?", (character_id,)).fetchone() is None:
                raise ValueError("Personagem de destino inválido")
            totals[reward_id] = totals.get(reward_id, 0) + quantity
        if any(totals.get(reward_id, 0) != int(reward["quantity"]) for reward_id, reward in reward_by_id.items()):
            raise ValueError("Distribua integralmente cada recompensa antes de confirmar")
        now = _now()
        created_items: dict[str, int] = {}
        for allocation in allocations:
            reward = reward_by_id[str(allocation["reward_id"])]
            reward_id = str(reward["id"])
            if reward_id not in created_items:
                cursor = connection.execute(
                    """INSERT INTO session_custom_items(name,item_type,description,effects_json,effect_rules_json,mechanics_json,usable,image_path,created_at,updated_at)
                       VALUES(?,?,?,'[]','[]','{}',0,NULL,?,?)""",
                    (reward["name"], reward.get("kind") or "loot", reward.get("description"), now, now),
                )
                created_items[reward_id] = int(cursor.lastrowid)
            item_id = created_items[reward_id]
            item_path = f"session-item:{item_id}"
            character_id = str(allocation["character_id"])
            quantity = int(allocation["quantity"])
            existing = connection.execute("SELECT quantity FROM player_inventory WHERE profile_id=? AND item_path=?", (character_id, item_path)).fetchone()
            next_quantity = int(existing["quantity"] if existing else 0) + quantity
            connection.execute(
                """INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,updated_at)
                   VALUES(?,?,?,?,0,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET quantity=excluded.quantity,item_title=excluded.item_title,updated_at=excluded.updated_at""",
                (character_id, item_path, reward["name"], next_quantity, f"Espólio de {item['source_name']}", now),
            )
        detail = {"loot_resolution_id": resolution_id, "source_name": item["source_name"], "allocations": allocations, "created_item_ids": created_items}
        ledger_id = append_session_ledger_event(
            connection, source_type="loot_distribution", source_id=resolution_id, event_kind="treasure",
            actor_id="master", actor_name="Mestre", actor_role="gm", character_id=None,
            title=f"Espólio de {item['source_name']} distribuído", detail=detail, visibility="table", created_at=now,
        )
        connection.execute(
            """UPDATE loot_resolutions SET status='distributed',distributed_at=?,distribution_ledger_id=?,
               distribution_request_id=?,allocations_json=? WHERE resolution_id=?""",
            (now, ledger_id, request_id, json.dumps(allocations, ensure_ascii=False), resolution_id),
        )
        updated = connection.execute("SELECT * FROM loot_resolutions WHERE resolution_id=?", (resolution_id,)).fetchone()
    return _record(updated), True
