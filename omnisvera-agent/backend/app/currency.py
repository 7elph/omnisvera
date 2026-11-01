"""Native wallet denominations; campaign rule confirmed by the GM on 2026-10-31.

No balance migration: one platinum remains 100 gold. The divergent Vault note
is intentionally not edited by this code change.
"""
from types import MappingProxyType

CURRENCY_RULE_ID = 'omnisvera-copper-v1-platinum-100-gold'
COIN_FIELDS = ('copper_coins', 'silver_coins', 'coins', 'platinum_coins')
COPPER_PER = MappingProxyType(dict(zip(COIN_FIELDS, (1, 10, 100, 10000))))


def rule_snapshot():
    return {'id': CURRENCY_RULE_ID, 'copper_per': dict(COPPER_PER)}
