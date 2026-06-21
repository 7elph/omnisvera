---
obsidianUIMode: preview
NoteIcon: magicitem
NoteStatus: Template
thumbnail:
cover:
status: Desconhecido
visibility: gm
location:
territory:
faction:
religion:
class:
race:
role: npc
occupation:
chapters: []
tags:
  - template
  - character
  - npc
---

# NOME DO PERSONAGEM

> [!NOTE|clean no-i right]+ Retrato
> Adicionar o retrato quando estiver disponível.

## Visão Geral

**Nome:**

**Título:**

**Apelido:**

**Reputação:**

**Classe:**

**Raça:**

**Idade:**

**Status:**

**Localização:**

**Território:**

**Facção:**

**Religião:**

**Ocupação:**

**Associados:**

**Inimigos:**

---

## História

Escrever a origem, o acontecimento transformador e a situação atual do personagem.

---

## Personalidade

**Temperamento:**

**Virtudes:**

**Defeitos:**

**Medos:**

**Crenças:**

---

## Habilidades

Descrever habilidades importantes para a narrativa e, quando necessário, para o sistema.

---

## Segredos

> [!gm]- Segredos do mestre
> - Adicionar segredo, verdade oculta ou informação ainda não confirmada.

---

## Equipamentos

- _Adicionar equipamento._

---

## Aparência

Descrever características físicas, roupas, postura e elementos reconhecíveis.

---

## Papel na Campanha

Registrar como o personagem se conecta aos outros protagonistas, às facções e ao conflito central.

## Aparições

```dataview
TABLE date, description
FROM #story
WHERE contains(characters, this.file.link)
SORT file.name ASC
```
