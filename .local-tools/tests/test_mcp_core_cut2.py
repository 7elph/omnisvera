from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

import assistant_bridge  # noqa: E402
import mcp_server  # noqa: E402
from omnisvera_mcp.adapters import VaultAdapter  # noqa: E402
from omnisvera_mcp.search import (  # noqa: E402
    LexicalIndex,
    OllamaSemanticBackend,
    SearchCoordinator,
    SearchHit,
    SemanticState,
)


class OfflineSemantic:
    def state(self, *, dirty_count: int) -> SemanticState:
        return SemanticState(False, "unavailable", None, "offline in test")

    def refresh_dirty(self, documents, deleted_paths):
        raise AssertionError("offline semantic backend must not refresh")

    def search(self, query: str, limit: int):
        raise AssertionError("offline semantic backend must not search")


class RecordingSemantic:
    def __init__(self) -> None:
        self.refreshed: list[tuple[set[str], set[str]]] = []

    def state(self, *, dirty_count: int) -> SemanticState:
        return SemanticState(True, "dirty" if dirty_count else "fresh", None)

    def refresh_dirty(self, documents, deleted_paths):
        self.refreshed.append((set(documents), set(deleted_paths)))
        return True

    def search(self, query: str, limit: int):
        return [
            SearchHit(
                path="semantic.md",
                text="resultado semântico controlado",
                score=0.75,
                modes=("semantic",),
            )
        ][:limit]


class TemporarySearchCase(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.index_path = self.root / ".local-index" / "lexical-v1.json"
        self.semantic_path = self.root / ".local-index" / "vault.jsonl"
        self.vault = VaultAdapter(self.root, python_executable=Path(sys.executable))

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def write_note(self, relative_path: str, text: str) -> Path:
        path = self.root / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def make_index(self) -> LexicalIndex:
        return LexicalIndex(
            self.vault,
            self.index_path,
            semantic_index_path=self.semantic_path,
        )

    def test_exact_title_and_lexical_search_work_without_ollama(self) -> None:
        self.write_note("Territories/Nimalia.md", "# Nimalia\nReino atravessado por rios.")
        self.write_note("Locations/Porto.md", "# Porto\nMercadores e embarcações.")
        coordinator = SearchCoordinator(self.make_index(), OfflineSemantic())

        exact = coordinator.search("Nimalia", 3)
        lexical = coordinator.search("embarcações", 3)

        self.assertEqual(exact.hits[0].path, "Territories/Nimalia.md")
        self.assertIn("exact", exact.hits[0].modes)
        self.assertEqual(lexical.hits[0].path, "Locations/Porto.md")
        self.assertIn("lexical", lexical.hits[0].modes)
        self.assertFalse(exact.semantic.available)

    def test_changed_note_is_detected_before_the_next_search(self) -> None:
        note = self.write_note("Locations/Porto.md", "# Porto\nTexto inicial.")
        coordinator = SearchCoordinator(self.make_index(), OfflineSemantic())
        coordinator.refresh()
        note.write_text("# Porto\nFarol de safira inconfundível.", encoding="utf-8")

        outcome = coordinator.search("safira", 3)

        self.assertEqual(outcome.refresh.changed, ("Locations/Porto.md",))
        self.assertEqual(outcome.hits[0].path, "Locations/Porto.md")
        self.assertIn("Locations/Porto.md", coordinator.lexical.dirty_documents())

    def test_deleted_and_renamed_notes_update_the_manifest(self) -> None:
        old = self.write_note("Locations/Antigo.md", "# Antigo\nPonte esquecida.")
        index = self.make_index()
        coordinator = SearchCoordinator(index, OfflineSemantic())
        coordinator.refresh()
        new = self.root / "Locations" / "Novo.md"
        old.rename(new)

        outcome = coordinator.search("Ponte esquecida", 5)

        self.assertEqual(outcome.refresh.deleted, ("Locations/Antigo.md",))
        self.assertEqual(outcome.refresh.changed, ("Locations/Novo.md",))
        self.assertEqual(outcome.hits[0].path, "Locations/Novo.md")
        self.assertIn("Locations/Antigo.md", index.semantic_deleted())

    def test_one_changed_file_does_not_rebuild_unchanged_documents(self) -> None:
        first = self.write_note("A.md", "# A\nPrimeiro conteúdo.")
        self.write_note("B.md", "# B\nSegundo conteúdo.")
        index = self.make_index()
        initial = index.refresh()
        state_before = json.loads(self.index_path.read_text(encoding="utf-8"))
        first.write_text("# A\nConteúdo alterado e único.", encoding="utf-8")

        changed = index.refresh()
        state_after = json.loads(self.index_path.read_text(encoding="utf-8"))

        self.assertTrue(initial.rebuilt)
        self.assertFalse(changed.rebuilt)
        self.assertEqual(changed.changed, ("A.md",))
        self.assertEqual(changed.unchanged, 1)
        self.assertEqual(state_before["documents"]["B.md"], state_after["documents"]["B.md"])

    def test_online_semantic_refresh_receives_only_dirty_documents(self) -> None:
        note_a = self.write_note("A.md", "# A\nConteúdo A.")
        note_b = self.write_note("B.md", "# B\nConteúdo B.")
        self.semantic_path.parent.mkdir(parents=True, exist_ok=True)
        self.semantic_path.write_text(
            "\n".join(
                [
                    json.dumps({"path": "A.md", "text": "Conteúdo A.", "embedding": [1.0]}),
                    json.dumps({"path": "B.md", "text": "Conteúdo B.", "embedding": [1.0]}),
                ]
            )
            + "\n",
            encoding="utf-8",
        )
        semantic_mtime = self.semantic_path.stat().st_mtime_ns
        for note in (note_a, note_b):
            note.touch()
        self.semantic_path.touch()
        self.assertGreaterEqual(self.semantic_path.stat().st_mtime_ns, semantic_mtime)
        index = self.make_index()
        index.refresh()
        index.mark_semantic_clean(set(index.dirty_documents()))
        note_a.write_text("# A\nSomente A foi alterado.", encoding="utf-8")
        semantic = RecordingSemantic()
        coordinator = SearchCoordinator(index, semantic)

        outcome = coordinator.search("alterado", 5)

        self.assertEqual(semantic.refreshed, [({"A.md"}, set())])
        self.assertEqual(index.dirty_documents(), {})
        self.assertIn("semantic", outcome.modes_used)

    def test_ollama_backend_replaces_only_dirty_and_deleted_paths(self) -> None:
        self.semantic_path.parent.mkdir(parents=True, exist_ok=True)
        initial_rows = [
            {"path": "A.md", "text": "A antigo", "embedding": [0.0, 1.0]},
            {"path": "B.md", "text": "B preservado", "embedding": [1.0, 0.0]},
            {"path": "Deleted.md", "text": "remover", "embedding": [0.5, 0.5]},
        ]
        self.semantic_path.write_text(
            "".join(json.dumps(row) + "\n" for row in initial_rows),
            encoding="utf-8",
        )

        class FakeClient:
            def __init__(self, **_kwargs) -> None:
                pass

            def embed(self, *, model, input):
                values = input if isinstance(input, list) else [input]
                return {"embeddings": [[1.0, 0.0] for _ in values]}

        backend = OllamaSemanticBackend(self.semantic_path)
        with patch.object(backend, "is_available", return_value=True), patch(
            "ollama.Client", FakeClient
        ):
            refreshed = backend.refresh_dirty(
                {"A.md": ["A atualizado"]},
                {"Deleted.md"},
            )
            hits = backend.search("consulta", 10)

        stored = [
            json.loads(line)
            for line in self.semantic_path.read_text(encoding="utf-8").splitlines()
        ]
        self.assertTrue(refreshed)
        self.assertEqual({row["path"] for row in stored}, {"A.md", "B.md"})
        self.assertEqual(
            next(row for row in stored if row["path"] == "A.md")["text"],
            "A atualizado",
        )
        self.assertEqual({hit.path for hit in hits}, {"A.md", "B.md"})


class CutTwoIntegrationTests(unittest.TestCase):
    def test_all_six_tools_now_run_through_the_registry(self) -> None:
        self.assertEqual(
            mcp_server.CORE_REGISTRY.names(),
            (
                "get_handoff",
                "get_migration_status",
                "semantic_search",
                "assistant_status",
                "create_local_proposal",
                "audit_changed_notes",
            ),
        )

    def test_assistant_status_remains_equivalent_to_the_legacy_implementation(self) -> None:
        self.assertEqual(mcp_server.assistant_status(), assistant_bridge.status())

    def test_real_search_returns_text_while_ollama_is_offline(self) -> None:
        result = mcp_server.semantic_search("Nimalia", 2)
        self.assertIsInstance(result, str)
        self.assertIn("Territories/Nimalia.md", result)

    def test_proposal_source_safety_boundary_is_unchanged(self) -> None:
        with self.assertRaisesRegex(ValueError, "Fonte inválida"):
            mcp_server.create_local_proposal(
                "Não deve chegar ao Ollama",
                ["../outside-the-vault.md"],
            )

    def test_changed_note_audit_still_returns_legacy_json_text(self) -> None:
        result = mcp_server.audit_changed_notes()
        parsed = json.loads(result)
        self.assertIn("arquivos", parsed)
        self.assertIn("yaml_erros", parsed)


if __name__ == "__main__":
    unittest.main()
