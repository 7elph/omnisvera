"""Testes determinísticos do inventário de prontidão dos catálogos."""
from unittest import TestCase

from app.catalog_readiness import build_catalog_readiness


def _fixture_monsters():
    return {
        "schema_version": 1,
        "catalog": {"id": "fixture-monsters", "title": "Fixture OD2", "edition": "2a edição"},
        "count": 2,
        "monsters": [
            {
                "id": "grifo-fixture",
                "name": "Grifo",
                "category": "Besta",
                "movement": "9, 21V",
                "attacks": [
                    {"name": "Mordida", "bonus": 7, "damage": "2d8", "count": 1},
                    {"name": "Garras", "bonus": 7, "damage": "1d4", "count": 2},
                ],
                "abilities": [{"name": "Presa Preferencial", "description": "Ataca cavalos."}],
                "image_path": "zz_media/ui/icons/monsters/grifo.webp",
                "image_attribution": "Acervo · SRD",
                "image_license": "CC BY-SA 4.0",
            },
            {
                "id": "dragao-fixture",
                "name": "Dragão Fixture",
                "category": "Dragão",
                "movement": "",
                "attacks": [],
                "abilities": [
                    {"name": "Baforada", "description": "cone de fogo sem números."},
                    {"name": "Magias", "description": "pode conjurar magias como um Mago de 7º nível."},
                ],
                "image_path": None,
                "image_attribution": None,
                "image_license": None,
            },
        ],
    }


def _fixture_spells():
    return {
        "schema_version": 1,
        "catalog": {"id": "fixture-spells", "title": "Fixture OD2", "edition": "2a edição"},
        "count": 5,
        "spells": [
            {
                "id": "arcana-alarme",
                "name": "Alarme",
                "tradition": "arcana",
                "circle": 1,
                "school": "Abjuração",
                "alcance": "0",
                "duracao": "4 horas",
                "description": "O conjurador protege uma área.",
                "source": "Fixture",
            },
            {
                "id": "arcana-toque",
                "name": "Toque Gelado",
                "tradition": "arcana",
                "circle": 1,
                "school": "Evocação",
                "alcance": "toque",
                "duracao": "instantânea",
                "description": "Causa 1d6 de dano ao alvo tocado.",
                "source": "Fixture",
            },
            {
                "id": "arcana-multi",
                "name": "Seta Múltipla",
                "tradition": "arcana",
                "circle": 2,
                "school": "Evocação",
                "alcance": "30 metros",
                "duracao": "instantânea",
                "description": "Atinge até 3 criaturas com 2d6 de dano; JPD reduz pela metade.",
                "source": "Fixture",
            },
            {
                "id": "arcana-cone",
                "name": "Sopro de Chamas",
                "tradition": "arcana",
                "circle": 3,
                "school": "Evocação",
                "alcance": "10 metros",
                "duracao": "instantânea",
                "description": "Um cone de fogo causa 3d6 de dano; JPD reduz pela metade.",
                "source": "Fixture",
            },
            {
                "id": "divina-bencao",
                "name": "Bênção",
                "tradition": "divina",
                "circle": 1,
                "school": "Encantamento",
                "alcance": "10 metros",
                "duracao": "1 hora",
                "description": "Aliados recebem um bônus narrativo.",
                "source": "Fixture",
            },
        ],
    }


def _fixture_items():
    return {
        "schema_version": 1,
        "catalog": {"id": "fixture-items", "title": "Fixture OD1", "edition": "1a edição"},
        "count": 7,
        "items": [
            {
                "id": "arma-espada",
                "name": "Espada",
                "category": "arma-corpo",
                "description": "Arma marcial.",
                "preco": "10 PO",
                "preco_po": 10.0,
                "peso": "2 kg",
                "source": "Fixture",
                "negociavel": True,
            },
            {
                "id": "item-classe-kit",
                "name": "Kit de Ingredientes",
                "category": "item-classe",
                "description": "Item de Alquimista. Usos: 3.",
                "preco": "12 PO",
                "preco_po": 12.0,
                "peso": "1 kg",
                "source": "Fixture",
                "negociavel": True,
            },
            {
                "id": "propriedades-cavalo",
                "name": "Cavalo de montaria",
                "category": "propriedades",
                "description": "Adulto, para viagem.",
                "preco": "13 PO",
                "preco_po": 13.0,
                "peso": None,
                "source": "Fixture",
                "negociavel": True,
            },
            {
                "id": "propriedades-casa",
                "name": "Casa pobre",
                "category": "propriedades",
                "description": "1 cômodo.",
                "preco": "200 PO",
                "preco_po": 200.0,
                "peso": None,
                "source": "Fixture",
                "negociavel": True,
            },
            {
                "id": "hospedagem-quarto",
                "name": "Quarto individual",
                "category": "hospedagem",
                "description": "Uma pessoa.",
                "preco": "1 PP",
                "preco_po": 0.1,
                "peso": None,
                "source": "Fixture",
                "negociavel": False,
            },
            {
                "id": "item-magico-anel",
                "name": "Anel aríete",
                "category": "item-magico",
                "description": "Efeito mágico.",
                "preco": "500 PO",
                "preco_po": 500.0,
                "peso": "0,1 kg",
                "source": "Fixture",
                "negociavel": True,
            },
            {
                "id": "tabela-saque-t9-2-efeito-1",
                "name": "Efeito 1",
                "category": "tabela-saque-t9-2",
                "description": "1d100 1-8.",
                "preco": "—",
                "preco_po": None,
                "peso": None,
                "source": "Fixture",
                "negociavel": False,
            },
        ],
    }


class CatalogReadinessFixtureTests(TestCase):
    def setUp(self):
        self.report = build_catalog_readiness(
            monster_payload=_fixture_monsters(),
            spell_payload=_fixture_spells(),
            item_payload=_fixture_items(),
        )
        self.monsters = {entry["id"]: entry for entry in self.report["monsters"]}
        self.spells = {entry["id"]: entry for entry in self.report["spells"]}
        self.items = {entry["id"]: entry for entry in self.report["items"]}

    def test_counts_and_editions_come_from_catalogs(self):
        self.assertEqual(self.report["counts"]["monsters"]["total"], 2)
        self.assertEqual(self.report["counts"]["spells"]["total"], 5)
        self.assertEqual(self.report["counts"]["items"]["total"], 7)
        self.assertEqual(self.report["catalogs"]["monsters"]["edition"], "OD2")
        self.assertEqual(self.report["catalogs"]["items"]["edition"], "OD1")
        self.assertEqual(self.report["automation_status"], "not_certified")

    def test_monster_movement_attacks_and_missing_data(self):
        grifo = self.monsters["grifo-fixture"]
        self.assertTrue(grifo["movement"]["terrestrial"]["declared"])
        self.assertEqual(grifo["movement"]["terrestrial"]["value"], 9)
        self.assertTrue(grifo["movement"]["fly"]["declared"])
        self.assertEqual(grifo["movement"]["fly"]["value"], 21)
        self.assertTrue(grifo["attack_kinds"]["bite"])
        self.assertTrue(grifo["attack_kinds"]["claws"])
        self.assertTrue(grifo["image"]["present"])
        self.assertTrue(grifo["configuration_complete"])

        dragao = self.monsters["dragao-fixture"]
        self.assertIn("imagem_ausente", dragao["gaps"])
        self.assertIn("sem_ataques_cadastrados", dragao["gaps"])
        self.assertIn("movimento_ilegivel", dragao["gaps"])
        self.assertIn("baforada_sem_dano_literal", dragao["gaps"])
        self.assertIn("baforada_sem_jp", dragao["gaps"])
        self.assertIn("baforada_sem_alcance_area", dragao["gaps"])
        self.assertIn("conjuracao_sem_repertorio", dragao["gaps"])
        self.assertFalse(dragao["configuration_complete"])
        entry = dragao["spellcasting"]["entries"][0]
        self.assertEqual(entry["caster_level"], 7)
        self.assertEqual(entry["named_spells"], [])

    def test_spell_families_and_handler_gaps(self):
        self.assertEqual(self.spells["arcana-alarme"]["family"], "proprio")
        self.assertEqual(self.spells["arcana-toque"]["family"], "toque")
        self.assertEqual(self.spells["arcana-multi"]["family"], "multi_alvo")
        self.assertEqual(self.spells["arcana-cone"]["family"], "area_linha_cone")
        self.assertEqual(self.spells["divina-bencao"]["family"], "passiva_assistida")
        self.assertIn("area_textual_nao_estruturada", self.spells["arcana-cone"]["gaps"])
        self.assertEqual(self.spells["arcana-alarme"]["handler"]["kind"], "manual_only")
        self.assertEqual(self.spells["arcana-cone"]["handler"]["kind"], "spell_engine_generic")
        for spell in self.spells.values():
            self.assertEqual(spell["handler"]["automation_status"], "not_certified")
            self.assertFalse(spell["cost"]["declared"])
            self.assertFalse(spell["recharge"]["declared"])

    def test_item_buckets_and_table_fragments(self):
        self.assertEqual(self.items["arma-espada"]["bucket"], "equipamento")
        self.assertEqual(self.items["item-classe-kit"]["bucket"], "consumivel")
        self.assertEqual(self.items["propriedades-cavalo"]["bucket"], "transporte_montaria")
        self.assertEqual(self.items["propriedades-casa"]["bucket"], "mercadoria")
        self.assertEqual(self.items["hospedagem-quarto"]["bucket"], "servico")
        self.assertEqual(self.items["item-magico-anel"]["bucket"], "item_magico")
        self.assertFalse(self.items["tabela-saque-t9-2-efeito-1"]["concrete"])
        self.assertIn(
            "entrada_de_tabela_nao_concreta",
            self.items["tabela-saque-t9-2-efeito-1"]["gaps"],
        )
        self.assertTrue(self.items["arma-espada"]["distribution_hints"])


class CatalogReadinessRealLoaderTests(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.report = build_catalog_readiness()
        cls.monsters = {entry["id"]: entry for entry in cls.report["monsters"]}

    def test_real_catalog_totals(self):
        self.assertEqual(self.report["counts"]["monsters"]["total"], 255)
        self.assertEqual(self.report["counts"]["spells"]["total"], 854)
        self.assertEqual(self.report["counts"]["items"]["total"], 329)
        self.assertEqual(self.report["catalogs"]["monsters"]["edition"], "OD2")
        self.assertEqual(self.report["catalogs"]["spells"]["edition"], "OD2")
        self.assertEqual(self.report["catalogs"]["items"]["edition"], "OD1")

    def test_highlighted_monsters_are_inventoried_without_inventing_spells(self):
        self.assertEqual(self.report["highlights"]["monster_ids"], ["grifo", "dragao-dourado"])
        grifo = self.monsters["grifo"]
        dragao = self.monsters["dragao-dourado"]
        self.assertTrue(grifo["attack_kinds"]["bite"])
        self.assertTrue(grifo["attack_kinds"]["claws"])
        self.assertFalse(grifo["spellcasting"]["present"])
        self.assertTrue(dragao["spellcasting"]["present"])
        entry = dragao["spellcasting"]["entries"][0]
        self.assertEqual(entry["caster_level"], 7)
        self.assertEqual(entry["named_spells"], [])
        self.assertIn("conjuracao_sem_repertorio", dragao["gaps"])
        self.assertTrue(dragao["breath_weapons"])
        self.assertEqual(dragao["breath_weapons"][0]["save"], "JPD")

    def test_real_lists_are_complete(self):
        self.assertEqual(len(self.report["monsters"]), 255)
        self.assertEqual(len(self.report["spells"]), 854)
        self.assertEqual(len(self.report["items"]), 329)
