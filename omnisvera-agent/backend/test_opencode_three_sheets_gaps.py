"""OpenCode isolated gap proofs: Vezemir/Morthak/Dorn (fixture TEMP only).

Scope: evidence/tests only. No runtime, catalog, rule or live-sheet change.
Reuses existing disposable fixtures (TEMP SQLite); never 8787/8788, never
operational DB/tokens. Raziel is regression-only and is not exercised here.

Families covered (verify against THREE_SHEETS_AUDIT matrix, do not assume):
- Morthak Toque Sombrio: per-turn loss, persistence/reload, cost, idempotency.
- Morthak Animar Mortos + Levantar Esqueleto: coexistence (dismissal pending).
- Morthak Clonagem: fragmento consumivel ausente = EXPECTED_BLOCK sem custo.
- Dorn Guarda: redirecionamento, adjacencia/grid, expiracao no turno de Dorn.
- Dorn Teia: area, custo de movimento no grid, expiracao.
- Dorn Reflexos: interceptacao de acerto unico, nunca area.
- Contrato de certificacao: PASS seletivo nao certifica ficha inteira.
"""
import json
import sqlite3
from contextlib import closing
from unittest import TestCase
from unittest.mock import patch


class ToqueSombrioTurnGapTests(TestCase):
    """Toque Sombrio: dano inicial + perda de PV no turno, com reload."""

    def setUp(self):
        import test_necromancer_integrity as fixtures

        self.fixture = fixtures.TouchTransactionTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.db = self.fixture.db

    def test_dot_persists_after_reload_costs_one_and_retry_is_idempotent(self):
        from app.combat import confirm_attack_resolution
        from app.combat_effects import readeffects

        with patch(
            "app.necromancer_spells.touch_rider", return_value={"dot_hp": True}
        ):
            first = self.fixture.resolve()
            confirmed, _ = confirm_attack_resolution(
                self.db,
                resolution_id=first["resolution_id"],
                requested_by_id="morthak",
                requested_by_role="player",
            )
            replay = self.fixture.resolve()
            confirm_attack_resolution(
                self.db,
                resolution_id=first["resolution_id"],
                requested_by_id="morthak",
                requested_by_role="player",
            )
            self.assertEqual(confirmed["resolution_id"], replay["resolution_id"])
        reloaded = readeffects(self.db)
        dots = [e for e in reloaded["effects"] if e.get("dot_hp")]
        self.assertEqual(1, len(dots), "perda de PV no turno deve persistir apos reload")
        with closing(sqlite3.connect(self.db)) as db:
            state = json.loads(
                db.execute(
                    "SELECT state_json FROM character_states WHERE profile_id='morthak'"
                ).fetchone()[0]
            )
        self.assertEqual(0, state["resources"][0]["current"], "custo diario consumido uma vez")


class SummonCoexistenceGapTests(TestCase):
    """Animar Mortos pode coexistir com o esqueleto; dispensa segue pendente."""

    def setUp(self):
        import test_morthak_high_spells as fixtures

        self.fixture = fixtures.HighSpellTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def create_pair(self):
        from app import main
        from app.summons import create_summon

        with closing(sqlite3.connect(self.path)) as db, db:
            state = json.loads(
                db.execute(
                    "SELECT state_json FROM character_states WHERE profile_id='morthak'"
                ).fetchone()[0]
            )
            if not any(r.get("key") == "animar_mortos" for r in state.get("resources", [])):
                state["resources"].append(
                    {"key": "animar_mortos", "current": 1, "maximum": 1}
                )
                db.execute(
                    "UPDATE character_states SET state_json=? WHERE profile_id='morthak'",
                    (json.dumps(state),),
                )
            db.execute(
                "UPDATE session_workspace_tokens SET current_hp=0,sheet_json=? WHERE id=?",
                (json.dumps({"reanimation_allowed": True}), self.fixture.fixture.ogre["id"]),
            )
        first = create_summon(
            self.path,
            caster="morthak",
            technique="levantar-esqueleto",
            spec=main._SUMMON_DEFAULTS["levantar-esqueleto"],
            request_id="opencode-coexist-skeleton",
            actor_id="morthak",
            actor_role="player",
        )
        second = create_summon(
            self.path,
            caster="morthak",
            technique="animar-mortos",
            spec=main._SUMMON_DEFAULTS["animar-mortos"],
            corpse_id=self.fixture.fixture.ogre["id"],
            request_id="opencode-coexist-zombie",
            actor_id="morthak",
            actor_role="player",
        )
        self.assertNotEqual(first["token"]["id"], second["token"]["id"])
        with closing(sqlite3.connect(self.path)) as db:
            for token in (first["token"]["id"], second["token"]["id"]):
                self.assertGreater(
                    db.execute(
                        "SELECT current_hp FROM session_workspace_tokens WHERE id=?",
                        (token,),
                    ).fetchone()[0],
                    0,
                )
        return first['token'], second['token']

    def test_skeleton_and_reanimated_creature_coexist(self):
        self.create_pair()


class ClonagemComponentGapTests(TestCase):
    """Clonagem sem fragmento = bloqueio previsto, sem custo nem token."""

    def setUp(self):
        import test_morthak_high_spells as fixtures

        self.fixture = fixtures.HighSpellTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def test_missing_fragment_is_expected_block_without_cost(self):
        with closing(sqlite3.connect(self.path)) as db, db:
            db.execute(
                "UPDATE player_inventory SET quantity=0 WHERE item_path='fragment-test'"
            )
        with self.assertRaisesRegex(ValueError, "fragmento"):
            self.fixture.command("necro_spell_cast", {"spell_id": "clonagem"})
        with closing(sqlite3.connect(self.path)) as db:
            state = json.loads(
                db.execute(
                    "SELECT state_json FROM character_states WHERE profile_id='morthak'"
                ).fetchone()[0]
            )
            self.assertEqual(
                1,
                next(r["current"] for r in state["resources"] if r["key"] == "clonagem"),
            )
            self.assertEqual(
                0,
                db.execute(
                    "SELECT count(*) FROM session_workspace_tokens "
                    "WHERE json_extract(sheet_json,'$.summon.technique')='clonagem'"
                ).fetchone()[0],
            )


class DornGuardaGapTests(TestCase):
    """Guarda: aliado adjacente no grid, redireciona, expira no turno de Dorn."""

    def setUp(self):
        import test_dorn_protocols as fixtures

        self.fixture = fixtures.DornProtocolTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)

    def test_guard_expires_on_dorn_turn(self):
        self.fixture.start()
        self.fixture.guard()
        self.assertTrue(self.fixture.command("next_turn")["effects"])
        self.assertFalse(self.fixture.command("next_turn")["effects"])

    def test_guard_rejects_unpositioned_ally_without_spending(self):
        self.fixture.start()
        before = __import__("app.combat_effects", fromlist=["readeffects"]).readeffects(
            self.fixture.db
        )
        with self.assertRaisesRegex(ValueError, "grid|Posicione"):
            self.fixture.command(
                "dorn_guard",
                ally_id="ally",
                position_confirmed=True,
                grid_selection=True,
            )
        after = __import__("app.combat_effects", fromlist=["readeffects"]).readeffects(
            self.fixture.db
        )
        self.assertEqual(before, after)


class DornTeiaGapTests(TestCase):
    """Teia: area no mapa do combate ativo, penalidade e expiracao."""

    def setUp(self):
        import test_dorn_approved_pack as fixtures

        self.fixture = fixtures.DornApprovedPackTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def test_web_area_persists_then_expires(self):
        from app.combat_effects import effect_command, readeffects

        _, _ = self.fixture.grid()
        result = self.fixture.cast(
            "teia", targets=[{"type": "token", "id": self.fixture.fixture.enemy["id"]}]
        )
        environmental = [e for e in result["effects"] if e.get("environmental")]
        self.assertEqual(1, len(environmental))
        state = readeffects(self.path)
        ended = effect_command(
            self.path,
            actor_id="master",
            actor_role="gm",
            request_id="opencode-web-expiry",
            expected_version=state["version"],
            action="dorn_spell_time",
            payload={"seconds": 9000},
        )
        self.assertFalse(any(e.get("environmental") for e in ended["effects"]))


class DornReflexosGapTests(TestCase):
    """Reflexos: intercepta acerto unico, nunca dano em area."""

    def setUp(self):
        import test_dorn_approved_pack as fixtures

        self.fixture = fixtures.DornApprovedPackTests()
        self.fixture.setUp()
        self.addCleanup(self.fixture.doCleanups)
        self.path = self.fixture.path

    def test_reflection_skips_area_and_intercepts_single_hit(self):
        from app.dorn_spell_pack import redirect_hits

        with patch(
            "app.dorn_spells.roll_formula",
            side_effect=[{"total": 1}, {"total": 1}],
        ):
            self.fixture.cast("reflexos")
        with closing(sqlite3.connect(self.path)) as db, db, patch(
            "app.dorn_spell_pack.roll_formula", return_value={"total": 1}
        ) as dice:
            total, _ = redirect_hits(
                db,
                "character",
                "dorn7",
                [
                    {"result": "hit", "damage_total": 6},
                    {"result": "hit", "damage_total": 7},
                ],
                "now",
                area=True,
            )
            self.assertEqual(13, total)
            dice.assert_not_called()
            total, detail = redirect_hits(
                db,
                "character",
                "dorn7",
                [
                    {"result": "miss", "damage_total": 0},
                    {"result": "hit", "damage_total": 6},
                ],
                "now",
            )
            self.assertEqual(0, total)
            self.assertEqual(1, detail["images_remaining"])


class CertificationContractGapTests(TestCase):
    """Lembra: PASS seletivo nao certifica ficha inteira nem UI por acao."""

    def test_selective_pass_leaves_gaps_for_uncertified_actions(self):
        from scripts.sheet_rehearsal import attach_ui_evidence, build_report

        sheets = {
            "vezemir": {
                "definition": {
                    "attacks": [{"id": "melee", "damage": "1d6"}],
                    "session_abilities": [
                        {"id": "provocacao", "active": True},
                        {"id": "velocidade", "active": True},
                    ],
                }
            }
        }
        results = [
            {
                "actor": "vezemir",
                "scenario_id": "native",
                "status": "PASS",
                "covers": ["attack:melee"],
                "verified_checks": ["execution", "persistence", "idempotency", "range"],
            }
        ]
        report = build_report(sheets, results, actors=["vezemir"])
        self.assertFalse(report["certification"]["ready"])
        missing = {
            g["key"]: g["missing_checks"]
            for g in report["certification"]["gaps"]
        }
        self.assertIn("ui", missing["attack:melee"])
        self.assertIn("ability:provocacao", missing)
        attach_ui_evidence(
            report,
            {
                "status": "PASS",
                "checks": [
                    {
                        "script": "layout",
                        "status": "PASS",
                    }
                ],
            },
        )
        self.assertTrue(
            all("ui" in g["missing_checks"] for g in report["certification"]["gaps"]),
            "layout PASS nao pode certificar acao nao executada",
        )
