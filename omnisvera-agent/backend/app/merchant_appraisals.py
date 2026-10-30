"""A Master's final offer for one native inventory instance, never a price rule."""
import json,time,uuid
from .item_registry import digest,allowed


def initialize(db):
    columns={r[1] for r in db.execute('PRAGMA table_info(merchant_stock)')}
    if 'instance_json' not in columns:db.execute('ALTER TABLE merchant_stock ADD COLUMN instance_json TEXT')
    db.execute('''CREATE TABLE IF NOT EXISTS merchant_item_appraisals(
      id TEXT PRIMARY KEY,merchant_id TEXT NOT NULL,character_id TEXT NOT NULL,
      item_path TEXT NOT NULL,unit_copper INTEGER NOT NULL,snapshot_hash TEXT NOT NULL,
      request_id TEXT UNIQUE NOT NULL,request_hash TEXT NOT NULL,response_json TEXT NOT NULL,
      expires_at REAL NOT NULL,used_receipt TEXT)''')
    db.execute('CREATE INDEX IF NOT EXISTS merchant_appraisal_owner ON merchant_item_appraisals(merchant_id,character_id,item_path)')


def snapshot(owned,item,merchant):
    fields={k:owned.get(k) for k in ('id','profile_id','item_path','quantity','equipped','equipment_slot','charges_current','charges_max','recharge','_trade_condition')}
    return digest([fields,item['revision'],merchant['buy_pct'],merchant.get('trade_policy_json')])


def eligible(owned,item,merchant):
    return bool(owned and not owned['equipped'] and item and item['catalog_entry_kind']!='reference' and item['trade_group']!='services' and allowed(merchant,item,'buy'))


def active(db,merchant,character_id,owned,item):
    if not eligible(owned,item,merchant):return None
    fingerprint=snapshot(owned,item,merchant)
    row=db.execute('''SELECT response_json FROM merchant_item_appraisals
      WHERE merchant_id=? AND character_id=? AND item_path=? AND snapshot_hash=?
      AND used_receipt IS NULL AND expires_at>? ORDER BY rowid DESC LIMIT 1''',
      (merchant['id'],character_id,owned['item_path'],fingerprint,time.time())).fetchone()
    return json.loads(row[0]) if row else None


def appraise(path,mid,access,*,character_id,item_path,unit_copper,request_id):
    if access.mode!='gm':raise PermissionError('Somente o Mestre avalia a oferta individual')
    if type(unit_copper) is not int or not 0<=unit_copper<=100000000 or not 8<=len(request_id)<=120:raise ValueError('Oferta individual inválida')
    from .map_commerce import initialize as init,_merchant,_ledger
    from .merchant import _connect
    from .item_registry import registry,resolve_item,owned_stock
    from contextlib import closing
    init(path);fingerprint=digest([mid,character_id,item_path,unit_copper])
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT * FROM merchant_item_appraisals WHERE request_id=?',(request_id,)).fetchone()
        if old:
            if old['request_hash']!=fingerprint:raise ValueError('Identificador já usado com outra avaliação')
            return json.loads(old['response_json'])
        merchant=_merchant(db,mid,access);index=registry(db);item=resolve_item(index,item_path)
        owned=next((o for o in owned_stock(db,character_id) if o['item_path']==item_path),None)
        if not eligible(owned,item,merchant):raise ValueError('Guarde um item físico aceito por este comprador antes de avaliar')
        if (owned.get('_trade_condition') or owned.get('charges_max') is not None) and owned['quantity']!=1:
            raise ValueError('Separe o objeto com cargas ou condição em uma unidade antes de avaliar')
        result={'id':'appraisal-'+uuid.uuid4().hex,'unit_copper':unit_copper,'expires_at':time.time()+86400,'snapshot_hash':snapshot(owned,item,merchant)}
        db.execute('INSERT INTO merchant_item_appraisals VALUES(?,?,?,?,?,?,?,?,?,?,NULL)',
            (result['id'],mid,character_id,item_path,unit_copper,result['snapshot_hash'],request_id,fingerprint,json.dumps(result),result['expires_at']))
        _ledger(db,access,'appraisal:'+result['id'],character_id,'Oferta individual de recompra definida pelo Mestre',{'merchant_id':mid,'item_path':item_path,**result},'gm')
        return result


def hold_instance(db,merchant_id,q,owned,now):
    """NPC acquired the object as-is. It never merges into retail stock as new."""
    stock_id='stock-'+uuid.uuid4().hex
    data={'status':'individual_review','item_path':owned['item_path'],'origin_inventory_id':owned['id'],
          'condition':owned.get('_trade_condition'),'charges_current':owned.get('charges_current'),
          'charges_max':owned.get('charges_max'),'recharge':owned.get('recharge'),'appraisal_id':q['individual_appraisal']['id']}
    db.execute('INSERT INTO merchant_stock(id,merchant_id,compendium_item_id,name,quantity,created_at,instance_json) VALUES(?,?,?,?,?,?,?)',
        (stock_id,merchant_id,q['catalog_id'],q['name'],q['quantity'],now,json.dumps(data)))
    db.execute('UPDATE merchant_item_appraisals SET used_receipt=? WHERE id=?',(q['id'],q['individual_appraisal']['id']))
    return stock_id,data
