# Combat repair — partial delivery

## Observed, not inferred

- Session ledger contains confirmed Vezemir and Raziel attacks. Several Raziel resolutions remained pending; creating a resolution does not apply HP damage.
- No Morthak attack resolution was found in the inspected records. This alone does not prove which action he attempted.
- Initiative engine already supported `next_turn`, but the request schema and UI did not expose it.
- Raziel's equipped melee-slot daggers were rejected as a ranged weapon. `Items/Adagas de Espectro Fantasma.md` explicitly documents throwing and 1d4 damage. The fix preserves the existing bonus; it does not grant another +2.
- Morthak's Adaga de Osso card is partial: no confirmed damage/attack formula. Its target selector does not resolve damage.
- Ability use currently consumes a resource or logs an action; this is not equivalent to resolving a targeted spell. Automatic spell damage is still pending.

## Implemented

- Authenticated next-turn endpoint; only the current character or Master can advance. Retries are idempotent; wrap advances round.
- Hidden participants no longer shift the visible active-turn index to an unrelated character.
- Visible current-turn banner and explicit pass button in combat panel.
- Master monster attack panel using persisted attack bonus/damage and the existing resolve/confirm ledger path.
- Monster pin image and Master-only current/max HP editor.
- Map pin HP progress bars with accessible numeric labels.
- Throwing mode retained for the documented campaign daggers.
- Pending attack modal explicitly states damage is not yet applied; backdrop click no longer silently dismisses it.

## Verification

177 backend tests passed; 72 existing frontend tests passed; 2 new frontend interaction tests passed. TypeScript and production build passed. Tests use disposable fixtures, not campaign attacks.

## Still open

- Confirm Morthak's Adaga de Osso mechanics with the Master.
- Implement atomic targeted spell/resource resolution, including reviewed missiles and bite rules.
- Broader map/item image availability audit and browser/mobile visual QA.
- Attacker-target line, global turn attention outside the combat panel, pending-resolution recovery across reloads.
- Master plus players on different networks: not yet tested for this change.

No Vault edits, campaign attack execution, push, or commit in this repair.

## Follow-up: ranged cards and spider sting

- Current saved spider attack is `1d8 + Veneno`, bonus 4. The previous endpoint sent the whole string to the dice parser. Numeric damage is now separated from the textual rider; a hit retains `Veneno` as a pending manual effect in the resolution and audit. Poison saving throw/death is NOT silently applied or claimed automated.
- Unsupported arithmetic such as `1d8+1d6` is rejected contextually, never truncated to its first die.
- Removed frontend hardcoded damage defaults (including a fictional ranged 1d6 for Vezemir). Cards with no server-defined weapon/damage explain missing setup instead of offering a target-only dead end.
- Authenticated current read: Raziel ranged has +3 / 1d4 and the daggers; Vezemir and Morthak ranged have no weapon or damage. Their precise ranged weapon/ability needs confirmation. Equipment-slot choices alone do not establish a throwing rule.
- Digital monster actions expose an explicit Atacar button and take no formula/damage input. Both attack roll and numeric damage come from server-side persisted stats.
- Browser read-only inspection confirmed a recent successful Raziel ranged hit in the visible session log (4 damage) and current table mode Digital; no campaign attack was performed for this inspection.

## Follow-up 2026-09-27: three-player rehearsal and orphan effects

The real-HTTP rehearsal initially failed at the GM round transition with
`Criatura não encontrada`. The copied campaign contained an active periodic
effect referring to a deleted token. Both explicit round advancement and
next-turn wrap previously tried to apply that effect to a nonexistent creature.

The engine now expires effects whose target no longer exists when ticking a
round, retaining the original record and a `target_missing` audit reason. Other
errors are not suppressed. No campaign effect was manually deleted or edited.
A regression test reproduced the failure before the fix and passes afterward.

### Current action coverage (not a new rules decision)

| Character | Action | Current executable path | Outstanding limit |
| --- | --- | --- | --- |
| Vezemir | Grisalma, melee | +2 / 2d6; resolve then confirm | Range not configured |
| Vezemir | Ranged | No linked weapon or damage | Do not invent a throwing attack |
| Vezemir | Força Arcana / Velocidade | Descriptions exist in session ability catalog | Description is not proof of automatic application |
| Raziel | Daggers, melee/ranged | Ranged +3 / 1d4; resolve then confirm | Do not grant the historical +2 again |
| Raziel | Blood techniques / Mordida | Catalog describes costs and effects | `useAbility` alone is not targeted damage/healing resolution |
| Raziel | Sentido do Sangue | Blocked | Preserve Master's decision; blood maximum remains 5 |
| Morthak | Cajado, melee | +0 / 1d4; resolve then confirm | Does not imply a ranged staff attack |
| Morthak | Adaga de Osso | Partial campaign action | Attack bonus, damage and range need a definitive rule |
| Morthak | Mísseis Mágicos | Reference text exists | Reconcile edition/campaign rule before atomic spell resolution |
| Morthak | Other necromancy | Partial/adapted catalog | Do not infer missing duration, control or targets |

Sources for this coverage are the copied current character API definitions,
`app/data/session_abilities.json`, and the existing `useAbility` implementation.
It is an implementation audit, not a fresh verification of every rule PDF.
Selecting an allowed inventory slot is not evidence of a weapon's range rule.

### Reproducible rehearsal

New `backend/scripts/combat_party_probe.py` runs against an OS-temporary database
prepared and served by `cf01_probe.py`, with local fixture credentials. It uses
the copied definitions without granting weapons or changing character rules.

Verified via loopback HTTP:

- Vezemir melee, Raziel ranged and Morthak melee: preview does not change HP;
  confirmation applies damage; retry after reconnect does not duplicate it;
  exactly one combat ledger event per resolution.
- Only the current player can pass their turn; retry does not advance twice.
- GM creature attack reads `1d8 + Veneno` from the token and requires no formula
  or damage field from the client. The digital run missed; the separate fixed-RNG
  regression covers a hit and retains venom as a manual effect.
- Final participant wraps to the first participant; encounter closes.

Commands executed:

- `.venv-observer/Scripts/python.exe backend/scripts/combat_party_probe.py <temp-db> 18879`: PASS.
- From backend: `../.venv-observer/Scripts/python.exe -m unittest discover -s . -p 'test_*.py' -q`: 180 PASS.
- From frontend: `node --test tests/*.test.cjs`: 75 PASS.
- From frontend: `npx --no-install tsc --noEmit`: PASS.
- From frontend: `npm run build`: PASS, existing large-chunk warning.
- `git diff --check`: PASS, line-ending warnings only.

This does not prove full spell automation, visual interaction or independent
mobile-network endurance. Production was not used for rehearsal attacks.
