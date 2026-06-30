---
obsidianUIMode: preview
NoteIcon: audit
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
created_by: Codex
tags:
  - audit
  - classes
  - regras
---

# Relatório — Padronização de Classes e Regras

## Status

LOTE 6 APLICADO.

Este lote padronizou a camada de classes e regras de apoio sem executar migração em massa de personagens.

## Classes Padronizadas

| Arquivo | Status | Observação |
|---|---|---|
| `Classes/Guerreiro.md` | Padronizado | Guerreiro confirmado como classe clássica. `Homem de Armas` permanece apenas como referência histórica, não classe ativa. |
| `Classes/Clérigo.md` | Padronizado | Resumo autoral, sem reprodução extensa de regras. |
| `Classes/Ladrão.md` | Padronizado | Mantido como classe base, mas Raziel não usa mais Ladrão operacionalmente. |
| `Classes/Mago.md` | Padronizado | Mantido como classe base para NPCs e referência futura. |
| `Classes/Alquimista.md` | Padronizado | Classe/arquétipo ligado a Varkh, sem copiar suplemento. |
| `Classes/Vampiro.md` | Padronizado | Classe especial/restrita, ligada a Raziel, Sangue Antigo e Clã Sanguinallis. |

## Raças Operacionais Consolidadas

Consolidadas em `Races/`:

| Arquivo | Visibilidade | Observação |
|---|---|---|
| `Antropo.md` | Jogadores | Substitui o termo beastfolk. Raça predominante em Nimalia. |
| `Humano.md` | Jogadores | Humanos existem, mas não são maioria automática em Omnisvera. |
| `Elfo.md` | Jogadores | Ligado a Avenor, Leth'valora e futuro reino élfico. |
| `Meio-Elfo.md` | Jogadores | Ligado a Vezemir e ao eixo humano/élfico. |
| `Anão.md` | Jogadores | Ligado a Gharok e ao futuro reino anão. |
| `Dragonborn.md` | Jogadores | Reino futuro ao noroeste; `Dragonborn` fixado como grafia operacional. |
| `Kenku.md` | Jogadores | Ligado a Varkh e à presença urbana/corvídea. |
| `Vampiro.md` | Mestre | Restrita, ligada a Raziel, Sangue Antigo e Clã Sanguinallis. |
| `Halfling.md` | Mestre | Mantida como raça em revisão/bônus futuro, sem uso central confirmado. |

## Índices Atualizados

| Arquivo | Ajuste |
|---|---|
| `Classes/INDICE_DE_CLASSES.md` | Índice oficial das classes em `Classes`. |
| `Races/INDICE_DE_RACAS.md` | Índice oficial das raças em `Races`. |
| `Rules/Spells/INDICE_DE_MAGIAS.md` | Recebeu regra explícita para não reproduzir textos protegidos. |

## Templates Alinhados

| Template | Ajuste |
|---|---|
| `Templates/RPG/Classe.md` | Estrutura operacional de classe, com uso em mesa e consulta de personagens. |
| `Templates/RPG/Raça.md` | Estrutura operacional de raça, com presença em Omnisvera e uso em mesa. |
| `Templates/RPG/Magia.md` | Estrutura autoral para magias, sem reprodução literal de livros. |
| `Templates/RPG/Monstro.md` | Estrutura autoral para monstros/criaturas, sem bloco completo protegido de estatísticas. |

## Conteúdo Preservado / Não Migrado

- A pasta `Races/` foi assumida como pasta oficial de raças.
- O conteúdo útil de `Rules/Races` foi fundido nas notas de `Races/`.
- `Rules/Classes` e `Rules/Races` foram removidas para evitar duplicação.
- Não houve renomeação de pastas.
- Não houve criação de notas de magias completas.

## Riscos e Pendências

| Item | Status | Observação |
|---|---|---|
| `Rules/Classes` / `Rules/Races` | Resolvido | Removidas após consolidação em `Classes` e `Races`. |
| Grafia Dragonborn/Dragonbourn | Resolvido | `Dragonborn` fixado como nome de arquivo e `Dragonbourn` mantido como alias. |
| Vampiro | Pendente | Separar definitivamente classe, raça/condição, Sangue Antigo e poderes de Raziel. |
| Regras de Kenku | Pendente | Definir limite mecânico da imitação vocal. |
| Antropos | Pendente | Definir se haverá sublinhagens mecânicas ou apenas variação cultural/visual. |

## Próximo Lote Recomendado

Lote 7 — Quests e Rumores.

Objetivo: padronizar `CAMPANHA/Quests`, `CAMPANHA/Rumors`, templates de Quest/Rumor e impedir que pistas públicas vazem segredos do mestre.
