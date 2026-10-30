"""Biblioteca de ações: tudo chama-se ação; blocos cobrem todos os tipos.

 Uma ação = {ref, name, kind, owner, blocks[], costs[], executable, execute}.
 Blocos tipados: attack, save, damage, heal, condition, resource, money,
 manual. Adaptadores: magias do grimório, ataques/usáveis de monstros e
 NPCs (catálogo ou token), técnicas da ficha. Execução despacha para os
 motores existentes (spell_engine, resolve_attack); técnicas seguem nos
 handlers próprios, aqui descritas de forma uniforme.
"""
from __future__ import annotations

import json
import re
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import Any

BLOCK_TYPES = ("attack", "save", "damage", "heal", "condition", "resource", "money", "manual")


def parse_action_ref(ref: str) -> tuple[str, str, str, str]:
    """(library, head, section, key). Ids de token têm ':' — separa pelo
    marcador de seção à direita, nunca pelo primeiro ':'."""
    text = (ref or "").strip()
    if text.startswith("spell:"):
        return ("spell", text[6:], "", "")
    if text.startswith("technique:"):
        head, _, key = text[10:].partition(":")
        return ("technique", head, "", key)
    library = text.split(":", 1)[0]
    if library not in ("monster", "token"):
        raise ValueError("Biblioteca de ação desconhecida")
    for marker, section in ((":attack:", "attack"), (":ability:", "ability")):
        if marker in text:
            left, _, key = text.rpartition(marker)
            return (library, left.split(":", 1)[1], section, key)
    return (library, text.split(":", 1)[1], "", "")


def _manual(text: str) -> dict[str, Any]:
    return {"type": "manual", "text": text}


def _spell_blocks(spell: dict[str, Any]) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    from .spell_engine import derive_spell_mechanic
    mechanic = derive_spell_mechanic(spell)
    blocks: list[dict[str, Any]] = []
    if mechanic["save"]:
        blocks.append({"type": "save", "jp": mechanic["save"],
                       "effect": "halves" if mechanic["save_effect"] == "halves" else "negates"})
    if mechanic["damage"]:
        blocks.append({"type": "damage", "dice": mechanic["damage"],
                       "when": "half on save" if mechanic["save_effect"] == "halves" else "on failed save"})
    if mechanic.get('healing'):
        blocks.append({'type':'heal','dice':mechanic['healing'],'mode':'normal',
                       'target':'single_corporeal_living','range_cells':1})
    blocks.append({"type": "manual",
                   "text": f"Área, duração e narrativa: {(mechanic['area'] or '—')} · {(mechanic['duration'] or '—')} · Mestre adjudica."})
    return blocks, mechanic


def _attack_blocks(entry: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    if entry.get("status") == "ready":
        blocks: list[dict[str, Any]] = [{"type": "attack", "bonus": entry.get("bonus"), "count": entry.get("count") or 1},
                                        {"type": "damage", "dice": entry.get("dice"), "when": "on hit"}]
        for rider in entry.get("riders") or []:
            blocks.append({"type": "manual", "text": f"Rider '{rider}' não automatizado."})
        return blocks, True
    return [_manual(f"Incompleto: {entry.get('reason') or 'revise a ficha'}.")], False


def _ability_blocks(entry: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    kind = entry.get("kind")
    if kind == "passive":
        return [_manual("Passiva: sempre ligada, sem ação."), _manual(entry.get("description") or "")], False
    blocks: list[dict[str, Any]] = []
    if entry.get("save"):
        blocks.append({"type": "save", "jp": entry["save"], "effect": "negates"})
    if entry.get("reference_dice"):
        blocks.append({"type": "damage", "dice": entry["reference_dice"], "when": "reference (on failed save)"})
    casting = entry.get("spellcasting") or {}
    for named in casting.get("named_spells") or []:
        for link in named.get("links") or []:
            blocks.append({"type": "manual",
                           "text": f"Magia '{named.get('mentioned_as')}' → {link['name']} ({link['tradition']} {link['circle']}º)."})
    if casting.get("caster_level") is not None:
        blocks.append({"type": "manual",
                       "text": f"Conjura como {casting.get('caster_class')} de {casting['caster_level']}º ({casting.get('tradition')})."})
    for ref in entry.get("spell_refs") or []:
        for link in ref.get("links") or []:
            blocks.append({"type": "manual",
                           "text": f"Ref: {link['name']} ({link['tradition']} {link['circle']}º)."})
    if not blocks:
        blocks.append(_manual("Sem JP/dano extraível — Mestre adjudica."))
    blocks.append(_manual((entry.get("description") or "")[:500]))
    return blocks, True


def _technique_blocks(entry: dict[str, Any]) -> tuple[list[dict[str, Any]], bool]:
    blocks: list[dict[str, Any]] = [{"type": "manual",
                                    "text": f"[{entry.get('kind', 'technique')}] {entry.get('description') or ''}"[:600]}]
    uses = entry.get("uses") or {}
    if uses.get("resource_key"):
        blocks.append({"type": "resource", "key": uses["resource_key"], "label": uses.get("label") or uses["resource_key"]})
    return blocks, False


def _technique_entry(character_id: str, ability_id: str) -> dict[str, Any]:
    if character_id=='raziel' and ability_id in {'velocidade','reforco'}:
        return {'id':ability_id,'name':'Velocidade' if ability_id=='velocidade' else 'Reforço',
                'kind':'technique','mechanics_status':'structured',
                'description':('1d4 + nível rodadas: +1 ataque, movimento x2 e +2 CA; um uso diário.'
                               if ability_id=='velocidade' else 'BA e dano x2 ou x3 por dois turnos; custa 2 ou 3 de sangue.'),
                'uses':{'resource_key':'velocidade' if ability_id=='velocidade' else 'reserva_de_sangue','cost':1}}
    if character_id == 'dorn7':
        from .dorn_mage import SPEC
        for entry in SPEC['abilities']:
            if entry['id'] == ability_id:
                return entry
        # Metadata lookup only: does not grant an ability or recharge a resource.
        from .approved_spell_pack import dorn_abilities
        for entry in dorn_abilities():
            if entry['id'] == ability_id:
                return entry
    from pathlib import Path as _P
    catalog = json.loads((_P(__file__).resolve().parent / "data" / "session_abilities.json").read_text(encoding="utf-8"))
    if character_id == 'morthak' and ability_id in {'clonagem','magia-da-morte'}:
        # Metadata for existing approved level abilities, never a grant on reads.
        from .level_advancement import NECROMANCER_ABILITIES_5
        entry = next(a for a in NECROMANCER_ABILITIES_5 if a['id']==ability_id)
        return {**entry, 'action_contract':catalog['action_contracts']['morthak'][ability_id]}
    for entry in (catalog.get("characters") or {}).get(character_id, []):
        if entry.get("id") == ability_id:
            return entry
    raise ValueError("Técnica não encontrada na ficha")


def native_action_contract(ref: str, level: int) -> dict | None:
    library, owner, _, key = parse_action_ref(ref)
    # Only these approved adapters are enabled. Catalog text is not executable.
    approved = {'dorn7': {'relampago', 'reflexos', 'forca-arcana', 'teia', 'dissipar-magia'},
                'vezemir': {'forca-arcana', 'velocidade'},
                'morthak': {'clonagem','magia-da-morte'},
                'raziel': {'sangue-defensivo'}}
    if library != 'technique' or key not in approved.get(owner, set()):
        return None
    from .action_contract import resolve_contract
    if owner == 'dorn7' and key != 'relampago':
        from .dorn_mage import SPEC
        definition = SPEC['action_contracts'][key]
        if key=='reflexos':
            definition={**definition,'revision':'dorn-reflexos-campaign-v2',
                        'resolution':{**definition['resolution'],'intercept_chance_percent':90}}
    else:
        definition = _technique_entry(owner, key)['action_contract']
    return {**resolve_contract(definition, level), 'ref':ref}


def lightning_description(contract: dict) -> str:
    return (f"Regra de campanha aprovada: até {contract['targeting']['max_targets']} alvos únicos "
            f"no alcance de {contract['range']['meters']} m. "
            f"Uma rolagem de {contract['resolution']['damage']['formula']}, dividida entre os alvos antes das JP; "
            "restos de divisão vão aos primeiros alvos selecionados. Uma JPD por alvo reduz sua parte à metade. "
            "Recarga 5–6 em 1d6 no início do turno. Sem reflexões automáticas.")


def _monster_source(monster_id: str) -> dict[str, Any]:
    from .monster_catalog import get_catalog_monster
    from .monster_actions import build_action_map
    monster = get_catalog_monster(monster_id)
    if monster is None:
        raise ValueError("Monstro não encontrado no bestiário")
    action_map = build_action_map(
        monster["name"], monster.get("attacks") or [],
        [(ability.get("name") or "", ability.get("description") or "") for ability in monster.get("abilities") or []], monster_id=monster["id"])
    return {"display": monster["name"], "map": action_map}


def _token_source(database_path: Path, token_id: str) -> dict[str, Any]:
    from .monster_actions import build_action_map
    with closing(sqlite3.connect(str(database_path), timeout=30)) as connection:
        connection.row_factory = sqlite3.Row
        row = connection.execute("SELECT name, sheet_json FROM session_workspace_tokens WHERE id=? AND token_type='monster'",
                                 (token_id,)).fetchone()
        if row is None:
            raise ValueError("Criatura não encontrada")
        sheet = json.loads(row["sheet_json"] or "{}")
    origin = sheet.get('source')
    monster_id = origin.get('monster_id') if isinstance(origin, dict) else None
    action_map = build_action_map(row["name"], sheet.get("attacks") or [], sheet.get("abilities") or [], monster_id=monster_id)
    return {"display": row["name"], "map": action_map}


def _find_in_map(action_map: dict[str, Any], section: str, key: str) -> dict[str, Any]:
    if section == "attack":
        entries = action_map["attacks"]
        if key.isdecimal() and int(key) < len(entries):
            return entries[int(key)]
        raise ValueError("Ataque não encontrado")
    pool = action_map["active_abilities"] + action_map["passive_abilities"] + action_map["spellcasting"]
    for entry in pool:
        if entry["name"].casefold() == key.casefold():
            return entry
    raise ValueError("Ação não encontrada")


def describe_action(database_path: Path, ref: str) -> dict[str, Any]:
    """Descreve qualquer ação em blocos. ref: spell:<id> | monster:<id>:attack|ability:<k> |
    token:<id>:attack|ability:<k> | technique:<char>:<ability>."""
    library, head, section, key = parse_action_ref(ref)
    if library == "spell":
        from .spell_catalog import get_catalog_spell
        spell = get_catalog_spell(head)
        if spell is None:
            raise ValueError("Magia não encontrada no grimório")
        blocks, _ = _spell_blocks(spell)
        from .catalog_spell_contracts import catalogue_automation
        automation = catalogue_automation(spell)
        return {"ref": ref, "name": spell["name"], "kind": "spell", "owner": {"type": "grimoire", "id": spell["id"]},
                "blocks": blocks, "costs": [], "executable": automation['status'] != 'blocked', 'automation':automation,
                "execute": {"endpoint": f"/gm/compendium/spells/{spell['id']}/cast", "method": "POST"}}
    if library in ("monster", "token"):
        if library == "monster":
            source = _monster_source(head)
            owner = {"type": "monster", "id": head}
        else:
            source = _token_source(Path(database_path), head)
            owner = {"type": "token", "id": head}
        action_map = source["map"]
        if section == "attack":
            entry = _find_in_map(action_map, "attack", key)
            blocks, executable = _attack_blocks(entry)
            kind = "attack"
        else:
            entry = _find_in_map(action_map, "ability", key)
            blocks, executable = _ability_blocks(entry)
            kind = "usable" if entry.get("kind") in ("active", "spellcasting") else "passive"
        label = entry.get("name", key)
        return {"ref": ref, "name": f"{source['display']} · {label}", "kind": kind, "owner": owner,
                "blocks": blocks, "costs": [], "executable": executable,
                "execute": ({"endpoint": f"/gm/workspace/tokens/{owner['id']}/actions/execute" if library == "token" else None,
                             "method": "POST"} if executable and library == "token" else None),
                "note": "Pine a criatura para executar magias do bestiário em um token." if library == "monster" else None}
    if library == "technique":
        entry = _technique_entry(head, key)
        blocks, _ = _technique_blocks(entry)
        if ((head == 'vezemir' and key in {'forca-arcana', 'velocidade'})
                or (head == 'morthak' and key in {'clonagem','magia-da-morte'})
                or (head == 'raziel' and key == 'sangue-defensivo')):
            with closing(sqlite3.connect(str(database_path), timeout=30)) as db:
                override = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (head,)).fetchone()
                sheet = db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?', (head,)).fetchone()
            level = ((json.loads(override[0]).get('level') if override else None)
                     or ((json.loads(sheet[0]).get('character_class') or {}).get('level') if sheet else None) or 1)
            contract = native_action_contract(ref, int(level))
            cost = contract['costs'][0]
            return {'ref': ref, 'name': entry['name'], 'kind': entry['kind'],
                    'owner': {'type': 'character', 'id': head}, 'contract': contract,
                    'blocks': [{'type': 'condition', **contract['resolution']},
                               {'type': 'resource', 'key': cost['key'], 'amount': cost['amount'],
                                'label': (entry.get('uses') or {}).get('label') or cost['key']}],
                    'costs': contract['costs'], 'executable': False,
                    'execute': {'endpoint': f'/characters/{head}/techniques/{key}', 'method': 'POST',
                                'note': 'Executor nativo; não usa a rota genérica de ações.'}}
        if head == 'dorn7' and key in {'relampago', 'reflexos', 'forca-arcana', 'teia', 'dissipar-magia'}:
            with closing(sqlite3.connect(str(database_path), timeout=30)) as db:
                row = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(head,)).fetchone()
            level = int(json.loads(row[0]).get('level') or 3) if row else 3
            contract = native_action_contract(ref,level)
            if key == 'relampago':
                blocks = [{'type':'save','jp':'JPD','effect':'halves'},
                          {'type':'damage','dice':contract['resolution']['damage']['formula'],'shared':True}]
            else:
                resolution = contract['resolution']
                blocks = [{'type':'condition', **resolution}]
                if key == 'reflexos':
                    blocks = [{'type':'condition', 'effect':'mirror_images',
                               'images':resolution['images'], 'duration':resolution['lifetime']}]
            return {'ref':ref,'name':entry['name'],'kind':entry['kind'],
                    'owner':{'type':'character','id':head},'contract':contract,
                    'blocks':blocks,
                    'costs':contract['costs'],'executable':False,
                    'execute':{'endpoint':'/gm/combat/effects','method':'POST',
                               'action':'dorn_spell_cast','payload':{'spell_id':key},
                               'note':'Executor nativo; não usa a rota genérica de ações.'}}
        return {"ref": ref, "name": entry.get("name") or key, "kind": entry.get("kind") or "technique",
                "owner": {"type": "character", "id": head}, "blocks": blocks, "costs": [],
                "executable": False,
                "execute": {"endpoint": f"/characters/{head}/techniques/{entry.get('id')}", "method": "POST",
                            "note": "Handlers próprios da ficha; migram para blocos na fase 2."}}
    raise ValueError("Biblioteca de ação desconhecida")


def execute_action(database_path: Path, ref: str, *, targets: list[dict[str, str]], roll_mode: str = "digital",
                   d20: int | list[int] | None = None, damage_override: str | None = None,
                   save_override: str | None = None, range_m: float | None = None, range_cells: int | None = None,
                   caster_type: str | None = None, caster_id: str | None = None,
                   request_id: str | None = None) -> dict[str, Any]:
    """Executa ações de grimório e de tokens; demais refs descrevem o caminho."""
    from .spell_command_receipts import command_receipt
    command_receipt(request_id, 'action-library', {'ref': ref})  # validate before any write
    described = describe_action(database_path, ref)
    if not described["executable"]:
        raise ValueError("Esta ação não executa direto; use o caminho indicado em 'execute'.")
    library, head, section, key = parse_action_ref(ref)
    if library == "spell":
        from .spell_engine import cast_spell
        if not caster_type or not caster_id:
            raise ValueError("Informe o conjurador (caster_type/caster_id)")
        return {"action": described, "result": cast_spell(
            database_path, spell_id=head, caster_type=caster_type, caster_id=caster_id,
            targets=targets, roll_mode=roll_mode, d20=d20, damage_override=damage_override,
            save_override=save_override, range_m=range_m, range_cells=range_cells, request_id=request_id)}
    if library == "token":
        token_id = head
        if section == "attack":
            return {"action": described, "result": _execute_token_attack(
                database_path, token_id, key, targets, roll_mode, d20, range_m, range_cells, request_id)}
        from .spell_engine import execute_token_action
        ability = _find_in_map(_token_source(Path(database_path), token_id)["map"], "ability", key)
        return {"action": described, "result": execute_token_action(
            database_path, token_id=token_id, ability_name=ability["name"], targets=targets,
            roll_mode=roll_mode, d20=d20, damage_override=damage_override,
            range_m=range_m, range_cells=range_cells, request_id=request_id)}
    raise ValueError("Biblioteca de ação desconhecida")


def _execute_token_attack(database_path: Path, token_id: str, attack_index: str, targets: list[dict[str, str]],
                          roll_mode: str, d20: int | list[int] | None,
                          range_m: float | None = None, range_cells: int | None = None,
                          request_id: str | None = None) -> dict[str, Any]:
    import uuid
    from datetime import datetime, timezone
    from .action_range import enforce_action_range
    from .combat import confirm_attack_resolution, monster_attack_definition, resolve_attack
    from .session_workspace import list_workspace_tokens
    database_path = Path(database_path)
    token = next((item for item in list_workspace_tokens(database_path) if item["id"] == token_id), None)
    if token is None or token.get("token_type") != "monster":
        raise ValueError("Criatura não encontrada")
    definition = monster_attack_definition(token, attack_index)
    if len(targets) != 1:
        raise ValueError("Ataque direto mira um alvo por vez")
    item = targets[0]
    if range_m is not None or range_cells is not None:
        enforce_action_range(database_path, attacker_token_id=token_id, target_type=item["type"], target_id=item["id"],
                             mode="ranged" if range_cells != 1 else "melee",
                             range_m=range_m, range_cells=range_cells)
    if item["type"] == "token":
        from .combat_effects import readeffects
        from .session_workspace import list_workspace_tokens
        token_target = next((entry for entry in list_workspace_tokens(database_path) if entry["id"] == item["id"]), None)
        if token_target is None or token_target.get("token_type") == "location":
            raise ValueError("Alvo não encontrado")
        sheet = token_target.get("sheet") or {}
        base_ac = sheet.get("armor_class")
        effect_ac = sum(effect.get("modifiers", {}).get("armor_class_bonus", 0)
                        for effect in readeffects(database_path)["effects"]
                        if effect["target_type"] == "token" and effect["target_id"] == item["id"])
        target = {"type": "token", "id": str(token_target["id"]), "name": str(token_target.get("name") or "Criatura"),
                  "armor_class": None if base_ac is None else base_ac + effect_ac,
                  "current_hp": token_target.get("current_hp"), "maximum_hp": token_target.get("maximum_hp")}
    else:
        try:
            from .main import _combat_target
            from .combat import CombatNotFoundError
            try:
                target = _combat_target(item["type"], item["id"])
            except CombatNotFoundError as error:
                raise ValueError(str(error)) from error
        except ImportError as error:
            raise ValueError("Alvo de combate indisponível") from error
    if target["type"] == "token" and target["id"] == token_id:
        raise ValueError("Escolha outro alvo")
    request_id = request_id or f"library-{uuid.uuid4().hex[:16]}"
    dice = [int(value) for value in (d20 if isinstance(d20, list) else [d20])] if roll_mode == "physical" else None
    if roll_mode == "physical" and (not dice or any(not 1 <= value <= 20 for value in dice)):
        raise ValueError("Informe o d20 físico (1-20)")
    resolution, _ = resolve_attack(
        database_path, request_id=request_id, actor_character_id=token_id, actor_name=token["name"],
        requested_by_id="master", requested_by_role="gm", controlling_character_id=None,
        guard_effect_id=None, definition=definition, inventory=[], attack_id=attack_index, target=target,
        roll_mode=roll_mode, physical_d20=dice[0] if dice else None, attack_count=1, physical_d20s=None)
    confirmed, _ = confirm_attack_resolution(
        database_path, resolution_id=resolution["resolution_id"], requested_by_id="master", requested_by_role="gm",
        now=datetime.now(timezone.utc))
    return confirmed
