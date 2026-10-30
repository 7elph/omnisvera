"""Inventário determinístico de prontidão dos catálogos locais do Companion.

Este módulo lê os catálogos já existentes (monstros, magias e itens) e produz
uma fotografia auditável: identificadores estáveis, fonte/edição, imagens,
famílias de ação e lacunas objetivas. Ele não cria regras, não executa ações,
não altera catálogos e não declara automação comprovada.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from typing import Any

from .item_catalog import load_item_catalog, is_catalog_reference, item_offer_readiness
from .monster_actions import build_action_map
from .monster_catalog import load_monster_catalog
from .monster_movement import movement_modes, movement_pending
from .spell_catalog import load_spell_catalog
from .spell_engine import derive_spell_mechanic


SCHEMA_VERSION = 1
HIGHLIGHT_MONSTER_IDS = ("grifo", "dragao-dourado")

_DICE_RE = re.compile(r"\d+\s*[dD]\s*\d+(?:\s*[+-]\s*\d+)?")
_SAVE_RE = re.compile(r"\bJP\s*([DCS])\b", re.IGNORECASE)
_FREQ_RE = re.compile(
    r"(?:\d+\s*vez(?:es)?\s*(?:ao dia|por dia|por combate|por semana)|"
    r"uma vez\s*(?:ao dia|por combate|a cada[^.;]*)|"
    r"recarrega[^.;]*)",
    re.IGNORECASE,
)
_CONE_RE = re.compile(
    r"cone[^.]{0,80}?(\d+)\s*metros?\s*de\s*largura[^.]{0,60}?(\d+)\s*metros?\s*de\s*dist",
    re.IGNORECASE,
)
_LINE_RE = re.compile(r"linha[^.]{0,80}?(\d+)\s*metros?", re.IGNORECASE)
_RADIUS_RE = re.compile(r"raio\s*de\s*(\d+)\s*metros?", re.IGNORECASE)
_DISTANCE_RE = re.compile(r"(\d+)\s*metros?\s*de\s*dist", re.IGNORECASE)

_SPELL_AREA_RE = re.compile(
    r"\bcone\b(?:[^.]{0,80}?\d+\s*metros)?|"
    r"\bcubo\b(?:[^.]{0,60}?\d+\s*metros)?|"
    r"\bcilindro\b(?:[^.]{0,60}?\d+\s*metros)?|"
    r"\besfera\b[^.]{0,80}?\d+\s*metros|"
    r"\blinha\b[^.]{0,80}?\d+\s*metros|"
    r"raio\s+de\s+\d+\s*metros|"
    r"área\s+de\s+efeito|area\s+de\s+efeito|"
    r"\bexplosão\b|\bexplosao\b",
    re.IGNORECASE,
)
_SPELL_MULTI_RE = re.compile(
    r"at[ée]\s+\d+\s+(?:criaturas|alvos|seres|pessoas)|"
    r"\b\d+\s+criaturas\b|"
    r"todos\s+os\s+(?:inimigos|aliados|alvos)|"
    r"um\s+ou\s+mais|várias\s+criaturas|varias\s+criaturas",
    re.IGNORECASE,
)
_SPELL_OFFENSIVE_RE = re.compile(
    r"\b(dano|ferimento|ferimentos|ataque|atacar|matar|morte|destruir|"
    r"explosão|explosao|incendiar|queimar|veneno)\b",
    re.IGNORECASE,
)
_SPELL_COST_RE = re.compile(
    r"(custa[^.;]*|custo[^.;]*|componente\s+material[^.;]*|gasta[^.;]*)",
    re.IGNORECASE,
)
_BREATH_RE = re.compile(r"\b(baforada|sopro)\b", re.IGNORECASE)

_ATTACK_BITE = re.compile(r"mordida|mordidas|presa|presas|dentada|mand[ií]bula", re.IGNORECASE)
_ATTACK_CLAWS = re.compile(r"\bgarra?s?\b", re.IGNORECASE)
_ATTACK_RANGED = re.compile(
    r"arco|besta|funda|pedrada|dardo|azagaia|arremesso|proj[eé]til|"
    r"pistola|mosquete|zarabatana",
    re.IGNORECASE,
)
_ATTACK_WEAPON = re.compile(
    r"arma|espada|machado|lan[cç]a|adaga|clava|martelo|cimitarra|alabarda|"
    r"florete|picareta|sabre|katana|foice|mangual|tridente|a[çc]oite|"
    r"escudo|ma[cç]a|bord[aã]o|cajado",
    re.IGNORECASE,
)

_CONSUMABLE_RE = re.compile(
    r"usos?\s*:\s*[1-9]\d*|po[cç][aã]o|água\s+benta|agua\s+benta|"
    r"frasco|ingredientes|estrepes|kemuridama|hikaridama|giz|"
    r"boneca\s+de\s+vodu|agulhas|cubos\s+de\s+a[cç][úu]car|ma[cç][ãa]s",
    re.IGNORECASE,
)
_TRANSPORT_RE = re.compile(
    r"barco|canoa|navio|carro[cç]a|carruagem|cavalo|montaria|elefante|"
    r"camelo|pônei|ponei",
    re.IGNORECASE,
)
_TABLE_CATEGORIES = {
    "vara-cetro-tabela",
    "tabela-saque-t9-2",
    "arma-caotica-t9-3",
    "arma-ordeira-t9-4",
}
_TABLE_NAME_RE = re.compile(
    r"^(efeito\s+\d+|t9\s+\d+|por\s+exemplo|por\s+copi)|\b\d+[.,]?\d*\s*(?:kg|po|pp|pc)\b",
    re.IGNORECASE,
)
_NON_DESCRIPTIVE_NAME_RE = re.compile(
    r"^\s*[\d.,]+\s*(?:kg|g|po|pp|pc)\b|^\s*(?:efeito|t9)\s+\d+",
    re.IGNORECASE,
)

_ITEM_BUCKET = {
    "arma-corpo": "equipamento",
    "arma-distancia": "equipamento",
    "protecao": "equipamento",
    "kit-basico": "equipamento",
    "kit-explorador": "equipamento",
    "kit-ladrao": "equipamento",
    "especiais": "equipamento",
    "item-classe": "equipamento",
    "propriedades": "transporte_montaria",
    "hospedagem": "servico",
    "servico-magico": "servico",
    "item-magico": "item_magico",
    "item-magico-categoria": "item_magico",
    "vara-cetro-tabela": "item_magico",
    "tabela-saque-t9-2": "item_magico",
    "arma-caotica-t9-3": "item_magico",
    "arma-ordeira-t9-4": "item_magico",
}

_BUCKET_HINTS = {
    "equipamento": ["ferreiro ou armeiro", "loja de aventureiros", "mercado geral"],
    "consumivel": ["boticário ou alquimista", "taverna", "mercado geral"],
    "transporte_montaria": ["estábulo", "doca ou estaleiro", "caravana"],
    "servico": ["estalagem ou taverna", "templo", "círculo arcano"],
    "mercadoria": ["mercado geral", "feira", "guilda local"],
    "item_magico": ["torre arcana", "templo", "antiquário", "tesouro"],
}

_MOVEMENT_SLOTS = {
    "walk": "terrestrial",
    "fly": "fly",
    "swim": "swim",
    "climb": "climb",
    "burrow": "burrow",
}
_SELF_REACH = {"0", "pessoal", "proprio", "o lancador", "lancador"}


def _key(value: Any) -> str:
    text = unicodedata.normalize("NFKD", str(value or ""))
    return text.encode("ascii", "ignore").decode("ascii").casefold().strip()


def _catalog_edition(payload: dict[str, Any]) -> str:
    catalog = payload.get("catalog") or {}
    text = _key(f"{catalog.get('edition', '')} {catalog.get('title', '')}")
    if "old dragon 2" in text or "2a edi" in text or "2a edicao" in text:
        return "OD2"
    return "OD1"


def _catalog_summary(payload: dict[str, Any], total: int) -> dict[str, Any]:
    catalog = payload.get("catalog") or {}
    return {
        "id": catalog.get("id"),
        "title": catalog.get("title"),
        "edition": _catalog_edition(payload),
        "license": catalog.get("license"),
        "count": total,
    }


def _movement(raw: Any) -> dict[str, Any]:
    text = str(raw or "").strip()
    modes = movement_modes(text)
    slots: dict[str, int | float | None] = {
        "terrestrial": None,
        "fly": None,
        "swim": None,
        "climb": None,
        "burrow": None,
    }
    for mode, value in modes.items():
        slot = _MOVEMENT_SLOTS.get(mode)
        if slot is not None:
            slots[slot] = int(value) if float(value).is_integer() else value
    return {
        "raw": text,
        "terrestrial": {"declared": slots["terrestrial"] is not None, "value": slots["terrestrial"]},
        "fly": {"declared": slots["fly"] is not None, "value": slots["fly"]},
        "swim": {"declared": slots["swim"] is not None, "value": slots["swim"]},
        "climb": {"declared": slots["climb"] is not None, "value": slots["climb"]},
        "burrow": {"declared": slots["burrow"] is not None, "value": slots["burrow"]},
        "readable": bool(modes),
        "pending": movement_pending(text),
    }


def _attack_kind(name: str) -> str:
    if _ATTACK_RANGED.search(name):
        return "ranged"
    if _ATTACK_BITE.search(name):
        return "bite"
    if _ATTACK_CLAWS.search(name):
        return "claws"
    if _ATTACK_WEAPON.search(name):
        return "weapon"
    return "other"


def _breath_geometry(text: str) -> dict[str, Any]:
    cone = _CONE_RE.search(text)
    if cone:
        return {"shape": "cone", "width_m": int(cone.group(1)), "length_m": int(cone.group(2)),
                "radius_m": None, "declared": True}
    line = _LINE_RE.search(text)
    if line:
        return {"shape": "line", "width_m": None, "length_m": int(line.group(1)),
                "radius_m": None, "declared": True}
    radius = _RADIUS_RE.search(text)
    if radius:
        return {"shape": "radius", "width_m": None, "length_m": None,
                "radius_m": int(radius.group(1)), "declared": True}
    distance = _DISTANCE_RE.search(text)
    if distance:
        return {"shape": "distance", "width_m": None, "length_m": int(distance.group(1)),
                "radius_m": None, "declared": True}
    return {"shape": None, "width_m": None, "length_m": None, "radius_m": None, "declared": False}


def _breath_weapons(abilities: list[dict[str, Any]]) -> list[dict[str, Any]]:
    entries = []
    for ability in abilities or []:
        name = str(ability.get("name") or "")
        description = str(ability.get("description") or "")
        text = f"{name} {description}"
        if not _BREATH_RE.search(text):
            continue
        dice = _DICE_RE.search(description)
        save = _SAVE_RE.search(text)
        frequency = _FREQ_RE.search(text)
        geometry = _breath_geometry(description)
        gaps = []
        if not dice:
            gaps.append("baforada_sem_dano_literal")
        if not save:
            gaps.append("baforada_sem_jp")
        if not geometry["declared"]:
            gaps.append("baforada_sem_alcance_area")
        if not frequency:
            gaps.append("baforada_sem_recarga")
        entries.append({
            "name": name or "Baforada",
            "damage_dice": dice.group(0) if dice else None,
            "save": f"JP{save.group(1).upper()}" if save else None,
            "frequency": frequency.group(0).strip() if frequency else None,
            "geometry": geometry,
            "description_excerpt": re.sub(r"\s+", " ", description).strip()[:400],
            "gaps": gaps,
        })
    return entries


def _spellcasting(action_map: dict[str, Any]) -> dict[str, Any]:
    entries = []
    for ability in action_map.get("spellcasting") or []:
        info = ability.get("spellcasting") or {}
        named = info.get("named_spells") or []
        gaps = []
        if not named:
            gaps.append("conjuracao_sem_repertorio")
        if info.get("caster_level") is None:
            gaps.append("conjuracao_sem_nivel")
        entries.append({
            "name": ability.get("name"),
            "caster_level": info.get("caster_level"),
            "caster_class": info.get("caster_class"),
            "tradition": info.get("tradition"),
            "named_spells": [
                {"id": link.get("id"), "name": link.get("name"), "circle": link.get("circle")}
                for item in named for link in (item.get("links") or [])
            ],
            "gaps": gaps,
        })
    return {
        "present": bool(entries),
        "entries": entries,
        "repertoire_declared": any(entry["named_spells"] for entry in entries),
    }


def _monster_entry(monster: dict[str, Any], edition: str) -> dict[str, Any]:
    attacks_raw = monster.get("attacks") or []
    abilities_raw = monster.get("abilities") or []
    action_map = build_action_map(str(monster.get("name") or monster.get("id") or ""), attacks_raw, abilities_raw, monster_id=monster.get("id"))

    attacks = []
    kinds = Counter()
    for attack in action_map.get("attacks") or []:
        kind = _attack_kind(str(attack.get("name") or ""))
        kinds[kind] += 1
        gaps = []
        if attack.get("status") != "ready":
            gaps.append("ataque_sem_dano_rolavel")
        if attack.get("bonus") is None:
            gaps.append("ataque_sem_bonus")
        attacks.append({
            "name": attack.get("name"),
            "kind": kind,
            "count": attack.get("count"),
            "bonus": attack.get("bonus"),
            "damage": attack.get("damage"),
            "damage_dice": attack.get("dice"),
            "riders": attack.get("riders") or [],
            "status": attack.get("status"),
            "reason": attack.get("reason"),
            "gaps": gaps,
        })

    breath = _breath_weapons(abilities_raw)
    spellcasting = _spellcasting(action_map)
    movement = _movement(monster.get("movement"))

    image_path = monster.get("image_path")
    attribution = str(monster.get("image_attribution") or "")
    if not image_path:
        image_source = "none"
    elif 'openai imagegen' in attribution.casefold():
        image_source = 'mesa_openai_imagegen'
    elif attribution.casefold().startswith("mesa omnisvera"):
        image_source = "mesa_flux"
    else:
        image_source = "srd_manifest"

    gaps: list[str] = []
    if not attacks:
        gaps.append("sem_ataques_cadastrados")
    for attack in attacks:
        gaps.extend(attack["gaps"])
    for entry in breath:
        gaps.extend(entry["gaps"])
    for entry in spellcasting["entries"]:
        gaps.extend(entry["gaps"])
    if not movement["readable"]:
        gaps.append("movimento_ilegivel")
    if not image_path:
        gaps.append("imagem_ausente")

    blocking = [gap for gap in gaps if gap != "imagem_ausente"]
    preset = monster.get('encounter_defaults')
    configured_actions = build_action_map(monster.get('name') or '', preset['attacks'], preset['abilities'], monster_id=monster.get('id')) if preset else action_map
    configured_casting = _spellcasting(configured_actions)
    return {
        "id": monster.get("id"),
        "name": monster.get("name"),
        "category": monster.get("category"),
        "edition": edition,
        "source_url": monster.get("source_url"),
        "image": {
            "present": bool(image_path),
            "path": image_path,
            "source": image_source,
            "attribution": monster.get("image_attribution"),
            "license": monster.get("image_license"),
        },
        "movement": movement,
        "attacks": attacks,
        "attack_kinds": {
            "bite": kinds.get("bite", 0) > 0,
            "claws": kinds.get("claws", 0) > 0,
            "weapon": kinds.get("weapon", 0) > 0,
            "ranged": kinds.get("ranged", 0) > 0,
            "other": kinds.get("other", 0) > 0,
        },
        "breath_weapons": breath,
        "spellcasting": spellcasting,
        "passive_abilities": [
            {"name": ability.get("name"), "description": ability.get("description")}
            for ability in action_map.get("passive_abilities") or []
        ],
        "active_abilities": [
            {"name": ability.get("name"), "description": ability.get("description")}
            for ability in action_map.get("active_abilities") or []
        ],
        "blockers": action_map.get("blockers") or [],
        "gaps": sorted(set(gaps)),
        "blocking_gaps": sorted(set(blocking)),
        "configuration_complete": not blocking,
        "automation_status": "not_certified",
        "encounter_configuration": {
            "kind": preset.get('kind') if preset else None,
            "attacks_incomplete": configured_actions['summary']['attacks_incomplete'],
            "repertoire_declared": configured_casting['repertoire_declared'],
            "spellcasting_present": configured_casting['present'],
        },
    }


def _spell_family(spell: dict[str, Any], mechanic: dict[str, Any]) -> str:
    text = f"{spell.get('name', '')} {spell.get('description', '')}"
    reach = _key(spell.get("alcance"))
    if _SPELL_AREA_RE.search(text):
        return "area_linha_cone"
    if _SPELL_MULTI_RE.search(text):
        return "multi_alvo"
    if reach in _SELF_REACH:
        return "proprio"
    if reach.startswith("toque"):
        return "toque"
    if not mechanic.get("save") and not mechanic.get("damage") and not _SPELL_OFFENSIVE_RE.search(text):
        return "passiva_assistida"
    return "alvo"


def _spell_entry(spell: dict[str, Any], edition: str) -> dict[str, Any]:
    mechanic = derive_spell_mechanic(spell)
    family = _spell_family(spell, mechanic)
    description = str(spell.get("description") or "")
    cost_match = _SPELL_COST_RE.search(description)
    recharge_match = _FREQ_RE.search(description)
    handler_ready = bool(
        mechanic.get("save") or mechanic.get("damage") or mechanic.get("range_m") or mechanic.get("area")
    )

    gaps: list[str] = []
    reach = str(spell.get("alcance") or "").strip()
    if not reach:
        gaps.append("alcance_ausente")
    elif (
        mechanic.get("range_m") is None
        and _key(reach) not in _SELF_REACH
        and not _key(reach).startswith("toque")
    ):
        gaps.append("alcance_nao_estruturado")
    if family == "area_linha_cone" and not mechanic.get("area"):
        gaps.append("area_textual_nao_estruturada")
    if not cost_match:
        gaps.append("custo_nao_declarado")
    if not recharge_match:
        gaps.append("recarga_nao_declarada")
    if not handler_ready:
        gaps.append("sem_handler_mecanico")

    return {
        "id": spell.get("id"),
        "name": spell.get("name"),
        "edition": edition,
        "source": spell.get("source"),
        "tradition": spell.get("tradition"),
        "circle": spell.get("circle"),
        "school": spell.get("school"),
        "family": family,
        "range_text": reach or None,
        "duration": (spell.get("duracao") or "").strip() or None,
        "save": mechanic.get("save"),
        "save_effect": mechanic.get("save_effect"),
        "damage": mechanic.get("damage"),
        "range_m": mechanic.get("range_m"),
        "handler": {
            "kind": "spell_engine_generic" if handler_ready else "manual_only",
            "mechanic": {
                "save": mechanic.get("save"),
                "save_effect": mechanic.get("save_effect"),
                "damage": mechanic.get("damage"),
                "range_m": mechanic.get("range_m"),
                "range_text": mechanic.get("range_text"),
                "area": mechanic.get("area"),
                "duration": mechanic.get("duration"),
            },
            "automation_status": "not_certified",
        },
        "cost": {
            "declared": bool(cost_match),
            "text": cost_match.group(0).strip() if cost_match else None,
        },
        "recharge": {
            "declared": bool(recharge_match),
            "text": recharge_match.group(0).strip() if recharge_match else None,
        },
        "gaps": sorted(set(gaps)),
    }


def _item_bucket(item: dict[str, Any]) -> tuple[str, str]:
    category = _key(item.get("category"))
    name = str(item.get("name") or "")
    description = str(item.get("description") or "")
    text = f"{name} {description}"
    if category == "propriedades":
        if _TRANSPORT_RE.search(text):
            return "transporte_montaria", "propriedade_de_transporte_ou_montaria"
        return "mercadoria", "propriedade_imovel_ou_ativo"
    if category == "item-classe":
        if _CONSUMABLE_RE.search(text):
            return "consumivel", "item_de_classe_com_uso_limitado"
        return "equipamento", "item_de_classe_permanente"
    bucket = _ITEM_BUCKET.get(category)
    if bucket:
        return bucket, "categoria_mapeada"
    return "mercadoria", "categoria_sem_bucket_explicito"


def _is_table_fragment(item: dict[str, Any]) -> bool:
    # Prices/weights inside the title of a wagon, horse or inn are not fragments.
    return is_catalog_reference(item)


def _item_entry(item: dict[str, Any], edition: str) -> dict[str, Any]:
    bucket, bucket_rule = _item_bucket(item)
    name = str(item.get("name") or "")
    description = str(item.get("description") or "")
    table_fragment = _is_table_fragment(item)
    price = item.get("preco_po")
    price_text = str(item.get("preco") or "").strip()
    offer = item_offer_readiness(item)

    gaps: list[str] = []
    if table_fragment:
        gaps.append("entrada_de_tabela_nao_concreta")
    elif price is None and price_text in ("", "—", "-"):
        gaps.append("preco_ausente")
    if not description.strip():
        gaps.append("descricao_ausente")
    if _NON_DESCRIPTIVE_NAME_RE.search(name):
        gaps.append("nome_nao_descritivo")
    if not item.get("source"):
        gaps.append("fonte_ausente")
    gaps.extend(offer['blocking_gaps'])

    return {
        "id": item.get("id"),
        "name": name,
        "category": item.get("category"),
        "bucket": bucket,
        "bucket_rule": bucket_rule,
        "edition": edition,
        "source": item.get("source"),
        "concrete": not table_fragment,
        "price": price_text or None,
        "price_po": price,
        "negotiable": bool(item.get("negociavel")),
        "weight": item.get("peso"),
        "damage": item.get("dano"),
        "distribution_hints": list(_BUCKET_HINTS.get(bucket, [])),
        "distribution_note": "sugestao_de_estoque_apenas_nao_cria_npc_preco_ou_canon",
        "gaps": sorted(set(gaps)),
        "offer_readiness": offer,
    }


def _counter_dict(counter: Counter) -> dict[str, int]:
    return {str(key): int(value) for key, value in sorted(counter.items(), key=lambda pair: str(pair[0]))}


def build_catalog_readiness(
    *,
    monster_payload: dict[str, Any] | None = None,
    spell_payload: dict[str, Any] | None = None,
    item_payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Monta o inventário completo a partir dos loaders locais ou de fixtures."""
    monsters_payload = monster_payload if monster_payload is not None else load_monster_catalog()
    spells_payload = spell_payload if spell_payload is not None else load_spell_catalog()
    items_payload = item_payload if item_payload is not None else load_item_catalog()

    monster_edition = _catalog_edition(monsters_payload)
    spell_edition = _catalog_edition(spells_payload)
    item_edition = _catalog_edition(items_payload)

    monsters = [
        _monster_entry(monster, monster_edition)
        for monster in monsters_payload.get("monsters") or []
    ]
    spells = [
        _spell_entry(spell, spell_edition)
        for spell in spells_payload.get("spells") or []
    ]
    items = [
        _item_entry(item, item_edition)
        for item in items_payload.get("items") or []
    ]

    monster_attack_total = sum(len(entry["attacks"]) for entry in monsters)
    monster_attack_ready = sum(
        1 for entry in monsters for attack in entry["attacks"] if attack["status"] == "ready"
    )
    monster_attack_incomplete = monster_attack_total - monster_attack_ready

    spell_families = Counter(entry["family"] for entry in spells)
    spell_traditions = Counter(entry["tradition"] for entry in spells)
    spell_circles = Counter(entry["circle"] for entry in spells)
    spell_handlers = Counter(entry["handler"]["kind"] for entry in spells)

    item_buckets = Counter(entry["bucket"] for entry in items)
    item_categories = Counter(entry["category"] for entry in items)

    highlights = [entry for entry in monsters if entry["id"] in HIGHLIGHT_MONSTER_IDS]

    return {
        "schema_version": SCHEMA_VERSION,
        "mode": "local_catalog_inventory",
        "automation_status": "not_certified",
        "catalogs": {
            "monsters": _catalog_summary(monsters_payload, len(monsters)),
            "spells": _catalog_summary(spells_payload, len(spells)),
            "items": _catalog_summary(items_payload, len(items)),
        },
        "counts": {
            "monsters": {
                "total": len(monsters),
                "with_public_description": sum(1 for entry in monsters_payload['monsters'] if entry.get('description')),
                "with_image": sum(1 for entry in monsters if entry["image"]["present"]),
                "without_image": sum(1 for entry in monsters if not entry["image"]["present"]),
                "image_sources": _counter_dict(Counter(entry["image"]["source"] for entry in monsters)),
                "with_attacks": sum(1 for entry in monsters if entry["attacks"]),
                "without_attacks": sum(1 for entry in monsters if not entry["attacks"]),
                "attacks": monster_attack_total,
                "attacks_ready": monster_attack_ready,
                "attacks_incomplete": monster_attack_incomplete,
                "attacks_incomplete_after_encounter_choices": sum(m['encounter_configuration']['attacks_incomplete'] for m in monsters),
                "spellcasting_without_repertoire_after_encounter_choices": sum(m['encounter_configuration']['spellcasting_present'] and not m['encounter_configuration']['repertoire_declared'] for m in monsters),
                "with_breath_weapon": sum(1 for entry in monsters if entry["breath_weapons"]),
                "with_spellcasting": sum(1 for entry in monsters if entry["spellcasting"]["present"]),
                "spellcasting_without_repertoire": sum(
                    1 for entry in monsters
                    if entry["spellcasting"]["present"] and not entry["spellcasting"]["repertoire_declared"]
                ),
                "configuration_complete": sum(1 for entry in monsters if entry["configuration_complete"]),
                "with_blocking_gaps": sum(1 for entry in monsters if entry["blocking_gaps"]),
            },
            "spells": {
                "total": len(spells),
                "by_family": _counter_dict(spell_families),
                "by_tradition": _counter_dict(spell_traditions),
                "by_circle": _counter_dict(spell_circles),
                "by_handler": _counter_dict(spell_handlers),
                "with_generic_handler": spell_handlers.get("spell_engine_generic", 0),
                "manual_only": spell_handlers.get("manual_only", 0),
                "with_declared_cost": sum(1 for entry in spells if entry["cost"]["declared"]),
                "with_declared_recharge": sum(1 for entry in spells if entry["recharge"]["declared"]),
                "with_gaps": sum(1 for entry in spells if entry["gaps"]),
            },
            "items": {
                "total": len(items),
                "by_bucket": _counter_dict(item_buckets),
                "by_category": _counter_dict(item_categories),
                "concrete": sum(1 for entry in items if entry["concrete"]),
                "table_fragments": sum(1 for entry in items if not entry["concrete"]),
                "without_price": sum(1 for entry in items if "preco_ausente" in entry["gaps"]),
                "with_gaps": sum(1 for entry in items if entry["gaps"]),
                "concrete_with_gaps": sum(1 for entry in items if entry['concrete'] and entry['gaps']),
                "commerce_ready": sum(1 for entry in items if entry['offer_readiness']['commerce_ready']),
                "effect_status": _counter_dict(Counter(entry['offer_readiness']['effect_status'] for entry in items)),
            },
        },
        "highlights": {
            "monster_ids": list(HIGHLIGHT_MONSTER_IDS),
            "monsters": highlights,
        },
        "monsters": monsters,
        "spells": spells,
        "items": items,
    }
