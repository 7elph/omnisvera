"""Adamas uses the four basic-book sword profiles and native instance conditions."""
import json
import sqlite3
from contextlib import closing
from copy import deepcopy
from .magic_equipment import identity

ID='item-magico-espada-adamas'
FORMS={
 'arma-corpo-espada-curta':{'name':'Espada curta','damage':'1d6','weight':'1,5 kg'},
 'arma-corpo-espada-longa':{'name':'Espada longa','damage':'1d8','weight':'2 kg'},
 'arma-corpo-espada-bastarda':{'name':'Espada bastarda','damage':'1d10','weight':'2,8 kg'},
 'arma-corpo-espada-larga':{'name':'Espada larga','damage':'2d6','weight':'7 kg'}}
DEFAULT='arma-corpo-espada-curta'
ENHANCEMENT_ID='catalog:'+ID+':embedded-damage-enchantment'


def compile_item(item):
 if item.get('id')!=ID:return None
 return {'catalog_id':ID,'item_type':'weapon','description':item.get('description',''),
  'damage_formula':'1d6+4','effects':[],'effect_rules':[],'usable':False,'thumbnail':item.get('image_path'),
  'mechanics':{'family_schema':1,'family':'weapon','kind':'weapon','magical':True,
   'magic_form_schema':1,'magic_form_id':ID,'weapon_form_id':DEFAULT,
   'enchantment_bonus':4,
   'embedded_enhancement_rules':[{'id':ENHANCEMENT_ID,'trigger':'while_equipped','kind':'damage_bonus',
       'target':'melee','value':4,'label':'Encantamento Adamas · dano embutido na fórmula'}],
   'rust_profile':{'material':'metal','magical':True,'enchantment_bonus':4,'enhancement_rule_ids':[ENHANCEMENT_ID]},
   'weapon_forms':[{'id':key,**value} for key,value in FORMS.items()],
   'damage_formula':'1d6+4','damage_type':'slashing','critical_threshold':18,'critical_multiplier':2,
   'equipment_slots':['Corpo a corpo'],'approved_equipment_slots':['Corpo a corpo'],
   'attack_modes':['melee'],'slot_limit':1,'charges_max':0,'consume_mode':'none','recharge':'none',
   'weight':FORMS[DEFAULT]['weight'],'family_gaps':[],'source':item.get('source')}}


def project(item,condition):
 if identity(item)!=ID:return item
 form=(condition or {}).get('magic_form') or DEFAULT
 if not isinstance(form,str) or form not in FORMS:raise ValueError('Forma persistida da Adamas inválida')
 result=deepcopy(item);spec=FORMS[form]
 bonus=4
 if (condition or {}).get('kind')=='rust' and ENHANCEMENT_ID in (condition.get('enhancement_rule_ids') or []):
  bonus=max(0,4-max(0,int(condition.get('original_bonus',0))-int(condition.get('bonus_remaining',0))))
 result['damage_formula']=spec['damage']+(f'+{bonus}' if bonus else '')
 result['mechanics']={**result.get('mechanics',{}),'weapon_form_id':form,
     'damage_formula':result['damage_formula'],'weight':spec['weight']}
 from .item_catalog import get_catalog_item
 from .item_dimensions import METADATA_FIELDS
 physical=(get_catalog_item(form) or {}).get('mechanics') or {}
 result['mechanics'].update({key:physical[key] for key in METADATA_FIELDS if key in physical})
 return result


def command(path,*,owner,actor,role,request_id,payload):
 if role!='gm' and actor!=owner:raise PermissionError('Esta arma não pertence ao personagem')
 if not request_id or len(request_id)>120:raise ValueError('Informe uma chave idempotente')
 if set(payload)!={'item_path','form_id'} or not isinstance(payload['form_id'],str) or payload['form_id'] not in FORMS:
  raise ValueError('Escolha uma espada do livro básico')
 if not isinstance(payload['item_path'],str) or not 1<=len(payload['item_path'])<=1000:raise ValueError('Item inválido')
 from .combat_effects import init_effects
 from .inventory_conditions import init_schema,read_condition,save_condition
 from .character_play import _now,_write_event
 from .session_ledger import append_session_ledger_event
 init_effects(path)
 fingerprint=json.dumps(['weapon_form',owner,actor,role,payload],sort_keys=True)
 with closing(sqlite3.connect(path,timeout=30)) as db,db:
  db.row_factory=sqlite3.Row;db.execute('BEGIN IMMEDIATE')
  receipt=db.execute('SELECT fingerprint,response_json FROM combat_effect_commands WHERE request_id=?',(request_id,)).fetchone()
  if receipt:
   if receipt[0]!=fingerprint:raise ValueError('Requisição pertence a outra ação')
   return json.loads(receipt[1])
  from .item_registry import registry,resolve_item
  row=db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,payload['item_path'])).fetchone()
  entry=resolve_item(registry(db),payload['item_path'])
  if not row or row['quantity']!=1 or not entry or (entry.get('mechanics') or {}).get('magic_form_id')!=ID:
   raise ValueError('Escolha uma única Espada Adamas do inventário')
  from .battle_mode import require_actor_alive
  from .night_form import require_humanoid
  require_actor_alive(db,owner);require_humanoid(db,owner)
  init_schema(db);previous=read_condition(db,row['id']) or {}
  if previous.get('destroyed'):raise ValueError('A arma foi destruída')
  now=_now();after={**previous,'magic_form':payload['form_id']}
  save_condition(db,row['id'],after,now)
  db.execute('UPDATE player_inventory SET updated_at=? WHERE id=?',(now,row['id']))
  event=_write_event(db,character_id=owner,actor_id=actor,actor_role=role,event_type='weapon_form',
   field='inventory',before=previous,after=after,reason='Adamas · '+FORMS[payload['form_id']]['name'],session_id=None)
  append_session_ledger_event(db,source_type='weapon_form',source_id=request_id,event_kind='action',
   actor_id=actor,actor_name=owner,actor_role=role,character_id=owner,
   title='Adamas assumiu '+FORMS[payload['form_id']]['name'],detail={'item_path':payload['item_path'],'form_id':payload['form_id']},
   visibility='table',created_at=now)
  result={'event_id':event,'form_id':payload['form_id']}
  db.execute('INSERT INTO combat_effect_commands VALUES(?,?,?)',(request_id,fingerprint,json.dumps(result)))
  return result
