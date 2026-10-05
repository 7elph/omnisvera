"""Synthetic-only S6 acceptance. Never reads the campaign database or Vault.

Usage: python session6_acceptance.py seed <OS-temp-db>
       python session6_acceptance.py probe <OS-temp-db> <port>
Serve with cf01_probe.py serve; only public cf01 fixture credentials are used.
"""
from contextlib import closing
from pathlib import Path
import json
import sqlite3
import sys
import uuid

from cf01_probe import checked_database, TOKENS, BACKEND
sys.path.insert(0, str(BACKEND))


def seed(database):
    database = checked_database(database)
    if database.exists():
        raise ValueError('Refusing to replace an existing database')
    from app.character_creation import init_character_creation
    from app.character_play import init_character_play
    from app.combat import init_combat
    from app.combat_effects import init_effects
    from app.dice_rolls import init_dice_rolls
    from app.vault_index import init_db
    from app.player_inventory import init_player_inventory, upsert_inventory
    from app.session_workspace import set_workspace_map, save_workspace_token, save_session_item
    from app.dorn_mage import SPEC
    for initializer in (init_db, init_character_creation, init_character_play,
                        init_combat, init_effects, init_dice_rolls, init_player_inventory):
        initializer(database)
    maps = [set_workspace_map(database, title=title, image_path='', visible_to_players=True)
            for title in ('Exploração fixture S6', 'Arena fixture S6')]
    for profile, title, cls, hp, ba, jp in (
        ('vezemir', 'Vezemir', 'Guerreiro', 12, 1, 16),
        ('raziel', 'Raziel', 'Hemomante', 12, 1, 15),
        ('morthak', 'Morthak', 'Mago', 4, 0, 14),
        ('dorn7', 'Dorn 7', 'Mago', 13, 0, 14),
        ('varkh', 'Varkh Nimalis', 'Guerreiro', 12, 1, 16)):
        path = f'Characters/Individual/{title}.md'
        data = {'attributes': dict.fromkeys(('strength','dexterity','constitution','intelligence','wisdom','charisma'),16),
                'character_class': {'class_name':cls,'level':1,'hit_points':hp,'base_attack':ba,'saving_throw':jp,'experience':2500},
                'race': {'race':'Fixture','movement':'9 m'}, 'armor':{'armor_class':14},
                'attacks':{'melee_bonus':3,'ranged_bonus':3}}
        if profile == 'dorn7':
            data = SPEC['sheet']
        with closing(sqlite3.connect(database)) as db, db:
            db.execute('INSERT INTO notes(path,title,aliases,type,visibility,tags,frontmatter,content,updated_at) VALUES(?,?,?,?,?,?,?,?,?)',
                       (path,title,'[]','character','public','[]','{}',f'# {title}\nPersonagem sintético para aceitação S6.','fixture'))
            db.execute('INSERT INTO character_sheets(profile_id,character_path,character_title,status,data_json,updated_at) VALUES(?,?,?,?,?,?)',
                       (profile,path,title,'approved',json.dumps(data),'fixture'))
            if profile == 'dorn7':
                overrides = {'level':2,'maximum_hp':13,'armor_class':11,'race':'Constructo Arcano','class_name':'Mago',
                             'attributes':data['attributes'], 'approved_session_abilities':SPEC['abilities']}
                db.execute('INSERT INTO character_definition_overrides VALUES(?,?,?)',(profile,json.dumps(overrides),'fixture'))
                state={'current_hp':13,'maximum_hp':13,'temporary_hp':0,'conditions':[],
                       'resources':[{'key':a['uses']['resource_key'],'label':a['uses']['label'],
                                     'current':1,'maximum':1,'recharge':'inn_rest'} for a in SPEC['abilities']]}
                db.execute('INSERT INTO character_states VALUES(?,?,1,?)',(profile,json.dumps(state),'fixture'))
        weapon = save_session_item(database,name=f'Arma fixture {title}',item_type='Arma',description='Teste sintético',
                    effects=[],mechanics={'equipment_slots':['arma corpo a corpo'],'damage_formula':'1d6','consume_mode':'none'},usable=False)
        upsert_inventory(database,profile_id=profile,item_path=f"session-item:{weapon['id']}",item_title=weapon['name'],
                         quantity=1,equipped=True,equipment_slot='arma corpo a corpo',notes='fixture')
        save_workspace_token(database,token_type='character',character_id=profile,name=title,
                         latitude=20,longitude=20+10*len(title),map_id=maps[0]['id'],visible_to_players=True,current_hp=hp,maximum_hp=hp)
    print(json.dumps({'seed':'PASS','source':'synthetic only','database':str(database),'maps':[m['id'] for m in maps]}))


def probe(database, port):
    database = checked_database(database)
    if not database.is_file():
        raise ValueError('Seed a synthetic disposable database first')
    import httpx
    prefix = 'accept-' + uuid.uuid4().hex
    clients = {r:httpx.Client(base_url=f'http://127.0.0.1:{int(port)}',headers={'X-Omnisvera-Token':TOKENS[r]},trust_env=False,timeout=30)
               for r in ('gm','vezemir','raziel','morthak')}
    gm=clients['gm']; marks={}
    def require(r):
        if r.is_error: raise AssertionError(f'{r.request.method} {r.request.url.path}: {r.status_code} {r.text}')
        return r.json()
    def post(c,path,data): return require(c.post(path,json=data))
    def character(p): return require(gm.get('/characters/'+p))
    def clock(): return require(gm.get('/combat/effects'))
    def command(action,payload=None): return post(gm,'/gm/combat/effects',{'request_id':prefix+uuid.uuid4().hex,'expected_version':clock()['version'],'action':action,'payload':payload or {}})
    def turn(c):
        body={'request_id':prefix+uuid.uuid4().hex,'expected_version':clock()['version'],'action':'next_turn'}
        first=post(c,'/combat/next-turn',body)
        assert first==post(c,'/combat/next-turn',body)
    def resolve(c,p,attack,target):
        return post(c,f'/characters/{p}/attacks/resolve',{'request_id':prefix+uuid.uuid4().hex,'attack_id':attack,
                        'target_type':'token','target_id':target,'roll_mode':'physical','d20':20})
    def confirm(c,r):
        path=f"/combat/attacks/{r['resolution_id']}/confirm"
        first=require(c.post(path)); assert first==require(c.post(path)); return first
    try:
        assert require(gm.get('/health'))['access_mode']=='gm'
        # Refuse writes unless this server exposes the exact random map IDs in
        # the nominated disposable fixture. A temp path alone cannot bind HTTP.
        with closing(sqlite3.connect(database)) as db:
            local_maps = {r[0] for r in db.execute('SELECT id FROM session_workspace_maps')}
            synthetic_notes = db.execute("SELECT count(*) FROM notes WHERE content LIKE '%Personagem sintético para aceitação S6.%'").fetchone()[0]
        remote_maps = {m['id'] for m in require(gm.get('/workspace/maps'))}
        assert synthetic_notes == 5 and local_maps and remote_maps == local_maps, 'HTTP server is not the nominated synthetic fixture'
        require(gm.patch('/gm/workspace/table-mode', json={'table_mode':'physical'}))
        views={p:character(p) for p in ('vezemir','raziel','morthak','varkh','dorn7')}
        assert views['dorn7']['definition']['level']==2
        assert views['dorn7']['definition']['defenses']['armor_class']==11
        assert views['dorn7']['state']['maximum_hp']==13
        marks['dorn_sheet']='PASS'
        # Reconcile/advance only synthetic characters, retaining spent resources.
        for p in views:
            if p == 'varkh':
                blocked = gm.post(f'/gm/characters/{p}/level/preview',json={'target_level':2,'hp_roll':2})
                assert blocked.status_code == 400 and 'não foi conferida' in blocked.json()['detail'], blocked.text
                marks['varkh_unreviewed_progression_blocked']='PASS'
                continue
            plan=post(gm,f'/gm/characters/{p}/level/preview',{'target_level':2,'hp_roll':None if p=='dorn7' else 2})
            if plan['status']=='applied':
                assert character(p)['definition']['level']==2
                continue
            assert plan['status']=='ready',plan
            data={'target_level':2,'hp_roll':None if p=='dorn7' else 2,'fingerprint':plan['fingerprint']}
            assert post(gm,f'/gm/characters/{p}/level/confirm',data)['applied']
            assert not post(gm,f'/gm/characters/{p}/level/confirm',data)['applied']
            assert character(p)['definition']['level']==2
        marks['four_supported_level_flows_including_dorn']='PASS'
        if clock().get('encounter',{}).get('active'): command('end')
        post(gm,'/characters/vezemir/actions',{'action':'rest_at_inn','payload':{},'reason':'Pré-condição fixture'})
        original=require(gm.get('/workspace'))['map']['id']
        arena=next(m['id'] for m in require(gm.get('/workspace/maps')) if m['id']!=original)
        enemy=post(gm,'/gm/workspace/tokens',{'token_type':'monster','name':'Lobo fixture loot Q','map_id':original,
                 'visible_to_players':True,'current_hp':1,'maximum_hp':12,'sheet':{'armor_class':1,'treasure':'Q',
                 'attacks':[{'name':'Mordida','bonus':2,'damage':'1d6'},{'name':'Garra','bonus':1,'damage':'1d4'}]}})
        command('start',{'title':'Aceitação S6','map_id':arena,'battle_mode':True,'participants':[
            {'target_type':'character','target_id':'vezemir','initiative':30},
            {'target_type':'character','target_id':'morthak','initiative':20},
            {'target_type':'token','target_id':enemy['id'],'initiative':10}]})
        response=clients['morthak'].post('/characters/morthak/attacks/resolve',json={'request_id':prefix+'outturn','attack_id':'adaga-de-osso','target_type':'token','target_id':enemy['id'],'roll_mode':'physical','d20':20})
        assert response.status_code==400,response.text
        force=post(clients['vezemir'],'/characters/vezemir/techniques/forca-arcana',{'request_id':prefix+'force'})
        duration=force['duration_rounds']; base=views['vezemir']['definition']['attributes']['strength']
        assert character('vezemir')['definition']['attributes']['strength']>base
        # Incremental Dorn must retain current turn and effect.
        participants=clock()['encounter']['participants']
        current=participants[clock()['encounter']['turn_index']]['target_id']
        command('initiative',{'participants':participants+[{'target_type':'character','target_id':'dorn7','initiative':15}]})
        assert clock()['encounter']['participants'][clock()['encounter']['turn_index']]['target_id']==current
        for remaining in range(duration-1,-1,-1):
            round_before=clock()['round']
            for _ in participants+[{'target_id':'dorn7'}]: command('next_turn')
            assert clock()['round']==round_before+1
            active=[e for e in clock()['effects'] if e['target_id']=='vezemir']
            assert (active[0]['rounds'] if active else 0)==remaining
            player_effects=require(clients['vezemir'].get('/combat/effects'))['effects']
            assert [e['rounds'] for e in player_effects]==[e['rounds'] for e in active]
        assert character('vezemir')['definition']['attributes']['strength']==base
        marks['effect_expiration_and_incremental_dorn']='PASS'
        done=confirm(clients['vezemir'],resolve(clients['vezemir'],'vezemir','melee',enemy['id']))
        assert done['hp_after']==0
        turn(clients['vezemir'])
        command('end'); marks['combat_zero_hp']='PASS'
        loot=post(gm,'/gm/workspace/loot/resolve',{'request_id':prefix+'loot','token_id':enemy['id'],'scope':'carried','roll_mode':'digital'})
        assert loot['resolution_id'] not in {r['resolution_id'] for r in require(clients['vezemir'].get('/workspace/loot'))}
        assert loot['rewards'],loot
        require(gm.post(f"/gm/workspace/loot/{loot['resolution_id']}/reveal"))
        allocation={'request_id':prefix+'distribution','allocations':[{'reward_id':r['id'],'character_id':'vezemir','quantity':r['quantity']} for r in loot['rewards']]}
        path=f"/gm/workspace/loot/{loot['resolution_id']}/distribute"
        post(gm,path,allocation)
        inventory_after=character('vezemir')['inventory']
        post(gm,path,allocation)
        assert character('vezemir')['inventory']==inventory_after
        marks['loot_reveal_distribution_retry']='PASS'
        magic_target=post(gm,'/gm/workspace/tokens',{'token_type':'monster','name':'Alvo mágico fixture','map_id':original,
                    'visible_to_players':True,'current_hp':100,'maximum_hp':100,'sheet':{'armor_class':1}})
        for p in ('morthak','dorn7'):
            key='misseis-magicos'
            resource_key='dorn_misseis_magicos' if p=='dorn7' else 'misseis_magicos'
            count=next(r['current'] for r in character(p)['state']['resources'] if r['key']==resource_key)
            assert 1<=count<=10
            for _ in range(count):
                require(gm.patch('/gm/workspace/table-mode', json={'table_mode':'digital'}))
                record=post(gm,f'/characters/{p}/attacks/resolve',{'request_id':prefix+uuid.uuid4().hex,'attack_id':key,'target_type':'token','target_id':magic_target['id'],'roll_mode':'digital'})
                confirm(gm,record)
            before=character(p)['state']; magic=next(r for r in before['resources'] if r['key'] in ('misseis_magicos','dorn_misseis_magicos'))
            assert magic['current']==0
            rejected=gm.post(f'/characters/{p}/attacks/resolve',json={'request_id':prefix+uuid.uuid4().hex,'attack_id':key,
                            'target_type':'token','target_id':magic_target['id'],'roll_mode':'digital'})
            assert rejected.status_code==400,rejected.text
            for _ in range(2): post(gm,f'/characters/{p}/actions',{'action':'rest_at_inn','payload':{},'reason':'Descanso fixture S6'})
            after=character(p)['state']; restored=next(r for r in after['resources'] if r['key']==magic['key'])
            assert restored['current']==restored['maximum']
            assert after['current_hp']==after['maximum_hp']
        marks['magic_and_existing_rest']='PASS'
        require(gm.patch('/gm/workspace/table-mode',json={'table_mode':'physical'}))
        post(gm,'/characters/raziel/actions',{'action':'damage','payload':{'amount':4},'reason':'Pré-condição Mordida fixture'})
        command('start',{'title':'Mordida fixture','map_id':original,'battle_mode':True,'participants':[
            {'target_type':'character','target_id':'raziel','initiative':20},
            {'target_type':'token','target_id':magic_target['id'],'initiative':10}]})
        before=character('raziel')['state']
        result=confirm(clients['raziel'],resolve(clients['raziel'],'raziel','melee',magic_target['id']))
        bite_body={'request_id':prefix+'bite','resolution_id':result['resolution_id']}
        bite=post(clients['raziel'],'/characters/raziel/techniques/mordida',bite_body)
        after=character('raziel')['state']
        assert after['current_hp']==min(before['maximum_hp'],before['current_hp']+bite['heal_roll'])
        assert after['resources']==before['resources']
        assert 1<=bite['heal_roll']<=4
        assert clients['raziel'].post('/characters/raziel/techniques/mordida',json=bite_body).status_code==400
        assert character('raziel')['state']['current_hp']==after['current_hp']
        command('end'); marks['mordida_attack_heal_once_no_blood_cost']='PASS'
        print(json.dumps({'status':'PASS','checks':marks,'live_table':'NOT_TESTED'},ensure_ascii=False,indent=2))
    finally:
        for c in clients.values(): c.close()


if __name__=='__main__':
    db=checked_database(sys.argv[2])
    if sys.argv[1]=='seed': seed(db)
    elif sys.argv[1]=='probe': probe(db,sys.argv[3])
    else: raise ValueError('Use seed or probe')
