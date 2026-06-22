---
obsidianUIMode: preview
NoteIcon: religion
NoteStatus: Active
status: Ativo
visibility: shared
cover: zz_media/ui/card-religiao.webp
tags:
  - home
  - religion
  - index
---

# Religiões de Earthropo

> [!NOTE|clean no-i right]+ Religiões
> ![[zz_media/ui/card-religiao.webp|400]]

Earthropo possui vários deuses, tradições raciais e crenças regionais. Nenhuma nota pública confirma toda a verdade cosmológica.

## Religiões conhecidas

```datacards
TABLE cover, info, status
FROM "Religion"
WHERE file.name != this.file.name
AND (visibility = "player" OR visibility = "shared")
SORT file.name ASC

// Settings
preset: grid
columns: 4
imageProperty: cover
cardSpacing: 4
```

## Referências

- [[Igreja das Chamas]] — instituição organizada presente em Nimalia.
- [[Fé dos Antigos]] — conjunto de tradições antigas e regionais.
- [[Caminho dos Errantes]] — tradição espiritual de viajantes.

O antigo nome “Igreja das Sete Chamas” foi consolidado como uma referência às sete chamas da doutrina da Igreja das Chamas.
