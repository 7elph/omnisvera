"""Small reviewed effect families over the existing catalogue, not an interpreter."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import re

from .damage_profiles import normalized


def source_fingerprint(spell):
    fields = {key: spell.get(key) for key in ('id', 'name', 'description', 'alcance', 'duracao', 'jogada_protecao')}
    return hashlib.sha256(json.dumps(fields, ensure_ascii=False, sort_keys=True).encode()).hexdigest()


@lru_cache(maxsize=1)
def contracts():
    data = json.loads((Path(__file__).parent / 'data/catalog_spell_contracts.json').read_text(encoding='utf8'))
    if data.get('schema_version') != 1:
        raise ValueError('Versão inválida de contratos do catálogo')
    for value in data['spells'].values():
        healing = (value.get('family') == 'healing_hp' and value.get('mode') == 'normal'
                   and value.get('formula') in {'1d8', '2d8+1', '3d8+3'})
        condition = (value.get('family') == 'condition_cure' and value.get('mode') == 'single_target'
                     and value.get('condition') == 'paralyzed' and value.get('range_m_per_level') == 10)
        if not (healing or condition):
            raise ValueError('Contrato revisado do catálogo inválido')
    return data['spells']


def reviewed_contract(spell, *, strict=False):
    contract = contracts().get(spell.get('id'))
    if not contract:
        return None
    if source_fingerprint(spell) != contract['source_sha256']:
        if strict:
            raise ValueError('A fonte desta magia mudou; revise o contrato antes de executar.')
        return None
    return dict(contract)


def reviewed_heal(spell, *, strict=False):
    contract = reviewed_contract(spell, strict=strict)
    return contract if contract and contract['family'] == 'healing_hp' else None


def reviewed_condition_cure(spell, *, strict=False):
    contract = reviewed_contract(spell, strict=strict)
    return contract if contract and contract['family'] == 'condition_cure' else None


def catalogue_automation(spell):
    contract = reviewed_contract(spell)
    if contract and contract['family'] == 'healing_hp':
        return {**{key: contract[key] for key in ('family', 'mode', 'formula')}, 'status': 'effect_automated',
                'note': 'Cura de PV por toque automatizada (versão normal). Custos/repertório assistidos; reverso não automatizado.'}
    if contract and contract['family'] == 'condition_cure':
        return {'family': 'condition_cure', 'mode': contract['mode'], 'status': 'effect_automated',
                'condition': contract['condition'], 'target_limit': 1,
                'note': 'Remove paralisia individual identificada, em um alvo, com alcance de 10 m/nível. Custos, barreiras, lentidão e imobilizações de área continuam assistidos; não executa a versão em grupo.'}
    if spell.get('id') in contracts():
        return {'family':contracts()[spell['id']]['family'],'status':'blocked',
                'note':'A fonte da magia mudou; contrato aguardando revisão.'}
    if not str(spell.get('description') or '').strip():
        return {'family': 'unmapped', 'status': 'blocked', 'note': 'Fonte sem descrição suficiente para executar.'}
    from .spell_engine import derive_spell_mechanic
    mechanic = derive_spell_mechanic(spell)
    if mechanic['damage']:
        return {'family': 'damage_save', 'status': 'partial',
                'note': 'JP e dano integrados. Custos, área e condições restantes são assistidos.'}
    return {'family': 'unmapped', 'status': 'assisted',
            'note': 'Efeito assistido; descrição não é um executor completo.'}


def remove_reviewed_condition(db, victim, contract, now):
    """Remove native individual paralysis; never erase an area root or other condition."""
    if contract['family'] != 'condition_cure' or contract['condition'] != 'paralyzed':
        raise ValueError('Família de condição sem executor revisado.')
    kind, identity = victim['type'], victim['id']
    removed = []
    for row in db.execute('SELECT id,data_json FROM combat_effects WHERE active=1 AND target_type=? AND target_id=?',
                          (kind, identity)).fetchall():
        effect = json.loads(row[1])
        if effect.get('monster_condition') != 'paralyzed' or any(effect.get(key) for key in ('environmental','area','area_cells','area_root_id')):
            continue
        db.execute('UPDATE combat_effects SET active=0 WHERE id=?', (row[0],))
        removed.append({'id': row[0], 'label': str(effect.get('label') or 'Paralisia')})
    labels = []
    if kind == 'character':
        raw = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (identity,)).fetchone()
        state = json.loads(raw[0])
        conditions = state.get('conditions') or []
        if isinstance(conditions, list):
            labels = [condition for condition in conditions if isinstance(condition, str) and normalized(condition) in {'paralisia','paralyzed'}]
            if labels:
                state['conditions'] = [condition for condition in conditions if condition not in labels]
                db.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?',
                    (json.dumps(state,ensure_ascii=False),now,identity))
    if removed or labels:
        db.execute('UPDATE combat_effect_clock SET version=version+1 WHERE id=1')
    return {'condition_cure': contract['condition'], 'removed_effects': removed,
            'removed_conditions': labels, 'damage_dealt': 0}


def require_healing_target(db, victim):
    """Only classified corporeal living recipients. Unknown nature fails closed."""
    kind, identity = victim['type'], victim['id']
    if kind == 'character':
        from .construct_rules import validate_healing
        from .character_play import _step_fields
        validate_healing(db, identity, 'conventional_magical_healing')
        row = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (identity,)).fetchone()
        data = json.loads(row[0] or '{}') if row else {}
        sheetrow = db.execute('SELECT data_json FROM character_sheets WHERE profile_id=?', (identity,)).fetchone()
        sheet = json.loads(sheetrow[0] or '{}') if sheetrow else {}
        root_race=sheet.get('race')
        root_race=root_race.get('race') if isinstance(root_race,dict) else root_race if isinstance(root_race,str) else None
        category = data.get('race') or _step_fields(sheet, 'race').get('race') or root_race or ''
    else:
        from .monster_runtime import token_monster
        monster, data = token_monster(db, identity)
        category = data.get('creature_type') or data.get('category') or (monster or {}).get('category') or ''
        if monster:
            from .monster_catalog import get_catalog_monster
            original = get_catalog_monster(monster['id']) or monster
            nature = ' '.join([str(original.get('name') or ''), str(original.get('description') or ''), *(
                str(a.get('description') or '') for a in monster.get('abilities') or [] if isinstance(a, dict))])
            if re.search(r'\b(?:incorpore[oa]|extraplanar|morto-vivo|constructo|elemental)\b|'
                         r'\b(?:outros? planos?|plano (?:inferior|superior|abissal|externo|infernal))\b', normalized(nature)):
                raise ValueError('Natureza da criatura exige resolução assistida da cura.')
    excluded = ('is_undead', 'undead_traits', 'construct_traits', 'incorporeal', 'is_incorporeal', 'extraplanar', 'is_extraplanar')
    summon = data.get('summon') or {}
    if not isinstance(summon, dict):
        raise ValueError('Natureza da invocação não está classificada para cura.')
    if (any(data.get(key) for key in excluded) or data.get('is_alive') is False
            or data.get('corporeal') is False or data.get('reanimated_by')
            or summon.get('technique') in {'levantar-esqueleto', 'animar-mortos'}):
        raise ValueError('Cura convencional exige alvo vivo, corpóreo e não extraplanar.')
    text = normalized(category)
    if re.search(r'vampir|morto.?vivo|construct|incorp|extraplan|elemental|demon|diabo|celestial|espirito', text):
        raise ValueError('Este tipo de criatura não recebe cura convencional.')
    known = r'^(?:humano|meio-elfo|elfo|anao|halfling|gnomo|animal|besta|dragao|gigante|gosma|inseto|planta|variacao de)'
    if not re.search(known, text):
        raise ValueError('Tipo de criatura indefinido para cura; resolução assistida necessária.')
