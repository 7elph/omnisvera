"""Literal metre formulas and source-backed weapon ceilings; no executable prose."""
import math
import re
import unicodedata
from functools import lru_cache


def metre_formula(text):
    """Return (base, per_level), or None for touch/special/unrecognised rules."""
    value=unicodedata.normalize('NFKD', str(text or '').lower())
    value=''.join(c for c in value if not unicodedata.combining(c)).strip().replace(',', '.')
    value=re.sub(r'\bmetros?\b', 'm', value)
    value=re.sub(r'\bpor\s+nivel\b', '/nivel', value)
    number=r'(\d+(?:\.\d+)?)'
    # A bare + nível explicitly means +1 metre per level.
    match=re.fullmatch(number+r'\s*m?\s*\+\s*(?:'+number+r'\s*m?\s*/\s*)?nivel',value)
    if match:return float(match[1]),float(match[2] or 1)
    match=re.fullmatch(r'(?:'+number+r'\s*m?\s*\+\s*)?'+number+r'\s*m?\s*/\s*nivel',value)
    if match:return float(match[1] or 0),float(match[2])
    match=re.fullmatch(number+r'\s*m',value)
    return (float(match[1]),0) if match else None


def resolved_metres(text, level=None):
    formula=metre_formula(text)
    if formula is None:return None
    base, coefficient=formula
    if coefficient and (type(level) is not int or not 1<=level<=100):
        raise ValueError('Defina o nível de conjurador para calcular o alcance desta magia')
    return base+coefficient*(level or 0)


def _key(value):
    return ''.join(c for c in unicodedata.normalize('NFKD',value.casefold()) if not unicodedata.combining(c)).strip()


@lru_cache(maxsize=1)
def _weapon_ranges():
    from .item_catalog import load_item_catalog
    result={}
    for item in load_item_catalog()['items']:
        mechanics=item.get('mechanics') or {}
        maximum=mechanics.get('range_m')
        if mechanics.get('family')=='weapon' and maximum:
            result.setdefault(_key(item['name']), {'mode':'ranged','range_m':maximum,
                'source':item.get('source') or 'Tabela de armas do catálogo', 'catalog_id':item['id']})
    # The monster catalogue is OD2 SRD. Funda is absent from the OD1 item extract;
    # use its literal OD2 equipment rule, keeping monster damage/bonus unchanged.
    result['funda']={'mode':'ranged','range_m':27,
        'source':'https://olddragon.com.br/equipamentos/funda','edition':'Old Dragon 2 SRD'}
    return result


def weapon_range(attack):
    maximum=attack.get('max_range_m',attack.get('range_m'))
    if maximum is not None:
        if type(maximum) not in (int,float) or not math.isfinite(maximum) or maximum<=0:
            raise ValueError('Alcance da arma inválido no cadastro')
        return {'mode':'ranged','range_m':maximum,'source':'Ficha da criatura'}
    return dict(_weapon_ranges().get(_key(str(attack.get('name') or ''))) or {})
