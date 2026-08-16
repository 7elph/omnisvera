from __future__ import annotations

import unittest
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.character_play import (
    apply_character_action,
    init_character_play,
    load_session_abilities,
    seed_session_ability_resources,
)


def by_name(profile_id: str) -> dict[str, dict]:
    return {entry["name"]: entry for entry in load_session_abilities(profile_id)}


class SessionAbilityCatalogTests(unittest.TestCase):
    def test_each_character_receives_only_their_catalog(self) -> None:
        expected = {
            "raziel": {
                "Reserva de Sangue", "Regeneração Vampírica", "Lâmina de Sangue", "Marca Rubra",
                "Fome de Sangue", "Mordida", "Caixão", "Medo", "Forma da Noite",
                "Sentido do Sangue", "Fotossensibilidade", "Cura Vampírica Invertida",
            },
            "varkh": {"Manipulação de Elementos", "Transmutação"},
            "vezemir": {"Força Arcana", "Velocidade"},
            "morthak": {
                "Mísseis Mágicos", "Adaga de Osso", "Levantar um Esqueleto", "Animar Mortos",
                "Não-Vida Consciente", "Memória Fraturada", "Chamado Necromântico", "Ossos sem Carne",
                "Corpo Quebradiço", "Cura Antinatural", "Repouso Imóvel", "Afastar Mortos-Vivos",
                "Grimório de Mago",
            },
        }
        catalogs = {profile_id: set(by_name(profile_id)) for profile_id in expected}
        shared_names = {"Não-Vida Consciente"}
        for profile_id, required in expected.items():
            self.assertTrue(required <= catalogs[profile_id])
            foreign_required = set().union(*(names for other, names in expected.items() if other != profile_id))
            self.assertFalse((catalogs[profile_id] & foreign_required) - shared_names)

    def test_morthak_spells_preserve_campaign_circles_and_source_boundaries(self) -> None:
        spells = by_name("morthak")
        self.assertEqual(spells["Mísseis Mágicos"]["circle"], 1)
        self.assertEqual(spells["Adaga de Osso"]["kind"], "attack")
        self.assertNotIn("circle", spells["Adaga de Osso"])
        self.assertEqual(spells["Levantar um Esqueleto"]["circle"], 2)
        self.assertEqual(spells["Animar Mortos"]["circle"], 3)
        self.assertEqual(spells["Mísseis Mágicos"]["mechanics_status"], "structured")
        self.assertIn("1d4 + 1", spells["Mísseis Mágicos"]["description"])
        self.assertIn("10 metros + 3 metros por nível", spells["Mísseis Mágicos"]["description"])
        self.assertEqual(spells["Adaga de Osso"]["mechanics_status"], "partial")
        self.assertIn("Ataque básico", spells["Adaga de Osso"]["description"])
        self.assertEqual(spells["Levantar um Esqueleto"]["mechanics_status"], "partial")
        self.assertIn("Nenhuma regra com esse nome foi localizada", spells["Levantar um Esqueleto"]["description"])
        self.assertEqual(spells["Animar Mortos"]["mechanics_status"], "partial")
        self.assertIn("5º círculo", spells["Animar Mortos"]["description"])
        self.assertIn("3º círculo", spells["Animar Mortos"]["description"])

    def test_prompt_only_varkh_powers_remain_mechanically_partial(self) -> None:
        powers = by_name("varkh")
        for name in ("Manipulação de Elementos", "Transmutação"):
            self.assertEqual(powers[name]["mechanics_status"], "partial")
            self.assertTrue(powers[name]["description"])

    def test_canonical_numbers_only_appear_where_the_source_has_them(self) -> None:
        raziel = by_name("raziel")
        morthak = by_name("morthak")
        vezemir = by_name("vezemir")
        self.assertIn("1d4", raziel["Mordida"]["description"])
        self.assertIn("1d4", raziel["Lâmina de Sangue"]["description"])
        self.assertIn("1d6", raziel["Fotossensibilidade"]["description"])
        self.assertIn("+2", morthak["Ossos sem Carne"]["description"])
        self.assertIn("metade dos PV", morthak["Cura Antinatural"]["description"])
        self.assertIn("1d6 + nível", vezemir["Força Arcana"]["description"])
        self.assertIn("1d4 + nível", vezemir["Velocidade"]["description"])

    def test_campaign_use_counters_are_structured_as_resources(self) -> None:
        expected = {
            "raziel": {"reserva_de_sangue": 5, "forma_da_noite": 1},
            "morthak": {"misseis_magicos": 3},
            "vezemir": {"forca_arcana": 1, "velocidade": 1},
        }
        for profile_id, counters in expected.items():
            resources = {entry["key"]: entry for entry in seed_session_ability_resources(profile_id)}
            self.assertEqual({key: resources[key]["maximum"] for key in counters}, counters)
            self.assertTrue(all(resources[key]["recharge"] == "inn_rest" for key in counters))

    def test_inn_rest_restores_hp_conditions_and_all_resources(self) -> None:
        with TemporaryDirectory() as directory:
            database_path = Path(directory) / "companion.sqlite3"
            init_character_play(database_path)
            initial = {
                "current_hp": 2,
                "maximum_hp": 12,
                "temporary_hp": 4,
                "conditions": ["Envenenado", "Caído"],
                "resources": [
                    {"key": "magias_de_1o_circulo", "label": "Magias de 1º círculo", "current": 0, "maximum": 1},
                    {"key": "misseis_magicos", "label": "Mísseis Mágicos · usos", "current": 0, "maximum": 3},
                    {"key": "mana", "label": "Mana", "current": 1, "maximum": 6},
                ],
                "coins": 10,
                "location": "Nimalis",
                "session_notes": "",
            }
            with closing(sqlite3.connect(database_path)) as connection, connection:
                connection.execute(
                    "INSERT INTO character_states(profile_id,state_json,version,updated_at) VALUES(?,?,1,?)",
                    ("morthak", json.dumps(initial, ensure_ascii=False), "2026-08-15T00:00:00+00:00"),
                )
            apply_character_action(
                database_path,
                character_id="morthak",
                actor_id="master",
                actor_role="gm",
                action="rest_at_inn",
                payload={},
            )
            with closing(sqlite3.connect(database_path)) as connection:
                state = json.loads(connection.execute(
                    "SELECT state_json FROM character_states WHERE profile_id='morthak'"
                ).fetchone()[0])
            self.assertEqual(state["current_hp"], 12)
            self.assertEqual(state["temporary_hp"], 0)
            self.assertEqual(state["conditions"], [])
            self.assertEqual([resource["current"] for resource in state["resources"]], [1, 3, 6])


if __name__ == "__main__":
    unittest.main()
