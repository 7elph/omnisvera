# DataCards Compatibility Rules

Estas regras definem como manter cards funcionando durante a transição.

## Regras centrais

- `thumbnail` continua como imagem de card compacto.
- `cover` pode ser usado em páginas maiores, lore, territórios e locais.
- `portrait` pode existir sem substituir `thumbnail`.
- Tags antigas ainda podem alimentar cards.
- Tags novas devem ser adicionadas antes de trocar consultas.
- Não alterar `imageProperty` sem garantir que todas as notas tenham o campo correspondente.

## Campos de imagem

| uso | campo recomendado | observação |
| --- | --- | --- |
| Personagem em lista/card pequeno | `thumbnail` | Campo herdado crítico. |
| Território/lore/local em card visual | `cover` | Campo herdado crítico. |
| Retrato dentro da nota | `portrait` | Complementar. |
| Mapa | `map_image` | Não substituir `cover`. |
| Handout | `handout_image` | Exige visibilidade. |

## Exemplo de DataCards com `thumbnail`

```dataview
TABLE thumbnail, status, location, faction
FROM "Characters"
WHERE contains(tags, "character")
SORT file.name ASC
```

Configuração conceitual:

```text
imageProperty: thumbnail
preset: portrait
columns: 5
```

## Exemplo de DataCards com `cover`

```dataview
TABLE cover, region, leader, population
FROM #territory
SORT file.name ASC
```

Configuração conceitual:

```text
imageProperty: cover
preset: portrait
columns: 6
```

## Tags antigas e novas

Durante transição, cards podem consultar tags antigas e novas.

```dataview
TABLE thumbnail, status, faction
FROM "Characters"
WHERE contains(tags, "character") OR contains(tags, "individual")
SORT file.name ASC
```

## Dashboard público

DataCards públicos precisam de filtro de visibilidade:

```dataview
TABLE thumbnail, status, location
FROM "Characters"
WHERE contains(tags, "character")
AND (visibility = "Público" OR visibility = "Jogadores" OR player_known = true)
SORT file.name ASC
```

## Anti-padrões

- Trocar `imageProperty: thumbnail` para `portrait` sem preencher `portrait` em todas as notas.
- Trocar tags antigas por tags novas numa única etapa.
- Criar cards públicos sem `visibility`.
- Usar `cover` como substituto universal de `thumbnail`.
- Remover campos antigos porque o card novo parece funcionar.
