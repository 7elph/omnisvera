"""Validated metadata, not a rule executor. Native handlers keep transactions/RNG.

Only bounded integer level formulas and an allowlisted native binding are
supported in this pilot. No eval, script, URL, SQL or client-defined mechanics.
"""
from typing import Annotated, Literal, get_args, get_origin
from pydantic import BaseModel, ConfigDict, Field, field_validator

BoundedInt = Annotated[int, Field(strict=True, ge=0, le=9999)]


class Definition(BaseModel):
    model_config = ConfigDict(extra='forbid', strict=True)

    @field_validator('*', mode='before')
    @classmethod
    def strict_literal_types(cls, value, info):
        # Pydantic Literal otherwise accepts True for 1, or False for 0,
        # even on strict models. Definition data must preserve JSON types.
        annotation = cls.model_fields[info.field_name].annotation
        if get_origin(annotation) is Literal:
            allowed_types = {type(item) for item in get_args(annotation)}
            if type(value) not in allowed_types:
                raise ValueError('Tipo inválido para literal do contrato')
        return value


class LevelFormula(Definition):
    base: BoundedInt = 0
    per_level: BoundedInt = 0
    cap: Annotated[int, Field(strict=True, ge=1, le=100)] | None = None

    def resolve(self, level):
        value = self.base + self.per_level * level
        return min(value, self.cap) if self.cap is not None else value


class Executor(Definition):
    binding: Literal['dorn_relampago']


class Targeting(Definition):
    kind: Literal['living']
    min_targets: Literal[1]
    max_targets: Annotated[int, Field(strict=True, ge=1, le=30)]
    unique_by: Literal['entity']
    include_self: Literal[False]  # Pilot preserves origin-pin omission in preview.


class Range(Definition):
    mode: Literal['ranged']
    meters: LevelFormula


class Damage(Definition):
    count: LevelFormula
    sides: Literal[4, 6, 8, 10, 12, 20]
    shared: Literal[True]


class Save(Definition):
    attribute: Literal['dexterity']
    on_success: Literal['half_floor']


class Resolution(Definition):
    damage: Damage
    save: Save


class ResourceCost(Definition):
    type: Literal['resource']
    key: Literal['dorn_relampago']
    amount: Annotated[int, Field(strict=True, ge=1, le=100)]
    recharge: Literal['inn_rest']


class Approval(Definition):
    kind: Literal['campaign']
    reference: Annotated[str, Field(min_length=1, max_length=240)]


class ActionContract(Definition):
    schema_version: Literal[1]
    revision: Annotated[str, Field(pattern=r'^[a-z0-9-]{8,100}$')]
    approval: Approval
    executor: Executor
    targeting: Targeting
    range: Range
    area: Literal['selected_targets']
    duration: Literal['instant']
    action_budget: Literal['native_main_action']
    costs: Annotated[list[ResourceCost], Field(min_length=1, max_length=1)]
    resolution: Resolution


class SelfExecutor(Definition):
    binding: Literal['dorn_reflexos']


class SelfTargeting(Definition):
    kind: Literal['self']
    min_targets: Literal[1]
    max_targets: Literal[1]
    unique_by: Literal['entity']
    include_self: Literal[True]


class SelfRange(Definition):
    mode: Literal['self']
    meters: Literal[0]


class EffectRoll(Definition):
    count: Literal[1]
    sides: Literal[4, 6]
    add: LevelFormula
    multiplier: Annotated[int, Field(strict=True, ge=1, le=86400)]


class MirrorResolution(Definition):
    effect: Literal['mirror_images']
    images: EffectRoll
    lifetime: EffectRoll
    intercept_chance_percent: Literal[50,90]
    intercept_area: Literal[False]


class SelfResourceCost(Definition):
    type: Literal['resource']
    key: Literal['dorn_reflexos']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class MirrorContract(Definition):
    schema_version: Literal[1]
    revision: Annotated[str, Field(pattern=r'^[a-z0-9-]{8,100}$')]
    approval: Approval
    executor: SelfExecutor
    targeting: SelfTargeting
    range: SelfRange
    area: Literal['self']
    duration: Literal['fictional_time']
    action_budget: Literal['native_main_action']
    costs: Annotated[list[SelfResourceCost], Field(min_length=1, max_length=1)]
    resolution: MirrorResolution


class PackTargeting(Definition):
    kind: Literal['living_or_dorn', 'token_anchor', 'active_arcane_effect']
    min_targets: Literal[1]
    max_targets: Literal[1]
    unique_by: Literal['entity', 'effect']
    include_self: Literal[True]


class TouchRange(Definition):
    mode: Literal['touch']
    cells: Literal[1]


class StrengthExecutor(Definition):
    binding: Literal['dorn_forca_arcana']


class StrengthCost(Definition):
    type: Literal['resource']
    key: Literal['dorn_forca_arcana']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class StrengthResolution(Definition):
    effect: Literal['strength_bonus']
    strength_divisor: Literal[5]
    rounding: Literal['floor']
    source_attribute: Literal['original_strength']
    lifetime: EffectRoll


class PackContract(Definition):
    schema_version: Literal[1]
    revision: Annotated[str, Field(pattern=r'^[a-z0-9-]{8,100}$')]
    approval: Approval
    action_budget: Literal['native_main_action']


class StrengthContract(PackContract):
    executor: StrengthExecutor
    targeting: PackTargeting
    range: TouchRange
    area: Literal['selected_target']
    duration: Literal['fictional_time']
    costs: Annotated[list[StrengthCost], Field(min_length=1, max_length=1)]
    resolution: StrengthResolution


class WebExecutor(Definition):
    binding: Literal['dorn_teia']


class WebCost(Definition):
    type: Literal['resource']
    key: Literal['dorn_teia']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class WebDimensions(Definition):
    width_m: Literal[3]
    height_m: Literal[3]
    vertical_m: Literal[6]


class WebPenalties(Definition):
    movement_multiplier: Literal[3]
    armor_class_bonus: Literal[-2]
    dexterity_save_bonus: Literal[-2]


class WebResolution(Definition):
    effect: Literal['web_area']
    dimensions: WebDimensions
    lifetime_seconds: LevelFormula
    penalties: WebPenalties


class WebContract(PackContract):
    executor: WebExecutor
    targeting: PackTargeting
    range: Range
    area: Literal['anchor_rectangle']
    duration: Literal['fictional_time']
    costs: Annotated[list[WebCost], Field(min_length=1, max_length=1)]
    resolution: WebResolution


class DispelExecutor(Definition):
    binding: Literal['dorn_dissipar_magia']


class DispelCost(Definition):
    type: Literal['resource']
    key: Literal['dorn_dissipar_magia']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class DispelCheck(Definition):
    count: Literal[1]
    sides: Literal[20]
    add: LevelFormula
    multiplier: Literal[1]


class DispelDifficulty(Definition):
    base: Literal[5]
    include_spell_circle: Literal[True]
    include_caster_level: Literal[True]


class DispelResolution(Definition):
    effect: Literal['dispel_arcane']
    check: DispelCheck
    difficulty: DispelDifficulty


class DispelContract(PackContract):
    executor: DispelExecutor
    targeting: PackTargeting
    range: Range
    area: Literal['selected_effect']
    duration: Literal['instant']
    costs: Annotated[list[DispelCost], Field(min_length=1, max_length=1)]
    resolution: DispelResolution


class VezemirBuffExecutor(Definition):
    binding: Literal['vezemir_forca_arcana', 'vezemir_velocidade']


class VezemirBuffCost(Definition):
    type: Literal['resource']
    key: Literal['forca_arcana', 'velocidade']
    amount: Literal[1]
    recharge: Literal['inn_rest']


class VezemirStrengthResolution(Definition):
    effect: Literal['strength_bonus']
    strength_divisor: Literal[5]
    minimum_bonus: Literal[1]
    rounding: Literal['floor']
    source_attribute: Literal['effective_strength']
    lifetime: EffectRoll


class VezemirSpeedModifiers(Definition):
    movement_multiplier: Literal[2]
    armor_class_bonus: Literal[2]
    extra_attacks: Literal[1]


class VezemirSpeedResolution(Definition):
    effect: Literal['speed_buff']
    modifiers: VezemirSpeedModifiers
    lifetime: EffectRoll


class VezemirBuffContract(PackContract):
    executor: VezemirBuffExecutor
    targeting: SelfTargeting
    range: SelfRange
    area: Literal['self']
    duration: Literal['rounds']
    action_budget: Literal['native_resource_turn_gate']
    costs: Annotated[list[VezemirBuffCost], Field(min_length=1, max_length=1)]
    resolution: VezemirStrengthResolution | VezemirSpeedResolution


def _effect_roll(model: EffectRoll | DispelCheck, level: int) -> dict:
    add = model.add.resolve(level)
    if not 0 <= add <= 9999:
        raise ValueError('Fórmula fora dos limites do contrato')
    return {'dice': f'{model.count}d{model.sides}', 'add': add,
            'multiplier': model.multiplier}


def resolve_contract(definition: dict, level: int) -> dict:
    if type(level) is not int or not 1 <= level <= 20:
        raise ValueError('Nível inválido para o contrato de ação')
    executor = definition.get('executor') if isinstance(definition, dict) else None
    binding = executor.get('binding') if isinstance(executor, dict) else None
    if binding in {'morthak_clonagem', 'morthak_magia_da_morte'}:
        from .morthak_action_contracts import resolve_morthak_contract
        return resolve_morthak_contract(definition, level)
    if binding == 'raziel_sangue_defensivo':
        from .raziel_action_contracts import resolve_blood_defense_contract
        return resolve_blood_defense_contract(definition, level)
    if binding in {'vezemir_forca_arcana', 'vezemir_velocidade'}:
        model = VezemirBuffContract.model_validate(definition)
        key, effect, sides = (('forca_arcana', 'strength_bonus', 6) if binding == 'vezemir_forca_arcana'
                              else ('velocidade', 'speed_buff', 4))
        if (model.costs[0].key != key or model.resolution.effect != effect
                or model.resolution.lifetime.sides != sides
                or model.resolution.lifetime.multiplier != 1):
            raise ValueError('Definição incompatível com o buff nativo')
        result = model.model_dump()
        result.update(level=level)
        result['resolution']['lifetime'] = _effect_roll(model.resolution.lifetime, level)
        return result
    pack_models = {'dorn_forca_arcana': StrengthContract, 'dorn_teia': WebContract,
                   'dorn_dissipar_magia': DispelContract}
    if binding in pack_models:
        model = pack_models[binding].model_validate(definition)
        expected_kind, expected_unique = {
            'dorn_forca_arcana': ('living_or_dorn', 'entity'),
            'dorn_teia': ('token_anchor', 'entity'),
            'dorn_dissipar_magia': ('active_arcane_effect', 'effect'),
        }[binding]
        if model.targeting.kind != expected_kind or model.targeting.unique_by != expected_unique:
            raise ValueError('Alvo incompatível com executor nativo')
        result = model.model_dump()
        result.update(level=level)
        if binding == 'dorn_forca_arcana':
            result['resolution']['lifetime'] = _effect_roll(model.resolution.lifetime, level)
        else:
            meters = model.range.meters.resolve(level)
            if not 0 < meters <= 9999:
                raise ValueError('Fórmula fora dos limites do contrato')
            result['range']['meters'] = meters
            if binding == 'dorn_teia':
                seconds = model.resolution.lifetime_seconds.resolve(level)
                if not 1 <= seconds <= 86400:
                    raise ValueError('Duração fora dos limites do contrato')
                result['resolution']['lifetime_seconds'] = seconds
            else:
                result['resolution']['check'] = _effect_roll(model.resolution.check, level)
        return result
    if isinstance(executor, dict) and executor.get('binding') == 'dorn_reflexos':
        model = MirrorContract.model_validate(definition)
        result = model.model_dump()
        result.update(level=level)
        result['resolution']['images'] = _effect_roll(model.resolution.images, level)
        result['resolution']['lifetime'] = _effect_roll(model.resolution.lifetime, level)
        return result
    model = ActionContract.model_validate(definition)
    result = model.model_dump()
    meters, count = model.range.meters.resolve(level), model.resolution.damage.count.resolve(level)
    if not 0 < meters <= 9999 or not 1 <= count <= 100:
        raise ValueError('Fórmula fora dos limites do contrato')
    result.update(level=level)
    result['range']['meters'] = meters
    result['resolution']['damage'] = {'formula':f'{count}d{model.resolution.damage.sides}', 'shared':True}
    return result
