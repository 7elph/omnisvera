"""Explicit gaze/gas source contracts plus the Master's three approved choices."""
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path
from .damage_profiles import normalized
from .monster_actions import explicit_damage_dice
from .monster_action_specs import _uses


@lru_cache(maxsize=1)
def approved_rules():
    return json.loads(Path(__file__).with_name('data').joinpath('monster_condition_rules.json').read_text(encoding='utf-8'))


def exposure_specs(monster):
    result=[]
    for index,ability in enumerate(monster.get('abilities') or []):
        name=str(ability.get('name') or '');description=str(ability.get('description') or '')
        text=normalized(description);title=normalized(name)
        if re.search(r'imun|resisten',title):continue
        gaze=bool(re.search(r'\b(?:olhar|olhos)\b',text) and 'petrific' in title+text)
        gas=bool(re.search(r'\bgas\b',text) and re.search(r'baforada|nuvem',title+text))
        if not (gaze or gas):continue
        approved=approved_rules()['overrides'].get(monster.get('id'),{}).get(name,{})
        gaps=[];saves=re.findall(r'\bjp\s*([dcs])\b',text)
        saving='JP'+saves[0].upper() if len(set(saves))==1 else None
        if saving is None:gaps.append('jp_ausente_ou_ambigua')
        if re.search(r'\b(?:nao|nunca)\s+(?:causa|petrifica|produz)',text):gaps.append('efeito_negado')
        radius=approved.get('range_m')
        match=re.search(r'(?:alcanca|alcance(?: de)?|ate)\s+(\d+)\s+metros',text)
        if radius is None and match:radius=int(match[1])
        if radius is None:gaps.append('alcance_ausente')
        permanent=approved.get('duration_unit')=='permanent' or bool(re.search(r'permanente|apenas por meios magicos|ate alguma magia',text))
        petrifying='petrific' in title+text
        if petrifying and not permanent:gaps.append('duracao_petrificacao_ausente')
        formula=None if petrifying else explicit_damage_dice(description)
        if gas and not petrifying and not formula:gaps.append('dano_ausente')
        if not petrifying and 'venen' not in text:gaps.append('tipo_de_gas_pendente')
        uses=_uses(description)
        # No daily cap is invented when the source declares none.
        if not uses['recharge']:uses={'maximum':None,'recharge':'at_will'}
        condition={'id':f"{monster.get('id')}:exposure:{index}",'name':name,'effect':'petrified',
            'duration_unit':'permanent','duration_formula':None,'save':saving,'immunity_races':[],'exposure':'gaze' if gaze else 'gas'} if petrifying else None
        spec={'id':f"{monster.get('id')}:exposure:{index}",'name':name,'ability_index':index,
            'description_full':description,'activation':'gaze' if gaze else 'gas','requires_eye_contact':gaze,
            'reflection_allowed':gaze and bool(re.search(r'proprio olhar.*petrificado',text)),
            'geometry':{'shape':'radius','radius_m':radius,'width_m':None,'depth_m':None,'height_m':None,'declared':radius is not None},
            'targeting_mode':'single' if gaze else 'area','condition':condition,'damage_formula':formula,
            'damage_multiplier':1,'damage_type':'poison' if not petrifying else None,
            'save':saving,'save_effect':'halves' if 'metade' in text else 'negates','uses':uses,
            'gaps':gaps,'execution_status':'assisted' if gaps else 'native'}
        spec['revision']=hashlib.sha256(json.dumps([monster.get('id'),spec,approved_rules()['revision'] if approved else None],sort_keys=True,ensure_ascii=False).encode()).hexdigest()
        result.append(spec)
    return result
