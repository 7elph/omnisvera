from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from omnisvera_mcp.adapters.companion import CompanionAdapter


class Response:
    def __enter__(self): return self
    def __exit__(self, *_): return False
    def read(self): return b'{"backend":"ok","ollama_accessible":false}'


class HealthTimeoutTests(unittest.TestCase):
    def test_health_budget_exceeds_companion_ollama_probe_without_retry(self):
        calls = []
        def opener(request, timeout):
            calls.append((request.full_url, timeout))
            if timeout <= 1.5:
                raise TimeoutError("Companion still waiting for optional Ollama")
            return Response()
        adapter = CompanionAdapter(Path.cwd(), token="test-only", opener=opener)
        result = adapter.get_health()
        self.assertEqual(result.status, "healthy")
        self.assertFalse(result.value["ollama_accessible"])
        self.assertEqual(len(calls), 1)
        self.assertEqual(calls[0][1], 3.0)

    def test_other_reads_keep_the_short_timeout(self):
        timeouts = []
        def opener(request, timeout):
            timeouts.append(timeout)
            return Response()
        adapter = CompanionAdapter(Path.cwd(), token="test-only", opener=opener)
        adapter.get_app_state()
        adapter.get_dashboard()
        self.assertEqual(timeouts, [1.5, 1.5, 1.5])

    def test_health_timeout_is_bounded_and_error_does_not_expose_secrets(self):
        calls = []
        def opener(request, timeout):
            calls.append(timeout)
            raise TimeoutError("secret-test-token")
        adapter = CompanionAdapter(Path.cwd(), token="secret-test-token", opener=opener)
        result = adapter.get_health()
        self.assertEqual(result.status, "offline")
        self.assertEqual(result.limitation, "TimeoutError")
        self.assertNotIn("secret-test-token", str(result.as_dict()))
        self.assertEqual(calls, [3.0])


if __name__ == "__main__":
    unittest.main()
