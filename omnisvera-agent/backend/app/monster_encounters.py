"""Editable encounter choices; original SRD records and saved tokens stay intact."""
from copy import deepcopy
import json
from pathlib import Path
import re
from functools import lru_cache


@lru_cache(maxsize=1)
def _profiles():
    return json.loads((Path(__file__).parent / 'data/monster_encounter_defaults.json').read_text(encoding='utf-8'))['profiles']


def encounter_defaults(monster):
    from .item_catalog import load_item_catalog
    from .spell_catalog import get_catalog_spell
    from .dice_rolls import parse_formula
    profile = _profiles().get(monster['id'])
    if monster['id']=='flagelo-da-podridao':
        from .monster_parasites import DESCRIPTION
        return {'kind':'campaign_provisional_rule','label':'Regra provisória da campanha · editável',
                'attacks':deepcopy(monster.get('attacks') or []),
                'abilities':[{'name':'Infestação','description':DESCRIPTION}], 'equipment':[], 'spells':[]}
    if not profile:
        return None
    attacks = deepcopy(monster.get('attacks') or [])
    abilities = deepcopy(monster.get('abilities') or [])
    equipment = []
    variant_label = ''
    if profile.get('variant') == 'nonvenomous':
        variant_label = ' · variante não venenosa'
        attacks[0]['damage'] = '1d3'
        attacks[0]['notes'] = 'Escolha de encontro: serpente não venenosa. Variante venenosa permanece na fonte original.'
        abilities = [a for a in abilities if a.get('name') != 'Veneno']
    if profile.get('weapon_item_id'):
        weapon = next(i for i in load_item_catalog()['items'] if i['id'] == profile['weapon_item_id'])
        base = parse_formula(weapon['dano'])
        for attack in attacks:
            match = re.fullmatch(r'Arma(?:\s*\+(\d+))?', attack.get('damage', ''), re.I)
            if not match:
                continue
            bonus = base.modifier + int(match[1] or 0)
            attack.update(name=weapon['name'], damage=f'{base.count}d{base.sides}' + (f'{bonus:+d}' if bonus else ''),
                          notes=f"Equipamento da campanha: {weapon['name']}; original: {attack['raw']}")
        equipment = [{'id': weapon['id'], 'name': weapon['name'], 'damage': weapon['dano'], 'edition': 'OD1'}]
    spells = []
    for identity in profile.get('spell_ids', []):
        spell = get_catalog_spell(identity)
        if spell is None:
            raise ValueError(f'Magia de encontro ausente: {identity}')
        spells.append({k: spell[k] for k in ('id', 'name', 'circle', 'tradition')})
    if spells:
        names = ', '.join(s['name'] for s in spells)
        for ability in abilities:
            if ability['name'].casefold() in {'magia', 'magias'}:
                ability['description'] += f' Repertório da campanha (editável): {names}.'
    return {'kind': 'campaign_encounter_choices', 'label': 'Configuração da campanha · editável' + variant_label,
            'attacks': attacks, 'abilities': abilities, 'equipment': equipment, 'spells': spells}
