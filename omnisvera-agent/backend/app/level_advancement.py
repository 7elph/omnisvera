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
               "source": "Classes/Hemomante.md, tabela de mesa 1-20 (Sage)"},
    "morthak": {"class": "Mago", "die": 4, "ba1": 0, "ba2": 0, "jp": 14,
                "source": "Old Dragon 1E Aprimorada (2017), pp. 13–15, 40–42, T3-6; Races/Morto-Vivo Esqueleto.md"},
    "dorn7": {"class": "Mago", "die": 4, "ba1": 0, "ba2": 0, "jp": 14,
              "source": "Old Dragon 1E Aprimorada (2017), T3-6; CAMPANHA/DORN_7_MAGO_2_APROVADO.md"},
}

# Campaign scale is OD1 (Apr morado T3-3/T3-6): Guerreiro nv5 (5,15) XP16000,
# Mago nv5 (2,13) XP20000. OD2 consulted only for specialization mechanics,
# never for BA/JP numbers. Raziel stays to nv2: Hemomante 3+ has no approved
# table; Raziel advances via an explicit progression_contract instead.
TABLES = {
    # Guerreiro OD1 T3-3 (BA simples; multiataque +7/+1 etc. a partir do nv7
    # segue em proposta: attack_count existe, bônus decrescente não).
    "vezemir": {1: (1, 16), 2: (2, 16), 3: (3, 16), 4: (4, 15), 5: (5, 15),
                6: (6, 15), 7: (7, 14), 8: (8, 14), 9: (9, 14), 10: (10, 13),
                11: (10, 13), 12: (11, 13), 13: (11, 12), 14: (12, 12), 15: (12, 12)},
    "raziel": {1: (1, 15), 2: (1, 15), 3: (2, 15), 4: (2, 14), 5: (2, 14)},
    "morthak": {1: (0, 14), 2: (0, 14), 3: (1, 14), 4: (1, 13), 5: (2, 13),
                6: (2, 13), 7: (3, 12), 8: (3, 12), 9: (3, 12), 10: (4, 11),
                11: (4, 11), 12: (4, 11), 13: (5, 10), 14: (5, 10), 15: (5, 10)},
    "dorn7": {1: (0, 14), 2: (0, 14), 3: (1, 14), 4: (1, 13), 5: (2, 13),
              6: (2, 13), 7: (3, 12), 8: (3, 12), 9: (3, 12), 10: (4, 11),
              11: (4, 11), 12: (4, 11), 13: (5, 10), 14: (5, 10), 15: (5, 10)},
}

# PV fixos pós-nome (OD1): sem rolagem de dados a partir do nv10.
# Sem bônus de CON aplicado: sem regra localizada; Mestre decide.
HP_FIXED = {
    "vezemir": {10: 2, 11: 2, 12: 4, 13: 4, 14: 5, 15: 5},
    "morthak": {10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 2},
    "dorn7": {10: 1, 11: 1, 12: 1, 13: 1, 14: 1, 15: 2},
}

# Espaços-base de Mago por círculo (OD1 T3-6). Bônus de INT só até o 3º
# círculo (sem regra localizada para o 4º+): +2/+1/+0 base do código atual.
MAGE_SLOTS = {
    1: [1], 2: [2], 3: [2, 1], 4: [2, 2], 5: [2, 2, 1], 6: [3, 2, 2],
    7: [3, 2, 2, 1], 8: [3, 3, 2, 2], 9: [3, 3, 2, 2, 1], 10: [3, 3, 3, 2, 2],
    11: [4, 3, 3, 2, 2, 1], 12: [4, 3, 3, 3, 2, 2], 13: [4, 4, 3, 3, 2, 2, 1],
    14: [4, 4, 3, 3, 3, 2, 2], 15: [5, 4, 4, 3, 3, 2, 2, 1],
}

# Total acumulado de XP por nível (Old Dragon). Hemomante é homebrew de mesa
# sem tabela publicada: sem requisito exibido até definição do Mestre.
XP_REQUIRED = {
    "vezemir": {3: 4000, 4: 8000, 5: 16000, 6: 32000, 7: 64000, 8: 128000,
                9: 256000, 10: 304000, 11: 408000, 12: 516000, 13: 632000,
                14: 704000, 15: 808000},
    "morthak": {3: 5000, 4: 10000, 5: 20000, 6: 40000, 7: 80000, 8: 160000,
                9: 310000, 10: 460000, 11: 510000, 12: 660000, 13: 710000,
                14: 860000, 15: 910000},
    "dorn7": {3: 5000, 4: 10000, 5: 20000, 6: 40000, 7: 80000, 8: 160000,
              9: 310000, 10: 460000, 11: 510000, 12: 660000, 13: 710000,
              14: 860000, 15: 910000},
    "raziel": {3: 3000, 4: 6000, 5: 12000, 6: 24000, 7: 48000, 8: 100000,
               9: 200000, 10: 300000, 11: 400000, 12: 500000, 13: 600000,
               14: 700000, 15: 800000},
}

# Especializações validadas. Só entradas deste catálogo podem ser registradas;
# qualquer outra escolha falha fechado. Aquisição tardia no nv5 autorizada.
SPECIALIZATIONS = {
    "necromante": {
        "name": "Necromante",
        "class": "Mago",
        "source": "Old Dragon 2, Livro Básico 1 p.45 (especialização de Mago desde o nv1; sem pré-requisito publicado)",
        "locked_to": "morthak",
        "note": "Morthak já é Necromante: nenhuma nova escolha pedida. Abre mão dos círculos 7º-9º; recebe exclusivas por nível.",
        "benefits": [
            "Toque Sombrio: ataque de toque contra alvo vivo, 1d4 de dano e possibilidade de drenar FOR com JPC. Usos e custo adicional aparecem no card da magia.",
            "Aterrorizar: criaturas com menos de 2 DV resistem com JPS; a falha torna os testes difíceis. Alcance, duração e usos aparecem no card da magia.",
        ],
        "restrictions": ["Abre mão dos círculos de magia 7º, 8º e 9º."],
    },
}

def validate_specialization_choice(profile_id, class_name, spec):
    """Normalized choice or ValueError. Only catalog options, matching class,
    honoring locked_to. None clears."""
    wanted = (spec or "").strip() or None
    if wanted is None:
        return None
    entry = SPECIALIZATIONS.get(wanted)
    if entry is None:
        raise ValueError("Especialização sem catálogo validado; escolha apenas opções aprovadas")
    if entry.get("class") != class_name:
        raise ValueError("Especialização incompatível com a classe")
    locked = entry.get("locked_to")
    if locked is not None and locked != profile_id:
        raise ValueError("Especialização reservada a outro personagem")
    return wanted


# Especializações de Guerreiro OD1 (Aprimorado, Homem de Armas): aquisição
# tardia autorizada no nv5. Regras extraídas do PDF da edição da campanha.
WARRIOR_SPECIALIZATIONS = {
    "guerreiro-arma": {
        "name": "Guerreiro de Arma",
        "class": "Guerreiro", "min_level": 5,
        "source": "OD1 Aprimorado (arma de escolha no nv5; +1 a cada 5 nv; crito nv8; re-rolagem nv16)",
        "requires": {"weapon_choice": True},
        "benefits": ["+1 ataque e dano com a arma escolhida (nv5-9; +2 no nv10+)"],
        "restrictions": ["Bônus vale só com a arma escolhida e equipada"],
        "upcoming": ["nv8: margem de crítico -1", "nv16: re-rolar 1 ataque/dia (propostas)"],
        "abilities": {5: [{"id": "maestria-em-arma", "name": "Maestria em Arma", "kind": "ability",
                           "group": "Especialização",
                           "description": "+1 ataque e dano com a arma escolhida enquanto empunhada.",
                           "mechanics_status": "structured", "source": "OD1 Aprimorado",
                           "active": True, "blocked": False}]},
    },
    "barbaro": {
        "name": "Bárbaro",
        "class": "Guerreiro", "min_level": 5,
        "source": "OD1 Aprimorado (rejeita armadura superior a cota de malha; +2 JP-CON)",
        "requires": {},
        "benefits": ["+2 em Jogadas de Proteção modificadas por Constituição"],
        "restrictions": ["Sem armadura superior a cota de malha", "Abandono das regras sociais (narrativo)"],
        "upcoming": ["nv8: frenesi 2x/dia (proposta)"],
        "abilities": {5: [{"id": "selvageria", "name": "Selvageria", "kind": "ability",
                           "group": "Especialização",
                           "description": "+2 JP-CON; sem armadura superior a cota de malha.",
                           "mechanics_status": "structured", "source": "OD1 Aprimorado",
                           "active": True, "blocked": False}]},
    },
    "paladino": {
        "name": "Paladino",
        "class": "Guerreiro", "min_level": 5, "alignment": "ordeiro",
        "source": "OD1 Aprimorado (causa, detectar caos, bônus vs caóticas)",
        "requires": {"alignment": "ordeiro"},
        "benefits": ["Detectar o caos a 1 km (concentração)",
                     "+1 a cada 3 CAR em ataques vs caóticas"],
        "restrictions": ["Dedicação à causa; perde 2 nv com item caótico; perde 3 nv e poderes se deixar ordeiro"],
        "upcoming": ["nv8: +1d6/3CAR + aura 3 m (proposta)", "nv16: aura em aliados (proposta)"],
        "abilities": {5: [{"id": "causa-do-paladino", "name": "Causa do Paladino", "kind": "ability",
                           "group": "Especialização",
                           "description": "Detectar o caos; +1/3 CAR vs caóticas. Aplicação contra caóticas assistida pelo Mestre (sem alinhamento em monstros).",
                           "mechanics_status": "partial", "source": "OD1 Aprimorado",
                           "active": True, "blocked": False}]},
    },
}
SPECIALIZATIONS.update(WARRIOR_SPECIALIZATIONS)

# Propostas NÃO validas para escolha: documentadas, nunca oferecidas.
PROPOSED_SPECIALIZATIONS = {}

# Habilidades e recursos por nível vindos de especialização/tabela, aplicados
# por level_recalculation.recalculate via overrides['level_abilities'].
# Recarga diária = inn_rest (descanso da campanha); sem recarga automática.
NECROMANCER_ABILITIES_5 = [
    {"id": "toque-sombrio", "name": "Toque Sombrio", "kind": "spell", "group": "Magias de Necromante",
     "circle": 1, "active": True, "blocked": False, "mechanics_status": "structured",
     "description": "Regra da campanha: alvo vivo adjacente no grid, ataque de toque 1d4. No início dos turnos seguintes, 1–3 em 1d6 causa perda de 1 PV. Zero PV mata; termina com morte ou fim do combate.",
     "uses": {"resource_key": "toque_sombrio", "label": "Toque Sombrio · uso diário", "maximum": 1, "recharge": "inn_rest"},
     "source": "Old Dragon 2, LB1 p.135; 1 uso/dia + extras consumindo magia memorizada."},
    {"id": "aterrorizar", "name": "Aterrorizar", "kind": "spell", "group": "Magias de Necromante",
     "circle": 1, "active": True, "blocked": False, "mechanics_status": "structured",
     "description": "Regra da campanha: raio 9m+3m/nível pelo grid; dura 1d6+nível turnos individuais do alvo. Criaturas com menos de 2 DV: JPS nega; falha aplica −2 em todos os testes d20. Encerra ao fim do combate.",
     "uses": {"resource_key": "aterrorrizar", "label": "Aterrorizar · uso diário", "maximum": 1, "recharge": "inn_rest"},
     "source": "Old Dragon 2, LB1 p.107; 1 uso/dia + extras consumindo magia memorizada."},
]
NECROMANCER_ABILITIES_5 += [
    {'id':'clonagem','name':'Clonagem','kind':'spell','group':'Magias de Necromante','circle':5,'active':True,'blocked':False,'mechanics_status':'structured',
     'description':'Exceção aprovada no nível 5: um uso por descanso diário e um Fragmento de Cristal Arcano consumível. Executa em 1 rodada; cria até 2 clones em células livres até 10 m. PV 25% dos máximos, ataque básico não mágico, movimento normal. Dura 5 rodadas, exige concentração; cópias não conjuram nem ativam itens.',
     'uses':{'resource_key':'clonagem','label':'Clonagem','maximum':1,'recharge':'inn_rest'},'source':'Magia original aprovada pelo Mestre em 13/10'},
    {'id':'magia-da-morte','name':'Magia da Morte','kind':'spell','group':'Magias de Necromante','circle':5,'active':True,'blocked':False,'mechanics_status':'structured',
     'description':'Exceção aprovada no nível 5: um uso por descanso diário. Até 2d6 criaturas com DV≤4 em 3 m+1 m/nível, por proximidade. JPC evita a morte. Texto literal inclui aliados elegíveis. O conjurador perde 90% dos PV atuais; sobra arredondada para baixo.',
     'uses':{'resource_key':'magia_da_morte','label':'Magia da Morte','maximum':1,'recharge':'inn_rest'},'source':'Regra de campanha aprovada pelo Mestre em 13/10'},
]
NECROMANCER_RESOURCES_5 = {"toque_sombrio": 1, "aterrorrizar": 1,"clonagem":1,"magia_da_morte":1}


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
        if baseline['overrides'].get('pending_progression'):
            blockers.append('PV pendentes: o controlador deve concluir a solicitação de rolagem antes de conferir outro avanço')
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
        reason = ("Hemomante além do nv5: tabela de mesa vai até o 20, mas técnicas e marcos exigem definição com o Mestre."
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
    fixed_hp = HP_FIXED.get(profile_id, {}).get(target_level)
    if needs_hp and fixed_hp is not None:
        # PV fixo pós-nome (OD1): sem rolagem, sem CON (Mestre decide).
        hp_after += int(fixed_hp)
        warnings.append(f"PV fixo de {fixed_hp} no nível {target_level} (OD1, sem dado e sem CON).")
        needs_hp = False
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
            int_bonus = [bonus, 1 if intelligence >= 20 else 0, 1 if intelligence >= 17 else 0]
            base = MAGE_SLOTS[target_level]
            slots = [value + (int_bonus[i] if i < 3 else 0) for i, value in enumerate(base)]
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
