from __future__ import annotations

import asyncio
import inspect
import sys
import unittest
from pathlib import Path


LOCAL_TOOLS = Path(__file__).resolve().parents[1]
ROOT = LOCAL_TOOLS.parent
if str(LOCAL_TOOLS) not in sys.path:
    sys.path.insert(0, str(LOCAL_TOOLS))

import mcp_server  # noqa: E402
from omnisvera_mcp.core import (  # noqa: E402
    AuthorizationDenied,
    CallContext,
    RegisteredTool,
    ToolRegistry,
)


EXPECTED_SCHEMAS = {
    "get_handoff": {
        "properties": {},
        "title": "get_handoffArguments",
        "type": "object",
    },
    "get_migration_status": {
        "properties": {},
        "title": "get_migration_statusArguments",
        "type": "object",
    },
    "semantic_search": {
        "properties": {
            "limit": {"default": 8, "title": "Limit", "type": "integer"},
            "query": {"title": "Query", "type": "string"},
        },
        "required": ["query"],
        "title": "semantic_searchArguments",
        "type": "object",
    },
    "assistant_status": {
        "properties": {},
        "title": "assistant_statusArguments",
        "type": "object",
    },
    "create_local_proposal": {
        "properties": {
            "source_files": {
                "items": {"type": "string"},
                "title": "Source Files",
                "type": "array",
            },
            "task": {"title": "Task", "type": "string"},
        },
        "required": ["task", "source_files"],
        "title": "create_local_proposalArguments",
        "type": "object",
    },
    "audit_changed_notes": {
        "properties": {},
        "title": "audit_changed_notesArguments",
        "type": "object",
    },
}


class ExistingContractTests(unittest.TestCase):
    def test_all_six_tool_schemas_match_the_captured_baseline(self) -> None:
        tools = asyncio.run(mcp_server.mcp.list_tools())
        schemas = {tool.name: tool.inputSchema for tool in tools}
        self.assertEqual([tool.name for tool in tools[:6]], list(EXPECTED_SCHEMAS))
        self.assertEqual(
            {name: schemas[name] for name in EXPECTED_SCHEMAS},
            EXPECTED_SCHEMAS,
        )

    def test_all_direct_python_signatures_remain_compatible(self) -> None:
        self.assertEqual(str(inspect.signature(mcp_server.get_handoff)), "() -> 'str'")
        self.assertEqual(
            str(inspect.signature(mcp_server.get_migration_status)),
            "() -> 'str'",
        )
        self.assertEqual(
            str(inspect.signature(mcp_server.semantic_search)),
            "(query: 'str', limit: 'int' = 8) -> 'str'",
        )
        self.assertEqual(str(inspect.signature(mcp_server.assistant_status)), "() -> 'str'")
        self.assertEqual(
            str(inspect.signature(mcp_server.create_local_proposal)),
            "(task: 'str', source_files: 'list[str]') -> 'str'",
        )
        self.assertEqual(
            str(inspect.signature(mcp_server.audit_changed_notes)),
            "() -> 'str'",
        )

    def test_migrated_tool_matches_the_previous_file_read(self) -> None:
        expected = (ROOT / "Workflow" / "MIGRATION_LEDGER.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertEqual(mcp_server.get_migration_status(), expected)

    def test_handoff_contract_is_string_but_current_semantics_are_dynamic(self) -> None:
        handoff = mcp_server.get_handoff()
        self.assertIsInstance(handoff, str)
        self.assertIn("handoff dinâmico", handoff)
        self.assertIn("Source:", handoff)
        self.assertIn("Freshness:", handoff)


class RegistryAndPolicyTests(unittest.TestCase):
    def test_call_context_is_not_exposed_in_public_schemas(self) -> None:
        tools = asyncio.run(mcp_server.mcp.list_tools())
        serialized = repr([tool.inputSchema for tool in tools])
        for forbidden in ("actor", "client", "transport", "scopes", "request_id"):
            self.assertNotIn(forbidden, serialized)

    def test_client_arguments_cannot_override_identity(self) -> None:
        registry = ToolRegistry()
        registry.register(
            RegisteredTool(
                name="probe",
                handler=lambda context, arguments: (context, arguments),
                action="read",
                resource="system://probe",
                required_scopes=frozenset(),
            )
        )
        context = CallContext.trusted_local_stdio()
        with self.assertRaisesRegex(ValueError, "transport-controlled"):
            registry.invoke("probe", context, {"actor": "attacker"})

    def test_policy_runs_before_handler(self) -> None:
        handler_ran = False

        def handler(_context, _arguments):
            nonlocal handler_ran
            handler_ran = True
            return "unexpected"

        registry = ToolRegistry()
        registry.register(
            RegisteredTool(
                name="protected",
                handler=handler,
                action="read",
                resource="sage://private",
                required_scopes=frozenset({"sage.memory.read"}),
            )
        )
        untrusted = CallContext(
            actor="guest",
            client="test",
            transport="stdio",
            scopes=frozenset(),
            request_id="test-request",
        )

        with self.assertRaises(AuthorizationDenied):
            registry.invoke("protected", untrusted, {})
        self.assertFalse(handler_ran)

    def test_trusted_local_context_can_invoke_migrated_tool(self) -> None:
        registered = mcp_server.CORE_REGISTRY.get("get_migration_status")
        self.assertEqual(registered.resource, "omnisvera://migration/status")
        self.assertEqual(registered.required_scopes, frozenset({"vault.migration.read"}))
        result = mcp_server.CORE_REGISTRY.invoke(
            "get_migration_status",
            CallContext.trusted_local_stdio(),
            {},
        )
        expected = (ROOT / "Workflow" / "MIGRATION_LEDGER.md").read_text(
            encoding="utf-8-sig"
        )
        self.assertEqual(result, expected)


if __name__ == "__main__":
    unittest.main()
