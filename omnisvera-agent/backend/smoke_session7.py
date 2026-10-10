"""Operational rehearsal against a SQLite backup ONLY; leaves the live table untouched."""
import json
import gc
from contextlib import closing
from dataclasses import replace
from pathlib import Path
import sqlite3
from tempfile import TemporaryDirectory
from unittest.mock import patch

from fastapi.testclient import TestClient
from app import main
from app.access import AccessContext
from app.combat_effects import effect_command, readeffects
from app.scene_play import change_session_status, list_sessions, scene_view, update_element
from app.session_workspace import update_workspace_map_visibility, set_active_workspace_map, get_workspace_snapshot
from app.loot import list_loot, reveal_loot, distribute_loot
from prepare_session7 import DATABASE, install, start_encounter


def smoke(source=DATABASE):
    results=[]
    with TemporaryDirectory(prefix='omnisvera-s7-qa-') as temporary:
        root=Path(temporary)
        db=root/'rehearsal.sqlite3'
        with closing(sqlite3.connect(source)) as src, closing(sqlite3.connect(db)) as dst:
            src.backup(dst)
        with closing(sqlite3.connect(db)) as con:
            historical=con.execute('SELECT * FROM game_sessions WHERE session_number<=6 ORDER BY id').fetchall()
            historical_scenes=con.execute('SELECT * FROM scenes WHERE session_id IN (SELECT id FROM game_sessions WHERE session_number<=6) ORDER BY id').fetchall()
        prepared=install(db,root)
        assert install(db,root)==prepared
        results.append('create/load/idempotency/maps/roster')
        # Close any old combat on QA COPY only; never make this call against live DB.
        snapshot=readeffects(db)
        if snapshot.get('encounter',{}).get('active'):
            effect_command(db,actor_id='master',actor_role='gm',request_id='s7-qa-end-old',expected_version=snapshot['version'],action='end',payload={})
        for s in list_sessions(db):
            if s['status']=='active' and s['id']!=prepared['session_id']:
                change_session_status(db,s['id'],'paused')
        gm=AccessContext(mode='gm')
        with patch.object(main,'settings',replace(main.settings,database_path=db,rebuild_on_startup=False,auto_refresh_index=False)):
            old_overrides=dict(main.app.dependency_overrides)
            main.app.dependency_overrides[main.require_master]=lambda:gm
            main.app.dependency_overrides[main.require_any]=lambda:gm
            client=TestClient(main.app)  # no lifespan: do not rebuild the real Vault index
            def request(method,url,**kwargs):
                response=getattr(client,method)(url,**kwargs)
                assert response.status_code==200,(url,response.status_code,response.text[:400])
                return response.json()
            def command(action,payload=None):
                return request('post','/gm/combat/effects',json=dict(request_id=f's7-qa-{action}-{readeffects(db)["version"]}',expected_version=readeffects(db)['version'],action=action,payload=payload or {}))
            try:
                request('post',f'/gm/sessions/{prepared["session_id"]}/status',json={'status':'active'})
                for sid in prepared['scenes']:
                    request('post',f'/gm/scenes/{sid}/open-on-table',json={'request_id':f's7-qa-open-{sid}'})
                    request('get',f'/scenes/{sid}')
                results.append('all 9 scene openings via HTTP')
                sheets={p:request('get',f'/characters/{p}') for p in prepared['players']+['dorn7']}
                assert sheets['morthak']['state']['maximum_hp']==8
                assert not any(p['character_id']=='varkh' for p in scene_view(db,prepared['scenes'][5],access_mode='gm',profile_id=None)['participants'])
                results.append('actual player sheets/Dorn; Varkh excluded from S7')
                request('post',f'/gm/scenes/{prepared["scenes"][5]}/open-on-table',json={'request_id':'s7-qa-open-arena'})
                encounter=start_encounter(db,include_dorn=True)
                assert len(encounter['encounter']['participants'])==8
                enemy=prepared['enemy_tokens'][0]
                mode='physical' if get_workspace_snapshot(db,is_gm=True)['table_mode']=='physical' else 'digital'
                attack=request('post','/characters/vezemir/attacks/resolve',json={'request_id':'s7-qa-attack','attack_id':'melee','target_type':'token','target_id':enemy,'roll_mode':mode,**({'d20':15} if mode=='physical' else {})})
                request('post',f'/combat/attacks/{attack["resolution_id"]}/confirm',json={})
                results.append('native encounter/attack/confirmation')
                command('next_turn')
                summon=request('post','/characters/morthak/techniques/levantar-esqueleto',json={'request_id':'s7-qa-summon'})
                token=summon['token']
                assert token['sheet']['armor_class']==16 and token['maximum_hp']==10
                assert token['sheet']['attacks'][0]['damage']=='1d6+1'
                assert token['image_path'] and 'invocacao_de_esqueleto' in token['image_path']
                snapshot=get_workspace_snapshot(db,is_gm=True,map_id=prepared['maps']['inside'])
                actual=next(t for t in snapshot['tokens'] if t['id']==token['id'])
                assert actual['sheet']['reward_items'][0]['name']=='Essência de Mana'
                results.append('Morthak native summon/vegetal stats/essence card')
                # Next skeleton -> Raziel -> Dorn.
                for _ in range(3): command('next_turn')
                assert readeffects(db)['encounter']['participants'][readeffects(db)['encounter']['turn_index']]['target_id']=='dorn7'
                command('dorn_guard',{'ally_id':'morthak','position_confirmed':True})
                command('end')
                diagnosis=command('dorn_diagnose',{'subject':'encaixe C-B','difficulty':14})
                assert diagnosis['protocol_result']['information'] is None
                command('dorn_vanguard',{'enabled':True})
                command('dorn_vanguard',{'enabled':False})
                results.append('Dorn Guard/Vanguard/Diagnosis; no automatic lore')
                office=prepared['scenes'][6]
                request('post',f'/gm/scenes/{office}/open-on-table',json={'request_id':'s7-qa-office'})
                for e in scene_view(db,office,access_mode='gm',profile_id=None)['elements']:
                    if e['element_type']=='clue': update_element(db,e['id'],fields={},reveal=True)
                public=scene_view(db,office,access_mode='player',profile_id='raziel')
                assert len(public['elements'])==3 and 'private_notes' not in public
                assert all('private_description' not in e for e in public['elements'])
                cache=next(x for x in list_loot(db,gm) if x['resolution_id']=='loot:session7-cache')
                assert cache['status']=='draft'
                assert all(x['resolution_id']!='loot:session7-cache' for x in list_loot(db,AccessContext(mode='player',profile_id='vezemir')))
                reveal_loot(db,cache['resolution_id'])
                allocations=[dict(reward_id=r['id'],character_id='vezemir',quantity=r['quantity']) for r in cache['rewards']]
                distribute_loot(db,resolution_id=cache['resolution_id'],request_id='s7-qa-loot-delivery',allocations=allocations)
                results.append('handouts/privacy/native loot/reveal/distribution')
                request('post',f'/gm/sessions/{prepared["session_id"]}/status',json={'status':'completed'})
                assert next(s for s in list_sessions(db) if s['id']==prepared['session_id'])['status']=='completed'
                assert next(x for x in list_loot(db,gm) if x['resolution_id']==cache['resolution_id'])['status']=='distributed'
                results.append('close/reload/persistence')
            finally:
                client.close()
                main.app.dependency_overrides.clear()
                main.app.dependency_overrides.update(old_overrides)
        with closing(sqlite3.connect(db)) as con:
            assert historical==con.execute('SELECT * FROM game_sessions WHERE session_number<=6 ORDER BY id').fetchall()
            assert historical_scenes==con.execute('SELECT * FROM scenes WHERE session_id IN (SELECT id FROM game_sessions WHERE session_number<=6) ORDER BY id').fetchall()
        results.append('sessions/scenes 1–6 byte-for-field unchanged')
        # Some legacy DB helpers rely on connection finalization; force it before
        # Windows removes the QA copy (never relax assertions or touch live DB).
        gc.collect()
    return results


if __name__=='__main__':
    print(json.dumps(smoke(),ensure_ascii=False,indent=2))
