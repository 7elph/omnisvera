---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Aplicado
tags:
  - workflow
  - audit
  - padronizacao
  - lore
---

# Relatório de Padronização — Lore e Fenômenos

Status: aplicado em 2026-06-29.

## Objetivo

Padronizar a pasta `Lore` como quarto lote da fila do vault.

O foco foi separar lore pública, lore de mestre, fenômenos, mitos e rascunhos sem inventar cânone novo e sem mover segredos para notas de jogador.

## Escopo Aplicado

Foram padronizadas as 9 notas existentes em `Lore`.

| nota | tipo | visibilidade | observação |
|---|---|---|---|
| `Véu Cinzento.md` | lore / fenômeno | Jogadores | fenômeno público em cânone de trabalho |
| `Eclipse de Obsidiana.md` | lore / história | Jogadores | evento histórico em revisão |
| `Guardiões do Véu Cinzento.md` | lore / registro | Jogadores | registro de lore; ficha operacional fica em `Factions` |
| `Criadores.md` | lore / mito de criação | Mestre | cosmologia sensível |
| `O Fraturamento.md` | lore / cosmologia | Mestre | rascunho pesado de fundo |
| `Ancião Primordial.md` | lore / entidade | Mestre | spoiler forte de Raziel |
| `Sangue Antigo.md` | lore / mecânica autoral | Mestre | spoiler forte de Raziel |
| `Vampiro Sanguinallis.md` | lore / linhagem | Mestre | spoiler médio de Raziel |
| `Remédios Falsos de Maré Baixa.md` | lore / investigação | Mestre | suspeitas do arco de Varkh |

## Critério Aplicado

- Todas as notas receberam ou preservaram `type: lore`.
- Campos rejeitados foram removidos:
  - `canon_status`;
  - `requires_review`;
  - tags `Category/Lore`.
- HTML antigo foi substituído por Markdown.
- Cada nota passou a ter:
  - `## Visão Geral`;
  - `## Uso em Mesa`;
  - `## Pendências do Sage`.
- Lore pública recebeu:
  - `visibility: Jogadores`;
  - `spoiler_level: light`;
  - `gm_secret: false`.
- Lore sensível recebeu:
  - `visibility: Mestre`;
  - `spoiler_level: medium` ou `heavy`;
  - `gm_secret: true`.
- A mecânica do [[Sangue Antigo]] foi mantida como regra própria do Omnisvera, sem reproduzir material protegido de livros.

## Separação Pública / Mestre

### Público / Jogadores

Estas notas podem aparecer em consultas de jogadores com filtros de visibilidade:

- [[Véu Cinzento]]
- [[Eclipse de Obsidiana]]
- [[Guardiões do Véu Cinzento]]

### Mestre / Spoiler

Estas notas não devem aparecer em dashboard de jogadores:

- [[Criadores]]
- [[O Fraturamento]]
- [[Ancião Primordial]]
- [[Sangue Antigo]]
- [[Vampiro Sanguinallis]]
- [[Remédios Falsos de Maré Baixa]]

## Ajustes Importantes

### Guardiões do Véu Cinzento

A nota em `Lore` foi definida como registro/mistério. A ficha operacional da ordem fica em [[Factions/Guardiões do Véu Cinzento]].

### Sangue Antigo

A mecânica foi preservada como camada original da campanha:

- custo antes de poder;
- poder visível;
- não é magia comum;
- não é ilimitado;
- uso no nível 1 controlado pelo mestre.

### Remédios Falsos

A nota continua como Mestre porque contém suspeitas e bastidores do arco de [[Varkh Nimalis]]. Uma versão pública pode ser criada depois, se necessário.

## Validação

Resultado após o lote:

- Frontmatter inválido: `0`
- Wikilinks quebrados: `0`
- Referências de mídia quebradas: `0`
- Ocorrências em `Lore` de `canon_status`, `requires_review`, `Category/Lore`, HTML antigo ou mojibake operacional: `0`

## Pendências do Sage

- Decidir quanto dos [[Criadores]] poderá ser público.
- Decidir se [[O Fraturamento]] é fato, mito, teoria falsa ou metáfora.
- Definir relação exata entre [[Véu Cinzento]], [[Eclipse de Obsidiana]] e [[Criadores]].
- Confirmar a mecânica final do [[Sangue Antigo]].
- Decidir se haverá versão pública para [[Remédios Falsos de Maré Baixa]].
- Decidir se a lore dos [[Guardiões do Véu Cinzento]] deve ser ainda mais separada entre público e mestre.

## Próximo Lote Recomendado

Seguir a fila:

1. Padronizar `Items`, porque já existem itens importantes ligados a Vezemir, Raziel, Varkh e ao primeiro capítulo.
2. Depois padronizar `Classes`, `Rules` e notas mecânicas, sem copiar conteúdo protegido.
