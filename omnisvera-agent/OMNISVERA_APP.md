# Omnisvera App — local read-only prototype

Independent Football / System Monitor entry point. Companion contributes CSS only;
there are no player, Master, character or campaign roles in this App.

The dedicated operator token grants only the fixed read scopes in `omnisvera_app.py`.
Set `OMNISVERA_APP_TOKEN` to a separate secret (32+ characters), never a Companion token.
Set `OMNISVERA_APP_DB` to the existing MCP memory SQLite file. Do not commit either value.

Use a dedicated environment: `uv venv .venv-observer`, then `uv pip install --python .venv-observer/Scripts/python.exe -r backend/requirements-observer.txt`.
Build from `frontend`: `npx vite build --config vite.omnisvera.config.ts`.
Start from `backend`: `../.venv-observer/Scripts/python.exe -m uvicorn omnisvera_app:configured_app --factory --host 127.0.0.1 --port 18911`.
Open `http://127.0.0.1:18911` and enter the operator token. Token is held in page memory only.
Do not expose this local HTTP endpoint publicly. No tunnel or remote deployment is configured.

No Core initialization or Registry invocation: Registry writes audit events. Reads reuse
MemoryStore methods with SQLite `mode=ro` and `query_only`. No schemas are migrated.
HTTP GET reads do not call providers, model builders, Companion, scheduler or MCP tools.
Monitor shows historical events, not live service health. Raw errors and metadata are withheld.
Football includes only rows explicitly identified by `world_id=football`; unclassified legacy rows are not guessed.

Signals Explorer supports exact signal/entity filters, timezone-aware inclusive periods,
bounded pagination, scalar values, sanitized provenance and observation age. Freshness labels
are explicitly the labels persisted at capture: without a persisted TTL, age does not imply
current validity. Missing provenance and values stay unavailable, never fabricated.

Experience history is grouped by predictor/version, newest state first, with pagination,
previous-version references, Core-computed hash integrity, persisted performance and links
to contributing Predictions/Outcomes. Larger details are collapsed. Missing contributors
are identified as unavailable. No learned state update is performed.

Prediction signal links filter the history. If the original reference lacks a timestamp/hash,
the UI explicitly does not claim the resulting observations were used by that Prediction.
Snapshot view exposes hashes and source descriptors, not arbitrary memory contents.
Accuracy and ROI remain unavailable.

Tests from `backend`: `../.venv-observer/Scripts/python.exe -m unittest test_omnisvera_app`.
Frontend: `npx tsc --noEmit`, then the dedicated build above. Companion dist is untouched.

## Local visual QA

From `backend`: `../.venv-observer/Scripts/python.exe observer_qa.py`.
This serves `http://127.0.0.1:18911/` against a newly created disposable database, never
the operational database. The page displays `QA SINTÉTICO — não são dados operacionais`.
Test-only token: `synthetic-qa-only-not-an-operational-secret` (no operational authority).
Other scenarios: `--scenario empty`, `--scenario monitor-error`, `--scenario unavailable`;
choose a free explicit `--port` without terminating existing services.

## Validation — 2026-09-20

- App tests: 10/10 PASS; read paths preserve fixture database SHA-256, scoped auth,
  identity rejection, missing store, forbidden writes, filters/periods/pagination,
  provenance redaction, lineage/integrity/contributors, missing values and no network.
- Backend regression: `python -m unittest discover -s backend -p "test_*.py"`:
  159/159 PASS in `.venv-observer`, including the 10 App tests.
- Previous baseline attempt: NOT VALIDATED — 13 import errors due to missing Pillow.
  That attempt was not a product regression and was not counted as passing.
  Installed the declared requirements only into the isolated environment, then reran.
- TypeScript PASS; dedicated Vite build PASS; `git diff --check` PASS.
- Real local store: authenticated in-process GET smoke returned 200 for summary,
  signals, monitor, both Football prediction details and predictor history.
  All these connections used SQLite read-only/query-only; no operational mutation run.
- Browser QA: Chrome desktop and 390×844 viewport; open and resolved Predictions,
  signal navigation/filtering, missing value/source, fresh/stale/error capture labels,
  history v2→v1 and contributor→resolved Prediction verified with synthetic fixtures.
  Empty database and monitor unavailable states verified; monitor failure does not block
  Football. Healthy badge describes the last successful DB read, not external services.
- No new Core tools, provider calls, domain writes, production builds or tunnels.

Limitations: mobile viewport is not physical-device or multi-network testing. The running
QA URL is not the operational App or a remote access URL. Operational startup still needs
the explicitly configured DB and dedicated operator token. No public deployment performed.
# Operational read-only investigation cut

Start with `./start_observer.ps1`. Default URL: `http://127.0.0.1:18914/`.
This is distinct from the disposable QA instance on port 18911.
The launcher uses the existing monorepo `.assistant-runtime/omnisvera-mcp/memory.db`;
it fails if absent and never initializes/migrates that database.
The dedicated token is stored encrypted with Windows DPAPI in ignored
`.observer-runtime/operator-token.xml`. Run `./start_observer.ps1 -ShowToken`
locally to display it when signing in. Do not paste it in issues or commit it.
The service binds loopback only; no external publication or automatic startup was added.

Predictions now open a modal side drawer containing the persisted claim,
explicit evidence references, outcome, associated Experience and inline history.
Missing match links are not reconstructed from prose. Technical details are collapsed.
Timestamps without a timezone are labeled rather than silently converted.
Performance includes the stored resolution window; monitor impact is limited to
the last Football scheduler execution, not inferred live provider health.

Validation for this cut: 160 backend tests passed; TypeScript passed; observer
Vite build passed (sandbox escalation required for esbuild directory reads).
Operational authenticated HTTP smoke: football, monitor, prediction detail and
signals returned 200. This does not prove current provider availability.
