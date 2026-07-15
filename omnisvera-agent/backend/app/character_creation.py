from __future__ import annotations

import copy
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

STEP_GUIDANCE = {
    "attributes": {
        "instruction": "Role 3d6 seis vezes e distribua os resultados entre Força, Destreza, Constituição, Inteligência, Sabedoria e Carisma. Depois aplique os ajustes da raça.",
        "checklist": [
            "Registre primeiro os valores rolados ou aprovados pelo Mestre.",
            "Confira na referência racial quais ajustes entram na ficha final.",
            "Os seis valores precisam estar preenchidos para concluir esta etapa.",
        ],
    },
    "race": {
        "instruction": "Confirme a raça, aplique seus modificadores e registre movimento, idiomas e habilidades raciais.",
        "checklist": [
            "Use a configuração específica do personagem quando ela existir.",
            "Não some novamente um ajuste racial que já esteja incluído nos atributos finais.",
            "Copie para a ficha apenas as habilidades liberadas no nível atual.",
        ],
    },
    "character_class": {
        "instruction": "Registre classe, nível, habilidades, Jogada de Proteção, Base de Ataque, experiência e Pontos de Vida.",
        "checklist": [
            "No nível 1, use a primeira linha da progressão da classe.",
            "Pontos de Vida iniciais usam o Dado de Vida da classe e o ajuste de Constituição.",
            "Especializações futuras não precisam ser aplicadas antes do nível indicado.",
        ],
    },
    "attacks": {
        "instruction": "Calcule cada ataque com a Base de Ataque da classe, ajustes raciais e o modificador do atributo apropriado.",
        "checklist": [
            "Corpo a corpo: Base de Ataque + ajuste de Força + bônus raciais ou do item.",
            "À distância: Base de Ataque + ajuste de Destreza + bônus raciais ou do item.",
            "Anote separadamente arma, dano, alcance e qualquer propriedade importante.",
        ],
    },
    "languages": {
        "instruction": "Registre os idiomas falados e quais deles o personagem consegue ler ou escrever.",
        "checklist": [
            "Idiomas falados: idioma nativo, Comum e adicionais permitidos por Inteligência.",
            "Leitura e escrita: Inteligência dividida por 6, arredondada para baixo.",
            "Inteligência inferior a 6 torna o personagem analfabeto.",
        ],
    },
    "alignment": {
        "instruction": "Escolha entre Ordeiro, Neutro ou Caótico, respeitando indicações da raça e restrições da classe.",
        "checklist": [
            "O alinhamento descreve uma orientação, não obriga toda decisão do personagem.",
            "Valores antigos mais específicos devem ser confirmados com o Mestre.",
        ],
    },
    "equipment": {
        "instruction": "Compre ou confirme o equipamento, registre a renda inicial e calcule o peso carregado.",
        "checklist": [
            "Renda inicial padrão: 3d6 × 10 PO, salvo equipamento já aprovado.",
            "Some o peso dos itens realmente carregados, não apenas possuídos.",
            "A carga pode reduzir o movimento em 1 m, 2 m ou deixá-lo em 1 m.",
        ],
    },
    "armor": {
        "instruction": "Calcule a Classe de Armadura somando base 10, Destreza, armadura, escudo, raça e outros bônus.",
        "checklist": [
            "Registre cada parcela do cálculo para o Mestre conseguir revisar.",
            "Confira se a classe permite a armadura e o escudo escolhidos.",
            "A penalidade de carga ou armadura pode afetar o movimento.",
        ],
    },
    "magic": {
        "instruction": "Escolha e registre magias, fórmulas, técnicas ou poderes permitidos pela classe e pelo nível.",
        "checklist": [
            "Use somente a quantidade liberada pela progressão do nível atual.",
            "Anote custos, usos, preparação ou memorização quando existirem.",
            "Se a etapa não se aplicar, escolha ‘Não se aplica’.",
        ],
    },
    "details": {
        "instruction": "Finalize aparência, peso, altura, personalidade, origem e objetivos do personagem.",
        "checklist": [
            "Explique quem o personagem era antes de se tornar aventureiro.",
            "Defina pelo menos uma motivação que possa gerar decisões em jogo.",
            "Não é necessário revelar segredos do Mestre para concluir o histórico.",
        ],
    },
}

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


def _first_paragraph(value: str, limit: int = 420) -> str:
    prose_only = "\n".join(
        line for line in value.splitlines()
        if not line.strip().startswith("|") and not line.strip().startswith("> [!")
    )
    cleaned = _clean_markdown(prose_only, limit * 2)
    for paragraph in re.split(r"\n\s*\n", cleaned):
        paragraph = paragraph.strip()
        if paragraph:
            return paragraph[:limit].strip()
    return ""


def _parse_tables(value: str, *, level: int = 1, max_tables: int = 5, max_rows: int = 10) -> list[dict[str, Any]]:
    lines = value.splitlines()
    tables: list[dict[str, Any]] = []
    index = 0
    while index < len(lines) and len(tables) < max_tables:
        if not lines[index].strip().startswith("|"):
            index += 1
            continue
        block: list[str] = []
        while index < len(lines) and lines[index].strip().startswith("|"):
            block.append(lines[index].strip())
            index += 1
        if len(block) < 3:
            continue
        rows = [[_clean_markdown(cell.strip(), 320) for cell in line.strip("|").split("|")] for line in block]
        headers = rows[0]
        separator = rows[1]
        if not all(re.fullmatch(r":?-{3,}:?", cell.replace(" ", "")) for cell in separator):
            continue
        body_rows = [row for row in rows[2:] if len(row) == len(headers)]
        if headers and _normalize(headers[0]) == "nivel":
            matching = [row for row in body_rows if _number(row[0]) == level]
            body_rows = matching or body_rows[:max_rows]
        else:
            body_rows = body_rows[:max_rows]
        if body_rows:
            tables.append({"headers": headers, "rows": body_rows})
    return tables


def _subsections(value: str, *, limit: int = 8) -> list[dict[str, str]]:
    matches = list(re.finditer(r"^###\s+(.+?)\s*$", value, flags=re.MULTILINE))
    result: list[dict[str, str]] = []
    for position, match in enumerate(matches[:limit]):
        end = matches[position + 1].start() if position + 1 < len(matches) else len(value)
        content = _clean_markdown(value[match.end():end], 620)
        if content:
            result.append({"title": _clean_markdown(match.group(1), 120), "text": content})
    return result


def _source_card(note: dict[str, Any] | None, *, kind: str, level: int = 1) -> dict[str, Any] | None:
    if not note:
        return None
    frontmatter = note.get("frontmatter") if isinstance(note.get("frontmatter"), dict) else {}
    body = str(note.get("content") or "")
    title = str(frontmatter.get("name") or note.get("title") or ("Raça" if kind == "race" else "Classe"))
    if kind == "race":
        core_names = ("Mecânica Resumida", "Mecânica de Consulta", "Traços Raciais Propostos")
        ability_names = ("Habilidades Raciais",)
    else:
        core_names = (f"{title} em Jogo", "Mecânica Resumida", "Notas de Mecânica")
        ability_names = ("Habilidades de Classe", "Técnicas Iniciais de Raziel")

    core = _section(body, *core_names)
    abilities = "\n\n".join(section for name in ability_names if (section := _section(body, name)))
    tables = _parse_tables(core, level=level, max_tables=3, max_rows=12)
    ability_tables = _parse_tables(abilities, level=level, max_tables=3, max_rows=8)
    tables.extend(ability_tables)

    rules: list[dict[str, str]] = []
    for table in tables[:1]:
        if len(table["headers"]) == 2:
            rules = [{"label": row[0], "value": row[1]} for row in table["rows"]]

    intro = _first_paragraph(core) or _first_paragraph(_section(body, "Visão Geral"))
    return {
        "kind": kind,
        "title": title,
        "intro": intro,
        "rules": rules,
        "level_one": _progression_level_one(body) if kind == "class" else {},
        "abilities": _subsections(abilities),
        "tables": tables,
    }


def _build_guides(
    *,
    race_note: dict[str, Any] | None,
    class_note: dict[str, Any] | None,
    level: int = 1,
) -> dict[str, dict[str, Any]]:
    race_card = _source_card(race_note, kind="race", level=level)
    class_card = _source_card(class_note, kind="class", level=level)
    def compact(card: dict[str, Any] | None) -> dict[str, Any] | None:
        if not card:
            return None
        reduced = copy.deepcopy(card)
        reduced["abilities"] = []
        reduced["tables"] = reduced.get("tables", [])[:1]
        return reduced

    compact_race = compact(race_card)
    compact_class = compact(class_card)
    guides: dict[str, dict[str, Any]] = {}
    for key, _, _ in STEP_DEFINITIONS:
        guide = copy.deepcopy(STEP_GUIDANCE[key])
        sources: list[dict[str, Any]] = []
        if key == "race" and race_card:
            sources.append(race_card)
        elif key in {"attributes", "languages", "attacks", "armor"} and compact_race:
            sources.append(compact_race)
        if key == "character_class" and class_card:
            sources.append(class_card)
        elif key in {"attacks", "equipment", "armor", "magic"} and compact_class:
            sources.append(compact_class)
        guide["sources"] = sources
        guides[key] = guide
    return guides


def _attribute_modifier(value: Any) -> int | None:
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


def _signed(value: int) -> str:
    return f"+{value}" if value >= 0 else str(value)


def _load_limits(strength: Any) -> tuple[int, int, int, int] | None:
    score = _number(strength)
    if score is None:
        return None
    score = int(score)
    if score <= 3:
        return 10, 10, 20, 30
    if score <= 8:
        return 20, 20, 30, 50
    if score <= 12:
        return 30, 30, 50, 70
    if score <= 15:
        return 40, 40, 70, 90
    if score <= 17:
        return 50, 50, 80, 100
    return 60, 60, 100, 120


def _dynamic_calculations(step_key: str, data: dict[str, Any]) -> list[str]:
    attributes = data.get("attributes") or {}
    class_fields = data.get("character_class") or {}
    strength = attributes.get("strength")
    dexterity = attributes.get("dexterity")
    constitution = attributes.get("constitution")
    intelligence = _number(attributes.get("intelligence"))
    base_attack = _number(class_fields.get("base_attack"))
    calculations: list[str] = []
    if step_key == "attributes":
        modifiers = []
        for label, field in (("FOR", "strength"), ("DES", "dexterity"), ("CON", "constitution"), ("INT", "intelligence"), ("SAB", "wisdom"), ("CAR", "charisma")):
            modifier = _attribute_modifier(attributes.get(field))
            if modifier is not None:
                modifiers.append(f"{label} {_signed(modifier)}")
        if modifiers:
            calculations.append("Ajustes atuais: " + " · ".join(modifiers))
    elif step_key == "character_class":
        constitution_modifier = _attribute_modifier(constitution)
        if constitution_modifier is not None:
            calculations.append(f"Ajuste de Constituição nos PV por Dado de Vida: {_signed(constitution_modifier)}.")
    elif step_key == "attacks" and base_attack is not None:
        strength_modifier = _attribute_modifier(strength)
        dexterity_modifier = _attribute_modifier(dexterity)
        if strength_modifier is not None:
            calculations.append(f"Corpo a corpo antes de bônus racial/item: BA {int(base_attack)} + FOR {_signed(strength_modifier)} = {_signed(int(base_attack) + strength_modifier)}.")
        if dexterity_modifier is not None:
            calculations.append(f"À distância antes de bônus racial/item: BA {int(base_attack)} + DES {_signed(dexterity_modifier)} = {_signed(int(base_attack) + dexterity_modifier)}.")
    elif step_key == "languages" and intelligence is not None:
        written = max(0, int(intelligence) // 6)
        if intelligence < 6:
            calculations.append("Com esta Inteligência, o personagem é analfabeto.")
        else:
            calculations.append(f"Com INT {int(intelligence)}, pode ler/escrever em até {written} idioma(s).")
    elif step_key == "equipment":
        limits = _load_limits(strength)
        if limits:
            no_load, light, heavy, maximum = limits
            calculations.append(f"FOR {int(_number(strength) or 0)}: sem carga até {no_load} kg; carga leve a partir de {light} kg; pesada a partir de {heavy} kg; máxima {maximum} kg.")
    elif step_key == "armor":
        dexterity_modifier = _attribute_modifier(dexterity)
        if dexterity_modifier is not None:
            calculations.append(f"CA antes de armadura, escudo, raça e outros bônus: 10 + DES {_signed(dexterity_modifier)} = {10 + dexterity_modifier}.")
    return calculations


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
    stored_guides = data.get("_guides") if isinstance(data.get("_guides"), dict) else {}
    steps = []
    for key, title, summary in STEP_DEFINITIONS:
        fields = data.get(key, {})
        missing = missing_fields(key, fields)
        guide = copy.deepcopy(stored_guides.get(key) or STEP_GUIDANCE.get(key) or {})
        guide["calculations"] = _dynamic_calculations(key, data)
        steps.append({
            "key": key,
            "title": title,
            "summary": summary,
            "status": "complete" if not missing else "pending",
            "fields": fields,
            "missing_fields": missing,
            "guide": guide,
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
    seeded = seed_from_note(note, race_note=race_note, class_note=class_note)
    level = int(_number((note.get("frontmatter") or {}).get("level")) or 1)
    guides = _build_guides(race_note=race_note, class_note=class_note, level=level)
    with closing(_connect(database_path)) as connection, connection:
        row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
        if row is None:
            now = datetime.now(timezone.utc).isoformat()
            seeded["_guides"] = guides
            seeded["_meta"] = {"manual_fields": []}
            connection.execute(
                "INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at) VALUES (?, ?, ?, ?, ?)",
                (
                    profile_id,
                    character_path,
                    character_title,
                    json.dumps(seeded, ensure_ascii=False),
                    now,
                ),
            )
            row = connection.execute("SELECT * FROM character_sheets WHERE profile_id = ?", (profile_id,)).fetchone()
        else:
            data = json.loads(row["data_json"])
            metadata = data.setdefault("_meta", {})
            manual_fields = set(metadata.get("manual_fields") or [])
            changed = data.get("_guides") != guides
            data["_guides"] = guides
            # Refresh only blank values that are now explicitly confirmed by the
            # Vault. Fields already touched by the player always win, including
            # when the player deliberately cleared one for review.
            for step_key, seeded_fields in seeded.items():
                if step_key.startswith("_") or not isinstance(seeded_fields, dict):
                    continue
                current = data.setdefault(step_key, {})
                for field, value in seeded_fields.items():
                    token = f"{step_key}.{field}"
                    if token in manual_fields or not _present(value):
                        continue
                    if field not in current or not _present(current.get(field)):
                        current[field] = value
                        changed = True
            if changed or row["character_path"] != character_path or row["character_title"] != character_title:
                now = datetime.now(timezone.utc).isoformat()
                connection.execute(
                    "UPDATE character_sheets SET character_path = ?, character_title = ?, data_json = ?, updated_at = ? WHERE profile_id = ?",
                    (character_path, character_title, json.dumps(data, ensure_ascii=False), now, profile_id),
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
        metadata = data.setdefault("_meta", {})
        manual_fields = set(metadata.get("manual_fields") or [])
        manual_fields.update(f"{step_key}.{field}" for field in fields)
        metadata["manual_fields"] = sorted(manual_fields)
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
