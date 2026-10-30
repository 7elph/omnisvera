"""Pure poison specs for complex on-hit/venom effects. Missing source parameters remain pending."""
from __future__ import annotations

import re
from typing import Any, Dict, List

from .damage_profiles import normalized
from .monster_riders import _attack_indices


_FAMILIES = {'poison': r'venen'}


def _extract_jp_saves(text: str) -> List[str]:
    saves = re.findall(r'\bjp\s*([dcs])\b', text)
    return saves


def _first_dice(text: str) -> str | None:
    m = re.search(r'(\d+\s*d\s*\d+(?:\s*[+-]\s*\d+)?)', text)
    if not m:
        return None
    return re.sub(r'\s+', '', m.group(1))


def _has_negation(text: str) -> bool:
    if re.search(r'\bnunca\b', text):
        return True
    if re.search(r'\bnao\s+(?:causa|produz|provoca|paralis|petrific|mata|morrer|faz|inocul)', text):
        return True
    if re.search(r'\bnao\s+e\s+capaz\b', text):
        return True
    return False


def _make_id(identity: str, ability_index: int) -> str:
    return f'{identity}:poison:{ability_index}'


def _build_hit_base(identity: str, ability_index: int, name: str, description: str, attack_indices: List[int], save: str) -> Dict[str, Any]:
    return {
        'id': _make_id(identity, ability_index),
        'monster_id': identity,
        'name': name,
        'description': description,
        'ability_index': ability_index,
        'attack_indices': attack_indices,
        'save': save,
    }


_SEWER_FEVER_SOURCE = normalized('um rato possui 1 chance em 1d6 de transmitir Febre do Esgoto a um alvo mordido. Um alvo mordido que falhar em uma JPC, ficará doente e com valor de Constituição igual a 1 por 1d6 dias.')


def disease_specs(monster: Dict[str, Any]) -> Dict[str, Any]:
    """One reviewed source, copied IDs supported. Disease is never poison."""
    on_hit, pending = [], []
    for index, ability in enumerate(monster.get('abilities') or []):
        description = str(ability.get('description') or '')
        text = normalized(description)
        if not re.search(r'doenca|infect|febre|colera', text):
            continue
        indices = _attack_indices(monster.get('attacks') or [], text, r'doenc')
        if text != _SEWER_FEVER_SOURCE or not indices:
            pending.append({'ability_index': index, 'name': ability.get('name'), 'text': description,
                            'reason': 'doenca_chance_cumulativa_sem_escopo_revisado' if 'cumulativ' in text else 'doenca_sem_contrato_completo_revisado'})
            continue
        hit = _build_hit_base(str(monster.get('id') or ''), index, 'Febre do Esgoto', description, indices, 'JPC')
        hit.update(effect='disease_attribute', condition='diseased', natural_disease=True,
                   attribute='constitution', attribute_max=1, chance_formula='1d6', chance_success_max=1,
                   duration_formula='1d6', duration_unit='days')
        hit['id'] = f"{monster.get('id')}:disease:{index}"
        on_hit.append(hit)
    return {'on_hit': on_hit, 'pending': pending}


def poison_specs(monster: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(monster, dict):
        raise TypeError('monster deve ser um dicionário')
    identity = str(monster.get('id') or '')
    sources: List[Dict[str, Any]] = []
    pending: List[Dict[str, Any]] = []
    on_hit: List[Dict[str, Any]] = []

    attacks = monster.get('attacks') or []
    abilities = monster.get('abilities') or []

    for index, ability in enumerate(abilities):
        name = str(ability.get('name') or '')
        description = str(ability.get('description') or '')
        source = {'ability_index': index, 'name': name, 'text': description}
        sources.append(source)

        text_norm = normalized(description)
        title_norm = normalized(name)
        full_norm = title_norm + ' ' + text_norm

        def reject(reason: str, src=source):
            pending.append({**src, 'reason': reason})

        # Exclusions
        if re.search(r'^\s*imun|imunidade|imune\b', title_norm) or re.search(r'\bimunidade\b', title_norm) or re.search(r'\bimune\b', title_norm):
            reject('fora_do_corte')
            continue
        if re.search(r'\bresisten', title_norm):
            reject('fora_do_corte')
            continue
        if re.search(r'\b(?:olhar|olhos|gaze|cuspe|baforada|sopro|nuvem|gas)\b', text_norm):
            reject('ativacao_nao_on_hit')
            continue
        if _has_negation(text_norm):
            reject('efeito_negado')
            continue
        # Reject disease/infection
        if re.search(r'\bdoenca|doenca|infecc|infectad|colera|cler|cera|diarre', text_norm):
            reject('doenca_ou_infeccao')
            continue

        # Must be poison-related
        if not re.search(r'venen', full_norm):
            # if it's clearly venom-linked by attack marker in full context? keep strict as before
            reject('fora_do_corte')
            continue

        # Extract JP
        saves = _extract_jp_saves(text_norm)
        if not saves:
            reject('jp_ausente')
            continue
        if len(set(s.lower() for s in saves)) != 1:
            reject('jp_ausente_ou_ambigua')
            continue
        save_type = saves[0].lower()
        save = 'JP' + save_type.upper()

        # Attack linkage
        indices = _attack_indices(attacks, text_norm, _FAMILIES['poison'])
        if not indices:
            # Medusa hair snakes - no configured snake attack
            if re.search(r'serpent', text_norm) and re.search(r'cabelo', text_norm):
                reject('medusa_cabelo_sem_gatilho_configurado')
                continue
            reject('sem_vinculo_ataque')
            continue

        # Delayed attribute - strength halved
        if re.search(r'metade.*forca|forca.*metade', text_norm):
            delay_m = re.search(r'(1d[0-9]+(?:\s*[+-]\s*[0-9]+)?)\s+turnos', text_norm)
            dur_m = re.search(r'(2d[0-9]+(?:\s*[+-]\s*[0-9]+)?)\s+turnos', text_norm)
            if delay_m and dur_m:
                hit = _build_hit_base(identity, index, name, description, indices, save)
                hit.update({
                    'effect': 'delayed_attribute',
                    'attribute': 'strength',
                    'multiplier': 0.5,
                    'delay_formula': re.sub(r'\s+', '', delay_m.group(1)),
                    'delay_unit': 'turns',
                    'duration_formula': re.sub(r'\s+', '', dur_m.group(1)),
                    'duration_unit': 'turns',
                    'rounding': None,
                })
                on_hit.append(hit)
                continue
            reject('descricao_incompleta')
            continue

        # Delayed condition
        if re.search(r'sonifer|adormec', full_norm) or re.search(r'paralis', full_norm):
            # Skip if it's actually attribute drain
            if re.search(r'perda.*pontos|perder.*pontos', text_norm) and re.search(r'por\s+turno', text_norm):
                # will be handled by periodic if conditions met
                pass
            else:
                delay_m = re.search(r'(1d[0-9]+(?:\s*[+-]\s*[0-9]+)?)\s+rodadas', text_norm)
                dur_m = re.search(r'(1d[0-9]+(?:\s*[+-]\s*[0-9]+)?)\s+turnos', text_norm)
                if delay_m and dur_m and re.search(r'comeca.*fazer.*efeito|começa', text_norm):
                    hit = _build_hit_base(identity, index, name, description, indices, save)
                    if re.search(r'sonifer|adormec', full_norm):
                        hit.update({
                            'effect': 'delayed_condition',
                            'condition': 'asleep',
                            'delay_formula': re.sub(r'\s+', '', delay_m.group(1)),
                            'delay_unit': 'rounds',
                            'duration_formula': re.sub(r'\s+', '', dur_m.group(1)),
                            'duration_unit': 'turns',
                        })
                    elif re.search(r'paralis', full_norm):
                        hit.update({
                            'effect': 'delayed_condition',
                            'condition': 'paralyzed',
                            'delay_formula': re.sub(r'\s+', '', delay_m.group(1)),
                            'delay_unit': 'rounds',
                            'duration_formula': re.sub(r'\s+', '', dur_m.group(1)),
                            'duration_unit': 'turns',
                        })
                    else:
                        reject('descricao_incompleta')
                        continue
                    hit['delay_seconds_per_unit'] = 10
                    hit['duration_seconds_per_unit'] = 600
                    on_hit.append(hit)
                    continue
                # if periodic-like, don't reject as sono_sem_atraso
                if re.search(r'perda.*pontos|perder.*pontos', text_norm) and re.search(r'por\s+turno', text_norm):
                    pass  # will be handled by periodic below
                else:
                    reject('sono_sem_atraso')
                    continue

        # Periodic
        if re.search(r'por\s+turno|a cada.*turno', text_norm):
            floor_match = re.search(r'\bcheg(?:ar|ue|a)\b[^.]*?\ba\s*(\d+)\b', text_norm)
            if floor_match or re.search(r'at.*zero|ate.*zero|morrer|perder todos', text_norm):
                attr = None
                for a in ['constituicao', 'destreza', 'inteligencia', 'forca', 'sabedoria', 'carisma']:
                    if re.search(r'\b' + a + r'\b', text_norm):
                        if a == 'constituicao':
                            attr = 'constitution'
                        elif a == 'destreza':
                            attr = 'dexterity'
                        elif a == 'inteligencia':
                            attr = 'intelligence'
                        elif a == 'forca':
                            attr = 'strength'
                        elif a == 'sabedoria':
                            attr = 'wisdom'
                        elif a == 'carisma':
                            attr = 'charisma'
                        break
                if not attr:
                    reject('atributo_sem_dado')
                    continue
                amt = _first_dice(text_norm)
                if not amt:
                    reject('descricao_incompleta')
                    continue
                hit = _build_hit_base(identity, index, name, description, indices, save)
                hit.update({
                    'effect': 'poison_attribute_periodic',
                    'attribute': attr,
                    'amount_formula': amt,
                    'interval_seconds': 600,
                    'floor': 0,
                    'lethal_at_floor': True,
                    'duration': None,
                    'restoration': None,
                })
                floor_val = 0
                if floor_match:
                    floor_val = int(floor_match.group(1))
                hit['floor'] = floor_val
                if floor_val == 0:
                    if re.search(r'morrer|morte|matar', text_norm):
                        hit['lethal_at_floor'] = True
                    else:
                        hit['lethal_at_floor'] = False
                else:
                    hit['lethal_at_floor'] = False
                on_hit.append(hit)
                continue

        # Instant attribute
        if re.search(r'perda.*pontos.*constituicao|constituicao.*perder', text_norm):
            attr = 'constitution'
            amt = _first_dice(text_norm)
            if not amt:
                reject('descricao_incompleta')
                continue
            hit = _build_hit_base(identity, index, name, description, indices, save)
            hit.update({
                'effect': 'poison_attribute',
                'attribute': attr,
                'amount_formula': amt,
                'interval_seconds': None,
                'floor': 0,
                'duration': None,
                'restoration': None,
            })
            on_hit.append(hit)
            continue

        # Wyvern etc - not in this parser scope
        if re.search(r'mortal.*matar', text_norm):
            reject('fora_do_corte')
            continue

        reject('fora_do_corte')
        continue

    return {
        'schema_version': 1,
        'monster_id': identity,
        'on_hit': on_hit,
        'pending': pending,
        'sources': sources,
    }
