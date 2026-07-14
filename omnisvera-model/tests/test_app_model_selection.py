from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path
from unittest.mock import AsyncMock, patch

ROOT=Path(__file__).resolve().parents[2]
sys.path.insert(0,str(ROOT/"omnisvera-agent"/"backend"))

from app.config import get_settings
from app.ollama_client import chat_with_fallback


class ModelSelectionTests(unittest.TestCase):
    def test_baseline_is_safe_default(self):
        env={"OMNISVERA_MODEL_MODE":"baseline","OMNISVERA_FAST_MODEL":"qwen2:1.5b",
             "OMNISVERA_QUALITY_MODEL":"llama-3.2-omnisvera-3b"}
        with patch.dict(os.environ,env,clear=False):
            settings=get_settings()
        self.assertEqual("baseline",settings.model_mode); self.assertEqual("qwen2:1.5b",settings.ollama_model)

    def test_candidate_is_explicit(self):
        env={"OMNISVERA_MODEL_MODE":"candidate","OMNISVERA_CANDIDATE_MODEL":"candidate:test",
             "OMNISVERA_FAST_MODEL":"qwen2:1.5b"}
        with patch.dict(os.environ,env,clear=False): settings=get_settings()
        self.assertEqual("candidate:test",settings.ollama_model)

    def test_unapproved_production_falls_back_to_baseline(self):
        env={"OMNISVERA_MODEL_MODE":"production","OMNISVERA_PRODUCTION_MODEL":"unapproved:test",
             "OMNISVERA_FAST_MODEL":"qwen2:1.5b"}
        with patch.dict(os.environ,env,clear=False): settings=get_settings()
        self.assertFalse(settings.production_approved); self.assertEqual("qwen2:1.5b",settings.ollama_model)


class ModelFallbackTests(unittest.IsolatedAsyncioTestCase):
    async def test_failed_candidate_retries_baseline(self):
        with patch("app.ollama_client.resolve_ollama_model",new=AsyncMock(return_value="candidate:test")), \
             patch("app.ollama_client.chat_with_ollama",new=AsyncMock(side_effect=["","resposta segura"])) as chat:
            answer,model,used=await chat_with_fallback("http://localhost:11434","candidate:test","qwen2:1.5b",[{"role":"user","content":"teste"}])
        self.assertEqual("resposta segura",answer); self.assertEqual("qwen2:1.5b",model); self.assertTrue(used); self.assertEqual(2,chat.await_count)


if __name__ == "__main__": unittest.main()
