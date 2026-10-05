"""The rehearsal must never inherit the operational Vault or database."""
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from scripts.cf01_probe import BACKEND, configure


class RehearsalIsolationTests(TestCase):
    def test_configuration_overrides_operational_paths_and_disables_refresh(self):
        with TemporaryDirectory() as root, patch.dict(os.environ, {
            "OMNISVERA_DB_PATH": str(BACKEND / "data" / "operational.sqlite3"),
            "OMNISVERA_VAULT_PATH": str(BACKEND.parent.parent),
            "OMNISVERA_AUTO_REFRESH_INDEX": "true",
        }):
            database = Path(root) / "rehearsal.sqlite3"
            configure(database)
            vault = database.with_suffix(".vault")
            self.assertEqual(str(database.resolve()), os.environ["OMNISVERA_DB_PATH"])
            self.assertEqual(str(vault.resolve()), os.environ["OMNISVERA_VAULT_PATH"])
            self.assertTrue(vault.is_dir())
            self.assertEqual([], list(vault.iterdir()))
            self.assertEqual("false", os.environ["OMNISVERA_AUTO_REFRESH_INDEX"])
            self.assertEqual("false", os.environ["OMNISVERA_REBUILD_ON_STARTUP"])
            self.assertEqual("off", os.environ["OMNISVERA_TRAINING_CAPTURE_MODE"])
            self.assertTrue(Path(os.environ["OMNISVERA_SEMANTIC_INDEX_PATH"]).is_relative_to(vault))
            configure(database)
            self.assertEqual([], list(vault.iterdir()))

    def test_configuration_rejects_operational_database_before_any_write(self):
        with patch.dict(os.environ, {}, clear=True), patch.object(Path, "mkdir") as mkdir:
            with self.assertRaisesRegex(ValueError, "temporary directory"):
                configure(BACKEND / "data" / "operational.sqlite3")
            mkdir.assert_not_called()
            self.assertNotIn("OMNISVERA_DB_PATH", os.environ)
