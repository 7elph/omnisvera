import unittest
from audit_session06 import resource_conflicts


class ResourceAuditTests(unittest.TestCase):
    def test_distinct_keys(self):
        self.assertEqual([], resource_conflicts([{'key': 'blood', 'current': 4}, {'key': 'magic', 'current': 1}]))

    def test_conflicting_duplicate_is_not_silently_healed(self):
        items = [{'key': 'blood', 'current': 4}, {'key': 'blood', 'current': 5}]
        self.assertEqual([4, 5], resource_conflicts(items)[0]['values'])
        self.assertEqual(4, items[0]['current'])

    def test_identical_duplicate_still_reported(self):
        self.assertEqual(1, len(resource_conflicts([{'key': 'blood', 'current': 5}] * 2)))


if __name__ == '__main__':
    unittest.main()
