"""Bounded metadata for approved Raziel adapters, never an alternate executor."""
from typing import Annotated, Literal

from pydantic import Field

from .action_contract import Approval, Definition, SelfRange, SelfTargeting


BLOOD_DEFENSE_SOURCE='Sangue Defensivo (Raziel)'


class BloodDefenseExecutor(Definition):
    binding: Literal['raziel_sangue_defensivo']


class BloodDefenseCost(Definition):
    type: Literal['resource']
    key: Literal['reserva_de_sangue']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class BloodDefenseResolution(Definition):
    effect: Literal['armor_class_bonus']
    armor_class_bonus: Literal[2]
    rounds: Literal[1]


class BloodDefenseContract(Definition):
    schema_version: Literal[1]
    revision: Annotated[str,Field(pattern=r'^[a-z0-9-]{8,100}$')]
    approval: Approval
    executor: BloodDefenseExecutor
    targeting: SelfTargeting
    range: SelfRange
    area: Literal['self']
    duration: Literal['rounds']
    action_budget: Literal['native_resource_turn_gate']
    costs: Annotated[list[BloodDefenseCost],Field(min_length=1,max_length=1)]
    resolution: BloodDefenseResolution


def resolve_blood_defense_contract(definition,level):
    if type(level) is not int or not 1<=level<=20:
        raise ValueError('Nível inválido para o contrato de ação')
    return {**BloodDefenseContract.model_validate(definition).model_dump(),'level':level}


def native_blood_defense_contract(definition_revision=None,level=1):
    from .action_library import native_action_contract
    from .action_components import require_definition_revision
    contract=native_action_contract('technique:raziel:sangue-defensivo',level)
    if contract is None:
        raise ValueError('Contrato de Sangue Defensivo indisponível')
    require_definition_revision({'definition_revision':definition_revision},contract)
    return contract


def native_blood_defense_payload(definition_revision=None):
    """Preserve the existing apply fingerprint, transaction and resource turn gate."""
    contract=native_blood_defense_contract(definition_revision)
    resolution=contract['resolution'];cost=contract['costs'][0]
    return {'target_type':'character','target_id':'raziel',
            'label':'Sangue Defensivo — escudo (Raziel)','source':BLOOD_DEFENSE_SOURCE,
            'duration':contract['duration'],'rounds':resolution['rounds'],
            'modifiers':{'armor_class_bonus':resolution['armor_class_bonus']},
            'resource':{'character_id':'raziel','key':cost['key'],'cost':cost['amount']}}
