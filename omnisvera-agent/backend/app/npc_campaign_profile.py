"""Explicit campaign build, not a conversion rule from guild rank to level."""
from copy import deepcopy
from contextlib import closing
import json
from .merchant import _connect,_now

PROFILE={
 'id':'klhauss-warrior-mage-v1','label':'Configuração da campanha · editável','rank':'S',
 'level':10,'role':'Guerreiro com magia · Mestre do Conclave','armor_class':20,
 'initiative':1,'saving_throw':8,'movement':9,'spellcaster_level':6,
 'attributes':{'strength':18,'dexterity':14,'constitution':16,'intelligence':16,'wisdom':14,'charisma':16},
 'attacks':[
   {'name':'Espada longa +2','damage':'1d8+5','bonus':15,'slot':'melee','damage_type':'slashing','magical':True,'notes':'BA 10 + FOR 3 + melhoria 2; configuração da campanha'},
   {'name':'Arco longo +1','damage':'1d8+1','bonus':12,'slot':'ranged','range_m':30,'damage_type':'piercing','magical':True,'notes':'BA 10 + DES 1 + melhoria 1; alcance da campanha editável'}],
 'abilities':['Magias: Conjura como um Mago de 6º nível. Repertório da campanha: Dardos Místicos e Toque Chocante. Três usos diários de cada; recupera no descanso geral do Mestre.'],
 'spell_repertoire':[{'spell_id':'arcana-dardos-misticos','daily_uses':3},{'spell_id':'arcana-toque-chocante','daily_uses':3}],
 'equipment':['Espada longa +2','Arco longo +1','Armadura de placas','Escudo','Foco arcano'],
}


def proposal():return {'maximum_hp':65,'sheet':deepcopy(PROFILE),'note':'Rank S identifica a campanha; não implica nível universal. PV/CA/BA/repertório são escolhas editáveis, não canon do Vault.'}


def apply(path,npc_id,access,*,request_id):
    if access.mode!='gm':raise PermissionError('Somente o Mestre configura a ficha do NPC')
    if not 8<=len(request_id)<=120:raise ValueError('Identificador inválido')
    from .map_commerce import initialize
    initialize(path)
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        db.execute('CREATE TABLE IF NOT EXISTS npc_campaign_commands(request_id TEXT PRIMARY KEY,npc_id INTEGER NOT NULL,response_json TEXT NOT NULL)')
        old=db.execute('SELECT npc_id,response_json FROM npc_campaign_commands WHERE request_id=?',(request_id,)).fetchone()
        if old:
            if old['npc_id']!=npc_id:raise ValueError('Identificador usado com outro NPC')
            return json.loads(old['response_json'])
        npc=db.execute('SELECT * FROM npc_definitions WHERE id=?',(npc_id,)).fetchone()
        if not npc or npc['name']!='Klhauss':raise ValueError('Este perfil é exclusivo de Klhauss')
        clock=db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone()
        if clock:
            state=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
            if state and json.loads(state[0] or '{}').get('active'):raise ValueError('Finalize o combate antes de configurar Klhauss')
        shop=db.execute('SELECT token_id FROM merchants WHERE npc_id=?',(npc_id,)).fetchone()
        candidates=[]
        if shop:
            for token in db.execute("SELECT * FROM session_workspace_tokens WHERE token_type='monster' AND name='Klhauss'"):
                if json.loads(token['sheet_json'] or '{}').get('embedded_in_location')==shop[0]:candidates.append(token)
        if len(candidates)!=1:raise ValueError('Vínculo único de Klhauss ao Conclave não encontrado')
        token=candidates[0];sheet=json.loads(token['sheet_json'] or '{}')
        if sheet.get('campaign_profile',{}).get('id')==PROFILE['id']:
            return {'token_id':token['id'],'npc_id':npc_id,'status':'already_configured'}
        if sheet.get('attacks') or sheet.get('level',1)!=1 or token['maximum_hp']!=10:
            raise ValueError('Klhauss já tem ficha editada; configuração automática preservou essa ficha')
        build=proposal();before=dict(token)
        template=deepcopy(PROFILE);template.pop('id');template.pop('label')
        sheet.update(template);sheet['campaign_profile']={k:PROFILE[k] for k in ('id','label')}
        now=_now()
        db.execute('UPDATE session_workspace_tokens SET sheet_json=?,maximum_hp=?,current_hp=?,updated_at=? WHERE id=?',
            (json.dumps(sheet,ensure_ascii=False),build['maximum_hp'],build['maximum_hp'],now,token['id']))
        db.execute("UPDATE npc_definitions SET class_or_role='Guerreiro com magia · Mestre do Conclave · Rank S',version=version+1,updated_at=? WHERE id=?",(now,npc_id))
        from .npc_memory import _event
        result={'npc_id':npc_id,'token_id':token['id'],'status':'configured','maximum_hp':build['maximum_hp'],'profile':build['sheet']}
        _event(db,event_key='npc:campaign-profile:'+request_id,npc_id=npc_id,actor_id='master',actor_role='gm',event_type='npc_updated',title='Ficha Rank S de Klhauss configurada',before=before,after=result)
        from .session_ledger import append_session_ledger_event
        append_session_ledger_event(db,source_type='npc_campaign_profile',source_id=request_id,event_kind='state',actor_id='master',actor_name='Mestre',actor_role='gm',character_id=None,title='Klhauss: guerreiro com magia, Rank S',detail={'before':before,**result},visibility='gm',created_at=now)
        db.execute('INSERT INTO npc_campaign_commands VALUES(?,?,?)',(request_id,npc_id,json.dumps(result)))
        return result
