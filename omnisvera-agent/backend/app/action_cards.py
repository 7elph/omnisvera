"""Read-only presentation of already visible actions, never execution or inventory disclosure."""
import re
import math

from .access import sanitize_player_text


def active_effect_icons(effects, load_cards, profiles):
    """Presentation only: caller supplies active effects and visible targets."""
    if not effects:
        return []
    catalogs = {profile: load_cards(profile) for profile in profiles}
    icons = []
    for effect in effects:
        # An area's storage anchor is not a buff/debuff on its caster.
        # Occupants are expanded separately by the authoritative map service.
        if effect.get('web_area'):
            continue
        if effect.get('duration') == 'rounds' and int(effect.get('rounds') or 0) <= 0:
            continue
        if effect.get('remaining_seconds') is not None and effect['remaining_seconds'] <= 0:
            continue
        text = f"{effect.get('label') or ''} {effect.get('source') or ''}"
        matches = [card for cards in catalogs.values() for card in cards
                   if not card.get('hidden') and card.get('name') and re.search(
                       r'(?<!\w)' + re.escape(card['name']) + r'(?!\w)', text, re.IGNORECASE)]
        if not matches and effect.get('hemomancy_kind'):
            from .hemomancy import weapons
            kind=effect['hemomancy_kind']
            weapon=next((w for w in weapons() if w['weapon']=={'bleed':'foice','exposed':'marreta','revenge':'escudo','shield':'escudo'}.get(kind,effect.get('weapon'))),None)
            if weapon:
                source=weapon['skill'] if kind=='bleed' else weapon['passive'] if kind in {'exposed','revenge'} else weapon
                matches=[{'id':'hemomancia-'+weapon['weapon'],'name':source['name'],'description':source.get('description',''),'image_path':'zz_media/ui/icons/uploads/lamina_de_sangue_ea48fc7f8a.jpg'}]
        if effect.get('monster_condition'):
            matches=[{'id':'condition:'+effect['monster_condition'],'name':effect['label'],
                'description':effect.get('condition_description',''),'image_path':None}]
        if not matches:continue
        card = max(matches, key=lambda card: len(card['name']))
        if card.get('id') == 'forma-da-noite' and effect.get('animal'):
            card = attach_action_cards([{'character_id': 'raziel', 'event_kind': 'action',
                'title': f"Forma da Noite: {effect['animal']}"}], lambda _: [card])[0]['action_cards'][0]
        remaining=effect.get('turns_remaining',effect.get('remaining_turns'))
        unit=effect.get('source_duration_unit') if effect.get('monster_condition') else None
        if unit in {'turns','rounds'} and effect.get('remaining_seconds') is not None:
            remaining=math.ceil(effect['remaining_seconds']/(600 if unit=='turns' else 10))
        icons.append({'effect_id': effect['id'], 'target_type': effect['target_type'],
                      'target_id': effect['target_id'], 'duration': effect['duration'],
                      'rounds': effect.get('rounds'), 'turns_remaining': remaining,
                      **({'duration_unit':unit} if unit else {}),
                      'remaining_seconds': effect.get('remaining_seconds'),
                      'card': {'id': str(card.get('id') or card['name']), 'name': card['name'],
                               'description': sanitize_player_text(str(card.get('description') or '')),
                               'image_path': card.get('image_path')}})
    return icons


def attach_action_cards(entries, load_cards):
    cache = {}
    result = []
    for entry in entries:
        entry = dict(entry)
        if entry.get('event_kind') not in {'action', 'roll'}:
            result.append(entry)
            continue
        character = entry.get('character_id')
        if character not in cache:
            cache[character] = load_cards(character) if character else []
        title = str(entry.get('title') or '')
        detail = entry.get('detail') or {}
        identity = detail.get('ability_id') or detail.get('attack_id') or detail.get('technique')
        paths = {e.get('item_path') for e in (detail.get('breakdown') or {}).get('equipment', []) if isinstance(e, dict) and e.get('role') == 'weapon'}
        if detail.get('item_path'):
            paths.add(detail['item_path'])
        source_names = {'vampire_power': 'Regeneração Vampírica', 'construct_repair': 'Reparo'}
        source_name = source_names.get(entry.get('source_type'))
        matches = []
        # Longest names first prevents a short power name matching another card.
        occupied = []
        for card in sorted(cache[character], key=lambda c: len(c.get('name') or ''), reverse=True):
            name = str(card.get('name') or '')
            if not name or card.get('hidden'):
                continue
            pattern = re.compile(r'(?<!\w)' + re.escape(name) + r'(?!\w)', re.IGNORECASE)
            found = pattern.search(title)
            if not (identity == card.get('id') or card.get('id') in paths or source_name == name or found):
                continue
            if found and any(found.start() < end and found.end() > start for start, end in occupied):
                continue
            if found:
                occupied.append(found.span())
            # Explicit allowlist: no resources, inventory notes, GM fields or mechanics.
            matches.append({'id': str(card.get('id') or name), 'name': name,
                            'description': sanitize_player_text(str(card.get('description') or '')),
                            'image_path': card.get('image_path') or None})
        if matches:
            night_images = {'coruja': 'raziel_coruja_969cca62e9.jpg', 'morcego': 'raziel_morcego_82a3c8733e.jpg', 'corvo': 'raziel_corvo_ae9c2df01e.jpg'}
            for card in matches:
                if card['id'] == 'forma-da-noite':
                    animal = next((key for key in night_images if re.search(r'\b' + key + r'\b', title, re.IGNORECASE)), None)
                    if animal or not card['image_path']:
                        card['image_path'] = 'zz_media/ui/icons/uploads/' + night_images[animal or 'corvo']
                if card['name'] == 'Malha Rúnica' and not card['image_path']:
                    card['image_path'] = 'zz_media/ui/icons/uploads/malha_runica_05ad221463.jpg'
            entry['action_cards'] = matches
            for card in matches:
                title = re.sub(r'(?<!\w)' + re.escape(card['name']) + r'(?!\w)', lambda _: card['name'], title, flags=re.IGNORECASE)
            entry['title'] = title
        result.append(entry)
    return result
