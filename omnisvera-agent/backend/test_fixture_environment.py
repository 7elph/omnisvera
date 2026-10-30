import json
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch


class FixtureEnvironmentTests(TestCase):
    def test_child_never_inherits_host_python_or_operational_settings(self):
        from scripts.cf01_probe import fixture_environment
        with TemporaryDirectory() as folder, patch.dict(os.environ, {
            'PYTHONHOME':'host-runtime', 'PYTHONPATH':'host-packages',
            'OMNISVERA_MASTER_TOKEN':'PRIVATE', 'OPENCODE_SERVER_PASSWORD':'PRIVATE',
            'HTTP_PROXY':'PRIVATE', '__PYVENV_LAUNCHER__':'host-launcher'}):
            database=Path(folder)/'simulation.sqlite3'
            env=fixture_environment(database)
            self.assertEqual('cf01-local-gm',env['OMNISVERA_MASTER_TOKEN'])
            self.assertEqual(str(database),env['OMNISVERA_DB_PATH'])
            self.assertEqual(str(database.with_suffix('.vault')),env['OMNISVERA_VAULT_PATH'])
            self.assertEqual(str(database.with_suffix('.workshop.sqlite3')), env['OMNISVERA_AI_WORKSHOP_DB'])
            self.assertEqual(str(database.with_suffix('.workshop-config.json')), env['AI_WORKSHOP_CONFIG_FILE'])
            for key in ('PYTHONHOME','PYTHONPATH','OPENCODE_SERVER_PASSWORD','HTTP_PROXY','__PYVENV_LAUNCHER__'):
                self.assertNotIn(key,env)
            self.assertNotIn('PRIVATE',json.dumps(env))
            self.assertEqual('host-runtime',os.environ['PYTHONHOME'])

    def test_operational_path_is_rejected_before_any_spawn(self):
        from scripts.cf01_probe import fixture_environment
        with self.assertRaises(ValueError):fixture_environment(Path(__file__).resolve())
