"""Explicit approved economic maintenance; no startup or GET ever applies it.

Refund uses verified native receipts and a source-receipt uniqueness constraint.
Shop setup affects native offers only; it never edits sheets, combat or the Vault.
"""
import json,uuid
from contextlib import closing
from decimal import Decimal,ROUND_HALF_UP
from . import map_commerce as commerce
from .item_registry import registry,resolve_item,digest
from .merchant import _connect,_now,_character_state,_save_purse,purse_copper
from .session_ledger import append_session_ledger_event


def initialize(path):
    commerce.initialize(path)
    with closing(_connect(path)) as db,db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS merchant_maintenance_receipts(
          id TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,response_json TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS merchant_refund_sources(
          source_id TEXT PRIMARY KEY,correction_id TEXT NOT NULL);
        ''')


def _master(access):
    if access.mode!='gm':raise PermissionError('Somente o Mestre aplica manutenção econômica')


def refund_hp_overcharge(path,access,*,character_id,source_receipts,expected_refund_copper=1800):
    _master(access);initialize(path)
    if len(source_receipts)!=2 or len(set(source_receipts))!=2:raise ValueError('Exige os dois recibos distintos aprovados')
    identity='hp-price-refund:'+digest([character_id,sorted(source_receipts)])
    fingerprint=digest([character_id,sorted(source_receipts),500,expected_refund_copper])
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT * FROM merchant_maintenance_receipts WHERE id=?',(identity,)).fetchone()
        if old:
            if old['fingerprint']!=fingerprint:raise ValueError('Correção já aplicada com outros parâmetros')
            return json.loads(old['response_json'])
        paid=correct=0
        for source in source_receipts:
            if db.execute('SELECT 1 FROM merchant_refund_sources WHERE source_id=?',(source,)).fetchone():raise ValueError('Recibo já corrigido')
            row=db.execute("SELECT detail_json FROM session_ledger WHERE source_type='commerce' AND source_id=? AND character_id=? AND voided_at IS NULL",(source,character_id)).fetchone()
            if not row:raise ValueError('Compra original não encontrada')
            receipt=json.loads(row[0]);multiplier=(receipt.get('bargain') or {}).get('multiplier',1)
            if receipt.get('kind')!='buy' or receipt.get('quantity')!=1 or receipt.get('name') not in ['Poção (serviço)','Poção de HP'] or receipt.get('total_copper')!=1350 or Decimal(str(multiplier))!=Decimal('.9'):
                raise ValueError('Recibo difere da correção de duas poções aprovada')
            paid+=receipt['total_copper'];correct+=int((Decimal(500)*Decimal(str(multiplier))).quantize(Decimal('1'),rounding=ROUND_HALF_UP))
        refund=paid-correct
        if refund!=expected_refund_copper or refund!=1800:raise ValueError('Diferença não corresponde aos 18 PO aprovados')
        state=_character_state(db,character_id);before={k:int(state.get(k) or 0) for k in ['copper_coins','silver_coins','coins','platinum_coins']}
        after=_save_purse(db,character_id,purse_copper(state)+refund)
        response={'receipt_id':identity,'character_id':character_id,'kind':'refund','name':'Correção de duas poções de HP','quantity':2,'total_copper':refund,
            'purse_before':before,'purse_after':after,'balance_before_copper':purse_copper(before),'balance_after_copper':purse_copper(after),
            'source_receipts':sorted(source_receipts),'original_paid_copper':paid,'correct_paid_copper':correct,'audit_schema_version':1,
            'inventory_changes':[],'stock_before':None,'stock_after':None,'service_status':None}
        append_session_ledger_event(db,source_type='commerce_refund',source_id=identity,event_kind='state',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=character_id,
            title=f'{character_id} recebeu reembolso de 18 PO: correção do preço de duas poções',detail=response,visibility='table',created_at=_now())
        db.execute('INSERT INTO merchant_maintenance_receipts VALUES(?,?,?)',(identity,fingerprint,json.dumps(response)))
        db.executemany('INSERT INTO merchant_refund_sources VALUES(?,?)',[(source,identity) for source in source_receipts])
        return response


def setup_shops(path,access,*,thoradin_id,conclave_id,request_id='market-separation-v2',replenish_empty_arcane=0):
    _master(access);initialize(path)
    if type(replenish_empty_arcane) is not int or not 0<=replenish_empty_arcane<=20:raise ValueError('Reposição inválida')
    fingerprint=digest([thoradin_id,conclave_id,'equipment-supplies-healing','arcane',500,replenish_empty_arcane])
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        old=db.execute('SELECT * FROM merchant_maintenance_receipts WHERE id=?',(request_id,)).fetchone()
        if old:
            if old['fingerprint']!=fingerprint:raise ValueError('Configuração já aplicada a outros estabelecimentos')
            return json.loads(old['response_json'])
        shops={row['id']:dict(row) for row in db.execute('SELECT * FROM merchants WHERE id IN (?,?)',(thoradin_id,conclave_id))}
        if len(shops)!=2:raise ValueError('Escolha dois estabelecimentos existentes e distintos')
        before={'shops':list(shops.values()),'stock':[dict(r) for r in db.execute('SELECT * FROM merchant_stock WHERE merchant_id IN (?,?)',(thoradin_id,conclave_id))]}
        index=registry(db);moved=[];price_changes=[];replenished=[]
        for row in before['stock']:
            item=resolve_item(index,row['compendium_item_id'])
            if not item:continue
            destination=conclave_id if item['trade_group']=='arcane' else thoradin_id if item['trade_group'] in {'equipment','supplies','healing'} else row['merchant_id']
            if destination!=row['merchant_id']:
                db.execute('UPDATE merchant_stock SET merchant_id=? WHERE id=?',(destination,row['id']));moved.append({'stock_id':row['id'],'from':row['merchant_id'],'to':destination})
            if row['compendium_item_id']=='campanha-pocao-hp':
                db.execute('UPDATE merchant_stock SET price_override_po=5 WHERE id=?',(row['id'],));price_changes.append({'stock_id':row['id'],'before_po':row['price_override_po'],'after_po':5})
            if row['compendium_item_id']=='item-magico-po-do-desaparecimento' and row['quantity']==0 and replenish_empty_arcane:
                db.execute('UPDATE merchant_stock SET quantity=? WHERE id=?',(replenish_empty_arcane,row['id']))
                replenished.append({'stock_id':row['id'],'before':0,'after':replenish_empty_arcane})
        policies={thoradin_id:{'buy':['equipment','supplies','healing'],'sell':['equipment','supplies','healing']},conclave_id:{'buy':['arcane'],'sell':['arcane']}}
        for mid,policy in policies.items():db.execute('UPDATE merchants SET trade_policy_json=?,enabled=1 WHERE id=?',(json.dumps(policy),mid))
        # Configure existing supported services, with catalogue-backed lodging price.
        services=[]
        for mid,name in [(thoradin_id,'Avaliação de equipamentos'),(conclave_id,'Avaliação de itens arcanos')]:
            sid='service-market-'+digest([mid,'appraisal'])[:20]
            db.execute("INSERT OR IGNORE INTO merchant_services(id,merchant_id,name,kind,price_copper,amount,active) VALUES(?,?,?,'appraisal',0,1,1)",(sid,mid,name));services.append(sid)
        room=next((i for i in index['entries'].values() if i['id']=='hospedagem-quarto-coletivo-para-ate-5-pessoas-preco-individual-5-pc'),None)
        if room:
            sid='service-market-'+digest([conclave_id,'lodging'])[:20]
            db.execute("INSERT OR IGNORE INTO merchant_services(id,merchant_id,name,kind,price_copper,amount,active) VALUES(?,?,?,'lodging',?,1,1)",(sid,conclave_id,'Reserva de quarto coletivo',room['price_copper']));services.append(sid)
        after_stock=[dict(r) for r in db.execute('SELECT * FROM merchant_stock WHERE merchant_id IN (?,?)',(thoradin_id,conclave_id))]
        restocked={r['stock_id']:r['after'] for r in replenished}
        assert sorted((r['id'],restocked.get(r['id'],r['quantity'])) for r in before['stock'])==sorted((r['id'],r['quantity']) for r in after_stock)
        # Enable the existing responsible NPC's public trade card, preserving private text.
        for mid in shops:
            npc=shops[mid].get('npc_id')
            if npc:
                row=db.execute('SELECT id,name,visible_to_players,version FROM npc_definitions WHERE id=?',(npc,)).fetchone()
                if row and not row['visible_to_players']:
                    before.setdefault('npc_visibility',[]).append(dict(row))
                    db.execute('UPDATE npc_definitions SET visible_to_players=1,version=version+1,updated_at=? WHERE id=?',(_now(),npc))
                if row and mid==conclave_id and row['name']=='Mestre do Conclave':
                    before.setdefault('npc_names',[]).append(dict(row))
                    db.execute("UPDATE npc_definitions SET name='Klhauss',version=version+1,updated_at=? WHERE id=?",(_now(),npc))
                if row:
                    after=dict(db.execute('SELECT id,name,visible_to_players,version FROM npc_definitions WHERE id=?',(npc,)).fetchone())
                    if after!=dict(row):
                        from .npc_memory import _event
                        _event(db,event_key=f'npc:update:{npc}:{after["version"]}',npc_id=npc,actor_id='master',actor_role='gm',event_type='npc_updated',title='Responsável pelo estabelecimento atualizado',before=dict(row),after=after)
                if row and mid==conclave_id:
                    parent=db.execute("SELECT id,map_id FROM session_workspace_tokens WHERE id=? AND token_type='location'",(shops[mid].get('token_id'),)).fetchone()
                    portrait=db.execute('SELECT portrait_path FROM npc_definitions WHERE id=?',(npc,)).fetchone()[0]
                    if parent and portrait:
                        children=db.execute("SELECT * FROM session_workspace_tokens WHERE map_id=? AND token_type='monster' AND name IN ('Mestre do Conclave','Klhauss') AND image_path=?",(parent['map_id'],portrait)).fetchall()
                        for child in children:
                            sheet=json.loads(child['sheet_json'] or '{}')
                            if sheet.get('embedded_in_location')==parent['id']:continue
                            before.setdefault('embedded_tokens',[]).append(dict(child))
                            sheet['embedded_in_location']=parent['id']
                            db.execute("UPDATE session_workspace_tokens SET name='Klhauss',sheet_json=?,updated_at=? WHERE id=?",(json.dumps(sheet),_now(),child['id']))
        response={'moved':moved,'price_changes':price_changes,'services':services,'policies':policies,'stock_quantities_preserved':not bool(replenished),'replenished':replenished}
        append_session_ledger_event(db,source_type='merchant_maintenance',source_id=request_id,event_kind='state',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,
            title='Thoradin e Conclave: estoques, recompra e serviços organizados',detail={'before':before,'after_stock':after_stock,**response},visibility='gm',created_at=_now())
        db.execute('INSERT INTO merchant_maintenance_receipts VALUES(?,?,?)',(request_id,fingerprint,json.dumps(response)))
        return response
