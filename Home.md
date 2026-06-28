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

# Omnisvera — Home dos Jogadores

> [!info]+ CONTEÚDO LIBERADO
> Esta Home mostra apenas conteúdo público, conhecido pelos jogadores ou explicitamente liberado.
>
> Se uma nota ainda não tiver classificação de visibilidade, ela não deve aparecer automaticamente aqui.

> [!warning]- ÁREA DO MESTRE
> [[Home_Mestre]] é uma área de preparação e pode conter spoilers, segredos e relatórios técnicos.

## Entrada rápida

- [[Calendar|Calendário de Nimalia]]
- [[MAPA DE EARTHROPO|Mapa de Earthropo]]
- [[MAPA DE NIMALIA|Mapa de Nimalia]]
- [[MAPA DE NIMALIS|Mapa de Nimalis]]

> [!infobox]- Calendário
> ```calendarium
> ```

## Personagens dos jogadores

```dataview
TABLE
  ("<img src='" + thumbnail + "' width='60' style='border-radius:4px;box-shadow:0 0 3px rgba(255, 255, 255, 0.4);' />") AS "Imagem",
  status,
  location,
  territory,
  faction
FROM "Characters"
WHERE contains(tags, "player")
AND (visibility = "Jogadores" OR visibility = "Público")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Locais conhecidos

```dataview
TABLE cover, territory, info
FROM #location
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND !contains(file.path, "Workflow/")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Facções conhecidas

```dataview
TABLE thumbnail, status, leader, territory
FROM #faction
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND !contains(file.path, "Workflow/")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT file.name ASC
```

## Conteúdos liberados

Handouts e encontros não fazem parte da estrutura operacional desta etapa.

Conteúdo público deve aparecer nas seções de personagens, locais, facções e crônicas jogadas quando `visibility` permitir.

## Crônicas jogadas

```dataview
TABLE date, description
FROM #story
WHERE (visibility = "Jogadores" OR visibility = "Público")
AND !contains(file.path, "Workflow/")
AND gm_secret != true
AND spoiler_level != "medium"
AND spoiler_level != "heavy"
SORT date ASC
```

## Nota de segurança

Este painel é conservador por padrão. Se algo que os jogadores já conhecem não aparecer aqui, a nota provavelmente ainda precisa receber campos como:

```yaml
visibility: Jogadores
visibility: Público
gm_secret: false
spoiler_level: none
```

---

2026, © **Omnisvera**
