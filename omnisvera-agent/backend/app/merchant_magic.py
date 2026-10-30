"""Paid services over reviewed catalogue contracts and native HP/condition helpers."""
from .dice_rolls import roll_formula


def specification(spell_id):
    from .spell_catalog import get_catalog_spell
    from .catalog_spell_contracts import reviewed_contract
    from .item_catalog import get_catalog_item
    spell=get_catalog_spell(spell_id)
    contract=reviewed_contract(spell,strict=True) if spell else None
    if not contract:raise ValueError('Serviço sem efeito revisado: nenhuma cobrança ou aplicação automática')
    tariff=get_catalog_item('servico-magico-lancar-magia')
    circle=spell['circle']
    return {'spell_id':spell_id,'name':spell['name'].removesuffix(' R'),'circle':circle,
            'default_price_copper':round(tariff['preco_po']*100)*circle,'contract':contract,
            'price_source':'Livro: 30 PO × círculo; preço do estabelecimento editável pelo Mestre'}


def catalogue():
    from .catalog_spell_contracts import contracts
    return [specification(identity) for identity in contracts()]


def require_target(db,character_id,spec):
    import json
    clock=db.execute("SELECT 1 FROM sqlite_master WHERE name='combat_effect_clock'").fetchone()
    if clock:
        row=db.execute('SELECT encounter_json FROM combat_effect_clock WHERE id=1').fetchone()
        if row and json.loads(row[0] or '{}').get('active'):raise ValueError('Atendimento mágico do mercado indisponível durante combate')
    from .dorn_spells import target
    victim=target(db,'character',character_id)
    if spec['contract']['family']=='healing_hp':
        from .catalog_spell_contracts import require_healing_target
        require_healing_target(db,victim)
        state=json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(character_id,)).fetchone()[0])
        if int(state.get('current_hp') or 0)>=int(state.get('maximum_hp') or 0):raise ValueError('Personagem já está com PV completos')
    elif not clock:raise ValueError('Motor de condições não inicializado')
    else:
        from .damage_profiles import normalized
        state=json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?',(character_id,)).fetchone()[0])
        labels=any(isinstance(v,str) and normalized(v) in {'paralisia','paralyzed'} for v in state.get('conditions') or [])
        effects=[json.loads(r[0]) for r in db.execute("SELECT data_json FROM combat_effects WHERE active=1 AND target_type='character' AND target_id=?",(character_id,))]
        removable=any(e.get('monster_condition')=='paralyzed' and not any(e.get(k) for k in ('environmental','area','area_cells','area_root_id')) for e in effects)
        if not labels and not removable:raise ValueError('Não há paralisia individual removível')
    return victim


def apply(db,character_id,spell_id,now):
    spec=specification(spell_id);victim=require_target(db,character_id,spec)
    contract=spec['contract']
    if contract['family']=='healing_hp':
        from .combat_effects import change_hp
        roll=roll_formula(contract['formula']);changed=change_hp(db,'character',character_id,max(0,int(roll['total'])),now)
        return {'spell_id':spell_id,'family':contract['family'],'roll':roll,'healing_applied':changed['hp_after']-changed['hp_before'],**changed}
    from .catalog_spell_contracts import remove_reviewed_condition
    result=remove_reviewed_condition(db,victim,contract,now)
    if not result['removed_effects'] and not result['removed_conditions']:raise ValueError('Não há paralisia individual removível; nada foi cobrado')
    return {'spell_id':spell_id,'family':contract['family'],**result}


def configure_defaults(path,mid,access):
    if access.mode!='gm':raise PermissionError('Somente o Mestre configura atendimento mágico')
    from .map_commerce import initialize,_merchant,_ledger
    from .merchant import _connect
    from .item_registry import digest
    from contextlib import closing
    initialize(path);result=[]
    with closing(_connect(path)) as db,db:
        db.execute('BEGIN IMMEDIATE');_merchant(db,mid,access)
        for spec in catalogue():
            sid='service-magic-'+digest([mid,spec['spell_id']])[:20]
            db.execute("INSERT OR IGNORE INTO merchant_services(id,merchant_id,name,kind,price_copper,amount,active,spell_id) VALUES(?,?,?,'spell',?,1,1,?)",(sid,mid,spec['name'],spec['default_price_copper'],spec['spell_id']))
            result.append(sid)
        _ledger(db,access,'magic-services:'+mid,None,'Atendimento mágico revisado configurado',{'merchant_id':mid,'service_ids':result},'gm')
    return result
