"""Operator-authorized catalogue repair, not an AI sandbox tool. Never uses the ring on production."""
import argparse
from contextlib import closing
import hashlib
import json
from pathlib import Path
import shutil
import sqlite3
import tempfile
import sys
import httpx
from cf01_probe import BACKEND
from runic_ring_contract import repair_payload
sys.path.insert(0,str(BACKEND))
from app.schemas import SessionItemEffectRule


def verify_preserved(backup, *, allow_startup_map_timestamps=False):
    source=BACKEND/'data'/'omnisvera_companion.sqlite3'
    credentials=BACKEND/'data'/'access_tokens.json'
    # The official launcher reserializes JSON. Compare every credential/profile
    # value, not whitespace/property order; never print token values.
    assert json.loads(credentials.read_text(encoding='utf-8-sig'))==json.loads((backup/'access_tokens.json').read_text(encoding='utf-8-sig')), 'Credentials changed'
    with closing(sqlite3.connect((backup/'companion.sqlite3').as_uri()+'?mode=ro',uri=True)) as old, closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as current:
        protected=('character_states','character_sheets','character_definition_overrides','character_notes',
                   'scenes','game_sessions','combat_effects','combat_effect_clock','session_workspace_tokens',
                   'session_workspace_maps','session_workspace_map_grids','session_workspace_entity_positions')
        for table in protected:
            before=old.execute('SELECT * FROM '+table).fetchall();after=current.execute('SELECT * FROM '+table).fetchall()
            if table=='session_workspace_maps' and allow_startup_map_timestamps:
                columns=[r[1] for r in current.execute('PRAGMA table_info('+table+')')]
                stamp=columns.index('updated_at');identity=columns.index('id')
                def without_bootstrap_stamp(row):
                    row=list(row)
                    if row[identity] in {'official:nimalia','official:earthropo'}:row[stamp]=None
                    return tuple(row)
                before=[without_bootstrap_stamp(row) for row in before];after=[without_bootstrap_stamp(row) for row in after]
            assert sorted(before,key=repr)==sorted(after,key=repr),table+' changed'
        columns=[row[1] for row in current.execute('PRAGMA table_info(player_inventory)') if row[1]!='updated_at']
        sql='SELECT '+','.join(columns)+' FROM player_inventory ORDER BY id'
        assert old.execute(sql).fetchall()==current.execute(sql).fetchall(), 'Inventory quantities/charges changed'


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apply',action='store_true',help='Requires direct authorization to repair live catalogue')
    args=parser.parse_args()
    source=BACKEND/'data'/'omnisvera_companion.sqlite3'
    credentials=BACKEND/'data'/'access_tokens.json'
    token_bytes=credentials.read_bytes()
    saved=json.loads(token_bytes)
    with httpx.Client(base_url='http://127.0.0.1:8787',headers={'X-Omnisvera-Token':saved['master_token']},
                      trust_env=False,timeout=30) as client:
        health=client.get('/health');health.raise_for_status()
        if Path(health.json()['database_path']).resolve()!=source.resolve():
            raise ValueError('Runtime is not the expected operational database; no repair applied')
        response=client.get('/gm/workspace/items');response.raise_for_status()
        rings=[item for item in response.json() if str(item.get('name')).casefold() in ('anel runico','anel rúnico')]
        if len(rings)!=1:raise ValueError('Expected one existing runic ring; no catalogue guessing')
        ring=rings[0];payload=repair_payload(ring)
        if ring['mechanics']['consume_mode']=='charges':
            print(json.dumps({'status':'UNCHANGED','reason':'already uses charges'}));return
        if not args.apply:
            print(json.dumps({'status':'PREVIEW','item_id':ring['id'],'change':'consume_mode: none -> charges'}));return
        backup=Path(tempfile.mkdtemp(prefix='omnisvera-before-runic-ring-'))
        with closing(sqlite3.connect(source.as_uri()+'?mode=ro',uri=True)) as original, closing(sqlite3.connect(backup/'companion.sqlite3')) as copy:
            original.backup(copy)
        shutil.copy2(credentials,backup/'access_tokens.json')
        result=client.patch('/gm/workspace/items/'+str(ring['id']),json=payload);result.raise_for_status()
        after=result.json()
        assert after['mechanics']['consume_mode']=='charges'
        for field in ('name','description','image_path','usable','effects','effect_rules'):
            expected=ring[field]
            if field=='effect_rules':
                # The native editor materializes existing DTO defaults; compare
                # effective rules, not missing-versus-default JSON keys.
                expected=[SessionItemEffectRule.model_validate(r).model_dump() for r in expected]
            assert after[field]==expected, 'Unexpected catalogue change: '+field
        assert credentials.read_bytes()==token_bytes, 'Credentials changed during repair'
        verify_preserved(backup)
        print(json.dumps({'status':'APPLIED','item_id':ring['id'],'consume_mode':'charges','charges_max':1,
            'recharge':'inn_rest','backup':str(backup),'inventory_and_saved_state_preserved':True,
            'credentials_hash':hashlib.sha256(token_bytes).hexdigest()[:12]},ensure_ascii=True))


if __name__=='__main__':main()
