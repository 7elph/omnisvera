"""Read projections of native item sources, trade metadata and private gap plans.

No alternate inventory or effect executor. Unknown prices/rules stay explicit.
"""
import hashlib,json,re,sqlite3,unicodedata
from collections import Counter
from contextlib import closing
from decimal import Decimal,ROUND_HALF_UP
from pathlib import Path
from .item_catalog import load_item_catalog,is_catalog_reference
from .merchant import COPPER_PER

GROUPS={'equipment','supplies','healing','arcane','transport','livestock','services','unclassified'}

def key(value):
    return re.sub(r'[^a-z0-9]+','-',unicodedata.normalize('NFKD',str(value)).encode('ascii','ignore').decode().lower()).strip('-')

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()

def initialize(db):
    db.execute('''CREATE TABLE IF NOT EXISTS item_trade_profiles(
      item_path TEXT PRIMARY KEY, price_copper INTEGER, trade_group TEXT NOT NULL,
      version INTEGER NOT NULL DEFAULT 1, request_id TEXT NOT NULL, updated_at TEXT NOT NULL)''')
    db.execute('CREATE TABLE IF NOT EXISTS item_trade_commands(request_id TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,response_json TEXT NOT NULL)')

def tables(db):
    return {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}

def price(raw,po=False):
    if raw is None or isinstance(raw,bool):return None
    match=re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*(PC|PP|PO|PL)?\s*',str(raw),re.I)
    if not match or (not match[2] and not po):return None
    rate={'PC':1,'PP':10,'PO':100,'PL':COPPER_PER['platinum_coins']}[str(match[2] or 'PO').upper()]
    return int((Decimal(match[1].replace(',','.'))*rate).quantize(Decimal('1'),rounding=ROUND_HALF_UP))

def group(category,name,magical=False):
    text=key(category+' '+name)
    if 'servico' in text:return 'services'
    if magical or 'magico' in text or 'grimorio' in text:return 'arcane'
    if 'pocao-de-hp' in text or 'pocao-de-cura' in text:return 'healing'
    if any(x in text for x in ['montaria','cavalo','mula','poney','ponei','animal']):return 'livestock'
    if any(x in text for x in ['carroca','barco','navio','transporte','canoa']):return 'transport'
    if any(x in text for x in ['arma','protecao','espada','adaga','arco','virote','flecha','escudo','armadura']):return 'equipment'
    if any(x in text for x in ['kit','ferramenta','racao','equipamento','mochila','corda','tocha','consumivel']):return 'supplies'
    return 'unclassified'

def registry(db,*,vault_root=None):
    """List every catalog, indexed Vault, session and held orphan identity once."""
    available=tables(db);entries={};by_path={}
    if vault_root is None:
        from .config import get_settings
        vault_root=get_settings().vault_path
    root=Path(vault_root)
    icons={}
    if 'session_workspace_icons' in available:
        icons={key(r['label']):r['path'] for r in db.execute("SELECT label,path FROM session_workspace_icons WHERE category='items'")}
    def add(identity,name,path,kind,category,raw,base_price=None,image=None,description='',rules=None,mechanics=None,reference=False):
        trade_group=group(str(category or ''),name,bool((mechanics or {}).get('magical')))
        if (mechanics or {}).get('family_schema')==1 and mechanics.get('family') in {'armor','shield','weapon','ammunition'}:trade_group='equipment'
        if not image:image=icons.get(key(name))
        if not image:
            image=next((f'zz_media/ui/icons/items/{key(name)}.{ext}' for ext in ['png','jpg','webp'] if (root/f'zz_media/ui/icons/items/{key(name)}.{ext}').is_file()),None)
        snapshot={'id':identity,'name':name,'item_path':path,'source_kind':kind,'category':category or 'item',
                  'price_copper':base_price,'trade_group':trade_group,'image_path':image,
                  'description':description,'effect_rules':rules or [],'mechanics':mechanics or {},
                  'catalog_entry_kind':'reference' if reference else 'item','source_snapshot':raw}
        snapshot['revision']=digest(snapshot)
        entries[identity]=snapshot;by_path.setdefault(path,identity)
    for item in load_item_catalog()['items']:
        add(item['id'],item['name'],item.get('native_item_path') or 'compendium:'+item['id'],item.get('source_kind','book'),item.get('category'),item,
            price(item.get('preco_po'),True),item.get('image_path'),item.get('description',''),item.get('effect_rules'),item.get('mechanics'),is_catalog_reference(item))
    if 'notes' in available:
        for row in db.execute("SELECT path,title,frontmatter,content FROM notes WHERE path LIKE 'Items/%' ORDER BY path"):
            meta=json.loads(row['frontmatter'] or '{}')
            value=next((price(meta[k],k.endswith('_po')) for k in ['base_price','preco_po','price_po','price','preco'] if meta.get(k) is not None),None)
            add('vault:'+row['path'],row['title'],row['path'],'vault',meta.get('item_type') or meta.get('item_category'),{'frontmatter':meta,'content':row['content']},
                value,meta.get('thumbnail') or meta.get('image_path') or meta.get('cover'),meta.get('description') or meta.get('summary') or '',meta.get('effect_rules'),meta.get('mechanics'))
    if 'session_custom_items' in available:
        for row in db.execute('SELECT * FROM session_custom_items ORDER BY id'):
            item=dict(row);mechanics=json.loads(item['mechanics_json'] or '{}');identity='session-item:'+str(item['id'])
            add(identity,item['name'],identity,'session',item['item_type'],item,price(mechanics.get('base_price_po'),True),item.get('image_path'),item.get('description') or '',json.loads(item['effect_rules_json'] or '[]'),mechanics)
    if 'player_inventory' in available:
        for row in db.execute('SELECT DISTINCT item_path,item_title FROM player_inventory WHERE quantity>0 ORDER BY item_path'):
            path=row['item_path']
            if path in by_path or path.startswith(('merchant:','compendium:')):continue
            add('held:'+digest(path)[:32],row['item_title'],path,'held','item',{'path':path,'name':row['item_title']})
    profiles={r['item_path']:dict(r) for r in db.execute('SELECT * FROM item_trade_profiles')} if 'item_trade_profiles' in available else {}
    # Exact native names can provide a price for common Vault goods only. Never
    # strip enchantments, suffixes or qualifiers to price a unique relic as mundane.
    common={}
    for item in entries.values():
        if item['source_kind']=='book' and item['price_copper'] is not None and item['trade_group'] in {'equipment','supplies'} and item['catalog_entry_kind']=='item':
            common.setdefault(key(item['name']),[]).append(item)
    for item in entries.values():
        profile=profiles.get(item['item_path'])
        if profile:
            item.update(price_copper=profile['price_copper'],trade_group=profile['trade_group'],valuation_source='master',trade_profile_version=profile['version'])
        elif item['source_kind']=='vault' and item['price_copper'] is None and len(common.get(key(item['name']),[]))==1:
            match=common[key(item['name'])][0];item.update(price_copper=match['price_copper'],trade_group=match['trade_group'],valuation_source=match['id'])
        item['revision']=digest({k:v for k,v in item.items() if k!='revision'})
    return {'entries':entries,'by_path':by_path}

def resolve_item(index,identity):
    if identity in index['entries']:return index['entries'][identity]
    if identity in index['by_path']:return index['entries'][index['by_path'][identity]]
    if identity.startswith('compendium:'):return index['entries'].get(identity.removeprefix('compendium:'))
    if identity.startswith('merchant:'):return index['entries'].get(identity.split(':',2)[-1])
    return None

def catalog_item(item):
    if not item:return None
    return {'id':item['id'],'name':item['name'],'category':item['category'],'preco_po':None if item['price_copper'] is None else item['price_copper']/100,
            'native_item_path':item['item_path'],'catalog_entry_kind':item['catalog_entry_kind'],'description':item['description'],
            'image_path':item.get('image_path'),'dano':(item.get('source_snapshot') or {}).get('dano')}

def allowed(merchant,item,side):
    policy=json.loads(merchant.get('trade_policy_json') or '{}')
    groups=policy.get(side)
    return groups is None or item['trade_group'] in groups

def sale_reason(item,equipped,merchant,owned=None):
    if equipped:return 'equipped'
    if owned and owned.get('_trade_condition'):return 'modified_item'
    if owned and owned.get('charges_max') is not None and owned.get('charges_current') is not None and owned['charges_current']<owned['charges_max']:return 'depleted'
    if not item or item['price_copper'] is None:return 'price_missing'
    if item['catalog_entry_kind']=='reference' or item['trade_group']=='services':return 'not_physical'
    if not allowed(merchant,item,'buy'):return 'merchant_category'
    return None

def owned_stock(db,profile_id):
    from .hp_potions import stack_sources,ITEM_PATH
    sources=stack_sources(db,profile_id);paths={r['item_path'] for r in sources}
    rows=[dict(r) for r in db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND quantity>0',(profile_id,)) if r['item_path'] not in paths]
    from .inventory_conditions import read_condition
    for row in rows:
        condition=read_condition(db,row['id'])
        if condition:row['_trade_condition']=condition
    if sources:rows.append({**dict(sources[0]),'item_path':ITEM_PATH,'item_title':'Poção de HP','equipped':False,'quantity':sum(r['quantity'] for r in sources)})
    return rows

def take_stock(db,profile_id,item_path,quantity):
    from .hp_potions import stack_sources,ITEM_PATH
    sources=stack_sources(db,profile_id) if item_path==ITEM_PATH else db.execute('SELECT * FROM player_inventory WHERE profile_id=? AND item_path=? AND quantity>0',(profile_id,item_path)).fetchall()
    if sum(r['quantity'] for r in sources)<quantity:raise ValueError('Quantidade indisponível')
    remaining=quantity;changes=[]
    for row in sources:
        spent=min(remaining,row['quantity'])
        if not spent:break
        from .merchant import _now
        db.execute('UPDATE player_inventory SET quantity=quantity-?,updated_at=? WHERE id=?',(spent,_now(),row['id']))
        changes.append({'item_path':row['item_path'],'before':row['quantity'],'after':row['quantity']-spent});remaining-=spent
    return changes

def set_trade_profile(path,access,*,item_path,price_copper,trade_group,request_id):
    if access.mode!='gm':raise PermissionError('Somente o Mestre define valores')
    if type(price_copper) is not int or not 0<=price_copper<=100000000 or trade_group not in GROUPS:raise ValueError('Preço ou categoria inválidos')
    from .merchant import _connect,_now
    from .session_ledger import append_session_ledger_event
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE');initialize(db)
        fingerprint=digest([item_path,price_copper,trade_group])
        receipt=db.execute('SELECT * FROM item_trade_commands WHERE request_id=?',(request_id,)).fetchone()
        if receipt:
            if receipt['fingerprint']!=fingerprint:raise ValueError('Requisição já usada com outros valores')
            return json.loads(receipt['response_json'])
        existing=db.execute('SELECT * FROM item_trade_profiles WHERE item_path=?',(item_path,)).fetchone()
        if existing and existing['request_id']==request_id:
            if existing['price_copper']!=price_copper or existing['trade_group']!=trade_group:raise ValueError('Requisição já usada com outros valores')
            return dict(existing)
        if not resolve_item(registry(db),item_path):raise ValueError('Item inexistente')
        db.execute('INSERT INTO item_trade_profiles VALUES(?,?,?,1,?,?) ON CONFLICT(item_path) DO UPDATE SET price_copper=excluded.price_copper,trade_group=excluded.trade_group,version=item_trade_profiles.version+1,request_id=excluded.request_id,updated_at=excluded.updated_at',(item_path,price_copper,trade_group,request_id,_now()))
        append_session_ledger_event(db,source_type='item_valuation',source_id=request_id,event_kind='state',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,title='Valor de negociação definido',detail={'item_path':item_path,'price_copper':price_copper,'trade_group':trade_group},visibility='gm',created_at=_now())
        result=dict(db.execute('SELECT * FROM item_trade_profiles WHERE item_path=?',(item_path,)).fetchone())
        db.execute('INSERT INTO item_trade_commands VALUES(?,?,?)',(request_id,fingerprint,json.dumps(result)))
        return result

def audit_items(path,*,vault_root=None):
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row;index=registry(db,vault_root=vault_root)
    items=[];plan=[]
    for item in index['entries'].values():
        reference=item['catalog_entry_kind']=='reference' or item['trade_group']=='services'
        gaps=[]
        if not reference:
            if item['price_copper'] is None:gaps.append('valuation')
            if item['trade_group']=='unclassified':gaps.append('classification')
            if not item['image_path']:gaps.append('image')
            # Descriptive text/damage is not proof that every rule is executable.
            if item['description'] and not item['effect_rules']:gaps.append('mechanics_review')
            gaps.append('test_evidence')
        record={k:v for k,v in item.items() if k!='source_snapshot'};record.update(gaps=gaps,automation_status='not_certified',requires_generation=bool(gaps));items.append(record)
        mechanics=item.get('mechanics') or {}
        if mechanics.get('family_schema')==1:
            record['runtime_support']={'schema_version':1,'family':mechanics['family'],
                'status':'native_base_rules','limitations':list(mechanics.get('family_gaps') or [])}
        for gap in gaps:
            plan.append({'item_id':item['id'],'revision':item['revision'],'gap':gap,'queue':'image' if gap=='image' else 'code' if gap in {'mechanics_review','test_evidence'} else 'text'})
    return {'schema_version':1,'total':len(items),'items':items,'gap_count':len(plan),'generation_plan':plan,'coverage':{'inventoried':len(items),'planned_gaps':len(plan)},'counts_by_source':dict(Counter(r['source_kind'] for r in items)),'production_modified':False}

def enqueue_gaps(path,workshop_path,access,*,request_id,vault_root=None):
    if access.mode!='gm':raise PermissionError('Somente o Mestre agenda propostas')
    from .ai_workshop import enqueue_job
    report=audit_items(path,vault_root=vault_root)
    with closing(sqlite3.connect(Path(path).resolve().as_uri()+'?mode=ro',uri=True)) as db:
        db.row_factory=sqlite3.Row;index=registry(db,vault_root=vault_root)
    ids=[];parents={}
    order={'classification':0,'valuation':1,'mechanics_review':2,'image':3,'test_evidence':4}
    for task in sorted(report['generation_plan'],key=lambda t:(t['item_id'],order[t['gap']])):
        item=index['entries'][task['item_id']];text=json.dumps(item,ensure_ascii=False,default=str)[:11000]
        purpose='item_'+task['gap'];identity='item:'+digest(item['id'])[:32]
        source={'path':'item-registry/'+item['id'],'sha256':hashlib.sha256(text.encode()).hexdigest(),'text':text}
        payload={'sources':[source],'facts':[item['name']],'questions':[], 'entity_type':'item','entity_id':identity,'asset_type':'icon','source_hash':task['revision'],
                 'prompt':'Proposta privada para '+item['name']+'. Resolver apenas '+task['gap']+'. Não inventar aprovação, testes executados ou regras canônicas.',
                 'context':{'item_name':item['name'],'description':item['description'][:3000],'source_revision':task['revision'],'gap':task['gap']}}
        dependencies=[parents[(task['item_id'],gap)] for gap in (['classification','mechanics_review'] if task['gap']=='test_evidence' else ['classification']) if gap!=task['gap'] and (task['item_id'],gap) in parents]
        job=enqueue_job(workshop_path,queue=task['queue'],entity_type='item',entity_id=identity,revision=task['revision'],purpose=purpose,
            request_id='item-gap-'+digest([request_id,task])[:48],gap=True,payload=payload,max_variants=0,depends_on=dependencies)['job']
        ids.append(job['id']);parents[(task['item_id'],task['gap'])]=job['id']
    return {'planned':report['gap_count'],'job_ids':ids,'published':False,'provider_calls':0}
