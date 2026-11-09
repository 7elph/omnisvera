"""Reviewed Ferrugem contact against explicitly identified native equipment.

Call inside a native command transaction after role, contact/range and budget
validation. The caller owns command receipts, ledger and realtime. Unknown
material or nonnumeric magic never becomes a destructive default.
"""
from copy import deepcopy
import hashlib
import json
import re
import unicodedata

from .dice_rolls import roll_formula
from .inventory_conditions import read_condition,save_condition

POLICY='campaign-rust-2026-10-27'
KINDS={'attack_bonus','damage_bonus','armor_class_bonus'}


def _key(value):
    return unicodedata.normalize('NFKD',str(value or '')).encode('ascii','ignore').decode('ascii').casefold()


def _owner(db,kind,identity):
    if kind=='character':return identity
    if kind!='token':raise ValueError('Tipo de alvo inválido')
    row=db.execute('SELECT character_id,token_type FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
    if not row:raise ValueError('Alvo não encontrado')
    return row[0] if row[1]=='character' and row[0] else identity


def _source(db,path):
    front={};rules=[];mechanics={}
    if path.startswith(('compendium:','merchant:')):
        from .item_catalog import get_catalog_item
        item=get_catalog_item(path.split(':',1)[1] if path.startswith('compendium:') else path.split(':',2)[-1])
        if item:
            mechanics=deepcopy(item.get('mechanics') or {})
            return {'rules':deepcopy(item.get('effect_rules') or [])+deepcopy(mechanics.get('embedded_enhancement_rules') or []),'mechanics':mechanics}
    if db.execute("SELECT 1 FROM sqlite_master WHERE name='notes'").fetchone():
        row=db.execute('SELECT frontmatter FROM notes WHERE path=?',(path,)).fetchone()
        if row:
            front=json.loads(row[0] or '{}');mechanics=deepcopy(front.get('mechanics') or {})
            for entry in front.get('effect_rules') or []:
                if not isinstance(entry,dict) or entry.get('trigger')!='while_equipped':continue
                rule=deepcopy(entry)
                rule['id']=str(rule.get('id') or f"vault:{path}:{rule.get('kind')}:{rule.get('target','')}")
                try:rule['value']=int(rule.get('value') or 0)
                except (ValueError,TypeError):continue
                rule['target']=str(rule.get('target') or '').strip()
                rule['label']=str(rule.get('label') or '').strip() or None
                rule['formula']=None
                rules.append(rule)
            return {'rules':rules,'mechanics':mechanics,'material':front.get('material'),
                    'magical':front.get('magical'),'enchantment_bonus':front.get('enchantment_bonus')}
    if path.startswith('session-item:') and path.split(':',1)[1].isdigit() and db.execute("SELECT 1 FROM sqlite_master WHERE name='session_custom_items'").fetchone():
        row=db.execute('SELECT effect_rules_json,mechanics_json FROM session_custom_items WHERE id=?',(int(path.split(':')[1]),)).fetchone()
        if row:return {'rules':json.loads(row[0] or '[]'),'mechanics':json.loads(row[1] or '{}')}
    raise ValueError('Fonte do item indisponível; Ferrugem exige metadados verificados')


def _selection(source,selection,old):
    if old:
        if selection is not None and selection!=old['selection']:
            raise ValueError('Os metadados de corrosão já foram identificados para esta instância')
        return deepcopy(old['selection'])
    if selection is None:selection=deepcopy((source.get('mechanics') or {}).get('rust_profile'))
    if selection is None:return None
    if not isinstance(selection,dict) or set(selection)!={'material','magical','enchantment_bonus','enhancement_rule_ids'}:
        raise ValueError('Confirme os metadados de material e encantamento do item')
    value=deepcopy(selection);bonus=value['enchantment_bonus'];ids=value['enhancement_rule_ids']
    if value['material'] not in {'metal','nonmetal'} or type(value['magical']) is not bool:
        raise ValueError('Confirme os metadados de material e magia do item')
    if type(bonus) is not int or not 0<=bonus<=10 or not isinstance(ids,list) or any(not isinstance(x,str) for x in ids) or len(ids)!=len(set(ids)):
        raise ValueError('Encantamento numérico ou vínculos inválidos')
    if value['material']=='metal' and value['magical'] and bonus==0:
        raise ValueError('Item mágico sem bônus numérico exige decisão específica; não será destruído como comum')
    if not value['magical'] and bonus>0:raise ValueError('Bônus de encantamento exige item mágico')
    declared=source.get('magical')
    if declared is None:declared=source.get('mechanics',{}).get('magical')
    if declared is True and not value['magical']:raise ValueError('A fonte declara item mágico')
    explicit_bonus=source.get('enchantment_bonus')
    if explicit_bonus is None:explicit_bonus=source.get('mechanics',{}).get('enchantment_bonus')
    if explicit_bonus is not None and (type(explicit_bonus) is not int or explicit_bonus!=bonus):
        raise ValueError('O bônus de encantamento diverge da fonte do item')
    if bonus and not ids:raise ValueError('Identifique os componentes de encantamento do item')
    if not bonus and ids:raise ValueError('Item comum não reduz componentes de encantamento')
    available={str(r.get('id')):r for r in source['rules'] if isinstance(r,dict)}
    for identity in ids:
        rule=available.get(identity)
        if (not rule or rule.get('kind') not in KINDS or rule.get('trigger')!='while_equipped'
                or type(rule.get('value')) is not int or rule['value']!=bonus or rule.get('formula')
                or re.search(r'\b(?:for|forca|strength|atributo|attribute|classe|class|nivel|level|maestria|mastery)\b',_key(rule.get('label')))):
            raise ValueError('Componente de atributo/classe ou não identificado como encantamento separado')
    return value


def preview(db,target_type,target_id,inventory_id,selection=None):
    if type(inventory_id) is not int or inventory_id<=0:raise ValueError('Item de inventário inválido')
    owner=_owner(db,target_type,target_id)
    cursor=db.execute('SELECT * FROM player_inventory WHERE id=? AND profile_id=?',(inventory_id,owner))
    row=cursor.fetchone()
    if not row:raise ValueError('Item não pertence ao inventário do alvo')
    item=dict(zip([d[0] for d in cursor.description],row));old=read_condition(db,inventory_id)
    if int(item['quantity'])<=0:raise ValueError('Item não está mais disponível no inventário')
    if not item['equipped']:raise ValueError('Escolha um item equipado que recebeu o contato')
    source=_source(db,item['item_path'])
    source_hash=hashlib.sha256(json.dumps(source,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    if old and old.get('source_fingerprint')!=source_hash:
        raise ValueError('A fonte do item mudou; revise seus componentes antes de resolver Ferrugem')
    metadata=_selection(source,selection,old)
    if metadata and metadata['magical'] and int(item['quantity'])!=1:
        raise ValueError('Separe uma unidade do item mágico antes de degradar seu encantamento')
    canonical=[POLICY,item,old,source_hash,metadata,target_type,target_id]
    fingerprint=hashlib.sha256(json.dumps(canonical,sort_keys=True,ensure_ascii=False).encode()).hexdigest()
    return {'inventory_id':inventory_id,'item_title':item['item_title'],'item_path':item['item_path'],
            'fingerprint':fingerprint,'source_fingerprint':source_hash,'needs_metadata':metadata is None,
            'selection':metadata,'version':old.get('version',0) if old else 0,
            'bonus':int(old['bonus_remaining']) if old else (metadata['enchantment_bonus'] if metadata else None),
            'rules':[{key:r.get(key) for key in ('id','kind','value','label')} for r in source['rules']],
            'quantity':int(item['quantity']),'policy':POLICY}


def contact(db,target_type,target_id,inventory_id,selection=None,*,expected_fingerprint,now):
    current=preview(db,target_type,target_id,inventory_id,selection)
    if not isinstance(expected_fingerprint,str) or expected_fingerprint!=current['fingerprint']:
        raise ValueError('O item ou sua condição mudou; confirme o contato novamente')
    if current['needs_metadata']:raise ValueError('Confirme os metadados de material e encantamento antes de aplicar Ferrugem')
    metadata=current['selection'];before=int(current['bonus']);roll=None;destroyed=False
    if metadata['material']=='nonmetal':
        save_condition(db,inventory_id,{'kind':'rust','policy':POLICY,'source_fingerprint':current['source_fingerprint'],
            'selection':metadata,'enhancement_rule_ids':metadata['enhancement_rule_ids'],
            'original_bonus':metadata['enchantment_bonus'],'bonus_remaining':before,'destroyed':False},now)
        return {**current,'unaffected':True,'resisted':False,'bonus_before':before,'bonus_after':before,'destroyed':False}
    if before>0:
        roll=roll_formula('1d100');resisted=int(roll['total'])<=min(100,before*10)
        after=before if resisted else before-1
    else:
        resisted=False;after=0;destroyed=True
    state={'kind':'rust','policy':POLICY,'source_fingerprint':current['source_fingerprint'],'selection':metadata,
           'enhancement_rule_ids':metadata['enhancement_rule_ids'],'original_bonus':metadata['enchantment_bonus'],
           'bonus_remaining':after,'destroyed':destroyed}
    if destroyed:
        db.execute('UPDATE player_inventory SET quantity=MAX(0,quantity-1),equipped=0,equipment_slot=NULL,updated_at=? WHERE id=?',(now,inventory_id))
        # A mundane stack loses just the contacted unit. Remaining units are
        # not themselves destroyed/corroded and are intentionally unequipped.
        if current['quantity']>1:
            db.execute('DELETE FROM inventory_item_conditions WHERE inventory_id=?',(inventory_id,))
        else:save_condition(db,inventory_id,state,now)
    else:save_condition(db,inventory_id,state,now)
    return {'inventory_id':inventory_id,'item_title':current['item_title'],'policy':POLICY,
            'resisted':resisted,'chance_percent':min(100,before*10),'roll':roll,
            'bonus_before':before,'bonus_after':after,'destroyed':destroyed}


def reverse_contact(db,record,now):
    """Metal melee weapon touching Ferrugem after a confirmed native hit.

Receipts are owned by combat.confirm_attack_resolution; invoke this once
inside that transaction. Ranged ammunition and unknown material remain
explicitly assisted rather than corroding the equipped bow/arbitrary item.
"""
    if record.get('target_type')!='token' or record.get('result')!='hit':return []
    target=db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(record.get('target_id'),)).fetchone()
    sheet=json.loads(target[0] or '{}') if target else {}
    origin=sheet.get('source')
    if not isinstance(origin,dict) or origin.get('monster_id')!='monstro-ferrugem':return []
    breakdown=record.get('breakdown') or {}
    intercepted={entry['strike'] for entry in (breakdown.get('reflection_result') or {}).get('rolls',[]) if entry.get('intercepted')}
    hits=[strike for index,strike in enumerate(breakdown.get('strikes') or [record]) if strike.get('result')=='hit' and index not in intercepted]
    if not hits:return []
    path=(breakdown.get('attack') or {}).get('weapon_item_path')
    if not path or path.startswith(('spell:','hemomancy:')):return []
    if (breakdown.get('damage_profile') or {}).get('kind') in {'spell','effect'}:return []
    actor=record.get('actor_character_id')
    rows=db.execute('SELECT id,equipment_slot FROM player_inventory WHERE profile_id=? AND item_path=? AND equipped=1 AND quantity>0',(actor,path)).fetchall()
    if not rows:return [{'manual':True,'reason':'Contato com Ferrugem: item físico não identificado no inventário do atacante'}]
    identity,slot=rows[0]
    if record.get('attack_id')=='ranged' or _key(slot) in {'a distancia','ranged'}:
        return [{'manual':True,'inventory_id':identity,'reason':'Projétil tocou Ferrugem; não corroer automaticamente a arma lançadora'}]
    old=read_condition(db,identity)
    if not old or not old.get('selection'):
        return [{'manual':True,'inventory_id':identity,'reason':'Contato com Ferrugem: confirme material e encantamento do item; nenhum novo ataque é necessário'}]
    kind='character' if db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(actor,)).fetchone() else 'token'
    results=[]
    for _ in hits:
        try:
            current=preview(db,kind,actor,identity)
            result=contact(db,kind,actor,identity,expected_fingerprint=current['fingerprint'],now=now)
        except ValueError as error:
            results.append({'manual':True,'inventory_id':identity,'reason':str(error)});break
        results.append(result)
        if result.get('destroyed'):break
    return results
