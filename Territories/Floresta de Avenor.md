---
obsidianUIMode: preview
NoteIcon: settlement
NoteStatus: Active
status: Ativa
visibility: shared
type: Região florestal
capital:
leader: Desconhecido
government: Nenhum governo unificado
region: Fronteira oriental de Nimalia
population: Desconhecida
cover: zz_media/avenor.png
tags:
  - territory
  - earthropo
  - forest
  - avenor
---

# Floresta de Avenor

> [!NOTE|clean no-i right]+ Floresta de Avenor
> ![[avenor.png|400]]

Avenor é uma grande região florestal fora do Reino de [[Nimalia]]. Sua borda ocidental forma parte da fronteira do reino, enquanto seu interior reúne trilhas antigas, rios, comunidades pequenas e áreas pouco conhecidas.

## Geografia

- **Oeste:** campos e estradas de Nimalia.
- **Interior:** floresta densa, colinas, cursos d’água e ruínas.
- **Posição cartográfica:** leste ou nordeste de [[Nimalis]].

## Lugares conhecidos

- [[Leth'valora]], pequena vila élfica destruída.
- A antiga fortaleza onde [[Elarion Valthor]] criou [[Players/Characters/Vezemir]].
- Trilhas usadas por caçadores, mensageiros e viajantes.

## Relação com os elfos

Leth'valora não era o reino élfico. Seus habitantes escolheram viver fora do grande território élfico que será apresentado futuramente.

## Pessoas relacionadas

```dataview
TABLE status, location, faction
FROM "Characters"
WHERE contains(string(territory), this.file.name)
SORT file.name ASC
```

> [!gm]- Desenvolvimento
> [[Bosque Sussurrante]] pode tornar-se uma região interna de Avenor, mas ainda não possui posição ou função confirmada.
