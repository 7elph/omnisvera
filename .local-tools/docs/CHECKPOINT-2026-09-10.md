# Companion + MCP checkpoint — 2026-09-10

This is a preservation checkpoint of the current local implementation, not a
claim that every subsystem is production-ready. Repository: 7elph/omnisvera.
Branch: devin/create-omnisvera-class-standard. No merge to main.

## Code and history

- Companion: `omnisvera-agent/backend`, `frontend`, tests, scripts and docs.
- MCP: `.local-tools/omnisvera_mcp`, HTTP/stdio and Claude connectors, launcher
  scripts, tests, ADRs and technical specifications under `.local-tools/docs`.
- AI Console: `tools/ai-console`; install dependencies from its package lock.
- Existing 22 local commits after `66fad31` preserve the incremental Core,
  memory, bridge, worlds, experience and prediction implementation history.
- Bridge declares 31 remote tools. Authorization is server-side; discovery is
  not itself permission to execute writes. Companion access remains separate.

## Validation actually performed

- Companion: backend venv `python -m unittest discover -s backend -p test_*.py`:
  149 tests passed.
- Frontend: `npx --no-install tsc --noEmit`: passed.
- Frontend: `node --test tests/*.test.cjs`: 49 passed.
- Frontend: `npm run build`: passed; Vite warns about chunks over 500 kB.
- AI Console: `node --check` on server.js and public/app.js: passed.
- MCP: `.omnisvera-tools/Scripts/python.exe -m unittest discover
  -s .local-tools/tests -p test_*.py`: 324 tests, 11 failures, 4 errors.
  The suite is NOT green. Observed issues include expired fixed prospective
  Crypto horizons, legacy tests expecting seven remote tools/four tables,
  remote discovery ordering, and an EPL expectation of 1520 versus 380 rows.
  These are not all proven harmless; follow-up diagnosis is required.
- Warnings also include Starlette/httpx deprecation and unclosed SQLite
  connections in MCP tests. Existing trailing whitespace remains in scripts.
- No live ChatGPT/Claude handoff or operational Prediction was requested.

## Exclusions and reproducibility boundaries

This is not a backup of private operational state. Credentials, OAuth sessions,
tokens, database files, logs, downloaded executables, dependency directories,
raw conversation attachments and runtime-generated images are excluded.
Operational memories and session state need a separate private backup; do not
publish them to this public repository. Original Vault/media changes unrelated
to this code checkpoint remain in the local working tree.

Reinstall Python/Node dependencies, supply private runtime configuration and
Vault/media paths, then build the frontend before starting a fresh installation.
See existing launcher documentation for local credential storage. Historical
launcher URLs and tool counts in older documents describe their original cuts,
not necessarily the current deployment.

## GitHub access

The connected GitHub plugin reported `Allow all actions` on this date and read
a Companion file from this branch successfully. This does not grant arbitrary
filesystem access or prove every separate ChatGPT conversation uses the same
connection. No repository visibility or OAuth scopes were expanded.
