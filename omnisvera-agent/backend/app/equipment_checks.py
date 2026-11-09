"""Reviewed percentage checks; use the native roll store, not a second dice engine."""
import sqlite3
from contextlib import closing
from .magic_equipment import identity
from .magic_item_rulebook import rules_for

SPECS={
 'item-magico-botas-elficas':{'slot':'Pés','label':'Mover-se em silêncio','unit':'tentativa'},
 'item-magico-manto-da-aranha':{'slot':'Acessório','label':'Escalada · 3 m','unit':'3 m'},
}
for key,spec in SPECS.items():
 chance=rules_for(key)['parameters']['chance_percent']
 if type(chance) is not int or not 1<=chance<=100:raise ValueError('Chance percentual inválida na fonte estruturada')
 spec['chance']=chance
PREFIX='equipment:'

def compile_item(item):
 key=item.get('id');spec=SPECS.get(key)
 if not spec:return None
 return {'catalog_id':key,'item_type':'accessory','description':item.get('description',''),'damage_formula':None,
  'effects':[],'effect_rules':[],'usable':False,'thumbnail':item.get('image_path'),
  'mechanics':{'family_schema':1,'family':'magic_equipment','kind':'accessory','magical':True,
   'equipment_check_schema':1,'equipment_check_id':key,'chance_percent':spec['chance'],'check_unit':spec['unit'],
   'equipment_slots':[spec['slot']],'approved_equipment_slots':[spec['slot']],
   'consume_mode':'none','charges_max':0,'recharge':'none','family_gaps':[],
   'source':'Old Dragon 1, p.146'}}

def resolve(inventory,source_id):
 path=str(source_id or '').removeprefix(PREFIX)
 spec=SPECS.get(identity({'item_path':path}))
 row=next((i for i in inventory if i.get('item_path')==path and i.get('equipped') and i.get('quantity',0)>0),None)
 if not spec or not row or row.get('equipment_slot')!=spec['slot']:
  raise ValueError('Equipe o equipamento correto antes de realizar este teste')
 return path,spec

def validate(db,owner,path,formula,target,comparison):
 row=db.execute('SELECT item_path,equipped,equipment_slot,quantity FROM player_inventory WHERE profile_id=? AND item_path=?',(owner,path)).fetchone()
 inventory=[dict(zip(('item_path','equipped','equipment_slot','quantity'),row))] if row else []
 _,spec=resolve(inventory,PREFIX+path)
 if formula!='1d100' or target!=spec['chance'] or comparison!='at_most':
  raise ValueError('Chance/fórmula do equipamento não pode ser substituída')
 from .night_form import current_form
 state=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(owner,)).fetchone()
 if state:
  import json
  if current_form(json.loads(state[0])):raise ValueError('Forma animal não utiliza equipamento humanoide')

def replay(path,owner,actor,request):
 """A historical receipt survives unequipping; a new attempt still needs gear."""
 from .dice_rolls import _roll_record
 with closing(sqlite3.connect(str(path))) as db:
  db.row_factory=sqlite3.Row
  if not db.execute("SELECT 1 FROM sqlite_master WHERE name='dice_roll_events'").fetchone():return None
  row=db.execute('SELECT * FROM dice_roll_events WHERE request_id=?',(request.request_id,)).fetchone()
 if row is None:return None
 record=_roll_record(row)
 expected={'actor_id':actor,'character_id':owner,'source':'equipment_check','source_id':str(request.source_id)[len(PREFIX):],
  'visibility':request.visibility,'target_hidden':bool(request.hide_target),'session_id':request.session_id,
  'scene_id':request.scene_id,'action_id':request.action_id,'reason':str(request.reason or '').strip()[:500] or None}
 if request.roll_type!='skill' or any(record.get(k)!=v for k,v in expected.items()) or (request.label is not None and request.label.strip()[:160]!=record['label']) or request.target_value not in (None,record['target_value']):
  raise ValueError('request_id já utilizado com outra intenção de teste')
 return record
