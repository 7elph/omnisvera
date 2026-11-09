"""Reviewed source parameters and gaps; classification never executes prose."""
import json
from copy import deepcopy
from functools import lru_cache
from pathlib import Path

@lru_cache(maxsize=1)
def _load():
    raw=json.loads((Path(__file__).parent/'data/magic_item_rulebook.json').read_text(encoding='utf-8'))
    if raw.get('schema_version')!=1:raise ValueError('Versão do catálogo de regras mágicas inválida')
    return raw

def rules_for(identity):
    value=_load()['items'].get(identity)
    return deepcopy(value) if value else None

def enrich(item):
    result=dict(item);rulebook=rules_for(item.get('id'))
    if not rulebook:return result
    result['source_rulebook']={'schema_version':1,**rulebook}
    recovered=rulebook.get('recovered_description')
    if recovered:
        result.setdefault('source_description',item.get('description',''))
        result['description']=recovered
        result['source_recovery']={**_load()['attribution'],'page':rulebook['source']}
    return result


def remaining_audit():
    """Stable baseline: all 24 requested entries, including partial executions."""
    previous={'item-magico-botas-elficas','item-magico-manto-da-aranha',
              'item-magico-armadura-leve-da-rapina','item-magico-tambores-do-panico'}
    from .item_catalog import load_item_catalog
    catalog={item['id']:item for item in load_item_catalog()['items']}
    entries=[]
    for key,rule in _load()['items'].items():
        if key in previous:continue
        item=catalog[key]
        gaps=rule['blocking_gaps']
        state='assisted' if not rule.get('native_adapter') else 'partial' if gaps else 'implemented'
        entries.append({'id':key,'name':item['name'],'family':rule['family'],
            'implementation':state,'native_adapter':rule.get('native_adapter'),
            'blocking_gaps':list(gaps),'source':rule['source'],'parameters':deepcopy(rule['parameters']),
            'campaign_decision':rule.get('campaign_decision'),
            'campaign_rule_status':rule.get('campaign_rule_status'),
            'verification':'separate_isolated_report_required'})
    return {'schema_version':1,'baseline_count':len(entries),
        'counts':{state:sum(i['implementation']==state for i in entries) for state in ('implemented','partial','assisted')},
        'items':entries,'runtime_activation':'not_implied_by_source_audit'}
