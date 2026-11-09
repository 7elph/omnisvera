"""OD1 p.75/T7-3 modifiers using the native grid and declared item ceiling.

Only catalog-family weapons with explicit short/max ranges participate.
No map/grid/position means assisted, never a guessed distance. This module
does not extend the existing maximum range or alter campaign power ranges.
"""
import math

POLICY='od1-t7-3-declared-ceiling-v1'


def classify_distance(meters, short_range, maximum):
    if any(type(v) not in (int,float) or not math.isfinite(v) for v in (meters,short_range,maximum)):
        raise ValueError('Distância e alcances precisam de números finitos')
    if meters<0 or short_range<=0 or not short_range<=maximum<=3*short_range:
        raise ValueError('Revise as faixas de alcance da arma')
    if meters>maximum+1e-8:
        raise ValueError('Fora do alcance declarado da arma')
    if meters<3:return 'adjacent',-4
    if meters<=short_range+1e-8:return 'short',0
    if meters<=2*short_range+1e-8:return 'medium',-2
    return 'long',-5


def range_context(db,path,actor_id,attack,inventory,target):
    if (attack.get('slot') or attack.get('id'))!='ranged':return None
    item=next((i for i in inventory if i.get('item_path')==attack.get('weapon_item_path')),None)
    m=(item or {}).get('mechanics') or {}
    if m.get('family_schema')!=1 or m.get('short_range_m') is None or m.get('range_m') is None:return None
    short,maximum=m['short_range_m'],m['range_m']
    classify_distance(0,short,maximum)
    from .spatial_grid import check_attack_range
    checked=check_attack_range(path,actor_character_id=actor_id,target_type=target['type'],target_id=target['id'],slot='ranged',max_range_m=maximum,connection=db,include_context=True)
    result={'policy':POLICY,'weapon_item_path':item['item_path'],'short_range_m':short,'max_range_m':maximum,'checked':checked['checked'],'bonus':0}
    if checked['checked']:
        band,bonus=classify_distance(checked['meters'],short,maximum)
        result.update(meters=checked['meters'],cells=checked['cells'],context=checked['context'],band=band,bonus=bonus)
    else:result['reason']='assisted_without_grid_positions'
    return result


def validate_confirm(db,path,record):
    saved=record['breakdown'].get('item_range')
    if saved is None:return
    if saved.get('policy')!=POLICY:raise ValueError('A regra de alcance mudou; resolva o ataque novamente')
    if saved['checked'] and not saved.get('context'):raise ValueError('Contexto de distância incompleto; resolva novamente')
    # Inventory rules/condition changes are checked by combat's existing fingerprint.
    from .spatial_grid import check_attack_range
    current=check_attack_range(path,actor_character_id=record['actor_character_id'],target_type=record['target_type'],target_id=record['target_id'],slot='ranged',max_range_m=saved['max_range_m'],connection=db,include_context=True)
    if (current['checked']!=saved['checked'] or
            current['checked'] and (current['meters']!=saved['meters'] or current['cells']!=saved['cells'] or current['context']!=saved['context'])):
        raise ValueError('A distância mudou desde a rolagem; resolva o ataque novamente')
