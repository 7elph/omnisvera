import unittest


class RemainingMagicAuditTests(unittest.TestCase):
 def test_every_requested_item_is_accounted_for_and_partial_effects_are_not_complete(self):
  from app.magic_item_rulebook import remaining_audit
  report=remaining_audit()
  self.assertEqual(report['baseline_count'],24)
  self.assertEqual(len({item['id'] for item in report['items']}),24)
  self.assertEqual(report['counts'],{'implemented':14,'partial':3,'assisted':7})
  for item in report['items']:
   self.assertTrue(item['source']);self.assertTrue(item['parameters'])
   if item['implementation']=='implemented':self.assertFalse(item['blocking_gaps'])
   if item['implementation']=='partial':self.assertTrue(item['blocking_gaps'])

 def test_recovered_deck_has_all_seventeen_source_cards_without_pretending_to_execute_them(self):
  from app.magic_item_rulebook import rules_for
  rule=rules_for('item-magico-baralho-das-maravilhas')
  self.assertEqual(len(rule['parameters']['cards']),17)
  self.assertEqual(len({c['id'] for c in rule['parameters']['cards']}),17)
  self.assertNotIn('complete_card_table',rule['blocking_gaps'])
  self.assertIn('permanent_changes',rule['blocking_gaps'])
  self.assertIsNone(rule['native_adapter'])
