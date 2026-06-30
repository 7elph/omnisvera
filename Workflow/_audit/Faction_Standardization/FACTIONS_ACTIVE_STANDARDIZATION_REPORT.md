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
  - faccoes
---

# Relatório de Padronização — Facções

Status: aplicado em 2026-06-29.

## Objetivo

Padronizar a pasta `Factions` como terceiro lote da fila de organização do vault.

O foco foi deixar as facções tecnicamente coerentes para uso em Obsidian, Home/DataCards/Dataview e preparação de mesa, sem inventar lore pesada e sem transformar rascunhos em cânone definitivo.

## Escopo Aplicado

Foram padronizadas as 10 notas atualmente existentes em `Factions`.

| nota | status operacional | visibilidade | observação |
|---|---|---|---|
| `Coroa de Nimalia.md` | ativa | Jogadores | facção política central |
| `Guarda Real de Nimalia.md` | ativa / em revisão | Jogadores | números e comandante ainda em revisão |
| `Nobreza de Nimalia.md` | ativa | Jogadores | casas nobres ainda não definidas |
| `Conclave dos Errantes.md` | ativa | Jogadores | facção ligada a Vezemir e Varkh |
| `Guilda dos Mercadores.md` | ativa | Jogadores | organização econômica de Earthropo |
| `Guardiões do Véu Cinzento.md` | cânone de trabalho | Jogadores | ordem antiga, ainda misteriosa |
| `Sentinelas de Leth'valora.md` | destruída | Jogadores | guarda local da vila destruída |
| `Clã Sanguinallis.md` | em revisão / sensível | Mestre | contém spoilers da origem de Raziel |
| `Rede de Falsificadores de Maré Baixa.md` | em desenvolvimento / sensível | Mestre | contém suspeitas e bastidores do arco de Varkh |
| `Culto dos Sussurrantes.md` | rascunho | Mestre | ainda precisa decisão do Sage |

## Critério Aplicado

- Todas as notas receberam ou preservaram `type: faction`.
- `state`, `canon_status` e `requires_review` foram removidos como campos ativos.
- `status` e `campaign_status` foram usados para estado operacional.
- Tags antigas genéricas foram reduzidas ou convertidas para vocabulário Omnisvera.
- `faction` e `faccao` foram mantidas como tags-ponte para Dataview/DataCards.
- Notas seguras receberam:
  - `visibility: Jogadores`;
  - `spoiler_level: light`;
  - `gm_secret: false`.
- Notas com spoilers de origem/arco receberam:
  - `visibility: Mestre`;
  - `spoiler_level: medium`;
  - `gm_secret: true`.
- HTML antigo e consultas vazias herdadas foram removidos.
- Cada facção recebeu bloco `Uso em Mesa`.
- Cada facção recebeu ou preservou `Pendências do Sage`.

## Ajustes Importantes

### Coroa, Guarda e Nobreza

- A Coroa ficou como autoridade política central de Nimalia.
- A Guarda ficou como braço militar oficial.
- A Nobreza ficou como estrutura social/política do reino, sem casas específicas inventadas.

### Conclave e Mercadores

- O Conclave ficou como rede de aventureiros e errantes.
- A Guilda dos Mercadores ficou como estrutura econômica de Earthropo, não apenas de Nimalia.

### Guardiões e Sentinelas

- Os Guardiões do Véu Cinzento ficaram como ordem antiga em cânone de trabalho.
- Os Sentinelas de Leth'valora ficaram como guarda local destruída no incidente do dragão, não como grande ordem.

### Facções Sensíveis

- `Clã Sanguinallis` foi mantido como nota de Mestre porque ainda entrega estrutura de traição, vingança e hierarquia de Raziel.
- `Rede de Falsificadores de Maré Baixa` foi mantida como nota de Mestre porque contém suspeitas e possíveis culpados do arco de Varkh.
- `Culto dos Sussurrantes` foi mantido como rascunho de Mestre e não deve ser tratado como ameaça ativa até decisão do Sage.

## Padrão Resultante

### Facção pública / segura

```yaml
type: faction
visibility: Jogadores
spoiler_level: light
gm_secret: false
status: Ativa
campaign_status: Ativa
tags:
  - faction
  - faccao
```

### Facção sensível / mestre

```yaml
type: faction
visibility: Mestre
spoiler_level: medium
gm_secret: true
status: Em revisão
campaign_status: Em revisão
tags:
  - faction
  - faccao
```

## Validação

Resultado após o lote:

- Frontmatter inválido: `0`
- Wikilinks quebrados: `0`
- Referências de mídia quebradas: `0`
- Ocorrências operacionais de `state`, `canon_status`, `requires_review`, `Category/Faction`, HTML antigo e `#guarda`: `0`

## Pendências do Sage

- Definir casas nobres de Nimalia.
- Confirmar comandante da Guarda Real.
- Definir liderança/sede do Conclave dos Errantes.
- Definir liderança da Guilda dos Mercadores.
- Definir quanto dos Guardiões do Véu Cinzento pode ser público.
- Criar versão pública do Clã Sanguinallis, se essa facção precisar aparecer para jogadores.
- Decidir se o Culto dos Sussurrantes permanece no cânone, vira rumor falso ou deve ser arquivado.

## Próximo Lote Recomendado

Seguir a fila:

1. Padronizar `Lore`, separando lore pública, lore de mestre e fenômenos.
2. Depois padronizar `Items`, porque já existem itens importantes ligados a Vezemir, Raziel e à campanha inicial.
