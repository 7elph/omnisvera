from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Literal

from .access import sanitize_player_text


AccessLevel = Literal["gm", "owner", "public"]

SESSION_ABILITY_CATALOG_PATH = Path(__file__).with_name("data") / "session_abilities.json"


def load_session_abilities(profile_id: str) -> list[dict[str, Any]]:
    """Load player-safe abilities without embedding character-specific data in the UI."""
    try:
        payload = json.loads(SESSION_ABILITY_CATALOG_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return []

    raw_entries = (payload.get("characters") or {}).get(profile_id, [])
    if not isinstance(raw_entries, list):
        return []

    entries: list[dict[str, Any]] = []
    for raw_entry in raw_entries:
        if not isinstance(raw_entry, dict):
            continue
        name = str(raw_entry.get("name") or "").strip()
        if not name:
            continue
        entry = {
            "id": str(raw_entry.get("id") or name).strip(),
            "name": name,
            "kind": str(raw_entry.get("kind") or "ability").strip(),
            "group": str(raw_entry.get("group") or "Habilidades").strip(),
            "description": str(raw_entry.get("description") or "").strip(),
            "mechanics_status": (
                "structured" if raw_entry.get("mechanics_status") == "structured" else "partial"
            ),
            "source": str(raw_entry.get("source") or "").strip(),
        }
        circle = raw_entry.get("circle")
        if isinstance(circle, int) and circle > 0:
            entry["circle"] = circle
        uses = raw_entry.get("uses")
        if isinstance(uses, dict):
            maximum = _number(uses.get("maximum"))
            if maximum is not None and maximum > 0:
                entry["uses"] = {
                    "resource_key": _resource_key(str(uses.get("resource_key") or raw_entry.get("id") or name)),
                    "label": str(uses.get("label") or f"{name} · usos").strip(),
                    "maximum": int(maximum),
                    "recharge": str(uses.get("recharge") or "inn_rest").strip(),
                }
        entries.append(entry)
    return entries

STATE_ACTIONS = {
    "damage",
    "heal",
    "set_hp",
    "add_condition",
    "remove_condition",
    "consume_resource",
    "restore_resource",
    "equip_item",
    "unequip_item",
    "change_quantity",
    "grant_item",
    "remove_item",
    "set_location",
    "set_session_notes",
    "rest_at_inn",
}

OWNER_ACTIONS = {
    "damage",
    "heal",
    "set_hp",
    "add_condition",
    "remove_condition",
    "consume_resource",
    "equip_item",
    "unequip_item",
    "change_quantity",
}

DEFINITION_FIELDS = {
    "epithet",
    "player_name",
    "campaign",
    "race",
    "class_name",
    "level",
    "attributes",
    "maximum_hp",
    "armor_class",
    "initiative",
    "movement",
    "location",
    "current_status",
    "gm_fields",
}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")
    return connection


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def init_character_play(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.executescript(
            """
            CREATE TABLE IF NOT EXISTS character_states (
                profile_id TEXT PRIMARY KEY,
                state_json TEXT NOT NULL,
                version INTEGER NOT NULL DEFAULT 1,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS character_definition_overrides (
                profile_id TEXT PRIMARY KEY,
                data_json TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS character_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                character_id TEXT NOT NULL,
                session_id TEXT,
                actor_id TEXT NOT NULL,
                actor_role TEXT NOT NULL,
                event_type TEXT NOT NULL,
                field TEXT NOT NULL,
                before_json TEXT,
                after_json TEXT,
                reason TEXT,
                created_at TEXT NOT NULL,
                reverted_at TEXT,
                reverted_by TEXT
            );

            CREATE INDEX IF NOT EXISTS idx_character_events_character
              ON character_events(character_id, id DESC);
            """
        )


def _normalize(value: Any) -> str:
    return "".join(
        char
        for char in unicodedata.normalize("NFKD", str(value or "").strip().lower())
        if not unicodedata.combining(char)
    )


def _number(value: Any) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value or ""))
    if not match:
        return None
    parsed = float(match.group(0).replace(",", "."))
    return int(parsed) if parsed.is_integer() else parsed


def attribute_modifier(value: Any) -> int | None:
    """Old Dragon modifier table already used by the character creation flow."""
    score = _number(value)
    if score is None:
        return None
    score = int(score)
    if score <= 1:
        return -5
    if score <= 3:
        return -4
    if score <= 5:
        return -3
    if score <= 7:
        return -2
    if score <= 9:
        return -1
    if score <= 11:
        return 0
    if score <= 13:
        return 1
    if score <= 15:
        return 2
    if score <= 17:
        return 3
    if score <= 19:
        return 4
    return 5


def _step_fields(sheet: dict[str, Any], key: str) -> dict[str, Any]:
    for step in sheet.get("steps") or []:
        if step.get("key") == key:
            return dict(step.get("fields") or {})
    return {}


def _step_guide(sheet: dict[str, Any], key: str) -> dict[str, Any]:
    for step in sheet.get("steps") or []:
        if step.get("key") == key:
            return dict(step.get("guide") or {})
    return {}


def _clean_link(value: Any) -> str | None:
    text = str(value or "").strip()
    if not text:
        return None
    text = re.sub(r'^\[\[|\]\]$', "", text)
    if "|" in text:
        text = text.split("|", 1)[1]
    return text.strip() or None


def _clean_text(value: Any, limit: int = 5000) -> str:
    text = sanitize_player_text(str(value or ""))
    text = re.sub(r"```(?:dataview|datacards|leaflet)[\s\S]*?```", "", text, flags=re.IGNORECASE)
    text = re.sub(r"!\[\[[^\]]+\]\]", "", text)
    text = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", text)
    text = re.sub(r"\[\[([^\]]+)\]\]", r"\1", text)
    text = re.sub(r"^>\s*\[![^\]]+\].*$", "", text, flags=re.MULTILINE)
    text = re.sub(r"\n{3,}", "\n\n", text).strip()
    return text[:limit].strip()


def _section(content: str, *headings: str, limit: int = 5000) -> str:
    for heading in headings:
        match = re.search(
            rf"^(#{{2,4}})\s+{re.escape(heading)}\s*$",
            content,
            flags=re.IGNORECASE | re.MULTILINE,
        )
        if not match:
            continue
        level = len(match.group(1))
        end = len(content)
        for candidate in re.finditer(r"^(#{2,4})\s+.+$", content[match.end():], flags=re.MULTILINE):
            if len(candidate.group(1)) <= level:
                end = match.end() + candidate.start()
                break
        return _clean_text(content[match.end():end], limit)
    return ""


def _split_title(note: dict[str, Any], frontmatter: dict[str, Any]) -> tuple[str, str | None]:
    title = str(frontmatter.get("name") or note.get("title") or "Personagem").strip()
    epithet = str(frontmatter.get("epithet") or "").strip() or None
    if not frontmatter.get("name") and " — " in title:
        name, inferred = title.split(" — ", 1)
        title = name.strip().title()
        inferred = inferred.strip().title()
        for particle in (" Da ", " Das ", " De ", " Do ", " Dos ", " E "):
            inferred = inferred.replace(particle, particle.lower())
        epithet = epithet or inferred
    return title, epithet


def _parse_equipment_names(value: Any) -> list[str]:
    text = str(value or "")
    entries = [entry.strip(" -\t") for entry in re.split(r"[,;\n]+", text)]
    return list(dict.fromkeys(entry for entry in entries if entry and len(entry) <= 120))


def _resource_key(label: str) -> str:
    key = re.sub(r"[^a-z0-9]+", "_", _normalize(label)).strip("_")
    return key or "recurso"


def seed_resources(sheet: dict[str, Any]) -> list[dict[str, Any]]:
    resources: dict[str, dict[str, Any]] = {}
    class_guide = _step_guide(sheet, "character_class")
    for source in class_guide.get("sources") or []:
        if source.get("kind") != "class":
            continue
        progression = source.get("level_one") or {}
        for label, raw_value in progression.items():
            normalized = _normalize(label)
            if normalized in {"nivel", "xp", "dv", "dv/pv", "ba", "jp", "marco"}:
                continue
            if not (
                "reserva de sangue" in normalized
                or "pontos alquimicos" in normalized
                or re.fullmatch(r"[1-9][oaºª]?", normalized)
            ):
                continue
            maximum = _number(raw_value)
            if maximum is None or maximum <= 0:
                continue
            display = f"Magias de {normalized[0]}º círculo" if re.fullmatch(r"[1-9][oaºª]?", normalized) else label
            key = _resource_key(display)
            resources[key] = {
                "key": key,
                "label": display,
                "current": int(maximum),
                "maximum": int(maximum),
            }

    class_fields = _step_fields(sheet, "character_class")
    searchable = "\n".join(
        str(value or "")
        for value in (
            class_fields.get("class_abilities"),
            _step_fields(sheet, "magic").get("known_magic"),
        )
    )
    for pattern, label in (
        (r"Reserva de Sangue(?: inicial)?\s*:\s*(\d+)", "Reserva de Sangue"),
        (r"Pontos Alquímicos(?: iniciais)?\s*:\s*(\d+)", "Pontos Alquímicos"),
    ):
        match = re.search(pattern, searchable, flags=re.IGNORECASE)
        if match:
            maximum = int(match.group(1))
            key = _resource_key(label)
            resources[key] = {"key": key, "label": label, "current": maximum, "maximum": maximum}
    return list(resources.values())


def seed_session_ability_resources(profile_id: str) -> list[dict[str, Any]]:
    resources: list[dict[str, Any]] = []
    for ability in load_session_abilities(profile_id):
        uses = ability.get("uses")
        if not isinstance(uses, dict):
            continue
        maximum = int(uses.get("maximum") or 0)
        if maximum <= 0:
            continue
        key = _resource_key(str(uses.get("resource_key") or ability["id"]))
        resources.append({
            "key": key,
            "label": str(uses.get("label") or f"{ability['name']} · usos"),
            "current": maximum,
            "maximum": maximum,
            "recharge": str(uses.get("recharge") or "inn_rest"),
        })
    return resources


def seed_all_resources(profile_id: str, sheet: dict[str, Any]) -> list[dict[str, Any]]:
    resources = {resource["key"]: resource for resource in seed_resources(sheet)}
    for resource in seed_session_ability_resources(profile_id):
        resources[resource["key"]] = resource
    return list(resources.values())


def load_definition_overrides(database_path: Path, profile_id: str) -> dict[str, Any]:
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection:
        row = connection.execute(
            "SELECT data_json FROM character_definition_overrides WHERE profile_id = ?",
            (profile_id,),
        ).fetchone()
    return json.loads(row["data_json"]) if row else {}


def build_character_definition(
    *,
    profile_id: str,
    note: dict[str, Any],
    sheet: dict[str, Any],
    inventory: list[dict[str, Any]],
    overrides: dict[str, Any] | None = None,
    access_level: AccessLevel = "owner",
) -> dict[str, Any]:
    overrides = dict(overrides or {})
    frontmatter = dict(note.get("frontmatter") or {})
    name, epithet = _split_title(note, frontmatter)
    attributes = dict(_step_fields(sheet, "attributes"))
    attributes.update(overrides.get("attributes") or {})
    class_fields = _step_fields(sheet, "character_class")
    race_fields = _step_fields(sheet, "race")
    attacks = _step_fields(sheet, "attacks")
    armor = _step_fields(sheet, "armor")
    magic = _step_fields(sheet, "magic")
    details = _step_fields(sheet, "details")
    content = str(note.get("content") or "")

    race = overrides.get("race") or race_fields.get("race") or frontmatter.get("race")
    class_name = overrides.get("class_name") or class_fields.get("class_name") or frontmatter.get("class")
    level = int(_number(overrides.get("level") or class_fields.get("level") or frontmatter.get("level")) or 1)
    maximum_hp = _number(overrides.get("maximum_hp") if "maximum_hp" in overrides else class_fields.get("hit_points"))
    armor_class = _number(overrides.get("armor_class") if "armor_class" in overrides else armor.get("armor_class"))
    initiative = _number(overrides.get("initiative"))
    movement = overrides.get("movement") or race_fields.get("movement")
    location = overrides.get("location") or _clean_link(frontmatter.get("location"))
    current_status = overrides.get("current_status") or frontmatter.get("status") or frontmatter.get("campaign_status")

    attack_entries: list[dict[str, Any]] = []
    if attacks.get("melee_bonus") is not None:
        attack_entries.append(
            {
                "id": "melee",
                "name": "Corpo a corpo",
                "attack_bonus": _number(attacks.get("melee_bonus")),
                "damage": None,
                "range": None,
                "notes": "Dano não configurado nas fontes da ficha.",
            }
        )
    if attacks.get("ranged_bonus") is not None:
        attack_entries.append(
            {
                "id": "ranged",
                "name": "À distância",
                "attack_bonus": _number(attacks.get("ranged_bonus")),
                "damage": None,
                "range": None,
                "notes": "Dano e alcance não configurados nas fontes da ficha.",
            }
        )

    inventory_names = [str(item.get("item_title") or "").strip() for item in inventory]
    base_equipment = list(
        dict.fromkeys(
            [name for name in inventory_names if name]
            + _parse_equipment_names(_step_fields(sheet, "equipment").get("equipment_list"))
        )
    )
    public_description = (
        _section(content, "O que os jogadores sabem", "Visão Geral", limit=1800)
        or _clean_text(details.get("background"), 1800)
    )

    result: dict[str, Any] = {
        "id": profile_id,
        "slug": profile_id,
        "name": name,
        "portrait": frontmatter.get("thumbnail") or frontmatter.get("portrait") or frontmatter.get("cover"),
        "cover": frontmatter.get("cover"),
        "epithet": overrides.get("epithet") or epithet,
        "race": race,
        "class_name": class_name,
        "level": level,
        "player_name": overrides.get("player_name"),
        "campaign": overrides.get("campaign") or "Omnisvera",
        "attributes": attributes,
        "attribute_modifiers": {key: attribute_modifier(value) for key, value in attributes.items()},
        "abilities": {
            "racial": _clean_text(race_fields.get("racial_abilities"), 5000),
            "class": _clean_text(class_fields.get("class_abilities"), 5000),
            "magic": _clean_text(magic.get("known_magic"), 4000),
            "magic_notes": _clean_text(magic.get("magic_notes"), 1800),
        },
        "session_abilities": load_session_abilities(profile_id),
        "attacks": attack_entries,
        "attack_notes": _clean_text(attacks.get("attack_notes"), 1800),
        "defenses": {
            "armor_class": int(armor_class) if armor_class is not None and armor_class > 0 else None,
            "saving_throw": class_fields.get("saving_throw"),
            "initiative": int(initiative) if initiative is not None else None,
            "initiative_configured": initiative is not None,
        },
        "progression": {
            "experience": _number(class_fields.get("experience")),
            "base_attack": _number(class_fields.get("base_attack")),
            "maximum_hp": int(maximum_hp) if maximum_hp is not None and maximum_hp > 0 else None,
        },
        "movement": movement,
        "base_equipment": base_equipment,
        "public_description": public_description,
        "history": _clean_text(details.get("background"), 5000),
        "relationships": _section(content, "Relações", limit=3200),
        "physical_description": _clean_text(details.get("physical_description"), 2600),
        "personality": _clean_text(details.get("personality"), 2600),
        "goals": _clean_text(details.get("goals"), 2600),
        "location": location,
        "current_status": current_status,
        "canonical_state": frontmatter.get("canon_status") or frontmatter.get("campaign_status"),
        "source_vault": note.get("path") if access_level == "gm" else None,
        "definition_updated_at": note.get("updated_at"),
        "gm_fields": dict(overrides.get("gm_fields") or {}) if access_level == "gm" else None,
    }
    if access_level == "public":
        return {
            key: result[key]
            for key in (
                "id",
                "slug",
                "name",
                "portrait",
                "cover",
                "epithet",
                "race",
                "class_name",
                "level",
                "campaign",
                "public_description",
                "location",
                "current_status",
            )
        }
    return result


def _initial_state(profile_id: str, sheet: dict[str, Any], definition: dict[str, Any]) -> dict[str, Any]:
    maximum_hp = definition.get("progression", {}).get("maximum_hp")
    equipment = _step_fields(sheet, "equipment")
    return {
        "current_hp": maximum_hp,
        "maximum_hp": maximum_hp,
        "temporary_hp": 0,
        "conditions": [],
        "resources": seed_all_resources(profile_id, sheet),
        "coins": _number(equipment.get("starting_gold")),
        "location": definition.get("location"),
        "session_notes": "",
    }


def get_or_create_state(
    database_path: Path,
    *,
    profile_id: str,
    sheet: dict[str, Any],
    definition: dict[str, Any],
) -> dict[str, Any]:
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute(
            "SELECT * FROM character_states WHERE profile_id = ?", (profile_id,)
        ).fetchone()
        if row is None:
            now = _now()
            state = _initial_state(profile_id, sheet, definition)
            connection.execute(
                "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                (profile_id, json.dumps(state, ensure_ascii=False), now),
            )
            row = connection.execute(
                "SELECT * FROM character_states WHERE profile_id = ?", (profile_id,)
            ).fetchone()
        else:
            state = json.loads(row["state_json"])
            changed = False
            confirmed_maximum = definition.get("progression", {}).get("maximum_hp")
            if confirmed_maximum is not None and state.get("maximum_hp") != int(confirmed_maximum):
                previous_maximum = state.get("maximum_hp")
                state["maximum_hp"] = int(confirmed_maximum)
                if state.get("current_hp") is None:
                    state["current_hp"] = int(confirmed_maximum)
                elif previous_maximum is not None:
                    state["current_hp"] = min(int(state["current_hp"]), int(confirmed_maximum))
                changed = True
            existing_resources = {item.get("key"): item for item in state.get("resources") or []}
            for resource in seed_all_resources(profile_id, sheet):
                existing = existing_resources.get(resource["key"])
                if existing is None:
                    state.setdefault("resources", []).append(resource)
                    changed = True
                elif int(existing.get("maximum") or 0) != int(resource["maximum"]):
                    spent = max(0, int(existing.get("maximum") or 0) - int(existing.get("current") or 0))
                    existing["maximum"] = int(resource["maximum"])
                    existing["current"] = max(0, int(resource["maximum"]) - spent)
                    existing["label"] = resource["label"]
                    if resource.get("recharge"):
                        existing["recharge"] = resource["recharge"]
                    changed = True
            if changed:
                now = _now()
                connection.execute(
                    "UPDATE character_states SET state_json=?, version=version+1, updated_at=? WHERE profile_id=?",
                    (json.dumps(state, ensure_ascii=False), now, profile_id),
                )
                row = connection.execute(
                    "SELECT * FROM character_states WHERE profile_id = ?", (profile_id,)
                ).fetchone()
    if row is None:
        raise RuntimeError("Estado do personagem não pôde ser criado")
    state = json.loads(row["state_json"])
    state.update({"updated_at": row["updated_at"], "version": row["version"]})
    return state


def _event_payload(row: sqlite3.Row) -> dict[str, Any]:
    result = dict(row)
    result["before"] = json.loads(result.pop("before_json")) if result.get("before_json") else None
    result["after"] = json.loads(result.pop("after_json")) if result.get("after_json") else None
    return result


def list_character_events(database_path: Path, character_id: str, limit: int = 100) -> list[dict[str, Any]]:
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute(
            "SELECT * FROM character_events WHERE character_id=? ORDER BY id DESC LIMIT ?",
            (character_id, max(1, min(limit, 500))),
        ).fetchall()
    return [_event_payload(row) for row in rows]


def _write_event(
    connection: sqlite3.Connection,
    *,
    character_id: str,
    actor_id: str,
    actor_role: str,
    event_type: str,
    field: str,
    before: Any,
    after: Any,
    reason: str | None,
    session_id: str | None,
) -> int:
    cursor = connection.execute(
        """
        INSERT INTO character_events(
          character_id,session_id,actor_id,actor_role,event_type,field,
          before_json,after_json,reason,created_at
        ) VALUES(?,?,?,?,?,?,?,?,?,?)
        """,
        (
            character_id,
            session_id,
            actor_id,
            actor_role,
            event_type,
            field,
            json.dumps(before, ensure_ascii=False) if before is not None else None,
            json.dumps(after, ensure_ascii=False) if after is not None else None,
            (reason or "").strip() or None,
            _now(),
        ),
    )
    return int(cursor.lastrowid)


def _load_state_row(connection: sqlite3.Connection, profile_id: str) -> tuple[sqlite3.Row, dict[str, Any]]:
    row = connection.execute(
        "SELECT * FROM character_states WHERE profile_id=?", (profile_id,)
    ).fetchone()
    if row is None:
        raise ValueError("Estado do personagem ainda não foi inicializado")
    return row, json.loads(row["state_json"])


def _save_state(connection: sqlite3.Connection, profile_id: str, state: dict[str, Any]) -> None:
    connection.execute(
        "UPDATE character_states SET state_json=?, version=version+1, updated_at=? WHERE profile_id=?",
        (json.dumps(state, ensure_ascii=False), _now(), profile_id),
    )


def _inventory_row(connection: sqlite3.Connection, profile_id: str, item_path: str) -> dict[str, Any] | None:
    row = connection.execute(
        "SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?",
        (profile_id, item_path),
    ).fetchone()
    if not row:
        return None
    result = dict(row)
    result["equipped"] = bool(result["equipped"])
    return result


def apply_character_action(
    database_path: Path,
    *,
    character_id: str,
    actor_id: str,
    actor_role: Literal["gm", "player"],
    action: str,
    payload: dict[str, Any],
    reason: str | None = None,
    session_id: str | None = None,
) -> dict[str, Any]:
    if action not in STATE_ACTIONS:
        raise ValueError("Ação de ficha inválida")
    if actor_role != "gm" and (actor_id != character_id or action not in OWNER_ACTIONS):
        raise PermissionError("Este perfil não pode executar esta ação")
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        _row, state = _load_state_row(connection, character_id)
        field = action
        before: Any
        after: Any

        if action == "rest_at_inn":
            before = json.loads(json.dumps(state, ensure_ascii=False))
            state["current_hp"] = state.get("maximum_hp")
            state["temporary_hp"] = 0
            state["conditions"] = []
            state["resources"] = [
                {**resource, "current": int(resource.get("maximum") or 0)}
                for resource in state.get("resources") or []
            ]
            after = json.loads(json.dumps(state, ensure_ascii=False))
            field = "state"
            _save_state(connection, character_id, state)

        elif action in {"damage", "heal", "set_hp"}:
            maximum = state.get("maximum_hp")
            current = state.get("current_hp")
            if maximum is None or current is None:
                raise ValueError("Pontos de Vida ainda não foram configurados")
            amount = int(_number(payload.get("amount")) or 0)
            if action != "set_hp" and amount <= 0:
                raise ValueError("Informe um valor positivo")
            before = current
            if action == "damage":
                after = max(0, current - amount)
            elif action == "heal":
                after = min(maximum, current + amount)
            else:
                requested = _number(payload.get("value"))
                if requested is None:
                    raise ValueError("Informe o novo valor de PV")
                after = max(0, min(maximum, int(requested)))
            state["current_hp"] = after
            field = "current_hp"
            _save_state(connection, character_id, state)

        elif action in {"add_condition", "remove_condition"}:
            condition = str(payload.get("condition") or "").strip()
            if not condition or len(condition) > 80:
                raise ValueError("Condição inválida")
            conditions = list(state.get("conditions") or [])
            before = list(conditions)
            if action == "add_condition" and condition not in conditions:
                conditions.append(condition)
            if action == "remove_condition":
                conditions = [item for item in conditions if _normalize(item) != _normalize(condition)]
            after = conditions
            state["conditions"] = conditions
            field = "conditions"
            _save_state(connection, character_id, state)

        elif action in {"consume_resource", "restore_resource"}:
            if action == "restore_resource" and actor_role != "gm":
                raise PermissionError("Somente o Mestre pode restaurar recursos")
            resource_key = str(payload.get("resource_key") or "").strip()
            amount = int(_number(payload.get("amount")) or 0)
            if amount <= 0:
                raise ValueError("Informe uma quantidade positiva")
            resources = list(state.get("resources") or [])
            index = next((i for i, item in enumerate(resources) if item.get("key") == resource_key), -1)
            if index < 0:
                raise ValueError("Recurso não encontrado")
            before = dict(resources[index])
            current = int(before.get("current") or 0)
            maximum = int(before.get("maximum") or 0)
            new_current = current - amount if action == "consume_resource" else current + amount
            resources[index] = {**before, "current": max(0, min(maximum, new_current))}
            after = dict(resources[index])
            state["resources"] = resources
            field = f"resources.{resource_key}"
            _save_state(connection, character_id, state)

        elif action in {"set_location", "set_session_notes"}:
            if actor_role != "gm":
                raise PermissionError("Somente o Mestre pode alterar este campo")
            field = "location" if action == "set_location" else "session_notes"
            value = str(payload.get("value") or "").strip()
            if len(value) > (200 if field == "location" else 4000):
                raise ValueError("Valor muito longo")
            before = state.get(field)
            after = value
            state[field] = after
            _save_state(connection, character_id, state)

        else:
            item_path = str(payload.get("item_path") or "").strip()
            if not item_path:
                raise ValueError("Item não informado")
            existing = _inventory_row(connection, character_id, item_path)
            before = existing
            if action == "grant_item":
                if actor_role != "gm":
                    raise PermissionError("Somente o Mestre pode conceder itens")
                title = str(payload.get("item_title") or "").strip()
                quantity = int(_number(payload.get("quantity")) or 1)
                if not title or quantity <= 0:
                    raise ValueError("Item ou quantidade inválida")
                after = {
                    **(existing or {}),
                    "profile_id": character_id,
                    "item_path": item_path,
                    "item_title": title,
                    "quantity": (int(existing.get("quantity") or 0) if existing else 0) + quantity,
                    "equipped": bool(payload.get("equipped", False)),
                    "notes": str(payload.get("notes") or "").strip() or None,
                }
            elif action == "remove_item":
                if actor_role != "gm":
                    raise PermissionError("Somente o Mestre pode remover itens")
                if not existing:
                    raise ValueError("Item não encontrado")
                after = {**existing, "quantity": 0, "equipped": False}
            else:
                if not existing:
                    raise ValueError("Item não encontrado no inventário")
                after = dict(existing)
                if action == "equip_item":
                    after["equipped"] = True
                elif action == "unequip_item":
                    after["equipped"] = False
                elif action == "change_quantity":
                    quantity = _number(payload.get("quantity"))
                    if quantity is None or not 0 <= int(quantity) <= 999:
                        raise ValueError("Quantidade deve ficar entre 0 e 999")
                    after["quantity"] = int(quantity)
                    if int(quantity) == 0:
                        after["equipped"] = False
            now = _now()
            connection.execute(
                """
                INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,updated_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(profile_id,item_path) DO UPDATE SET
                  item_title=excluded.item_title,quantity=excluded.quantity,equipped=excluded.equipped,
                  notes=excluded.notes,updated_at=excluded.updated_at
                """,
                (
                    character_id,
                    item_path,
                    after["item_title"],
                    int(after.get("quantity") or 0),
                    int(bool(after.get("equipped"))),
                    after.get("notes"),
                    now,
                ),
            )
            after = _inventory_row(connection, character_id, item_path)
            field = f"inventory.{item_path}"

        event_id = _write_event(
            connection,
            character_id=character_id,
            actor_id=actor_id,
            actor_role=actor_role,
            event_type=action,
            field=field,
            before=before,
            after=after,
            reason=reason,
            session_id=session_id,
        )
    return {"event_id": event_id, "field": field, "before": before, "after": after}


def update_definition_overrides(
    database_path: Path,
    *,
    character_id: str,
    actor_id: str,
    fields: dict[str, Any],
    reason: str | None = None,
) -> dict[str, Any]:
    unknown = set(fields) - DEFINITION_FIELDS
    if unknown:
        raise ValueError(f"Campos de definição não permitidos: {', '.join(sorted(unknown))}")
    if "level" in fields:
        level = _number(fields["level"])
        if level is None or not 1 <= int(level) <= 20:
            raise ValueError("Nível deve ficar entre 1 e 20")
        fields["level"] = int(level)
    if "attributes" in fields:
        attributes = dict(fields["attributes"] or {})
        if set(attributes) - {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"}:
            raise ValueError("Atributo inválido")
        for key, value in attributes.items():
            number = _number(value)
            if number is None or not 1 <= int(number) <= 30:
                raise ValueError(f"{key} deve ficar entre 1 e 30")
            attributes[key] = int(number)
        fields["attributes"] = attributes
    for key in ("maximum_hp", "armor_class", "initiative"):
        if key in fields and fields[key] not in (None, ""):
            number = _number(fields[key])
            if number is None or int(number) < 0:
                raise ValueError(f"{key} precisa ser um número não negativo")
            fields[key] = int(number)
    if "gm_fields" in fields:
        gm_fields = dict(fields["gm_fields"] or {})
        allowed = {"notes", "private_state"}
        if set(gm_fields) - allowed:
            raise ValueError("Campo de Mestre inválido")
        fields["gm_fields"] = {key: str(value or "")[:5000] for key, value in gm_fields.items()}

    init_character_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute(
            "SELECT data_json FROM character_definition_overrides WHERE profile_id=?",
            (character_id,),
        ).fetchone()
        current = json.loads(row["data_json"]) if row else {}
        before = dict(current)
        for key, value in fields.items():
            if key == "attributes":
                current[key] = {**dict(current.get(key) or {}), **dict(value or {})}
            elif key == "gm_fields":
                current[key] = {**dict(current.get(key) or {}), **dict(value or {})}
            else:
                current[key] = value
        now = _now()
        connection.execute(
            """
            INSERT INTO character_definition_overrides(profile_id,data_json,updated_at)
            VALUES(?,?,?) ON CONFLICT(profile_id) DO UPDATE SET
              data_json=excluded.data_json,updated_at=excluded.updated_at
            """,
            (character_id, json.dumps(current, ensure_ascii=False), now),
        )
        _write_event(
            connection,
            character_id=character_id,
            actor_id=actor_id,
            actor_role="gm",
            event_type="definition_update",
            field="definition",
            before=before,
            after=current,
            reason=reason,
            session_id=None,
        )
    return current


def revert_character_event(
    database_path: Path,
    *,
    character_id: str,
    event_id: int,
    actor_id: str,
) -> dict[str, Any]:
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute(
            "SELECT * FROM character_events WHERE id=? AND character_id=?",
            (event_id, character_id),
        ).fetchone()
        if row is None:
            raise ValueError("Evento não encontrado")
        event = _event_payload(row)
        if event.get("reverted_at"):
            raise ValueError("Evento já revertido")
        before = event.get("before")
        after = event.get("after")
        field = str(event["field"])

        if field == "definition":
            current_row = connection.execute(
                "SELECT data_json FROM character_definition_overrides WHERE profile_id=?",
                (character_id,),
            ).fetchone()
            current = json.loads(current_row["data_json"]) if current_row else {}
            if current != after:
                raise ValueError("A definição mudou depois deste evento; reverta o evento mais recente primeiro")
            connection.execute(
                """
                INSERT INTO character_definition_overrides(profile_id,data_json,updated_at)
                VALUES(?,?,?) ON CONFLICT(profile_id) DO UPDATE SET
                  data_json=excluded.data_json,updated_at=excluded.updated_at
                """,
                (character_id, json.dumps(before or {}, ensure_ascii=False), _now()),
            )
        elif field == "state":
            _state_row, current = _load_state_row(connection, character_id)
            if current != after:
                raise ValueError("O estado mudou depois deste descanso; reverta o evento mais recente primeiro")
            _save_state(connection, character_id, dict(before or {}))
        elif field.startswith("inventory."):
            item_path = field.split(".", 1)[1]
            current = _inventory_row(connection, character_id, item_path)
            if current != after:
                raise ValueError("O item mudou depois deste evento; reverta o evento mais recente primeiro")
            if before is None:
                connection.execute(
                    "DELETE FROM player_inventory WHERE profile_id=? AND item_path=?",
                    (character_id, item_path),
                )
            else:
                connection.execute(
                    """
                    INSERT INTO player_inventory(profile_id,item_path,item_title,quantity,equipped,notes,updated_at)
                    VALUES(?,?,?,?,?,?,?) ON CONFLICT(profile_id,item_path) DO UPDATE SET
                      item_title=excluded.item_title,quantity=excluded.quantity,equipped=excluded.equipped,
                      notes=excluded.notes,updated_at=excluded.updated_at
                    """,
                    (
                        character_id,
                        item_path,
                        before["item_title"],
                        int(before.get("quantity") or 0),
                        int(bool(before.get("equipped"))),
                        before.get("notes"),
                        _now(),
                    ),
                )
        else:
            _state_row, state = _load_state_row(connection, character_id)
            if field.startswith("resources."):
                key = field.split(".", 1)[1]
                index = next((i for i, item in enumerate(state.get("resources") or []) if item.get("key") == key), -1)
                if index < 0 or state["resources"][index] != after:
                    raise ValueError("O recurso mudou depois deste evento; reverta o evento mais recente primeiro")
                state["resources"][index] = before
            else:
                if state.get(field) != after:
                    raise ValueError("O estado mudou depois deste evento; reverta o evento mais recente primeiro")
                state[field] = before
            _save_state(connection, character_id, state)

        reverted_at = _now()
        connection.execute(
            "UPDATE character_events SET reverted_at=?,reverted_by=? WHERE id=?",
            (reverted_at, actor_id, event_id),
        )
    return {**event, "reverted_at": reverted_at, "reverted_by": actor_id}


def compose_character_view(
    *,
    definition: dict[str, Any],
    state: dict[str, Any] | None,
    inventory: list[dict[str, Any]],
    access_level: AccessLevel,
) -> dict[str, Any]:
    if access_level == "public":
        return {
            "access_level": "public",
            "definition": definition,
            "state": None,
            "inventory": [],
            "permissions": {
                "view_private_mechanics": False,
                "edit_state": False,
                "edit_definition": False,
                "view_gm_fields": False,
                "revert_events": False,
            },
        }
    return {
        "access_level": access_level,
        "definition": definition,
        "state": state,
        "inventory": inventory,
        "permissions": {
            "view_private_mechanics": True,
            "edit_state": True,
            "edit_definition": access_level == "gm",
            "view_gm_fields": access_level == "gm",
            "revert_events": access_level == "gm",
        },
    }
