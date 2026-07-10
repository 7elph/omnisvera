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
name: Investigar Remédios Falsos de Maré Baixa
location: "[[Maré Baixa]]"
territory: "[[Nimalia]]"
faction:
  - "[[Conclave dos Errantes]]"
  - "[[Guilda dos Mercadores]]"
danger_level: D
hooks:
  - "[[02 - Remédios Falsos da Maré Baixa]]"
rumors:
  - "[[02 - Remédios Falsos da Maré Baixa]]"
chapters:
  - 01 - Ecos do Mundo Perdido
thumbnail: zz_media/thumbnails/th_remedios_falsos.PNG
cover: zz_media/misc/remedios_falsos.png
tags:
  - quest
  - story
  - capitulo01
  - remedios-falsos
  - mare-baixa
---

# Investigar Remédios Falsos de Maré Baixa

## Gancho Público

Remédios falsos começaram a circular em [[Nimalia]], especialmente entre viajantes, trabalhadores pobres e gente que não pode pagar por cura confiável.

Alguns frascos usam símbolos e métodos parecidos com os de [[Mestre Odran Veyl]], mas há sinais de adulteração.

## Objetivo Conhecido

Descobrir de onde vêm os remédios falsos, quem está distribuindo os frascos e por que o nome de Odran está sendo associado ao caso.

## Locais Relacionados

- [[Maré Baixa]]
- [[O Frasco Afogado]]
- [[Porto de Nimalia]]
- rotas entre [[Nimalis]] e a [[Floresta de Avenor]]

## Envolvidos Conhecidos

- [[Varkh Nimalis]]
- [[Mestre Odran Veyl]]
- [[Conclave dos Errantes]]
- [[Guilda dos Mercadores]]
- vítimas envenenadas ou enganadas pelos frascos

## Pistas Públicas

- Frascos escuros reaproveitados.
- Símbolo semelhante ao método de Odran, mas com traços errados.
- Testemunhas que compraram cura barata e pioraram.
- Cargas pequenas circulando junto de caravanas comuns.

## Rumores Relacionados

```dataview
TABLE status, visibility, location
FROM "CAMPANHA/Rumors"
WHERE (contains(hooks, this.file.link) OR contains(rumors, this.file.link))
AND type != "index"
SORT file.name ASC
```

## Estado

Quest inicial ligada ao Capítulo 01. Deve ser apresentada como investigação, não como acusação definitiva contra Odran, a Guilda ou a Coroa.

## Uso em Mesa

- Como os jogadores descobrem: frascos quebrados na estrada, vítimas, mercadores assustados ou contato do Conclave.
- Objetivo claro: rastrear origem e distribuição.
- Complicação: as marcas apontam para Odran, mas parecem adulteradas.
- Recompensa: informação, reputação, pagamento modesto ou acesso a contatos.
- Consequência se ignorada: mais vítimas aparecem e alguém pode culpar a pessoa errada.

## Pendências do Sage

- Definir qual prova física será levada pelo falsificador no fim da sessão.
- Definir quando os jogadores poderão visitar [[O Frasco Afogado]].
- Manter a verdade completa no [[ESTADO_DA_CAMPANHA]].
