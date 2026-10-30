"""Run the fixed Scene Lab browser smoke on an EXISTING stopped TEMP fixture.

No backup, operational tokens, publication, real-server restart, test-job lease
or proposal execution. Only the server/browser processes created here are stopped.
PASS remains pending explicit screenshot review, not visual/real-table acceptance.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

import httpx

try:
    from .cf01_probe import BACKEND, TOKENS, checked_database, fixture_environment
    from .run_sheet_test import checked_port, stop_owned_server
except ImportError:
    from cf01_probe import BACKEND, TOKENS, checked_database, fixture_environment
    from run_sheet_test import checked_port, stop_owned_server


FRONTEND = BACKEND.parent / "frontend"
QA_MODULES = Path.home() / ".cache/codex-runtimes/codex-primary-runtime/dependencies/node/node_modules"
PENDING_REVIEW = "pending_human_or_agent_image_review"
SCOPE = "isolated_private_scene_lab_ui_only"


def _environment(database: Path, vault: Path, output: Path) -> dict[str, str]:
    # Deliberate OS allowlist: no inherited OMNISVERA/model/provider/tunnel secrets,
    # access profiles, proxy URLs, Python overrides or unrelated service settings.
    env = fixture_environment(database)
    env.update({"OMNISVERA_DB_PATH": str(database), "OMNISVERA_VAULT_PATH": str(vault),
                "OMNISVERA_MASTER_TOKEN": TOKENS["gm"], "OMNISVERA_ACCESS_TOKEN": TOKENS["gm"],
                "OMNISVERA_PLAYER_TOKEN": "cf01-local-generic",
                "OMNISVERA_REBUILD_ON_STARTUP": "false", "OMNISVERA_AUTO_REFRESH_INDEX": "false",
                "OMNISVERA_TRAINING_CAPTURE_MODE": "off", "OMNISVERA_BEHAVIOR_MEMORY_ENABLED": "false",
                "OMNISVERA_SEMANTIC_INDEX_PATH": str(vault / ".local-index/vault.jsonl"),
                "OLLAMA_BASE_URL": "http://127.0.0.1:1",
                "OMNISVERA_SHEET_QA_URL": "http://127.0.0.1:8871",
                "OMNISVERA_QA_EVIDENCE_DIR": str(output / "screenshots"),
                "OMNISVERA_QA_MODULES": str(QA_MODULES)})
    return env


def _read_health(port: int, timeout: float) -> dict:
    response = httpx.get(f"http://127.0.0.1:{port}/health", timeout=timeout, trust_env=False,
                         headers={"X-Omnisvera-Token": TOKENS["gm"]})
    response.raise_for_status()
    return response.json()


def _wait_for_fixture(server, database: Path, vault: Path, port: int) -> None:
    deadline = time.monotonic() + 60
    while True:
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError("Fixture health deadline exceeded")
        if server.poll() is not None:
            raise RuntimeError("Owned fixture child exited before readiness")
        try:
            health = _read_health(port, min(2, remaining))
        except (httpx.HTTPError, ValueError):
            time.sleep(min(.25, max(0, deadline - time.monotonic())))
            continue
        if (not isinstance(health, dict) or health.get("access_mode") != "gm" or health.get("backend") != "ok"
                or not isinstance(health.get("database_path"), str) or not isinstance(health.get("vault_path"), str)):
            raise ValueError("Fixture identity is not confirmed")
        actual_database = checked_database(health["database_path"])
        actual_vault = checked_database(health["vault_path"])
        if actual_database != database or actual_vault != vault:
            raise ValueError("Fixture database/Vault do not match the requested isolated copy")
        if server.poll() is not None:
            raise RuntimeError("Owned fixture child exited during readiness")
        return


def _readable(value) -> str:
    return value.decode("utf-8", errors="replace") if isinstance(value, bytes) else value or ""


def run_scene_lab_visual(database: Path, output_dir: Path, *, port: int = 8871) -> dict:
    if type(port) is not int or port != 8871:
        raise ValueError("Only the dedicated isolated fixture port 8871 is allowed")
    database = checked_database(database)
    vault = checked_database(database.with_suffix(".vault"))
    output = checked_database(output_dir)
    if database.name != "simulation.sqlite3" or not database.is_file() or not vault.is_dir():
        raise ValueError("An existing TEMP simulation.sqlite3 and its isolated .vault are required")
    if output.exists() or output.is_relative_to(vault):
        raise ValueError("Use a new TEMP evidence directory outside the fixture Vault")
    if not (FRONTEND / "dist/index.html").is_file() or not (FRONTEND / "tests/scene-lab-smoke.cjs").is_file():
        raise ValueError("Current frontend build and fixed Scene Lab smoke are required")
    node = shutil.which("node")
    if not node or not (QA_MODULES / "playwright/package.json").is_file():
        raise ValueError("Node and bundled Playwright dependencies are required")
    checked_port(port)  # Never stop an existing listener, even another test fixture.
    output.mkdir(parents=True, exist_ok=False)
    env = _environment(database, vault, output)
    flags = subprocess.CREATE_NO_WINDOW if os.name == "nt" else 0
    result = {"status": "INCONCLUSIVE", "scope": SCOPE, "visual_acceptance": PENDING_REVIEW,
              "real_networks": "INCONCLUSIVE", "proposal_execution": "NOT_IMPLEMENTED_NOT_TESTED",
              "production_modified": False, "checks_count": 0, "screenshots": []}
    server = browser = None
    stdout = stderr = ""
    phase = "fixture_start"
    try:
        with (output / "lab-server.private.log").open("w", encoding="utf-8") as server_log:
            server = subprocess.Popen([sys.executable, str(BACKEND / "scripts/cf01_probe.py"),
                "serve", "--database", str(database), "--port", str(port)], cwd=BACKEND, env=env,
                stdout=server_log, stderr=subprocess.STDOUT, creationflags=flags)
            phase = "fixture_health"
            _wait_for_fixture(server, database, vault, port)
            phase = "browser_smoke"
            browser = subprocess.Popen([node, str(FRONTEND / "tests/scene-lab-smoke.cjs")],
                cwd=FRONTEND, env=env, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                text=True, encoding="utf-8", errors="replace", creationflags=flags)
            stdout, stderr = browser.communicate(timeout=300)
            stdout, stderr = _readable(stdout), _readable(stderr)
            if browser.returncode:
                result.update(status="FAIL", reason="Fixed Scene Lab browser smoke failed")
            else:
                try:
                    payload = json.loads(stdout.rstrip().splitlines()[-1])
                except (ValueError, IndexError):
                    payload = None
                if (not isinstance(payload, dict) or payload.get("status") != "PASS" or payload.get("scope") != SCOPE
                        or payload.get("visual_acceptance") != PENDING_REVIEW):
                    result["reason"] = "Browser exit lacked explicit PASS evidence pending image review"
                else:
                    screenshots = payload.get("screenshots") or []
                    if not isinstance(screenshots, list) or any(not isinstance(path, str)
                            or not checked_database(path).is_relative_to(output) for path in screenshots):
                        raise ValueError("Screenshot evidence path is outside this TEMP run")
                    result.update(status="PASS", checks_count=len(payload.get("checks") or []), screenshots=screenshots)
    except subprocess.TimeoutExpired as error:
        stdout, stderr = _readable(error.stdout), _readable(error.stderr)
        result["reason"] = "Owned browser smoke timed out"
    except (OSError, ValueError, RuntimeError, TimeoutError):
        result["reason"] = "Isolated " + phase + " could not be validated"
    finally:
        for child in (browser, server):
            if child is not None and (child is server or child.poll() is None):
                try:
                    stop_owned_server(child)
                except (OSError, subprocess.TimeoutExpired):
                    result.update(status="INCONCLUSIVE", reason="Owned child cleanup was not confirmed")
        (output / "lab-smoke.private.log").write_text(stdout + "\n" + stderr, encoding="utf-8")
        (output / "scene-lab-visual-result.json").write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--port", type=int, choices=(8871,), default=8871)
    args = parser.parse_args()
    try:
        result = run_scene_lab_visual(args.database, args.output_dir, port=args.port)
    except ValueError:
        result = {"status": "INCONCLUSIVE", "reason": "Scene Lab fixture preflight failed; no existing service was stopped",
                  "visual_acceptance": PENDING_REVIEW, "production_modified": False}
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["status"] == "PASS" else 1 if result["status"] == "FAIL" else 2


if __name__ == "__main__":
    raise SystemExit(main())
