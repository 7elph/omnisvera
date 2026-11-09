from __future__ import annotations

from functools import lru_cache
import json
from pathlib import Path
import unicodedata
import re
import math


CATALOG_PATH = Path(__file__).resolve().parent / "data" / "old_dragon_items.json"

_REFERENCE_CATEGORIES={'item-magico-categoria','vara-cetro-tabela','tabela-saque-t9-2','arma-caotica-t9-3','arma-ordeira-t9-4'}
_KIT_NAMES=('Armadura de couro batido','Armadura de couro','Armadura de placas','Armadura acolchoada',
            'Armadura completa','Escudo de madeira','Escudo de aço','Escudo torre','Cota de malha',
            'Pé de cabra','Pá/picareta','Pena/tinta','Pergaminhos','Pederneira','Mochila','Arpéu',
            'Corda','Giz','Odre','Tocha','Vara','Broquel','Tenda')


def is_catalog_reference(item: dict) -> bool:
    """Keep source paragraphs/table fragments inspectable, never sell them as items."""
    name=str(item.get('name') or '').strip().lstrip('–—-*/ ')
    return (item.get('id') in {'item-magico-braceletes-de-armadura','item-magico-sacola-magica'} or item.get('category') in _REFERENCE_CATEGORIES
            or bool(re.match(r'^(?:\d+[.,]?\d*\s*(?:kg|g|PO|PP|PC)|Preço do Kit:|Efeito \d+|T9\s)',name,re.I)))


def item_offer_readiness(item: dict | None, *, price_override_po=None,
                         require_automated_effect: bool = False) -> dict:
    """A sale guard and honest effect inventory; a price/text is not an executor."""
    gaps, warnings = [], []
    if not item:
        return {'commerce_ready': False, 'blocking_gaps': ['item_catalogo_ausente'],
                'warnings': [], 'price_po': None, 'effect_status': 'unknown',
                'automation_status': 'not_certified'}
    if is_catalog_reference(item):
        gaps.append('entrada_de_tabela_nao_concreta')
    if item.get('category') == 'servico-magico':
        gaps.append('servico_nao_e_item_fisico')
    raw_price = price_override_po if price_override_po is not None else item.get('preco_po')
    price = None
    if raw_price is None:
        gaps.append('preco_ausente')
    else:
        try:
            price = float(raw_price)
            if isinstance(raw_price,bool) or not math.isfinite(price) or price < 0:
                raise ValueError('invalid price')
        except (TypeError, ValueError, OverflowError):
            gaps.append('preco_invalido'); price = None
    category = str(item.get('category') or '')
    if (item.get('mechanics') or {}).get('requires_variant'):
        effect_status='variant_template'
        warnings.append('escolha_variante_concreta')
    elif (item.get('mechanics') or {}).get('magic_container_schema')==1:
        effect_status='native_inventory_container'
        warnings.append('recipiente_com_validacao_de_medidas')
    elif (item.get('mechanics') or {}).get('magic_appearance_schema')==1:
        effect_status='native_on_equip'
        warnings.append('efeito_permanente_ao_equipar')
    elif (item.get('mechanics') or {}).get('equipment_check_schema')==1:
        effect_status='native_on_check'
        warnings.append('teste_percentual_nativo')
    elif (item.get('mechanics') or {}).get('magic_activation_schema')==1:
        effect_status='native_on_use'
        warnings.append('efeito_automatico_ao_usar')
    elif (item.get('mechanics') or {}).get('magic_absorption_schema')==1 or (item.get('mechanics') or {}).get('magic_passive_schema')==1:
        effect_status='native_while_equipped'
        warnings.append('efeito_automatico_ao_equipar')
    elif (item.get('mechanics') or {}).get('magic_contract_schema')==1:
        effect_status='native_while_equipped'
        warnings.append('efeito_automatico_ao_equipar')
    elif (item.get('mechanics') or {}).get('magic_readiness', {}).get('status') == 'native_field_interaction':
        effect_status='native_field_interaction'
        if item['mechanics']['magic_readiness'].get('blocking_gaps'):
            warnings.append('efeito_parcial')
    elif category in {'arma-corpo','arma-distancia'} and re.fullmatch(r'\d{1,2}d\d{1,4}(?:[+-]\d+)?', re.sub(r'\s+','',str(item.get('dano') or ''))):
        effect_status = 'weapon_damage_only'
        warnings.append('somente_dano_base_cadastrado')
    elif category in {'protecao','item-classe','servico-magico'} or category.startswith('item-magico') or item.get('usos'):
        effect_status = 'assisted'
        warnings.append('efeito_especial_assistido')
    else:
        effect_status = 'not_applicable'
    if require_automated_effect:
        gaps.append('efeito_automatizado_nao_comprovado')
    if item.get('preco_origem') == 'mesa' and price_override_po is None:
        warnings.append('preco_de_campanha_identificado')
    return {'commerce_ready': not gaps, 'blocking_gaps': gaps, 'warnings': warnings,
            'price_po': price, 'price_origin': 'mestre' if price_override_po is not None else item.get('preco_origem'),
            'effect_status': effect_status, 'automation_status': 'not_certified'}


def require_offerable_item(item: dict | None, *, price_override_po=None) -> dict:
    report = item_offer_readiness(item, price_override_po=price_override_po)
    if not report['commerce_ready']:
        messages = {'item_catalogo_ausente':'Item do compêndio não encontrado',
            'entrada_de_tabela_nao_concreta':'Entrada de referência de tabela; escolha um item concreto',
            'servico_nao_e_item_fisico':'Serviço mágico não é um item físico; cadastre o item concreto ou um serviço',
            'preco_ausente':'O Mestre precisa definir o preço deste item', 'preco_invalido':'Preço inválido'}
        raise ValueError('; '.join(messages[gap] for gap in report['blocking_gaps']))
    return report


def normalize_catalog_item(item: dict) -> dict:
    result=dict(item)
    if item.get('category')=='item-magico':
        from .magic_equipment import normalize_source
        result=normalize_source(result)
        from .magic_item_rulebook import enrich
        result=enrich(result)
    if str(item.get('category','')).startswith('kit-'):
        original=str(item.get('name') or '')
        title=next((n for n in _KIT_NAMES if original==n or original.startswith(n+' ')),None)
        if title:
            result.update(name=title,source_name=original)
            # Only the final table weight; an internal carrying capacity is not its weight.
            match=re.search(r'(\d+(?:[.,]\d+)?\s*kg)(?:\s+\d[\d.,]*\s*P[OCP]?)?\s*$',original,re.I)
            if match and not item.get('peso'):result['peso']=match.group(1)
    result['catalog_entry_kind']='reference' if is_catalog_reference(item) else 'item'
    from .item_families import descriptor
    compiled=descriptor(result)
    if (compiled.get('mechanics') or {}).get('family_schema')==1:
        result.update(mechanics=compiled['mechanics'],effect_rules=compiled['effect_rules'],damage_formula=compiled.get('damage_formula'))
        if result['mechanics'].get('magic_activation_schema')==1:result['usable']=True
    if item.get('category')=='item-magico':
        from .magic_equipment import readiness
        result['mechanics']={**(result.get('mechanics') or {}),'magic_readiness':readiness(result)}
    from .item_dimensions import enrich as enrich_dimensions
    return enrich_dimensions(result)


def _search_key(value: str) -> str:
    return unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii").casefold()


@lru_cache(maxsize=1)
def load_item_catalog() -> dict:
    payload = json.loads(CATALOG_PATH.read_text(encoding="utf-8"))
    items = payload.get("items", [])
    if payload.get("schema_version") != 1 or payload.get("count") != len(items):
        raise RuntimeError("O catálogo de itens está incompleto.")
    from .hp_potions import catalog_entry
    native = [normalize_catalog_item(item) for item in items]
    from .magic_passives import BRACERS,variants
    parent=next((item for item in items if item['id']==BRACERS),None)
    if parent:
        native.extend(normalize_catalog_item(item) for item in variants(parent)
                      if not any(existing['id']==item['id'] for existing in native))
    from .magic_absorption import CATALOG_ENTRY as BROOCH
    from .magic_containers import BAG,variants as container_variants
    bag=next((item for item in items if item['id']==BAG),None)
    if bag:
        native.extend(normalize_catalog_item(item) for item in container_variants(bag)
                      if not any(existing['id']==item['id'] for existing in native))
    from .magic_field_items import CRYSTAL, variants as crystal_variants
    crystal=next((item for item in items if item['id']==CRYSTAL),None)
    if crystal:
        native.extend(normalize_catalog_item(item) for item in crystal_variants(crystal)
                      if not any(existing['id']==item['id'] for existing in native))
    if not any(item['id']==BROOCH['id'] for item in native):
        native.append(normalize_catalog_item(BROOCH))
    from .item_specials import NET, DART
    for addition in (NET, DART):
        if not any(item['id'] == addition['id'] for item in native):
            native.append(normalize_catalog_item(addition))
    from .item_specials import NET, DART
    for addition in (NET, DART):
        if not any(item['id'] == addition['id'] for item in native):
            native.append(normalize_catalog_item(addition))
    campaign = catalog_entry()
    if not any(item['id'] == campaign['id'] for item in native):
        native.append(normalize_catalog_item(campaign))
    return {**payload, 'source_count': len(items), 'count': len(native), 'items': native}


def list_item_catalog(query: str = "", category: str = "") -> dict:
    payload = load_item_catalog()
    query_key = _search_key(query.strip())
    category_key = category.strip().casefold()
    items = [
        item
        for item in payload["items"]
        if (not query_key or query_key in _search_key(f"{item['name']} {item.get('description', '')[:500]}"))
        and (not category_key or category_key == str(item.get("category", "")).casefold())
    ]
    return {
        "catalog": payload["catalog"],
        "count": len(items),
        "total": payload["count"],
        "items": items,
    }


def get_catalog_item(item_id: str) -> dict | None:
    return next((item for item in load_item_catalog()["items"] if item["id"] == item_id), None)
