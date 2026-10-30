"""Direct CLI and MCP must resolve the same trusted backend modules."""
import os
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory
from unittest import TestCase


class SheetRuntimeImportTests(TestCase):
    def test_direct_runner_can_load_audit_and_catalog_media_from_an_unrelated_cwd(self):
        backend=Path(__file__).resolve().parent
        code="import sys;sys.path.insert(0,sys.argv[1]);import all_actions_simulation;import run_sheet_test;from sheet_rehearsal import build_report;from app.character_play import load_session_abilities;assert callable(build_report);assert callable(load_session_abilities);print('IMPORTS_OK')"
        env={key:value for key,value in os.environ.items() if key.casefold() in
             {'systemroot','windir','comspec','path','temp','tmp','pathext','localappdata','appdata'}}
        with TemporaryDirectory() as folder:
            result=subprocess.run([sys.executable,'-c',code,str(backend/'scripts')],cwd=folder,
                env=env,capture_output=True,text=True,timeout=30)
        self.assertEqual(0,result.returncode,result.stderr)
        self.assertEqual('IMPORTS_OK',result.stdout.strip())
