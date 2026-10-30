"""Pure on-hit contracts. Missing source parameters remain pending."""
import re
from .damage_profiles import normalized
from .monster_actions import explicit_damage_dice

_FAMILIES={'blinded':r'cegueir','paralyzed':r'paralis','petrified':r'petrific','poison':r'venen'}
_DURATION=re.compile(r'(\d+\s*d\s*\d+(?:\s*[+-]\s*\d+)?)\s+(turnos?|rodadas?)')


def _attack_indices(attacks,text,pattern):
    # A hair-snake bite is a distinct trigger, never the bow or an unrelated bite.
    if pattern==_FAMILIES['poison'] and 'serpent' in text and 'cabelo' in text:
        return [index for index,attack in enumerate(attacks)
                if 'mordid' in normalized(attack.get('name'))
                and re.search(r'serpent|cabelo',normalized(attack.get('name')))]
    indices=[]
    for index,attack in enumerate(attacks):
        marker=normalized(str(attack.get('damage') or '')+' '+str(attack.get('raw') or ''))
        if re.search(r'\+\s*[^+()]*'+pattern,marker):indices.append(index);continue
        if re.search(pattern,normalized(attack.get('damage'))) and not re.search(r'\d',str(attack.get('damage') or '')):indices.append(index);continue
        name=normalized(attack.get('name'))
        for stem,reference in [('bicad',r'\bbico\b|bicad'),('mordid',r'mordid'),('garr',r'\bgarras?\b'),('ferrao',r'\bferrao\b'),('picad',r'picad')]:
            if stem in name and re.search(reference,text):indices.append(index);break
    return list(dict.fromkeys(indices))


def rider_specs(monster):
    if not isinstance(monster,dict):raise TypeError('monster deve ser um dicionário')
    identity=str(monster.get('id') or '');sources=[];pending=[];on_hit=[]
    for index,ability in enumerate(monster.get('abilities') or []):
        name=str(ability.get('name') or '');description=str(ability.get('description') or '')
        source={'ability_index':index,'name':name,'text':description};sources.append(source)
        text=normalized(description);title=normalized(name);full=title+' '+text
        def reject(reason):pending.append({**source,'reason':reason})
        if re.search(r'\b(?:sono|sonifer|adormec|falsa morte)',full):reject('sono_ou_falsa_morte_pendente');continue
        family=next((kind for kind,pattern in _FAMILIES.items() if re.search(pattern,full)),None)
        if not family or re.search(r'imun|resisten',title):reject('fora_do_corte');continue
        if family=='poison' and re.search(r'\bpor\s+(?:rodada|turno)\b|\ba cada\b',text):reject('veneno_periodico_pendente');continue
        if re.search(r'\b(?:olhar|olhos|gaze|cuspe|baforada|sopro|nuvem|gas)\b',text):reject('ativacao_nao_on_hit');continue
        if re.search(r'\b(?:sono|sonifer|adormec|chance|comeca|atras|adiad|apos|falsa morte)',full):reject('chance_sono_ou_inicio_atrasado');continue
        if re.search(r'\b(?:forca|destreza|constituicao|sabedoria|inteligencia|carisma)\b',text):reject('dreno_atributo_pendente');continue
        if re.search(r'\bnao\s+(?:(?:e capaz de|pode|consegue)\s+)?(?:causa|paralis|petrific|provoca|produz)|\bnunca\b',text):reject('efeito_negado');continue
        saves=re.findall(r'\bjp\s*([dcs])\b',text)
        if len(set(saves))!=1:reject('jp_ausente_ou_ambigua');continue
        indices=_attack_indices(monster.get('attacks') or [],text,_FAMILIES[family])
        if not indices:reject('sem_vinculo_ataque');continue
        duration=_DURATION.search(text);formula=re.sub(r'\s+','',duration[1]) if duration else None
        unit=('turns' if duration[2].startswith('turn') else 'rounds') if duration else None
        damage=None;effect=family;save_effect='negates'
        if family=='poison':
            if re.search(r'\bmorte\b|\bmorrer\b|\bmatar\b|\bcaira mort[oa]\b',text):
                if not duration:reject('veneno_letal_sem_prazo_explicito');continue
                effect='poison_death'
            else:
                damage=explicit_damage_dice(description)
                if not damage:reject('veneno_sem_dano_ou_prazo_explicito');continue
                effect='poison_damage';unit='instant';save_effect='halves' if 'metade' in text else 'negates'
        elif not duration:
            if re.search(r'permanente|ate\s+(?:alguma\s+)?magia|apenas por meios magicos',text):unit='permanent'
            else:reject('duracao_ausente');continue
        races=['elfo'] if re.search(r'\belfos?\s+sao\s+imunes',text) else []
        on_hit.append({'id':f'{identity}:rider:{index}','ability_index':index,'name':name,'description':description,
            'attack_indices':indices,'effect':effect,'save':'JP'+saves[0].upper(),'save_effect':save_effect,
            'duration_formula':formula,'duration_unit':unit,'damage_formula':damage,'immunity_races':races})
    return {'schema_version':1,'monster_id':identity,'on_hit':on_hit,'pending':pending,'sources':sources,
            'coverage':{'has_riders':bool(on_hit),'fully_automated':False}}


def combat_rider_specs(monster):
    """Existing on-hit families plus reviewed complex poison contracts."""
    from .monster_poison_specs import poison_specs,disease_specs
    result=rider_specs(monster);extra=poison_specs(monster);diseases=disease_specs(monster)
    from .monster_parasites import specs as parasite_specs
    result['on_hit'].extend(parasite_specs(monster))
    bound={s['ability_index'] for s in result['on_hit']}
    result['on_hit'].extend({**s,'poison':True} for s in extra['on_hit'] if s['ability_index'] not in bound)
    result['on_hit'].extend(s for s in diseases['on_hit'] if s['ability_index'] not in bound)
    bound.update(s['ability_index'] for s in result['on_hit'])
    result['pending']=[p for p in result['pending'] if p['ability_index'] not in bound]
    disease_gaps={p['ability_index']:p for p in diseases['pending']}
    result['pending']=[disease_gaps.get(p['ability_index'],p) for p in result['pending']]
    result['coverage']['has_riders']=bool(result['on_hit'])
    return result
