"""Cold process with empty runtime, no credentials and no network dependencies."""
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


class CleanInstallationTests(unittest.TestCase):
    def test_cold_core_and_remote_contract(self):
        source = Path(__file__).resolve().parents[1]
        script = r'''
import asyncio, json, sys
from pathlib import Path
from unittest.mock import patch
sys.path.insert(0, sys.argv[1])
from mcp.server.fastmcp import FastMCP
from omnisvera_mcp.server import register_foundation_tools
from omnisvera_mcp.bridge import register_remote_bridge_tools, REMOTE_TOOL_NAMES
from omnisvera_mcp.core.context import CallContext
root = Path(sys.argv[2])
with patch('urllib.request.urlopen', side_effect=OSError('isolated offline fixture')), patch('httpx.Client.request', side_effect=OSError('isolated offline fixture')):
    local = FastMCP('clean-local')
    _, registry, _ = register_foundation_tools(local, root)
    context = CallContext.trusted_local_stdio(client='cold-install-test')
    results = {name: json.loads(registry.invoke(name, context, {})) for name in
               ('system.health', 'system.manifest', 'system.bootstrap', 'world.list')}
    remote = FastMCP('clean-remote')
    register_remote_bridge_tools(remote, registry)
    names = [tool.name for tool in asyncio.run(remote.list_tools())]
    assert len(names) == len(set(names)) == 31
    assert set(names) == set(REMOTE_TOOL_NAMES)
    assert 'epistemic.create_prediction' not in names
    store = registry.services['memory']
    assert store.path.is_relative_to(root)
    assert store.experience_latest('football', 'football.elo', 'v1') is None
    assert store.stats()['counts']['predictions'] == 0
    assert results['system.health']['mcp_core']['status'] == 'healthy'
    assert isinstance(results['world.list'], list)
    assert results['system.bootstrap']['system']
    print(json.dumps({'cold_start': True, 'remote_tools': len(names), 'predictions': 0}))
'''
        # Deliberately exclude operational tokens and provider keys from the child.
        env = {key: value for key, value in os.environ.items()
               if not any(term in key.upper() for term in
                          ('TOKEN', 'SECRET', 'PASSWORD', 'API_KEY', 'OMNISVERA', 'OLLAMA'))}
        with tempfile.TemporaryDirectory() as directory:
            result = subprocess.run([sys.executable, '-c', script, str(source), directory],
                                    cwd=directory, env=env, capture_output=True,
                                    text=True, timeout=45)
            self.assertEqual(result.returncode, 0, result.stderr)
            report = json.loads(result.stdout.splitlines()[-1])
            self.assertEqual(report, {'cold_start': True, 'remote_tools': 31, 'predictions': 0})


if __name__ == '__main__':
    unittest.main()
