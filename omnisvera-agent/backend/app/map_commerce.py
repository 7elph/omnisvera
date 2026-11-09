"""Map interactions over native merchants, NPCs, inventory, purse and ledger.

Quotes are server priced and expire after ten minutes. One bargain per item,
character and merchant until the Master's rest; another quote cannot reroll it.
Lodging reserves a stay; only the existing Master's rest completes it.
"""
import hashlib
import json
import re
import sqlite3
import time
import uuid
from contextlib import closing
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path

from .access import AccessContext
from .dice_rolls import roll_formula
from .item_catalog import get_catalog_item, item_offer_readiness, require_offerable_item
from .merchant import (_connect, _now, _character_state, _character_sheet, _save_purse,
                       _inventory_get, _inventory_upsert, purse_copper, init_merchants, HAGGLE_TIERS)
from .session_ledger import append_session_ledger_event


def initialize(path):
    init_merchants(path)
    with closing(_connect(path)) as db, db:
        columns={row[1] for row in db.execute('PRAGMA table_info(merchants)')}
        for name,definition in [('token_id','TEXT'),('npc_id','INTEGER'),('location_id','INTEGER'),('enabled','INTEGER NOT NULL DEFAULT 0'),('trade_policy_json',"TEXT NOT NULL DEFAULT '{}'")]:
            if name not in columns: db.execute(f'ALTER TABLE merchants ADD COLUMN {name} {definition}')
        from .item_registry import initialize as init_item_registry
        init_item_registry(db)
        from .merchant_appraisals import initialize as init_appraisals
        init_appraisals(db)
        service_columns={row[1] for row in db.execute('PRAGMA table_info(merchant_services)')}
        if service_columns and 'stock_id' not in service_columns:db.execute('ALTER TABLE merchant_services ADD COLUMN stock_id TEXT')
        if service_columns and 'spell_id' not in service_columns:db.execute('ALTER TABLE merchant_services ADD COLUMN spell_id TEXT')
        db.executescript('''
          CREATE TABLE IF NOT EXISTS merchant_quotes (
            id TEXT PRIMARY KEY, actor_id TEXT NOT NULL, fingerprint TEXT NOT NULL,
            request_id TEXT NOT NULL, data_json TEXT NOT NULL, expires_at REAL NOT NULL,
            receipt_json TEXT, UNIQUE(actor_id,request_id));
          CREATE TABLE IF NOT EXISTS merchant_commands (
            actor_id TEXT NOT NULL, request_id TEXT NOT NULL, quote_id TEXT NOT NULL,
            response_json TEXT NOT NULL, PRIMARY KEY(actor_id,request_id));
          CREATE TABLE IF NOT EXISTS merchant_bargains (
            bargain_key TEXT PRIMARY KEY, result_json TEXT NOT NULL);
          CREATE TABLE IF NOT EXISTS merchant_services (
            id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, name TEXT NOT NULL,
            kind TEXT NOT NULL, price_copper INTEGER NOT NULL, compendium_item_id TEXT,
            amount INTEGER NOT NULL DEFAULT 1, active INTEGER NOT NULL DEFAULT 1, stock_id TEXT,spell_id TEXT);
          CREATE TABLE IF NOT EXISTS merchant_service_orders (
            id TEXT PRIMARY KEY, merchant_id TEXT NOT NULL, character_id TEXT NOT NULL,
            name TEXT NOT NULL, status TEXT NOT NULL, created_at TEXT NOT NULL, completed_at TEXT);
        ''')


def _actor(access): return f'{access.mode}:{access.profile_id or "master"}'


def appraise_item(path,mid,access,**fields):
    from .merchant_appraisals import appraise
    return appraise(path,mid,access,**fields)


def _owner(access, character_id):
    if access.mode!='gm' and (not access.profile_id or access.profile_id!=character_id):
        raise PermissionError('Você só pode negociar pela sua própria ficha')


def _copper(price):
    value=Decimal(str(price))
    if not value.is_finite() or value<0: raise ValueError('Preço inválido')
    return int((value*100).quantize(Decimal('1'),rounding=ROUND_HALF_UP))


def _merchant(db, mid, access):
    row=db.execute('SELECT * FROM merchants WHERE id=?',(mid,)).fetchone()
    if not row: raise ValueError('Mercador não encontrado')
    m=dict(row)
    if access.mode=='gm': return m
    pin=db.execute('SELECT * FROM session_workspace_tokens WHERE id=?',(m['token_id'],)).fetchone()
    active=db.execute('SELECT map_id FROM session_workspace_state WHERE id=1').fetchone()
    if not m['enabled'] or not pin or not pin['visible_to_players'] or not active or pin['map_id']!=active[0]:
        raise PermissionError('Este estabelecimento não está disponível neste mapa')
    map_row=db.execute('SELECT visible_to_players FROM session_workspace_maps WHERE id=?',(pin['map_id'],)).fetchone()
    if not map_row or not map_row[0]: raise PermissionError('Mapa não revelado')
    if m['npc_id']:
        npc=db.execute('SELECT d.visible_to_players,s.active FROM npc_definitions d JOIN npc_states s ON s.npc_id=d.id WHERE d.id=?',(m['npc_id'],)).fetchone()
        if not npc or not npc[0] or not npc[1]: raise PermissionError('NPC indisponível')
    if m['location_id']:
        location=db.execute('SELECT visibility,active FROM world_locations WHERE id=?',(m['location_id'],)).fetchone()
        if not location or location['visibility'] not in {'table','public'} or not location['active']:
            raise PermissionError('Local não revelado')
    return m


def configure(path, mid, access, *, token_id, npc_id=None, location_id=None, enabled=True, buy_pct=50,policy=None):
    if access.mode!='gm': raise PermissionError('Somente o Mestre configura ofertas')
    if not 0<=buy_pct<=100: raise ValueError('Percentual de recompra inválido')
    from .item_registry import GROUPS
    if policy is not None and (set(policy)-{'buy','sell'} or any(not isinstance(v,list) or set(v)-GROUPS for v in policy.values())):raise ValueError('Categorias de comércio inválidas')
    initialize(path)
    with closing(_connect(path)) as db, db:
        _merchant(db,mid,access)
        pin=db.execute('SELECT token_type FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()
        if not pin or pin[0]=='character': raise ValueError('Escolha um pin de NPC ou local existente')
        for table,value in [('npc_definitions',npc_id),('world_locations',location_id)]:
            if value and not db.execute(f'SELECT id FROM {table} WHERE id=?',(value,)).fetchone():
                raise ValueError('NPC/local inexistente')
        db.execute('UPDATE merchants SET token_id=?,npc_id=?,location_id=?,enabled=?,buy_pct=? WHERE id=?',
            (token_id,npc_id,location_id,int(enabled),buy_pct,mid))
        if policy is not None:db.execute('UPDATE merchants SET trade_policy_json=? WHERE id=?',(json.dumps(policy),mid))
        _ledger(db,access,'setup:'+uuid.uuid4().hex,None,'Ofertas do estabelecimento atualizadas',{'merchant_id':mid},'gm')
    return {'id':mid,'token_id':token_id,'npc_id':npc_id,'location_id':location_id,'enabled':enabled,'buy_pct':buy_pct}


def add_service(path,mid,access,*,name,kind,price_copper,compendium_item_id=None,amount=1,stock_id=None,spell_id=None):
    if access.mode!='gm': raise PermissionError('Somente o Mestre configura serviços')
    if kind not in {'delivery','lodging','appraisal','spell','repair'} or not name.strip() or type(price_copper)!=int or price_copper<0 or not 1<=amount<=999:
        raise ValueError('Serviço inválido')
    if kind=='repair' and (amount!=1 or compendium_item_id or stock_id or spell_id):
        raise ValueError('Reparo atende um item por orçamento, sem entrega ou recarga')
    initialize(path)
    with closing(_connect(path)) as db,db:
        merchant=_merchant(db,mid,access)
        from .item_registry import registry
        index=registry(db)
        data={'name':name.strip(),'kind':kind,'price_copper':price_copper,'compendium_item_id':compendium_item_id,'amount':amount,'stock_id':stock_id,'spell_id':spell_id}
        _require_service(data,index,merchant)
        if stock_id:
            stock=db.execute('SELECT * FROM merchant_stock WHERE id=? AND merchant_id=?',(stock_id,mid)).fetchone()
            if kind!='delivery' or not stock or stock['instance_json'] or stock['compendium_item_id']!=compendium_item_id:raise ValueError('Estoque do serviço incompatível')
        identity='service-'+uuid.uuid4().hex
        db.execute('INSERT INTO merchant_services(id,merchant_id,name,kind,price_copper,compendium_item_id,amount,active,stock_id,spell_id) VALUES(?,?,?,?,?,?,?,1,?,?)',
            (identity,mid,name.strip(),kind,price_copper,compendium_item_id,amount,stock_id,spell_id))
        _ledger(db,access,'service:'+identity,None,'Serviço cadastrado',{'merchant_id':mid,'service_id':identity},'gm')
        return {'id':identity,**data}


def _price_line(row,index=None):
    from .item_registry import resolve_item,catalog_item
    item=catalog_item(resolve_item(index,row['compendium_item_id'])) if index else get_catalog_item(row['compendium_item_id'])
    ready = require_offerable_item(item, price_override_po=row['price_override_po'])
    return _copper(ready['price_po'])


def _service_readiness(row,index=None,merchant=None):
    from .item_registry import resolve_item,catalog_item,allowed
    price=row['price_copper'];valid_price=type(price) is int and 0<=price<=100000000
    if row['kind']=='repair':
        return {'commerce_ready':valid_price,'blocking_gaps':[] if valid_price else ['preco_invalido'],'effect_status':'rust_repair'}
    if row['kind']=='spell':
        from .merchant_magic import specification
        try:spec=specification(row['spell_id'])
        except ValueError:return {'commerce_ready':False,'blocking_gaps':['magia_sem_contrato_revisado'],'effect_status':'blocked'}
        return {'commerce_ready':valid_price,'blocking_gaps':[] if valid_price else ['preco_cobre_invalido'],'effect_status':spec['contract']['family']}
    if row['kind']=='appraisal':
        return {'commerce_ready':valid_price,'blocking_gaps':[] if valid_price else ['preco_cobre_invalido'],'effect_status':'inventory_valuation'}
    native=resolve_item(index,row['compendium_item_id']) if index and row['kind']=='delivery' else None
    item=(catalog_item(native) if index else get_catalog_item(row['compendium_item_id'])) if row['kind']=='delivery' else {'name':row['name'],'category':'hospedagem','preco_po':0}
    result=item_offer_readiness(item,price_override_po=price/100 if valid_price else -1)
    if row['kind'] not in {'delivery','lodging'}:result['blocking_gaps'].append('tipo_servico_sem_executor')
    if not valid_price:result['blocking_gaps'].append('preco_cobre_invalido')
    if merchant and native and not allowed(merchant,native,'sell'):result['blocking_gaps'].append('merchant_category')
    result['commerce_ready']=not result['blocking_gaps']
    result['effect_status']='delivery_only' if row['kind']=='delivery' else 'lodging_reservation_only'
    return result


def _require_service(row,index=None,merchant=None):
    report=_service_readiness(row,index,merchant)
    if not report['commerce_ready']:
        if 'entrada_de_tabela_nao_concreta' in report['blocking_gaps']:
            raise ValueError('Serviço entrega referência de tabela, não um item concreto')
        raise ValueError('Serviço com item, preço ou categoria incompatível; confira o cadastro')
    return report


def catalog_inventory(path):
    """Preserve catalog identity/mechanics through native inventory enrichment."""
    item_id=path.removeprefix('compendium:') if path.startswith('compendium:') else path.split(':',2)[-1] if path.startswith('merchant:') else ''
    item=get_catalog_item(item_id)
    if not item: return None
    from .item_families import descriptor
    return descriptor(item)


def sale_value(db,merchant,item,index):
    """A campaign shop discount must not become book-price buyback arbitrage."""
    from .item_registry import resolve_item
    base=item['price_copper'];stock_ids=[]
    for row in db.execute('SELECT * FROM merchant_stock WHERE merchant_id=?',(merchant['id'],)):
        candidate=resolve_item(index,row['compendium_item_id'])
        if candidate and candidate['id']==item['id'] and row['price_override_po'] is not None:
            local=_copper(row['price_override_po'])
            if local<base:base=local
            stock_ids.append(row['id'])
    return {'base_value_copper':base,'buy_pct':merchant['buy_pct'],'stock_ids':sorted(stock_ids),'unit_copper':base*merchant['buy_pct']//100}


def for_pin(path,token_id,access,character_id=None):
    initialize(path)
    if character_id: _owner(access,character_id)
    with closing(_connect(path)) as db:
        from .item_registry import registry,resolve_item,catalog_item,owned_stock,sale_reason,allowed
        index=registry(db)
        result=[]
        for row in db.execute('SELECT id FROM merchants WHERE token_id=? ORDER BY name',(token_id,)).fetchall():
            try: m=_merchant(db,row[0],access)
            except PermissionError: continue
            offers=[]
            blocked=[]
            for line in db.execute('SELECT * FROM merchant_stock WHERE merchant_id=?',(m['id'],)):
                if line['instance_json']:
                    blocked.append({'id':line['id'],'name':line['name'],'quantity':line['quantity'],'kind':'buy','instance':json.loads(line['instance_json']),'readiness':{'commerce_ready':False,'blocking_gaps':['instancia_aguardando_avaliacao_de_revenda']}})
                    continue
                item=resolve_item(index,line['compendium_item_id'])
                readiness=item_offer_readiness(catalog_item(item),price_override_po=line['price_override_po'])
                if item and not allowed(m,item,'sell'):
                    readiness={**readiness,'commerce_ready':False,'blocking_gaps':[*readiness['blocking_gaps'],'merchant_category']}
                if not readiness['commerce_ready']:
                    blocked.append({'id':line['id'],'name':line['name'],'kind':'buy','readiness':readiness})
                    continue
                price=_copper(readiness['price_po'])
                offers.append({'id':line['id'],'name':line['name'],'quantity':line['quantity'],
                    'price_copper':price,'image_path':(item or {}).get('image_path'),'trade_group':(item or {}).get('trade_group'),'description':(item or {}).get('description',''),'kind':'buy','readiness':readiness})
            services=[]
            for service in db.execute('SELECT * FROM merchant_services WHERE merchant_id=? AND active=1',(m['id'],)):
                readiness=_service_readiness(service,index,m)
                if not readiness['commerce_ready']:
                    blocked.append({'id':service['id'],'name':service['name'],'kind':'service','readiness':readiness})
                    continue
                availability={}
                if service['kind']=='spell' and character_id:
                    from .merchant_magic import require_target,specification
                    try:require_target(db,character_id,specification(service['spell_id']))
                    except ValueError as error:availability={'available':False,'unavailable_reason':str(error)}
                if service['kind']=='repair':
                    from .merchant_repairs import available
                    repair_items=available(db,character_id)
                    availability={'repair_items':repair_items,'available':bool(repair_items)}
                    if not repair_items:availability['unavailable_reason']='Sem item com encantamento corroído verificado; não repara em combate'
                services.append({**{key:service[key] for key in ('id','name','kind','price_copper','amount','spell_id')},'readiness':readiness,**availability})
            sellable=[];blocked_sales=[]
            if character_id:
                for owned in owned_stock(db,character_id):
                    item=resolve_item(index,owned['item_path']);reason=sale_reason(item,owned['equipped'],m,owned)
                    from .merchant_appraisals import active
                    individual=active(db,m,character_id,owned,item) if item else None
                    if individual:reason=None
                    if not reason:
                        sellable.append({'id':owned['item_path'],'name':owned['item_title'],'quantity':owned['quantity'],
                            'price_copper':individual['unit_copper'] if individual else sale_value(db,m,item,index)['unit_copper'],'image_path':item.get('image_path'),'trade_group':item['trade_group'],'kind':'sell','individual_appraisal':bool(individual)})
                    else:blocked_sales.append({'id':owned['item_path'],'name':owned['item_title'],'quantity':owned['quantity'],'reason':reason})
            entry={k:m[k] for k in ('id','name','location','token_id','enabled','buy_pct')}
            entry.update(offers=offers,services=services,sellable=sellable,blocked_sales=blocked_sales,trade_policy=json.loads(m.get('trade_policy_json') or '{}'))
            if m['npc_id']:
                public_npc=db.execute('SELECT name,portrait_path,public_description FROM npc_definitions WHERE id=?',(m['npc_id'],)).fetchone()
                if public_npc:entry['responsible_npc']=dict(public_npc)
            if access.mode=='gm':
                entry.update(npc_id=m['npc_id'],location_id=m['location_id'],blocked_offers=blocked)
                if entry.get('responsible_npc'):
                    children=[r['id'] for r in db.execute("SELECT id,sheet_json FROM session_workspace_tokens WHERE token_type='monster' AND name=?",(entry['responsible_npc']['name'],)) if json.loads(r['sheet_json'] or '{}').get('embedded_in_location')==token_id]
                    if len(children)==1:entry['responsible_npc']['combat_token_id']=children[0]
            result.append(entry)
        return result


def _offer(db,m,character_id,kind,target_id,index=None,inventory_id=None):
    from .item_registry import registry,resolve_item,catalog_item,allowed,owned_stock,sale_reason
    index=index or registry(db)
    if kind=='buy':
        row=db.execute('SELECT * FROM merchant_stock WHERE id=? AND merchant_id=?',(target_id,m['id'])).fetchone()
        if not row: raise ValueError('Oferta removida')
        if row['instance_json']:raise ValueError('Objeto adquirido no estado atual: não disponível como item novo')
        item=resolve_item(index,row['compendium_item_id'])
        if item and not allowed(m,item,'sell'):raise ValueError('Este estabelecimento não vende este tipo de item')
        return {'name':row['name'],'base_unit_copper':_price_line(row,index),'catalog_id':row['compendium_item_id'],'item_revision':item['revision'] if item else None}
    if kind=='sell':
        row=next((r for r in owned_stock(db,character_id) if r['item_path']==target_id),None)
        item=resolve_item(index,target_id)
        if not row or row['quantity']<1:raise ValueError('Item indisponível')
        reason=sale_reason(item,row['equipped'],m,row)
        from .merchant_appraisals import active
        individual=active(db,m,character_id,row,item) if item else None
        if individual:
            return {'name':row['item_title'],'base_unit_copper':individual['unit_copper'],'valuation':{'source':'master_individual_offer','unit_copper':individual['unit_copper']},'individual_appraisal':individual,'catalog_id':item['id'],'item_revision':item['revision']}
        if reason:raise ValueError({'equipped':'Guarde o item antes de vender','price_missing':'O Mestre precisa avaliar o preço deste item','merchant_category':'Este estabelecimento não compra este tipo de item','not_physical':'Serviço não é um item físico','depleted':'Item com cargas usadas: precisa de avaliação individual','modified_item':'Item modificado: venda individual ainda não suportada'}[reason])
        valuation=sale_value(db,m,item,index)
        return {'name':row['item_title'],'base_unit_copper':valuation['unit_copper'],'valuation':valuation,'catalog_id':item['id'],'item_revision':item['revision']}
    if kind=='service':
        row=db.execute('SELECT * FROM merchant_services WHERE id=? AND merchant_id=? AND active=1',(target_id,m['id'])).fetchone()
        if not row: raise ValueError('Serviço indisponível')
        _require_service(row,index,m)
        repair_target=None
        if inventory_id is not None and row['kind']!='repair':
            raise ValueError('Este serviço não recebe item para reparar')
        if row['kind']=='repair':
            from .merchant_repairs import preview
            repair_target=preview(db,character_id,inventory_id)
        if row['kind']=='spell':
            from .merchant_magic import require_target,specification
            require_target(db,character_id,specification(row['spell_id']))
        if row['stock_id']:
            stock=db.execute('SELECT quantity,instance_json FROM merchant_stock WHERE id=? AND merchant_id=?',(row['stock_id'],m['id'])).fetchone()
            if not stock or stock['instance_json'] or stock['quantity']!=-1 and stock['quantity']<row['amount']:raise ValueError('Estoque do serviço insuficiente')
        return {'name':row['name'],'base_unit_copper':row['price_copper'],'service':dict(row),**({'repair_target':repair_target} if repair_target else {})}
    raise ValueError('Operação inválida')


def offer_readiness_report(path, access):
    """GM-only read-only inventory of existing offers; never creates stock/schema."""
    if access.mode != 'gm':
        raise PermissionError('Somente o Mestre consulta lacunas de ofertas')
    uri = Path(path).resolve().as_uri() + '?mode=ro'
    rows=[]
    with closing(sqlite3.connect(uri,uri=True)) as db:
        db.row_factory=sqlite3.Row
        tables={r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'merchant_stock' in tables:
            for line in db.execute('SELECT * FROM merchant_stock ORDER BY merchant_id,id'):
                if 'instance_json' in line.keys() and line['instance_json']:
                    rows.append({'id':line['id'],'merchant_id':line['merchant_id'],'catalog_id':line['compendium_item_id'],'name':line['name'],'kind':'buy','readiness':{'commerce_ready':False,'blocking_gaps':['instancia_aguardando_avaliacao_de_revenda'],'effect_status':'individual_review'}})
                    continue
                rows.append({'id':line['id'],'merchant_id':line['merchant_id'],'catalog_id':line['compendium_item_id'],
                    'name':line['name'],'kind':'buy','readiness':item_offer_readiness(
                        get_catalog_item(line['compendium_item_id']),price_override_po=line['price_override_po'])})
        if 'merchant_services' in tables:
            for line in db.execute('SELECT * FROM merchant_services WHERE active=1 ORDER BY merchant_id,id'):
                rows.append({'id':line['id'],'merchant_id':line['merchant_id'],'catalog_id':line['compendium_item_id'],
                    'name':line['name'],'kind':'service','readiness':_service_readiness(line)})
    blocked=sum(not entry['readiness']['commerce_ready'] for entry in rows)
    return {'mode':'read_only_offer_inventory','production_modified':False,'offers':rows,
        'counts':{'total':len(rows),'ready_for_commerce':len(rows)-blocked,'blocked':blocked},
        'automation_status':'not_certified'}


def _ledger(db,access,key,character_id,title,detail,visibility='table'):
    if db.execute("SELECT 1 FROM session_ledger WHERE source_type='commerce' AND source_id=?",(key,)).fetchone(): return
    append_session_ledger_event(db,source_type='commerce',source_id=key,event_kind='state',
        actor_id=access.profile_id or 'master',actor_name=access.character_title or access.profile_id or 'Mestre',
        actor_role=access.mode,character_id=character_id,title=title,detail=detail,visibility=visibility,created_at=_now())


def quote(path,mid,access,*,request_id,character_id,kind,target_id,quantity=1,negotiate=False,inventory_id=None):
    _owner(access,character_id)
    if not 8<=len(request_id)<=120 or type(quantity)!=int or not 1<=quantity<=999: raise ValueError('Quantidade/identificador inválido')
    if inventory_id is not None and (kind!='service' or type(inventory_id) is not int or inventory_id<=0):raise ValueError('Item de reparo inválido')
    initialize(path)
    actor=_actor(access)
    fingerprint=json.dumps([mid,character_id,kind,target_id,quantity,negotiate]+([inventory_id] if inventory_id is not None else []))
    with closing(_connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        m=_merchant(db,mid,access)
        state=_character_state(db,character_id)
        previous=db.execute('SELECT * FROM merchant_quotes WHERE actor_id=? AND request_id=?',(actor,request_id)).fetchone()
        if previous:
            if previous['fingerprint']!=fingerprint: raise ValueError('Identificador já usado com outro conteúdo')
            return json.loads(previous['data_json'])
        from .item_registry import registry
        bargain_index=registry(db) if negotiate else None
        offer=_offer(db,m,character_id,kind,target_id,index=bargain_index,inventory_id=inventory_id)
        if kind=='sell':
            from .item_registry import owned_stock
            available=next((r['quantity'] for r in owned_stock(db,character_id) if r['item_path']==target_id),0)
            if quantity>available:raise ValueError('Quantidade indisponível')
        if kind=='service' and quantity!=1: raise ValueError('Contrate um serviço por vez')
        if kind=='buy':
            stock=db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(target_id,)).fetchone()[0]
            if stock!=-1 and stock<quantity: raise ValueError('Estoque insuficiente')
        bargain=None
        key=json.dumps([mid,character_id,offer.get('catalog_id'),state.get('commerce_rest_epoch',0)])
        if negotiate and kind!='buy': raise ValueError('A barganha está disponível para compras de itens')
        if kind=='buy':
            old=db.execute('SELECT result_json FROM merchant_bargains WHERE bargain_key=?',(key,)).fetchone()
            if old: bargain=json.loads(old[0])
            elif negotiate:
                from .character_play import attribute_modifier
                data=_character_sheet(db,character_id)
                attrs={**data['sheet'].get('attributes',{}),**data['overrides'].get('attributes',{})}
                from .magic_passives import attribute_check_modifier
                mod=attribute_check_modifier(db,character_id,attrs,'charisma',index=bargain_index)
                roll=int(roll_formula('1d20')['total']); total=roll+mod
                multiplier,label=next(((mult,label) for floor,mult,label in HAGGLE_TIERS if total>=floor),(1.1,'+10%'))
                bargain={'d20':roll,'modifier':mod,'total':total,'multiplier':multiplier,'label':label}
                db.execute('INSERT INTO merchant_bargains VALUES(?,?)',(key,json.dumps(bargain)))
        unit=int((Decimal(offer['base_unit_copper'])*Decimal(str(bargain['multiplier'] if bargain else 1))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        expires=time.time()+600
        result={'id':uuid.uuid4().hex,'merchant_id':mid,'character_id':character_id,'kind':kind,
            'target_id':target_id,'quantity':quantity,**offer,'unit_copper':unit,'total_copper':unit*quantity,
            'bargain':bargain,'expires_at':expires}
        result['rest_epoch']=state.get('commerce_rest_epoch',0)
        db.execute('INSERT INTO merchant_quotes(id,actor_id,fingerprint,request_id,data_json,expires_at) VALUES(?,?,?,?,?,?)',
            (result['id'],actor,fingerprint,request_id,json.dumps(result),expires))
        if bargain:
            _ledger(db,access,'bargain:'+hashlib.sha256(key.encode()).hexdigest(),character_id,
                f'{character_id} negociou {offer["name"]}: d20 {bargain["d20"]} + {bargain["modifier"]} = {bargain["total"]} ({bargain["label"]})',bargain)
        return result


def _give(db,character_id,catalog_id,quantity,index=None):
    from .item_registry import registry,resolve_item
    from .item_transfer import grant_item
    item=resolve_item(index or registry(db),catalog_id)
    if not item:raise ValueError('Item de entrega inexistente')
    return [grant_item(db,item,character_id,quantity,_now(),origin='Compra no mercado')]


def confirm(path,quote_id,access,*,request_id):
    if not 8<=len(request_id)<=120: raise ValueError('Identificador inválido')
    initialize(path)
    with closing(_connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        row=db.execute('SELECT * FROM merchant_quotes WHERE id=?',(quote_id,)).fetchone()
        if not row or row['actor_id']!=_actor(access): raise PermissionError('Negociação pertence a outro acesso')
        q=json.loads(row['data_json']); _owner(access,q['character_id'])
        previous=db.execute('SELECT * FROM merchant_commands WHERE actor_id=? AND request_id=?',(_actor(access),request_id)).fetchone()
        if previous:
            if previous['quote_id']!=quote_id: raise ValueError('Identificador já usado com outra negociação')
            return json.loads(previous['response_json'])
        if row['receipt_json']:
            response=row['receipt_json']
            db.execute('INSERT INTO merchant_commands VALUES(?,?,?,?)',(_actor(access),request_id,quote_id,response))
            return json.loads(response)
        if row['expires_at']<time.time(): raise ValueError('Negociação expirou; consulte as ofertas novamente')
        m=_merchant(db,q['merchant_id'],access)
        from .item_registry import registry
        index=registry(db)
        offer=_offer(db,m,q['character_id'],q['kind'],q['target_id'],index,inventory_id=(q.get('repair_target') or {}).get('inventory_id'))
        if any(offer.get(k)!=q.get(k) for k in ('base_unit_copper','catalog_id','service','item_revision','valuation','individual_appraisal','repair_target')):
            raise ValueError('Oferta alterada; consulte o novo preço')
        state=_character_state(db,q['character_id']); balance=purse_copper(state)
        purse_before={key:int(state.get(key) or 0) for key in ('copper_coins','silver_coins','coins','platinum_coins')}
        if state.get('commerce_rest_epoch',0)!=q.get('rest_epoch',0):
            raise ValueError('Um novo descanso ocorreu; consulte as ofertas novamente')
        if q['kind']=='buy':
            bargain_key=json.dumps([m['id'],q['character_id'],q.get('catalog_id'),state.get('commerce_rest_epoch',0)])
            bargain=db.execute('SELECT result_json FROM merchant_bargains WHERE bargain_key=?',(bargain_key,)).fetchone()
            if bargain and json.loads(bargain[0])!=q.get('bargain'):
                raise ValueError('A negociação mudou; consulte o preço negociado')
        qty=q['quantity']; kind=q['kind']; cost=q['total_copper']
        if kind!='sell' and balance<cost: raise ValueError('Saldo insuficiente')
        status=None;inventory_changes=[];stock_before=None;stock_after=None;appraisal=None;stock_id=None;service_effect=None;instance=None
        if kind=='buy':
            stock=db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(q['target_id'],)).fetchone()[0]
            stock_before=stock;stock_after=stock-qty if stock!=-1 else -1
            if stock!=-1 and stock<qty: raise ValueError('Estoque insuficiente')
            if stock!=-1: db.execute('UPDATE merchant_stock SET quantity=quantity-? WHERE id=?',(qty,q['target_id']))
            inventory_changes=_give(db,q['character_id'],q['catalog_id'],qty,index);stock_id=q['target_id']
        elif kind=='sell':
            from .item_registry import take_stock,owned_stock
            owned=next(o for o in owned_stock(db,q['character_id']) if o['item_path']==q['target_id'])
            inventory_changes=take_stock(db,q['character_id'],q['target_id'],qty)
            stock=db.execute("SELECT id,quantity FROM merchant_stock WHERE merchant_id=? AND compendium_item_id=? AND COALESCE(instance_json,'')='' ORDER BY id LIMIT 1",(m['id'],q['catalog_id'])).fetchone()
            stock_before=stock['quantity'] if stock else 0;stock_after=stock_before+qty if stock_before!=-1 else -1
            stock_id=stock['id'] if stock else 'stock-'+uuid.uuid4().hex
            if q.get('individual_appraisal'):
                from .merchant_appraisals import hold_instance
                stock_id,instance=hold_instance(db,m['id'],q,owned,_now());stock_before=0;stock_after=qty
            elif stock:
                if stock['quantity']!=-1: db.execute('UPDATE merchant_stock SET quantity=quantity+? WHERE id=?',(qty,stock['id']))
            else: db.execute('INSERT INTO merchant_stock(id,merchant_id,compendium_item_id,name,quantity,created_at) VALUES(?,?,?,?,?,?)',(stock_id,m['id'],q['catalog_id'],q['name'],qty,_now()))
        else:
            service=offer['service']
            if service['kind']=='spell':
                from .merchant_magic import apply
                service_effect=apply(db,q['character_id'],service['spell_id'],_now());status='completed'
            elif service['kind']=='repair':
                from .merchant_repairs import apply
                service_effect=apply(db,q['character_id'],offer['repair_target'],_now());status='completed'
            elif service['kind']=='delivery':
                if service.get('stock_id'):
                    stock_id=service['stock_id'];stock=db.execute('SELECT quantity FROM merchant_stock WHERE id=?',(stock_id,)).fetchone()
                    stock_before=stock['quantity'];stock_after=stock_before-service['amount'] if stock_before!=-1 else -1
                    if stock_before!=-1:db.execute('UPDATE merchant_stock SET quantity=? WHERE id=?',(stock_after,stock_id))
                inventory_changes=_give(db,q['character_id'],service['compendium_item_id'],service['amount'],index);status='completed'
            elif service['kind']=='appraisal':
                from .item_registry import owned_stock,resolve_item,sale_reason
                appraisal=[]
                for owned in owned_stock(db,q['character_id']):
                    item=resolve_item(index,owned['item_path']);reason=sale_reason(item,owned['equipped'],m,owned)
                    appraisal.append({'id':owned['item_path'],'name':owned['item_title'],'quantity':owned['quantity'],'price_copper':sale_value(db,m,item,index)['unit_copper'] if item and item['price_copper'] is not None else None,'reason':reason})
                status='completed'
            else:
                if db.execute("SELECT 1 FROM merchant_service_orders WHERE character_id=? AND status='reserved'",(q['character_id'],)).fetchone():
                    raise ValueError('Você já tem hospedagem reservada para o próximo descanso')
                db.execute('INSERT INTO merchant_service_orders VALUES(?,?,?,?,?,?,NULL)',(quote_id,m['id'],q['character_id'],q['name'],'reserved',_now()))
                status='reserved'
        purse=_save_purse(db,q['character_id'],balance+cost if kind=='sell' else balance-cost) if cost or (service_effect or {}).get('family')=='rust_repair' else purse_before
        response={'receipt_id':quote_id,'merchant_id':m['id'],'character_id':q['character_id'],'audit_schema_version':1,'kind':kind,'name':q['name'],'quantity':qty,'total_copper':cost,
            'purse_before':purse_before,'purse_after':purse,'balance_before_copper':balance,'balance_after_copper':purse_copper(purse),
            'appraisal':appraisal,'stock_id':stock_id,'inventory_changes':inventory_changes,'stock_before':stock_before,'stock_after':stock_after,'item_revision':q.get('item_revision'),
            'valuation':q.get('valuation'),'unit_copper':q['unit_copper'],'catalog_id':q.get('catalog_id'),'base_unit_copper':q['base_unit_copper'],
            'individual_appraisal':q.get('individual_appraisal'),'stock_instance':instance,'service_effect':service_effect,
            'service_status':status,'bargain':q.get('bargain')}
        from .currency import rule_snapshot
        response['currency_rule'] = rule_snapshot()
        verb={'buy':'comprou','sell':'vendeu','service':'contratou'}[kind]
        title=f'{q["character_id"]} {verb} {qty}× {q["name"]} por {cost/100:g} PO'
        if (service_effect or {}).get('family')=='rust_repair':
            title+=f" · {service_effect['name']}: encantamento +{service_effect['bonus_before']} → +{service_effect['bonus_after']}"
        _ledger(db,access,quote_id,q['character_id'],title,response)
        if m['npc_id']:
            from .npc_memory import _event
            _event(db,event_key='commerce:'+quote_id,npc_id=m['npc_id'],actor_id=access.profile_id or 'master',
                actor_role=access.mode,event_type='commerce',title=title,public_text=title,character_id=q['character_id'],visibility='table')
        encoded=json.dumps(response)
        db.execute('UPDATE merchant_quotes SET receipt_json=? WHERE id=?',(encoded,quote_id))
        db.execute('INSERT INTO merchant_commands VALUES(?,?,?,?)',(_actor(access),request_id,quote_id,encoded))
        return response


def complete_lodging(db,character_id):
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='merchant_service_orders'").fetchone(): return
    for order in db.execute("SELECT * FROM merchant_service_orders WHERE character_id=? AND status='reserved'",(character_id,)).fetchall():
        db.execute("UPDATE merchant_service_orders SET status='completed',completed_at=? WHERE id=?",(_now(),order['id']))
        _ledger(db,AccessContext(mode='gm'),'stay:'+order['id'],character_id,
            f'{character_id} concluiu {order["name"]} no descanso concedido pelo Mestre',{'service_order':order['id']})


def remove_service(path,mid,service_id,access):
    if access.mode!='gm': raise PermissionError('Somente o Mestre configura serviços')
    initialize(path)
    with closing(_connect(path)) as db, db:
        if not db.execute('UPDATE merchant_services SET active=0 WHERE id=? AND merchant_id=?',(service_id,mid)).rowcount:
            raise ValueError('Serviço inexistente')
        _ledger(db,access,'service-remove:'+uuid.uuid4().hex,None,'Serviço retirado das ofertas',{'merchant_id':mid},'gm')
    return {'removed':service_id}


def history(path,access,character_id,limit=40):
    """Owner/GM receipt projection. Old partial receipts remain honestly marked."""
    _owner(access,character_id)
    with closing(_connect(path)) as db:
        rows=db.execute("SELECT id,title,detail_json,created_at FROM session_ledger WHERE source_type IN ('commerce','commerce_refund','merchant_buy','merchant_sell') AND character_id=? AND voided_at IS NULL ORDER BY id DESC LIMIT ?",(character_id,min(100,max(1,int(limit))))).fetchall()
        result=[]
        for row in rows:
            receipt=json.loads(row['detail_json'] or '{}')
            complete=receipt.get('audit_schema_version')==1 and 'purse_before' in receipt
            result.append({**receipt,'ledger_id':row['id'],'title':row['title'],'created_at':row['created_at'],'audit_status':'complete' if complete else 'legacy_partial'})
        return result
