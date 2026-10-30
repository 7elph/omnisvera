"""Campaign approval 24/10: base dice only; no proc/bonus multiplication."""
import re
from .dice_rolls import parse_formula,roll_formula

def weapon_critical(attack,inventory):
    path=attack.get('weapon_item_path') or ''
    item=next((i for i in inventory if i.get('item_path')==path),{})
    name=item.get('item_title') or ''
    if name=='Grisalma' or path.replace('\\','/').endswith('/Grisalma.md'):
        return 20,3
    mechanics=item.get('mechanics') or {}
    if mechanics.get('family_schema')==1:
        return int(mechanics.get('critical_threshold',20)),int(mechanics.get('critical_multiplier',2))
    threshold,multiplier=20,2
    # Read only an exact weapon's numeric critical table, never execute item prose.
    if name:
        from .item_catalog import load_item_catalog,_search_key
        entry=next((i for i in load_item_catalog()['items'] if i.get('category','').startswith('arma') and _search_key(i['name'])==_search_key(name)),None)
        if entry:
            text=entry.get('description','')
            match=re.search(r'(?:(19)[/–-]20\s*)?[xX](\d)\b',text)
            if match:threshold,multiplier=(19 if match[1] else 20),int(match[2])
    return threshold,max(2,min(5,multiplier))

def augment_strike(strike,attack,inventory,rng,*,player_attack):
    if not player_attack:return
    formula=parse_formula(attack['damage'])
    if strike['d20']==1:
        rolled=roll_formula(formula.formula,rng)
        strike['fumble_damage']=max(0,int(rolled['total']))
        strike['fumble_rolls']=rolled['individual_results']
        return
    threshold,multiplier=weapon_critical(attack,inventory)
    if strike['result']!='hit' or strike['d20']<threshold:return
    # Bow critical belongs to its existing approved hemomancy passive.
    if isinstance(attack.get('hemomancy'),dict) and attack['hemomancy']['weapon']=='arco':return
    rolls=[]
    for _ in range(multiplier-1):rolls+=roll_formula(formula.dice,rng)['individual_results']
    strike.update(critical=True,critical_multiplier=multiplier,critical_rolls=rolls)
    strike['damage_rolls']+=rolls;strike['damage_total']+=sum(rolls)

