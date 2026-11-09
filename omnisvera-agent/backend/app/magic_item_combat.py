"""Confirmed native attack reactions; never recursively triggered by HP writes."""
from .magic_equipment import identity
from .magic_item_rulebook import rules_for

RAPINA='item-magico-armadura-leve-da-rapina'
RAPINA_RULES=rules_for(RAPINA)['parameters']


def reflect_rapina(db,record,damage_received,now):
    if damage_received<2 or record.get('result')!='hit':return None
    if not db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='player_inventory'").fetchone():return None
    kind,owner=record['target_type'],record['target_id']
    if kind=='token':
        row=db.execute('SELECT character_id FROM session_workspace_tokens WHERE id=?',(owner,)).fetchone()
        if not row or not row[0]:return None
        kind,owner='character',row[0]
    if kind!='character':return None
    armor=next((row for row in db.execute('SELECT item_path FROM player_inventory WHERE profile_id=? '
        'AND equipped=1 AND quantity>0 AND equipment_slot=?',(owner,'Armadura'))
        if identity({'item_path':row[0]})==RAPINA),None)
    if not armor:return None
    attacker=record['actor_character_id']
    actor_kind='character' if db.execute('SELECT 1 FROM character_states WHERE profile_id=?',(attacker,)).fetchone() else 'token'
    if actor_kind=='character' and attacker==owner:return None
    damage=int(damage_received)//2
    from .combat_effects import change_hp
    profile=record['breakdown'].get('damage_profile') or {}
    hp=change_hp(db,actor_kind,attacker,-damage,now,damage_context={
        'kind':'magic_item_reflection','magical':True,'damage_type':profile.get('damage_type')})
    if hp['hp_after']==0:
        from .vezemir_skills import kill_reward
        kill_reward(db,owner,actor_kind,attacker,now)
    return {'item_path':armor[0],'damage_received':int(damage_received),'damage':damage,
            'target_type':actor_kind,'target_id':attacker,'hp':hp,'rounding':'floor'}
