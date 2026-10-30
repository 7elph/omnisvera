import json
from importlib import import_module
from pathlib import Path
from unittest import TestCase
from app.main import app


class AIComponentMapTests(TestCase):
    def test_code_index_references_real_files_native_routes_and_contracts(self):
        root=Path(__file__).resolve().parents[1]
        manifest=json.loads((root/'docs/AI_COMPONENT_MAP.json').read_text(encoding='utf-8'))
        self.assertFalse(manifest['campaign_data']);self.assertEqual('code_component_index',manifest['kind'])
        routes=app.openapi()['paths'];contracts=app.openapi()['components']['schemas'];ids=[]
        for component in manifest['components']:
            ids.append(component['id'])
            for file in component['backend']+component['frontend']:
                with self.subTest(component=component['id'],file=file):self.assertTrue((root/file).is_file(),file)
            for route in component['routes']:
                with self.subTest(component=component['id'],route=route):
                    self.assertIn(route['path'],set(routes));self.assertIn(route['method'].lower(),routes[route['path']])
            for contract in component['contracts']:
                with self.subTest(component=component['id'],contract=contract):self.assertIn(contract,set(contracts))
            for contract in component.get('internal_contracts', []):
                with self.subTest(component=component['id'],internal_contract=contract):
                    from pydantic import BaseModel
                    self.assertTrue(issubclass(getattr(import_module(contract['module']),contract['name']),BaseModel))
        self.assertEqual(len(ids),len(set(ids)));self.assertEqual(12,len(ids))
