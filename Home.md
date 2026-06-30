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
gm_secret: false
---

<div style="text-align: center;">
  <img src="zz_media/omnisvera.PNG" width="900px">
</div>

# Omnisvera — Home dos Jogadores

> [!info]+ CONTEÚDO LIBERADO
> Esta Home mostra apenas conteúdo público, conhecido pelos jogadores ou explicitamente liberado.
>
> Se algo não aparece aqui, isso não significa que não exista no mundo: significa apenas que ainda não foi liberado para os personagens.

> [!cards|5]
> **EARTHROPO**
> [![[earthropo.png|sban htiny ctr p+t]]](MAPA%20DE%20EARTHROPO.md)
>
> **NIMALIA**
> [![[mapa-de-nimalia.png|sban htiny ctr]]](MAPA%20DE%20NIMALIA.md)
>
> **NIMALIS**
> [![[mapa-de-nimalis.png|sban htiny ctr]]](MAPA%20DE%20NIMALIS.md)
>
> **CRÔNICAS**
> [![[banner-earthropo.png|sban htiny ctr]]](EARTHROPO/EARTHROPO.md)
>
> **CALENDÁRIO**
> [[Calendar|Calendário de Nimalia]]

---

> [!world]+ CAPÍTULO EM FOCO
> ```datacards
> TABLE cover, status, campaign_status, description
> FROM "EARTHROPO"
> WHERE contains(tags, "capitulo")
> AND !contains(tags, "bside")
> AND !contains(tags, "origem")
> AND (visibility = "Jogadores" OR visibility = "Público")
> AND gm_secret != true
> AND spoiler_level != "medium"
> AND spoiler_level != "heavy"
> SORT file.name ASC
>
> // Settings
> preset: square
> columns: 1
> imageProperty: cover
> imageWidth: 80px
> showImageOnHover: true
> ```

---

## Personagens dos Jogadores

```datacards
TABLE thumbnail, status, location, territory, faction
FROM "Characters/Individual"
WHERE (contains(tags, "player") OR contains(tags, "jogador"))
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC

// Settings
preset: compact
columns: 3
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Quests Liberadas

```dataview
TABLE quest_status, danger_level, location, faction
FROM "CAMPANHA/Quests"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND quest_status != "Concluída"
AND quest_status != "Falhou"
SORT file.name ASC
```

## Rumores Liberados

```dataview
TABLE status, danger_level, location, faction
FROM "CAMPANHA/Rumors"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

---

## Territórios Conhecidos

```datacards
TABLE cover, region, leader, population
FROM "Territories"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND NoteStatus != "Placeholder"
SORT file.name ASC

// Settings
preset: portrait
columns: 4
imageProperty: cover
cardSpacing: 4
showImageOnHover: true
```

## Locais Conhecidos

```datacards
TABLE cover, territory, info
FROM "Locations"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND NoteStatus != "Placeholder"
SORT file.name ASC

// Settings
preset: grid
columns: 5
imageProperty: cover
cardSpacing: 4
showImageOnHover: true
```

## Facções Conhecidas

```datacards
TABLE thumbnail, status, leader, territory
FROM "Factions"
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND NoteStatus != "Placeholder"
SORT file.name ASC

// Settings
preset: compact
columns: 4
imageProperty: thumbnail
cardSpacing: 4
showImageOnHover: true
```

---

> [!infobox]- CALENDÁRIO
> ```calendarium
> ```

> [!note]- COMO USAR ESTA HOME
> - Use os mapas para se localizar.
> - Use personagens, facções, territórios e locais conhecidos como referência rápida.
> - Quests e rumores aparecem aqui apenas quando estiverem liberados para os jogadores.
> - B-Sides, segredos de origem e bastidores ficam fora desta página até serem revelados em jogo.

---

2026, © **Omnisvera**
