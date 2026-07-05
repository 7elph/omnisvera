---
obsidianUIMode: preview
NoteIcon: class
NoteStatus: Deprecated
type: class
status: Substituído
rules_status: Ponte / compatibilidade
campaign_status: Arquivado
visibility: Mestre
spoiler_level: light
gm_secret: false
created_by: Sage
name: Vampiro
aliases:
  - Classe Vampiro
system: Old Dragon / ponte Omnisvera
class_group: Sobrenatural
primary_attribute:
level:
danger_level: Médio
thumbnail: zz_media/thumbnails/th_raziel.png
cover: zz_media/thumbnails/th_raziel.png
chapters:
  - 00 - As Crônicas de Névoa de Sangue
tags:
  - classe
  - vampiro
  - ponte
  - deprecated
  - raziel
  - class
---

# Vampiro

> [!warning] Nota ponte
> Esta nota era usada como classe, mas a decisão atual do Sage separa a estrutura:
>
> - **Raça/condição:** [[Vampiro]]
> - **Classe:** [[Hemomante]]
> - **Linhagem:** [[Vampiro Sanguinallis]]
> - **Camada única de campanha:** [[Sangue Antigo]]
>
> Manter esta nota por enquanto para não quebrar links antigos, consultas e histórico.

## Decisão Atual

`Vampiro` não deve ser usado como classe principal nova.

Para personagens como [[Raziel]], usar:

```yaml
race: Vampiro
class: Hemomante
```

## Como Interpretar Links Antigos

Se uma nota antiga diz que alguém tem classe Vampiro, ler como:

- a criatura é ou foi tratada como vampírica;
- a mecânica precisa ser convertida para [[Hemomante]] se for personagem jogável;
- a condição racial deve apontar para [[Vampiro]].

## Consulta de Transição

```dataview
TABLE thumbnail, race, class, status, location, faction
FROM "Characters"
WHERE class = "Vampiro" OR class = this.file.link OR contains(string(class), "Vampiro")
SORT file.name ASC
```

## Pendências

- Migrar personagens ativos que ainda usam `class: Vampiro` para `class: Hemomante`, quando seguro.
- Revisar criaturas/NPCs vampíricos caso precisem de classe própria ou apenas raça/condição.
- Remover esta ponte somente depois de confirmar que nenhum Dataview/DataCards depende dela.
