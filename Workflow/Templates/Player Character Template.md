---
obsidianUIMode: preview
NoteIcon: magicitem
NoteStatus: Template
thumbnail:
cover:
status: Vivo
visibility: gm
location:
territory:
faction:
religion:
class:
race:
level: 1
alignment:
role: player
chapters: []
forca:
destreza:
constituicao:
inteligencia:
sabedoria:
carisma:
classe_armadura:
pontos_vida:
bonus_ataque:
jogada_protecao:
movimento:
tags:
  - template
  - character
  - player
---

# NOME — TÍTULO

> [!NOTE|clean no-i right]+ Nome
> Adicionar o retrato principal quando estiver disponível.

## Atributos

> [!info] Valores reutilizáveis
> Os números abaixo vêm do frontmatter. Outras notas podem consultá-los com Dataview, por exemplo: `` `= [[Vezemir]].forca` ``.

| FOR | DES | CON | INT | SAB | CAR |
|:--:|:--:|:--:|:--:|:--:|:--:|
| `= this.forca` | `= this.destreza` | `= this.constituicao` | `= this.inteligencia` | `= this.sabedoria` | `= this.carisma` |

| Combate | Valor |
|:--|--:|
| Classe de Armadura | `= this.classe_armadura` |
| Pontos de Vida | `= this.pontos_vida` |
| Bônus de Ataque | `= this.bonus_ataque` |
| Jogada de Proteção | `= this.jogada_protecao` |
| Movimento | `= this.movimento` |

## Visão Geral

**Títulos:**

**Apelido:**

**Localização Atual:**

**Território:**

**Reputação Pública:**

**Gênero:**

**Classe:**

**Raça:**

**Idade:**

**Altura:**

**Nível:** 1

**Alinhamento:**

**Status:**

**Afiliação:**

**Afiliações Anteriores:**

**Associados Conhecidos:**

**Inimigos Conhecidos:**

**Origem:**

**Posses:**

---

## História

> <h4>"Citação do personagem."</h4>

Registrar a origem e o acontecimento transformador.

---

## Marco da História

Descrever um arco importante.

---

## Atualidade

Registrar a situação no início da campanha.

---

## Personalidade

**Temperamento:**

> [!infobox]
>
> Adicionar o thumbnail quando estiver disponível.

**Virtudes:**

**Defeitos:**

**Medos:**

**Crenças:**

---

## Habilidades

**Habilidade:**
Descrição.

---

## Segredos

> [!gm]- Segredos do mestre
> - Adicionar segredo ou questão deliberadamente em aberto.

---

## Equipamentos

### Item

Descrição.

---

## Aparência

Descrever características físicas, roupas, postura e elementos reconhecíveis.

---

## Armas e Equipamento

Adicionar uma consulta DataCards somente quando existirem notas de itens vinculadas ao personagem.

### Armas e carga

- _Adicionar._

### Idiomas

- _Adicionar._

### Habilidades especiais

- _Adicionar apenas regras confirmadas ou marcar como autorais pendentes._

---

## Capítulos

```dataview
TABLE date, description
FROM #story
WHERE contains(characters, this.file.link)
SORT file.name ASC
```
