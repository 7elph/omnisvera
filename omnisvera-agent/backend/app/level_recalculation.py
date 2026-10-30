"""Manual level corrections share deterministic rules and the existing dice inbox.

No HP dice are rolled by an edit. The dice request completion transaction applies
the recorded result once. Unknown class/level contracts fail closed.
"""
from copy import deepcopy
import json
import uuid
from datetime import datetime, timedelta, timezone


def contract(definition, overrides):
    from .level_advancement import TABLES, RULES, NECROMANCER_ABILITIES_5, NECROMANCER_RESOURCES_5
    # These are the already recorded campaign class tables, not new RAW rules.
    by_class = {r['class']: {'levels': TABLES[p], 'die': r['die'], 'source': r['source']}
                for p, r in RULES.items()}
    supplied = overrides.get('progression_contract')
    if supplied:
        return supplied
    rule = by_class.get(definition.get('class_name'))
    if not rule:
        raise ValueError('Classe sem contrato de progressão aprovado; nenhuma alteração aplicada')
    return rule


def morthak_level_grants(target):
    from .level_advancement import NECROMANCER_ABILITIES_5, NECROMANCER_RESOURCES_5
    if target >= 5:
        return {'abilities': list(NECROMANCER_ABILITIES_5),
                'resource_maxima': dict(NECROMANCER_RESOURCES_5)}
    return {}


def recalculate(db, character_id, definition, before, overrides, target, now):
    from .character_play import _save_state, attribute_modifier
    rule = contract(definition, overrides)
    table = {int(k): v for k, v in rule['levels'].items()}
    source = int(definition.get('level') or 1)
    if int(before.get('level', source)) != source:
        raise ValueError('A ficha mudou durante o ajuste; atualize antes de tentar novamente')
    if source not in table or target not in table:
        raise ValueError('Nível fora da tabela aprovada desta classe; falta regra, não uma rolagem')
    old_ba, old_jp = table[source][:2]
    new_ba, new_jp = table[target][:2]
    progression = definition.get('progression') or {}
    sheet_level = int(progression.get('sheet_level') or source)
    if sheet_level not in table:
        raise ValueError('Nível da ficha-base fora do contrato aprovado')
    if 'advancement_base_attack' not in before:
        old_ba = table[sheet_level][0]
    if 'advancement_saving_throw' not in before:
        old_jp = table[sheet_level][1]
    overrides['advancement_attack_delta'] = int(before.get('advancement_attack_delta') or 0) + new_ba - old_ba
    # Preserve manual offsets relative to the authoritative source-level table.
    actual_ba = (definition.get('progression') or {}).get('base_attack')
    actual_jp = (definition.get('defenses') or {}).get('saving_throw')
    overrides['advancement_base_attack'] = new_ba + (int(actual_ba) - old_ba if actual_ba is not None else 0)
    overrides['advancement_saving_throw'] = new_jp + (int(actual_jp) - old_jp if actual_jp is not None else 0)
    state_row = db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()
    if not state_row:
        raise ValueError('Ficha sem estado de PV confirmado')
    state = json.loads(state_row[0])
    history = deepcopy(before.get('level_hp_history') or [])
    pending = deepcopy(before.get('pending_progression') or [])
    base_hp = int((definition.get('progression') or {}).get('base_maximum_hp') or state['maximum_hp'])
    if not before.get('level_hp_anchor') and not before.get('level_advancement') and source > sheet_level:
        if base_hp != progression.get('sheet_maximum_hp'):
            raise ValueError('Nível já alterado, mas histórico de PV ambíguo; confira o override antes de reconciliar')
        source = sheet_level  # Proven unchanged HP: request the missing dice.
    anchor = deepcopy(before.get('level_hp_anchor') or {'level': source, 'maximum_hp': base_hp})
    if target < source:
        removed = range(target + 1, source + 1)
        records = {int(h['level']): h for h in history}
        known_pending = {int(p['level']) for p in pending}
        if target < int(anchor['level']) or any(n not in records and n not in known_pending for n in removed):
            raise ValueError('Histórico de PV insuficiente para reduzir nível; não serão inventadas rolagens antigas')
        base_hp -= sum(int(records[n]['increment']) for n in removed if n in records)
        for p in pending:
            if p['level'] > target:
                db.execute("UPDATE dice_roll_requests SET status='cancelled' WHERE id=? AND status='pending'", (p['request_id'],))
        pending = [p for p in pending if p['level'] <= target]
    elif target > source:
        if pending:
            raise ValueError('Resolva a progressão de PV pendente antes de subir outro nível')
        from .level_advancement import HP_FIXED
        fixed_levels = HP_FIXED.get(character_id, {})
        recorded = {int(h['level']): h for h in history}
        for level in range(source + 1, target + 1):
            if level not in table:
                raise ValueError('Falta contrato para um nível intermediário')
            if level in recorded:
                base_hp += int(recorded[level]['increment'])
                continue
            if level in fixed_levels:
                # PV fixo pós-nome (OD1): sem rolagem, sem CON (sem regra
                # localizada; Mestre decide). Registrado no histórico.
                increment = int(fixed_levels[level])
                history.append({'level': level, 'fixed': True, 'increment': increment,
                                'note': 'PV fixo OD1, sem dado e sem CON'})
                base_hp += increment
                continue
            key = f'level-hp:{uuid.uuid4().hex}'
            expires = (datetime.now(timezone.utc) + timedelta(days=7)).isoformat()
            gm_owned = character_id == 'dorn7' or overrides.get('controller') == 'gm'
            cursor = db.execute('''INSERT INTO dice_roll_requests
                (request_id,campaign_id,character_id,requested_by,roll_type,label,formula,visibility,source,source_id,
                 status,created_at,expires_at) VALUES(?,?,?,?,?,?,?,?,?,?,?, ?,?)''',
                (key, 'omnisvera', character_id, 'master', 'free', f"{definition['name']} · PV do nível {level}",
                 f"1d{rule['die']}", 'gm' if gm_owned else 'owner', 'level_progression', str(level), 'pending', now, expires))
            pending.append({'level': level, 'request_id': cursor.lastrowid, 'die': rule['die'],
                            'constitution_modifier': attribute_modifier((definition.get('base_attributes') or {}).get('constitution', 10)),
                            'controller': 'master' if gm_owned else character_id})
    overrides.update(level_hp_anchor=anchor, level_hp_history=history, pending_progression=pending, maximum_hp=base_hp)
    if definition.get('class_name') == 'Mago' and not overrides.get('prepared_magic_override'):
        from .level_advancement import MAGE_SLOTS
        intelligence = int((definition.get('base_attributes') or {}).get('intelligence') or 10)
        int_bonus = [2 if intelligence >= 18 else 1 if intelligence >= 16 else 0,
                     1 if intelligence >= 20 else 0, 1 if intelligence >= 17 else 0]
        def _slots(level):
            base = MAGE_SLOTS[level]
            return [value + (int_bonus[i] if i < 3 else 0) for i, value in enumerate(base)]
        slots = _slots(target)
        maxima = dict(before.get('advancement_resources') or {})
        # Existing table-derived resources keep manual surplus, but removed
        # circles lose only the table contribution. Never recharge on level edit.
        old_slots = _slots(source)
        for circle in range(1, max(len(slots), len(old_slots)) + 1):
            key = f'magias_de_{circle}o_circulo'
            resource = next((r for r in state.get('resources', []) if r['key'] == key), None)
            old_table = old_slots[circle - 1] if circle <= len(old_slots) else 0
            new_table = slots[circle - 1] if circle <= len(slots) else 0
            extra = max(0, int((resource or {}).get('maximum', old_table)) - old_table)
            maxima[key] = new_table + extra
            if resource is None:
                resource = {'key': key, 'label': f'Magias de {circle}º círculo', 'current': 0, 'recharge': 'inn_rest'}
                state.setdefault('resources', []).append(resource)
            resource.update(maximum=maxima[key], current=min(int(resource.get('current') or 0), maxima[key]))
        overrides['advancement_resources'] = maxima
        overrides['magic_access'] = len(slots)
    # Optional level-keyed approved contracts reuse the same mechanism.
    for field in ('resource_maxima', 'abilities'):
        values = rule.get(field, {})
        applicable = values.get(str(target), values.get(target))
        if applicable is not None:
            if field == 'abilities':
                overrides['level_abilities'] = deepcopy(applicable)
            else:
                overrides.setdefault('advancement_resources', {}).update(applicable)
                for resource in state.get('resources', []):
                    if resource['key'] in applicable:
                        resource['maximum'] = applicable[resource['key']]
                        resource['current'] = min(resource['current'], resource['maximum'])
    if character_id == 'morthak':
        grants = morthak_level_grants(target)
        if grants.get('abilities'):
            overrides['level_abilities'] = deepcopy(grants['abilities'])
        for key, maximum in (grants.get('resource_maxima') or {}).items():
            overrides.setdefault('advancement_resources', {})[key] = maximum
            resource = next((r for r in state.get('resources', []) if r['key'] == key), None)
            if resource is None:
                # New spell resources start available; existing ones are
                # never refilled by a level edit.
                resource = {'key': key,
                            'label': next((a.get('uses', {}).get('label', key) for a in grants['abilities']
                                           if a.get('uses', {}).get('resource_key') == key), key),
                            'current': maximum, 'maximum': maximum, 'recharge': 'inn_rest'}
                state.setdefault('resources', []).append(resource)
            else:
                resource['maximum'] = max(int(resource.get('maximum') or 0), maximum)
                resource['current'] = min(int(resource.get('current') or 0), resource['maximum'])
    state['maximum_hp'] = base_hp + int((definition.get('progression') or {}).get('maximum_hp_modifier') or 0)
    state['current_hp'] = min(int(state['current_hp']), state['maximum_hp'])
    _save_state(db, character_id, state)


def acknowledge_manual_hp(db, character_id, level, *, actor_id, actor_role, reason):
    """Remove a pending die already included in stored HP. Never roll or heal."""
    from .character_play import _write_event, _now
    if actor_role!='gm':raise PermissionError('Somente o Mestre pode reconhecer PV ajustados manualmente')
    row=db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?',(character_id,)).fetchone()
    if not row:raise ValueError('Progressão não encontrada')
    overrides=json.loads(row[0]);before=deepcopy(overrides)
    if any(h.get('level')==level and h.get('included_in_manual_hp') for h in overrides.get('level_hp_history',[])):
        return {'applied':False,'level':level}
    entry=next((p for p in overrides.get('pending_progression',[]) if p['level']==level),None)
    if not entry:raise ValueError('Não há rolagem pendente para este nível')
    changed=db.execute("UPDATE dice_roll_requests SET status='cancelled' WHERE id=? AND status='pending'",(entry['request_id'],))
    if changed.rowcount!=1:raise ValueError('A rolagem mudou; atualize antes de reconhecer o ajuste')
    overrides['pending_progression']=[p for p in overrides['pending_progression'] if p['level']!=level]
    overrides.setdefault('level_hp_history',[]).append({**entry,'increment':0,'included_in_manual_hp':True,'note':reason})
    now=_now();db.execute('UPDATE character_definition_overrides SET data_json=?,updated_at=? WHERE profile_id=?',
                         (json.dumps(overrides,ensure_ascii=False),now,character_id))
    _write_event(db,character_id=character_id,actor_id=actor_id,actor_role=actor_role,event_type='level_hp_manual_acknowledgement',
                 field='definition',before=before,after=overrides,reason=reason,session_id=None)
    return {'applied':True,'level':level,'request_id':entry['request_id'],'hp_changed':False}


def complete_hp(db, request, event):
    """Called inside the existing roll completion transaction, including retries."""
    from .character_play import _save_state, _write_event, _now
    if request.get('source') != 'level_progression':
        return
    character_id = request['character_id']
    row = db.execute('SELECT data_json FROM character_definition_overrides WHERE profile_id=?', (character_id,)).fetchone()
    overrides = json.loads(row[0]) if row else {}
    entry = next((p for p in overrides.get('pending_progression', []) if p['request_id'] == request['id']), None)
    if not entry:
        return  # already applied or legitimately cancelled by a level correction
    natural = int(event['total'])
    if not 1 <= natural <= int(entry['die']):
        raise ValueError('Resultado de PV fora do Dado de Vida aprovado')
    before = deepcopy(overrides)
    increment = max(1, natural + int(entry['constitution_modifier']))
    overrides.setdefault('level_hp_history', []).append({**entry, 'roll': natural, 'increment': increment, 'roll_event_id': event['id']})
    overrides['pending_progression'] = [p for p in overrides['pending_progression'] if p['request_id'] != request['id']]
    overrides['maximum_hp'] += increment
    state = json.loads(db.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()[0])
    state['maximum_hp'] += increment  # A gain in maximum HP does not heal.
    _save_state(db, character_id, state)
    db.execute('UPDATE character_definition_overrides SET data_json=?,updated_at=? WHERE profile_id=?',
               (json.dumps(overrides, ensure_ascii=False), _now(), character_id))
    _write_event(db, character_id=character_id, actor_id=event['actor_id'], actor_role=event['actor_role'],
                 event_type='level_hp_resolution', field='definition', before=before, after=overrides,
                 reason=f"PV do nível {entry['level']}: {natural} + CON; +{increment} PV máximos, sem cura", session_id=None)
