"""Explicit item contracts; never execute rules inferred from free-form prose."""
from copy import deepcopy
import json
import uuid

NET_ID = 'kit-explorador-rede'
NET = {
    'id': NET_ID, 'name': 'Rede', 'category': 'arma-corpo', 'dano': 'Especial',
    'preco_po': 20, 'peso': '1,5 kg', 'source': 'Old Dragon 1 — Livro Básico Aprimorado, pp. 60, 72–73',
    'description': 'Toque corpo a corpo: constrição, −2 nas jogadas e perda do bônus de DES na CA. Libertação pelo Mestre; a fonte não define teste de escape.',
}
DART = {
    'id': 'arma-distancia-dardo-zarabatana-x20', 'name': 'Dardo de zarabatana x20',
    'category': 'arma-distancia', 'dano': '1d6', 'preco_po': 10, 'peso': '0,1 kg',
    'source': 'Expansão de Itens (Caio Mouriz, CC-BY-SA 4.0), T02-02, p.11',
    'description': 'Pe. Munição de zarabatana; pacote com 20 dardos comuns. Sem efeito especial.',
}


def test_penalty(effects: list[dict]) -> int:
    return -2 if any(e.get('item_special') == 'net' for e in effects) else 0


def dexterity_ac_bonus(attributes: dict, cap: int | None = None) -> int | None:
    value = attributes.get('dexterity')
    if type(value) is not int:
        return None
    from .combat_effects import _attribute_modifier
    modifier = _attribute_modifier(value)
    return min(modifier, cap) if cap is not None else modifier


def net_ac_penalty(effects: list[dict], dexterity_bonus: int | None) -> int:
    nets = [e for e in effects if e.get('item_special') == 'net']
    if not nets:
        return 0
    if dexterity_bonus is None:
        dexterity_bonus = max(e.get('dexterity_ac_bonus', 0) for e in nets)
    return -max(0, dexterity_bonus)


def touch_target_fields(definition: dict, inventory: list[dict] = ()) -> dict:
    effects = definition.get('active_effects') or []
    modifier = dexterity_ac_bonus(definition.get('attributes') or {})
    caps = [i['mechanics']['dexterity_cap'] for i in inventory
            if i.get('equipped') and i.get('quantity', 0) > 0 and 'dexterity_cap' in (i.get('mechanics') or {})]
    capped = min(modifier, min(caps)) if modifier is not None and caps else modifier
    return {'touch_armor_class': None if modifier is None else 10 + modifier + net_ac_penalty(effects, modifier),
            'dexterity_ac_bonus': capped}


def prepare_attack(db, attack: dict, inventory: list[dict], target: dict, *, blood_boost: int = 0, actor_id: str = '', definition: dict | None = None) -> dict:
    item = next((i for i in inventory if i.get('item_path') == attack.get('weapon_item_path')), {})
    special=(item.get('mechanics') or {}).get('special_attack')
    if special=='dart':
        if blood_boost:raise ValueError('Dardo especial não possui dano base para reforçar')
        return {**attack,'damage':'0','effect_only':True,'item_special':'dart'}
    if special=='vibranium':
        from .item_throwing import prepare
        return prepare(db,actor_id,item,target,definition or {},attack)
    if special=='garrote':
        if blood_boost:raise ValueError('Garrote não possui dano inicial para reforçar')
        from .item_grapple import contract
        return {**attack,'damage':'0','effect_only':True,'item_special':'garrote',
                'item_special_contract':contract(db,actor_id,target,attack['weapon_item_path'])}
    if special != 'net':return attack
    if blood_boost:
        raise ValueError('Rede não possui dano para reforçar com sangue')
    if type(target.get('touch_armor_class')) is not int:
        raise ValueError('Rede exige Destreza cadastrada no alvo para calcular a CA de toque')
    return {**attack, 'damage': '0', 'effect_only': True, 'item_special': 'net'}


def validate_net(db, actor_id: str, path: str):
    row = db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?', (actor_id, path)).fetchone()
    active = db.execute("SELECT COUNT(*) FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.item_special')='net' AND json_extract(data_json,'$.item_owner')=? AND json_extract(data_json,'$.item_path')=?", (actor_id, path)).fetchone()[0]
    if not row or not row[1] or row[0] <= active:
        raise ValueError('Rede indisponível: equipe uma rede livre ou liberte o alvo já preso')


def confirm_hit(db, record: dict, now: str) -> dict | None:
    contract = record['breakdown'].get('item_special')
    if not contract or contract['kind']=='vibranium':
        return None
    from .item_defense import intercepted_strikes
    intercepted = intercepted_strikes(record)
    if not any(s['result'] == 'hit' and index not in intercepted for index, s in enumerate(record['breakdown']['strikes'])):
        return None
    if contract['kind']=='garrote':
        from .item_grapple import bind
        return bind(db,record,contract,now)
    effect = {'id': 'item-net:' + uuid.uuid4().hex, 'target_type': record['target_type'],
        'target_id': record['target_id'], 'label': 'Constrito', 'source': 'Rede',
        'duration': 'rest', 'rounds': None, 'modifiers': {}, 'item_special': 'net',
        'item_owner': record['actor_character_id'], 'item_path': contract['item_path'],
        'dexterity_ac_bonus': contract['dexterity_ac_bonus'], 'updated_at': now,
        'condition_description': '−2 nas jogadas; sem bônus de DES na CA. O Mestre encerra ao libertar.'}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',
        (effect['id'], effect['target_type'], effect['target_id'], json.dumps(effect, ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return {'effect_id': effect['id'], 'label': effect['label'], 'roll_penalty': -2}


def validate_confirmation(db, record):
    spec=record['breakdown'].get('item_special')
    from .item_defense import has_tower
    if has_tower(db,record['target_type'],record['target_id']) != bool(record['breakdown'].get('tower_shield')):
        raise ValueError('O escudo do alvo mudou; atualize a resolução')
    if not spec:return
    if spec['kind']=='vibranium':
        from .item_throwing import validate
        from .combat_effects import effect_snapshot
        validate(db,record,effect_snapshot(db))
    elif spec['kind']=='net':
        validate_net(db,record['actor_character_id'],spec['item_path'])
    elif spec['kind']=='garrote':
        row=db.execute('SELECT quantity,equipped FROM player_inventory WHERE profile_id=? AND item_path=?',(record['actor_character_id'],spec['item_path'])).fetchone()
        if not row or row[0]<1 or not row[1]:raise ValueError('Equipe o garrote antes de confirmar')
        from .item_grapple import contract
        current=contract(db,record['actor_character_id'],{'type':record['target_type'],'id':record['target_id'],'server_token_id':spec['victim_pin']},spec['item_path'])
        if current!=spec:raise ValueError('Posição do garrote mudou; confirme novamente')

def attack_intent(request) -> dict:
    intent = request.model_dump(exclude={'request_id'})
    # Preserve retry fingerprints created before this optional field existed.
    for key in ('damage_type','tower_protected_side','ammunition_item_path'):
        if intent.get(key) is None:intent.pop(key,None)
    return intent


def select_damage_type(attack: dict, inventory: list[dict], selected: str | None) -> dict:
    """Only choose among the actual equipped item's physical damage types."""
    item = next((i for i in inventory if i.get('item_path') == attack.get('weapon_item_path')), {})
    mechanics = item.get('mechanics') or {}
    choices = mechanics.get('damage_types') or []
    if choices and selected is None:
        raise ValueError('Escolha o tipo de dano da arma na confirmação do alvo')
    if selected is not None:
        allowed = choices or [mechanics.get('damage_type') or attack.get('damage_type')]
        if selected not in allowed:
            raise ValueError('Este tipo de dano não pertence à arma equipada')
        return {**attack, 'damage_type': selected}
    return deepcopy(attack)
