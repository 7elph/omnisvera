"""Campaign exceptions, using native pins, effects, grid and command receipts.

No parallel summons/turn engine. One-round execution; no invented damage
concentration save. Death magic follows the supplied literal 'creatures'.
"""
import json
import re
import uuid
from .dice_rolls import roll_formula

SPELLS={'clonagem':'Clonagem','magia-da-morte':'Magia da Morte'}


def clone_spec(db,overrides,state,contract=None):
    from .character_play import build_character_definition,attribute_modifier
    if contract is None:
        from .action_library import native_action_contract
        contract=native_action_contract('technique:morthak:clonagem',int(overrides.get('level') or 5))
    data=json.loads(db.execute("SELECT data_json FROM character_sheets WHERE profile_id='morthak'").fetchone()[0])
    definition=build_character_definition(profile_id='morthak',note={'title':'Morthak'},sheet={'steps':[{'key':k,'fields':v} for k,v in data.items()]},inventory=[],overrides=overrides)
    strength=int(definition['attributes'].get('strength') or 10)
    damage=None
    # Copy only mundane dice, never enhancement, magical effects or equipment.
    for path, in db.execute("SELECT item_path FROM player_inventory WHERE profile_id='morthak' AND quantity>0 AND equipped=1 AND equipment_slot LIKE '%corpo a corpo%' ORDER BY item_path"):
        if path.startswith('session-item:'):
            row=db.execute('SELECT mechanics_json FROM session_custom_items WHERE id=?',(int(path.split(':')[1]),)).fetchone()
            formula=json.loads(row[0] or '{}').get('damage_formula') if row else None
        else:
            row=db.execute('SELECT frontmatter,content FROM notes WHERE path=?',(path,)).fetchone()
            front=json.loads(row[0] or '{}') if row else {}
            formula=front.get('damage') or front.get('damage_formula')
            if not formula and row:
                from .player_inventory import normalize_inventory_item_mechanics
                formula=normalize_inventory_item_mechanics({'item_title':front.get('name') or path,'item_type':front.get('type'),'effects':front.get('effects') or [],'description':row[1] or ''}).get('damage_formula')
        match=re.match(r'^\s*(\d+d\d+)',str(formula or ''))
        if match:
            bonus=attribute_modifier(strength);damage=match[1]+(f'{bonus:+d}' if bonus else '');break
    if not damage:raise ValueError('Cadastre o dano básico da arma corpo a corpo equipada; clones não copiam dano mágico')
    attack=next(a for a in definition['attacks'] if a['id']=='melee')
    if definition['defenses'].get('armor_class') is None or not definition.get('movement'):raise ValueError('CA e movimento básicos precisam estar cadastrados')
    hp=contract['resolution']['hp']
    return {'hp':max(hp['minimum'],int(state['maximum_hp'])//hp['maximum_divisor']),'armor_class':definition['defenses']['armor_class'],
            'movement':definition['movement'],'hit_dice':int(overrides['level']),
            'attributes':definition['attributes'],'attacks':[{'name':'Ataque básico (cópia não mágica)','bonus':attack['base_attack_bonus'],'damage':damage}]}


def available_cells(db,map_id,origin,reach):
    from .spatial_grid import distance_cells
    row=db.execute('SELECT cols,rows,cell_size_m,distance_rule,origin_x,origin_y FROM session_workspace_map_grids WHERE map_id=?',(map_id,)).fetchone()
    if not row:raise ValueError('Clonagem exige um mapa com grid lógico')
    cols,rows,scale,rule,ox,oy=row
    occupied=set()
    for x,y,w,h in db.execute('SELECT p.cell_x,p.cell_y,p.footprint_w,p.footprint_h FROM session_workspace_entity_positions p JOIN session_workspace_tokens t ON t.id=p.token_id WHERE p.map_id=? AND t.current_hp>0',(map_id,)):
        occupied.update((i,j) for i in range(x,x+w) for j in range(y,y+h))
    cells=[(x,y) for x in range(cols) for y in range(rows) if (x,y) not in occupied and distance_cells(rule,origin,(x,y))*scale<=reach]
    return sorted(cells,key=lambda p:(distance_cells(rule,origin,p),p)),(cols,rows,ox,oy)


def spawn(db,effect,encounter,now):
    anchor=db.execute("SELECT t.id,t.image_path,p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.map_id=? AND t.character_id='morthak' ORDER BY t.id LIMIT 1",(effect['map_id'],)).fetchone()
    if not anchor:return []
    # New casts freeze their validated geometry/duration. Legacy effects retain
    # the exact former constants instead of being rewritten on a read/restart.
    cells,grid=available_cells(db,effect['map_id'],anchor[2:4],effect.get('clone_range_m',10))
    duration=effect.get('clone_duration_rounds',5)
    cols,rows,ox,oy=grid;identities=[]
    for index,(x,y) in enumerate(cells[:effect['clone_count']]):
        identity='monster:'+uuid.uuid4().hex;spec=effect['clone_spec'];name=f'Clone de Morthak {index+1}'
        sheet={**spec,'has_blood':False,'marker':'◇','role':'Aliado invocado','summon':{'caster':'morthak','technique':'clonagem','duration':f'{duration} rodadas'},'clone_effect_id':effect['id']}
        lat=oy+(y+.5)*(100-oy)/rows;lng=ox+(x+.5)*(100-ox)/cols
        db.execute("INSERT INTO session_workspace_tokens(id,token_type,map_id,name,image_path,visible_to_players,color,latitude,longitude,current_hp,maximum_hp,conditions_json,sheet_json,created_at,updated_at) VALUES(?,'monster',?,?,?,1,'#9568c8',?,?,?,?, '[]',?,?,?)",(identity,effect['map_id'],name,anchor[1],lat,lng,spec['hp'],spec['hp'],json.dumps(sheet),now,now))
        db.execute('INSERT OR REPLACE INTO session_workspace_entity_positions VALUES(?,?,?,?,1,1,1)',(effect['map_id'],identity,x,y))
        if encounter.get('active'):
            members=encounter['participants'];caster_index=next(i for i,p in enumerate(members) if p['target_type']=='character' and p['target_id']=='morthak')
            members.insert(caster_index+index+1,{'target_type':'token','target_id':identity,'token_id':identity,'name':name,'controller_id':'morthak','initiative':members[caster_index]['initiative']})
            encounter.setdefault('return_tokens',[]).append({'id':identity,'created':True})
        identities.append(identity)
    effect.update(clone_ids=identities,phase='active',duration='rounds',rounds=duration,updated_at=now)
    db.execute('UPDATE combat_effects SET data_json=?,active=? WHERE id=?',(json.dumps(effect),int(bool(identities)),effect['id']))
    return identities


def clone_turn(db,encounter,now):
    members=encounter.get('participants') or []
    current=members[int(encounter.get('turn_index') or 0)%len(members)] if members else {}
    if current.get('target_type')!='character' or current.get('target_id')!='morthak':return
    for raw, in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND json_extract(data_json,'$.necro_spell')='clonagem' AND json_extract(data_json,'$.phase')='pending'").fetchall():
        effect=json.loads(raw)
        if int(encounter.get('turn_sequence') or 0)>effect['cast_sequence']:spawn(db,effect,encounter,now)


def cleanup(db,now):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effects'").fetchone():return
    removed = False
    state=db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()
    alive=state and int(json.loads(state[0]).get('current_hp') or 0)>0
    for identity,active,raw in db.execute("SELECT id,active,data_json FROM combat_effects WHERE json_extract(data_json,'$.necro_spell')='clonagem'").fetchall():
        effect=json.loads(raw)
        if not alive or not active:
            db.execute('UPDATE combat_effects SET active=0 WHERE id=?',(identity,))
            for token in effect.get('clone_ids',[]):
                removed = bool(db.execute("DELETE FROM session_workspace_tokens WHERE id=? AND json_extract(sheet_json,'$.clone_effect_id')=?",(token,identity)).rowcount) or removed
        else:
            removed = bool(db.execute("DELETE FROM session_workspace_tokens WHERE current_hp<=0 AND json_extract(sheet_json,'$.clone_effect_id')=?",(identity,)).rowcount) or removed
    if removed:
        from .battle_mode import retire_defeated
        retire_defeated(db, now)


def death_targets(db,snapshot,level,contract=None):
    from .necromancer_spells import authorized_target,victim_hit_dice,grid_distance_m
    if contract is None:
        from .action_library import native_action_contract
        contract=native_action_contract('technique:morthak:magia-da-morte',level)
    map_id=(snapshot.get('encounter') or {}).get('map_id') if (snapshot.get('encounter') or {}).get('active') else None
    if not map_id:
        row=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone();map_id=row[0] if row else None
    targets=[];seen=set()
    # Literal supplied rule: eligible creatures, including allies; never caster.
    for identity,character,raw in db.execute("SELECT id,character_id,sheet_json FROM session_workspace_tokens WHERE map_id=? AND token_type!='location' AND visible_to_players=1 AND current_hp>0 ORDER BY id",(map_id,)).fetchall():
        sheet=json.loads(raw or '{}')
        if sheet.get('statless') or sheet.get('combat_retired') or (sheet.get('summon') or {}).get('dismissed'):continue
        kind,target=('character',character) if character else ('token',identity)
        if target=='morthak' or (kind,target) in seen:continue
        distance=grid_distance_m(db,kind,target)
        if distance is None:raise ValueError('Posicione todas as criaturas reveladas no grid antes de Magia da Morte')
        if distance>contract['range']['meters']:continue
        victim=authorized_target(db,kind,target,'player');dv=victim_hit_dice(db,victim)
        if dv is None:raise ValueError('DV ausente em '+victim['name']+'; cadastre antes de Magia da Morte')
        if dv<=contract['resolution']['max_hit_dice']:targets.append((distance,target,victim))
        seen.add((kind,target))
    return [v for _,_,v in sorted(targets,key=lambda t:(t[0],t[1]))]


def command(db,snapshot,payload,now):
    from .necromancer_spells import caster,add_effect,save_difficult
    from .battle_mode import require_battle_turn,commit_battle_action
    from .combat_effects import change_hp
    from .session_ledger import append_session_ledger_event
    overrides,state,level=caster(db)
    if level<5:raise ValueError('Exceção da campanha liberada no nível 5')
    spell=payload['spell_id']
    if spell=='clonagem' and payload.get('mode')=='end':
        db.execute("UPDATE combat_effects SET active=0 WHERE target_type='character' AND target_id='morthak' AND json_extract(data_json,'$.necro_spell')='clonagem'")
        cleanup(db,now)
        return {'spell':'Clonagem','results':[{'target':'Morthak','execution':'Concentração encerrada'}]}
    from .action_library import native_action_contract
    from .action_components import require_definition_revision,roll_native_component,spend_native_resource
    contract=native_action_contract('technique:morthak:'+spell,level)
    require_definition_revision(payload,contract)
    require_battle_turn(db,snapshot,'morthak')
    encounter=snapshot.get('encounter') or {}
    if encounter.get('active') and (encounter.get('attacks_used') or encounter.get('action_committed')):raise ValueError('A magia exige ação completa disponível')
    resource_cost=contract['costs'][0];key=resource_cost['key'];cost=resource_cost['amount']
    resource=next((r for r in state.get('resources',[]) if r['key']==key),None)
    if not resource or int(resource.get('current') or 0)<cost:raise ValueError('Sem uso diário de '+SPELLS[spell])
    results=[];death_info={}
    if spell=='clonagem':
        if sum(e.get('necro_spell')=='clonagem' for e in snapshot['effects'])>=contract['resolution']['max_active_groups']:raise ValueError('Já há Clonagem ativa ou em execução')
        component=contract['costs'][1]
        fragment=db.execute("SELECT item_path FROM player_inventory WHERE profile_id='morthak' AND item_title=? COLLATE NOCASE AND quantity>=? ORDER BY item_path LIMIT 1",(component['item_title'],component['amount'])).fetchone()
        if not fragment:raise ValueError('Clonagem exige um fragmento de cristal arcano consumível')
        anchor=db.execute("SELECT t.map_id,p.cell_x,p.cell_y FROM session_workspace_tokens t JOIN session_workspace_entity_positions p ON p.token_id=t.id AND p.map_id=t.map_id WHERE t.character_id='morthak' AND t.map_id=? LIMIT 1",(encounter.get('map_id') if encounter.get('active') else db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()[0],)).fetchone()
        if not anchor:raise ValueError('Posicione Morthak no grid ativo')
        cells,_=available_cells(db,anchor[0],anchor[1:3],contract['range']['meters'])
        if not cells:raise ValueError('Nenhum espaço desocupado no alcance de Clonagem')
        from .morthak_action_contracts import clone_circle_and_count
        circle,count=clone_circle_and_count(contract,overrides.get('clonagem_circle'))
        spec=clone_spec(db,overrides,state,contract)
        effect=add_effect(db,{'type':'character','id':'morthak'},'Clonagem','Morthak',now,necro_spell='clonagem',magic_type='arcane',spell_circle=circle,caster_level=level,phase='pending',cast_sequence=int(encounter.get('turn_sequence') or 0),map_id=anchor[0],clone_count=count,clone_spec=spec,clone_ids=[],clone_range_m=contract['range']['meters'],clone_duration_rounds=contract['resolution']['duration_rounds'])
        db.execute("UPDATE player_inventory SET quantity=quantity-?,updated_at=? WHERE profile_id='morthak' AND item_path=?",(component['amount'],now,fragment[0]))
        if not encounter.get('active'):spawn(db,effect,encounter,now)
        results=[{'target':'Morthak','effect':effect,'execution':'1 rodada; surgem no próximo turno do conjurador' if encounter.get('active') else '1 rodada ficcional concluída fora do combate'}]
    else:
        victims=death_targets(db,snapshot,level,contract)
        if not victims:raise ValueError('Nenhuma criatura elegível no alcance')
        limit_roll={}
        def roll_limit(formula):
            rolled=roll_formula(formula);limit_roll.update(rolled);return rolled
        limit=roll_native_component(contract['resolution']['victim_limit'],roll_limit)
        death_info={'victim_limit':limit,'victim_limit_roll':limit_roll,'eligible_count':len(victims)}
        # Validate JP before any mutation; the transaction also rolls back failures.
        from .dice_rolls import resolve_character_roll
        attribute=contract['resolution']['save']['attribute']
        for victim in victims[:limit]:resolve_character_roll({'defenses':victim['defenses']},[],'saving_throw',attribute)
        for victim in victims[:limit]:
            saving=save_difficult(db,victim,attribute);outcome=None
            if not saving['success']:
                hp=db.execute('SELECT '+('state_json FROM character_states WHERE profile_id=?' if victim['type']=='character' else 'current_hp FROM session_workspace_tokens WHERE id=?'),(victim['id'],)).fetchone()[0]
                hp=int(json.loads(hp)['current_hp']) if victim['type']=='character' else int(hp)
                outcome=change_hp(db,victim['type'],victim['id'],-hp-(10 if victim['type']=='character' and victim['id']=='vezemir' else 0),now,ignore_temporary_hp=True)
            results.append({'target':victim['name'],'saving_throw':saving,
                            'execution':'Resistiu' if saving['success'] else 'Morte instantânea',**(outcome or {})})
        death_info.update(defeated=sum(not r['saving_throw']['success'] for r in results),
                          resisted=sum(bool(r['saving_throw']['success']) for r in results))
    remaining=spend_native_resource(db,'morthak',key,cost,now)
    hp_result={}
    if spell=='magia-da-morte':
        hp_cost=contract['costs'][1]
        latest=json.loads(db.execute("SELECT state_json FROM character_states WHERE profile_id='morthak'").fetchone()[0])
        current_hp=int(latest['current_hp'])
        hp_result=change_hp(db,'character','morthak',-(current_hp-current_hp//hp_cost['retained_divisor']),now,ignore_temporary_hp=hp_cost['ignore_temporary_hp'])
        death_info.update(caster_hp_before=current_hp,caster_hp_after=hp_result['hp_after'],
                          hp_cost=current_hp-hp_result['hp_after'])
    commit_battle_action(db,snapshot)
    title=(f"Magia da Morte — {death_info['defeated']} derrotados · {death_info['resisted']} resistiram · PV {death_info['caster_hp_before']} → {death_info['caster_hp_after']}"
           if death_info else SPELLS[spell]+' — '+('; '.join(r['target']+': efeito aplicado' for r in results)))
    append_session_ledger_event(db,source_type='necro_high_spell',source_id=uuid.uuid4().hex,event_kind='action',actor_id='morthak',actor_name='Morthak',actor_role='player',character_id='morthak',title=title,detail={'spell':SPELLS[spell],'results':results,**hp_result,**death_info},visibility='table',created_at=now)
    return {'spell':SPELLS[spell],'results':results,'resource_remaining':remaining,
            'action_contract':{'ref':contract['ref'],'revision':contract['revision'],'level':level},**hp_result,**death_info}
