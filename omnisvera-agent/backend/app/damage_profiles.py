"""Source-backed damage metadata; never treats a hit bonus as enchantment."""
from functools import lru_cache
import json
from pathlib import Path
import re
import unicodedata


_TYPES={
    'fire':r'\bfogo\b', 'cold':r'\b(?:frio|gelo)\b',
    'acid':r'\bacid[oa]s?\b', 'lightning':r'\b(?:eletricidade|eletric[oa]s?|relampagos?|raios)\b',
    'poison':r'\bvenen(?:o|os|oso|osa)\b', 'necrotic':r'\bnecroti[ck][oa]\b',
    'slashing':r'\bcortantes?\b', 'piercing':r'\bperfurantes?\b',
    'bludgeoning':r'\b(?:impactantes?|contundentes?)\b', 'physical':r'\bfisic[oa]s?\b',
}


def normalized(text):
    return ''.join(c for c in unicodedata.normalize('NFD',str(text or '').casefold()) if unicodedata.category(c)!='Mn')


def canonical_type(value):
    text=normalized(value)
    if text in _TYPES:return text
    found=[kind for kind,pattern in _TYPES.items() if re.fullmatch(pattern,text)]
    return found[0] if len(found)==1 else None


def infer_damage_type(name,text=''):
    """An explicit offensive clause or unambiguous spell name, not immunity prose."""
    body=normalized(text);clauses=re.split(r'[.;\n]',body)
    offensive=[c for c in clauses if 'dano' in c and not re.search(r'\b(?:nao|nunca|imune|imunidade|resistencia|protecao)\b',c)]
    if not offensive:return None
    relevant=' '.join(offensive)+' '+normalized(name)
    found=[kind for kind,pattern in _TYPES.items() if re.search(pattern,relevant)]
    return found[0] if len(found)==1 else None


@lru_cache(maxsize=1)
def approved_profiles():
    return json.loads(Path(__file__).with_name('data').joinpath('damage_profiles.json').read_text(encoding='utf-8'))


def _catalog_type(item,base_name=None):
    from .item_catalog import load_item_catalog
    candidates={normalized(base_name),normalized(item.get('item_title')),normalized(str(item.get('item_type') or '').split('/')[0]).strip()}
    entry=next((i for i in load_item_catalog()['items'] if i.get('category','').startswith('arma') and normalized(i['name']) in candidates),None)
    prefix=(entry or {}).get('description','').split('–')[0]
    kinds=[kind for kind,code in [('slashing','Co.'),('piercing','Pe.'),('bludgeoning','Im.')] if code in prefix]
    return kinds[0] if len(kinds)==1 else None


def attack_profile(attack,inventory):
    path=str(attack.get('weapon_item_path') or '').replace('\\','/')
    item=next((i for i in inventory if i.get('item_path')==path),{})
    mechanics=item.get('mechanics') or {}
    approved=approved_profiles()['items'].get(path,{})
    hemomancy=attack.get('hemomancy') if isinstance(attack.get('hemomancy'),dict) else None
    kind=attack.get('damage_kind')
    if kind not in {'weapon','spell','effect'}:kind='spell' if path.startswith('spell:') else 'weapon'
    explicit=attack.get('damage_type') or mechanics.get('damage_type') or (hemomancy or {}).get('damage_type')
    damage_type=canonical_type(explicit) or _catalog_type(item,approved.get('base_weapon'))
    damage_type=damage_type or infer_damage_type(attack.get('name',''),str(attack.get('raw') or '')+' '+str(attack.get('notes') or ''))
    if kind=='weapon' and not damage_type:damage_type='physical'
    magical=mechanics.get('magical')
    if magical is None:magical=attack.get('magical')
    if magical is None:magical=approved.get('magical')
    if hemomancy:magical=approved_profiles()['hemomancy']['magical']
    if magical is not None and type(magical) is not bool:raise ValueError('Metadado de arma mágica inválido')
    if magical is None:
        text=normalized(str(item.get('item_type') or '')+' '+str(item.get('description') or ''))
        magical=kind=='spell' or bool(re.search(r'\bmagico\b|\bmagica\b',text) and not re.search(r'\b(?:nao|sem)\b',text))
    material=mechanics.get('material') or attack.get('material')
    if material is None and re.search(r'\b(?:prata|pratead[oa])\b',normalized(item.get('item_title'))):material='silver'
    return {'damage_type':damage_type,'kind':kind,'magical':bool(magical),'material':material,
            'source':'approved-2026-10-25' if approved or hemomancy else 'declared_or_catalog'}


def weapon_defense(monster,context):
    """Only unconditional weapon wards; transformation/HD/magic exceptions stay manual."""
    if context.get('kind')!='weapon' or context.get('magical') is not False:return 1
    for ability in (monster or {}).get('abilities') or []:
        text=normalized(ability.get('description'))
        for clause in re.split(r'[.;\n]',text):
            if not re.search(r'\barmas?\b',clause):continue
            if re.search(r'\b(?:quando|transformad[oa]s?|se|exceto|dados de vida|nivel)\b',clause):continue
            ward=re.search(r'imune ao dano de (?:qualquer )?arma nao magica|nao recebe dano de armas nao magicas|todo dano causado por armas nao magicas|ferid[oa]s? apenas por magia e armas magicas',clause)
            if not ward:continue
            if 'prata' in text and context.get('material')=='silver':
                return .5 if re.search(r'armas de prata causam apenas metade',text) else 1
            return 0
    return 1
