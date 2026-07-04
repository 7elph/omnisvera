from __future__ import annotations

import re
import unicodedata
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ITEMS = ROOT / "Items"


def slug(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    ascii_text = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    ascii_text = ascii_text.lower()
    ascii_text = re.sub(r"[^a-z0-9]+", "-", ascii_text).strip("-")
    return ascii_text or "item"


def yaml_scalar(value) -> str:
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value).replace(",", ".")
    text = str(value).replace("\\", "\\\\").replace('"', '\\"')
    return f'"{text}"'


def yaml_frontmatter(data: dict) -> str:
    lines = ["---"]
    for key, value in data.items():
        if value is None:
            continue
        if isinstance(value, list):
            lines.append(f"{key}:")
            if value:
                for item in value:
                    lines.append(f"  - {yaml_scalar(item)}")
            else:
                lines.append("  []")
        else:
            lines.append(f"{key}: {yaml_scalar(value)}")
    lines.append("---")
    return "\n".join(lines)


ORIGINS = {
    "origem-vezemir": {
        "character": "[[Vezemir]]",
        "chapter": "[[00 - O Bastardo de Ferro]]",
        "label": "linha de frente, armas pesadas, escudos, armaduras e logística militar",
    },
    "origem-varkh": {
        "character": "[[Varkh Nimalis]]",
        "chapter": "[[00 - O Corvo da Maré Baixa]]",
        "label": "infiltração urbana, ferramentas, alquimia de rua, arcos curtos e lâminas discretas",
    },
    "origem-raziel": {
        "character": "[[Raziel]]",
        "chapter": "[[00 - As Crônicas de Névoa de Sangue]]",
        "label": "executor sombrio, lâminas, prata, anti-imortais e recursos contra criaturas sobrenaturais",
    },
    "capitulo01": {
        "character": "grupo inicial",
        "chapter": "[[01 - Ecos do Mundo Perdido]]",
        "label": "catálogo comum para compras antes e durante o primeiro capítulo coletivo",
    },
}


STORE_BY_FAMILY = {
    "Armas": "Armeiros, caravanas armadas, guarda local e mercados grandes de [[Nimalis]].",
    "Proteção": "Armeiros, ferreiros, quartéis, escoltas de caravana e encomendas em cidades maiores.",
    "Kits e ferramentas": "Empórios, docas, armazéns de estrada, oficinas e mercados urbanos.",
    "Alquimia e especiais": "[[O Frasco Afogado]], boticários, alquimistas de rua, contrabandistas e templos, conforme o item.",
    "Propriedades e montarias": "Corretores, estábulos, guildas mercantes, nobreza local e autoridades da Coroa.",
    "Hospedagem e serviços": "Estalagens, tavernas, estábulos, casas de banho e cozinhas de estrada.",
    "Materiais e magia": "Artesãos especializados, templos, círculos arcanos e fornecedores raros.",
}


def default_chapters(origin_fit: list[str]) -> list[str]:
    chapters = ["01 - Ecos do Mundo Perdido"]
    if "origem-vezemir" in origin_fit:
        chapters.append("00 - O Bastardo de Ferro")
    if "origem-varkh" in origin_fit:
        chapters.append("00 - O Corvo da Maré Baixa")
    if "origem-raziel" in origin_fit:
        chapters.append("00 - As Crônicas de Névoa de Sangue")
    seen = []
    for chapter in chapters:
        if chapter not in seen:
            seen.append(chapter)
    return seen


def origin_block(origin_fit: list[str]) -> str:
    if not origin_fit:
        origin_fit = ["capitulo01"]
    lines = []
    for key in origin_fit:
        origin = ORIGINS.get(key)
        if not origin:
            continue
        lines.append(
            f"- **{origin['character']} / {origin['chapter']}:** {origin['label']}."
        )
    return "\n".join(lines) if lines else "- **Capítulo 01:** item comum de logística e compra."


def fmt_kg(value) -> str:
    if value is None:
        return "—"
    text = f"{value:g}".replace(".", ",")
    return f"{text} kg"


def table_row(label: str, value) -> str:
    if value is None or value == "":
        value = "—"
    return f"| {label} | {value} |"


def note_for_item(item: dict) -> str:
    name = item["name"]
    family = item["family"]
    category = item["category"]
    origin_fit = item.get("origin_fit") or ["capitulo01"]
    tags = [
        "item",
        "equipamento",
        "compra",
        "old-dragon",
        slug(family),
        slug(category),
    ]
    tags.extend(origin_fit)
    tags.extend(item.get("extra_tags", []))

    frontmatter = {
        "obsidianUIMode": "preview",
        "NoteIcon": "items",
        "NoteStatus": "Active",
        "type": "item",
        "status": "Ativo",
        "campaign_status": item.get("campaign_status", "Disponível para compra"),
        "visibility": item.get("visibility", "Jogadores"),
        "spoiler_level": "none",
        "gm_secret": False,
        "created_by": "Codex",
        "source_system": "Old Dragon 2e",
        "source_book": "Old Dragon - Livro Básico Aprimorado",
        "source_section": item.get("source_section", "Capítulo 5 - Equipamentos"),
        "source_table": item.get("source_table"),
        "item_family": family,
        "item_category": category,
        "item_type": item.get("item_type", category),
        "purchase_status": item.get("purchase_status", "Comprável"),
        "price": item.get("price"),
        "price_po": item.get("price_po"),
        "weight_kg": item.get("weight_kg"),
        "size_category": item.get("size"),
        "damage": item.get("damage"),
        "damage_type": item.get("damage_type"),
        "range": item.get("range"),
        "reload": item.get("reload"),
        "critical": item.get("critical"),
        "armor_bonus": item.get("armor_bonus"),
        "movement_penalty": item.get("movement_penalty"),
        "max_dex_bonus": item.get("max_dex_bonus"),
        "capacity": item.get("capacity"),
        "duration": item.get("duration"),
        "mechanical_effect": item.get("effect"),
        "base_item": item.get("base_item"),
        "aliases": item.get("aliases"),
        "kit_membership": item.get("kit_membership"),
        "origin_fit": origin_fit,
        "chapters": default_chapters(origin_fit),
        "hooks": item.get(
            "hooks",
            [
                "catálogo de compras",
                "equipamento inicial",
                "economia de mesa",
            ],
        ),
        "rumors": [],
        "tags": sorted(set(tags)),
    }

    purchase_rows = [
        table_row("Preço", item.get("price", "—")),
        table_row("Preço em PO", item.get("price_po", "—")),
        table_row("Peso", fmt_kg(item.get("weight_kg"))),
        table_row("Disponibilidade", item.get("purchase_status", "Comprável")),
        table_row("Onde comprar", STORE_BY_FAMILY.get(family, "Mercados, fornecedores e contatos locais.")),
    ]

    mechanics = [
        ("Tamanho", item.get("size")),
        ("Dano", item.get("damage")),
        ("Tipo de dano", item.get("damage_type")),
        ("Alcance", item.get("range")),
        ("Recarga", item.get("reload")),
        ("Crítico", item.get("critical")),
        ("Bônus de CA", item.get("armor_bonus")),
        ("Penalidade de movimento", item.get("movement_penalty")),
        ("Bônus máximo de DES", item.get("max_dex_bonus")),
        ("Capacidade", item.get("capacity")),
        ("Duração", item.get("duration")),
        ("Efeito", item.get("effect")),
        ("Item base", item.get("base_item")),
    ]
    mechanic_rows = [table_row(label, value) for label, value in mechanics if value not in (None, "")]

    components = item.get("components", [])
    component_block = ""
    if components:
        component_lines = "\n".join(f"- {component}" for component in components)
        component_block = f"\n## Componentes\n\n{component_lines}\n"

    related = item.get("related", [])
    related_links = ["[[Catálogo de Compras]]", "[[INDICE_DE_ITENS]]", "[[Regras de Compra e Equipamento]]"]
    related_links.extend(related)
    if item.get("kit_membership"):
        related_links.extend(item["kit_membership"])
    related_block = "\n".join(f"- {link}" for link in dict.fromkeys(related_links))

    note = f"""{yaml_frontmatter(frontmatter)}

# {name}

> [!world]- SINOPSE PÚBLICA
> {item.get("description", f"{name} é um item comum de compra em Earthropo, registrado para uso direto em mesa.")}

## Compra

| Campo | Valor |
| :-- | :-- |
{chr(10).join(purchase_rows)}

## Dados Mecânicos

| Campo | Valor |
| :-- | :-- |
{chr(10).join(mechanic_rows) if mechanic_rows else "| Regra | Sem regra mecânica direta além do preço, peso e uso narrativo. |"}
{component_block}
## Encaixe em Omnisvera

{origin_block(origin_fit)}

- **Uso inicial:** usar os valores de tabela como referência comum; versões excepcionais devem ter nota própria e liberação narrativa.
- **Compra em jogo:** {item.get("buy_note", STORE_BY_FAMILY.get(family, "Disponível conforme o mercado local."))}

## Relações

{related_block}

## Observações de Mesa

- Item registrado a partir do capítulo de equipamentos do livro-base anexado.
- Mantém função mundana no início da campanha, salvo decisão explícita do mestre.
- Pode receber variações culturais de [[Nimalis]], [[Leth'valora]] ou fornecedores ligados aos personagens, sem alterar preço base.
"""
    return note.rstrip() + "\n"


def add_item(items: list[dict], folder: str, **kwargs) -> None:
    kwargs["folder"] = folder
    items.append(kwargs)


CATALOG: list[dict] = []


def build_catalog() -> None:
    items = CATALOG

    ranged_folder = "01 Armas"
    melee_folder = "01 Armas"
    armor_folder = "02 Protecao"
    tools_folder = "03 Kits e Ferramentas"
    special_folder = "04 Alquimia e Especiais"
    property_folder = "05 Propriedades e Montarias"
    service_folder = "06 Hospedagem e Servicos"
    magic_folder = "07 Materiais e Magia"

    ranged = [
        ("Arco curto", "Arma à distância", "25 PO", 25, 0.5, "Pequena", "—", "—", "15/30", "Ação livre", None, ["origem-varkh"], "Arco leve usado para telhados, becos e disparos discretos; o dano vem da munição usada.", ["[[Flecha x20]]"]),
        ("Arco longo", "Arma à distância", "60 PO", 60, 1.5, "Média", "—", "—", "25/50", "Ação livre", None, ["origem-vezemir"], "Arco de maior alcance, comum entre caçadores, sentinelas e escoltas de estrada.", ["[[Flecha x20]]"]),
        ("Besta de mão", "Arma à distância", "30 PO", 30, 3.5, "Pequena", "—", "—", "20/40", "Ação de movimento", None, ["origem-varkh"], "Besta compacta para emboscadas, becos e defesa de curta distância.", []),
        ("Besta", "Arma à distância", "50 PO", 50, 4, "Média", "—", "—", "35/60", "Ação de movimento", None, ["capitulo01"], "Besta comum de guarda e caravana, lenta para recarregar, mas confiável.", []),
        ("Dardo x20", "Munição", "10 PO", 10, 1, "Pequena", "1d6", "Perfuração", "—", "—", None, ["origem-varkh"], "Conjunto de vinte dardos leves para arremesso, emboscadas e improviso.", []),
        ("Flecha x20", "Munição", "7 PO", 7, 1.5, "Pequena", "1d8", "Perfuração", "—", "—", None, ["origem-varkh"], "Conjunto de vinte flechas comuns para arcos.", ["[[Arco curto]]", "[[Arco longo]]"]),
        ("Flecha improvisada", "Munição", "—", None, 0.5, "Pequena", "1d6", "Perfuração", "—", "—", None, ["origem-varkh"], "Flecha de fabricação improvisada; serve quando não há munição adequada, mas não tem preço regular.", ["[[Arco curto]]", "[[Arco longo]]"]),
    ]
    for name, category, price, price_po, weight, size, damage, damage_type, range_, reload, critical, origin, description, related in ranged:
        add_item(
            items,
            ranged_folder,
            name=name,
            family="Armas",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            size=size,
            damage=damage,
            damage_type=damage_type,
            range=range_,
            reload=reload,
            critical=critical,
            origin_fit=origin,
            source_table="T5-2 - Armas à distância",
            description=description,
            related=related,
            purchase_status="Improvisado" if name == "Flecha improvisada" else "Comprável",
        )

    melee = [
        ("Adaga", "Pequena", "1d4", "Perfuração", "Arremesso 3/6", "x2", 0.5, "2 PO", 2, ["origem-varkh", "origem-raziel"], "Lâmina curta, discreta e fácil de esconder; útil para Varkh e como base mundana das adagas de Raziel.", ["[[Adagas de Espectro Fantasma]]"]),
        ("Alabarda", "Grande", "1d10", "Corte", "3", "x3", 7, "8 PO", 8, ["origem-vezemir"], "Arma de haste para manter inimigos à distância e receber investidas.", []),
        ("Azagaia", "Média", "1d10", "Perfuração", "Arremesso 6/9", "x3", 7, "10 PO", 10, ["origem-vezemir"], "Lança arremessável de guerra, útil para caçadas, patrulhas e combates de estrada.", []),
        ("Bordão", "Média", "1d6", "Impacto", "—", "x2", 1.5, "5 PP", 0.5, ["capitulo01"], "Bastão simples de viagem, defesa e apoio em exploração.", []),
        ("Cajado", "Média", "1d6", "Impacto", "—", "x2", 1.5, "5 PP", 0.5, ["capitulo01"], "Cajado comum para viajantes, eremitas e conjuradores sem arma marcial.", []),
        ("Chicote", "Grande", "1d2", "Corte", "6", "x2", 0.5, "1 PO", 1, ["origem-varkh"], "Arma de controle, mais útil para desarmar e derrubar do que para causar dano.", []),
        ("Cimitarra", "Média", "1d6", "Corte", "—", "19-20 x2", 1.5, "15 PO", 15, ["capitulo01"], "Lâmina curva de corte rápido, comum em estilos móveis de combate.", []),
        ("Espada bastarda", "Grande", "1d10", "Corte/Impacto", "—", "19-20 x2", 2.8, "12 PO", 12, ["origem-vezemir"], "Espada pesada entre arma comum e arma de campo, adequada a combatentes fortes.", []),
        ("Espada curta", "Pequena", "1d6", "Perfuração", "—", "x2", 1.5, "6 PO", 6, ["origem-varkh"], "Arma confiável para becos estreitos e lutas rápidas; uma das bases de treinamento de Varkh.", []),
        ("Espada larga", "Grande", "2d6", "Corte/Impacto", "—", "19-20 x2", 7, "50 PO", 50, ["origem-vezemir"], "Espada grande para guerreiros de linha de frente.", []),
        ("Espada longa", "Média", "1d8", "Corte", "—", "19-20 x2", 2, "10 PO", 10, ["origem-vezemir"], "Espada comum de soldados, guardas e aventureiros.", []),
        ("Falcione", "Grande", "2d4", "Corte", "—", "19-20 x2", 8, "75 PO", 75, ["origem-vezemir"], "Lâmina grande e curva, cara e voltada a golpes de corte amplo.", []),
        ("Foice de mão", "Pequena", "1d6", "Corte", "—", "x2", 1, "6 PO", 6, ["capitulo01"], "Ferramenta rural adaptada para combate simples.", []),
        ("Lança curta", "Pequena", "1d6", "Perfuração", "3", "x3", 1, "1 PO", 1, ["capitulo01"], "Lança leve para manter distância e preparar contra carga.", []),
        ("Lança longa", "Grande", "1d8", "Perfuração", "3", "x3", 9, "10 PO", 10, ["origem-vezemir"], "Lança pesada de formação, muito eficiente contra investidas.", []),
        ("Maça", "Média", "1d8", "Impacto", "—", "x2", 5, "6 PO", 6, ["origem-vezemir"], "Arma de impacto para enfrentar armaduras e ossos resistentes.", []),
        ("Machado", "Média", "1d6", "Corte/Impacto", "—", "x3", 2.5, "6 PO", 6, ["origem-vezemir"], "Machado comum de combate e trabalho pesado.", []),
        ("Machado de arremesso", "Pequena", "1d6", "Corte", "Arremesso 3/6", "x3", 2, "8 PO", 8, ["origem-vezemir"], "Machado pequeno para arremesso e combate de curta distância.", []),
        ("Machado de batalha", "Grande", "2d6", "Corte/Impacto", "—", "x3", 8, "12 PO", 12, ["origem-vezemir"], "Machado pesado de linha de frente; referência mecânica comum para Grisalma no início.", ["[[Grisalma]]"]),
        ("Mangual", "Média", "1d8", "Impacto/Perfuração", "—", "x2", 2, "8 PO", 8, ["origem-vezemir"], "Arma articulada útil para contornar escudos e desarmar.", []),
        ("Martelo", "Média", "1d6", "Impacto", "Arremesso 3/6", "x2", 3, "5 PO", 5, ["origem-vezemir"], "Martelo de combate simples, arremessável em curtas distâncias.", []),
        ("Martelo de batalha", "Grande", "2d4", "Impacto", "—", "x2", 10, "15 PO", 15, ["origem-vezemir"], "Martelo pesado para quebrar defesa e armadura.", []),
        ("Montante", "Grande", "2d6", "Corte/Impacto", "3", "19-20 x2", 10, "20 PO", 20, ["origem-vezemir"], "Espada enorme de alcance estendido, feita para controlar espaço.", []),
        ("Picareta", "Média", "1d6", "Perfuração", "—", "x4", 7, "8 PO", 8, ["capitulo01"], "Ferramenta pesada adaptada para perfurar armaduras e superfícies duras.", []),
        ("Porrete", "Média", "1d4", "Impacto", "—", "x2", 0.5, "1 PO", 1, ["capitulo01"], "Arma simples de madeira, barata e fácil de improvisar.", []),
        ("Sabre", "Pequena", "1d6", "Perfuração", "—", "19-20 x2", 1, "8 PP", 0.8, ["origem-varkh"], "Lâmina pequena e ágil, boa para combates urbanos e duelos rápidos.", []),
        ("Tridente", "Média", "1d8", "Perfuração", "3", "x2", 2, "10 PO", 10, ["capitulo01"], "Arma de haste curta, útil em ambientes costeiros e portuários.", []),
    ]
    for name, size, damage, damage_type, range_, critical, weight, price, price_po, origin, description, related in melee:
        add_item(
            items,
            melee_folder,
            name=name,
            family="Armas",
            category="Arma corpo a corpo",
            item_type="Arma corpo a corpo",
            price=price,
            price_po=price_po,
            weight_kg=weight,
            size=size,
            damage=damage,
            damage_type=damage_type,
            range=range_,
            critical=critical,
            origin_fit=origin,
            source_table="T5-2 - Armas corpo a corpo",
            description=description,
            related=related,
            effect="Preparada contra carga causa dano dobrado." if name in {"Alabarda", "Azagaia", "Lança curta", "Lança longa", "Tridente"} else (
                "+2 em manobras de desarmar e derrubar." if name == "Chicote" else (
                    "+2 em manobras de desarmar." if name == "Mangual" else None
                )
            ),
            aliases=["Bordão/cajado"] if name == "Bordão" else None,
        )

    protections = [
        ("Armadura acolchoada", "Armadura leve", "+1", "—", "—", 5, "5 PO", 5, ["capitulo01"], "Proteção acolchoada barata, leve e comum.", []),
        ("Armadura de couro", "Armadura leve", "+2", "—", "+6", 7, "20 PO", 20, ["origem-varkh", "origem-raziel"], "Armadura leve e flexível; boa base para furtividade e para o manto de Raziel.", ["[[Manto Primordial do Ancião]]"]),
        ("Armadura de couro batido", "Armadura leve", "+3", "—", "+6", 15, "25 PO", 25, ["origem-varkh", "origem-raziel"], "Couro endurecido para quem precisa de proteção sem armadura pesada.", ["[[Manto Primordial do Ancião]]"]),
        ("Armadura de placas", "Armadura pesada", "+6", "-2 metros", "+3", 13, "300 PO", 300, ["origem-vezemir"], "Armadura de placas para combatentes pesados e guardas de elite.", []),
        ("Armadura completa", "Armadura pesada", "+8", "-3 metros", "+1", 20, "2.000 PO", 2000, ["origem-vezemir"], "Armadura pesada completa, referência para a armadura escura registrada na ficha de Vezemir.", ["[[Vezemir]]"]),
        ("Broquel", "Escudo", "+1", "—", "—", 7, "15 PO", 15, ["capitulo01"], "Escudo pequeno de uso ágil.", []),
        ("Cota de malha", "Armadura média", "+4", "-1 metro", "+2", 17, "60 PO", 60, ["origem-vezemir"], "Armadura de malha comum entre soldados e mercenários.", []),
        ("Escudo de madeira", "Escudo", "+1", "—", "—", 3, "8 PO", 8, ["capitulo01"], "Escudo simples, mais barato e fácil de repor.", []),
        ("Escudo de aço", "Escudo", "+2", "—", "—", 7, "15 PO", 15, ["origem-vezemir"], "Escudo robusto; referência mecânica comum para a Muralha de Dorn no início.", ["[[Muralha de Dorn]]"]),
        ("Escudo torre", "Escudo", "Especial", "—", "—", 20, "30 PO", 30, ["origem-vezemir"], "Escudo enorme usado como cobertura portátil.", []),
    ]
    for name, category, armor_bonus, movement, max_dex, weight, price, price_po, origin, description, related in protections:
        effect = None
        if name == "Escudo torre":
            effect = "Não concede bônus direto de CA; oferece cobertura. Ataques pelo lado protegido têm 25% de chance de atingir o escudo e falhar."
        add_item(
            items,
            armor_folder,
            name=name,
            family="Proteção",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            armor_bonus=armor_bonus,
            movement_penalty=movement,
            max_dex_bonus=max_dex,
            origin_fit=origin,
            source_table="T5-3 - Itens de proteção",
            description=description,
            related=related,
            effect=effect,
        )

    basic_components = ["[[Arpéu]]", "[[Corda]]", "[[Giz]]", "[[Mochila]]", "[[Odre]]", "[[Pederneira]]", "[[Tocha]]", "[[Vara]]"]
    add_item(
        items,
        tools_folder,
        name="Kit básico",
        family="Kits e ferramentas",
        category="Kit",
        item_type="Kit de aventura",
        price="2,7 PO",
        price_po=2.7,
        weight_kg=21.65,
        origin_fit=["origem-vezemir", "capitulo01"],
        source_table="T5-4 - Kit básico",
        description="Conjunto mínimo de exploração para aventureiros iniciantes.",
        components=basic_components,
        related=basic_components,
    )
    basic_tools = [
        ("Arpéu", "Ferramenta", "5 PP", 0.5, 3, "Gancho triplo para escalada.", "Auxilia escaladas e fixação de corda."),
        ("Corda", "Ferramenta", "1 PO", 1, 15, "Corda de 15 metros capaz de sustentar carga pesada.", "Suporta até 250 kg."),
        ("Giz", "Ferramenta", "1 PC", 0.01, 0.1, "Giz branco para marcações em pedra, madeira e paredes.", "Marca caminhos e sinais."),
        ("Mochila", "Recipiente", "5 PP", 0.5, 2, "Mochila comum de aventureiro.", "Comporta até 30 kg."),
        ("Odre", "Recipiente", "5 PP", 0.5, 0.5, "Bolsa de couro para água ou outros líquidos.", "Comporta até 1 litro."),
        ("Pederneira", "Ferramenta", "1 PC", 0.01, 0.5, "Pedra útil para acender fogo e manter lâminas.", "Acende tochas e auxilia manutenção simples de lâminas."),
        ("Tocha", "Iluminação", "5 PC", 0.05, 0.5, "Fonte simples de luz para exploração.", "Ilumina 10 metros de raio por 1 hora."),
        ("Vara", "Ferramenta", "1 PP", 0.1, 0.5, "Vara de madeira de 3 metros.", "Testa pisos, alcança objetos e mantém distância."),
    ]
    for name, category, price, price_po, weight, description, effect in basic_tools:
        add_item(
            items,
            tools_folder,
            name=name,
            family="Kits e ferramentas",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=["capitulo01"],
            source_table="T5-4 - Kit básico",
            description=description,
            effect=effect,
            kit_membership=["[[Kit básico]]"],
            related=["[[Kit básico]]"],
        )

    explorer_components = ["[[Apito]]", "[[Escada de corda]]", "[[Frasco de óleo]]", "[[Lanterna furta-fogo]]", "[[Pá ou picareta]]", "[[Pé de cabra]]", "[[Pena e tinta]]", "[[Pergaminhos]]", "[[Ração de viagem]]", "[[Rede]]", "[[Saco de dormir]]", "[[Tenda]]"]
    add_item(
        items,
        tools_folder,
        name="Kit explorador",
        family="Kits e ferramentas",
        category="Kit",
        item_type="Kit de exploração",
        price="40,2 PO",
        price_po=40.2,
        weight_kg=42,
        origin_fit=["origem-varkh", "capitulo01"],
        source_table="T5-4 - Kit explorador",
        description="Conjunto ampliado para exploração, acampamento, luz, escrita e controle de terreno.",
        components=explorer_components,
        related=explorer_components,
    )
    explorer_tools = [
        ("Apito", "Ferramenta", "2 PC", 0.02, None, "Pequeno apito com cordão para pescoço.", "Sinalização sonora."),
        ("Escada de corda", "Ferramenta", "5 PO", 5, 15, "Escada portátil para escalada.", "Dobra a velocidade de escalada."),
        ("Frasco de óleo", "Alquímico simples", "5 PP", 0.5, 1, "Frasco com 500 ml de óleo para fogo, lubrificação ou lanternas.", "Alimenta fogo e lanternas."),
        ("Lanterna furta-fogo", "Iluminação", "1 PO", 1, 3, "Lanterna com feixe direcionado.", "Ilumina cone de 15 metros à frente por 1 hora."),
        ("Pá ou picareta", "Ferramenta", "5 PP", 0.5, 1.5, "Ferramenta de escavação e quebra de solo.", "Usada em escavações e remoção de obstáculos.", ["Pá/picareta", "Pá", "Picareta (ferramenta)"]),
        ("Pé de cabra", "Ferramenta", "2 PO", 2, 4, "Ferramenta para forçar portas, tampas e grades.", "Ajuda a abrir portas e baús pela força."),
        ("Pena e tinta", "Escrita", "5 PC", 0.05, 0.5, "Material de escrita para registros, mapas e falsificações simples.", "Permite escrita e cópia de documentos.", ["Pena/tinta"]),
        ("Pergaminhos", "Escrita", "5 PP", 0.5, None, "Conjunto com dez folhas soltas.", "Suporte para mapas, notas, contratos e magia se preparado adequadamente."),
        ("Ração de viagem", "Suprimento", "1 PO", 1, 1.5, "Comida seca para viagens.", "Alimenta uma pessoa por uma semana."),
        ("Rede", "Ferramenta de captura", "20 PO", 20, 1.5, "Rede usada para prender alvos.", "Ataque de toque; alvo fica constrito, sofre -2 em jogadas e perde bônus de DES na CA."),
        ("Saco de dormir", "Acampamento", "15 PP", 1.5, 10, "Saco para dormir ao relento.", "Acomoda humanoide médio e ajuda a preservar calor."),
        ("Tenda", "Acampamento", "10 PO", 10, 4, "Tenda de viagem para grupo pequeno.", "Acomoda até quatro pessoas em espaço de 2 x 2 metros."),
    ]
    for row in explorer_tools:
        name, category, price, price_po, weight, description, effect = row[:7]
        aliases = row[7] if len(row) > 7 else None
        add_item(
            items,
            tools_folder,
            name=name,
            family="Kits e ferramentas",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=["origem-varkh", "capitulo01"] if name in {"Frasco de óleo", "Pena e tinta", "Rede", "Pé de cabra"} else ["capitulo01"],
            source_table="T5-4 - Kit explorador",
            description=description,
            effect=effect,
            aliases=aliases,
            kit_membership=["[[Kit explorador]]"],
            related=["[[Kit explorador]]", "[[O Frasco Afogado]]"] if name == "Frasco de óleo" else ["[[Kit explorador]]"],
        )

    thief_components = ["[[Cadeado]]", "[[Estrepe x5]]", "[[Ferramentas de arrombamento]]", "[[Ferramentas de desarme de armadilhas]]", "[[Vela]]"]
    add_item(
        items,
        tools_folder,
        name="Kit ladrão",
        family="Kits e ferramentas",
        category="Kit",
        item_type="Kit de ladrão",
        price="52 PO / 72 PO com ferramentas especiais",
        price_po=52,
        weight_kg=3,
        origin_fit=["origem-varkh", "origem-raziel"],
        source_table="T5-4 - Kit ladrão",
        description="Conjunto de infiltração, arrombamento, armadilhas e luz discreta.",
        components=thief_components,
        related=thief_components,
    )
    thief_tools = [
        ("Cadeado", "Ferramenta", "5 PC / 1 PO especial", 0.05, 0.5, "Tranca simples para baús e portas.", "Versão especial impõe penalidade ao teste de abertura.", ["Cadeado especial"]),
        ("Estrepe x5", "Ferramenta de terreno", "1 PO", 1, 0.5, "Cinco estrelas metálicas pontiagudas para espalhar no chão.", "Criatura que atravessa a área faz JP+DES; falha sofre 1 dano e tem movimento reduzido à metade.", ["Estrepe (x5)", "Estrepes"]),
        ("Ferramentas de arrombamento", "Ferramenta de ladrão", "25 PO / 35 PO especial", 25, 1, "Conjunto para abrir fechaduras sem destruí-las.", "Versão especial concede +5% em testes apropriados."),
        ("Ferramentas de desarme de armadilhas", "Ferramenta de ladrão", "25 PO / 35 PO especial", 25, 1, "Conjunto para localizar e desarmar mecanismos perigosos.", "Versão especial concede +5% em testes apropriados."),
        ("Vela", "Iluminação", "1 PC", 0.01, None, "Pequena fonte de luz de chama baixa.", "Ilumina 50 cm de raio por 2 horas."),
    ]
    for row in thief_tools:
        name, category, price, price_po, weight, description, effect = row[:7]
        aliases = row[7] if len(row) > 7 else None
        add_item(
            items,
            tools_folder,
            name=name,
            family="Kits e ferramentas",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=["origem-varkh", "origem-raziel"],
            source_table="T5-4 - Kit ladrão",
            description=description,
            effect=effect,
            aliases=aliases,
            kit_membership=["[[Kit ladrão]]"],
            related=["[[Kit ladrão]]"],
        )

    specials = [
        ("Ácido", "10 PO", 10, 0.5, "Frasco de líquido corrosivo para uso ofensivo.", "Ataque de área; causa 1d6 de dano ácido regressivo.", ["origem-varkh", "origem-raziel"]),
        ("Água benta", "25 PO", 25, 0.5, "Água consagrada contra mortos-vivos, demônios e diabos.", "Ataque de área; causa 2d4 de dano conforme a regra do item contra alvos profanos.", ["origem-raziel"]),
        ("Antitoxina", "50 PO", 50, 0.5, "Preparado para resistir melhor a venenos.", "+2 em JP+CON contra venenos.", ["origem-varkh"]),
        ("Bastão solar", "2 PO", 2, 0.5, "Bastão químico ou mágico simples que emite luz forte.", "Ilumina 30 metros de raio por 6 horas.", ["origem-varkh", "origem-raziel"]),
        ("Fogo de alquimista", "25 PO", 25, 0.5, "Líquido inflamável preparado para combate.", "Ataque de área; causa 1d6 de dano de fogo.", ["origem-varkh"]),
        ("Ímã", "20 PO", 20, 1, "Pequeno ímã para recuperar objetos metálicos.", "Preso a vara ou corda, recolhe objetos metálicos de até 1 kg.", ["origem-varkh"]),
        ("Incenso", "20 PO", 20, 0.5, "Incenso de fumaça escura para ocultação.", "Preenche 20 m³ por 1d3 turnos; ataques contra criaturas na área têm 50% de chance de falhar mesmo após acerto.", ["origem-varkh", "origem-raziel"]),
        ("Pedra trovão", "30 PO", 30, 1, "Pedra que libera ruído ensurdecedor ao ser ativada.", "Ataque de área em raio de 10 metros; JP+CON evita ficar atordoado por 1d4 turnos.", ["origem-varkh", "origem-raziel"]),
    ]
    for name, price, price_po, weight, description, effect, origin in specials:
        add_item(
            items,
            special_folder,
            name=name,
            family="Alquimia e especiais",
            category="Item especial",
            item_type="Item especial",
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=origin,
            source_table="T5-4 - Itens especiais",
            description=description,
            effect=effect,
            related=["[[O Frasco Afogado]]"],
        )

    properties = [
        ("Barco à vela", "Veículo", "450 PO", 450, None, "Embarcação à vela para oito pessoas.", "Capacidade para 8 pessoas.", ["capitulo01"]),
        ("Canoa", "Veículo", "20 PO", 20, None, "Canoa simples para travessias curtas.", "Capacidade para 4 pessoas.", ["capitulo01"]),
        ("Carroça", "Veículo", "8 PO", 8, None, "Carroça simples de carga.", "Capacidade de 100 kg.", ["origem-vezemir", "capitulo01"]),
        ("Casa pobre", "Propriedade", "200 PO", 200, None, "Casa simples de um cômodo.", "1 cômodo.", ["capitulo01"]),
        ("Casa rica", "Propriedade", "450 PO", 450, None, "Casa confortável de vários cômodos.", "6 cômodos.", ["capitulo01"]),
        ("Castelo", "Fortificação", "100.000 PO", 100000, None, "Grande fortificação sustentada por guarnição numerosa.", "Estrutura para 1.500 homens.", ["origem-vezemir"]),
        ("Cavalo de guerra", "Montaria", "150 PO", 150, None, "Cavalo adulto treinado para batalha.", "Montaria adulta de combate.", ["origem-vezemir"]),
        ("Cavalo de montaria", "Montaria", "13 PO", 13, None, "Cavalo adulto para viagem e carga.", "Montaria adulta de viagem.", ["capitulo01"]),
        ("Fazenda", "Propriedade", "700 PO", 700, None, "Fazenda de criação em escala local.", "Espaço para 100 bois.", ["capitulo01"]),
        ("Forte", "Fortificação", "25.000 PO", 25000, None, "Forte militar de menor porte.", "Estrutura para 50 homens.", ["origem-vezemir"]),
        ("Mansão", "Propriedade", "3.500 PO", 3500, None, "Residência grande e luxuosa.", "20 cômodos.", ["capitulo01"]),
        ("Navio", "Veículo", "4.500 PO", 4500, None, "Navio de médio porte para viagens marítimas.", "Capacidade para 50 pessoas.", ["capitulo01"]),
    ]
    for name, category, price, price_po, weight, description, effect, origin in properties:
        add_item(
            items,
            property_folder,
            name=name,
            family="Propriedades e montarias",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=origin,
            source_table="T5-4 - Propriedades",
            description=description,
            effect=effect,
            purchase_status="Compra especial" if category in {"Propriedade", "Fortificação", "Veículo"} and price_po >= 200 else "Comprável",
        )

    lodging = [
        ("Banquete", "Alimentação", "15 PP", 1.5, None, "Banquete para dez pessoas.", "Serve 10 pessoas."),
        ("Cerveja", "Bebida", "3 PC", 0.03, None, "Caneca ou porção de cerveja comum.", "500 ml."),
        ("Cerveja anã", "Bebida", "1 PP", 0.1, None, "Cerveja anã de alta qualidade.", "500 ml."),
        ("Estrebaria", "Serviço", "5 PC", 0.05, None, "Abrigo e alimentação para cavalos.", "Serviço de estábulo."),
        ("Hidromel", "Bebida", "1 PO", 1, None, "Porção de hidromel.", "500 ml."),
        ("Latrina", "Serviço", "5 PC", 0.05, None, "Uso de latrina em estalagem ou estabelecimento.", "Preço por uso."),
        ("Quarto coletivo", "Hospedagem", "5 PC", 0.05, None, "Leito em quarto coletivo.", "Até 5 pessoas; preço individual."),
        ("Quarto de banho", "Serviço", "1 PP", 0.1, None, "Banho em instalação de estalagem.", "Preço por uso."),
        ("Quarto de luxo", "Hospedagem", "1 PO", 1, None, "Quarto individual de luxo com banho.", "1 pessoa com banho."),
        ("Quarto individual", "Hospedagem", "1 PP", 0.1, None, "Quarto individual simples.", "1 pessoa sem banho."),
        ("Refeição", "Alimentação", "2 PP", 0.2, None, "Refeição individual em estalagem.", "Desjejum, almoço, jantar ou ceia."),
        ("Vinho", "Bebida", "1 PP", 0.1, None, "Porção de vinho comum.", "500 ml."),
    ]
    for name, category, price, price_po, weight, description, effect in lodging:
        add_item(
            items,
            service_folder,
            name=name,
            family="Hospedagem e serviços",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=["capitulo01"],
            source_table="T5-4 - Hospedagem",
            description=description,
            effect=effect,
            aliases=["Cerveja anã de alta qualidade"] if name == "Cerveja anã" else None,
        )

    magic_and_materials = [
        ("Material especial - Prata", "Material especial", "Preço da arma x2", None, None, "Aplicação de prata em arma para enfrentar licantropos.", "Armas de prata atingem licantropos sem sofrer redução de dano.", ["origem-raziel"], "Raro", ["Prata", "Arma de prata"]),
        ("Material especial - Bronze", "Material especial", "Preço da armadura x1,5", None, None, "Armadura de bronze, menos protetora, porém mais leve.", "Armadura recebe -1 na CA, mas reduz a penalidade de movimento em 1.", ["capitulo01"], "Raro", ["Bronze", "Armadura de bronze"]),
        ("Material especial - Mitral", "Material especial", "Preço do item x10", None, None, "Material raríssimo usado em armas e armaduras superiores.", "Melhora a defesa de armaduras e o dano de armas em +1.", ["origem-vezemir", "origem-raziel"], "Raro", ["Mitral"]),
        ("Arma racial", "Equipamento racial", "Preço da arma +350 PO", None, None, "Arma ajustada a tradições raciais específicas.", "Anões recebem +1 em ataques; elfos reduzem a categoria de tamanho da arma em uma etapa.", ["capitulo01"], "Raro", None),
        ("Proteção racial", "Equipamento racial", "Preço da proteção +300 PO", None, None, "Armadura ou escudo ajustado a tradições raciais específicas.", "Anões recebem +1 na CA; elfos reduzem a penalidade de movimento em 1.", ["capitulo01"], "Raro", None),
        ("Serviço de lançar magia", "Serviço mágico", "30 PO x círculo da magia", None, None, "Contratação de conjurador para lançar uma magia.", "Custo base: 30 PO multiplicado pelo círculo da magia.", ["capitulo01"], "Raro", ["Lançar magia"]),
        ("Poção mágica", "Serviço mágico", "50 PO x círculo da magia", None, None, "Poção preparada com efeito de magia.", "Custo base: 50 PO multiplicado pelo círculo da magia.", ["origem-varkh"], "Raro", ["Poção"]),
        ("Pergaminho mágico", "Serviço mágico", "100 PO x círculo da magia", None, None, "Pergaminho contendo magia preparada.", "Custo base: 100 PO multiplicado pelo círculo da magia.", ["capitulo01"], "Raro", ["Pergaminho"]),
        ("Varinha mágica", "Serviço mágico", "100 PO x círculo da magia", None, None, "Varinha com cargas mágicas.", "Custo base: 100 PO multiplicado pelo círculo da magia; varinhas possuem 50 cargas.", ["capitulo01"], "Raro", ["Varinha"]),
    ]
    for name, category, price, price_po, weight, description, effect, origin, status, aliases in magic_and_materials:
        add_item(
            items,
            magic_folder,
            name=name,
            family="Materiais e magia",
            category=category,
            item_type=category,
            price=price,
            price_po=price_po,
            weight_kg=weight,
            origin_fit=origin,
            source_table="Capítulo 5 - Materiais especiais e serviços mágicos",
            source_section="Capítulo 5 - Equipamentos especiais",
            description=description,
            effect=effect,
            purchase_status=status,
            aliases=aliases,
            buy_note="Disponível apenas com fornecedor especializado, templo, guilda arcana ou artesão raro.",
        )


def write_catalog_notes() -> None:
    build_catalog()
    for item in CATALOG:
        folder = ITEMS / item["folder"]
        folder.mkdir(parents=True, exist_ok=True)
        path = folder / f"{item['name']}.md"
        path.write_text(note_for_item(item), encoding="utf-8", newline="\n")


def write_index_notes() -> None:
    catalog_fm = yaml_frontmatter(
        {
            "obsidianUIMode": "preview",
            "NoteIcon": "items",
            "NoteStatus": "Active",
            "type": "index",
            "status": "Ativo",
            "campaign_status": "Ativo",
            "visibility": "Jogadores",
            "spoiler_level": "none",
            "gm_secret": False,
            "created_by": "Codex",
            "source_system": "Old Dragon 2e",
            "tags": ["indice", "indice-item", "catalogo-compra", "item"],
        }
    )
    catalog_body = """# Catálogo de Compras

Catálogo jogável de itens comuns, raros e serviços disponíveis para compras em Omnisvera. Os valores vêm do livro-base anexado e devem ser tratados como referência inicial, sem transformar equipamento comum em relíquia.

## Como Usar

- `purchase_status: Comprável` indica compra comum.
- `purchase_status: Raro` exige fornecedor especializado ou cena de busca.
- `purchase_status: Compra especial` envolve patrimônio, montarias caras, veículos ou autorização social.
- `purchase_status: Improvisado` não tem preço fixo e deve nascer de cena.
- Relíquias dos personagens continuam em notas próprias e usam `base_item` para equilíbrio inicial.

## Armas

```dataview
TABLE item_category AS Categoria, damage AS Dano, damage_type AS "Tipo", range AS Alcance, critical AS Crítico, weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Armas"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Proteção

```dataview
TABLE item_category AS Categoria, armor_bonus AS CA, movement_penalty AS Movimento, max_dex_bonus AS "DES máx.", weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Proteção"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Kits e Ferramentas

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Efeito, weight_kg AS "Peso kg", price AS Preço, kit_membership AS Kit, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Kits e ferramentas"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Alquimia e Especiais

```dataview
TABLE mechanical_effect AS Efeito, weight_kg AS "Peso kg", price AS Preço, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Alquimia e especiais"
AND purchase_status != "Não comprável"
SORT file.name ASC
```

## Propriedades e Montarias

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Detalhe, price AS Preço, purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Propriedades e montarias"
AND purchase_status != "Não comprável"
SORT price_po ASC, file.name ASC
```

## Hospedagem e Serviços

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Detalhe, price AS Preço
FROM "Items"
WHERE type = "item"
AND item_family = "Hospedagem e serviços"
AND purchase_status != "Não comprável"
SORT item_category ASC, price_po ASC, file.name ASC
```

## Materiais e Magia

```dataview
TABLE item_category AS Categoria, mechanical_effect AS Efeito, price AS Preço, purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND item_family = "Materiais e magia"
AND purchase_status != "Não comprável"
SORT item_category ASC, file.name ASC
```

## Por Origem

### Vezemir

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-vezemir")
SORT item_family ASC, file.name ASC
```

### Varkh

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-varkh")
SORT item_family ASC, file.name ASC
```

### Raziel

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-raziel")
SORT item_family ASC, file.name ASC
```

## Regras Relacionadas

- [[Regras de Compra e Equipamento]]
- [[INDICE_DE_ITENS]]
"""
    (ITEMS / "Catálogo de Compras.md").write_text(catalog_fm + "\n\n" + catalog_body.rstrip() + "\n", encoding="utf-8", newline="\n")

    rules_fm = yaml_frontmatter(
        {
            "obsidianUIMode": "preview",
            "NoteIcon": "rules",
            "NoteStatus": "Active",
            "type": "rule",
            "status": "Ativo",
            "campaign_status": "Ativo",
            "visibility": "Jogadores",
            "spoiler_level": "none",
            "gm_secret": False,
            "created_by": "Codex",
            "source_system": "Old Dragon 2e",
            "source_book": "Old Dragon - Livro Básico Aprimorado",
            "source_section": "Capítulo 5 - Equipamentos",
            "tags": ["rules", "item", "compra", "old-dragon", "economia"],
        }
    )
    rules_body = """# Regras de Compra e Equipamento

Nota de referência para usar o catálogo de itens em Omnisvera sem perder o equilíbrio inicial da campanha.

## Moedas

| Moeda | Conversão |
| :-- | :-- |
| 1 PPL | 10 PE / 100 PO / 1.000 PP / 10.000 PC |
| 1 PE | 10 PO / 100 PP / 1.000 PC |
| 1 PO | 10 PP / 100 PC |
| 1 PP | 10 PC |

## Renda Inicial

- A referência padrão para personagens novos é `3d6 x 10 PO`.
- O valor deve ser ajustado pelo mestre quando a origem do personagem justificar riqueza, dívida, roubo, patrono ou perda de equipamento.

## Equipamento Comum e Relíquias

- Itens comuns do catálogo entram com os valores de tabela.
- Relíquias como [[Grisalma]], [[Muralha de Dorn]], [[Adagas de Espectro Fantasma]] e [[Manto Primordial do Ancião]] podem parecer únicas, mas devem usar `base_item` enquanto suas propriedades especiais não forem liberadas.
- Itens narrativos sem preço, como [[O Medalhão]], [[Caderninho de Vozes]] e [[Máscara de Médico da Peste de Varkh]], continuam fora da economia comum.

## Materiais Especiais

| Material | Custo | Regra inicial |
| :-- | :-- | :-- |
| [[Material especial - Prata]] | preço da arma x2 | atinge licantropos sem redução de dano |
| [[Material especial - Bronze]] | preço da armadura x1,5 | armadura perde 1 ponto de CA e reduz penalidade de movimento em 1 |
| [[Material especial - Mitral]] | preço do item x10 | armas recebem +1 no dano e armaduras recebem +1 na defesa |

## Equipamentos Raciais

- [[Arma racial]]: preço da arma +350 PO; versões anãs recebem +1 em ataques, versões élficas reduzem a categoria de tamanho em uma etapa.
- [[Proteção racial]]: preço da proteção +300 PO; versões anãs recebem +1 na CA, versões élficas reduzem a penalidade de movimento em 1.
- Esses itens são raros e normalmente exigem encomenda ou contato cultural específico.

## Serviços Mágicos

| Serviço | Custo |
| :-- | :-- |
| [[Serviço de lançar magia]] | 30 PO x círculo da magia |
| [[Poção mágica]] | 50 PO x círculo da magia |
| [[Pergaminho mágico]] | 100 PO x círculo da magia |
| [[Varinha mágica]] | 100 PO x círculo da magia; 50 cargas |

> [!warning] Disponibilidade
> Magias acima do 3º círculo raramente estão à venda. Poções divinas de cura são a exceção mais comum.

## Índices

- [[Catálogo de Compras]]
- [[INDICE_DE_ITENS]]
"""
    (ITEMS / "Regras de Compra e Equipamento.md").write_text(rules_fm + "\n\n" + rules_body.rstrip() + "\n", encoding="utf-8", newline="\n")

    master_fm = yaml_frontmatter(
        {
            "obsidianUIMode": "preview",
            "NoteIcon": "items",
            "NoteStatus": "Active",
            "type": "index",
            "status": "Ativo",
            "campaign_status": "Ativo",
            "visibility": "Mestre",
            "spoiler_level": "none",
            "gm_secret": True,
            "created_by": "Sage",
            "tags": ["indice", "indice-item"],
        }
    )
    master_body = """# Índice de Itens

Índice operacional para itens comuns, catálogo de compras, relíquias, armas, escudos, objetos narrativos e serviços compráveis.

## Notas Centrais

- [[Catálogo de Compras]] — índice jogável para compra de equipamentos.
- [[Regras de Compra e Equipamento]] — moedas, materiais especiais, serviços mágicos e regra de item base.

## Regra de Uso

- `item_family` organiza o catálogo por função ampla.
- `item_category` define a categoria prática: arma, proteção, kit, serviço, propriedade etc.
- `purchase_status` separa `Comprável`, `Raro`, `Compra especial`, `Improvisado` e `Não comprável`.
- `base_item` liga relíquias narrativas a um item comum de equilíbrio inicial.
- `origin_fit` conecta itens aos capítulos de origem: `origem-vezemir`, `origem-varkh`, `origem-raziel` e `capitulo01`.
- `visibility` e `gm_secret` continuam controlando o que aparece para jogadores.

## Catálogo Comprável

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, weight_kg AS "Peso kg", purchase_status AS Compra, origin_fit AS Origem
FROM "Items"
WHERE type = "item"
AND purchase_status != "Não comprável"
SORT item_family ASC, item_category ASC, file.name ASC
```

## Relíquias e Itens Narrativos

```dataview
TABLE item_type AS Tipo, owner AS Portador, base_item AS "Item base", status, visibility, danger_level
FROM "Items"
WHERE type = "item"
AND purchase_status = "Não comprável"
SORT owner ASC, file.name ASC
```

## Todos os Itens

```dataview
TABLE item_family AS Família, item_category AS Categoria, item_type AS Tipo, price AS Preço, owner AS Portador, status, visibility, danger_level
FROM "Items"
WHERE type = "item"
SORT item_family ASC, file.name ASC
```

## Itens dos Jogadores

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, owner AS Portador, status
FROM "Items"
WHERE type = "item"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT owner ASC, item_family ASC, file.name ASC
```

## Itens de Mestre / Spoiler

```dataview
TABLE item_type AS Tipo, owner AS Portador, status, spoiler_level, base_item AS "Item base"
FROM "Items"
WHERE type = "item"
AND visibility = "Mestre"
SORT spoiler_level DESC, file.name ASC
```

## Por Origem

### Vezemir

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-vezemir")
SORT item_family ASC, file.name ASC
```

### Varkh

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-varkh")
SORT item_family ASC, file.name ASC
```

### Raziel

```dataview
TABLE item_family AS Família, item_category AS Categoria, price AS Preço, purchase_status AS Compra
FROM "Items"
WHERE type = "item"
AND contains(origin_fit, "origem-raziel")
SORT item_family ASC, file.name ASC
```

## Pendências

- Definir imagens para itens comuns apenas quando houver necessidade visual.
- Confirmar se as relíquias liberam propriedades especiais por nível, capítulo ou gatilho narrativo.
- Manter o catálogo de compra separado dos itens únicos de campanha.
"""
    (ITEMS / "INDICE_DE_ITENS.md").write_text(master_fm + "\n\n" + master_body.rstrip() + "\n", encoding="utf-8", newline="\n")


def replace_once(text: str, old: str, new: str) -> str:
    if old not in text:
        return text
    return text.replace(old, new, 1)


def insert_after_line(text: str, marker: str, insert: str) -> str:
    if insert.strip() in text:
        return text
    return replace_once(text, marker, marker + "\n" + insert.rstrip())


def update_existing_item(path: Path, inserts: list[str], replacements: list[tuple[str, str]]) -> None:
    text = path.read_text(encoding="utf-8")
    for marker, insert in inserts:
        text = insert_after_line(text, marker, insert)
    for old, new in replacements:
        text = replace_once(text, old, new)
    path.write_text(text, encoding="utf-8", newline="\n")


def update_existing_notes() -> None:
    update_existing_item(
        ITEMS / "Grisalma.md",
        [
            (
                "item_type: Machado de batalha / artefato marcial",
                """item_family: Relíquia
item_category: Arma narrativa
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Machado de batalha]]"
base_price: 12 PO
base_damage: 2d6
base_weight_kg: 8""",
            )
        ],
        [
            (
                "A ficha atual de Vezemir registra **2d8 de dano** para Grisalma.\n\n> [!warning] Ajuste de regras\n> A ficha visual da relíquia propõe dano de 2d10 com duas mãos e 1d10 com uma mão. A ficha de personagem mais recente registra 2d8; esse é o valor mantido até confirmação do mestre.",
                "No início da campanha, Grisalma usa [[Machado de batalha]] como item base: **2d6 de dano**, corte/impacto, crítico x3, peso de referência 8 kg e preço de referência 12 PO.\n\n> [!warning] Ajuste de regras\n> Valores antigos como 2d8 ou 2d10 ficam como proposta de evolução/desbloqueio. Enquanto a relíquia não liberar propriedades próprias, prevalece o item base do catálogo.",
            ),
            ("- Confirmar dano final.", "- Confirmar quando, se e como Grisalma ultrapassa o dano base de [[Machado de batalha]]."),
        ],
    )
    update_existing_item(
        ITEMS / "Muralha de Dorn.md",
        [
            (
                "item_type: Escudo grande / relíquia marcial",
                """item_family: Relíquia
item_category: Escudo narrativo
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Escudo de aço]]"
base_price: 15 PO
base_armor_bonus: "+2"
base_weight_kg: 7""",
            )
        ],
        [
            (
                "A ficha atual de Vezemir registra a Muralha de Dorn como o bônus de **+2 na Classe de Armadura**.\n\n> [!warning] Ajuste de regras\n> A ficha visual propõe bônus e reduções maiores que os usados na ficha de personagem. Até nova decisão do mestre, prevalece o bônus de **+2 na CA** registrado na ficha atual.",
                "No início da campanha, a Muralha de Dorn usa [[Escudo de aço]] como item base: **+2 na Classe de Armadura**, peso de referência 7 kg e preço de referência 15 PO.\n\n> [!warning] Ajuste de regras\n> Bônus maiores, redução de dano e efeitos de muralha ficam como propriedades narrativas bloqueadas até decisão do mestre.",
            )
        ],
    )
    update_existing_item(
        ITEMS / "Adagas de Espectro Fantasma.md",
        [
            (
                "item_type: Par de adagas / relíquia vampírica",
                """item_family: Relíquia
item_category: Arma narrativa
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Adaga]]"
base_price: 2 PO cada
base_damage: 1d4
base_weight_kg: 0.5 cada""",
            )
        ],
        [
            (
                "## Propriedades Conhecidas",
                "## Regra em Uso Inicial\n\nEnquanto as propriedades vampíricas não forem liberadas, cada lâmina usa [[Adaga]] como item base: **1d4 de dano**, perfuração, arremesso 3/6, crítico x2, peso de referência 0,5 kg e preço de referência 2 PO.\n\n## Propriedades Conhecidas",
            ),
            ("- Definir regra mecânica exata.", "- Confirmar quando as adagas deixam de usar apenas a regra base de [[Adaga]]."),
        ],
    )
    update_existing_item(
        ITEMS / "Manto Primordial do Ancião.md",
        [
            (
                "item_type: Manto / armadura leve / relíquia primordial",
                """item_family: Relíquia
item_category: Proteção narrativa
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Armadura de couro batido]]"
base_price: 25 PO
base_armor_bonus: "+3"
base_weight_kg: 15""",
            )
        ],
        [
            (
                "## Propriedades Conhecidas",
                "## Regra em Uso Inicial\n\nEnquanto sua natureza primordial permanecer bloqueada, o manto usa [[Armadura de couro batido]] como item base: **+3 na CA**, sem penalidade de movimento, bônus máximo de DES +6, peso de referência 15 kg e preço de referência 25 PO.\n\n## Propriedades Conhecidas",
            ),
            ("- Definir mecânica exata de furtividade/proteção.", "- Confirmar quando o manto deixa de usar apenas a regra base de [[Armadura de couro batido]]."),
        ],
    )
    update_existing_item(
        ITEMS / "Caderninho de Vozes.md",
        [
            (
                "item_type: Caderno pessoal / ferramenta de mimetismo",
                """item_family: Item narrativo
item_category: Ferramenta pessoal
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Pena e tinta]]"
base_support_item: "[[Pergaminhos]]\"""",
            )
        ],
        [
            (
                "## Uso em Mesa",
                "## Regra em Uso Inicial\n\nO caderno não concede bônus automático. Para compra e reposição de materiais, use [[Pena e tinta]] e [[Pergaminhos]] como referências comuns.\n\n## Uso em Mesa",
            )
        ],
    )
    update_existing_item(
        ITEMS / "Máscara de Médico da Peste de Varkh.md",
        [
            (
                "item_type: Máscara / equipamento pessoal",
                """item_family: Item narrativo
item_category: Equipamento pessoal
purchase_status: Não comprável
source_system: Omnisvera / Old Dragon 2e
base_item: "[[Antitoxina]]\"""",
            )
        ],
        [
            (
                "## Uso em Mesa",
                "## Regra em Uso Inicial\n\nA máscara é identidade e proteção narrativa. Ela não substitui [[Antitoxina]] nem concede bônus automático contra venenos, doenças ou gases sem preparação de cena.\n\n## Uso em Mesa",
            )
        ],
    )
    update_existing_item(
        ITEMS / "O Medalhão.md",
        [
            (
                "item_type: Medalhão / relíquia",
                """item_family: Relíquia
item_category: Objeto narrativo
purchase_status: Não comprável
source_system: Omnisvera""",
            )
        ],
        [
            (
                "## Uso em Mesa",
                "## Regra em Uso Inicial\n\nO medalhão não tem preço de compra, bônus ou função mecânica pública. Sua regra permanece travada até o arco dos [[Guardiões do Véu Cinzento]] pedir revelação.\n\n## Uso em Mesa",
            )
        ],
    )

    vezemir = ROOT / "Characters" / "Individual" / "Vezemir.md"
    text = vezemir.read_text(encoding="utf-8")
    text = text.replace("### [[Grisalma]]\n\nMachado lendário entregue por Elarion Vaelthor.", "### [[Grisalma]]\n\nMachado lendário entregue por Elarion Vaelthor. Em nível inicial, usa [[Machado de batalha]] como item base.")
    text = text.replace("### [[Muralha de Dorn]]\n\nEscudo ancestral entregue por Elarion Vaelthor.", "### [[Muralha de Dorn]]\n\nEscudo ancestral entregue por Elarion Vaelthor. Em nível inicial, usa [[Escudo de aço]] como item base.")
    text = text.replace("- **[[Grisalma]]:** dano registrado de 2d8.", "- **[[Grisalma]]:** usar [[Machado de batalha]] como referência inicial, com dano base de 2d6.")
    text = text.replace("- **Adaga oculta na bota:** dano de 1d4.", "- **Adaga oculta na bota:** usar [[Adaga]], dano de 1d4.")
    text = text.replace("- **Armadura pesada:** peso registrado de 20 kg.", "- **Armadura pesada:** usar [[Armadura completa]] como referência inicial, peso de 20 kg.")
    text = text.replace("- **[[Muralha de Dorn]]:** bônus de +2 na CA.", "- **[[Muralha de Dorn]]:** usar [[Escudo de aço]] como referência inicial, bônus de +2 na CA.")
    text = text.replace("- Kit básico.", "- [[Kit básico]].")
    vezemir.write_text(text, encoding="utf-8", newline="\n")

    varkh = ROOT / "Characters" / "Individual" / "Varkh Nimalis.md"
    text = varkh.read_text(encoding="utf-8")
    text = text.replace("### Espada Curta", "### [[Espada curta]]")
    text = text.replace("### Duas Adagas", "### Duas [[Adaga|Adagas]]")
    text = text.replace("### Arco Curto", "### [[Arco curto]]")
    text = text.replace("### Cinto de Frascos Alquímicos", "### Cinto de Frascos Alquímicos")
    text = text.replace("Carrega misturas como pó de sono, fumaça cinza, óleo escorregadio, ácido fraco e venenos leves.", "Carrega misturas inspiradas por itens comuns como [[Ácido]], [[Fogo de alquimista]], [[Frasco de óleo]], [[Antitoxina]], [[Incenso]] e [[Pedra trovão]].")
    text = text.replace("### Máscara de Médico da Peste", "### [[Máscara de Médico da Peste de Varkh|Máscara de Médico da Peste]]")
    text = text.replace("### Caderninho de Vozes", "### [[Caderninho de Vozes]]")
    text = text.replace("Os equipamentos de Varkh ainda não possuem notas individuais no vault. Quando forem transformados em itens próprios, esta seção poderá receber a mesma consulta de cartões usada na ficha de Vezemir.", "Os equipamentos comuns de Varkh agora usam notas do [[Catálogo de Compras]]. A máscara e o caderninho continuam como itens narrativos próprios.")
    text = text.replace("- Espada curta.", "- [[Espada curta]].")
    text = text.replace("- Duas adagas.", "- Duas [[Adaga|adagas]].")
    text = text.replace("- Arco curto.", "- [[Arco curto]].")
    text = text.replace("- Máscara de médico da peste.", "- [[Máscara de Médico da Peste de Varkh|Máscara de médico da peste]].")
    text = text.replace("- Cinto de frascos e utensílios alquímicos.", "- Cinto de frascos e utensílios alquímicos baseados em [[Ácido]], [[Fogo de alquimista]], [[Frasco de óleo]] e [[Antitoxina]].")
    text = text.replace("- Caderninho de vozes.", "- [[Caderninho de Vozes]].")
    varkh.write_text(text, encoding="utf-8", newline="\n")


def main() -> None:
    write_catalog_notes()
    write_index_notes()
    update_existing_notes()
    print(f"Generated {len(CATALOG)} catalog item notes.")


if __name__ == "__main__":
    main()
