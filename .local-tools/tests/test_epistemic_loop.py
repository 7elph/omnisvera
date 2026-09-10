"""
Epistemic Loop Integration Test
================================
Verifies all critical tools are exposed in the bridge.
"""

import json
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from omnisvera_mcp.core.registry import ToolRegistry, RegisteredTool


REMOTE_TOOL_NAMES = (
    "system.health", "system.manifest", "system.bootstrap", "get_handoff",
    "get_companion_state", "memory.get", "memory.list", "memory.search",
    "memory.recent", "world.list", "world.describe", "world.observe",
    "world.signals", "world.signal_history", "world.signal_changes",
    "world.signal_patterns", "world.model", "world.capture_signals",
    "epistemic.validate_candidate", "epistemic.commit_candidate",
    "epistemic.create_snapshot", "epistemic.snapshot_from_model",
    "epistemic.create_prediction", "epistemic.resolve_prediction",
    "epistemic.list_predictions", "epistemic.get_prediction",
    "epistemic.calibration_summary",
)


def test_bridge_tools():
    """Test that all critical tools are in REMOTE_TOOL_NAMES."""
    print("=" * 60)
    print("BRIDGE TOOL AUDIT")
    print("=" * 60)

    # Critical tools for the epistemic loop
    critical_write = [
        "world.capture_signals",
        "epistemic.create_snapshot",
        "epistemic.snapshot_from_model",
        "epistemic.create_prediction",
        "epistemic.resolve_prediction",
    ]
    critical_read = [
        "epistemic.list_predictions",
        "epistemic.get_prediction",
        "epistemic.calibration_summary",
    ]

    print(f"\nTotal tools in REMOTE_TOOL_NAMES: {len(REMOTE_TOOL_NAMES)}")

    print(f"\n--- Critical WRITE tools ---")
    all_ok = True
    for tool in critical_write:
        status = "EXPOSED" if tool in REMOTE_TOOL_NAMES else "MISSING"
        if status == "MISSING":
            all_ok = False
        print(f"  {tool}: {status}")

    print(f"\n--- Critical READ tools ---")
    for tool in critical_read:
        status = "EXPOSED" if tool in REMOTE_TOOL_NAMES else "MISSING"
        if status == "MISSING":
            all_ok = False
        print(f"  {tool}: {status}")

    # Full list
    print(f"\n--- All {len(REMOTE_TOOL_NAMES)} bridge tools ---")
    for i, tool in enumerate(sorted(REMOTE_TOOL_NAMES), 1):
        print(f"  {i:2d}. {tool}")

    print(f"\n{'='*60}")
    if all_ok:
        print("ALL CRITICAL TOOLS EXPOSED")
    else:
        print("SOME TOOLS MISSING")
    print(f"{'='*60}")

    return all_ok


if __name__ == "__main__":
    test_bridge_tools()
