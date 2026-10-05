from __future__ import annotations

import unittest

from app.main import _parse_frontmatter_effect_rules, _FRONTMATTER_RULE_KINDS


class FrontmatterEffectRulesTests(unittest.TestCase):
    def test_valid_relic_bonus_accepted(self):
        rules = _parse_frontmatter_effect_rules(
            [{"trigger": "while_equipped", "kind": "attack_bonus", "target": "melee",
              "value": 2, "label": "+2 ataque"}],
            source_path="Items/Grisalma.md",
        )
        self.assertEqual(1, len(rules))
        self.assertEqual("attack_bonus", rules[0]["kind"])
        self.assertEqual("melee", rules[0]["target"])
        self.assertEqual(2, rules[0]["value"])
        self.assertEqual("Items/Grisalma.md", rules[0]["item_path"])

    def test_non_passive_trigger_rejected(self):
        rules = _parse_frontmatter_effect_rules(
            [{"trigger": "on_use", "kind": "heal_hp", "target": "", "value": 4}],
            source_path="Items/Anel.md",
        )
        self.assertEqual([], rules)

    def test_unknown_kind_rejected(self):
        rules = _parse_frontmatter_effect_rules(
            [{"trigger": "while_equipped", "kind": "summon_dragon", "target": "", "value": 99}],
            source_path="Items/X.md",
        )
        self.assertEqual([], rules)

    def test_zero_and_non_list_rejected(self):
        self.assertEqual([], _parse_frontmatter_effect_rules(
            [{"trigger": "while_equipped", "kind": "attack_bonus", "target": "melee", "value": 0}],
            source_path="Items/X.md"))
        self.assertEqual([], _parse_frontmatter_effect_rules("attack_bonus", source_path="Items/X.md"))
        self.assertEqual([], _parse_frontmatter_effect_rules(None, source_path="Items/X.md"))

    def test_allowlist_covers_supported_kinds(self):
        for kind in ("attack_bonus", "damage_bonus", "armor_class_bonus", "attribute_bonus",
                     "maximum_hp_bonus", "movement_bonus", "saving_throw_bonus"):
            self.assertIn(kind, _FRONTMATTER_RULE_KINDS)


if __name__ == "__main__":
    unittest.main()
