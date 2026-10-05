"""Real API rehearsal against a disposable copy; no operational attacks."""
from contextlib import closing
import gc
import json
import os
from pathlib import Path
import sqlite3
import sys
from tempfile import TemporaryDirectory

ROOT = Path(__file__).resolve().parents[1]


def main():
    with TemporaryDirectory(prefix='dorn-mage-probe-') as temp:
        dbpath = Path(temp) / 'test.sqlite3'
        with closing(sqlite3.connect((ROOT/'backend/data/omnisvera_companion.sqlite3').as_uri()+'?mode=ro', uri=True)) as source, closing(sqlite3.connect(dbpath)) as dest:
            source.backup(dest)
        os.environ.update(OMNISVERA_DB_PATH=str(dbpath), OMNISVERA_VAULT_PATH=str(ROOT.parent),
            OMNISVERA_MASTER_TOKEN='test-master', OMNISVERA_ACCESS_TOKEN='test-master',
            OMNISVERA_PLAYER_PROFILES_JSON=json.dumps({'vezemir': {'token':'test-player','character_path':'Characters/Individual/Vezemir.md','character_title':'Vezemir'}}),
            OMNISVERA_REBUILD_ON_STARTUP='false', OMNISVERA_TRAINING_CAPTURE_MODE='off')
        sys.path.insert(0,str(ROOT/'backend'))
        from app.dorn_mage import apply_dorn_mage
        from app.main import app, settings
        from app.session_workspace import save_workspace_token, update_workspace_table_mode
        from fastapi.testclient import TestClient
        assert settings.database_path.resolve() == dbpath.resolve()
        apply_dorn_mage(dbpath)
        with closing(sqlite3.connect(dbpath)) as db, db:
            db.execute("UPDATE combat_effect_clock SET encounter_json='{}'")
        update_workspace_table_mode(dbpath,'digital')
        target=save_workspace_token(dbpath,token_type='monster',name='Alvo de ensaio',latitude=50,longitude=50,
            current_hp=100,maximum_hp=100,visible_to_players=True,sheet={'armor_class':99})
        gm={'X-Omnisvera-Token':'test-master'}
        player={'X-Omnisvera-Token':'test-player'}
        with TestClient(app) as client:
            response=client.get('/characters/dorn7',headers=gm)
            assert response.status_code==200,response.text
            view=response.json(); definition=view['definition']
            assert (definition['level'],definition['class_name'],definition['defenses']['armor_class'])==(2,'Mago',11)
            melee=next(a for a in definition['attacks'] if a['id']=='melee')
            assert (melee['attack_bonus'],melee['damage'])==(2,'1d6+2'),melee
            assert sum(r['maximum'] for r in view['state']['resources'])==3,view['state']['resources']
            body={'request_id':'dorn-mage-spell-probe','attack_id':'misseis-magicos','target_type':'token','target_id':target['id'],'roll_mode':'digital'}
            assert client.post('/characters/dorn7/attacks/resolve',json=body,headers=player).status_code==403
            response=client.post('/characters/dorn7/attacks/resolve',json=body,headers=gm)
            assert response.status_code==200,response.text
            result=response.json()
            assert result['breakdown']['automatic_hit'] and result['damage_formula']=='1d4+2',result
            for _ in range(2):
                response=client.post('/combat/attacks/'+result['resolution_id']+'/confirm',headers=gm)
                assert response.status_code==200,response.text
            view=client.get('/characters/dorn7',headers=gm).json()
            assert next(r['current'] for r in view['state']['resources'] if r['key']=='dorn_misseis_magicos')==0
            assert sum(r['current'] for r in view['state']['resources'])==2
            public=client.get('/characters/dorn7',headers=player).json()
            assert public.get('state') is None,public
            assert not public['definition'].get('gm_fields')
            with closing(sqlite3.connect(dbpath)) as db:
                assert db.execute('SELECT current_hp FROM session_workspace_tokens WHERE id=?',(target['id'],)).fetchone()[0]==100-result['damage_total']
            print('DORN_SHEET / STAFF / MISSILE / EXACTLY_ONCE / PLAYER_AUTHORIZATION / PRIVACY = PASS')
        gc.collect()


if __name__=='__main__':
    main()
