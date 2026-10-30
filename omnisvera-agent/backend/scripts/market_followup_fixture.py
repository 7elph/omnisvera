"""Prepare only the native rehearsal's TEMP database, never its source."""
import json
import sqlite3
import tempfile
from contextlib import closing
from pathlib import Path


def prepare(database):
    database=Path(database).resolve()
    if not database.is_relative_to(Path(tempfile.gettempdir()).resolve()) or database.name!='simulation.sqlite3' or not database.is_file():
        raise ValueError('Market fixture requires an existing TEMP simulation.sqlite3')
    from app.access import AccessContext
    from app.merchant_magic import configure_defaults
    from app.npc_campaign_profile import PROFILE,apply
    from app.merchant import _inventory_upsert
    from app.inventory_conditions import init_schema,save_condition
    with closing(sqlite3.connect(database)) as db:
        guild=db.execute("SELECT id,npc_id,token_id FROM merchants WHERE name='Conclave dos Errantes'").fetchone()
        if not guild or not guild[1]:raise ValueError('Market fixture requires the configured Conclave and Klhauss')
        configured=any(json.loads(row[0] or '{}').get('campaign_profile',{}).get('id')==PROFILE['id'] for row in db.execute("SELECT sheet_json FROM session_workspace_tokens WHERE name='Klhauss'"))
    gm=AccessContext(mode='gm')
    if not configured:apply(database,guild[1],gm,request_id='fixture-klhauss-profile')
    configure_defaults(database,guild[0],gm)
    with closing(sqlite3.connect(database)) as db,db:
        db.row_factory=sqlite3.Row;init_schema(db)
        item='compendium:arma-corpo-espada-longa'
        _inventory_upsert(db,profile_id='vezemir',item_path=item,item_title='Espada usada do ensaio',quantity=1,equipped=False,charges_current=1,charges_max=3,notes='Fixture only')
        db.execute("UPDATE player_inventory SET item_title='Espada usada do ensaio',quantity=1,equipped=0,equipment_slot=NULL,charges_current=1,charges_max=3 WHERE profile_id='vezemir' AND item_path=?",(item,))
        inventory_id=db.execute("SELECT id FROM player_inventory WHERE profile_id='vezemir' AND item_path=?",(item,)).fetchone()[0]
        save_condition(db,inventory_id,{'kind':'rust','original_bonus':2,'bonus_remaining':1,'enhancement_rule_ids':[]},'fixture')
    return {'prepared':True,'database':'TEMP','production_modified':False}
