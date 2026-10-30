"""Explicit approved maintenance, never startup or GET; preserves live progress."""
import json
import sqlite3
from contextlib import closing


def dorn_abilities():
    from .dorn_spell_pack import SPELLS,CIRCLES
    descriptions={
        'reflexos':'1d4+1 reflexos por 1d6 turnos de exploração+nível (turno: 10 min). Cada acerto individual tem 50% de atingir e destruir um reflexo. Dano de área não é desviado.',
        'teia':'Área de chão 3×3 m e altura 6 m; canto inicial na célula do pin selecionado. Alcance 3 m+nível. Duração 1 h+10 min/nível. Dentro: movimento a 1/3, CA −2, JP de DES −2. Grid valida automaticamente os ocupantes.',
        'forca-arcana':'Toque adjacente. Aumenta FOR em 1 por cada 5 da FOR original (sem itens/magias). Dura 1d6 turnos de exploração+nível; não acumula consigo. Dorn é receptor excepcional aprovado.',
        'dissipar-magia':'Alcance 10 m+3 m/nível. 1d20+nível contra 5+círculo+nível do conjurador de origem. Dissipa magia arcana ativa com origem cadastrada. Não destrói itens mágicos.'}
    return [{'id':key,'name':name,'kind':'spell','group':'Magias','circle':CIRCLES[key],'active':True,'blocked':False,'mechanics_status':'structured','description':descriptions[key],
             'uses':{'resource_key':'dorn_'+key.replace('-','_'),'label':name+' · preparada','maximum':1,'recharge':'inn_rest'},'source':'Old Dragon 1, livro básico: pp.103/107/122/126; preparação independente aprovada'} for key,name in SPELLS.items()]


def apply_approved_spell_pack(path):
    from .character_play import _now,_write_event
    from .level_advancement import NECROMANCER_ABILITIES_5
    now=_now();changed=[]
    with closing(sqlite3.connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE')
        for actor in ['dorn7','morthak']:
            row=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(actor,)).fetchone()
            state_row=db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(actor,)).fetchone()
            if not row or not state_row:raise ValueError('Ficha persistida ausente: '+actor)
            overrides=json.loads(row[0]);state=json.loads(state_row[0]);before={'overrides':json.loads(row[0]),'state':json.loads(state_row[0])}
            if actor=='dorn7':
                if not str(overrides.get('approved_build') or '').startswith('dorn-mage'):raise ValueError('Dorn sem ficha aprovada')
                additions=dorn_abilities();field='approved_session_abilities';removed={'levitacao','escuridao'}
            else:
                if overrides.get('specialization')!='necromante' or int(overrides.get('level') or 0)<5:raise ValueError('Morthak precisa ser Necromante nível 5')
                additions=[a for a in NECROMANCER_ABILITIES_5 if a['id'] in {'clonagem','magia-da-morte'}];field='level_abilities';removed=set()
            wanted={a['id'] for a in additions}
            overrides[field]=[a for a in overrides.get(field,[]) if a['id'] not in wanted|removed]+additions
            existing={r['key'] for r in state.get('resources',[])}
            for ability in additions:
                uses=ability['uses'];key=uses['resource_key']
                if key not in existing:state.setdefault('resources',[]).append({'key':key,'label':uses['label'],'maximum':1,'current':1,'recharge':'inn_rest'})
            # No recharge, level/HP/equipment mutation or deletion of old audit resources.
            if before=={'overrides':overrides,'state':state}:continue
            db.execute('UPDATE character_definition_overrides SET data_json=?,updated_at=? WHERE profile_id=?',(json.dumps(overrides,ensure_ascii=False),now,actor))
            db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?',(json.dumps(state,ensure_ascii=False),now,actor))
            _write_event(db,character_id=actor,actor_id='master',actor_role='gm',event_type='approved_spell_pack',field=field,before=before,after={'overrides':overrides,'state':state},reason='Pacote de magias aprovado em 13/10; PV, nível e recursos gastos preservados',session_id=None)
            changed.append(actor)
    return changed
