"""Evidence-based inventory of a sheet. Test metadata, NOT a second rules engine."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys

# Both direct scripts (parent and simulation child) start from backend/scripts.
# Resolve only this repository's backend, never an environment-provided path.
_BACKEND=str(Path(__file__).resolve().parents[1])
if _BACKEND not in sys.path:
    sys.path.insert(0,_BACKEND)
from app.sheet_action_inventory import audit_abilities


VERIFICATION_CHECKS = {'execution', 'persistence', 'idempotency', 'cost', 'range', 'expiration', 'ui'}
# Test obligations for mechanics already implemented/approved, not RPG rules.
TEMPORARY_ACTIONS = {'velocidade', 'forca-arcana', 'frenesi', 'provocacao', 'marca-rubra',
    'sangue-defensivo', 'forma-da-noite', 'toque-sombrio', 'aterrorizar', 'clonagem',
    'reflexos', 'teia', 'escuridao', 'levitacao', 'dorn_guard', 'dorn_vanguard'}


def _refresh_certification(report):
    gaps = []
    counts = {}
    for actor, character in report['characters'].items():
        actions = []
        for entry in character['entries']:
            if entry['origin'] not in {'attack', 'ability'}:
                continue
            if entry['origin'] == 'ability' and not entry.get('active', True):
                continue
            if not entry.get('visible_on_sheet',True):
                continue
            required = {'execution', 'persistence', 'idempotency', 'ui'}
            if entry['origin'] == 'attack' or entry.get('requires_target'):
                required.add('range')
            if (entry.get('uses') or {}).get('resource_key'):
                required.add('cost')
            if entry['key'].split(':', 1)[1] in TEMPORARY_ACTIONS or entry['key'].startswith('ability:hemomancia-'):
                required.add('expiration')
            proven = set(entry.get('verified_checks') or []) & VERIFICATION_CHECKS
            missing = sorted(required - proven)
            certified = not missing and entry['status'] == 'PASS'
            entry.update(required_checks=sorted(required), missing_checks=missing, certified=certified)
            actions.append(entry)
            if not certified:
                gaps.append({'actor': actor, 'key': entry['key'], 'name': entry['name'],
                             'status': entry['status'], 'missing_checks': missing})
        counts[actor] = {'actions': len(actions), 'certified': sum(a['certified'] for a in actions),
                        'assisted': sum(e['status'] == 'ASSISTED' for e in character['entries']),
                        'rule_blocked': sum(a['status'] == 'RULE_BLOCKED' for a in actions)}
    ui = report.get('ui_smoke') or {}
    failed = bool(report['scenario_counts'].get('FAIL')) or ui.get('status') == 'FAIL'
    full_party = set(report['characters']) == {'vezemir', 'morthak', 'raziel', 'dorn7'}
    ready = full_party and not gaps and not failed and ui.get('status') == 'PASS' and all(c['actions'] for c in counts.values())
    report['certification'] = {**report.get('certification', {}), 'contract_version': 1,
        'ready': ready, 'status': 'FAILED' if failed else 'READY' if ready else 'INCOMPLETE',
        'characters': counts, 'gaps': gaps,
        'scope': 'Ações ativas das quatro fichas e cenários explicitamente comprovados; passivas assistidas não são automação.',
        'real_table_validation': 'INCONCLUSIVE'}
    report['all_actions_certified'] = ready and all(character['entries'] and all(
        entry['status'] == 'PASS' for entry in character['entries']) for character in report['characters'].values())


def attach_ui_evidence(report, ui):
    """Only explicit, successful per-action UI attestations count; layout is not execution."""
    ui = {**{k: ui[k] for k in ('status', 'reason', 'suite', 'physical_actions', 'grid_actions') if k in ui},
          'checks': [{**{k: check[k] for k in ('script', 'status', 'duration_seconds') if k in check},
              'action_coverage': [{'actor': proof.get('actor'), 'key': proof.get('key'),
                                  'verified_checks': ['ui'] if 'ui' in (proof.get('verified_checks') or []) else []}
                                 for proof in check.get('action_coverage') or [] if isinstance(proof, dict)]}
                     for check in ui.get('checks') or []]}
    report['ui_smoke'] = ui
    if ui.get('status') == 'PASS':
        for check in ui.get('checks') or []:
            if check.get('status') != 'PASS':
                continue
            for proof in check.get('action_coverage') or []:
                if not isinstance(proof, dict) or 'ui' not in (proof.get('verified_checks') or []):
                    continue
                character = report['characters'].get(proof.get('actor'))
                if character is None:
                    continue
                for entry in character['entries']:
                    if entry['key'] == proof.get('key'):
                        # UI proof cannot assert backend costs/lifecycle or inject extra fields.
                        entry['verified_checks'] = sorted(set(entry.get('verified_checks') or []) | {'ui'})
    _refresh_certification(report)
    return report


def _entry(key, name, origin, **metadata):
    return {'key': key, 'name': name, 'origin': origin, **metadata}


def sheet_entries(sheet):
    """Explicit allowlist; never copy private notes or the complete character DTO."""
    definition = sheet['definition']
    entries = []
    for attack in definition.get('attacks', []):
        entries.append(_entry('attack:' + attack['id'], attack.get('name') or attack['id'], 'attack',
                              damage=attack.get('damage'), attack_bonus=attack.get('attack_bonus')))
    for ability in audit_abilities(definition):
        if ability.get('hidden'):
            continue
        entries.append(_entry('ability:' + ability['id'], ability.get('name') or ability['id'], 'ability',
            active=ability.get('active', True), blocked=bool(ability.get('blocked')),
            kind=ability.get('kind'), source=ability.get('source'),
            mechanics_status=ability.get('mechanics_status'), uses=ability.get('uses') or {},
            requires_target=bool(ability.get('requires_target')),visible_on_sheet=ability.get('visible_on_sheet',True),
            **{key:ability[key] for key in ('action_revision','damage','range_m','invocation_cost','skill_cost') if key in ability}))
    for resource in sheet.get('state', {}).get('resources', []):
        entries.append(_entry('resource:' + resource['key'], resource.get('label') or resource['key'], 'resource',
                              current=resource.get('current'), maximum=resource.get('maximum')))
    for item in sheet.get('inventory', []):
        entries.append(_entry('item:' + item['item_path'], item.get('item_title') or item['item_path'], 'item',
            quantity=item.get('quantity'), equipped=bool(item.get('equipped')),
            charges_current=item.get('charges_current'), charges_max=item.get('charges_max')))
    return entries


def build_report(sheets, results, *, actors):
    characters = {}
    for actor in actors:
        entries = sheet_entries(sheets[actor])
        for entry in entries:
            keys={entry['key']}
            if entry.get('kind')=='resource':
                resource=(entry.get('uses') or {}).get('resource_key')
                state_keys={r['key'] for r in sheets[actor].get('state',{}).get('resources',[])}
                if resource and resource not in state_keys:
                    resource=resource.replace('-','_')
                if resource: keys.add('resource:'+resource)
            evidence=[]
            for result in results:
                if result['actor']!=actor:
                    continue
                covered=set(result.get('covers',[]))
                # A native attack can prove use of its actual weapon without a
                # guessed name match. This does not certify equip/unequip.
                breakdown=(result.get('result') or {}).get('breakdown',{}) if isinstance(result.get('result'),dict) else {}
                weapon=(breakdown.get('attack') or {}).get('weapon_item_path')
                if weapon: covered.add('item:'+weapon)
                if keys.intersection(covered): evidence.append(result)
            statuses = {r['status'] for r in evidence}
            # A failure must never disappear behind a successful happy-path case.
            if 'FAIL' in statuses:
                status = 'FAIL'
            elif entry.get('blocked'):
                status = 'RULE_BLOCKED'
            elif 'PASS' in statuses:
                status = 'PASS'
            elif 'EXPECTED_BLOCK' in statuses:
                status = 'UNAVAILABLE'
            elif entry['origin'] == 'ability' and not entry.get('active', True):
                status = 'ASSISTED'
            else:
                status = 'PENDING'
            verified = set()
            for result in evidence:
                if result['status'] == 'PASS':
                    verified.update(set(result.get('verified_checks') or []) & VERIFICATION_CHECKS)
            entry.update(status=status, scenarios=[r.get('scenario_id', r.get('action')) for r in evidence],
                         verified_checks=sorted(verified))
            if status in {'PENDING', 'ASSISTED'}:
                entry['reason'] = 'Sem cenário executado; cadastro estruturado não certifica automação.'
            elif status == 'UNAVAILABLE':
                entry['reason'] = '; '.join(r['availability_reason'] for r in evidence if r.get('availability_reason')) or 'Rejeição de pré-requisito comprovada.'
        characters[actor] = {'name': sheets[actor]['definition'].get('name') or actor,
            'level': sheets[actor]['definition'].get('level'), 'entries': entries,
            'counts': dict(Counter(e['status'] for e in entries))}
    selected = [r for r in results if r['actor'] in actors]
    report = {'schema_version': 1, 'kind': 'sheet_test_evidence', 'characters': characters,
        'scenario_counts': dict(Counter(r['status'] for r in selected)),
        'all_actions_certified': bool(characters) and all(character['entries'] for character in characters.values()) and all(e['status'] == 'PASS'
            for character in characters.values() for e in character['entries']),
        'scope': 'Somente os cenários referenciados; não certifica todos os caminhos de uma regra.',
        'scenarios': [{k: r[k] for k in ('actor', 'action', 'scenario_id', 'status', 'covers', 'checks', 'verified_checks', 'availability_reason', 'error', 'commands', 'duration_seconds') if k in r}
                      for r in selected]}
    report['certification'] = {'sheet_fingerprints': {actor: hashlib.sha256(json.dumps({
        'definition': {k: sheets[actor]['definition'].get(k) for k in ('id', 'level', 'attributes', 'defenses', 'attacks')},
        'entries': sheet_entries(sheets[actor])}, sort_keys=True, ensure_ascii=False).encode('utf-8')).hexdigest()
        for actor in actors}}
    _refresh_certification(report)
    return report


def render_report(report):
    labels = {'PASS': 'Funcionou no ensaio', 'FAIL': 'Falhou', 'PENDING': 'Falta ensaio / contrato',
              'ASSISTED': 'Passiva/traço: aplicação não certificada', 'RULE_BLOCKED': 'Regra bloqueada',
              'UNAVAILABLE': 'Indisponível; rejeição comprovada'}
    lines = ['# Teste de ficha completa', '',
        'Cópia isolada. PASS comprova apenas os cenários citados, não automação universal.',
        'D20 físico digitado pelo teste; não houve rolagem humana nem mesa em redes distintas.', '']
    certificate = report.get('certification') or {}
    lines.extend(['Certificação das ações: ' + certificate.get('status', 'INCOMPLETE'),
                  'PASS de cenário não certifica custo, duração ou interface que não foram verificados.', ''])
    for actor, character in report['characters'].items():
        lines.extend([f"## {character['name']} — nível {character['level']}", '',
                      '| Origem | Ação / item / recurso | Resultado | Cenários |', '|---|---|---|---|'])
        for entry in character['entries']:
            cells = (entry['origin'], entry['name']+(' [legado/fora da ficha atual]' if not entry.get('visible_on_sheet',True) else ''), labels[entry['status']], ', '.join(entry['scenarios']) or '—')
            lines.append('| ' + ' | '.join(str(c).replace('|', '/').replace('\n', ' ') for c in cells) + ' |')
        lines.append('')
    lines.extend(['## Lacunas para certificação', '', '| Personagem | Ação | Falta comprovar |', '|---|---|---|'])
    for gap in certificate.get('gaps') or []:
        lines.append('| ' + ' | '.join(str(value).replace('|', '/').replace('\n', ' ') for value in (
            gap['actor'], gap['name'], ', '.join(gap['missing_checks']) or gap['status'])) + ' |')
    lines.extend(['## Cenários executados', ''])
    for scenario in report['scenarios']:
        lines.append(f"- {scenario['actor']} / {scenario.get('action')}: {scenario['status']}" +
                     (f" — {scenario['error']}" if scenario.get('error') else ''))
        if scenario.get('checks'):
            lines.append('  Verificações: ' + ', '.join(scenario['checks']) + '.')
    return '\n'.join(lines) + '\n'
