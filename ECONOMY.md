---
obsidianUIMode: preview
NoteIcon: lore
NoteStatus: Draft
status: Em desenvolvimento
visibility: gm
cover: zz_media/ui/economia.webp
tags:
  - economy
  - currency
  - earthropo
---

# Economia de Earthropo

> [!NOTE|clean no-i right]+ Moedas
> ![[zz_media/ui/economia.webp|400]]

## Moedas

Nimalia cunha moedas de cobre, prata, ouro e platina. Elas circulam amplamente nas rotas próximas ao reino, mas outros territórios podem usar moedas próprias, peso de metal, crédito ou escambo.

| Conversão de campanha | Valor |
|:--|--:|
| 10 peças de cobre | 1 peça de prata |
| 10 peças de prata | 1 peça de ouro |
| 10 peças de ouro | 1 peça de platina |

## Cunhagem

A [[Casa da Moeda de Nimalia]] controla peso, composição, brasão e marcas contra falsificação. Moedas antigas são avaliadas por metal, procedência e interesse histórico.

## Comércio de Nimalia

- **Produção:** grãos, artesanato, serviços e equipamentos.
- **Importação:** minérios, madeira e materiais raros.
- **Centro comercial:** [[Nimalis]].
- **Porto e mercado informal:** [[Maré Baixa]].
- **Organização mercantil:** [[Guilda dos Mercadores]].

## Catálogo de itens do vault

```dataview
TABLE item_type, owner, status, source
FROM "Items"
SORT item_type ASC, file.name ASC
```

## Equipamentos e preços de regras

O estoque mecânico completo permanece nos livros e referências adotados em [[Workflow/RULES_SOURCES|Fontes de Regras]]. O vault registra itens quando eles:

1. pertencem a um personagem;
2. aparecem em uma loja ou tesouro;
3. recebem alteração de preço ou regra;
4. tornam-se relevantes para a campanha.

Isso evita duplicar listas integrais de livros e permite que cada loja tenha estoque próprio por Dataview.

## Lojas

```dataview
TABLE territory, district, info
FROM #location
WHERE contains(tags, "shop") OR contains(tags, "market")
SORT file.name ASC
```

> [!gm]- Próxima expansão
> Criar notas de estoque para lojas específicas de Nimalis, começando pelo Frasco Afogado, Mercado Central e Distrito dos Ofícios.
