"""Typed creature capability, separate from carried magic items or guessed names."""
import unicodedata


def validate_sheet(sheet):
    if 'magic_capability' in sheet and sheet['magic_capability'] is not None and type(sheet['magic_capability']) is not bool:
        raise ValueError('Capacidade mágica deve ser Sim, Não ou Automático')


def resolve(sheet, *, monster=None):
    explicit=sheet.get('magic_capability')
    if type(explicit) is bool:return {'value':explicit,'source':'registered'}
    if (sheet.get('spell_repertoire') or sheet.get('spellcasting') or
            type(sheet.get('spellcaster_level')) is int and sheet['spellcaster_level']>0 or
            str(sheet.get('approved_build') or '').startswith('dorn-mage')):
        return {'value':True,'source':'caster_profile'}
    cls=sheet.get('character_class') or {}
    if not isinstance(cls,dict):cls={}
    text=str(sheet.get('class_name') or cls.get('class_name') or cls.get('name') or '')
    name=unicodedata.normalize('NFKD',text).encode('ascii','ignore').decode().casefold()
    if any(word in name for word in ('mago','clerigo','druida','hemomante','necromante')):
        return {'value':True,'source':'character_class'}
    if monster:
        from .monster_actions import build_action_map
        abilities=monster.get('abilities') or []
        actions=build_action_map(monster.get('name',''),monster.get('attacks') or [],
            [(a.get('name') or '',a.get('description') or '') for a in abilities],monster_id=monster.get('id'))
        if actions['spellcasting']:return {'value':True,'source':'catalog_spellcasting'}
        # An empty SRD ability list is explicit absence, unlike a custom sheet
        # whose source has not been catalogued. Ambiguous abilities stay unknown.
        if not abilities:return {'value':False,'source':'catalog_no_abilities'}
    return {'value':None,'source':'not_registered'}
