"""Scoped payload repair for the existing daily ring. No grants, recharge or inferred RPG rules."""
from copy import deepcopy
import unicodedata


def repair_payload(item):
    name=''.join(c for c in unicodedata.normalize('NFD',str(item.get('name') or '').casefold())
                 if unicodedata.category(c)!='Mn').strip()
    mechanics=item.get('mechanics') or {}
    rules=item.get('effect_rules') or []
    if (name!='anel runico' or not item.get('usable') or mechanics.get('charges_max')!=1 or
        mechanics.get('recharge')!='inn_rest' or len(rules)!=1 or rules[0].get('trigger')!='on_use' or
        rules[0].get('kind')!='heal_hp' or rules[0].get('value')!=4 or rules[0].get('formula')):
        raise ValueError('Not the approved existing daily runic ring; review its contract instead of inferring rules')
    fields=('name','item_type','description','effects','effect_rules','mechanics','usable','image_path')
    payload={field:deepcopy(item.get(field)) for field in fields}
    payload['mechanics']['consume_mode']='charges'
    return payload
