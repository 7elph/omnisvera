"""Mapa de ações de monstros e NPCs: tudo que uma criatura pode fazer.

 Junta ataques (com status pronto/incompleto, sem inventar dados), habilidades
 classificadas em passivas x usáveis (com JP, frequência, alcance e dano de
 referência extraídos do texto) e conjuração (magias nomeadas ligadas ao
 grimório + conjuradores por nível). Vale para o bestiário e para NPCs
 custom (sheet de token: attacks + abilities em texto livre).
"""
from __future__ import annotations

import re
import unicodedata

from .spell_catalog import load_spell_catalog


def _key(value: str) -> str:
    return unicodedata.normalize("NFKD", value or "").encode("ascii", "ignore").decode("ascii").casefold()


# Nomes de magia do bestiário -> nomes do grimório (Tomos usam sufixo R de
# reversível e variantes; nada aqui cria magia nova, só aponta a entrada).
SPELL_ALIASES = {
    "causar ferimentos": ["curar ferimentos leves r"],
    "curar ferimentos": ["curar ferimentos leves r"],
    "curar doencas": ["curar doenca r"],
    "curar doenca": ["curar doenca r"],
    "escuridao": ["escuridao,4,5 m"],
    "encantar pessoas": ["enfeiticar pessoas", "encantar pessoas ou mamiferos"],
    "enfeiticar pessoas": ["enfeiticar pessoas", "encantar pessoas ou mamiferos"],
    "remover maldicao": ["remover maldicoes r"],
    "amaldicoar": ["maldicao menor", "maldicao maior"],
    "ilusao": [],
    "sono": ["sono"],
    "medo": ["medo"],
}

_GENERIC_WORDS = {"arvore", "sombras", "genio", "magia", "magias", "efeito", "efeitos"}

_SAVE_RE = re.compile(r"\bJP\s*([DCS])\b", re.IGNORECASE)
_FREQ_RE = re.compile(
    r"(\d+)\s*(?:vez(?:es)?|x)\s*(?:ao dia|por dia|por combate|por semana)|"
    r"uma vez\s*(?:ao dia|por combate|a cada\s*[\d\w\s]+)|"
    r"(\d+)\s*vez\b", re.IGNORECASE)
_RANGE_RE = re.compile(r"(?:até|a|de)\s*(\d+)\s*metros?", re.IGNORECASE)
_DICE_RE = re.compile(r"\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?")
_CASTER_LEVEL_RE = re.compile(
    r"como\s+(?:se fosse\s+)?(?:um[a]?\s+)?(mago|clerigo|sacerdote|necromante|xama|conjurador)(?:\s+xama)?\s*(?:de\s*)?(\d+)[ºo°]?\s*n[íi]vel",
    re.IGNORECASE)
_ARMA_BONUS_RE = re.compile(r"^arma\s*\+(\d+)$", re.IGNORECASE)

_PASSIVE_RE = re.compile(
    r"imun|resist|morto-vivo|vulner|regener|detect|vis[aã]o|sentido|reflet|"
    r"deflex|prote[çc][ãa]o\s*[àa]\s*magia|dissipa", re.IGNORECASE)
_CASTER_FRAME_RE = re.compile(
    r"magias?\s+memorizadas|conjurar|lan[çc]ar\b[^.]{0,40}\bmagias?\b|"
    r"como\s+(?:se fosse\s+)?(?:um[a]?\s+)?(?:mago|cl[eé]rigo|sacerdote|necromante|xam[ãa]|conjurador)|"
    r"magia\s+inata", re.IGNORECASE)
_STRONG_ACTIVE_RE = re.compile(
    r"sopro|baforada|olhar|cuspe|saliva|possess|aura|grito|uivo|esporo|infec|"
    r"maldi[çc]|amald|dreno|invocar|animar|convocar|vez(?:es)?\s*(?:ao dia|por combate|por semana)|"
    r"uma vez\s*(?:ao dia|por combate)|a cada\s*\d+\s*ataques?", re.IGNORECASE)
_WEAK_ACTIVE_RE = re.compile(
    r"veneno|paralis|petrif|\bmedo\b|terror|teia|tinta|\bvoz\b|flauta|g[áa]s|"
    r"neblina|nevoa|\bJP\s*[DCS]\b", re.IGNORECASE)


def _spell_index() -> dict[str, list[dict]]:
    index: dict[str, list[dict]] = {}
    for spell in load_spell_catalog()["spells"]:
        index.setdefault(_key(spell["name"]), []).append(spell)
    return index


def link_spell(name: str) -> list[dict]:
    """Liga um nome de magia do bestiário às entradas do grimório."""
    index = _spell_index()
    candidates = [_key(name), *SPELL_ALIASES.get(_key(name), [])]
    seen: set[str] = set()
    links = []
    for candidate in candidates:
        for spell in index.get(candidate, []):
            if spell["id"] in seen:
                continue
            seen.add(spell["id"])
            links.append({"id": spell["id"], "name": spell["name"],
                          "tradition": spell["tradition"], "circle": spell["circle"]})
    return links


def parse_attack_entry(attack: dict, index: int) -> dict:
    name = str(attack.get("name") or f"Ataque {index + 1}").strip()
    damage = str(attack.get("damage") or "").strip()
    bonus_raw = attack.get("bonus")
    try:
        bonus = int(str(bonus_raw).strip().lstrip("+")) if bonus_raw is not None and str(bonus_raw).strip() not in ("", "None") else None
    except (TypeError, ValueError):
        bonus = None
    entry: dict = {"index": index, "name": name, "bonus": bonus, "damage": damage,
                   "notes": str(attack.get("notes") or "").strip() or None,
                   "count": attack.get("count") or 1}
    riders: list[str] = []
    dice = damage
    match = re.fullmatch(r"(\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?)\s*\+\s*(.+)", damage)
    if match:
        dice, rider = match.groups()
        riders.append(rider.strip())
    if re.fullmatch(r"\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?", dice or "") and bonus is not None:
        entry.update({"status": "ready", "dice": dice.strip(), "riders": riders})
        return entry
    arma = _ARMA_BONUS_RE.match(damage or "")
    entry["damage_bonus"] = int(arma.group(1)) if arma else None
    if riders:
        entry["riders"] = riders
    reason = ("defina o dano da arma no formulário do Mestre"
              if (damage or "").strip().lower().startswith("arma")
              else f"''{damage or 'sem dano'}'' não é rolável — revise no formulário do Mestre")
    if bonus is None:
        reason += "; bônus de ataque ausente"
    entry.update({"status": "incomplete", "reason": reason})
    return entry


def explicit_damage_dice(description: str) -> str | None:
    """Only a die explicitly tied to damage, never duration/chance/images.

    Scaling and compound formulas need a dedicated adapter. This function is
    deliberately conservative; missing evidence is not permission to invent damage.
    """
    formulas = []
    for match in _DICE_RE.finditer(description or ""):
        before = (description or "")[max(0, match.start() - 50):match.start()]
        after = (description or "")[match.end():match.end() + 70]
        if re.match(r"\s*(?:de\s+)?(?:chance|imagens?|rodadas?|turnos?|dias?|horas?|minutos?|por\s+n[íi]vel)", after, re.I):
            continue
        if re.search(r"(?:dano\s*(?:de|igual\s+a)?\s*|caus(?:a|am|ando)\s+)$", before, re.I) or re.match(
            r"\s*(?:pontos?\s+de\s+)?(?:de\s+)?dano\b", after, re.I
        ):
            formulas.append(re.sub(r"\s+", "", match.group(0)).lower())
    distinct = list(dict.fromkeys(formulas))
    return distinct[0] if len(distinct) == 1 else None


def classify_ability(name: str, description: str) -> dict:
    text = f"{name} {description}"
    if _CASTER_FRAME_RE.search(text) and not _PASSIVE_RE.search(text):
        kind = "spellcasting"
    elif _STRONG_ACTIVE_RE.search(text):
        kind = "active"
    elif _PASSIVE_RE.search(text):
        kind = "passive"
    elif _WEAK_ACTIVE_RE.search(text):
        kind = "active"
    else:
        kind = "passive"
    save_match = _SAVE_RE.search(text)
    freq_match = _FREQ_RE.search(text)
    range_match = _RANGE_RE.search(text)
    damage_dice = explicit_damage_dice(description)
    info: dict = {"name": name, "kind": kind,
                  "description": description}
    if save_match:
        info["save"] = f"JP{save_match.group(1).upper()}"
    if freq_match:
        info["frequency"] = re.sub(r"\s+", " ", freq_match.group(0)).strip()
    if range_match:
        info["range_m"] = int(range_match.group(1))
    if damage_dice and kind == "active":
        info["reference_dice"] = damage_dice
    if kind == "spellcasting":
        info["spellcasting"] = parse_spellcasting(description)
    elif kind == "active":
        refs = _scan_named_spells(description)
        if refs:
            info["spell_refs"] = refs
    return info


def _surface_form(description: str, alias: str) -> str:
    words = re.findall(r"[\wÀ-ú]+", description or "")
    parts = alias.split()
    for i in range(len(words) - len(parts) + 1):
        if [_key(word) for word in words[i:i + len(parts)]] == parts:
            return " ".join(words[i:i + len(parts)])
    return alias


def _scan_named_spells(description: str) -> list[dict]:
    """Acha magias do grimório citadas na descrição (nome verbatim ou alias).

    Nada é inventado: só vira link o que existe no catálogo de magias.
    """
    haystack = _key(description or "")
    found: list[dict] = []
    seen: set[str] = set()
    for spell in load_spell_catalog()["spells"]:
        name_key = _key(spell["name"])
        if len(name_key) < 6 and name_key not in ("sono", "medo"):
            continue
        if name_key in _GENERIC_WORDS:
            continue
        if not re.search(r"\b" + re.escape(name_key) + r"\b", haystack):
            continue
        if spell["id"] in seen:
            continue
        seen.add(spell["id"])
        found.append({"mentioned_as": spell["name"],
                      "links": [{"id": spell["id"], "name": spell["name"],
                                 "tradition": spell["tradition"], "circle": spell["circle"]}]})
    for alias, targets in SPELL_ALIASES.items():
        if alias in ("sono", "medo", "ilusao"):
            continue
        if not re.search(r"\b" + re.escape(alias) + r"\b", haystack):
            continue
        for target in targets:
            for spell in load_spell_catalog()["spells"]:
                if _key(spell["name"]) == target and spell["id"] not in seen:
                    seen.add(spell["id"])
                    found.append({"mentioned_as": _surface_form(description, alias),
                                  "links": [{"id": spell["id"], "name": spell["name"],
                                             "tradition": spell["tradition"],
                                             "circle": spell["circle"]}]})
    return found


def parse_spellcasting(description: str) -> dict:
    result: dict = {"named_spells": _scan_named_spells(description),
                    "caster_level": None, "tradition": None}
    level = _CASTER_LEVEL_RE.search(_key(description or ""))
    if level:
        cls, number = level.groups()
        result["caster_level"] = int(number)
        result["tradition"] = "divina" if _key(cls) in ("clerigo", "sacerdote", "xama") else "arcana"
        result["caster_class"] = cls
    return result


def _split_token_ability(raw: str) -> tuple[str, str]:
    text = (raw or "").strip()
    if ":" in text:
        head, tail = text.split(":", 1)
        if len(head.strip()) <= 60:
            return head.strip(), tail.strip()
    return (text[:60] + ("…" if len(text) > 60 else "")), text


def build_action_map(display_name: str, attacks: list, abilities: list, *, monster_id: str | None = None) -> dict:
    """attacks: lista de {name, damage, bonus, ...}; abilities: lista de
    (name, description) — serve ao catálogo e ao sheet de token custom."""
    parsed_attacks = [parse_attack_entry(attack or {}, index) for index, attack in enumerate(attacks or [])]
    parsed_abilities = []
    for ability in abilities or []:
        if isinstance(ability, (list, tuple)):
            ability_name, ability_desc = str(ability[0] or ""), str(ability[1] or "")
        elif isinstance(ability, dict):
            ability_name = str(ability.get("name") or "")
            ability_desc = str(ability.get("description") or "")
        else:
            ability_name, ability_desc = _split_token_ability(str(ability))
        if not ability_name and not ability_desc:
            continue
        parsed_abilities.append(classify_ability(ability_name or "(sem nome)", ability_desc))
    # Non-damaging attacks require a complete native on-hit contract, never dummy dice.
    from .monster_riders import combat_rider_specs
    native = combat_rider_specs({'id': monster_id or display_name, 'attacks': attacks, 'abilities': parsed_abilities})['on_hit']
    for attack in parsed_attacks:
        if attack['status'] == 'incomplete' and _key(attack['damage']) in {'cegueira', 'paralisia', 'especial'}:
            if any(attack['index'] in spec['attack_indices'] and spec['effect'] in {'blinded', 'paralyzed', 'parasite'} for spec in native):
                attack.update(status='ready', effect_only=True, dice=None)
                attack.pop('reason', None)
                if monster_id=='flagelo-da-podridao':
                    from .monster_parasites import DESCRIPTION
                    attack.update(campaign_rule='flagelo-provisional-v1',notes=DESCRIPTION)
    from .monster_contacts import binding
    contact=binding(monster_id)
    if contact and parsed_attacks:
        parsed_attacks[0].update(status='ready',execution_kind='native_contact',native_contact=contact,dice=None)
        parsed_attacks[0].pop('reason',None)
    if monster_id=='morcego' and parsed_attacks:
        parsed_attacks[0].update(status='ready',execution_kind='passive_grid',dice=None,notes='10 morcegos vivos em voo sobre o alvo no grid: −2 nas ações. Regra condicional, sem ataque de dano.')
        parsed_attacks[0].pop('reason',None)
    blockers = []
    for attack in parsed_attacks:
        if attack["status"] == "incomplete":
            blockers.append(f"{attack['name']}: {attack['reason']}")
    if not parsed_attacks:
        blockers.append("sem ataques cadastrados — o Mestre precisa definir ao menos um")
    ready = sum(1 for attack in parsed_attacks if attack["status"] == "ready")
    active = [ability for ability in parsed_abilities if ability["kind"] == "active"]
    passive = [ability for ability in parsed_abilities if ability["kind"] == "passive"]
    casting = [ability for ability in parsed_abilities if ability["kind"] == "spellcasting"]
    return {"name": display_name,
            "summary": {"attacks": len(parsed_attacks), "attacks_ready": ready,
                        "attacks_incomplete": len(parsed_attacks) - ready,
                        "active_abilities": len(active), "passive_abilities": len(passive),
                        "spellcasting": len(casting), "blockers": len(blockers)},
            "attacks": parsed_attacks, "active_abilities": active,
            "passive_abilities": passive, "spellcasting": casting, "blockers": blockers}
