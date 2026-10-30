"""Bounded components used inside existing native command transactions.

No endpoint, independent receipt, transaction, auth or game-loop is introduced.
"""
import json
import re


def require_definition_revision(payload: dict, contract: dict) -> None:
    if payload.get('definition_revision') is not None and payload['definition_revision'] != contract['revision']:
        raise ValueError('A revisão da definição mudou. Atualize a ação antes de continuar.')


def roll_native_component(spec: dict, roll) -> int:
    """Roll already-resolved, bounded metadata using the native injected RNG."""
    dice = spec.get('dice')
    if not isinstance(dice, str) or not re.fullmatch(r'(?:[1-9]|[1-9][0-9]|100)d(?:4|6|8|10|12|20)', dice):
        raise ValueError('Dado inválido no componente de ação')
    add, multiplier = spec.get('add', 0), spec.get('multiplier', 1)
    if type(add) is not int or not 0 <= add <= 9999 or type(multiplier) is not int or not 1 <= multiplier <= 86400:
        raise ValueError('Componente de dados fora dos limites')
    return (int(roll(dice)['total']) + add) * multiplier


def spend_native_resource(connection, character_id: str, key: str, amount: int, now: str) -> int:
    """Re-read latest state on the caller's transaction; preserve HP and other fields.

    No commit/retry/connection is created here. Existing effect_command owns
    serialization, rollback, receipt, permission, ledger and realtime.
    """
    if not connection.in_transaction:
        raise ValueError('Consumo exige a transação do comando nativo')
    if type(amount) is not int or not 1 <= amount <= 100:
        raise ValueError('Custo de recurso inválido')
    row = connection.execute('SELECT state_json FROM character_states WHERE profile_id=?', (character_id,)).fetchone()
    if not row:
        raise ValueError('Ficha persistida ausente')
    state = json.loads(row[0])
    resource = next((r for r in state.get('resources', []) if r.get('key') == key), None)
    remaining = resource.get('current') if resource else None
    if type(remaining) is not int or remaining < amount:
        raise ValueError('Sem preparação disponível ou recurso insuficiente')
    resource['current'] -= amount
    connection.execute('UPDATE character_states SET state_json=?,version=version+1,updated_at=? WHERE profile_id=?',
                       (json.dumps(state, ensure_ascii=False), now, character_id))
    return resource['current']
