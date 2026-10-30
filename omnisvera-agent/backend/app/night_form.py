"""Native Raziel transformation; normal HP stays stored separately from animal HP.

The Master approved the SRD bat profile for all three forms provisionally.
No extra attacks, swarm power, ability scores or vision rules are inferred.
"""
import copy
import json
IMAGES = {
    'coruja': 'zz_media/ui/icons/uploads/raziel_coruja_969cca62e9.jpg',
    'morcego': 'zz_media/ui/icons/uploads/raziel_morcego_82a3c8733e.jpg',
    'corvo': 'zz_media/ui/icons/uploads/raziel_corvo_ae9c2df01e.jpg',
}


def profile(animal):
    if animal not in IMAGES:raise ValueError('Escolha corvo, coruja ou morcego')
    return {'animal':animal,'current_hp':1,'maximum_hp':1,'temporary_hp':0,
            'armor_class':14,'saving_throw':4,'movement':'9V',
            'source':'SRD Old Dragon 2: Morcego; base provisória aprovada pelo Mestre para as três formas'}


def current_form(state):
    if state.get('animal_form') not in IMAGES:return None
    return state.get('night_form') or profile(state['animal_form'])  # Legacy visual-only state, no GET write.


def start(state, animal):
    if int(state.get('current_hp') or 0)<=0:raise ValueError('Forma da Noite não pode levantar Raziel de 0 PV')
    previous=current_form(state);new=profile(animal)
    if previous:new.update(current_hp=previous['current_hp'],temporary_hp=previous.get('temporary_hp',0))
    state['night_form']=new;state['animal_form']=animal


def end(state):
    state.pop('animal_form',None);state.pop('night_form',None)


def require_humanoid(db, actor_id, action='atacar ou conjurar'):
    if actor_id!='raziel':return
    row=db.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()
    if row and json.loads(row[0]).get('animal_form'):
        raise ValueError(f'Forma da Noite não permite {action}; desative a forma animal')


def change_animal_hp(state, amount):
    form=copy.deepcopy(current_form(state));before=int(form['current_hp'])
    absorbed=min(int(form.get('temporary_hp') or 0),-amount) if amount<0 else 0
    form['temporary_hp']=int(form.get('temporary_hp') or 0)-absorbed;delta=amount+absorbed
    raw=before+delta;after=max(0,min(int(form['maximum_hp']),raw))
    result={'hp_before':before,'hp_after':after,'temporary_hp_absorbed':absorbed,
            'damage_taken':max(0,before-after)}
    if delta<0 and raw<=0:
        overflow=max(0,-raw);normal_before=int(state['current_hp'])
        normal_absorbed=min(int(state.get('temporary_hp') or 0),overflow)
        state['temporary_hp']=int(state.get('temporary_hp') or 0)-normal_absorbed
        state['current_hp']=max(0,normal_before-(overflow-normal_absorbed));end(state)
        result.update(hp_after=state['current_hp'],night_form_returned=True,overflow_damage=overflow,
                      normal_hp_before=normal_before,normal_hp_after=state['current_hp'],
                      temporary_hp_absorbed=absorbed+normal_absorbed,
                      damage_taken=result['damage_taken']+normal_before-state['current_hp'])
    else:state['night_form']=form
    return result


def project(definition, state):
    form=current_form(state)
    if not form:return definition,state
    definition=copy.deepcopy(definition);state=copy.deepcopy(state)
    state.update(normal_current_hp=state['current_hp'],normal_maximum_hp=state['maximum_hp'],
                 current_hp=form['current_hp'],maximum_hp=form['maximum_hp'],
                 temporary_hp=form.get('temporary_hp',0),night_form=form)
    definition['attacks']=[];definition['movement']=form['movement']
    definition['attributes']={};definition['attribute_modifiers']={}
    definition['defenses'].update(armor_class=form['armor_class'],base_armor_class=form['armor_class'],
        unmodified_armor_class=form['armor_class'],armor_modifier=0,armor_modifier_source=None,
        saving_throw=form['saving_throw'],saving_throw_bonus=0,conditional_saving_throw_bonuses={})
    return definition,state

def apply_pin_visuals(connection, tokens):
    if not connection.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='character_states'").fetchone():
        return tokens
    row = connection.execute("SELECT state_json FROM character_states WHERE profile_id='raziel'").fetchone()
    animal = json.loads(row[0]).get('animal_form') if row else None
    image = IMAGES.get(animal)
    if image:
        state=json.loads(row[0]);form=current_form(state)
        for token in tokens:
            if token.get('token_type') == 'character' and token.get('character_id') == 'raziel':
                token['image_path'] = image
                token['current_hp']=form['current_hp'];token['maximum_hp']=form['maximum_hp']
                token['sheet']={**(token.get('sheet') or {}),'night_form':form,'armor_class':form['armor_class']}
    return tokens
