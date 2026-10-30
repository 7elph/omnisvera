# Test manifest - OMNISVERA Companion

This file is the inventory of test layers and the commands that may be used for
verification. It does not certify the whole Companion.

## Layers

| Layer | Files | Command or entry point | Safety |
| --- | --- | --- | --- |
| Frontend unit | 106 `*.test.cjs` | `cd frontend; npm test` | Local, no server required |
| Frontend smoke | 54 `*-smoke.cjs` | MCP `companion_test_start` with `ui: true`, or `run_sheet_test.py` | TEMP fixture only |
| Frontend visual | 12 `*-visual.cjs` | MCP visual suite or isolated runner | TEMP fixture; inspect screenshots |
| Frontend probe/helpers | 1 probe, 4 helpers | Called by other tests | Local helper code |
| Backend unit/integration | 184 `backend/test_*.py` | `python -m unittest discover -s backend -p "test_*.py"` | Must use isolated DB and `LOCALAPPDATA` |
| Native sheet rehearsal | `backend/scripts/run_sheet_test.py` | `test_sheet.ps1` | TEMP copy of SQLite and vault |
| MCP agent harness | `backend/scripts/companion_test_mcp.py` | `companion-tests` MCP server | TEMP fixture, bounded jobs |

Counts observed on 2026-10-30 after the baseline commit: 177 CJS files under
`frontend/tests` (106 unit, 54 smoke, 12 visual, 4 helpers/other, 1 probe).

## Frontend unit

```powershell
cd frontend
npm test
npx tsc --noEmit
npm run build
```

`npm test` runs every `tests/*.test.cjs` file. Last observed result: 491 pass,
0 fail. Unit tests are not a substitute for browser acceptance.

## Backend isolated suite

```powershell
$run = Join-Path $env:TEMP ("omnisvera-tests-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $run | Out-Null
$env:LOCALAPPDATA = Join-Path $run "localappdata"
$env:OMNISVERA_DB_PATH = Join-Path $run "fixture.sqlite3"
$env:OMNISVERA_AUTO_REFRESH_INDEX = "false"
$env:OMNISVERA_REBUILD_ON_STARTUP = "false"
& ".\.venv-observer\Scripts\python.exe" -m unittest discover -s backend -p "test_*.py"
```

The isolated `LOCALAPPDATA` prevents tests from contending with the live
`workload.lock`. Do not stop another rehearsal or delete its lock.

Last observed result on 2026-10-30: 1.768 tests, 1 skipped, 654 s, exit 0. A
`RESOURCE_BUSY` line can come from a test that exercises workload admission; it
is not a suite failure by itself.

## Native sheet and browser suites

Use `test_sheet.ps1` or the MCP tools. The MCP is the preferred path because it
creates a TEMP fixture, enforces time and process limits and returns structured
evidence.

```json
{
  "request_id": "baseline-audit-001",
  "actors": ["raziel", "morthak", "vezemir", "dorn7"],
  "ui": true
}
```

Relevant focused suites include `full`, `combat`, `lightning`, `hemomancy`,
`vampiric`, `necromancy`, `rest`, `passives`, `summon_turns`, `inventory_summons`,
`item_families`, `friday`, `oct24`, `monster_defaults`, `active_spells`,
`catalog` and `sprite_studio`. See `docs/AI_TEST_TOOLS.md` for scope and limits.

## Script classification

- `*.test.cjs`: isolated unit tests; safe for `npm test`.
- `*-smoke.cjs`: browser or API smoke scenarios; require a running isolated
  fixture and usually Playwright/Edge.
- `*-visual.cjs`: screenshot/layout checks; require explicit visual review.
- `*-probe.cjs`: diagnostic probe, not a certification suite.
- `owned-ui-preload.cjs`, `rest-alerts.cjs`, `shield-near-miss.cjs` and
  `monster-specials-scenarios.cjs`: helper modules.
- 36 CJS files are referenced by the native runner/MCP. The other browser,
  visual and probe scripts are historical or orphaned unless a new runner entry
  explicitly selects them. Do not claim coverage for an unreferenced script.

## Evidence rules

- `COMPLETED/PASS` covers only the selected scenarios.
- `COMPLETED/FAIL` is a real failed test.
- `ERROR/INCONCLUSIVE`, `CANCELLED` and `INTERRUPTED` are not PASS.
- `PENDING`, `ASSISTED`, `RULE_BLOCKED` and `UNAVAILABLE` are not automated.
- API checks do not certify UI; layout checks do not certify backend costs.
- Smoke or visual evidence is valid only for the current fixture fingerprint.
