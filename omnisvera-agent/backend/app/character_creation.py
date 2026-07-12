from __future__ import annotations

import json
import re
import sqlite3
import unicodedata
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


STEP_DEFINITIONS = (
    ("attributes", "1. Atributos", "Distribua os seis valores que definem as capacidades básicas."),
    ("race", "2. Raça", "Registre raça, movimento e habilidades raciais."),
    ("character_class", "3. Classe", "Complete classe, nível, vida, proteção, ataque e habilidades."),
    ("attacks", "4. Ataques", "Calcule ataques corpo a corpo, à distância e anote as opções usadas."),
    ("languages", "5. Idiomas", "Defina idiomas falados e formas de escrita conhecidas."),
    ("alignment", "6. Alinhamento", "Escolha a orientação moral usada pela campanha."),
    ("equipment", "7. Equipamentos e carga", "Feche dinheiro inicial, equipamentos e carga transportada."),
    ("armor", "8. Classe de Armadura", "Registre a defesa total e de onde cada bônus vem."),
    ("magic", "9. Magia e poderes", "Escolha magias, fórmulas ou técnicas; marque quando não se aplicar."),
    ("details", "10. Identidade e história", "Finalize aparência, personalidade, passado e objetivos."),
)

ALLOWED_FIELDS = {
    "attributes": {"strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma"},
    "race": {"race", "movement", "racial_abilities"},
    "character_class": {
        "class_name", "level", "hit_points", "saving_throw", "base_attack", "experience", "class_abilities"
    },
    "attacks": {"melee_bonus", "ranged_bonus", "attack_notes"},
    "languages": {"spoken_languages", "written_languages"},
    "alignment": {"alignment"},
    "equipment": {"equipment_list", "starting_gold", "carried_weight", "load_status"},
    "armor": {"armor_class", "armor_breakdown"},
    "magic": {"magic_mode", "known_magic", "magic_notes"},
    "details": {"physical_description", "personality", "background", "goals"},
}

NUMERIC_FIELDS = {
    "strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma",
    "level", "hit_points", "base_attack", "experience", "melee_bonus", "ranged_bonus",
    "starting_gold", "carried_weight", "armor_class",
}


def _connect(database_path: Path) -> sqlite3.Connection:
    database_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_character_creation(database_path: Path) -> None:
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            """
            CREATE TABLE IF NOT EXISTS character_sheets (
                profile_id TEXT PRIMARY KEY,
                character_path TEXT NOT NULL,
                character_title TEXT NOT NULL,
                data_json TEXT NOT NULL,
                status TEXT NOT NULL DEFAULT 'draft',
                submitted_at TEXT,
                reviewed_at TEXT,
                gm_feedback TEXT,
                updated_at TEXT NOT NULL
            )
            """
        )


def _normalize(value: str) -> str:
    return "".join(
        character
        for character in unicodedata.normalize("NFKD", value.lower())
        if not unicodedata.combining(character)
    )


def _clean_markdown(value: str, limit: int = 1800) -> str:
    value = re.sub(r"```[\s\S]*?```", "", value)
    value = re.sub(r"!\[\[[^\]]+\]\]", "", value)
    value = re.sub(r"\[\[([^\]|]+)\|([^\]]+)\]\]", r"\2", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"^>\s*\[![^\]]+\].*$", "", value, flags=re.MULTILINE)
    value = re.sub(r"[*_`#>|]", "", value)
    value = re.sub(r"\n{3,}", "\n\n", value).strip()
    return value[:limit].strip()


def _section(body: str, *names: str) -> str:
    for name in names:
        match = re.search(rf"^(#{{2,4}})\s+{re.escape(name)}\s*$", body, flags=re.IGNORECASE | re.MULTILINE)
        if match:
            level = len(match.group(1))
            end = len(body)
            for next_heading in re.finditer(r"^(#{2,4})\s+.+$", body[match.end():], flags=re.MULTILINE):
                if len(next_heading.group(1)) <= level:
                    end = match.end() + next_heading.start()
                    break
            return body[match.end():end].strip()
    return ""


def _label(body: str, label: str) -> str:
    match = re.search(rf"\*\*{re.escape(label)}:\*\*\s*([^\n]+)", body, flags=re.IGNORECASE)
    return _clean_markdown(match.group(1), 500) if match else ""


def _table_value(body: str, label: str) -> str:
    target = _normalize(label)
    for row_label, value in re.findall(r"^\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$", body, flags=re.MULTILINE):
        if _normalize(row_label.strip()) == target:
            return value.strip()
    return ""


def _number(value: Any) -> int | float | None:
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value
    match = re.search(r"[-+]?\d+(?:[.,]\d+)?", str(value or ""))
    if not match:
        return None
    raw = match.group(0).replace(",", ".")
    number = float(raw)
    return int(number) if number.is_integer() else number


def _list_from_section(section: str) -> str:
    lines = []
    for line in section.splitlines():
        clean = re.sub(r"^\s*[-*]\s*", "", line).strip()
        clean = _clean_markdown(clean, 600)
        if clean and not clean.startswith("---"):
            lines.append(clean)
    return "\n".join(dict.fromkeys(lines))


def _progression_level_one(body: str) -> dict[str, str]:
    section = _section(body, "Progressão", "Progressão de Classe")
    lines = [line.strip() for line in section.splitlines() if line.strip().startswith("|")]
    for index, line in enumerate(lines):
        headers = [cell.strip() for cell in line.strip("|").split("|")]
        if not headers or _normalize(headers[0]) != "nivel":
            continue
        for candidate in lines[index + 1:]:
            values = [cell.strip() for cell in candidate.strip("|").split("|")]
            if values and values[0] == "1" and len(values) == len(headers):
                return dict(zip(headers, values))
    return {}


def seed_from_note(
    note: dict[str, Any],
    *,
    race_note: dict[str, Any] | None = None,
    class_note: dict[str, Any] | None = None,
) -> dict[str, dict[str, Any]]:
    frontmatter = note.get("frontmatter") if isinstance(note.get("frontmatter"), dict) else {}
    body = str(note.get("content") or "")
    attributes = {
        "strength": _number(_table_value(body, "Força")),
        "dexterity": _number(_table_value(body, "Destreza")),
        "constitution": _number(_table_value(body, "Constituição")),
        "intelligence": _number(_table_value(body, "Inteligência")),
        "wisdom": _number(_table_value(body, "Sabedoria")),
        "charisma": _number(_table_value(body, "Carisma")),
    }
    race_body = str((race_note or {}).get("content") or "")
    class_body = str((class_note or {}).get("content") or "")
    language_section = _section(body, "Idiomas")
    language_lines = _list_from_section(language_section)
    spoken, written = [], []
    for line in language_lines.splitlines():
        if "escrit" in _normalize(line):
            written.append(line)
        elif "definir" not in _normalize(line) and "mestre" not in _normalize(line):
            spoken.append(line)
    race_languages = _table_value(race_body, "Idiomas")
    if race_languages and not spoken:
        spoken.append(_clean_markdown(race_languages, 500))
    if race_languages and not written and any(term in _normalize(race_languages) for term in ("le", "escreve")):
        written.append(_clean_markdown(race_languages, 500))

    equipment = _label(body, "Posses")
    if not equipment:
        equipment = _list_from_section(_section(body, "Armas e carga"))

    powers = _list_from_section(_section(body, "Poderes", "Habilidades especiais"))
    character_class = str(frontmatter.get("class") or _label(body, "Classe"))
    progression = _progression_level_one(class_body)
    progression_normalized = {_normalize(key): value for key, value in progression.items()}
    race_abilities = _clean_markdown(
        _section(race_body, "Habilidades Raciais", "Mecânica Resumida", "Mecânica de Consulta"),
        2200,
    )
    movement = _table_value(body, "Movimento") or _table_value(race_body, "Movimento base")
    if not movement and "movimento 9m" in _normalize(race_body):
        movement = "9 m"
    magic_mode = "none"
    if _normalize(character_class) in {"mago", "clerigo", "hemomante", "alquimista"}:
        magic_mode = {
            "mago": "arcane", "clerigo": "divine", "hemomante": "blood", "alquimista": "alchemical"
        }[_normalize(character_class)]
    elif powers:
        magic_mode = "special"

    history = _clean_markdown(_section(body, "História", "História Pública"), 2400)
    personality = _clean_markdown(_section(body, "Personalidade"), 1400)
    if "pendente" in _normalize(personality):
        personality = ""
    current = _clean_markdown(_section(body, "Situação Atual"), 1000)

    return {
        "attributes": attributes,
        "race": {
            "race": str(frontmatter.get("race") or _label(body, "Raça")),
            "movement": movement,
            "racial_abilities": race_abilities,
        },
        "character_class": {
            "class_name": character_class,
            "level": _number(frontmatter.get("level")) or 1,
            "hit_points": _number(_table_value(body, "Pontos de Vida")),
            "saving_throw": progression_normalized.get("jp", ""),
            "base_attack": _number(_table_value(body, "Bônus de Ataque")) if _table_value(body, "Bônus de Ataque") else _number(progression_normalized.get("ba")),
            "experience": _number(progression_normalized.get("xp")) if progression_normalized.get("xp") else 0,
            "class_abilities": _list_from_section(_section(body, "Capacidades", "Capacidades Conhecidas")) or _clean_markdown(_section(class_body, "Habilidades de Classe"), 1800) or powers,
        },
        "attacks": {
            "melee_bonus": _number(_table_value(body, "Bônus de Ataque")),
            "ranged_bonus": None,
            "attack_notes": equipment,
        },
        "languages": {"spoken_languages": "\n".join(spoken), "written_languages": "\n".join(written)},
        "alignment": {
            "alignment": "" if "aberto" in _normalize(str(frontmatter.get("alignment") or "")) else str(frontmatter.get("alignment") or "")
        },
        "equipment": {
            "equipment_list": equipment,
            "starting_gold": _number(_table_value(body, "Ouro inicial")),
            "carried_weight": None,
            "load_status": "",
        },
        "armor": {
            "armor_class": _number(_table_value(body, "Classe de Armadura")),
            "armor_breakdown": "",
        },
        "magic": {"magic_mode": magic_mode, "known_magic": powers, "magic_notes": ""},
        "details": {
            "physical_description": _clean_markdown(_section(body, "Aparência"), 1400),
            "personality": personality,
            "background": history,
            "goals": current,
        },
    }


def _present(value: Any) -> bool:
    if value is None:
        return False
    if isinstance(value, str):
        return bool(value.strip())
    return True


def missing_fields(step_key: str, fields: dict[str, Any]) -> list[str]:
    if step_key == "attributes":
        return [name for name in ALLOWED_FIELDS[step_key] if _number(fields.get(name)) is None]
    if step_key == "race":
        required = ("race", "movement", "racial_abilities")
    elif step_key == "character_class":
        required = ("class_name", "level", "hit_points", "saving_throw", "base_attack", "experience", "class_abilities")
    elif step_key == "attacks":
        required = ("melee_bonus", "ranged_bonus", "attack_notes")
    elif step_key == "languages":
        required = ("spoken_languages", "written_languages")
    elif step_key == "alignment":
        required = ("alignment",)
    elif step_key == "equipment":
        required = ("equipment_list", "starting_gold", "carried_weight", "load_status")
    elif step_key == "armor":
        required = ("armor_class",)
    elif step_key == "magic":
        mode = str(fields.get("magic_mode") or "").strip()
        if mode == "none":
            return []
        required = ("magic_mode", "known_magic")
    else:
        required = ("physical_description", "personality", "background", "goals")
    return [name for name in required if not _present(fields.get(name))]


def _row_to_response(row: sqlite3.Row) -> dict[str, Any]:
    data = json.loads(row["data_json"])
    steps = []
    for key, title, summary in STEP_DEFINITIONS:
        fields = data.get(key, {})
        missing = missing_fields(key, fields)
        steps.append({
            "key": key,
            "title": title,
            "summary": summary,
            "status": "complete" if not missing else "pending",
            "fields": fields,
            "missing_fields": missing,
        })
    return {
        "profile_id": row["profile_id"],
        "character_path": row["character_path"],
        "character_title": row["character_title"],
        "status": row["status"],
        "completion_count": sum(step["status"] == "complete" for step in steps),
        "total_steps": len(steps),
        "steps": steps,
        "submitted_at": row["submitted_at"],
        "reviewed_at": row["reviewed_at"],
        "gm_feedback": row["gm_feedback"],
        "updated_at": row["updated_at"],
    }


def get_or_create_sheet(
    database_path: Path,
    *,
    profile_id: str,
    character_path: str,
    character_title: str,
    note: dict[str, Any],
    race_note: dict[str, Any] | None = None,
    class_note: dict[str, Any] | None = None,
) -> dict[str, Any]:
    init_character_creation(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            connection.execute(
                "INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at) VALUES (?, ?, ?, ?, ?)",
                (
                    profile_id,
                    character_path,
                    character_title,
                    json.dumps(seed_from_note(note, race_note=race_note, class_note=class_note), ensure_ascii=False),
                    now,
                ),
            )
            row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
    if row is None:
        raise RuntimeError("A ficha não pôde ser criada")
    return _row_to_response(row)


def update_sheet_step(database_path: Path, *, profile_id: str, step_key: str, fields: dict[str, Any]) -> dict[str, Any] | None:
    if step_key not in ALLOWED_FIELDS:
        raise ValueError("Etapa de ficha inválida")
    unknown = set(fields) - ALLOWED_FIELDS[step_key]
    if unknown:
        raise ValueError(f"Campos não permitidos: {', '.join(sorted(unknown))}")
    for key in NUMERIC_FIELDS & set(fields):
        value = fields[key]
        if value in (None, ""):
            fields[key] = None
            continue
        number = _number(value)
        if number is None:
            raise ValueError(f"{key} precisa ser numérico")
        fields[key] = number
    if step_key == "attributes":
        for key, value in fields.items():
            number = _number(value)
            if number is not None and not 1 <= number <= 30:
                raise ValueError(f"{key} deve ficar entre 1 e 30")

    init_character_creation(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
        if row is None:
            return None
        data = json.loads(row["data_json"])
        current = data.setdefault(step_key, {})
        current.update(fields)
        now = datetime.now(timezone.utc).isoformat()
        connection.execute(
            "UPDATE character_sheets SET data_json = ?, status = 'draft', submitted_at = NULL, reviewed_at = NULL, gm_feedback = NULL, updated_at = ? WHERE profile_id = ?",
            (json.dumps(data, ensure_ascii=False), now, profile_id),
        )
        updated = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
    return _row_to_response(updated) if updated else None


def submit_sheet(database_path: Path, *, profile_id: str) -> dict[str, Any] | None:
    init_character_creation(database_path)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
        if row is None:
            return None
        response = _row_to_response(row)
        if response["completion_count"] != response["total_steps"]:
            raise ValueError("Complete as dez etapas antes de entregar a ficha")
        now = datetime.now(timezone.utc).isoformat()
        connection.execute(
            "UPDATE character_sheets SET status = 'submitted', submitted_at = ?, reviewed_at = NULL, gm_feedback = NULL, updated_at = ? WHERE profile_id = ?",
            (now, now, profile_id),
        )
        updated = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
    return _row_to_response(updated) if updated else None


def review_sheet(database_path: Path, *, profile_id: str, status: str, feedback: str | None) -> dict[str, Any] | None:
    if status not in {"approved", "changes_requested"}:
        raise ValueError("Revisão de ficha inválida")
    init_character_creation(database_path)
    now = datetime.now(timezone.utc).isoformat()
    with closing(_connect(database_path)) as connection, connection:
        connection.execute(
            "UPDATE character_sheets SET status = ?, reviewed_at = ?, gm_feedback = ?, updated_at = ? WHERE profile_id = ?",
            (status, now, (feedback or "").strip() or None, now, profile_id),
        )
        row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
    return _row_to_response(row) if row else None


def list_sheets(database_path: Path) -> list[dict[str, Any]]:
    init_character_creation(database_path)
    with closing(_connect(database_path)) as connection:
        rows = connection.execute("SELECT * FROM character_sheets ORDER BY character_title").fetchall()
    return [_row_to_response(row) for row in rows]
