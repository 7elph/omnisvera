from __future__ import annotations

import json
import sqlite3
import unittest
from contextlib import closing
from pathlib import Path
from tempfile import TemporaryDirectory

from app.merchant import (add_stock, buy, create_merchant, haggle, list_merchants,
                          purse_copper, remove_stock, sell, split_copper)
from app.player_inventory import list_inventory, upsert_inventory


class MerchantTests(unittest.TestCase):
    def setUp(self) -> None:
        folder = TemporaryDirectory()
        self.addCleanup(folder.cleanup)
        self.db = Path(folder.name) / "merchant.db"
        from app.character_play import init_character_play
        from app.character_creation import init_character_creation
        from app.dice_rolls import init_dice_rolls
        from app.session_workspace import init_session_workspace
        from app.session_ledger import init_session_ledger
        init_character_play(self.db)
        init_character_creation(self.db)
        init_dice_rolls(self.db)
        init_session_workspace(self.db)
        init_session_ledger(self.db)
        with closing(sqlite3.connect(self.db)) as connection, connection:
            connection.execute("INSERT INTO character_states(profile_id, state_json, updated_at) VALUES('vezemir', ?, 'now')",
                               (json.dumps({"current_hp": 10, "copper_coins": 5, "silver_coins": 3, "coins": 12, "platinum_coins": 0}),))
            sheet = {"attributes": {"charisma": 16}, "character_class": {"saving_throw": 14}}
            connection.execute("INSERT INTO character_sheets(profile_id, character_path, character_title, data_json, updated_at) VALUES('vezemir', 'p', 'Vezemir', ?, 'now')", (json.dumps(sheet),))
            connection.execute("INSERT INTO character_definition_overrides VALUES('vezemir', '{}', 'now')")
        self.merchant = create_merchant(self.db, name="Balcão do Anão", location="Maré Baixa")

    def purse(self) -> dict:
        with closing(sqlite3.connect(self.db)) as connection:
            return json.loads(connection.execute("SELECT state_json FROM character_states WHERE profile_id='vezemir'").fetchone()[0])

    def test_price_extraction_covers_tradable_goods(self) -> None:
        from app.item_catalog import load_item_catalog
        items = load_item_catalog()["items"]
        by_category: dict[str, list] = {}
        for item in items:
            by_category.setdefault(item["category"], []).append(item)
        for category in ("arma-corpo", "protecao", "item-classe", "kit-basico", "kit-explorador",
                         "kit-ladrao", "propriedades", "especiais", "hospedagem", "servico-magico"):
            missing = [item["name"] for item in by_category[category] if item.get("preco_po") is None]
            self.assertEqual(missing, [], category)
        missing_ranged = [item["name"] for item in by_category["arma-distancia"] if item.get("preco_po") is None]
        self.assertEqual(missing_ranged, [])  # flecha improvisada: 0 PO de mesa
        mesa = [item for item in items if item.get("preco_origem") == "mesa"]
        self.assertGreater(len(mesa), 30)  # magias sem preço no livro ganharam preço de mesa
        tapete = next(item for item in items if item["name"] == "Tapete voador")
        self.assertEqual((tapete["preco_po"], tapete["preco_origem"]), (8000, "mesa"))

    def test_stock_requires_price_for_non_goods(self) -> None:
        with self.assertRaises(ValueError):
            add_stock(self.db, merchant_id=self.merchant["id"],
                      compendium_item_id="tabela-saque-t9-2-arma-ordeira-1", quantity=1)
        line = add_stock(self.db, merchant_id=self.merchant["id"], compendium_item_id="item-magico-tapete-voador",
                         quantity=1)
        self.assertEqual(line["price_po"], 8000)  # preço de mesa
        line2 = add_stock(self.db, merchant_id=self.merchant["id"], compendium_item_id="item-magico-tapete-voador",
                          quantity=1, price_override_po=5000.0)
        self.assertEqual(line2["price_po"], 5000.0)

    def test_buy_deducts_purse_and_adds_inventory(self) -> None:
        line = add_stock(self.db, merchant_id=self.merchant["id"], compendium_item_id="arma-corpo-espada-longa", quantity=2)
        self.assertEqual(line["price_po"], 10.0)
        before = purse_copper(self.purse())
        result = buy(self.db, request_id='merchant-buy-001', merchant_id=self.merchant["id"], stock_id=line["id"], character_id="vezemir",
                     quantity=1, final_price_po=10.0, expected_purse={field: self.purse().get(field) or 0 for field in ("copper_coins", "silver_coins", "coins", "platinum_coins")})
        self.assertEqual(result["paid_po"], 10.0)
        self.assertEqual(purse_copper(self.purse()), before - 1000)
        inventory = list_inventory(self.db, "vezemir")
        self.assertTrue(any(item["item_title"] == "Espada longa" for item in inventory))
        merchants = list_merchants(self.db)
        self.assertEqual(merchants[0]["stock"][0]["quantity"], 1)

    def test_buy_rejects_insufficient_funds_and_stale_purse(self) -> None:
        line = add_stock(self.db, merchant_id=self.merchant["id"], compendium_item_id="arma-corpo-espada-longa", quantity=5)
        with self.assertRaises(ValueError):
            buy(self.db, request_id='merchant-buy-insufficient', merchant_id=self.merchant["id"], stock_id=line["id"], character_id="vezemir",
                quantity=5, final_price_po=10.0)
        with self.assertRaises(ValueError):
            buy(self.db, request_id='merchant-buy-stale', merchant_id=self.merchant["id"], stock_id=line["id"], character_id="vezemir",
                quantity=1, final_price_po=10.0, expected_purse={"copper_coins": 0, "silver_coins": 0, "coins": 0, "platinum_coins": 0})

    def test_haggle_tiers_follow_charisma_roll(self) -> None:
        result = haggle(self.db, character_id="vezemir", base_price_po=100.0, roll_mode="physical", d20=20)
        self.assertEqual(result["adjusted_price_po"], 80.0)
        self.assertEqual(result["modifier"], 3)
        low = haggle(self.db, character_id="vezemir", base_price_po=100.0, roll_mode="physical", d20=1)
        self.assertEqual(low["adjusted_price_po"], 110.0)

    def test_sell_pays_and_removes_inventory(self) -> None:
        item_path='compendium:arma-corpo-espada-longa'
        upsert_inventory(self.db, profile_id="vezemir", item_path=item_path, item_title="Espada longa", quantity=2, equipped=False, notes=None)
        before = purse_copper(self.purse())
        result = sell(self.db, request_id='merchant-sell-001', merchant_id=self.merchant["id"], character_id="vezemir", item_path=item_path,
                      quantity=1, unit_price_po=1.0)
        self.assertEqual(result["received_po"], 1.0)
        self.assertEqual(purse_copper(self.purse()), before + 100)
        remaining = next(item for item in list_inventory(self.db, "vezemir", include_empty=True) if item["item_path"] == item_path)
        self.assertEqual(remaining["quantity"], 1)

    def test_purse_split_round_trips(self) -> None:
        self.assertEqual(split_copper(12345), {"platinum_coins": 1, "coins": 23, "silver_coins": 4, "copper_coins": 5})

    def test_transaction_change_preserves_denominations_and_total(self):
        from app.merchant import transaction_purse
        initial = dict(coins=105, silver_coins=25, copper_coins=0, platinum_coins=0)
        self.assertEqual(transaction_purse(initial, 10700), {**initial, 'silver_coins':20})
        for state in [initial, dict(platinum_coins=2), dict(coins=2, silver_coins=1, copper_coins=8)]:
            total = purse_copper(state)
            for balance in range(0, total+201, 37):
                after = transaction_purse(state, balance)
                self.assertEqual(purse_copper(after), balance)
                self.assertTrue(all(v >= 0 for v in after.values()))
                self.assertLessEqual(after['platinum_coins'], state.get('platinum_coins', 0))
        self.assertEqual(transaction_purse(dict(coins=1), 95), dict(coins=0,silver_coins=9,copper_coins=5,platinum_coins=0))
        self.assertEqual(transaction_purse(initial, purse_copper(initial)+13), {**initial, 'silver_coins':26,'copper_coins':3})

    def test_remove_stock(self) -> None:
        line = add_stock(self.db, merchant_id=self.merchant["id"], compendium_item_id="arma-corpo-espada-longa", quantity=1)
        remove_stock(self.db, stock_id=line["id"])
        self.assertEqual(list_merchants(self.db)[0]["stock"], [])


if __name__ == "__main__":
    unittest.main()
