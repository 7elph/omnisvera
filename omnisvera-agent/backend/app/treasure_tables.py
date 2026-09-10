from __future__ import annotations

from typing import Any


SOURCE = {
    "title": "Old Dragon 2 SRD - Capítulo 9: Mestrando - Tabela 9.5",
    "url": "https://olddragon.com.br/livros/srd/capitulos/mestrando",
    "license": "CC BY-SA 4.0",
}


# Old Dragon 2 SRD, Livro I, tabela 9.5.  A entrada descreve apenas a
# composição do tesouro; equipamentos, objetos e itens mágicos permanecem
# identificáveis/editáveis pelo Mestre antes da distribuição.
def reward(kind: str, formula: str, *, chance: int = 6, label: str | None = None) -> dict[str, Any]:
    return {"kind": kind, "formula": formula, "chance": chance, "label": label}


TREASURE_TABLES: dict[str, dict[str, Any]] = {
    "A": {"scope": "lair", "quick": "12.000 PO", "rewards": [reward("po", "2d6*1000", chance=2), reward("pp", "1d6*1000", chance=2), reward("pc", "1d6*1000", chance=1), reward("gem", "6d6", chance=3), reward("valuable", "6d6", chance=3), reward("magic", "3", chance=2, label="Item mágico (qualquer)")]},
    "B": {"scope": "lair", "quick": "1.400 PO", "rewards": [reward("po", "1d3*1000", chance=1), reward("pp", "1d6*1000", chance=1), reward("pc", "1d8*1000", chance=3), reward("gem", "1d6", chance=1), reward("valuable", "1d6", chance=1), reward("magic", "1", chance=1, label="Arma mágica")]},
    "C": {"scope": "lair", "quick": "650 PO", "rewards": [reward("pp", "1d4*1000", chance=2), reward("pc", "1d12*1000", chance=2), reward("gem", "1d4", chance=1), reward("valuable", "1d4", chance=1), reward("magic", "2", chance=1, label="Item mágico (qualquer)")]},
    "D": {"scope": "lair", "quick": "3.400 PO", "rewards": [reward("po", "1d6*1000", chance=3), reward("pp", "1d12*1000", chance=1), reward("pc", "1d8*1000", chance=1), reward("gem", "1d8", chance=2), reward("valuable", "1d8", chance=2), reward("magic", "2", chance=1, label="Item mágico (qualquer)"), reward("magic", "1", chance=1, label="Poção mágica")]},
    "E": {"scope": "lair", "quick": "1.800 PO", "rewards": [reward("po", "1d8*1000", chance=1), reward("pp", "1d12*1000", chance=2), reward("pc", "1d10*1000", chance=1), reward("gem", "1d10", chance=1), reward("valuable", "1d10", chance=1), reward("magic", "3", chance=1, label="Item mágico (qualquer)"), reward("magic", "1", chance=1, label="Pergaminho mágico")]},
    "F": {"scope": "lair", "quick": "4.000 PO", "rewards": [reward("po", "1d12*1000", chance=2), reward("pp", "2d10*1000", chance=1), reward("gem", "2d12", chance=1), reward("valuable", "1d12", chance=1), reward("magic", "3", chance=2, label="Item mágico (não arma)"), reward("magic", "1", chance=2, label="Poção mágica"), reward("magic", "1", chance=2, label="Pergaminho mágico")]},
    "G": {"scope": "lair", "quick": "14.000 PO", "rewards": [reward("po", "10d4*1000", chance=3), reward("gem", "3d6", chance=1), reward("valuable", "1d10", chance=1), reward("magic", "4", chance=2, label="Item mágico (qualquer)"), reward("magic", "1", chance=2, label="Pergaminho mágico")]},
    "H": {"scope": "lair", "quick": "27.000 PO", "rewards": [reward("po", "10d6*1000", chance=3), reward("pp", "1d10*1000", chance=3), reward("pc", "3d8*1000", chance=1), reward("gem", "1d10", chance=3), reward("valuable", "10d4", chance=3), reward("magic", "4", chance=1, label="Item mágico (qualquer)"), reward("magic", "1", chance=1, label="Poção mágica"), reward("magic", "1", chance=1, label="Pergaminho mágico")]},
    "I": {"scope": "lair", "quick": "2.800 PO", "rewards": [reward("gem", "2d6", chance=3), reward("valuable", "2d6", chance=3), reward("magic", "1", chance=1, label="Item mágico (qualquer)")]},
    "J": {"scope": "lair", "quick": "25 PO", "rewards": [reward("pp", "1d3*1000", chance=1), reward("pc", "1d4*1000", chance=1)]},
    "K": {"scope": "lair", "quick": "15 PO", "rewards": [reward("pp", "1d2*1000", chance=1)]},
    "L": {"scope": "lair", "quick": "200 PO", "rewards": [reward("gem", "1d4", chance=3)]},
    "M": {"scope": "lair", "quick": "40.000 PO", "rewards": [reward("po", "8d10*1000", chance=5), reward("pp", "10d6*1000", chance=3), reward("gem", "5d4", chance=3), reward("valuable", "2d6", chance=2)]},
    "N": {"scope": "lair", "quick": "-", "rewards": [reward("magic", "2d4", chance=2, label="Poção mágica")]},
    "O": {"scope": "lair", "quick": "-", "rewards": [reward("magic", "1d4", chance=3, label="Poção mágica")]},
    "P": {"scope": "carried", "quick": "1 PP", "rewards": [reward("pc", "3d8")]},
    "Q": {"scope": "carried", "quick": "1 PO", "rewards": [reward("pp", "3d6")]},
    "R": {"scope": "carried", "quick": "3 PO", "rewards": [reward("po", "1d6"), reward("equipment", "1", chance=2, label="Equipamento") ]},
    "S": {"scope": "carried", "quick": "5 PO", "rewards": [reward("po", "2d4"), reward("equipment", "1", chance=2, label="Equipamento")]},
    "T": {"scope": "carried", "quick": "17 PO", "rewards": [reward("po", "1d6*5"), reward("equipment", "2", chance=2, label="Equipamento")]},
    "U": {"scope": "carried", "quick": "90 PO", "rewards": [reward("po", "1d10", chance=1), reward("pp", "1d10", chance=1), reward("pc", "1d10", chance=1), reward("equipment", "1d4", chance=1, label="Equipamento"), reward("valuable", "1", chance=1), reward("magic", "1", chance=1, label="Item mágico (qualquer)")]},
    "V": {"scope": "carried", "quick": "175 PO", "rewards": [reward("po", "1d10", chance=2), reward("pp", "1d10", chance=2), reward("equipment", "1d6", chance=1, label="Equipamento"), reward("valuable", "1d4", chance=1), reward("magic", "1", chance=2, label="Item mágico (qualquer)")]},
}


REWARD_LABELS = {
    "po": "Peça de Ouro (PO)",
    "pp": "Peça de Prata (PP)",
    "pc": "Peça de Cobre (PC)",
    "gem": "Gema não avaliada",
    "valuable": "Objeto de valor não avaliado",
    "equipment": "Equipamento",
    "magic": "Item mágico não identificado",
}


EQUIPMENT_TABLE = {
    2: {"common": "Símbolo Divino", "uncommon": "Aljava (1d6 flechas)", "rare": "Porta Mapas"},
    3: {"common": "Saco de Dormir", "uncommon": "Martelo", "rare": "Pena e Tinta"},
    4: {"common": "Ração de Viagem (1d4)", "uncommon": "Óleo", "rare": "Corrente"},
    5: {"common": "Pederneira", "uncommon": "Água Benta", "rare": "Algema"},
    6: {"common": "Corda de Cânhamo (15m)", "uncommon": "Pá ou Picareta", "rare": "Giz"},
    7: {"common": "Tochas (1d4)", "uncommon": "Arpéu", "rare": "Caixa Pequena"},
    8: {"common": "Mochila", "uncommon": "Lamparina", "rare": "Coberta de Inverno"},
    9: {"common": "Odre", "uncommon": "Vela (1d4)", "rare": "Espelho"},
    10: {"common": "Saco de Estopa", "uncommon": "Cravos ou Ganchos (1d4)", "rare": "Cadeado"},
    11: {"common": "Traje de Exploração", "uncommon": "Traje de Inverno", "rare": "Traje Nobre"},
    12: {"common": "Ferramenta de Ladrão", "uncommon": "Lanterna Furta-Fogo", "rare": "Rede"},
}


VALUABLE_TABLE = {
    "merchandise": {2: "Peles de Animais Raros", 3: "Peles de Animais Raros", 4: "Objetos de Marfim", 5: "Objetos de Marfim", 6: "Sacas de Especiaria", 7: "Sacas de Especiaria", 8: "Sacas de Incenso", 9: "Sacas de Incenso", 10: "Tecidos Nobres", 11: "Tecidos Nobres", 12: "Metros de Fina Seda"},
    "dishes": {2: "Objetos de Vidro Soprado", 3: "Objetos de Vidro Soprado", 4: "Copos de Vidro e com Prata", 5: "Copos de Vidro e com Prata", 6: "Baixelas de Louça", 7: "Baixelas de Louça", 8: "Baixelas de Porcelana com ouro", 9: "Baixelas de Porcelana com ouro", 10: "Vaso de Porcelana", 11: "Vaso de Porcelana", 12: "Cálices de Vidro com pedraria"},
    "utensils": {2: "Religiosos de Cobre", 3: "Religiosos de Cobre", 4: "Talheres de Prata", 5: "Talheres de Prata", 6: "Candelabros de Prata", 7: "Candelabros de Prata", 8: "Cutelaria Fina", 9: "Cutelaria Fina", 10: "Cálices de Ouro", 11: "Cálices de Ouro", 12: "Religiosos de Ouro"},
    "art": {2: "Móveis com Marchetaria", 3: "Móveis com Marchetaria", 4: "Tapeçaria Fina", 5: "Tapeçaria Fina", 6: "Livro Raro", 7: "Livro Raro", 8: "Escultura", 9: "Escultura", 10: "Tela Pintada", 11: "Tela Pintada", 12: "Estatueta em Bronze"},
    "jewelry": {2: "Cordão de Prata", 3: "Cordão de Prata", 4: "Brincos de Pérola", 5: "Brincos de Pérola", 6: "Bracelete de Prata", 7: "Bracelete de Prata", 8: "Pingente de Pedraria", 9: "Pingente de Pedraria", 10: "Camafeu de Ouro", 11: "Camafeu de Ouro", 12: "Tiara com Pedraria"},
}


GEM_TABLE = {
    2: ("Gema preciosa", 500), 3: ("Gema preciosa", 500),
    4: ("Gema ornamental", 50), 5: ("Gema ornamental", 50),
    6: ("Gema decorativa", 10), 7: ("Gema decorativa", 10),
    8: ("Gema decorativa", 10), 9: ("Gema decorativa", 10),
    10: ("Gema semipreciosa", 100), 11: ("Gema semipreciosa", 100),
    12: ("Joia", 1000),
}
