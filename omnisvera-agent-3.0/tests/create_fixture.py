"""Disposable native backend fixture. Reads no operational database or tokens."""
import json
import os
import sqlite3
import sys
import tempfile
from contextlib import closing
from pathlib import Path
from PIL import Image, ImageDraw

PROJECT = Path(__file__).resolve().parents[1]
COMPANION = PROJECT.parent / 'omnisvera-agent'
sys.path[:0] = [str(COMPANION / 'backend/scripts'), str(COMPANION / 'backend')]
from cf01_probe import configure


def create():
    directory = Path(tempfile.mkdtemp(prefix='omni-companion3-'))
    database = directory / 'fixture.sqlite3'
    configure(database)
    os.environ['LOCALAPPDATA'] = str(directory / 'localappdata')
    from test_map_commerce import MapCommerceTests
    fixture = MapCommerceTests()
    fixture.setUp()
    try:
        with closing(sqlite3.connect(fixture.db)) as source, closing(sqlite3.connect(database)) as dest:
            source.backup(dest)
    finally:
        fixture.doCleanups()
    from app.vault_index import init_db
    from app.combat_effects import init_effects
    from app.spatial_grid import init_spatial, configure_grid
    from app.session_workspace import save_workspace_token
    from app.session_ledger import append_session_ledger_event
    init_db(database)
    init_effects(database)
    init_spatial(database)
    configure_grid(database, actor_id='master', role='gm', request_id='companion3-grid-test',
                   map_id='default', config={'cols': 20, 'rows': 20, 'cell_size_m': 1})
    vault = database.with_suffix('.vault')
    art_dir = vault / 'zz_media/fixture'
    art_dir.mkdir(parents=True, exist_ok=True)
    for name, color, dimensions in [('portrait', '#4f927f', (128, 128)),
                                    ('map', '#596c49', (1000, 600)),
                                    ('session', '#384e68', (768, 400))]:
        picture = Image.new('RGB', dimensions, color)
        draw = ImageDraw.Draw(picture)
        draw.text((12, 12), 'SYNTHETIC UI TEST: ' + name, fill='white')
        for coordinate in range(0, dimensions[0], 50):
            draw.line([(coordinate, 0), (coordinate, dimensions[1])], fill='#718879')
        picture.save(art_dir / (name + '.png'))
    actors = {'dorn7': 'Unidade DORN-7', 'vezemir': 'Vezemir',
              'raziel': 'Raziel', 'morthak': 'Morthak', 'varkh': 'Varkh Nimalis'}
    pins = {}
    # A broken preferred image must resolve through the existing item catalog.
    item_icons = vault / 'zz_media/ui/icons/items'
    item_icons.mkdir(parents=True, exist_ok=True)
    with Image.open(art_dir / 'portrait.png') as image:
        image.save(item_icons / 'adaga.png')
        image.save(item_icons / 'inventario.jpg')
    with closing(sqlite3.connect(database)) as db, db:
        db.execute('''INSERT OR REPLACE INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at)
            VALUES('Items/Adaga de ensaio.md','Adaga','[]','item','[]',?,'# Adaga sintética','fixture')''',
            (json.dumps({'type': 'item', 'visibility': 'jogadores', 'item_type': 'arma',
                         'thumbnail': 'zz_media/fixture/missing.png'}),))
        for index, (identity, name) in enumerate(actors.items()):
            path = f'Characters/Individual/{name}.md'
            note = vault / path
            note.parent.mkdir(parents=True, exist_ok=True)
            note.write_text(f'---\ntype: character\nvisibility: jogadores\n---\n# {name}\nFicha sintética de ensaio.\n', encoding='utf-8')
            sheet = {'attributes': {'strength': 13, 'dexterity': 10, 'constitution': 12,
                                   'intelligence': 14, 'wisdom': 11, 'charisma': 9},
                     'character_class': {'class_name': 'Mago' if identity in {'dorn7', 'morthak'} else 'Guerreiro',
                                         'level': 5, 'saving_throw': 14, 'hit_points': 30},
                     'race': {'race': 'Constructo' if identity == 'dorn7' else 'Humano', 'movement': '9 metros'},
                     'armor': {'armor_class': 16}, 'attacks': {'melee_bonus': 5, 'ranged_bonus': 4}}
            state = {'current_hp': 27, 'maximum_hp': 30, 'temporary_hp': 0,
                     'conditions': [], 'coins': 20, 'resources': []}
            db.execute('''INSERT OR REPLACE INTO character_sheets
                (profile_id,character_path,character_title,status,data_json,updated_at)
                VALUES(?,?,?,'approved',?,'fixture')''', (identity, path, name, json.dumps(sheet)))
            db.execute('INSERT OR REPLACE INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)',
                       (identity, json.dumps(state), 'fixture'))
            db.execute('''INSERT OR REPLACE INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at)
                VALUES(?,?,'[]','character','[]',?,?,'fixture')''',
                       (path, name, json.dumps({'type': 'character', 'visibility': 'jogadores',
                                              'portrait': 'zz_media/fixture/portrait.png'}), f'# {name}\nFicha sintética'))
        append_session_ledger_event(db, source_type='fixture_private', source_id='companion3-private',
            event_kind='action', actor_id='master', actor_name='Mestre', actor_role='gm', character_id=None,
            title='GM_PRIVATE_COMPANION3', detail={}, visibility='gm', created_at='2026-11-06T00:00:00+00:00')
    for index, (identity, name) in enumerate(actors.items()):
        pins[identity] = save_workspace_token(database, token_type='character', character_id=identity,
            name=name, latitude=(5 + index + .5) * 5, longitude=(5 + index + .5) * 5,
            current_hp=27, maximum_hp=30)['id']
    hidden = save_workspace_token(database, token_type='monster', name='GM_HIDDEN_COMPANION3',
        visible_to_players=False, latitude=10, longitude=10, current_hp=10, maximum_hp=10)['id']
    # Approved Dorn mechanics exist only in this disposable fixture.
    with closing(sqlite3.connect(database)) as db, db:
        row = db.execute("SELECT state_json FROM character_states WHERE profile_id='dorn7'").fetchone()
        dorn_state = json.loads(row[0])
        dorn_state.update(current_hp=20, maximum_hp=20, resources=[])
        db.execute("UPDATE character_states SET state_json=? WHERE profile_id='dorn7'", (json.dumps(dorn_state),))
    from app.dorn_mage import apply_dorn_mage
    from app.player_inventory import upsert_inventory
    from app.combat import init_combat
    init_combat(database)
    apply_dorn_mage(database)
    for identity in actors:
        upsert_inventory(database, profile_id=identity, item_path='Items/Adaga de ensaio.md',
                         item_title='Adaga', quantity=2, equipped=True, notes='Synthetic fixture',
                         equipment_slot='Corpo a corpo')
    enemy = save_workspace_token(database, token_type='monster', name='Alvo do Relâmpago',
        latitude=42.5, longitude=42.5, current_hp=100, maximum_hp=100,
        sheet={'armor_class': 12, 'saving_throw': 20, 'movement': '9 m'})
    from app.scene_play import create_session, sync_historical_sessions
    sync_historical_sessions(database)
    session, _ = create_session(database, request_id='companion3-ui-session', campaign_id='omnisvera',
        title='Sessão de ensaio', created_by='fixture', private_notes='GM_PRIVATE_SESSION_COMPANION3')
    from app.session_workspace import set_workspace_map, update_workspace_fog
    public_map = set_workspace_map(database, title='Mapa de ensaio', image_path='zz_media/fixture/map.png', visible_to_players=True)
    private_map = set_workspace_map(database, title='GM_PRIVATE_MAP_COMPANION3', image_path='zz_media/fixture/map.png', visible_to_players=False)
    public_pin = save_workspace_token(database, map_id=public_map['id'], token_type='location', name='Local do ensaio',
        image_path='zz_media/fixture/portrait.png', latitude=50, longitude=50, sheet={'description': 'Detalhes públicos do pin'})
    save_workspace_token(database, map_id=public_map['id'], token_type='monster', name='GM_HIDDEN_MAP_PIN',
        image_path='zz_media/fixture/portrait.png', visible_to_players=False, latitude=20, longitude=20)
    update_workspace_fog(database, map_id=public_map['id'], layer='exploration', enabled=True,
        revealed_cells=[], mist_density={'0:0': 1})
    with closing(sqlite3.connect(database)) as db, db:
        db.execute("UPDATE game_sessions SET status='completed',image_path=?,public_summary='Resumo público do ensaio' WHERE id=?",
            ('zz_media/fixture/session.png', session['id']))
        db.execute("UPDATE session_workspace_maps SET image_path='zz_media/fixture/map.png' WHERE id='default'")
    from app.scene_play import create_scene, create_element
    preparation, _ = create_scene(database,request_id='native-preparation-scene',campaign_id='omnisvera',
        session_id=session['id'],title='Preparação isolada',location_name='Ensaio',created_by='master',
        map_id=public_map['id'],visibility='gm',private_notes='PRIVATE_SCENE_NOTES')
    elements=[]
    for i in range(2):
        element,_=create_element(database,preparation['id'],request_id='native-prep-element-'+str(i),
            element_type='clue',title='Pista '+str(i),status='hidden',visibility='gm',created_by='master',
            public_description='PUBLIC_CLUE_'+str(i),private_description='PRIVATE_CLUE_'+str(i))
        elements.append(element['id'])
    preparation_pins=[]
    for i in range(2):
        pin=save_workspace_token(database,map_id=public_map['id'],token_type='monster',name='Preparado '+str(i),
            latitude=30+i*10,longitude=40,visible_to_players=False)
        preparation_pins.append(pin['id'])
    receipt = {'preparation_id':preparation['id'],'preparation_elements':elements,'preparation_pins':preparation_pins,'synthetic' : True, 'database': str(database), 'directory': str(directory),
               'pins': pins, 'hidden': hidden, 'actors': list(actors), 'public_map': public_map['id'],
               'private_map': private_map['id'], 'public_pin': public_pin['id'], 'session_id': session['id'],
               'enemy': enemy['id']}
    (directory / 'fixture.json').write_text(json.dumps(receipt), encoding='utf-8')
    return receipt


if __name__ == '__main__':
    print(json.dumps(create()), flush=True)
