# Current state - OMNISVERA Companion

Atualização para publicação: 2026-10-31

O código atual inclui o baseline abaixo, os routers de arquitetura/saúde e os
efeitos especiais de itens. O ponto de entrada para revisar o snapshot publicado
é [CURRENT_COMPANION_CODE.md](CURRENT_COMPANION_CODE.md); testes e limites do
último corte estão em [ITEM_SPECIAL_EFFECTS_2026-10-31.md](ITEM_SPECIAL_EFFECTS_2026-10-31.md).
As descrições abaixo registram o baseline histórico de 30/10, não os números
atuais dos arquivos ou o estado atual da publicação.

Snapshot histórico: 2026-10-30

## Baseline

- Branch: `devin/create-omnisvera-class-standard`
- Baseline commit: `9710bf82 chore(companion): capture selective working baseline`
- Repository root: `C:\Users\delib\Desktop\OMNISVERA`
- Application directory: `omnisvera-agent`
- Commit scope: 765 files, 89.313 insertions, 1.390 deletions, about 62.5 MB of working-tree content.
- At the time of this baseline, the commit was local and had not been pushed.

The baseline captured source, active tests, catalogs, documentation, app assets and
scripts needed to inspect the current Companion. It intentionally excluded private
session preparation, temporary files and operational state.

## Deliberately outside the commit

- `docs/preparation/`: private GM preparation. Review before committing.
- `backend/app/dorn_spells.py.tmp2`: temporary edit artifact.
- Operational databases, logs, backups, uploads, `.autonomy/` and runtime state.
- `CAMPANHA/`, `zz_media/`, `omnisvera-model/` and the external Godot project.
- `frontend/dist/`: generated build output.

## Architecture as found

- Backend: FastAPI + SQLite, 141 Python modules under `backend/app`.
- `backend/app/main.py` is the current composition root: 6.492 lines and 273
  route decorators. There is no application factory yet.
- Frontend: React + Vite, 147 files under `frontend/src`.
- `frontend/src/pages/SessionWorkspace.tsx` is 3.007 lines; `frontend/src/api.ts`
  is 2.593 lines; `frontend/src/styles.css` is 4.766 lines.
- `backend/app/rag.py` is 3.959 lines.
- Database statements are spread across roughly 34 modules; there is no central
  migration layer.
- Action logic is partially domain-oriented already (`action_contract.py`,
  `dorn_spells.py`, `necromancer_spells.py`, `monster_*`, `merchant*`), but route
  registration, authorization and state ownership remain concentrated in
  `main.py`.
- Catalogs are data-driven but incomplete: 255 monsters, 854 spells, 326 static
  items versus 486 registry entries, 10 approved actions and 5 hemomancy passives.

## Implementation direction

1. Introduce an application factory and explicit router registration without
   changing URLs, authentication or response shapes.
2. Extract route groups by domain while keeping backend state authoritative.
3. Add declarative domain manifests for monsters, spells, items and actions.
4. Keep persistence in the existing SQLite schema until a migration layer is
   justified and tested.
5. Refactor the frontend after backend contracts stabilize.

A module means a domain engine plus declarative data and handlers. It does not
mean one source file per monster, spell, item or NPC.

## Canonical checks

Frontend:

```powershell
cd frontend
npm test
npx tsc --noEmit
npm run build
```

Backend, isolated from the live workload lock and operational database:

```powershell
$root = (Get-Location).Path
$run = Join-Path $env:TEMP ("omnisvera-tests-" + [guid]::NewGuid().ToString("N"))
New-Item -ItemType Directory -Path $run | Out-Null
$env:LOCALAPPDATA = Join-Path $run "localappdata"
$env:OMNISVERA_DB_PATH = Join-Path $run "fixture.sqlite3"
$env:OMNISVERA_AUTO_REFRESH_INDEX = "false"
$env:OMNISVERA_REBUILD_ON_STARTUP = "false"
& ".\.venv-observer\Scripts\python.exe" -m unittest discover -s backend -p "test_*.py"
```

Do not kill an active `run_sheet_test.py` process to free the real
`workload.lock`. Use the isolated `LOCALAPPDATA` above instead.

Browser, smoke and visual suites must run through the isolated MCP rehearsal
fixture. They are not authorized to mutate the live table. See
`docs/TEST_MANIFEST.md` and `docs/AI_TEST_TOOLS.md`.

## Known gaps

- Full backend suite passed on 2026-10-30: 1.768 tests, 1 skipped, 654 s.
- Frontend unit suite passed: 491 tests. Typecheck and build also passed.
- UI smoke and mobile acceptance were not run in this baseline.
- Some tracked smoke/visual scripts are historical or orphaned. Passing unit
  tests do not certify the full Companion.
- `docs/preparation/` remains outside git by design.
- Asset coverage, monster attacks, spell repertoires, prices and images still
  have catalog gaps.

## Next work

1. Verify the isolated backend suite and the new test runner.
2. Add the application factory and route registration contract.
3. Extract one low-risk domain at a time, with regression tests for URLs,
   authentication, private GM data and player visibility.
4. Only then begin the frontend page/component decomposition.
