"""A declarative Vault-like consumable in the owned TEMP rehearsal only."""
import json,sqlite3,tempfile
from pathlib import Path
from contextlib import closing

def prepare(database):
    database=Path(database).resolve()
    if database.name!='simulation.sqlite3' or not database.is_relative_to(Path(tempfile.gettempdir()).resolve()) or not database.is_file():
        raise ValueError('Item-family fixture requires TEMP simulation.sqlite3')
    metadata={'visibility':'jogadores','item_type':'Poção','base_price':'2 PO','usable':True,
              'description':'Consumível sintético do ensaio; restaura 3 PV e consome um frasco.',
              'mechanics':{'consume_mode':'quantity','equipment_slots':[]},
              'effect_rules':[{'id':'fixture-restorative','trigger':'on_use','kind':'heal_hp','value':3}]}
    with closing(sqlite3.connect(database)) as db,db:
        db.execute("INSERT INTO notes(path,title,aliases,type,tags,frontmatter,content,updated_at) VALUES('Items/__fixture_restorative.md','Poção do ensaio','[]','item','[]',?,'Somente fixture; não importar na campanha.','fixture') ON CONFLICT(path) DO UPDATE SET frontmatter=excluded.frontmatter",(json.dumps(metadata),))
