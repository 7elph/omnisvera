# MCP consolidation audit

Baseline: branch `devin/create-omnisvera-class-standard`, HEAD `84d5ff13a95abc600b4e820a43191ef1688b0c3e`.
Exact baseline command: `.omnisvera-tools/Scripts/python.exe -m unittest discover -s .local-tools/tests -p test_*.py`.
Result: **324 tests, 11 failures, 4 errors**, reproduced before edits.
Full baseline output was saved locally as `%TEMP%/omnisvera-mcp-consolidation-baseline.log`.

## Classification before changes

| Test (module / method) | Classification | Evidence and correction |
|---|---|---|
| test_crypto_btc_poc / test_dry_run_and_runtime_v2 | TIME_DEPENDENT_TEST | January 2026 horizon already expired; freeze commit/store clocks to Coinbase fixture timeline. |
| test_crypto_btc_poc / test_transport_identity_and_commit | TIME_DEPENDENT_TEST | Same fixture fails before transport identity assertion; same controlled clock. |
| test_crypto_btc_poc / test_identity_and_idempotence | TIME_DEPENDENT_TEST | Temporal rejection masks intended identity denial; do not weaken production horizon rule. |
| test_crypto_btc_poc / test_validation_and_hash | TIME_DEPENDENT_TEST | Same expired horizon; preserve missing/tampered Experience checks. |
| test_bridge_parity / test_world_describe_football | FIXTURE/DATA_MISMATCH | server.py deliberately constructs HttpFootballDataProvider; test expected FakeFootballDataProvider without injecting one. Verify the configured provider. |
| test_bridge_parity / test_bridge_tool_count_matches | OBSOLETE_TEST | Bridge has Experience reads and world.context, 31 names; compare actual discovery to explicit allowlist. |
| test_bridge_parity / test_remote_tool_count | OBSOLETE_TEST | 28 is an earlier cut; verify 31 unique names and deny exposure of create_prediction. |
| test_mcp_core_cut3 / test_schema_has_exactly_the_four_core_tables_and_provenance | OBSOLETE_TEST | store migrations deliberately add predictions, resolutions, signals, scheduler, Experiences, update events. Verify exact current ten-table schema. |
| test_memory_bootstrap / test_seed_inserts_four_explicit_memories_with_verifiable_sources | OBSOLETE_TEST | stats includes new domains; assert seed counts plus zero rows in every other reported domain. |
| test_memory_recall / test_public_schemas_and_explicit_remote_allowlist | OBSOLETE_TEST | Seven tools was Memory Recall cut; preserve memory schemas and compare complete current allowlist. |
| test_mia_bridge / test_remote_discovery_is_exactly_the_bounded_allowlist | OBSOLETE_TEST | Same names, different registration order. No positional contract in bridge; compare multiplicity/content, not order. |
| test_opencode_mcp / test_allowlist_and_identity_are_internal | OBSOLETE_TEST | Same ordering issue; preserve identity and write-denial assertions. |
| test_opencode_mcp / test_cold_start_discovery_read_and_write_denial | OBSOLETE_TEST | ExceptionGroup wraps the same ordering assertion, not a transport error. |
| test_real_brain_capstone (import error) | FIXTURE/DATA_MISMATCH | Script passes `until <date>` although commit requires ISO. Use ISO, frozen clock, managed temp DB, and a real unittest method instead of execution at import. Original scenario/assertions retained. |
| test_real_domain_learning / test_real_closed_loop | FIXTURE/DATA_MISMATCH | PRE_REG_RUN and filters explicitly select EPL_2324 (380), with 3040 train rows. Final assertions retained obsolete four-season 1520 count. Match documented bounded protocol and version increment to actual evaluation count. |

No baseline failure required changing authorization, table migrations, models,
prediction hashes, ordering of Experience updates, or the remote surface.

## Additional findings exposed by isolation and follow-up tests

- REAL_REGRESSION: snapshot validation owned a SQLite connection without closing
  it. sqlite3's context manager handles transactions, not lifetime. Use
  `contextlib.closing`; correct equivalent test-fixture ownership. New regression
  retains connections and proves every validation connection is closed.
- REAL_REGRESSION: validate_candidate swallowed malformed ISO horizon errors,
  returning valid while commit rejected the same candidate. Validation now
  reports invalid ISO explicitly; commit's authoritative time check is unchanged.
- OBSOLETE_TEST: write-annotation fixtures omitted resolve_due_predictions,
  which already has READ_WRITE in bridge.py. Update expectations, not permissions.
- The initial isolated source copy lacked Nimalia/old handoff fixtures and the
  configured Python runtime. Those setup omissions were supplied in the temporary
  copy; no product behavior was changed to hide the resulting errors.

## Isolation and acceptance checks

After the exact requested baseline, repeated suites run from a temporary source
copy with the same `.local-tools` files, required read-only Vault fixtures and a
junction to the installed Python dependencies. No operational DB, token file or
runtime directory is copied. This prevents legacy launcher-import tests from
using the real operational root. The standalone clean-install test additionally
uses a fresh subprocess, empty directory, filtered environment and offline
network mocks. Production launchers are unchanged.

The Crypto runtime test now exercises CoreStateVectorBuilder -> snapshot_from_model
-> candidate -> validate -> commit -> simulated Coinbase evidence -> resolution
-> Brier score -> Experience v2. It verifies predictor/snapshot provenance,
candidate hash, exact previous Experience ID/version/hash, previous_experience_id,
integrity, one resolution row and one update event. Replays leave two Experience
versions, not additional versions. No operational Prediction is created.

Three regression tests added to Crypto: expiry between validation/commit,
malformed ISO, deterministic connection closure. One subprocess clean-start test
added. The capstone now counts as one actual test instead of one failed import.
Final verified total: **328 tests in 103.255s, OK**, no failures, errors or skips.
Full final output: `%TEMP%/omnisvera-consolidation-final.log`.
There were no SQLite ResourceWarnings in this run. Starlette/httpx emitted one
deprecation warning. Targeted checks also passed: Crypto 10 tests; capstone 1;
clean-install subprocess 1. Python compilation and `git diff --check` passed.

Final full-suite command (inside the isolated source copy):
`.omnisvera-tools/Scripts/python.exe -m unittest discover -s .local-tools/tests -p test_*.py`.
Cold start, synthetic epistemic cycle, exactly-once update and Experience
integrity: PASS. Remote contract: the same 31 unique names; no new tools.

Production changes are limited to snapshot connection lifetime and early rejection
of invalid ISO horizons. All other changes are tests/documentation. Companion,
transport identity, scopes, hashes, causal ordering and allowlists are unchanged.

## Remaining limitations

- Starlette/httpx deprecation is dependency debt, not silenced here.
- Some legacy test modules still use custom exec loaders or module-level
  fixtures. The full-suite source-copy isolation is necessary for safe execution
  until a separately scoped test-harness cleanup is approved.
- Passing synthetic/local tests does not prove ChatGPT/Claude network availability
  or real-world predictive advantage. Neither is claimed by this consolidation.
