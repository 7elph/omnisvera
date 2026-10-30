from __future__ import annotations

import copy
import json
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from unittest.mock import patch

from app import catalog_provenance as provenance
from app.spell_catalog import get_catalog_spell


class CatalogProvenanceTests(unittest.TestCase):
    def setUp(self) -> None:
        provenance.load_catalog_provenance.cache_clear()
        self.addCleanup(provenance.load_catalog_provenance.cache_clear)

    def manifest(self) -> dict:
        return json.loads(provenance.PROVENANCE_PATH.read_text(encoding="utf-8"))

    def assert_invalid(self, payload: dict) -> None:
        with TemporaryDirectory() as temporary:
            path = Path(temporary) / "manifest.json"
            path.write_text(json.dumps(payload), encoding="utf-8")
            with patch.object(provenance, "PROVENANCE_PATH", path):
                provenance.load_catalog_provenance.cache_clear()
                with self.assertRaises(ValueError):
                    provenance.load_catalog_provenance()

    def test_verified_batch_reuses_four_existing_spell_ids_without_approving_execution(self) -> None:
        entries = provenance.list_catalog_provenance()
        self.assertEqual({entry["catalog_id"] for entry in entries}, {
            "arcana-relampago", "arcana-reflexos", "arcana-teia", "arcana-dissipar-magia",
        })
        for entry in entries:
            self.assertEqual(entry["kind"], "spell")
            self.assertIsNotNone(get_catalog_spell(entry["catalog_id"]))
            self.assertEqual(entry["review_state"], "source_verified")
            self.assertIs(entry["execution_approved"], False)
            self.assertEqual(entry["source"]["license"], "CC BY-SA 4.0")

    def test_pages_source_version_and_hash_are_explicit(self) -> None:
        expected = {"arcana-relampago": [82], "arcana-reflexos": [64],
                    "arcana-teia": [65, 66], "arcana-dissipar-magia": [71, 72]}
        for catalog_id, pages in expected.items():
            entry = provenance.get_catalog_provenance("spell", catalog_id)
            self.assertIsNotNone(entry)
            assert entry is not None
            self.assertEqual(entry["physical_pages"], pages)
            self.assertEqual(entry["printed_pages"], pages)
            self.assertEqual(entry["source"]["page_count"], 190)
            self.assertEqual(entry["source"]["version"], "1.0.0 (14/05/2024)")
            self.assertEqual(entry["source"]["sha256"],
                             "c24002d7fdd87af03435b66d065f462a9ce9112bdff9a660d649e4ee63244b51")

    def test_unknown_ids_or_kinds_never_receive_default_approval(self) -> None:
        self.assertIsNone(provenance.get_catalog_provenance("spell", "arcana-nao-existe"))
        self.assertIsNone(provenance.get_catalog_provenance("item", "arcana-reflexos"))
        self.assertEqual(provenance.list_catalog_provenance("item"), [])
        self.assertEqual(len(provenance.list_catalog_provenance("spell")), 4)

    def test_return_values_do_not_mutate_cached_metadata(self) -> None:
        entries = provenance.list_catalog_provenance()
        entries[0]["source"]["license"] = "changed"
        entries[0]["execution_approved"] = True
        entry = provenance.get_catalog_provenance("spell", entries[0]["catalog_id"])
        self.assertEqual(entry["source"]["license"], "CC BY-SA 4.0")
        self.assertIs(entry["execution_approved"], False)

    def test_duplicate_ids_and_missing_native_ids_are_rejected(self) -> None:
        manifest = self.manifest()
        manifest["entries"].append(copy.deepcopy(manifest["entries"][0]))
        self.assert_invalid(manifest)
        manifest = self.manifest()
        manifest["entries"][0]["catalog_id"] = "arcana-not-in-native-catalog"
        self.assert_invalid(manifest)

    def test_invalid_or_unmatched_pages_are_rejected(self) -> None:
        for key, value in (("physical_pages", [0]), ("physical_pages", [191]),
                           ("physical_pages", [True]), ("printed_pages", []),
                           ("printed_pages", [64, 65]), ("physical_pages", [64, 64])):
            with self.subTest(key=key, value=value):
                manifest = self.manifest()
                manifest["entries"][0][key] = value
                self.assert_invalid(manifest)

    def test_incomplete_or_execution_approved_metadata_is_rejected(self) -> None:
        for key, value in (("execution_approved", True), ("execution_approved", None),
                           ("review_state", "approved"), ("source_id", "missing")):
            with self.subTest(key=key):
                manifest = self.manifest()
                manifest["entries"][0][key] = value
                self.assert_invalid(manifest)
        manifest = self.manifest()
        del manifest["entries"][0]["execution_approved"]
        self.assert_invalid(manifest)

    def test_no_absolute_source_paths_or_invalid_hash_are_accepted(self) -> None:
        manifest = self.manifest()
        source = next(iter(manifest["sources"].values()))
        self.assertNotIn(":", source["file_name"])
        self.assertNotIn("/", source["file_name"])
        self.assertNotIn("\\", source["file_name"])
        source["file_name"] = "C:\\private\\source.pdf"
        self.assert_invalid(manifest)
        manifest = self.manifest()
        next(iter(manifest["sources"].values()))["sha256"] = "not-a-hash"
        self.assert_invalid(manifest)


if __name__ == "__main__":
    unittest.main()
