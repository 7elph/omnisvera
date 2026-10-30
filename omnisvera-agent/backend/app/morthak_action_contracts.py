"""Typed metadata for two approved Morthak native adapters, not an executor.

No definitions live here: the existing action catalog owns approved metadata.
The handlers retain permission, transactions, summons, saves, HP and receipts.
"""
from typing import Annotated, Literal

from pydantic import Field

from .action_contract import Definition, PackContract, Range, SelfTargeting


class CloneExecutor(Definition):
    binding: Literal['morthak_clonagem']


class DeathExecutor(Definition):
    binding: Literal['morthak_magia_da_morte']


class CloneResource(Definition):
    type: Literal['resource']
    key: Literal['clonagem']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class CrystalComponent(Definition):
    type: Literal['inventory']
    item_title: Literal['Fragmento de Cristal Arcano']
    amount: Literal[1]
    consumable: Literal[True]


class DeathResource(Definition):
    type: Literal['resource']
    key: Literal['magia_da_morte']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class CurrentHpFraction(Definition):
    type: Literal['current_hp_fraction']
    retained_divisor: Literal[10]
    rounding: Literal['floor']
    ignore_temporary_hp: Literal[True]


class CloneCount(Definition):
    source: Literal['clonagem_circle']
    min_circle: Literal[5]
    max_circle: Literal[9]
    subtract: Literal[3]


class CloneHp(Definition):
    maximum_divisor: Literal[4]
    minimum: Literal[1]
    rounding: Literal['floor']


class CloneResolution(Definition):
    effect: Literal['physical_clones']
    clone_count: CloneCount
    hp: CloneHp
    execution_rounds: Literal[1]
    duration_rounds: Literal[5]
    max_active_groups: Literal[1]
    concentration: Literal[True]
    magical_equipment: Literal[False]
    can_cast: Literal[False]
    can_use_magic_items: Literal[False]
    attacks_per_round: Literal[1]
    disappear_at_zero: Literal[True]


CloneCost = CloneResource | CrystalComponent


class CloneContract(PackContract):
    executor: CloneExecutor
    targeting: SelfTargeting
    range: Range
    area: Literal['spawn_near_caster']
    duration: Literal['rounds']
    costs: Annotated[list[CloneCost], Field(min_length=2, max_length=2)]
    resolution: CloneResolution


class DeathTargeting(Definition):
    kind: Literal['eligible_creatures']
    min_targets: Literal[1]
    max_targets: Literal[12]
    unique_by: Literal['entity']
    include_self: Literal[False]


class DeathVictimLimit(Definition):
    dice: Literal['2d6']


class DeathSave(Definition):
    attribute: Literal['constitution']
    on_success: Literal['negates']


class DeathResolution(Definition):
    effect: Literal['instant_death']
    victim_limit: DeathVictimLimit
    max_hit_dice: Literal[4]
    save: DeathSave
    include_allies: Literal[True]
    order: Literal['distance_then_entity_id']


DeathCost = DeathResource | CurrentHpFraction


class DeathContract(PackContract):
    executor: DeathExecutor
    targeting: DeathTargeting
    range: Range
    area: Literal['nearest_eligible_creatures']
    duration: Literal['instant']
    costs: Annotated[list[DeathCost], Field(min_length=2, max_length=2)]
    resolution: DeathResolution


def resolve_morthak_contract(definition: dict, level: int) -> dict:
    if type(level) is not int or not 1 <= level <= 20:
        raise ValueError('Nível inválido para o contrato de ação')
    executor = definition.get('executor') if isinstance(definition, dict) else None
    binding = executor.get('binding') if isinstance(executor, dict) else None
    if binding == 'morthak_clonagem':
        model = CloneContract.model_validate(definition)
        expected_costs = (CloneResource, CrystalComponent)
    elif binding == 'morthak_magia_da_morte':
        model = DeathContract.model_validate(definition)
        expected_costs = (DeathResource, CurrentHpFraction)
    else:
        raise ValueError('Executor de Morthak não aprovado')
    if tuple(type(cost) for cost in model.costs) != expected_costs:
        raise ValueError('Custos incompatíveis com o executor nativo')
    meters = model.range.meters.resolve(level)
    if not 0 < meters <= 9999:
        raise ValueError('Alcance fora dos limites do contrato')
    result = model.model_dump()
    result['range']['meters'] = meters
    result['level'] = level
    return result


def clone_circle_and_count(contract: dict, value) -> tuple[int, int]:
    """Preserve the existing circle override clamp; character level is not circle."""
    rule = contract['resolution']['clone_count']
    circle = max(rule['min_circle'], min(rule['max_circle'], int(value or rule['min_circle'])))
    return circle, circle - rule['subtract']
