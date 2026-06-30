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
  - itens
---

# Relatório de Padronização — Items

Status: aplicado em 2026-06-29.

## Objetivo

Padronizar a pasta `Items` como quinto lote da fila do vault.

O foco foi deixar armas, relíquias, escudos, objetos pessoais, estabelecimentos importantes e itens narrativos coerentes com o padrão atual do Omnisvera.

## Escopo Aplicado

Foram padronizadas as 9 notas existentes em `Items`.

| nota | tipo | visibilidade | observação |
|---|---|---|---|
| `Grisalma.md` | machado / artefato marcial | Jogadores | item de Vezemir |
| `Muralha de Dorn.md` | escudo / relíquia marcial | Jogadores | item de Vezemir |
| `O Medalhão.md` | medalhão / relíquia | Jogadores | item de Vezemir, mistério ainda em aberto |
| `Adagas de Espectro Fantasma.md` | par de adagas / relíquia vampírica | Jogadores | item de Raziel |
| `Manto Primordial do Ancião.md` | manto / relíquia primordial | Mestre | contém spoiler do Ancião Primordial |
| `Caderninho de Vozes.md` | caderno pessoal | Jogadores | item de Varkh |
| `Máscara de Médico da Peste de Varkh.md` | máscara / equipamento pessoal | Jogadores | item de Varkh |
| `O Frasco Afogado.md` | estabelecimento / símbolo alquímico | Jogadores | origem de Varkh e gancho de remédios falsos |
| `INDICE_DE_ITENS.md` | índice | Mestre | painel operacional |

## Critério Aplicado

- Itens reais receberam `type: item`.
- O índice manteve `type: index`.
- Campos rejeitados foram removidos:
  - `canon_status`;
  - `requires_review`;
  - `Category/Item`.
- Cada item recebeu ou preservou:
  - `item_type`;
  - `owner`;
  - `location`;
  - `visibility`;
  - `spoiler_level`;
  - `gm_secret`;
  - `hooks`;
  - `rumors`;
  - `chapters`.
- Cada item recebeu:
  - `## Visão Geral`;
  - `## Uso em Mesa`;
  - `## Pendências do Sage`.
- O template `Templates/RPG/Item.md` foi alinhado ao padrão aplicado.

## Itens Públicos / Jogadores

Estas notas podem aparecer em consultas filtradas para jogadores:

- [[Grisalma]]
- [[Muralha de Dorn]]
- [[O Medalhão]]
- [[Adagas de Espectro Fantasma]]
- [[Caderninho de Vozes]]
- [[Máscara de Médico da Peste de Varkh]]
- [[O Frasco Afogado]]

## Itens de Mestre / Spoiler

Estas notas não devem aparecer em dashboard de jogadores:

- [[Manto Primordial do Ancião]]

Motivo: a nota cita diretamente o [[Ancião Primordial]] e a origem sensível do item.

## Ajustes Importantes

### Itens de Vezemir

- [[Grisalma]], [[Muralha de Dorn]] e [[O Medalhão]] foram padronizados como itens de jogador.
- Regras provisórias foram preservadas:
  - Grisalma: `2d8` até decisão do mestre.
  - Muralha de Dorn: `+2 CA` até decisão do mestre.
- Propriedades narrativas foram mantidas como ganchos, não como regras finais.

### Itens de Raziel

- [[Adagas de Espectro Fantasma]] ficou como item de jogador.
- [[Manto Primordial do Ancião]] ficou como item de mestre por conter spoiler forte.

### Itens de Varkh

- [[Caderninho de Vozes]] e [[Máscara de Médico da Peste de Varkh]] ficaram como itens públicos/jogáveis.
- [[O Frasco Afogado]] foi mantido em `Items` por enquanto, mas marcado como estabelecimento/símbolo alquímico.

## Pendências do Sage

- Definir imagens para itens de Varkh.
- Decidir se [[O Frasco Afogado]] permanece em `Items` ou migra para `Locations`.
- Confirmar mecânicas finais de [[Grisalma]] e [[Muralha de Dorn]].
- Confirmar se [[O Medalhão]] é chave, selo, símbolo ou relíquia reativa.
- Definir mecânica das [[Adagas de Espectro Fantasma]].
- Definir quando [[Manto Primordial do Ancião]] poderá ser mostrado aos jogadores.

## Validação

Resultado após o lote:

- Frontmatter inválido: `0`
- Wikilinks quebrados: `0`
- Referências de mídia quebradas: `0`
- Ocorrências em `Items`/`Templates/RPG/Item.md` de `canon_status`, `requires_review`, `Category/Item` ou mojibake operacional: `0`

## Próximo Lote Recomendado

Seguir a fila:

1. Padronizar `Classes` e notas mecânicas próximas.
2. Depois consolidar `Quests` e `Rumors`, movendo ou classificando `Quest 1` e `Rumor 1` como notas reais de campanha.
