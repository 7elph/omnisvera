"""Reviewed magic item activations on native inventory and fictional time.

No wall-clock worker, new entity model, arbitrary prose execution or healing.
"""
import json
import uuid
from .dice_rolls import roll_formula
from .magic_equipment import identity
from .magic_item_combat import RAPINA, RAPINA_RULES
from .magic_item_rulebook import rules_for
from .magic_item_drums import DRUMS

CUP='item-magico-caneco-do-beberrao'
BOOTS='item-magico-botas-da-velocidade'
SPECS={CUP:{'maximum':3,'slot':'Acessório','consume_mode':'charges'},
       RAPINA:{'maximum':RAPINA_RULES['daily_uses'],'slot':'Armadura','consume_mode':'charges'},
       DRUMS:{'maximum':0,'slot':'Acessório','consume_mode':'none'},
       BOOTS:{'maximum':18000,'slot':'Pés','consume_mode':'none'}}
from .magic_targeted_items import SPECS as TARGETED
SPECS.update(TARGETED)


def spec_for(item):
    key=identity({'item_path':item['item_path']}) if item.get('item_path') else item.get('id')
    return key if key in SPECS else None


def compile_item(item):
    key=item.get('id')
    if key in TARGETED:
        from .magic_targeted_items import compile_item as compile_targeted
        return compile_targeted(item)
    if key not in SPECS:return None
    spec=SPECS[key]
    label=('Preenche o caneco; rola 1d100, três usos por descanso diário.' if key==CUP else
           'CA +3 por 1d4 rodadas; três usos por descanso diário.' if key==RAPINA else
           'Tocar/parar; aura de pânico de 10 m e JPS automática.' if key==DRUMS else
           'Ativa/para movimento ×4; até cinco horas acumuladas por descanso diário.')
    rule={'id':key+':activate','trigger':'on_use','kind':'magic_activation','value':1,
          'label':label,'target':'self','duration':'instant','stacking':'non_stack'}
    armor_rule={'id':key+':armor','trigger':'while_equipped','kind':'armor_class_bonus',
                'value':RAPINA_RULES['armor_class_bonus'],'target':'','stacking':'stack','label':item.get('source') or ''}
    kind='armor' if key==RAPINA else 'accessory'
    return {'catalog_id':key,'item_type':kind,'description':item.get('description') or '',
            'damage_formula':None,'effects':[],'effect_rules':[armor_rule,rule] if key==RAPINA else [rule],'usable':True,'thumbnail':item.get('image_path'),
            'mechanics':{'family_schema':1,'family':'magic_activation','kind':kind,'magical':True,
                'magic_activation_schema':1,'magic_activation_id':key,'equipment_slots':[spec['slot']],
                'approved_equipment_slots':[spec['slot']],'slot_limit':1,'charges_max':spec['maximum'],
                'consume_mode':spec['consume_mode'],'recharge':'none' if key==DRUMS else 'inn_rest','family_gaps':[],
                'activation_mode':'timed' if key==RAPINA else 'toggle' if key in {BOOTS,DRUMS} else 'instant',
                'activation_requires_equipped':key in {RAPINA,BOOTS},
                **({'charge_unit':'fictional_seconds'} if key==BOOTS else {}),
                'source':rules_for(key)['source'] if key in {RAPINA,DRUMS} else 'Old Dragon 1 — Livro Básico Aprimorado, p.146',
                **({'armor_defense':RAPINA_RULES['armor_class_bonus'],'reflect_fraction':RAPINA_RULES['reflect_fraction']} if key==RAPINA else {})}}


def active_effect(snapshot,owner,path):
    return next((e for e in snapshot['effects'] if (e.get('magic_item')==BOOTS or e.get('drum_performance'))
                 and e['target_id']==owner and e.get('item_path')==path),None)


def apply_use(db,snapshot,owner,item,inventory,charges,now,*,options=None,actor_role='gm'):
    key=spec_for(item)
    if key is None:return None
    if inventory['quantity']!=1 and SPECS[key]['consume_mode']!='quantity':
        raise ValueError('Cópias com cargas precisam estar individualizadas; não compartilham um contador')
    if key in TARGETED:
        from .magic_targeted_items import apply
        return apply(db,snapshot,owner,key,item,inventory,charges,now,options,actor_role)
    if options:raise ValueError('Este item não aceita opções adicionais')
    if key==DRUMS:
        from .magic_item_drums import use
        return use(db,snapshot,owner,item,inventory,now)
    if key==RAPINA:
        if not inventory['equipped'] or inventory['equipment_slot']!='Armadura':
            raise ValueError('Equipe a Armadura Leve da Rapina antes de ativar')
        if any(e.get('magic_item')==RAPINA and e.get('target_id')==owner for e in snapshot['effects']):
            raise ValueError('A proteção adicional da Rapina já está ativa')
        duration=roll_formula(RAPINA_RULES['duration_rounds']);turns=int(duration['total'])
        if not 1<=turns<=4:raise ValueError('Duração da Rapina inválida')
        effect={'id':'magic-item:'+uuid.uuid4().hex,'target_type':'character','target_id':owner,
            'label':'Rapina · proteção adicional','source':item.get('name') or inventory['item_title'],
            'duration':'fictional_time','rounds':None,'remaining_seconds':10*turns,'source_duration_unit':'rounds',
            'modifiers':{'armor_class_bonus':RAPINA_RULES['temporary_armor_class_bonus']},
            'magic_item':RAPINA,'item_path':item['item_path'],'inventory_id':inventory['id'],'updated_at':now}
        db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',(effect['id'],'character',owner,json.dumps(effect,ensure_ascii=False)))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        return [{'kind':'magic_activation','magic_item':key,'label':f'CA +3 por {turns} rodadas',
                 'duration_roll':duration,'rounds':turns,'resolved_value':3,'effect_id':effect['id']}]
    if key==CUP:
        die=roll_formula('1d100')
        n=int(die['total'])
        if not 1<=n<=100:raise ValueError('Resultado percentual inválido')
        drink=('Cerveja anã da mais alta qualidade' if n<=10 else 'Cerveja respeitável' if n<=45
               else 'Cerveja de baixa qualidade' if n<=98 else 'Urina de orc')
        return [{'kind':'magic_activation','magic_item':key,'label':drink+' · d100 '+str(n),'roll':die,'resolved_value':1}]
    effect=active_effect(snapshot,owner,item['item_path'])
    if effect:
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(effect['id'],))
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
        return [{'kind':'magic_activation','magic_item':key,'label':'Botas da Velocidade desativadas',
                 'phase':'stop','remaining_seconds':charges,'resolved_value':0}]
    if not inventory['equipped'] or inventory['equipment_slot']!='Pés':
        raise ValueError('Equipe as Botas da Velocidade nos pés antes de ativar')
    if charges<=0:raise ValueError('As cinco horas diárias das Botas da Velocidade acabaram')
    effect={'id':'magic-item:'+uuid.uuid4().hex,'target_type':'character','target_id':owner,
            'label':'Botas da Velocidade','source':item.get('name') or inventory['item_title'],
            'duration':'fictional_time','rounds':None,'remaining_seconds':charges,
            'modifiers':{'movement_multiplier':4},'magic_item':key,'item_path':item['item_path'],
            'inventory_id':inventory['id'],'updated_at':now}
    db.execute('UPDATE player_inventory SET charges_current=?,charges_max=18000,recharge=?,updated_at=? WHERE id=?',
               (charges,'inn_rest',now,inventory['id']))
    db.execute('INSERT INTO combat_effects VALUES(?,?,?,?,1)',
               (effect['id'],'character',owner,json.dumps(effect,ensure_ascii=False)))
    db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return [{'kind':'magic_activation','magic_item':key,'label':'Botas da Velocidade · movimento ×4',
             'phase':'start','remaining_seconds':charges,'resolved_value':4,'effect_id':effect['id']}]


def persist_remaining(db,effect,now):
    if effect.get('magic_item')!=BOOTS:return
    db.execute('UPDATE player_inventory SET charges_current=?,updated_at=? WHERE id=? AND profile_id=? AND item_path=?',
               (effect['remaining_seconds'],now,effect['inventory_id'],effect['target_id'],effect['item_path']))


def prune(db,now):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return
    from .magic_item_drums import prune as prune_drums
    prune_drums(db,now)
    changed=False
    for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.magic_item')=?",(RAPINA,)).fetchall():
        effect=json.loads(row[1])
        item=db.execute('SELECT quantity,equipped,equipment_slot FROM player_inventory WHERE id=? AND profile_id=? AND item_path=?',
                        (effect['inventory_id'],effect['target_id'],effect['item_path'])).fetchone()
        if not item or item[0]!=1 or not item[1] or item[2]!='Armadura':
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(row[0],));changed=True
    for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.magic_item')=?",(BOOTS,)).fetchall():
        effect=json.loads(row[1])
        item=db.execute('SELECT quantity,equipped,equipment_slot,charges_current FROM player_inventory WHERE id=? AND profile_id=? AND item_path=?',
                        (effect['inventory_id'],effect['target_id'],effect['item_path'])).fetchone()
        if not item or item[0]!=1 or not item[1] or item[2]!='Pés':
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(row[0],));changed=True
        elif item[3] is not None:
            remaining=max(0,min(18000,int(item[3])))
            if remaining!=effect['remaining_seconds']:
                effect.update(remaining_seconds=remaining,updated_at=now)
                db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',
                           (json.dumps(effect),int(remaining>0),row[0]));changed=True
    if changed:db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')


def recharge_active(db,cycle,owner,now):
    if cycle!='inn_rest' or not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return
    changed=False
    for row in db.execute("SELECT id,data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.magic_item')=?",(BOOTS,)).fetchall():
        effect=json.loads(row[1])
        if owner is not None and effect['target_id']!=owner:continue
        effect.update(remaining_seconds=18000,updated_at=now)
        db.execute('UPDATE combat_effects SET data_json=? WHERE id=?',(json.dumps(effect),row[0]));changed=True
    if changed:db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
