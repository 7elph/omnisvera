"""Read-only action migration inventory, not an executor or authorization layer.

Callers supply an already-authorized effective sheet. No database reads or raw
sheet-catalog reloads, resource mutation or executable user scripts.
Bindings name existing handlers; certification remains independently assessed.
"""
from __future__ import annotations

from urllib.parse import quote

from .dice_rolls import parse_formula
from .sheet_action_inventory import audit_abilities
from .hemomancy import ACTION_IDS as HEMOMANCY_ACTIONS
from .access import sanitize_player_text


_TECHNIQUES = {
    'vezemir': {'forca-arcana', 'velocidade', 'frenesi', 'provocacao'},
    'morthak': {'animar-mortos', 'levantar-esqueleto', 'levantar-um-esqueleto',
                'dispensar-invocacao', 'toque-sombrio', 'aterrorizar', 'clonagem', 'magia-da-morte'},
    'raziel': {'mordida', 'regeneracao-vampirica', 'lamina-de-sangue', 'marca-rubra',
               'sangue-defensivo', 'garras-predatorias', 'investida-predatoria', 'arma-de-sangue','velocidade','reforco'},
    'dorn7': {'dorn-reparo'},
}
_DORN_SPELLS = {'relampago', 'reflexos', 'teia', 'forca-arcana', 'dissipar-magia',
                'levitacao', 'escuridao'}
_LEGACY_BLOOD_COST = {'lamina-de-sangue': 1, 'marca-rubra': 1, 'regeneracao-vampirica': 1,
                      'sangue-defensivo': 2, 'garras-predatorias': 1, 'investida-predatoria': 2,
                      'arma-de-sangue': 2}
_CONFIRM = '/combat/attacks/{resolution_id}/confirm'
_NATIVE_LIMITS = ['Disponibilidade local não valida turno, alvo, alcance, permissões ou concorrência; '
                  'o handler nativo revalida tudo.',
                  'Binding nativo não certifica todos os efeitos, passivas ou caminhos da ação.']


def _number(value):
    return value if type(value) in (int, float) else None


def _rollable_damage(value):
    try:
        parse_formula(str(value or ''))
        return True
    except ValueError:
        return False


def _entry(ref, label, kind, origin):
    return {'ref': ref, 'label': str(label), 'kind': str(kind), 'binding': None,
            'execution': None, 'automation_scope': 'assisted',
            'availability': {'state': 'unknown', 'reason': 'Exige revisão da mecânica; cadastro não é automação.'},
            'limitations': [], 'certification': 'not_assessed', 'origin': origin}


def _native(entry, binding, endpoint, **execution):
    entry.update(binding=binding, automation_scope='native',
                 execution={'endpoint': endpoint, 'method': 'POST', **execution},
                 availability={'state': 'available', 'reason': 'Pré-requisitos locais satisfeitos; validação final no backend.'})
    entry['limitations'].extend(_NATIVE_LIMITS)


def _unavailable(entry, reason, *, blocked=False):
    entry['availability'] = {'state': 'unavailable', 'reason': reason}
    if blocked:
        entry.update(automation_scope='blocked', execution=None)


def _resource(state, key):
    # Mirrors the sheet's legacy hyphen/underscore resource lookup, not a new resource.
    resources = state.get('resources') or []
    return next((r for r in resources if r.get('key') == key), None) or next(
        (r for r in resources if r.get('key') == key.replace('-', '_')), None)


def _item(inventory, title, *, equipped=False):
    return next((item for item in inventory
                 if str(item.get('item_title') or '').casefold() == title.casefold()
                 and (_number(item.get('quantity')) or 0) > 0
                 and (not equipped or item.get('equipped'))), None)


def _check_prerequisites(entry, owner, ability, state, inventory):
    identity = ability.get('id')
    required = ability.get('requires_equipped_item')
    if required and not any(item.get('equipped') and (_number(item.get('quantity')) or 0) > 0
                            and required in (item.get('item_path'), item.get('item_title')) for item in inventory):
        _unavailable(entry, 'Item requerido não equipado: ' + str(required))
        return
    component = 'Fragmento de Cristal Arcano' if owner == 'morthak' and identity == 'clonagem' else (
        'Kit de Reparo' if owner == 'dorn7' and identity == 'dorn-reparo' else None)
    if component and not _item(inventory, component):
        _unavailable(entry, 'Componente consumível ausente: ' + component)
        return
    uses = ability.get('uses') or {}
    key = uses.get('resource_key')
    cost = _number(uses.get('cost'))
    if cost is None:
        cost = 1
    if owner == 'raziel' and identity in _LEGACY_BLOOD_COST and not key:
        key = 'reserva_de_sangue'
        cost = _number(uses.get('cost'))
        if cost is None:
            cost = _LEGACY_BLOOD_COST[identity]
    if key:
        resource = _resource(state, str(key))
        remaining = _number((resource or {}).get('current'))
        if remaining is None:
            entry['availability'] = {'state': 'unknown', 'reason': 'Recurso não informado na ficha efetiva: ' + str(key)}
        elif remaining < cost:
            if owner == 'morthak' and identity in {'aterrorizar', 'toque-sombrio'}:
                entry['availability'] = {'state': 'unknown',
                    'reason': 'Uso diário esgotado; o handler valida a alternativa memorizada explicitamente.'}
            else:
                _unavailable(entry, 'Recurso insuficiente: ' + str(key))
    if owner == 'raziel' and state.get('animal_form') and identity not in {'forma-da-noite', 'caixao'}:
        _unavailable(entry, 'Forma animal não permite técnicas humanoides; desative-a no fluxo nativo.')


def sheet_action_manifest(character_id: str, definition: dict, state: dict, inventory: list) -> list[dict]:
    """Describe every supplied effective attack/ability; never load a raw catalog.

    Visibility is the caller's responsibility. Returned fields are allowlisted;
    annotations, GM fields, descriptions and the original DTO are never copied.
    """
    owner = str(character_id)
    path_owner = quote(owner, safe='')
    result = []
    for attack in definition.get('attacks') or []:
        identity = str(attack.get('id') or '')
        entry = _entry(f'attack:{owner}:{identity}', attack.get('name') or identity, 'attack', 'effective_sheet')
        if identity:
            _native(entry, 'character_attack', f'/characters/{path_owner}/attacks/resolve',
                    payload={'attack_id': identity}, confirmation_endpoint=_CONFIRM)
        if not identity or not _rollable_damage(attack.get('damage')) or _number(attack.get('attack_bonus')) is None:
            _unavailable(entry, 'Ataque sem dano rolável ou bônus configurado; arma pode não estar equipada.', blocked=True)
        if owner == 'raziel' and state.get('animal_form'):
            _unavailable(entry, 'Forma animal não permite ataques humanoides.')
        if not state and entry['availability']['state'] == 'available':
            entry['availability'] = {'state': 'unknown', 'reason': 'Estado persistido ausente; não concede disponibilidade.'}
        result.append(entry)
    for ability in audit_abilities(definition):
        identity = str(ability.get('id') or '')
        kind = str(ability.get('kind') or 'ability')
        entry = _entry(f'technique:{owner}:{identity}', ability.get('name') or identity, kind, 'effective_sheet')
        entry['visible_on_sheet']=ability.get('visible_on_sheet',True)
        entry.update(description=sanitize_player_text(str(ability.get('description') or '')),
                     image_path=ability.get('image_path'), group=ability.get('group'))
        if ability.get('blocked'):
            entry.update(automation_scope='blocked', availability={'state': 'blocked', 'reason': 'Regra bloqueada na ficha efetiva.'})
        elif kind in {'passive', 'resource', 'trait'} or ability.get('active') is False:
            entry.update(automation_scope='passive', availability={'state': 'passive', 'reason': 'Consulta passiva/recurso; não emite comando.'})
            entry['limitations'].append('Cadastro passivo não comprova aplicação automática; veja o handler e evidências próprias.')
        elif owner=='raziel' and identity in HEMOMANCY_ACTIONS and ability.get('action_revision'):
            _native(entry,'hemomancy_shield' if identity=='hemomancia-escudo' else 'hemomancy_attack',
                f'/characters/{path_owner}/techniques/{quote(identity,safe="")}',
                payload={'definition_revision':ability['action_revision'],'mode':ability['hemomancy_mode']})
            if identity!='hemomancia-escudo':
                entry['execution']['confirmation_endpoint']=_CONFIRM
            entry['cost']={'resource_key':'reserva_de_sangue','current_estimate':ability['uses']['cost'],
                           'invocation':ability['invocation_cost'],'skill':ability['skill_cost']}
            entry['limitations'].append('Custo estimado para a arma ativa nesta leitura; o comando revalida invocação, turno e reserva atomicamente.')
        elif identity in _TECHNIQUES.get(owner, set()):
            binding = 'vezemir_skill' if identity in {'frenesi', 'provocacao'} else (
                'necromancer_spell' if owner == 'morthak' and identity in {'toque-sombrio', 'aterrorizar', 'clonagem', 'magia-da-morte'} else 'character_technique')
            _native(entry, binding, f'/characters/{path_owner}/techniques/{quote(identity, safe="")}')
            if identity in {'mordida', 'lamina-de-sangue', 'garras-predatorias', 'investida-predatoria', 'arma-de-sangue', 'toque-sombrio'}:
                entry['execution']['confirmation_endpoint'] = _CONFIRM
            if identity in {'animar-mortos', 'levantar-esqueleto', 'levantar-um-esqueleto'}:
                entry['limitations'].append('Cadáver, instância ativa, coexistência, dispensa e custo são validados pelo handler de invocação.')
        elif ((owner in {'morthak', 'dorn7'} and identity == 'misseis-magicos')
              or (owner == 'morthak' and identity == 'adaga-de-osso')):
            _native(entry, 'character_attack', f'/characters/{path_owner}/attacks/resolve',
                    payload={'attack_id': identity}, confirmation_endpoint=_CONFIRM)
        elif owner == 'dorn7' and identity in _DORN_SPELLS:
            _native(entry, 'dorn_spell', '/gm/combat/effects', action='dorn_spell_cast', payload={'spell_id': identity})
        elif owner == 'dorn7' and identity in {'dorn_guard', 'dorn_vanguard'}:
            _native(entry, 'dorn_protocol', '/gm/combat/effects', action=identity)
        elif owner == 'raziel' and identity in {'forma-da-noite', 'caixao'}:
            action = 'consume_resource' if identity == 'forma-da-noite' else 'rest_in_coffin'
            _native(entry, 'character_state_action', f'/characters/{path_owner}/actions', action=action)
            entry['limitations'].append('Forma exige recurso/animal válidos e possui desativação própria; Caixão depende do descanso concedido pelo Mestre.')
        else:
            entry['limitations'].append('Sem binding aprovado; não infere execução de texto, nome ou mechanics_status.')
        if entry['automation_scope'] == 'native':
            _check_prerequisites(entry, owner, ability, state, inventory)
            if not state and entry['availability']['state'] == 'available':
                entry['availability'] = {'state': 'unknown', 'reason': 'Estado persistido ausente; não concede disponibilidade.'}
        result.append(entry)
    for item in inventory:
        # Same display hints as the current sheet's isConsumable/resourceItem;
        # these hints only inventory an item, never infer an executable effect.
        item_type = str(item.get('item_type') or '').casefold()
        charges_max = _number(item.get('charges_max')) or 0
        uses_rules = any(rule.get('trigger') == 'on_use' for rule in item.get('effect_rules') or []
                         if isinstance(rule, dict))
        if not (item.get('usable') or charges_max > 0 or uses_rules
                or (owner == 'vezemir' and item.get('item_title') == 'Pulseira de Vinhas')
                or (owner == 'dorn7' and item.get('item_title') == 'Kit de Reparo')
                or any(term in item_type for term in ('consum', 'poção', 'potion'))):
            continue
        path = str(item.get('item_path') or '')
        entry = _entry(f'item:{owner}:{path}', item.get('item_title') or path, 'item', 'effective_sheet')
        entry.update(description=sanitize_player_text(str(item.get('description') or '')),
                     image_path=item.get('image_path') or item.get('thumbnail') or item.get('cover'))
        rules = [rule for rule in item.get('effect_rules') or [] if isinstance(rule, dict) and rule.get('trigger') == 'on_use']
        if owner == 'vezemir' and item.get('item_title') == 'Pulseira de Vinhas':
            _native(entry, 'vine_bracelet', '/characters/vezemir/vines')
            if not item.get('equipped'):
                _unavailable(entry, 'Pulseira de Vinhas não equipada.')
        elif owner == 'dorn7' and item.get('item_title') == 'Kit de Reparo':
            _native(entry, 'character_technique', '/characters/dorn7/techniques/dorn-reparo')
            entry['limitations'].append('O kit é consumido pelo Reparo nativo; não é um segundo uso independente.')
        elif item.get('usable') and rules and all(rule.get('kind') in {
                'heal_hp', 'restore_resource', 'temporary_hp', 'add_condition'} for rule in rules):
            _native(entry, 'inventory_item', f'/characters/{path_owner}/actions',
                    action='use_item', payload={'item_path': path})
            entry['limitations'].append('O comando nativo revalida regras, cura, estoque e orçamento de consumíveis; não consome por consulta.')
        else:
            entry['limitations'].append('Sem executor aprovado para as regras deste item; descrição e cargas não certificam uso automático.')
        quantity = _number(item.get('quantity'))
        charges = _number(item.get('charges_current'))
        if quantity is not None and quantity <= 0:
            _unavailable(entry, 'Item sem estoque no inventário efetivo.')
        elif charges_max > 0 and charges is not None and charges <= 0:
            _unavailable(entry, 'Item sem cargas disponíveis.')
        if not state and entry['availability']['state'] == 'available':
            entry['availability'] = {'state': 'unknown', 'reason': 'Estado persistido ausente; não concede disponibilidade.'}
        result.append(entry)
    return result


def token_action_manifest(token: dict) -> list[dict]:
    """Native token/NPC attacks only; extracted usables remain assisted.

    Uses the existing pure action-map parser. Frequencies/reference dice are not
    promoted into resource rules or universal executors.
    """
    from .monster_actions import build_action_map
    from .combat import monster_attack_definition
    identity = str(token.get('id') or '')
    sheet = token.get('sheet') or {}
    action_map = build_action_map(str(token.get('name') or ''), sheet.get('attacks') or [], sheet.get('abilities') or [])
    result = []
    for attack in action_map['attacks']:
        index = str(attack['index'])
        entry = _entry(f'token:{identity}:attack:{index}', attack['name'], 'attack', 'native_token')
        native_valid = False
        reason = attack.get('reason') or 'Token sem identidade persistida.'
        if token.get('token_type') not in (None, 'monster'):
            reason = 'Esta rota nativa aceita somente tokens de criatura (monster).'
        elif attack['status'] == 'ready' and identity:
            try:
                # The executor is the authority, not the looser catalogue parser.
                monster_attack_definition({**token, 'name': token.get('name') or 'Criatura'}, index)
                native_valid = True
            except ValueError as error:
                reason = str(error)
        if native_valid:
            _native(entry, 'token_attack', f'/gm/combat/tokens/{quote(identity, safe=":")}/attacks/resolve',
                    payload={'attack_id': index}, confirmation_endpoint=_CONFIRM)
            for rider in attack.get('riders') or []:
                entry['limitations'].append('Rider manual, não automatizado: ' + str(rider))
        else:
            _unavailable(entry, reason, blocked=True)
        result.append(entry)
    for ability in action_map['active_abilities'] + action_map['passive_abilities'] + action_map['spellcasting']:
        entry = _entry(f'token:{identity}:ability:{ability["name"]}', ability['name'], ability['kind'], 'native_token')
        if ability['kind'] == 'passive':
            entry.update(automation_scope='passive', availability={'state': 'passive', 'reason': 'Passiva extraída; aplicação não certificada.'})
        entry['limitations'].extend(['JP/dados/alcance extraídos são referência; condições e duração não são execução completa.',
                                    'A frequência extraída é texto, não custo automatizado.',
                                    'Sem executor genérico: faltam garantias de idempotência, hooks de PV e custos.'])
        result.append(entry)
    return result
