"""Fixed OD1 p.146 equipment contracts, not execution of arbitrary item prose."""
from copy import deepcopy

SOURCE='Old Dragon 1 — Livro Básico Aprimorado, p.146'
LABELS={'strength':'Força','dexterity':'Destreza','constitution':'Constituição',
        'intelligence':'Inteligência','wisdom':'Sabedoria','charisma':'Carisma'}
SPECS={
    'item-magico-coroa-do-dragao':('attribute_bonus','intelligence',2,'Cabeça'),
    'item-magico-cinto-da-forca-do-ogro':('attribute_bonus','strength',2,'Cinto'),
    'item-magico-cinturao-dos-anoes':('attribute_bonus','constitution',2,'Cinto'),
    'item-magico-colar-do-menestrel':('attribute_bonus','charisma',2,'Acessório'),
    'item-magico-luvas-do-acrobata':('attribute_bonus','dexterity',2,'Mãos'),
    'item-magico-manto-da-aguia':('attribute_bonus','wisdom',2,'Acessório'),
    'item-magico-manto-da-confusao':('armor_class_bonus','',2,'Acessório'),
    'item-magico-colar-do-comerciante':('skill_bonus','charisma',3,'Acessório'),
}
SPECS.update({'item-magico-braceletes-de-armadura-'+str(n):('armor_class_bonus','',n,'Acessório') for n in range(1,5)})
_DISPLAY_BOUNDARIES={
    'item-magico-botas-elficas':' Broche-escudo',
    'item-magico-anel-ariete':' Armazenamento de magia:',
    'item-magico-anel-inquisidor':' Invisibilidade:',
}


def normalize_source(item):
    """Repair display boundaries, retaining original catalog text for audit."""
    result=dict(item);boundary=_DISPLAY_BOUNDARIES.get(item.get('id'))
    text=str(item.get('description') or '')
    corrected=text.split(boundary,1)[0] if boundary else text
    if item.get('id')=='item-magico-medalhao-de-adaptacao':
        corrected='Permite ao portador respirar em qualquer ambiente (Old Dragon 1, pp.146–147).'
    if corrected!=text:result.update(description=corrected,source_description=text)
    return result


def readiness(item):
    identity=item['id']
    from .magic_containers import BAG,SPECS as CONTAINERS
    if identity==BAG:
        return {'schema_version':1,'status':'variants_available','activation':'select_variant','coverage':'reference_only',
            'variants':[BAG+'-ordeira',BAG+'-caotica']}
    if identity in CONTAINERS:
        return {'schema_version':1,'status':'native_inventory_container','activation':'inventory_popup',
            'coverage':'item_contents_weight_size_atomic_transfer','measurement_policy':'approved_provisional_family_estimates',
            'blocking_gaps':[],
            'occupancy':'voluntary_native_actors_fictional_air_clock' if identity=='item-magico-buraco-portatil' else None}
    if identity=='item-magico-cinto-da-mudanca-de-sexo':
        return {'schema_version':1,'status':'native_on_equip','activation':'equip_transition','coverage':'permanent_appearance_per_physical_belt'}
    if identity=='item-magico-espada-adamas':
        return {'schema_version':1,'status':'native_on_attack','contract_id':identity,
            'activation':'inventory_weapon_form','coverage':'basic_sword_forms_damage_critical_weight_and_corrosion',
            'blocking_gaps':[]}
    from .equipment_checks import SPECS as CHECKS
    if identity in CHECKS:
        return {'schema_version':1,'status':'native_on_check','activation':'equipment_check',
                'coverage':'percentile_check_only','source':'Old Dragon 1, p.146',
                'chance_percent':CHECKS[identity]['chance'],'unit':CHECKS[identity]['unit']}
    from .magic_passives import BRACERS,SPECS as PASSIVES
    if identity==BRACERS:
        return {'schema_version':1,'status':'variants_available','activation':'select_variant',
                'coverage':'reference_only','variants':[BRACERS+'-'+str(n) for n in range(1,5)]}
    if identity in PASSIVES:
        return {'schema_version':1,'status':'native_while_equipped','contract_id':identity,
                'source':PASSIVES[identity]['source'],'activation':'equip','coverage':PASSIVES[identity]['trait']}
    from .magic_absorption import ID as BROOCH, SOURCE as BROOCH_SOURCE
    if identity==BROOCH:
        return {'schema_version':1,'status':'native_while_equipped','contract_id':identity,
                'source':BROOCH_SOURCE,'activation':'equip','coverage':'magic_missile_lifetime_absorption'}
    from .magic_item_uses import SPECS as ACTIVATIONS
    if identity in ACTIVATIONS:
        from .magic_targeted_items import SPECS as TARGETED
        if identity in TARGETED:
            from .magic_item_rulebook import rules_for
            rule=rules_for(identity)
            return {'schema_version':1,'status':'native_on_use','contract_id':identity,
                'source':rule['source'],'activation':'grid_item_use','coverage':rule['native_adapter'],
                'blocking_gaps':rule['blocking_gaps']}
        from .magic_item_drums import DRUMS
        if identity==DRUMS:
            from .magic_item_rulebook import rules_for
            return {'schema_version':1,'status':'native_on_use','contract_id':identity,
                    'source':rules_for(identity)['source'],'activation':'play_and_stop',
                    'coverage':'fear_grid_save_action_and_retreat_constraints'}
        from .magic_item_combat import RAPINA
        if identity==RAPINA:
            from .magic_item_rulebook import rules_for
            return {'schema_version':1,'status':'native_on_use','contract_id':identity,
                    'source':rules_for(identity)['source'],'activation':'equip_and_use_item',
                    'coverage':'native_attack_reflection_and_timed_armor'}
        return {'schema_version':1,'status':'native_on_use','contract_id':identity,
                'source':SOURCE,'activation':'use_item','coverage':'charges_and_fictional_time'}
    if identity in SPECS:
        return {'schema_version':1,'status':'native_while_equipped','contract_id':identity,
                'source':item.get('source') if identity=='item-magico-colar-do-comerciante' else 'Old Dragon 1, pp.145–147' if identity.startswith('item-magico-braceletes-de-armadura-') else SOURCE,
                'activation':'equip','coverage':'fixed_bonus_only'}
    gaps={
        'item-magico-braceletes-de-armadura':['definir_variante_ca_1_a_4'],
        'item-magico-botas-da-velocidade':['ativacao_e_orcamento_diario_de_5_horas'],
        'item-magico-botas-elficas':['teste_percentual_60_porcento'],
        'item-magico-buraco-portatil':['recipiente_espacial_e_asfixia'],
        'item-magico-caneco-do-beberrao':['tabela_percentual_e_3_usos_diarios'],
        'item-magico-espelho-de-oposicao':['copia_hostil_de_ficha_e_equipamento'],
        'item-magico-espelho-do-teleporte':['dois_destinos_e_palavra_chave'],
        'item-magico-fivela-das-irmas':['fase_diurna_noturna_e_reducao_tipificada'],
        'item-magico-anel-ariete':['cargas_e_dano_no_grid','interacao_com_portas'],
        'item-magico-anel-inquisidor':['deteccao_magica_com_revelacao_controlada'],
        'item-magico-anel-da-conviccao':['interceptar_magia_mental_e_consumir_gema'],
        'item-magico-sacola-magica':['variante_ordeira_caotica_e_recipiente'],
        'item-magico-tapete-voador':['passageiros_e_movimento_por_turno_de_exploracao'],
    }
    from .magic_item_rulebook import rules_for
    from .magic_field_items import CRYSTAL, CRYSTAL_VARIANTS, ITEMS as FIELD_ITEMS
    base = CRYSTAL if identity in CRYSTAL_VARIANTS else identity
    rulebook=rules_for(base)
    if base in FIELD_ITEMS and rulebook and rulebook.get('native_adapter'):
        return {'schema_version':1,'status':'native_field_interaction','contract_id':identity,
                'source':rulebook['source'],'activation':'inventory_popup','coverage':rulebook['native_adapter'],
                'blocking_gaps':rulebook['blocking_gaps']}
    missing=(rulebook or {}).get('blocking_gaps') or gaps.get(identity,['contrato_especifico_a_revisar'])
    return {'schema_version':1,'status':'assisted','blocking_gaps':missing,
            'activation':'assisted','coverage':'not_automated'}



def identity(item):
    if item.get('catalog_id'):return item['catalog_id']
    path=str(item.get('item_path') or '')
    return path.removeprefix('compendium:') if path.startswith('compendium:') else path.split(':',2)[-1] if path.startswith('merchant:') else item.get('id')


def compile_item(item):
    spec=SPECS.get(item.get('id'))
    if not spec:return None
    kind,target,value,slot=spec;rid='catalog:'+item['id']+':fixed-magic'
    source=item.get('source') if item['id']=='item-magico-colar-do-comerciante' else 'Old Dragon 1, pp.145–147' if item['id'].startswith('item-magico-braceletes-de-armadura-') else SOURCE
    rules=[deepcopy(r) for r in item.get('effect_rules') or [] if r.get('id')!=rid]
    rules.append({'id':rid,'trigger':'while_equipped','kind':kind,'target':target,
        'value':value,'stacking':'highest' if item['id'].startswith('item-magico-braceletes-de-armadura-') else 'stack',
        **({'stacking_group':'magic_bracers'} if item['id'].startswith('item-magico-braceletes-de-armadura-') else {}),'condition':'','label':source})
    mechanics={**deepcopy(item.get('mechanics') or {}),'family_schema':1,'family':'magic_equipment',
        'kind':'accessory','magic_contract_schema':1,'magical':True,
        'equipment_slots':[slot],'approved_equipment_slots':[slot],'slot_limit':1,
        'consume_mode':'none','charges_max':0,'recharge':'none','family_gaps':[],
        'source':source,'weight':item.get('peso')}
    if item['id']=='item-magico-colar-do-comerciante' or item['id'].startswith('item-magico-braceletes-de-armadura-'):
        mechanics.update(magic_passive_schema=1,magic_passive_id=item['id'],passive_trait='check_bonus' if kind=='skill_bonus' else 'armor_bonus')
    return {'catalog_id':item['id'],'item_type':'accessory','description':item.get('description') or '',
        'damage_formula':None,'effects':list(item.get('effects') or []),'effect_rules':rules,
        'mechanics':mechanics,'usable':False,'thumbnail':item.get('image_path')}


def attribute_bonuses(inventory):
    bonuses={}
    for item in inventory:
        if not item.get('equipped') or int(item.get('quantity') or 0)<=0:continue
        spec=SPECS.get(identity(item))
        if spec and spec[0]=='attribute_bonus':bonuses[spec[1]]=bonuses.get(spec[1],0)+spec[2]
    return bonuses


def modifier_deltas(attributes,inventory):
    """Only the modifier change, not +2 BA for a +2 attribute score."""
    from .character_play import attribute_modifier
    result={}
    for target,bonus in attribute_bonuses(inventory).items():
        value=attributes.get(target)
        if type(value) is int:result[target]=attribute_modifier(value)-attribute_modifier(value-bonus)
    return result


def validate_equipping(item,attributes):
    if (item.get('mechanics') or {}).get('magic_container_schema'):
        raise ValueError('Recipientes são abertos no inventário; não ocupam um encaixe de equipamento')
    if identity(item)=='item-magico-braceletes-de-armadura':
        raise ValueError('Escolha uma variante concreta dos Braceletes de Armadura (+1 a +4)')
    spec=SPECS.get(identity(item))
    if spec and spec[0]=='attribute_bonus' and type(attributes.get(spec[1])) is not int:
        raise ValueError('Cadastre '+LABELS[spec[1]]+' da ficha antes de equipar este item mágico')
