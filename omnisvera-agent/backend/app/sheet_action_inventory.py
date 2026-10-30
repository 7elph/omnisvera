"""Pure inventory of the current sheet surface plus preserved legacy actions.

This is audit metadata, never authorization, rule execution or a sheet mutation.
Hemomancy entries require the already-authorized effective private DTO package.
"""
from copy import deepcopy
import unicodedata


def audit_abilities(definition):
    abilities=deepcopy(definition.get('session_abilities') or [])
    for ability in abilities:
        ability['visible_on_sheet']=not bool(ability.get('hidden'))
        if definition.get('id')=='dorn7' and ability.get('id') in {'levitacao','escuridao','dorn_diagnose'}:
            ability['visible_on_sheet']=False
    from .hemomancy import ACTION_IDS, REVISION
    package=definition.get('hemomancy') or {}
    if definition.get('id')!='raziel' or package.get('revision')!=REVISION:
        return abilities
    retained={'caixao','mordida','forma-da-noite','regeneracao-vampirica','marca-rubra'}
    for ability in abilities:
        group=''.join(c for c in unicodedata.normalize('NFD',str(ability.get('group') or 'Habilidades').casefold()) if not unicodedata.combining(c)).strip()
        if group in {'habilidades','poderes vampiricos'} and ability.get('id') not in retained:
            ability['visible_on_sheet']=False
        if ability.get('id') in {'marca-rubra','regeneracao-vampirica'}:
            ability['uses']={'resource_key':'reserva_de_sangue','cost':1}
    held=next((effect.get('weapon') for effect in definition.get('active_effects') or []
               if effect.get('hemomancy_kind')=='weapon' and effect.get('target_id')=='raziel'),None)
    generated=[]
    for weapon in package.get('weapons') or []:
        key=weapon.get('weapon');identity='hemomancia-'+str(key)
        if identity not in ACTION_IDS:
            continue
        shield=key=='escudo'
        for skill in ((False,) if shield else (False,True)):
            action_id=identity+('-habilidade' if skill else '')
            invocation=weapon['invocation_cost'] if shield or key!=held else 0
            from .hemomancy import blood_cost
            cost=blood_cost(weapon,skill,key==held)
            generated.append(dict(id=action_id,name=(weapon['skill']['name'] if skill or shield else weapon['name']),
                description=(weapon['skill'].get('description') if skill or shield else
                             f"{weapon['name']}: {weapon.get('damage') or 'sem dano'}; alcance {weapon.get('range_m') or 'adjacente'}."),
                kind='ability',group='Habilidades' if skill or shield else 'Hemomancia',active=True,
                requires_target=not shield,mechanics_status='structured',source='Hemomancia',
                visible_on_sheet=True,action_revision=package['revision'],hemomancy_mode='skill' if skill else 'basic',
                damage=weapon.get('damage'),range_m=weapon.get('range_m'),
                uses={'resource_key':'reserva_de_sangue','cost':cost},
                invocation_cost=weapon['invocation_cost'],skill_cost=weapon['skill']['cost'] if skill else 0))
        generated.append(dict(id='hemomancia-passiva-'+str(key),name=weapon['passive']['name'],
            description=weapon['passive'].get('description',''),
            kind='passive',group='Poderes vampíricos',active=False,requires_target=False,
            visible_on_sheet=True,source='Hemomancia',action_revision=package['revision']))
    # Preserve raw/legacy entries for audit, but do not duplicate a new card id.
    generated_ids={item['id'] for item in generated}
    return [a for a in abilities if a.get('id') not in generated_ids]+generated
