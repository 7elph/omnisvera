---
obsidianUIMode: preview
NoteIcon: quest
NoteStatus: Draft
type: quest
status: Rascunho
quest_status: Aberta
campaign_status: Em revisão
visibility: Jogadores
spoiler_level: light
gm_secret: false
revealed_in:
created_by: Sage
name: Explorar a Passagem Sob a Estrada
location: "Rota entre [[Nimalis]] e [[Floresta de Avenor]]"
territory: "[[Nimalia]]"
faction:
  - "[[Guarda Real de Nimalia]]"
danger_level: C
hooks:
  - "[[03 - Caravana Acidentada na Estrada de Avenor]]"
rumors:
  - "[[03 - Caravana Acidentada na Estrada de Avenor]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/locations/estrada_antiga.png
cover: zz_media/covers/banner_ecos_do_mundo_perdido.png
tags:
  - quest
  - story
  - capitulo01
  - nimalia
  - avenor
---

# Explorar a Passagem Sob a Estrada

## Gancho Público

Uma estrada secundária entre [[Nimalis]] e a [[Floresta de Avenor]] cedeu depois de um tremor localizado. Sob a terra, viajantes dizem ter visto pedra trabalhada, marcas antigas e luz fria vindo de uma passagem artificial.

## Objetivo Conhecido

Verificar o que apareceu sob a estrada, resgatar sobreviventes se houver, descobrir se a passagem representa perigo imediato e impedir que provas desapareçam.

## Locais Relacionados

- [[Nimalis]]
- [[Floresta de Avenor]]
- [[Antiga Estrada Esquecida]]
- rota secundária da caravana

## Envolvidos Conhecidos

- sobreviventes da caravana;
- viajantes da estrada;
- [[Guarda Real de Nimalia]];
- personagens atraídos pelo acidente.

## Pistas Públicas

- Terra aberta como se algo tivesse empurrado de baixo.
- Pedras antigas que não combinam com obra comum de estrada.
- Sons metálicos vindos do subterrâneo.
- Frascos falsificados misturados à carga da caravana.

## Rumores Relacionados

```dataview
TABLE status, visibility, location
FROM "CAMPANHA/Rumors"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```

## Estado

Quest de abertura do Capítulo 01. A verdade completa da passagem não deve ser explicada cedo demais.

## Uso em Mesa

- Como os jogadores descobrem: acidente na estrada, chamado de ajuda, rumor de caravana tombada ou atração pessoal pela energia antiga.
- Objetivo claro: entrar, observar, sobreviver e sair com informação.
- Complicação: a Guarda Real pode chegar no fim e tentar controlar a área.
- Recompensa: mapa fragmentado, pistas, sobreviventes salvos ou acesso a nova frente.
- Consequência se ignorada: a área pode ser isolada, saqueada ou manipulada por outra facção.

## Pendências do Sage

- Definir se a passagem recebe nome próprio após a sessão.
- Definir qual setor o mapa fragmentado aponta.
- Manter origem real e tecnologia antiga no [[ESTADO_DA_CAMPANHA]].
