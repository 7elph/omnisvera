"""Approved rest-bound optical suppression; item existence and other rules survive."""
import json
import uuid
from copy import deepcopy

MANTLE='item-magico-manto-da-confusao'


def suppressed(db,kind,identity):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return False
    return bool(db.execute("SELECT 1 FROM combat_effects WHERE active=1 AND target_type=? AND target_id=? AND json_extract(data_json,'$.optical_suppression')=1",(kind,identity)).fetchone())


def apply(db,victim,now):
    if suppressed(db,victim['type'],victim['id']):return
    effect={'id':'optical:'+uuid.uuid4().hex,'target_type':victim['type'],'target_id':victim['id'],
        'label':'Óptica suprimida','source':'Pó do Aparecimento','duration':'rest','rounds':None,
        'modifiers':{},'optical_suppression':True,'magic_item':'item-magico-po-do-aparecimento','updated_at':now}
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],victim['type'],victim['id'],json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def project(item):
    if not item.get('_optical_suppressed'):return item
    from .magic_equipment import identity
    if identity(item)!=MANTLE:return item
    result=deepcopy(item)
    for rule in result.get('effect_rules') or []:
        if rule.get('id')=='catalog:'+MANTLE+':fixed-magic':rule['value']=0
    result.setdefault('mechanics',{})['optical_suppressed']=True
    return result
