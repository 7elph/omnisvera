"""One click, native loot stages: durable roll then atomic group delivery."""
import hashlib
import json
import re
from contextlib import closing

from . import loot
from .currency import COPPER_PER
from .player_inventory import currency_item_field


def initialize(path):
    loot.init_loot(path)
    with closing(loot._connect(path)) as db, db:
        db.executescript('''
        CREATE TABLE IF NOT EXISTS loot_collections(
            resolution_id TEXT PRIMARY KEY,token_id TEXT UNIQUE NOT NULL,
            group_json TEXT NOT NULL,receipt_json TEXT,draft_hash TEXT);
        CREATE TABLE IF NOT EXISTS loot_collection_commands(
            request_id TEXT PRIMARY KEY,fingerprint TEXT NOT NULL,resolution_id TEXT NOT NULL);
        CREATE TABLE IF NOT EXISTS loot_group_rotation(
            group_key TEXT PRIMARY KEY,item_cursor INTEGER NOT NULL,coin_cursor INTEGER NOT NULL);
        ''')
        db.execute('BEGIN IMMEDIATE')
        if 'draft_hash' not in {r[1] for r in db.execute('PRAGMA table_info(loot_collections)')}:
            db.execute('ALTER TABLE loot_collections ADD COLUMN draft_hash TEXT')


def _member(access,group):
    if access.mode!='gm' and access.profile_id not in {p['id'] for p in group}:
        raise PermissionError('Seu personagem não pertence ao grupo deste espólio')


def _source(db,token_id,access):
    token=db.execute("SELECT * FROM session_workspace_tokens WHERE id=? AND token_type='monster'",(token_id,)).fetchone()
    if not token:raise loot.LootNotFoundError('Cadáver não encontrado')
    sheet=json.loads(token['sheet_json'] or '{}')
    if token['current_hp'] is None or token['current_hp']>0 or sheet.get('summon') or sheet.get('disintegrated') or sheet.get('reanimated_by'):
        raise loot.LootConflictError('Este token não é um cadáver saqueável')
    if not any(e['scope']=='carried' for e in loot.parse_treasure_code(sheet.get('treasure') or '')):
        raise loot.LootConflictError('Este monstro não possui espólio carregado; covil é separado')
    if access.mode!='gm':
        from .monster_runtime import public_token
        if not public_token(db,token_id):raise PermissionError('Cadáver fora do mapa visível')
    return token


def _group(db,token):
    party=json.loads(token['sheet_json'] or '{}').get('loot_party')
    if party:
        return [dict(id=person['id'],name=person['name']) for person in party]
    # Reuse the PCs staged on this map. Offline PCs still belong to the group;
    # duplicate pins never grant a second share. No client-supplied recipients.
    rows=db.execute('''SELECT t.character_id,t.name FROM session_workspace_tokens t
        JOIN character_states c ON c.profile_id=t.character_id
        WHERE COALESCE(t.map_id,'default')=? AND t.token_type='character'
        AND t.visible_to_players=1 ORDER BY t.character_id,t.id''',(token['map_id'] or 'default',)).fetchall()
    members={}
    for row in rows:members.setdefault(row['character_id'],{'id':row['character_id'],'name':row['name']})
    if not members:raise loot.LootConflictError('Coloque os personagens do grupo neste mapa antes de saquear')
    return list(members.values())


def _allocate(rewards,group,item_cursor,coin_cursor):
    """Coins use minimum units, items use an audited persistent round robin."""
    normalized=[];coins=[];total=0
    for reward in rewards:
        field=currency_item_field(reward)
        if field:
            total+=reward['quantity']*COPPER_PER[field];coins.append(reward)
        else:normalized.append(reward)
    if coins:
        normalized.insert(0,{'id':coins[0]['id'],'kind':'pc','name':'Moedas de cobre','quantity':total,
            'gm_notes':json.dumps({'original_currency_rewards':coins},ensure_ascii=False),
            'conversion':[{'kind':r['kind'],'quantity':r['quantity']} for r in coins]})
    allocations=[];count=len(group)
    for reward in normalized:
        money=bool(currency_item_field(reward));cursor=coin_cursor if money else item_cursor
        each,remaining=divmod(reward['quantity'],count)
        for index,person in enumerate(group):
            quantity=each+int((index-cursor)%count<remaining)
            if quantity:allocations.append({'reward_id':reward['id'],'character_id':person['id'],'quantity':quantity})
        if money:coin_cursor=(cursor+remaining)%count
        else:item_cursor=(cursor+remaining)%count
    return normalized,allocations,item_cursor,coin_cursor


def collect_group_loot(path,access,*,request_id,token_id):
    if access.mode not in {'gm','player'}:raise PermissionError('Acesso inválido')
    if not re.fullmatch(r'[A-Za-z0-9._:-]{8,120}',str(request_id or '')):raise ValueError('request_id inválido')
    initialize(path)
    fingerprint=json.dumps([access.mode,access.profile_id or 'master',token_id])
    # Generation is a durable native block. A failed delivery must not reroll.
    with closing(loot._connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        command=db.execute('SELECT * FROM loot_collection_commands WHERE request_id=?',(request_id,)).fetchone()
        if command and command['fingerprint']!=fingerprint:raise loot.LootConflictError('Identificador já usado para outro saque')
        collection=db.execute('SELECT * FROM loot_collections WHERE token_id=?',(token_id,)).fetchone()
        if collection:
            group=json.loads(collection['group_json']);_member(access,group)
            if collection['receipt_json']:
                db.execute('INSERT OR IGNORE INTO loot_collection_commands VALUES(?,?,?)',(request_id,fingerprint,collection['resolution_id']))
                return json.loads(collection['receipt_json'])
        token=_source(db,token_id,access)
        if not collection:
            group=_group(db,token);_member(access,group)
            previous=db.execute("SELECT * FROM loot_resolutions WHERE source_key=?",('carried:'+token_id,)).fetchone()
            if previous and (previous['status']=='distributed' or (previous['status']=='draft' and access.mode!='gm')):
                raise loot.LootConflictError('Este espólio já foi distribuído ou está em revisão privada pelo Mestre')
            key='collect-roll:'+hashlib.sha256(token_id.encode()).hexdigest()[:40]
            resolved,_=loot.resolve_token_loot(path,request_id=key,token_id=token_id,scope='carried',roll_mode='digital',_connection=db)
            draft=db.execute('SELECT rewards_json FROM loot_resolutions WHERE resolution_id=?',(resolved['resolution_id'],)).fetchone()[0]
            db.execute('INSERT INTO loot_collections(resolution_id,token_id,group_json,receipt_json,draft_hash) VALUES(?,?,?,NULL,?)',
                (resolved['resolution_id'],token_id,json.dumps(group),hashlib.sha256(draft.encode()).hexdigest()))
            resolution_id=resolved['resolution_id']
        else:resolution_id=collection['resolution_id']
        db.execute('INSERT OR IGNORE INTO loot_collection_commands VALUES(?,?,?)',(request_id,fingerprint,resolution_id))
    with closing(loot._connect(path)) as db, db:
        db.execute('BEGIN IMMEDIATE')
        collection=db.execute('SELECT * FROM loot_collections WHERE resolution_id=?',(resolution_id,)).fetchone()
        if collection['receipt_json']:return json.loads(collection['receipt_json'])
        _source(db,token_id,access)
        group=json.loads(collection['group_json']);_member(access,group)
        # Do not silently reassign to a changed party or a removed character.
        if any(not db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(p['id'],)).fetchone() for p in group):
            raise loot.LootConflictError('Um destinatário não está mais disponível; o Mestre precisa revisar')
        row=db.execute('SELECT * FROM loot_resolutions WHERE resolution_id=?',(resolution_id,)).fetchone()
        if not row or row['status']=='distributed':raise loot.LootConflictError('Espólio alterado pelo Mestre; atualize o mapa')
        if row['status']=='draft' and access.mode!='gm' and hashlib.sha256(row['rewards_json'].encode()).hexdigest()!=collection['draft_hash']:
            raise loot.LootConflictError('O Mestre está revisando este espólio; aguarde sua revelação')
        group_key=hashlib.sha256(json.dumps(sorted(p['id'] for p in group)).encode()).hexdigest()
        rotation=db.execute('SELECT * FROM loot_group_rotation WHERE group_key=?',(group_key,)).fetchone()
        rewards,allocations,item_cursor,coin_cursor=_allocate(json.loads(row['rewards_json']),group,
            rotation['item_cursor'] if rotation else 0,rotation['coin_cursor'] if rotation else 0)
        db.execute('UPDATE loot_resolutions SET rewards_json=? WHERE resolution_id=?',(json.dumps(rewards,ensure_ascii=False),resolution_id))
        loot.reveal_loot(path,resolution_id,_connection=db,_actor=access)
        loot.distribute_loot(path,resolution_id=resolution_id,request_id='collect-distribute:'+hashlib.sha256(token_id.encode()).hexdigest()[:40],
            allocations=allocations,_connection=db,_actor=access)
        by_id={r['id']:r for r in rewards}
        receipt={'resolution_id':resolution_id,'source_name':row['source_name'],'policy':'group-round-robin-v1','shares':[
            {'character_id':p['id'],'name':p['name'],'rewards':[{'name':by_id[a['reward_id']]['name'],'kind':by_id[a['reward_id']]['kind'],'quantity':a['quantity']}
                for a in allocations if a['character_id']==p['id']]} for p in group]}
        db.execute('INSERT INTO loot_group_rotation VALUES(?,?,?) ON CONFLICT(group_key) DO UPDATE SET item_cursor=excluded.item_cursor,coin_cursor=excluded.coin_cursor',
            (group_key,item_cursor,coin_cursor))
        sheet=json.loads(db.execute('SELECT sheet_json FROM session_workspace_tokens WHERE id=?',(token_id,)).fetchone()[0]);sheet['loot_collected']=True
        db.execute('UPDATE session_workspace_tokens SET sheet_json=?,updated_at=? WHERE id=?',(json.dumps(sheet),loot._now(),token_id))
        db.execute('UPDATE loot_collections SET receipt_json=? WHERE resolution_id=?',(json.dumps(receipt,ensure_ascii=False),resolution_id))
        return receipt
