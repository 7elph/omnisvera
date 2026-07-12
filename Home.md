---
obsidianUIMode: preview
banner: "zz_media/territories/avenor.png"
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
  <img src="zz_media/misc/omnisvera.png" width="900px">
</div>

# Omnisvera 

> [!cards|5]
> **CAPÍTULO ATUAL**
> [![[zz_media/covers/banner_ecos_do_mundo_perdido.png|sban htiny ctr p+t]]](EARTHROPO/01%20-%20Ecos%20do%20Mundo%20Perdido.md)
>
> **MISSÕES**
> [![[zz_media/covers/cover_missoes_ativas.png|sban htiny ctr p+t]]](#Quests)
>
> **RUMORES**
> [![[zz_media/covers/cover_rumores.png|sban htiny ctr p+t]]](#Rumores)
>
> **PERSONAGENS**
> [![[zz_media/covers/cover_personagens.png|sban htiny ctr p+t]]](#Personagens%20dos%20Jogadores)
>
> **MAPA**
> [![[zz_media/maps/earthropo.png|sban htiny ctr p+t]]](MAPA%20DE%20EARTHROPO.md)

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
> columns: 3
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
preset: full
columns: 4
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Quests

```datacards
TABLE cover, quest_status, danger_level, location, faction
FROM "CAMPANHA/Quests"
WHERE type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND quest_status != "Concluída"
AND quest_status != "Falhou"
SORT file.name ASC

// Settings
preset: grid
columns: 3
imageProperty: cover
cardSpacing: 4
showImageOnHover: true
```

## Rumores

```datacards
TABLE cover, status, danger_level, location, faction
FROM "CAMPANHA/Rumors"
WHERE type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC

// Settings
preset: compact
columns: 3
imageProperty: cover
cardSpacing: 4
showImageOnHover: true
```

---

## Mapas de Consulta

> [!note]- Abrir mapas
> - [[MAPA DE EARTHROPO]]
> - [[MAPA DE NIMALIA]]
> - [[MAPA DE NIMALIS]]

---

## Territórios Conhecidos

```datacards
TABLE cover, region, leader, population
FROM "Territories"
WHERE type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
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
WHERE type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
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
WHERE type != "index"
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
AND NoteStatus != "Placeholder"
SORT file.name ASC

// Settings
preset: full
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
> - Use missões e rumores para decidir o próximo passo.
> - Use os mapas apenas quando precisar se localizar.
> - Use personagens, facções, territórios e locais conhecidos como referência rápida.
> - Quests e rumores aparecem aqui apenas quando estiverem liberados para os jogadores.
> - B-Sides, segredos de origem e bastidores ficam fora desta página até serem revelados em jogo.

---

2026, © **Omnisvera**
