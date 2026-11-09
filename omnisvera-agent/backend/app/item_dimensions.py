"""Approved 02/11/2026 campaign estimates, not measurements from the books.

Only known portable catalog families receive defaults. Dimensions describe one
native inventory unit (including an ammunition pack), not each internal charge.
No persisted inventories, source files, prices or combat rules are changed.
"""
from copy import deepcopy
import re
import unicodedata

FIELDS = ('weight_kg', 'container_entry_cm', 'container_packed_length_cm', 'storage_volume_m3')
METADATA_FIELDS = (*FIELDS, 'physical_metadata')
# weight kg, minimum circular opening cm, packed length cm. Storage volume is
# a conservative square-prism envelope, diameter² * length; not material volume.
PROFILES = {
    'small_weapon': (0.5, 8, 35), 'sword': (2, 12, 110),
    'great_weapon': (7, 25, 160), 'polearm': (7, 40, 260),
    'spear': (3, 12, 250), 'club': (3, 18, 80),
    'axe': (3, 30, 90), 'flexible_weapon': (1, 20, 30),
    'bow': (1.5, 30, 150), 'long_bow': (2, 40, 210),
    'crossbow': (4, 65, 100), 'hand_crossbow': (1.5, 25, 45),
    'blowgun': (0.2, 4, 100), 'arrow_pack': (1.5, 12, 85),
    'bolt_pack': (1, 12, 40), 'dart_pack': (0.1, 8, 25),
    'soft_armor': (7, 28, 45), 'rigid_armor': (15, 60, 90),
    'shield': (5, 65, 85), 'tower_shield': (20, 95, 160),
    'jewelry': (0.1, 5, 8), 'belt': (0.3, 15, 20),
    'boots': (1, 25, 35), 'gloves': (0.2, 15, 20),
    'cloak': (1, 22, 35), 'headwear': (1, 28, 30),
    'book': (1.5, 28, 35), 'mirror': (5, 70, 120),
    'crystal_ball': (2, 20, 20), 'powder': (0.1, 6, 10),
    'flask': (0.5, 10, 20), 'cups': (0.4, 12, 20),
    'deck': (0.2, 10, 14), 'bomb': (0.3, 12, 15),
    'drums': (5, 50, 60), 'carpet': (10, 30, 160),
    'bag': (0.5, 20, 25), 'tools': (1, 20, 35),
    'rope': (3, 25, 30), 'backpack': (2, 28, 45),
    'tent': (4, 28, 65), 'torch': (0.5, 8, 55),
    'pole': (0.5, 5, 300), 'stationery': (0.2, 12, 30),
    'saddle': (12, 60, 75), 'banner': (1, 10, 200),
    'cloth': (0.5, 25, 35), 'gem': (0.1, 5, 8),
    'small_supplies': (0.3, 15, 25),
}


def _key(value):
    return unicodedata.normalize('NFKD', str(value)).encode('ascii', 'ignore').decode().lower()


def _profile(item):
    if item.get('catalog_entry_kind') == 'reference':
        return None
    category = item.get('category')
    name = _key(item.get('name', ''))
    if category in {'arma-corpo', 'arma-distancia'}:
        if 'dardo' in name:
            return 'dart_pack' if any(x in name for x in ('expansao', 'zarabatana', 'alucinante', 'cegante', 'sono', 'assobio', 'ensandecido', 'envenenado', 'fluorescente', 'paralisante')) else 'bolt_pack'
        if 'flecha' in name:
            return 'small_weapon' if 'improvisada' in name else 'arrow_pack'
        if 'besta' in name:
            return 'hand_crossbow' if 'mao' in name else 'crossbow'
        if 'arco' in name or name == 'yumi':
            return 'long_bow' if 'longo' in name or name == 'yumi' else 'bow'
        if 'zarabatana' in name:
            return 'blowgun'
        if any(x in name for x in ('alabarda', 'glaive', 'naginata', 'bisarma')):
            return 'polearm'
        if any(x in name for x in ('lanca', 'tridente', 'bordao', 'cajado', 'azagaia')):
            return 'spear'
        if any(x in name for x in ('chicote', 'garrote', 'corrente', 'nunchaku')):
            return 'flexible_weapon'
        if any(x in name for x in ('montante', 'larga', 'bastarda', 'falcione', 'panabas', 'batalha', 'madu')):
            return 'great_weapon'
        if any(x in name for x in ('machado', 'picareta')):
            return 'axe'
        if any(x in name for x in ('maca', 'martelo', 'porrete', 'mangual')):
            return 'club'
        if any(x in name for x in ('espada', 'katana', 'cimitarra', 'sabre', 'khopesh', 'pinuti', 'pata')):
            return 'sword'
        return 'small_weapon'
    if category == 'item-magico':
        for words, profile in (
            (('espada', 'maca'), 'sword'), (('armadura',), 'soft_armor'),
            (('anel', 'colar', 'medalhao', 'bracelete', 'fivela', 'broche'), 'jewelry'),
            (('cinto', 'cinturao'), 'belt'), (('botas',), 'boots'),
            (('luvas',), 'gloves'), (('manto', 'buraco portatil'), 'cloak'),
            (('coroa', 'elmo', 'oculos'), 'headwear'), (('livro',), 'book'),
            (('espelho',), 'mirror'), (('bola de cristal',), 'crystal_ball'),
            (('po do',), 'powder'), (('caneco', 'copos'), 'cups'),
            (('vaso',), 'flask'), (('baralho',), 'deck'), (('bomba',), 'bomb'),
            (('tambores',), 'drums'), (('tapete',), 'carpet'), (('sacola',), 'bag'),
        ):
            if any(word in name for word in words):
                return profile
        return None
    if item.get('id') == 'campanha-pocao-hp':
        return 'flask'
    if category == 'protecao' or str(category).startswith('kit-') or category == 'item-classe':
        for words, profile in (
            (('escudo torre', 'juggernaut', 'pavise'), 'tower_shield'),
            (('escudo', 'broquel'), 'shield'),
            (('couro', 'acolchoada', 'gibao', 'kamishimo'), 'soft_armor'),
            (('armadura', 'malha', 'yoroi'), 'rigid_armor'),
            (('sela',), 'saddle'), (('corda',), 'rope'), (('mochila',), 'backpack'),
            (('odre', 'cabaca', 'frasco'), 'flask'), (('tenda',), 'tent'),
            (('tocha',), 'torch'), (('vara',), 'pole'),
            (('estandarte', 'flamula', 'sashimono'), 'banner'),
            (('roupa', 'tatame', 'jinmaku'), 'cloth'), (('botas',), 'boots'),
            (('bainha',), 'sword'), (('rubi',), 'gem'),
            (('pena', 'pergaminho', 'giz'), 'stationery'),
            (('pa/picareta', 'pe de cabra', 'arpeu', 'shuko'), 'tools'),
        ):
            if any(word in name for word in words):
                return profile
        return 'rigid_armor' if category == 'protecao' else 'small_supplies'
    return None


def _weight(raw):
    match = re.fullmatch(r'\s*(\d+(?:[.,]\d+)?)\s*(kg|g)\s*', str(raw or ''), re.I)
    if match:
        return float(match[1].replace(',', '.')) / (1000 if match[2].lower() == 'g' else 1)
    return None


def enrich(item):
    profile = _profile(item)
    if profile is None:
        return deepcopy(item)
    result = deepcopy(item)
    mechanics = result.get('mechanics') or {}
    result['mechanics'] = mechanics
    old = mechanics.get('physical_metadata') or {}
    estimated = set(old.get('estimated_fields', []))
    weight, diameter, length = PROFILES[profile]
    values = {'weight_kg': weight, 'container_entry_cm': diameter,
              'container_packed_length_cm': length, 'storage_volume_m3': diameter ** 2 * length / 1_000_000}
    source_weight = next((v for v in (_weight(mechanics.get('weight')), _weight(item.get('peso'))) if v is not None), None)
    for field, value in values.items():
        if mechanics.get(field) is not None:
            continue  # Explicit/invalid values are never silently overridden.
        if field == 'weight_kg' and source_weight is not None:
            mechanics[field] = source_weight
        else:
            mechanics[field] = value
            estimated.add(field)
    if estimated:
        mechanics['physical_metadata'] = {
            'schema_version': 1, 'status': 'provisional_campaign',
            'label': 'Medidas estimadas por família · provisórias da campanha',
            'approval': 'Mestre, 02/11/2026', 'profile': profile,
            'unit': 'inventory_unit', 'estimated_fields': sorted(estimated),
            'volume_model': 'packed_square_prism_envelope',
        }
    return result
