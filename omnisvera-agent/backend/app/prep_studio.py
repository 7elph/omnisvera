"""Estúdio de preparação — Cenas com IA (PREP-STUDIO-20261108).

The GM asks in plain text; the local gpt-oss model drafts a monster, an NPC with a
full sheet, an item or a map (map art comes from Flux). The server validates and
normalizes every draft into the same shapes the table already uses, stores it as a
*draft* and never touches the table, sheets or the Vault by itself. A draft only
reaches play when the GM applies it (placing a hidden pin, creating a campaign
item or adding a map), and each application is recorded on the draft.
"""
from __future__ import annotations

import asyncio
import json
import re
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

KINDS = ("monster", "npc", "item", "map")
KIND_LABELS = {"monster": "monstro", "npc": "NPC", "item": "item", "map": "mapa"}
STATUSES = ("generating", "ready", "failed", "applied", "discarded")
REQUEST_ID_RE = re.compile(r"^[A-Za-z0-9._:-]{8,120}$")
DICE_RE = re.compile(r"^\d{0,2}d\d{1,3}([+-]\d{1,3})?$|^\d{1,3}$")
ATTRIBUTES = ("strength", "dexterity", "constitution", "intelligence", "wisdom", "charisma")
ITEM_TYPES = ("arma", "armadura", "escudo", "poção", "consumível", "pergaminho", "anel", "amuleto", "varinha",
              "ferramenta", "tesouro", "item mágico", "item", "chave", "documento")
CONTEXT_LIMIT = 24000
MAX_PROMPT = 1200


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat()


def _connect(database_path: Path) -> sqlite3.Connection:
    connection = sqlite3.connect(database_path, timeout=10)
    connection.row_factory = sqlite3.Row
    return connection


def init_prep_studio(database_path: Path) -> None:
    with closing(_connect(database_path)) as db, db:
        db.execute(
            "CREATE TABLE IF NOT EXISTS prep_drafts ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, request_id TEXT NOT NULL UNIQUE, kind TEXT NOT NULL, "
            "title TEXT NOT NULL DEFAULT '', status TEXT NOT NULL, prompt TEXT NOT NULL, "
            "payload_json TEXT, preview_path TEXT, error TEXT, applied_json TEXT NOT NULL DEFAULT '[]', "
            "model TEXT, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)")
        db.execute("CREATE TABLE IF NOT EXISTS prep_context (id INTEGER PRIMARY KEY CHECK (id = 1), "
                   "content TEXT NOT NULL, version INTEGER NOT NULL, updated_at TEXT NOT NULL)")
        columns = {row["name"] for row in db.execute("PRAGMA table_info(prep_drafts)")}
        if "session_id" not in columns:
            db.execute("ALTER TABLE prep_drafts ADD COLUMN session_id INTEGER")
        db.execute("CREATE TABLE IF NOT EXISTS prep_session_plans (session_id INTEGER PRIMARY KEY, brief TEXT NOT NULL DEFAULT '', "
                   "outline TEXT NOT NULL DEFAULT '', status TEXT NOT NULL DEFAULT 'draft', error TEXT, model TEXT, "
                   "version INTEGER NOT NULL DEFAULT 0, updated_at TEXT NOT NULL)")
        # A crash mid-generation must not leave drafts spinning forever.
        db.execute("UPDATE prep_drafts SET status='failed', error='Geração interrompida; peça de novo.', updated_at=? "
                   "WHERE status='generating'", (_now(),))
        db.execute("UPDATE prep_session_plans SET status='failed', error='Planejamento interrompido; peça de novo.', updated_at=? "
                   "WHERE status='planning'", (_now(),))


# --- Campaign context (written by the GM or by Claude from the session transcripts) --
def get_context(database_path: Path) -> dict[str, Any]:
    with closing(_connect(database_path)) as db:
        row = db.execute("SELECT content, version, updated_at FROM prep_context WHERE id=1").fetchone()
    return dict(row) if row else {"content": "", "version": 0, "updated_at": None}


def set_context(database_path: Path, content: str, version: int) -> dict[str, Any]:
    content = str(content or "").strip()
    if len(content) > CONTEXT_LIMIT:
        raise ValueError(f"O resumo da campanha deve ter no máximo {CONTEXT_LIMIT} caracteres.")
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT version FROM prep_context WHERE id=1").fetchone()
        current = int(row["version"]) if row else 0
        if int(version) != current:
            raise LookupError("O resumo mudou em outro lugar. Recarregue antes de salvar.")
        db.execute("INSERT INTO prep_context(id, content, version, updated_at) VALUES(1, ?, ?, ?) "
                   "ON CONFLICT(id) DO UPDATE SET content=excluded.content, version=excluded.version, "
                   "updated_at=excluded.updated_at", (content, current + 1, _now()))
    return get_context(database_path)


# --- Drafts ---------------------------------------------------------------------
def _dto(row: sqlite3.Row) -> dict[str, Any]:
    return {"id": row["id"], "request_id": row["request_id"], "kind": row["kind"], "title": row["title"],
            "status": row["status"], "prompt": row["prompt"],
            "payload": json.loads(row["payload_json"]) if row["payload_json"] else None,
            "preview_path": row["preview_path"], "error": row["error"],
            "applied": json.loads(row["applied_json"] or "[]"), "model": row["model"],
            "session_id": row["session_id"] if "session_id" in row.keys() else None,
            "created_at": row["created_at"], "updated_at": row["updated_at"]}


def list_drafts(database_path: Path, *, include_discarded: bool = False, limit: int = 60,
                session_id: int | None = None) -> list[dict[str, Any]]:
    clauses, params = [], []
    if not include_discarded:
        clauses.append("status != 'discarded'")
    if session_id is not None:
        clauses.append("session_id = ?")
        params.append(int(session_id))
    query = "SELECT * FROM prep_drafts" + (" WHERE " + " AND ".join(clauses) if clauses else "")
    with closing(_connect(database_path)) as db:
        rows = db.execute(query + " ORDER BY id DESC LIMIT ?", (*params, max(1, min(int(limit), 200)))).fetchall()
    return [_dto(row) for row in rows]


def get_draft(database_path: Path, draft_id: int) -> dict[str, Any]:
    with closing(_connect(database_path)) as db:
        row = db.execute("SELECT * FROM prep_drafts WHERE id=?", (int(draft_id),)).fetchone()
    if not row:
        raise LookupError("Rascunho não encontrado.")
    return _dto(row)


def create_draft(database_path: Path, *, request_id: str, kind: str, prompt: str,
                 session_id: int | None = None) -> tuple[dict[str, Any], bool]:
    """Return (draft, created). The same request_id never starts a second generation."""
    if not REQUEST_ID_RE.fullmatch(str(request_id or "")):
        raise ValueError("Identificador do pedido inválido.")
    if kind not in KINDS:
        raise ValueError("Tipo de rascunho inválido.")
    prompt = " ".join(str(prompt or "").split())
    if not 3 <= len(prompt) <= MAX_PROMPT:
        raise ValueError(f"Descreva o pedido em 3 a {MAX_PROMPT} caracteres.")
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM prep_drafts WHERE request_id=?", (request_id,)).fetchone()
        if row:
            if row["kind"] != kind or row["prompt"] != prompt:
                raise ValueError("Identificador usado com outro pedido.")
            return _dto(row), False
        now = _now()
        cursor = db.execute("INSERT INTO prep_drafts(request_id, kind, title, status, prompt, session_id, created_at, updated_at) "
                            "VALUES(?, ?, ?, 'generating', ?, ?, ?, ?)",
                            (request_id, kind, f"Gerando {KIND_LABELS[kind]}…", prompt,
                             int(session_id) if session_id is not None else None, now, now))
        row = db.execute("SELECT * FROM prep_drafts WHERE id=?", (cursor.lastrowid,)).fetchone()
        return _dto(row), True


def _finish(database_path: Path, draft_id: int, *, status: str, title: str = "", payload: Any = None,
            preview_path: str | None = None, error: str | None = None, model: str | None = None) -> None:
    with closing(_connect(database_path)) as db, db:
        db.execute("UPDATE prep_drafts SET status=?, title=COALESCE(NULLIF(?, ''), title), payload_json=?, "
                   "preview_path=?, error=?, model=?, updated_at=? WHERE id=? AND status='generating'",
                   (status, title, json.dumps(payload, ensure_ascii=False) if payload is not None else None,
                    preview_path, error, model, _now(), int(draft_id)))


def discard_draft(database_path: Path, draft_id: int) -> dict[str, Any]:
    with closing(_connect(database_path)) as db, db:
        db.execute("UPDATE prep_drafts SET status='discarded', updated_at=? WHERE id=? AND status != 'generating'",
                   (_now(), int(draft_id)))
    return get_draft(database_path, draft_id)


def record_applied(database_path: Path, draft_id: int, *, request_id: str, target: str, ref: str) -> dict[str, Any]:
    """Remember where a draft went (idempotent per request_id). Drafts can be applied many times."""
    if not REQUEST_ID_RE.fullmatch(str(request_id or "")):
        raise ValueError("Identificador do pedido inválido.")
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = db.execute("SELECT * FROM prep_drafts WHERE id=?", (int(draft_id),)).fetchone()
        if not row:
            raise LookupError("Rascunho não encontrado.")
        if row["status"] not in ("ready", "applied"):
            raise ValueError("Só rascunhos prontos podem ser usados.")
        applied = json.loads(row["applied_json"] or "[]")
        if not any(entry.get("request_id") == request_id for entry in applied):
            applied.append({"request_id": request_id, "target": str(target)[:40], "ref": str(ref)[:200], "at": _now()})
        db.execute("UPDATE prep_drafts SET status='applied', applied_json=?, updated_at=? WHERE id=?",
                   (json.dumps(applied[-50:]), _now(), int(draft_id)))
    return get_draft(database_path, draft_id)


# --- Validation: every field the table will use is checked and clamped here -------
def _s(value: Any, limit: int, default: str = "") -> str:
    text = " ".join(str(value if value is not None else default).split())
    return text[:limit]


def _i(value: Any, low: int, high: int, default: int) -> int:
    try:
        number = int(float(str(value).replace(",", ".").split()[0]))
    except (TypeError, ValueError, IndexError):
        return default
    return max(low, min(high, number))


def _dice(value: Any, default: str = "1d6") -> str:
    text = str(value or "").lower().replace(" ", "")
    return text if DICE_RE.fullmatch(text) else default


def _attacks(raw: Any, *, minimum: int = 1) -> list[dict[str, Any]]:
    attacks = []
    for entry in (raw if isinstance(raw, list) else [])[:6]:
        if not isinstance(entry, dict):
            continue
        slot = "ranged" if str(entry.get("slot", "")).lower() in ("ranged", "distancia", "distância", "à distância") else "melee"
        attack = {"name": _s(entry.get("name"), 80, "Ataque") or "Ataque", "bonus": _i(entry.get("bonus"), -5, 30, 1),
                  "damage": _dice(entry.get("damage")), "count": _i(entry.get("count", 1), 1, 6, 1), "slot": slot}
        if slot == "ranged":
            attack["range_m"] = _i(entry.get("range_m"), 3, 300, 30)
        notes = _s(entry.get("notes"), 200)
        if notes:
            attack["notes"] = notes
        attacks.append(attack)
    if len(attacks) < minimum:
        raise ValueError("O rascunho veio sem ataques válidos.")
    return attacks


def _abilities(raw: Any) -> list[dict[str, str]]:
    result = []
    for entry in (raw if isinstance(raw, list) else [])[:8]:
        if isinstance(entry, dict):
            name, text = _s(entry.get("name"), 80), _s(entry.get("description"), 400)
        else:
            name, text = _s(str(entry).split(":")[0], 80), _s(entry, 400)
        if name:
            result.append({"name": name, "description": text})
    return result


def _monster_attacks(data: dict[str, Any], level: int) -> list[dict[str, Any]]:
    raw = data.get("attacks", data.get("ataques"))
    if isinstance(raw, dict):
        raw = [raw]
    attacks = _attacks(raw, minimum=0)
    # A creature always has at least its natural attack; the GM edits it in the draft if needed.
    return attacks or [{"name": "Ataque natural", "bonus": min(level, 15), "damage": "1d6", "count": 1, "slot": "melee"}]


def _cap_monster(monster: dict[str, Any], party: list[dict[str, Any]]) -> dict[str, Any]:
    """Keep a single creature within reach of the group: at most average level + 4 hit dice."""
    levels = [int(m.get("level")) for m in party if str(m.get("level", "")).isdigit()]
    if not levels:
        return monster
    cap = max(1, round(sum(levels) / len(levels))) + 4
    if int(monster["hit_dice"]) <= cap:
        return monster
    hp = round(cap * 4.5)
    monster.update({"hit_dice": str(cap), "average_hp": hp, "hit_points": str(hp),
                    "saving_throw": max(5, 17 - cap // 2), "experience_points": min(int(monster["experience_points"]), cap * 100),
                    "armor_class": min(int(monster["armor_class"]), 12 + cap // 2)})
    for attack in monster["attacks"]:
        attack["bonus"] = min(int(attack["bonus"]), cap)
    return monster


def validate_monster(data: dict[str, Any]) -> dict[str, Any]:
    level = _i(data.get("hit_dice", data.get("level", 1)), 1, 30, 1)
    hp = _i(data.get("average_hp", data.get("hit_points")), 1, 500, max(1, round(level * 4.5)))
    monster = {"name": _s(data.get("name"), 120) or "Criatura", "category": _s(data.get("category"), 60, "Criatura"),
               "size": _s(data.get("size"), 30, "médio"), "alignment": _s(data.get("alignment"), 30, "neutro"),
               "hit_dice": str(level), "average_hp": hp, "hit_points": str(hp),
               "armor_class": _i(data.get("armor_class"), 0, 30, 12), "movement": _i(data.get("movement"), 0, 60, 9),
               "saving_throw": _i(data.get("saving_throw"), 2, 20, 16), "morale": _i(data.get("morale"), 2, 12, 8),
               "experience_points": _i(data.get("experience_points"), 0, 100000, level * 25),
               "treasure": _s(data.get("treasure"), 40, "-"), "attacks": _monster_attacks(data, level),
               "abilities": _abilities(data.get("abilities")), "description": _s(data.get("description"), 600),
               "tactics": _s(data.get("tactics"), 400), "image_prompt": _s(data.get("image_prompt"), 400)}
    monster["id"] = "prep-" + re.sub(r"[^a-z0-9]+", "-", monster["name"].lower()).strip("-")[:60]
    return monster


def validate_npc(data: dict[str, Any]) -> dict[str, Any]:
    raw_attributes = data.get("attributes") if isinstance(data.get("attributes"), dict) else {}
    attributes = {key: _i(raw_attributes.get(key), 3, 20, 10) for key in ATTRIBUTES}
    level = _i(data.get("level"), 1, 20, 1)
    spells = []
    for entry in (data.get("spells") if isinstance(data.get("spells"), list) else [])[:12]:
        if isinstance(entry, dict) and _s(entry.get("name"), 80):
            spells.append({"name": _s(entry.get("name"), 80), "circle": _i(entry.get("circle"), 0, 9, 1),
                           "daily_uses": _i(entry.get("daily_uses", 1), 0, 10, 1)})
    inventory = []
    for entry in (data.get("inventory") if isinstance(data.get("inventory"), list) else [])[:20]:
        if isinstance(entry, dict) and _s(entry.get("name"), 80):
            inventory.append({"name": _s(entry.get("name"), 80), "quantity": _i(entry.get("quantity", 1), 1, 999, 1)})
        elif isinstance(entry, str) and entry.strip():
            inventory.append({"name": _s(entry, 80), "quantity": 1})
    npc = {"name": _s(data.get("name"), 120) or "NPC", "race": _s(data.get("race"), 60, "humano"),
           "class_name": _s(data.get("class_name"), 60, "plebeu"), "level": level,
           "alignment": _s(data.get("alignment"), 30, "neutro"), "attributes": attributes,
           "maximum_hp": _i(data.get("maximum_hp"), 1, 300, 4 + level * 4),
           "armor_class": _i(data.get("armor_class"), 0, 30, 11), "movement": _i(data.get("movement"), 0, 60, 9),
           "saving_throw": _i(data.get("saving_throw"), 2, 20, 15), "base_attack": _i(data.get("base_attack"), 0, 20, 1),
           "initiative": _i(data.get("initiative"), -5, 10, 0), "attacks": _attacks(data.get("attacks")),
           "spells": spells, "inventory": inventory, "abilities": _abilities(data.get("abilities")),
           "coins": {"po": _i((data.get("coins") or {}).get("po") if isinstance(data.get("coins"), dict) else 0, 0, 100000, 0)},
           "personality": _s(data.get("personality"), 400), "appearance": _s(data.get("appearance"), 400),
           "motivation": _s(data.get("motivation"), 400), "secret": _s(data.get("secret"), 400),
           "description": _s(data.get("description"), 600),
           "hooks": [_s(hook, 200) for hook in (data.get("hooks") if isinstance(data.get("hooks"), list) else [])[:5] if _s(hook, 200)],
           "image_prompt": _s(data.get("image_prompt"), 400)}
    return npc


def validate_item(data: dict[str, Any]) -> dict[str, Any]:
    kind = _s(data.get("item_type"), 40, "item").lower()
    return {"name": _s(data.get("name"), 160) or "Item", "item_type": kind if kind in ITEM_TYPES else "item",
            "description": _s(data.get("description"), 1500),
            "effects": [_s(effect, 200) for effect in (data.get("effects") if isinstance(data.get("effects"), list) else [])[:8] if _s(effect, 200)],
            "usable": bool(data.get("usable", False)), "value_po": _i(data.get("value_po"), 0, 1000000, 0),
            "image_prompt": _s(data.get("image_prompt"), 400)}


def validate_map(data: dict[str, Any]) -> dict[str, Any]:
    image_prompt = _s(data.get("image_prompt"), 700)
    if len(image_prompt) < 20:
        raise ValueError("O rascunho do mapa veio sem descrição da imagem.")
    return {"title": _s(data.get("title"), 120) or "Mapa", "description": _s(data.get("description"), 800),
            "areas": [_s(area, 160) for area in (data.get("areas") if isinstance(data.get("areas"), list) else [])[:10] if _s(area, 160)],
            "hazards": [_s(h, 160) for h in (data.get("hazards") if isinstance(data.get("hazards"), list) else [])[:6] if _s(h, 160)],
            "image_prompt": image_prompt}


VALIDATORS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "monster": validate_monster, "npc": validate_npc, "item": validate_item, "map": validate_map}

# Placeholders, not example numbers: models copy example values verbatim.
SCHEMAS = {
    "monster": '{"name":"<nome>","category":"<animal|humanoide|morto-vivo|monstruosidade|...>","size":"<pequeno|médio|grande|enorme>",'
               '"alignment":"<ordeiro|neutro|caótico>","hit_dice":<DV inteiro>,"average_hp":<DV x 4,5 arredondado>,"armor_class":<CA>,'
               '"movement":<metros por turno>,"saving_throw":<JP: 17 menos metade do DV>,"morale":<2-12>,"experience_points":<XP do OD2 para esse DV>,'
               '"treasure":"<tipo de tesouro OD2 ou ->","attacks":[{"name":"<ataque>","bonus":<bônus: DV ou um pouco menos>,"damage":"<dados>",'
               '"count":<ataques por turno>,"slot":"<melee|ranged>"}],"abilities":[{"name":"<habilidade>","description":"<efeito em regras OD2>"}],'
               '"tactics":"<como luta>","description":"<aparência e comportamento>","image_prompt":"<English art prompt>"}',
    "npc": '{"name":"<nome>","race":"<raça>","class_name":"<classe OD2>","level":<nível>,"alignment":"<ordeiro|neutro|caótico>",'
           '"attributes":{"strength":<3-18>,"dexterity":<3-18>,"constitution":<3-18>,"intelligence":<3-18>,"wisdom":<3-18>,"charisma":<3-18>},'
           '"maximum_hp":<PV>,"armor_class":<CA>,"movement":<metros>,"saving_throw":<JP>,"base_attack":<BA>,"initiative":<modificador>,'
           '"attacks":[{"name":"<arma>","bonus":<bônus>,"damage":"<dados>","count":1,"slot":"<melee|ranged>"}],'
           '"spells":[{"name":"<magia>","circle":<círculo>,"daily_uses":<usos>}],"inventory":[{"name":"<item>","quantity":<n>}],'
           '"coins":{"po":<moedas de ouro>},"abilities":[{"name":"<habilidade>","description":"<efeito>"}],"personality":"<jeito>",'
           '"appearance":"<aparência>","motivation":"<o que quer>","secret":"<segredo>","hooks":["<gancho>"],"description":"<resumo>",'
           '"image_prompt":"<English portrait prompt>"}',
    "item": '{"name":"<nome>","item_type":"<arma|armadura|escudo|poção|consumível|pergaminho|anel|amuleto|varinha|ferramenta|tesouro|item mágico|item|chave|documento>",'
            '"description":"<descrição>","effects":["<efeito em regras OD2>"],"usable":<true|false>,"value_po":<preço em PO>,"image_prompt":"<English art prompt>"}',
    "map": '{"title":"<nome do local>","description":"<o que há no mapa>","areas":["<área>"],"hazards":["<perigo>"],'
           '"image_prompt":"<English prompt: top-down battle map, square grid-friendly>"}',
}

SYSTEM = ("Você é o assistente de preparação do Mestre de uma campanha de Old Dragon 2ª edição (OD2, d20, CA crescente, "
          "Jogada de Proteção única, Base de Ataque). Crie conteúdo coerente com a campanha e com o nível do grupo, "
          "usando as regras e números do OD2. Escreva em português do Brasil, exceto image_prompt (em inglês, sem nomes de "
          "obras, marcas ou artistas). Não invente fatos que contradigam o resumo da campanha. Responda SOMENTE com um "
          "objeto JSON no formato pedido, sem texto fora do JSON. Os <...> do formato descrevem o valor: preencha com números reais "
          "e coerentes, nunca copie os textos entre <>. Calibre pelo nível do grupo (Old Dragon, não D&D: nada de CR/ND): uma "
          "criatura comum tem DV perto do nível médio do grupo (capangas: menos), um chefe até nível+3; somando TODAS as "
          "criaturas, um combate médio tem DV total ≈ 3 × nível e um difícil ≈ 5 × nível. Evite dragões e criaturas lendárias para grupos de nível baixo, a menos que o Mestre peça.")


def build_messages(kind: str, prompt: str, *, campaign: str, party: list[dict[str, Any]], existing: list[str]) -> list[dict[str, str]]:
    party_lines = "; ".join(f"{m.get('name')} ({m.get('class_name') or m.get('race') or '?'} nível {m.get('level')})" for m in party)
    context = (f"Grupo atual: {party_lines or 'desconhecido'}.\n"
               f"Já existem na biblioteca (não repita nomes): {', '.join(existing[:80]) or 'nada'}.\n"
               f"Resumo da campanha:\n{campaign[:CONTEXT_LIMIT] or '(sem resumo cadastrado)'}")
    task = (f"Crie um {KIND_LABELS[kind]} para este pedido do Mestre: {prompt}\n"
            f"Formato JSON obrigatório (mesmas chaves, valores reais): {SCHEMAS[kind]}")
    if kind == "npc":
        task += "\nO NPC precisa de ficha completa como a de um personagem jogador: atributos, classe, nível, PV, CA, JP, BA, ataques, magias (se conjurar), inventário e moedas."
    if kind == "map":
        task += ("\nimage_prompt: describe a top-down orthographic tabletop battle map seen from directly above, "
                 "readable at grid scale, painted fantasy style, no text, no labels, no grid lines, no characters.")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": context + "\n\n" + task}]


def _repair_json(raw: str) -> str:
    """Common slips of local models: +3 bonuses, unquoted dice, trailing commas, // comments, <placeholders>."""
    text = re.sub(r"//[^\n\"]*$", "", raw, flags=re.M)
    text = re.sub(r":\s*\+(\d)", r": \1", text)
    text = re.sub(r":\s*(\d+d\d+(?:\s*[+-]\s*\d+)?)\s*([,}\]])", r': "\1"\2', text)
    text = re.sub(r":\s*<[^>\n]*>", ": null", text)
    text = re.sub(r",\s*([}\]])", r"\1", text)
    return text


def _parse_json(text: str) -> dict[str, Any]:
    text = str(text or "").strip()
    text = re.sub(r"^```(?:json)?\s*|\s*```$", "", text)
    candidates = [text]
    match = re.search(r"[\[{].*[\]}]", text, re.S)
    if match:
        candidates.append(match.group(0))
    for raw in candidates:
        for attempt in (raw, _repair_json(raw)):
            try:
                data = json.loads(attempt)
            except json.JSONDecodeError:
                continue
            if isinstance(data, list):  # asked for several creatures at once: keep the first
                data = next((item for item in data if isinstance(item, dict)), None)
            if isinstance(data, dict):
                inner = [value for value in data.values() if isinstance(value, dict)]
                if not (data.keys() & {"name", "title"}) and len(data) == 1 and inner:
                    data = inner[0]  # {"monster": {...}} wrappers
                return data
            raise ValueError("A IA devolveu um formato inesperado.")
    if not re.search(r"\{", text):
        raise ValueError("A IA não devolveu um rascunho em JSON. Tente reformular o pedido.")
    raise ValueError("A IA devolveu um JSON inválido. Tente de novo.")


MAP_STYLE = ("top-down orthographic tabletop RPG battle map seen from directly above, hand-painted dark fantasy, "
             "rich textures, clear walkable areas, no text, no letters, no grid lines, no people, no watermark. ")


def generate(database_path: Path, draft_id: int, *, chat: Callable[[list[dict[str, str]]], tuple[str, str]],
             image: Callable[[str, Path], None] | None, media_root: Path, campaign: str,
             party: list[dict[str, Any]], existing: list[str]) -> None:
    """Runs in a worker thread. Any failure lands on the draft as a readable error."""
    draft = get_draft(database_path, draft_id)
    kind = draft["kind"]
    try:
        messages = build_messages(kind, draft["prompt"], campaign=campaign, party=party, existing=existing)
        text, model = chat(messages)
        try:
            data = _parse_json(text)
        except ValueError:  # one repair round: models sometimes leave a placeholder or a trailing comma
            text, model = chat(messages + [{"role": "assistant", "content": str(text)[:6000]},
                                           {"role": "user", "content": "Esse JSON está inválido. Devolva somente o objeto JSON "
                                            "válido, com números reais no lugar de cada <...>, sem comentários."}])
            try:
                data = _parse_json(text)
            except ValueError:
                (Path(database_path).parent / "prep_last_invalid.txt").write_text(str(text)[:20000], encoding="utf-8")
                raise
        payload = VALIDATORS[kind](data)
        if kind == "monster":
            payload = _cap_monster(payload, party)
        preview = None
        if kind == "map":
            if image is None:
                raise ValueError("Gerador de imagens indisponível para mapas.")
            folder = media_root / "zz_media" / "prep"
            folder.mkdir(parents=True, exist_ok=True)
            stem = re.sub(r"[^a-z0-9]+", "_", payload["title"].lower()).strip("_")[:50] or "mapa"
            raw = folder / f"{stem}_{uuid.uuid4().hex[:8]}.download"
            target = raw.with_suffix(".jpg")
            image(MAP_STYLE + payload["image_prompt"], raw)
            try:
                from PIL import Image
                with Image.open(raw) as picture:
                    picture.convert("RGB").save(target, quality=88, optimize=True)
            finally:
                raw.unlink(missing_ok=True)
            preview = target.relative_to(media_root).as_posix()
        title = payload.get("name") or payload.get("title") or KIND_LABELS[kind]
        _finish(database_path, draft_id, status="ready", title=title, payload=payload, preview_path=preview, model=model)
    except Exception as error:  # noqa: BLE001 - every failure must end the spinner with a reason
        detail = str(error)
        if "4006" in detail or "neurônios" in detail:
            message = "Cota diária do gerador de imagens esgotada (renova às 21h). Gere este mapa de novo depois."
        else:
            message = detail if isinstance(error, ValueError) else f"Falha na geração ({type(error).__name__}: {detail[:160]})."
        _finish(database_path, draft_id, status="failed", title=f"Falhou: {KIND_LABELS[kind]}", error=message[:400])


def start_generation(database_path: Path, draft_id: int, **kwargs: Any) -> threading.Thread:
    worker = threading.Thread(target=generate, args=(database_path, draft_id), kwargs=kwargs,
                              name=f"prep-draft-{draft_id}", daemon=True)
    worker.start()
    return worker


def ollama_chat(base_url: str, model: str, fallback: str) -> Callable[[list[dict[str, str]]], tuple[str, str]]:
    from .ollama_client import OllamaRequestError, chat_with_ollama

    def chat(messages: list[dict[str, str]]) -> tuple[str, str]:
        options = {"num_ctx": 16384, "num_predict": 2400, "temperature": 0.7}
        reasons = []
        for candidate in dict.fromkeys([model, fallback]):
            for response_format in ("json", None):  # some cloud models reject the json format flag
                try:
                    answer = asyncio.run(chat_with_ollama(base_url, candidate, messages, options=options,
                                                          response_format=response_format, request_timeout=240,
                                                          raise_on_error=True))
                except OllamaRequestError as error:
                    reasons.append(f"{candidate}: {error}")
                    continue
                if answer:
                    return answer, candidate
                reasons.append(f"{candidate}: resposta vazia")
        detail = "; ".join(dict.fromkeys(reasons))[:300]
        raise ValueError("A IA local não respondeu (" + detail + "). Confira se o Ollama está aberto.")
    return chat


# --- Preparar sessão: the whole session (outline + its drafts) -----------------------
PLAN_SCHEMA = ('{"title":"","outline":"roteiro em markdown com quebras de linha (\\n): abertura, cenas em ordem (local, objetivo, '
               'conflito, saída), ganchos, recompensas em PO e XP do OD2, plano B","npcs":["pedido curto para gerar o NPC"],"monsters":["pedido curto"],'
               '"items":["pedido curto"],"maps":["pedido curto do mapa de batalha"]}')
PLAN_LIMITS = {"npcs": ("npc", 4), "monsters": ("monster", 4), "items": ("item", 4), "maps": ("map", 3)}
SESSION_RECORD_FIELDS = {"title": 180, "public_summary": 4000, "gm_summary": 4000, "public_chronicle": 12000}


def _plan_dto(row: sqlite3.Row | None, session_id: int) -> dict[str, Any]:
    if not row:
        return {"session_id": session_id, "brief": "", "outline": "", "status": "draft", "error": None, "model": None,
                "version": 0, "updated_at": None}
    return {key: row[key] for key in row.keys()}


def get_plan(database_path: Path, session_id: int) -> dict[str, Any]:
    with closing(_connect(database_path)) as db:
        row = db.execute("SELECT * FROM prep_session_plans WHERE session_id=?", (int(session_id),)).fetchone()
    return _plan_dto(row, int(session_id))


def _session_exists(db: sqlite3.Connection, session_id: int) -> sqlite3.Row:
    row = db.execute("SELECT * FROM game_sessions WHERE id=?", (int(session_id),)).fetchone()
    if not row:
        raise LookupError("Sessão não encontrada.")
    return row


def list_session_plans(database_path: Path) -> list[dict[str, Any]]:
    """Every game session with its preparation: outline status and how many drafts are ready."""
    with closing(_connect(database_path)) as db:
        sessions = db.execute("SELECT id, session_number, title, status, public_summary, gm_summary, public_chronicle, "
                              "private_notes, version FROM game_sessions ORDER BY COALESCE(session_number, id)").fetchall()
        plans = {row["session_id"]: row for row in db.execute("SELECT * FROM prep_session_plans")}
        counts: dict[int, dict[str, int]] = {}
        for row in db.execute("SELECT session_id, kind, count(*) n FROM prep_drafts WHERE session_id IS NOT NULL "
                              "AND status IN ('ready', 'applied', 'generating') GROUP BY session_id, kind"):
            counts.setdefault(row["session_id"], {})[row["kind"]] = row["n"]
    result = []
    for row in sessions:
        record = {key: row[key] for key in row.keys()}
        record["plan"] = _plan_dto(plans.get(row["id"]), row["id"])
        record["draft_counts"] = counts.get(row["id"], {})
        result.append(record)
    return result


def write_plan(database_path: Path, session_id: int, *, outline: str, version: int, brief: str | None = None) -> dict[str, Any]:
    outline = str(outline or "")[:CONTEXT_LIMIT]
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _session_exists(db, session_id)
        current = db.execute("SELECT * FROM prep_session_plans WHERE session_id=?", (int(session_id),)).fetchone()
        if int((current["version"] if current else 0)) != int(version):
            raise ValueError("O roteiro mudou em outro lugar. Recarregue antes de salvar.")
        if current and current["status"] == "planning":
            raise ValueError("A IA ainda está planejando esta sessão.")
        db.execute("INSERT INTO prep_session_plans(session_id, brief, outline, status, version, updated_at) VALUES(?, ?, ?, 'draft', 1, ?) "
                   "ON CONFLICT(session_id) DO UPDATE SET outline=excluded.outline, brief=COALESCE(?, brief), "
                   "status='draft', error=NULL, version=version+1, updated_at=excluded.updated_at",
                   (int(session_id), str(brief or "")[:MAX_PROMPT], outline, _now(), brief))
    return get_plan(database_path, session_id)


def write_session_record(database_path: Path, session_id: int, fields: dict[str, Any], *, version: int) -> dict[str, Any]:
    """GM curation of a session's title and summaries (the 2.0 import is create-only)."""
    updates = {key: str(value or "").strip()[:SESSION_RECORD_FIELDS[key]] for key, value in fields.items()
               if key in SESSION_RECORD_FIELDS and value is not None}
    status = fields.get("status")
    if status is not None:
        if status not in ("planned", "completed"):
            raise ValueError("Use o painel de sessão para iniciar ou pausar.")
        updates["status"] = status
    if not updates:
        raise ValueError("Nada para salvar.")
    if "title" in updates and not updates["title"]:
        raise ValueError("A sessão precisa de um título.")
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        row = _session_exists(db, session_id)
        if int(row["version"]) != int(version):
            raise ValueError("A sessão mudou em outro lugar. Recarregue antes de salvar.")
        clause = ", ".join(f"{key}=?" for key in updates)
        db.execute(f"UPDATE game_sessions SET {clause}, version=version+1 WHERE id=?", (*updates.values(), int(session_id)))
    return next(s for s in list_session_plans(database_path) if s["id"] == int(session_id))


def build_plan_messages(session: dict[str, Any], brief: str, *, campaign: str, party: list[dict[str, Any]],
                        previous: list[dict[str, Any]], existing: list[str]) -> list[dict[str, str]]:
    party_lines = "; ".join(f"{m.get('name')} ({m.get('class_name') or m.get('race') or '?'} nível {m.get('level')})" for m in party)
    history = "\n".join(f"Sessão {p.get('session_number')}: {p.get('title')} — {(p.get('gm_summary') or p.get('public_summary') or '')[:600]}"
                         for p in previous[-4:])
    context = (f"Grupo atual: {party_lines or 'desconhecido'}.\n"
               f"Já existem (reaproveite quando fizer sentido, não duplique nomes): {', '.join(existing[:80]) or 'nada'}.\n"
               f"Últimas sessões:\n{history or '(sem registro)'}\n"
               f"Resumo da campanha:\n{campaign[:CONTEXT_LIMIT] or '(sem resumo cadastrado)'}")
    task = (f"Prepare a sessão {session.get('session_number') or ''} inteira para o Mestre, continuando de onde a última parou. "
            f"Pedido do Mestre: {brief or 'continue a história de forma natural'}\n"
            "Inclua o que a mesa vai precisar: NPCs com quem falar, monstros dos combates, itens/recompensas e mapas dos locais "
            "de combate ou exploração. Cada pedido curto será gerado depois com ficha completa: faça UM pedido por "
            "criatura ou NPC distinto (ex.: 'bandido das sombras, capanga' e 'líder dos bandidos' separados), sem quantidades.\n"
            f"Formato JSON obrigatório: {PLAN_SCHEMA}")
    return [{"role": "system", "content": SYSTEM}, {"role": "user", "content": context + "\n\n" + task}]


def plan_session(database_path: Path, session_id: int, *, request_id: str, brief: str,
                 chat: Callable[[list[dict[str, str]]], tuple[str, str]], generate_kwargs: dict[str, Any],
                 party: list[dict[str, Any]]) -> None:
    """Worker: the AI writes the outline, then every NPC/monster/item/map draft is generated one at a time."""
    try:
        sessions = list_session_plans(database_path)
        session = next(s for s in sessions if s["id"] == int(session_id))
        previous = [s for s in sessions if (s.get("session_number") or 0) < (session.get("session_number") or 0)]
        text, model = chat(build_plan_messages(session, brief, campaign=generate_kwargs.get("campaign", ""), party=party,
                                               previous=previous, existing=generate_kwargs.get("existing", [])))
        data = _parse_json(text)
        raw_outline = data.get("outline")
        if isinstance(raw_outline, list):
            raw_outline = "\n".join(str(line) for line in raw_outline)
        outline = str(raw_outline or "").strip()[:CONTEXT_LIMIT]
        if not outline:
            raise ValueError("A IA não devolveu o roteiro da sessão.")
        title = _s(data.get("title"), 160)
        if title:
            outline = f"# {title}\n\n{outline}"
        with closing(_connect(database_path)) as db, db:
            db.execute("INSERT INTO prep_session_plans(session_id, brief, outline, status, model, version, updated_at) "
                       "VALUES(?, ?, ?, 'generating', ?, 1, ?) ON CONFLICT(session_id) DO UPDATE SET outline=excluded.outline, "
                       "status='generating', error=NULL, model=excluded.model, version=version+1, updated_at=excluded.updated_at",
                       (int(session_id), brief, outline, model, _now()))
        jobs = []
        for key, (kind, limit) in PLAN_LIMITS.items():
            entries = data.get(key) if isinstance(data.get(key), list) else []
            for index, entry in enumerate([_s(e, MAX_PROMPT) for e in entries if _s(e, MAX_PROMPT)][:limit]):
                draft, created = create_draft(database_path, request_id=f"{request_id}:{kind}{index}", kind=kind,
                                              prompt=f"{entry} (para a sessão {session.get('session_number')}: {title})",
                                              session_id=session_id)
                if created:
                    jobs.append(draft["id"])
        for draft_id in jobs:  # sequential: the local model and Flux are shared with the live table
            generate(database_path, draft_id, **generate_kwargs)
        status, error = "ready", None
    except Exception as failure:  # noqa: BLE001
        status = "failed"
        error = str(failure)[:400] if isinstance(failure, (ValueError, LookupError)) else f"Falha no planejamento ({type(failure).__name__})."
    with closing(_connect(database_path)) as db, db:
        db.execute("INSERT INTO prep_session_plans(session_id, brief, status, error, version, updated_at) VALUES(?, ?, ?, ?, 1, ?) "
                   "ON CONFLICT(session_id) DO UPDATE SET status=excluded.status, error=excluded.error, updated_at=excluded.updated_at",
                   (int(session_id), brief, status, error, _now()))


def start_plan(database_path: Path, session_id: int, *, request_id: str, brief: str, **kwargs: Any) -> dict[str, Any] | None:
    """Mark the plan as planning (once per request_id) and run it in the background. None = already running."""
    if not REQUEST_ID_RE.fullmatch(str(request_id or "")):
        raise ValueError("Identificador do pedido inválido.")
    brief = " ".join(str(brief or "").split())[:MAX_PROMPT]
    with closing(_connect(database_path)) as db, db:
        db.execute("BEGIN IMMEDIATE")
        _session_exists(db, session_id)
        current = db.execute("SELECT * FROM prep_session_plans WHERE session_id=?", (int(session_id),)).fetchone()
        if current and current["status"] in ("planning", "generating"):
            return None
        db.execute("INSERT INTO prep_session_plans(session_id, brief, outline, status, version, updated_at) VALUES(?, ?, '', 'planning', 1, ?) "
                   "ON CONFLICT(session_id) DO UPDATE SET brief=excluded.brief, status='planning', error=NULL, "
                   "version=version+1, updated_at=excluded.updated_at", (int(session_id), brief, _now()))
    threading.Thread(target=plan_session, args=(database_path, session_id),
                     kwargs={"request_id": request_id, "brief": brief, **kwargs},
                     name=f"prep-plan-{session_id}", daemon=True).start()
    return get_plan(database_path, session_id)
