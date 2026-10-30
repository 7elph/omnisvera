from __future__ import annotations

import unittest

from app.spell_catalog import get_catalog_spell, list_spell_catalog, load_spell_catalog
from app.ability_catalog import list_ability_catalog, load_ability_catalog
from app.item_catalog import list_item_catalog, load_item_catalog


class CompendiumCatalogTests(unittest.TestCase):
    def test_spell_catalog_has_arcana_and_divina(self) -> None:
        catalog = load_spell_catalog()
        self.assertGreaterEqual(catalog["count"], 800)
        self.assertEqual(catalog["count"], len(catalog["spells"]))
        traditions = {spell["tradition"] for spell in catalog["spells"]}
        self.assertEqual(traditions, {"arcana", "divina"})

    def test_bola_de_fogo_preserves_mechanics(self) -> None:
        spell = get_catalog_spell("arcana-bola-de-fogo")
        self.assertIsNotNone(spell)
        assert spell is not None
        self.assertEqual(spell["circle"], 3)
        self.assertEqual(spell["school"], "Evocação")
        self.assertIn("10 metros", spell["alcance"])
        self.assertIn("JPD", spell["jogada_protecao"])

    def test_spell_search_is_accent_insensitive(self) -> None:
        result = list_spell_catalog(query="area escorregadia")
        self.assertTrue(any(spell["name"] == "Área Escorregadia" for spell in result["spells"]))

    def test_spell_filter_by_tradition_and_circle(self) -> None:
        result = list_spell_catalog(tradition="divina", circle=1)
        self.assertGreater(result["count"], 30)
        self.assertTrue(all(spell["tradition"] == "divina" and spell["circle"] == 1 for spell in result["spells"]))

    def test_ability_catalog_has_all_specialists(self) -> None:
        catalog = load_ability_catalog()
        self.assertGreaterEqual(catalog["count"], 40)
        specs = {ability["spec"] for ability in catalog["abilities"]}
        for expected in ["Abjurante", "Adivinho", "Arquimago", "Diabolista", "Elementalista", "Teleportador"]:
            self.assertIn(expected, specs)

    def test_ability_search_finds_cronomancer(self) -> None:
        result = list_ability_catalog(query="voltar no tempo")
        self.assertTrue(any(ability["spec"] == "Cronomancer" for ability in result["abilities"]))

    def test_item_catalog_has_weapons_and_magic(self) -> None:
        catalog = load_item_catalog()
        self.assertGreaterEqual(catalog["count"], 300)
        categories = {item["category"] for item in catalog["items"]}
        self.assertIn("arma-corpo", categories)
        self.assertIn("item-magico", categories)
        self.assertIn("protecao", categories)
        self.assertIn("item-classe", categories)

    def test_item_search_finds_magic_and_mundane(self) -> None:
        magic = list_item_catalog(query="tapete voador")
        self.assertTrue(any(item["name"] == "Tapete voador" for item in magic["items"]))
        mundane = list_item_catalog(query="espada longa")
        self.assertTrue(any("Espada longa" in item["name"] for item in mundane["items"]))

    def test_item_filter_by_category(self) -> None:
        result = list_item_catalog(category="item-magico")
        self.assertGreater(result["count"], 30)
        self.assertTrue(all(item["category"] == "item-magico" for item in result["items"]))

    def test_expansao_itens_weapons_armor_and_magic(self) -> None:
        catalog = load_item_catalog()
        by_name = {item["name"]: item for item in catalog["items"]}
        katana = by_name.get("Katana")
        self.assertIsNotNone(katana)
        assert katana is not None
        self.assertEqual(katana["preco"], "50 PO")
        self.assertEqual(katana.get("dano"), "1D8")
        yoroi = by_name.get("Ō-Yoroi")
        self.assertIsNotNone(yoroi)
        assert yoroi is not None
        self.assertEqual(yoroi["category"], "protecao")
        adamas = by_name.get("Espada Adamas")
        self.assertIsNotNone(adamas)
        assert adamas is not None
        self.assertEqual(adamas.get("alinhamento"), "Neutra")
        shuko = by_name.get("Shuko (Garras para escalada)")
        self.assertIsNotNone(shuko)
        assert shuko is not None
        self.assertEqual(shuko.get("classe"), "Ninja")
        sources = " ".join(str(source) for source in catalog["catalog"]["sources"])
        self.assertIn("Expans", sources)


if __name__ == "__main__":
    unittest.main()
