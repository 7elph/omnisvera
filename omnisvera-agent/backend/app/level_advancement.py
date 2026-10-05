"""Atomic advancement using reviewed campaign tables, never the displayed level alone."""
from contextlib import closing
from copy import deepcopy
import hashlib
import json

from .character_play import _connect, _now, _save_state, _write_event, attribute_modifier, init_character_play


RULES = {
    "vezemir": {"class": "Guerreiro", "die": 10, "ba1": 1, "ba2": 2, "jp": 16,
                "source": "Old Dragon 1E Aprimorada (2017), pp. 32–34, T3-3"},
    "raziel": {"class": "Hemomante", "die": 8, "ba1": 1, "ba2": 1, "jp": 15,
               "source": "Classes/Hemomante.md, tabela de mesa, nível 2"},
    "morthak": {"class": "Mago", "die": 4, "ba1": 0, "ba2": 0, "jp": 14,
                "source": "Old Dragon 1E Aprimorada (2017), pp. 13–15, 40–42, T3-6; Races/Morto-Vivo Esqueleto.md"},
    "dorn7": {"class": "Mago", "die": 4, "ba1": 0, "ba2": 0, "jp": 14,
              "source": "Old Dragon 1E Aprimorada (2017), T3-6; CAMPANHA/DORN_7_MAGO_2_APROVADO.md"},
}

# Stop before specialization choices at level 5. Raziel's level 3 requires a
# new technique and interpretation of the approved blood adaptation, not a guess.
TABLES = {
    "vezemir": {1: (1, 16), 2: (2, 16), 3: (3, 16), 4: (4, 15)},
    "raziel": {1: (1, 15), 2: (1, 15)},
    "morthak": {1: (0, 14), 2: (0, 14), 3: (1, 14), 4: (1, 13)},
    "dorn7": {1: (0, 14), 2: (0, 14), 3: (1, 14), 4: (1, 13)},
}

# Total acumulado de XP por nível (Old Dragon). Hemomante é homebrew de mesa
# sem tabela publicada: sem requisito exibido até definição do Mestre.
XP_REQUIRED = {
    "vezemir": {3: 4000, 4: 8000},
    "morthak": {3: 5000, 4: 10000},
    "dorn7": {3: 5000, 4: 10000},
}


def manual_level_event(connection, profile_id, level):
    for row in connection.execute(
        "SELECT before_json,after_json FROM character_events WHERE character_id=? "
        "AND event_type='definition_update' AND reverted_at IS NULL ORDER BY id DESC", (profile_id,)
    ):
        before, after = json.loads(row[0] or '{}'), json.loads(row[1] or '{}')
        if after.get('level') == level and before.get('level', 1) != level:
            return before, after
    return None


def digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False).encode()).hexdigest()


def stored(connection, profile_id):
    row = connection.execute("SELECT data_json FROM character_definition_overrides WHERE profile_id=?", (profile_id,)).fetchone()
    state = connection.execute("SELECT state_json,version FROM character_states WHERE profile_id=?", (profile_id,)).fetchone()
    if state is None:
        raise ValueError("Carregue a ficha antes de preparar a progressão")
    return {"overrides": json.loads(row[0]) if row else {}, "state": json.loads(state[0]), "version": state[1]}


def preview(database_path, character, hp_roll=None, target_level=None, hp_policy='preserve_wounds'):
    if hp_policy not in {'preserve_current', 'preserve_wounds'}:
        raise ValueError('Regra de PV inválida')
    definition = character["definition"]
    profile_id = definition["id"]
    rule = RULES.get(profile_id)
    if not rule or definition.get("class_name") != rule["class"]:
        raise ValueError("Progressão desta classe/personagem ainda não foi conferida")
    level = definition.get("level")
    blockers = []
    warnings = ["Atributos raciais, equipamentos, ajustes manuais e XP são preservados."]
    warnings.append('PV atuais preservados; sem cura.' if hp_policy == 'preserve_current' else 'Regra da Sessão 6: preservar os ferimentos ao aumentar PV máximos. Personagens a 0 PV não são reanimados pelo avanço.')
    warnings.append("CA, atributos e dano de armas não aumentam só por subir de nível. Habilidades autorais e traços raciais não são concedidos novamente.")
    if profile_id == "raziel":
        warnings.append("Adaptação aprovada por Sage: Reserva de Sangue máxima 5; Sentido do Sangue permanece bloqueado. Este avanço não repõe recursos nem libera habilidades.")
    init_character_play(database_path)
    with closing(_connect(database_path)) as connection:
        baseline = stored(connection, profile_id)
        manual = manual_level_event(connection, profile_id, level)
        try:
            sheet_row = connection.execute("SELECT data_json FROM character_sheets WHERE profile_id=?", (profile_id,)).fetchone()
        except Exception:
            sheet_row = None
    xp_current = None
    if sheet_row:
        try:
            xp_current = (json.loads(sheet_row[0] or "{}").get("character_class") or {}).get("experience")
        except (ValueError, AttributeError):
            xp_current = None
    previous = baseline["overrides"].get("level_advancement")
    # Preserve the old explicit level-2 API; the UI supplies the intended target.
    target_level = target_level or 2
    if type(target_level) is not int or target_level < 2:
        raise ValueError("Nível inválido para progressão.")
    if target_level not in TABLES[profile_id]:
        reason = ("Hemomante nv3+ exige nova técnica e interpretação da adaptação de sangue: definir com o Mestre."
                  if profile_id == "raziel" else
                  "Nível ainda não automatizado: conferir escolhas de especialização/técnicas e adaptações antes de avançar.")
        return {"status": "blocked", "source": rule["source"], "target_level": target_level,
                "hit_die": rule["die"], "requires_hp_roll": False, "source_level": level,
                "xp_required": XP_REQUIRED.get(profile_id, {}).get(target_level), "xp_current": xp_current,
                "changes": [], "warnings": warnings, "blockers": [reason], "fingerprint": None}
    history = baseline["overrides"].get("advancement_history", [])
    previous = next((p for p in reversed(history) if p['target_level'] == target_level), previous if previous and previous['target_level'] == target_level else None)
    if previous:
        return {"status": "applied", "source": rule["source"], "target_level": target_level,
                "changes": [], "warnings": [], "blockers": [], "fingerprint": previous["fingerprint"]}
    confirmed = baseline["overrides"].get("level_advancement", {}).get("target_level")
    # A manual definition_update that deliberately set the current level is
    # accepted as proof of the baseline (the Oct-3 level edits happened outside
    # this flow); the DV roll is still always required for a real advance.
    manual_proof = bool(manual and manual[1].get('level') == level and manual[0].get('level', 1) != level)
    if level == target_level - 1 and (level == 1 or confirmed == level or manual_proof):
        source_level, needs_hp = level, True
        if manual_proof and confirmed != level:
            warnings.append("Sem concessão anterior comprovada para este nível: confira o resultado do dado de vida com a mesa.")
    elif level == target_level:
        source_level = target_level - 1
        if confirmed and confirmed != source_level:
            raise ValueError("Há níveis intermediários não conciliados; revise o histórico antes de avançar.")
        # Only known level-2 baselines may be reconciled without a previous grant,
        # unless a manual edit deliberately set the current level (then reconcile it).
        if not confirmed and target_level != 2 and not manual_proof:
            raise ValueError("Baseline anterior não comprovada; reconcilie os níveis em ordem.")
        manual_max_before = manual[0].get('maximum_hp') if manual else None
        manual_max_after = manual[1].get('maximum_hp') if manual else None
        # HP untouched by the manual edit + still at the old value = never granted.
        needs_hp = bool(manual and manual_max_before is not None
                        and manual_max_before == baseline['overrides'].get('maximum_hp')
                        and manual_max_after == manual_max_before)
        if needs_hp:
            warnings.append("Sem concessão anterior comprovada para este nível: confira o resultado do dado de vida com a mesa.")
        if not manual and profile_id == 'morthak':
            raise ValueError("Não foi possível provar se os PV de Morthak já foram concedidos; revise o histórico.")
    else:
        raise ValueError("Avance um nível por vez, a partir da ficha atual.")
    progression = definition.get("progression") or {}
    base_hp = progression.get("base_maximum_hp")
    ba = progression.get("base_attack")
    if base_hp is None or ba is None:
        raise ValueError("PV máximo/base de ataque ausentes; é necessária reconciliação da ficha")
    hp_after = int(base_hp)
    if needs_hp:
        if type(hp_roll) is not int or not 1 <= hp_roll <= rule["die"]:
            blockers.append(f"Informe o resultado natural de 1d{rule['die']} para os PV do nível {target_level}.")
        else:
            constitution = (definition.get("base_attributes") or {}).get("constitution")
            if constitution is None:
                blockers.append("Constituição base ausente.")
            else:
                hp_after += max(1, hp_roll + attribute_modifier(constitution))
    elif hp_roll is not None:
        raise ValueError("PV já reconciliados: não role nem conceda vida novamente")
    # A manual BA unlike either table value is ambiguous, never silently replace it.
    old_ba, old_jp = TABLES[profile_id][source_level]
    new_ba, new_jp = TABLES[profile_id][target_level]
    if ba not in (old_ba, new_ba):
        blockers.append("Base de ataque manual divergente: requer revisão do Mestre.")
    ba_after = new_ba
    jp = (definition.get("defenses") or {}).get("saving_throw")
    if str(jp) not in (str(old_jp), str(new_jp)):
        blockers.append("Jogada de proteção diverge da tabela: preservar até revisão.")
    if level == target_level:
        warnings.append("Reconciliação do nível já exibido: aplicar somente os benefícios pendentes.")
    resource_changes = []
    if profile_id == 'morthak':
        # Preserve unrelated racial/item/per-spell resources. Slots are the class
        # capacity, not an automatic grant of spells or a refill of daily uses.
        intelligence = (definition.get('base_attributes') or {}).get('intelligence')
        if type(intelligence) is not int or not 1 <= intelligence <= 21:
            blockers.append('Inteligência fora da faixa conferida para magias adicionais; revisão necessária.')
        else:
            bonus = 2 if intelligence >= 18 else 1 if intelligence >= 16 else 0
            slots = {2: [2 + bonus], 3: [2 + bonus, 1 + (1 if intelligence >= 20 else 0)],
                     4: [2 + bonus, 2 + (1 if intelligence >= 20 else 0)]}[target_level]
            current_resources = {r['key']: r for r in baseline['state'].get('resources', [])}
            for circle, maximum in enumerate(slots, 1):
                key = f'magias_de_{circle}o_circulo'
                existing = current_resources.get(key)
                before = int(existing['maximum']) if existing else 0
                # Explicit adjustment above the table is kept, never reduced.
                resource_changes.append({'key': key, 'label': f'Magias de {circle}º círculo',
                                         'before': before, 'after': max(before, maximum)})
            warnings.append('Capacidade de círculos inclui Inteligência (T1-1). Magias conhecidas, usos autorais e bônus de itens são preservados; não há descanso ou recarga automática.')
    xp_required = XP_REQUIRED.get(profile_id, {}).get(target_level)
    if xp_required is not None:
        if type(xp_current) is int and xp_current < xp_required:
            warnings.append(f"XP atual {xp_current} abaixo do necessário ({xp_required}) para o nv{target_level}; o Mestre decide.")
        elif type(xp_current) is not int:
            warnings.append("XP não registrado na ficha; o Mestre confirma o requisito.")
    changes = [
        {"field": "level", "label": "Nível", "before": level, "after": target_level},
        {"field": "maximum_hp", "label": "PV máximo base", "before": base_hp, "after": hp_after},
        {"field": "base_attack", "label": "Base de ataque", "before": ba, "after": ba_after},
        {"field": "saving_throw", "label": "Jogada de proteção", "before": jp, "after": new_jp},
    ]
    current_resources = {r['key']: r for r in baseline['state'].get('resources', [])}
    for r in resource_changes:
        existing = current_resources.get(r['key'], {})
        changes.append({"field": f"resource:{r['key']}", "label": r['label'],
                        "before": r['before'], "after": r['after'],
                        "current": existing.get('current'), "note": "capacidade máxima; usos atuais preservados, sem recarga"})
    old_current = baseline['state'].get('current_hp')
    old_maximum = baseline['state'].get('maximum_hp')
    new_maximum = hp_after + int(progression.get('maximum_hp_modifier') or 0)
    new_current = old_current
    if old_current is not None:
        new_current = min(old_current, new_maximum)
        if hp_policy == 'preserve_wounds' and old_current > 0:
            new_current = max(0, min(new_maximum, old_current + new_maximum - int(old_maximum if old_maximum is not None else new_maximum)))
        changes.append({'field': 'current_hp', 'label': 'PV atuais', 'before': old_current, 'after': new_current,
                        'old_maximum': old_maximum})
    changes.append({'field': 'maximum_hp_final', 'label': 'PV máximo final (com modificadores)',
                    'before': old_maximum, 'after': new_maximum, 'noop': old_maximum == new_maximum, 'info': True})
    attack_delta_total = int(baseline['overrides'].get('advancement_attack_delta') or 0) + (ba_after - ba)
    changes.append({'field': 'attack_delta_total', 'label': 'Delta de ataque acumulado',
                    'before': int(baseline['overrides'].get('advancement_attack_delta') or 0),
                    'after': attack_delta_total, 'noop': ba_after == ba, 'info': True})
    for change in changes:
        if "noop" not in change and "info" not in change:
            change["noop"] = str(change["before"]) == str(change["after"])
    if not needs_hp and all(c.get("noop") for c in changes if not c.get("info")) and not resource_changes:
        warnings.append("Nada pendente: a ficha já reflete este nível; confirmar só registra a conferência.")
    result = {
        "hp_policy": hp_policy,
        "status": "blocked" if blockers else "ready", "target_level": target_level, "hit_die": rule["die"],
        "requires_hp_roll": needs_hp, "source_level": source_level,
        "source": rule["source"], "warnings": warnings, "blockers": blockers,
        "xp_required": xp_required, "xp_current": xp_current,
        "changes": changes,
    }
    result["fingerprint"] = digest({"baseline": baseline, "definition": definition, "hp_roll": hp_roll, "plan": result})
    result["_baseline"] = baseline
    result["_resources"] = resource_changes
    return result


def apply(database_path, character, expected_fingerprint, hp_roll=None, target_level=None, hp_policy='preserve_wounds'):
    plan = preview(database_path, character, hp_roll, target_level, hp_policy)
    if plan["status"] == "applied":
        if plan["fingerprint"] != expected_fingerprint:
            raise ValueError("Este avanço já foi aplicado por outra confirmação")
        return False
    if plan["status"] != "ready":
        raise ValueError("; ".join(plan["blockers"]))
    if plan["fingerprint"] != expected_fingerprint:
        raise ValueError("A ficha mudou. Confira uma nova prévia antes de confirmar")
    profile_id = character["definition"]["id"]
    with closing(_connect(database_path)) as connection, connection:
        connection.execute("BEGIN IMMEDIATE")
        current = stored(connection, profile_id)
        if current != plan["_baseline"]:
            raise ValueError("Estado alterado durante a confirmação; atualize a prévia")
        overrides = deepcopy(current["overrides"])
        changes = {c["field"]: c for c in plan["changes"]}
        overrides.update(level=plan['target_level'], maximum_hp=changes["maximum_hp"]["after"])
        # Offset attacks already on the sheet, preserving attribute/manual/equipment bonuses.
        overrides["advancement_attack_delta"] = int(overrides.get('advancement_attack_delta') or 0) + changes["base_attack"]["after"] - changes["base_attack"]["before"]
        overrides["advancement_base_attack"] = changes["base_attack"]["after"]
        overrides['advancement_saving_throw'] = changes['saving_throw']['after']
        old_record = overrides.get('level_advancement')
        history = overrides.setdefault('advancement_history', [])
        if old_record and not any(p['fingerprint'] == old_record['fingerprint'] for p in history):
            history.append(deepcopy(old_record))
        overrides["level_advancement"] = {"target_level": plan['target_level'], "fingerprint": expected_fingerprint,
                                           "source": plan["source"], "hp_roll": hp_roll, "hp_policy": hp_policy}
        overrides.setdefault('advancement_history', []).append(deepcopy(overrides['level_advancement']))
        state = deepcopy(current["state"])
        state["maximum_hp"] = changes["maximum_hp"]["after"] + int(character["definition"]["progression"].get("maximum_hp_modifier") or 0)
        if state.get("current_hp") is not None:
            state["current_hp"] = changes['current_hp']['after']
        for change in plan['_resources']:
            overrides.setdefault('advancement_resources', {})[change['key']] = change['after']
            resource = next((r for r in state.setdefault('resources', []) if r['key'] == change['key']), None)
            if resource is None:
                resource = {'key': change['key'], 'label': change['label'], 'current': 0, 'recharge': 'inn_rest'}
                state['resources'].append(resource)
            resource['maximum'] = change['after']
        connection.execute("INSERT INTO character_definition_overrides VALUES(?,?,?) ON CONFLICT(profile_id) DO UPDATE SET data_json=excluded.data_json,updated_at=excluded.updated_at",
                           (profile_id, json.dumps(overrides, ensure_ascii=False), _now()))
        if state != current["state"]:
            _save_state(connection, profile_id, state)
        _write_event(connection, character_id=profile_id, actor_id="master", actor_role="gm",
                     event_type="level_advancement", field="definition", before=current["overrides"], after=overrides,
                     reason=f"Progressão conferida ao nível {plan['target_level']}; {plan['source']}; PV: {hp_policy}; sem recarga", session_id=None)
    return True
