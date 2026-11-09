"""GM-declared campaign phase; never derives RPG daylight from computer time."""
BUCKLE='item-magico-fivela-das-irmas'


def phase(db):
    columns={row[1] for row in db.execute('PRAGMA table_info(combat_effect_clock)')}
    if 'world_phase' not in columns:return 'unset'
    row=db.execute('SELECT world_phase FROM combat_effect_clock WHERE id=1').fetchone()
    return row[0] if row else 'unset'


def command(db,payload):
    if set(payload)!={'phase'} or not isinstance(payload['phase'],str) or payload['phase'] not in {'day','night'}:
        raise ValueError('Escolha dia ou noite para a campanha')
    db.execute('UPDATE combat_effect_clock SET world_phase=? WHERE id=1',(payload['phase'],))
    return {'world_phase':payload['phase'],'label':'Dia' if payload['phase']=='day' else 'Noite'}


def reduce_damage(db,kind,identity,amount,damage_type):
    if not db or damage_type not in {'fire','lightning'} or amount<=0:return amount
    owner=identity if kind=='character' else None
    if kind=='token':
        row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(identity,)).fetchone()
        owner=row[0] if row else None
    from .magic_passives import equipped
    if not equipped(db,owner,BUCKLE):return amount
    current=phase(db)
    if current not in {'day','night'}:raise ValueError('Defina dia/noite da campanha para calcular a Fivela das Irmãs')
    matches=(current=='day' and damage_type=='fire') or (current=='night' and damage_type=='lightning')
    return max(0,amount-5) if matches else amount
