---
obsidianUIMode: preview
banner: "[[zz_media/avenor.png]]"
banner-x: 51
banner-y: 34
banner-height: 280
content-start: 271
banner-fade: -45
visibility: Público
spoiler_level: none
player_known: true
gm_secret: false
---

# Omnisvera — Home dos Jogadores

> [!info]+ CONTEÚDO LIBERADO
> Esta Home mostra apenas conteúdo público, conhecido pelos jogadores ou explicitamente liberado.
>
> Se uma nota ainda não tiver classificação de visibilidade, ela não deve aparecer automaticamente aqui.

> [!warning]- ÁREA DO MESTRE
> [[Home_Mestre]] é uma área de preparação e pode conter spoilers, segredos e relatórios técnicos.

## Entrada rápida

- [[Calendar|Calendário de Nimalia]]
- [[MAPA DE NIMALIA]]

> [!infobox]- Calendário
> ```calendarium
> ```

## Personagens dos jogadores

```dataview
TABLE
  thumbnail AS "Imagem",
  status,
  life_status,
  location,
  territory,
  faction
FROM "Characters"
WHERE contains(tags, "player")
AND (visibility = "Jogadores" OR visibility = "Público" OR player_known = true)
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Locais conhecidos

```dataview
TABLE cover, territory, info
FROM #location
WHERE (visibility = "Jogadores" OR visibility = "Público" OR player_known = true)
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Facções conhecidas

```dataview
TABLE thumbnail, status, leader, territory
FROM #faction
WHERE (visibility = "Jogadores" OR visibility = "Público" OR player_known = true)
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Handouts liberados

```dataview
TABLE thumbnail, handout_image, description, revealed_in
FROM #handout
WHERE (visibility = "Jogadores" OR visibility = "Público" OR player_known = true)
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Sessões jogadas

```dataview
TABLE date, description
FROM #story
WHERE (visibility = "Jogadores" OR visibility = "Público" OR player_known = true)
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT date ASC
```

## Nota de segurança

Este painel é conservador por padrão. Se algo que os jogadores já conhecem não aparecer aqui, a nota provavelmente ainda precisa receber campos como:

```yaml
visibility: Jogadores
player_known: true
gm_secret: false
spoiler_level: none
```

---

2026, © **Omnisvera**
