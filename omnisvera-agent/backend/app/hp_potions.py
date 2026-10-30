"""Native S5 HP potion: 1d4, single-use. Preserve physical legacy stacks."""
from copy import deepcopy
import json

CATALOG_ID = 'campanha-pocao-hp'
ITEM_PATH = 'Items/Poção de HP.md'
_RULE = {'id': 'campaign-hp-potion', 'trigger': 'on_use', 'kind': 'heal_hp',
         'target': '', 'formula': '1d4', 'value': 0, 'label': 'Cura 1d4',
         'stacking': 'stack', 'duration': '', 'condition': ''}
_MECHANICS = {'equipment_slots': [], 'damage_formula': '', 'consume_mode': 'quantity',
              'charges_max': 0, 'recharge': 'none', 'slot_limit': 1}


def use_descriptor():
    return {'item_path': ITEM_PATH, 'name': 'Poção de HP', 'item_title': 'Poção de HP',
            'item_type': 'Poção', 'usable': True, 'damage_formula': None,
            'effects': ['Cura 1d4 ao beber'], 'effect_rules': [dict(_RULE)],
            'mechanics': deepcopy(_MECHANICS)}


def catalog_entry():
    return {**use_descriptor(), 'id': CATALOG_ID, 'category': 'campanha-consumivel',
            'native_item_path': ITEM_PATH, 'source_kind': 'campaign',
            'source_ref': ITEM_PATH, 'preco_po': 5, 'preco_origem': 'mesa',
            'description': 'Poção comum da campanha (sessão 5). Restaura 1d4 PV; frasco de uso único.'}


def is_compatible(item):
    """Only this known legacy identity or an explicitly equivalent custom item.

    Never infer a heal from a name/die alone, nor merge charged/modified flasks.
    """
    path = str(item.get('item_path') or '').replace('\\', '/')
    mechanics = item.get('mechanics') or {}
    if item.get('charges_max') or mechanics.get('charges_max') or mechanics.get('consume_mode') in {'charges', 'none'}:
        return False
    if item.get('condition') or item.get('item_condition'):
        return False
    rules = item.get('effect_rules') or []
    known = path == ITEM_PATH or path == 'compendium:' + CATALOG_ID or (path.startswith('merchant:') and path.split(':', 2)[-1] == CATALOG_ID)
    if not known and not (path.startswith('session-item:') and item.get('item_title', item.get('name')) == 'Poção de HP' and item.get('usable')):
        return False
    if rules:
        if len(rules) != 1:
            return False
        rule = rules[0]
        return (rule.get('trigger') == 'on_use' and rule.get('kind') == 'heal_hp'
                and str(rule.get('formula') or '').replace(' ', '').lower() == '1d4'
                and not any(rule.get(k) for k in ('target', 'condition', 'duration', 'effect_category')))
    return known


def normalize(item):
    if not is_compatible(item):
        return dict(item)
    # Keep the physical row identity until the response is coalesced. Never save
    # this read projection back as an administrative quantity assignment.
    return {**item, **{k: v for k, v in use_descriptor().items() if k != 'item_path'},
            'equipment_slot': None, 'equipped': False}


def coalesce_inventory(items):
    result, grouped = [], None
    for item in items:
        if not is_compatible(item):
            result.append(item)
            continue
        if grouped is None:
            grouped = {**normalize(item), 'item_path': ITEM_PATH, 'quantity': 0}
            result.append(grouped)
        grouped['quantity'] += max(0, int(item.get('quantity') or 0))
        if not grouped.get('thumbnail') and item.get('thumbnail'):
            grouped['thumbnail'] = item['thumbnail']
    return result


def stack_sources(db, profile_id):
    """Equivalent physical flasks, usable by consumption and native commerce."""
    sources = []
    rows = db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND quantity>0 ORDER BY CASE WHEN item_path=? THEN 0 ELSE 1 END,id', (profile_id, ITEM_PATH)).fetchall()
    for row in rows:
        item = dict(row)
        path = item['item_path']
        if path.startswith('session-item:'):
            custom = db.execute('SELECT * FROM session_custom_items WHERE id=?', (path.removeprefix('session-item:'),)).fetchone()
            if not custom:
                continue
            item.update(name=custom['name'], item_title=custom['name'], usable=bool(custom['usable']),
                        mechanics=json.loads(custom['mechanics_json'] or '{}'),
                        effect_rules=json.loads(custom['effect_rules_json'] or '[]'))
        if is_compatible(item):
            sources.append(row)
    return sources


def consumption_source(db, profile_id):
    sources = stack_sources(db, profile_id)
    return sources[0] if sources else None
