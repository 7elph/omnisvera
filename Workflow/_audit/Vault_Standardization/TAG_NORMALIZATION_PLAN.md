# Omnisvera — Plano Dry-Run de Normalizacao de Tags

Gerado em: 2026-07-01 04:07

> [!IMPORTANT]
> Este plano nao alterou nenhuma nota.
> A estrategia segura e adicionar tags oficiais e preservar tags legacy/hibridas.

## Resumo

| metrica | valor |
|---|---:|
| notas analisadas | 329 |
| notas candidatas | 46 |
| baixo risco | 46 |
| medio risco | 0 |
| alto risco | 0 |

## Baixo risco

Casos simples como `local` -> adicionar `location`, `faccao` -> adicionar `faction`, `raca` -> adicionar `race`.

| Arquivo | Tags atuais relevantes | Tags oficiais a adicionar | Tags preservadas | Risco | Observacao |
|---|---|---|---|---|---|
| `Characters/Individual/Augustus Terra Decimus.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Dragão de Colar Dourado.md` | `criatura`, `npc`, `personagem` | `character` | `criatura`, `npc`, `personagem` | low | Adicionar `character` preservando `criatura`. Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Elarion Vaelthor.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/General Cassian Valerius.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Kaelen, o Flagelo.md` | `antagonista`, `npc`, `personagem` | `character` | `antagonista`, `npc`, `personagem` | low | Adicionar `character` preservando `antagonista`. Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Lorde Malakar.md` | `antagonista`, `npc`, `personagem` | `character` | `antagonista`, `npc`, `personagem` | low | Adicionar `character` preservando `antagonista`. Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Mestre Odran Veyl.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Mira Valen.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Padre Oric.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Raziel.md` | `jogador`, `personagem` | `character` | `jogador`, `personagem` | low | Adicionar `character` preservando `jogador`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Unidade DORN-7.md` | `criatura`, `npc`, `personagem` | `character` | `criatura`, `npc`, `personagem` | low | Adicionar `character` preservando `criatura`. Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Vandor, o Senhor das Bestas.md` | `antagonista`, `npc`, `personagem` | `character` | `antagonista`, `npc`, `personagem` | low | Adicionar `character` preservando `antagonista`. Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Varkh Nimalis.md` | `jogador`, `personagem` | `character` | `jogador`, `personagem` | low | Adicionar `character` preservando `jogador`. Adicionar `character` preservando `personagem`. |
| `Characters/Individual/Vezemir.md` | `jogador`, `personagem` | `character` | `jogador`, `personagem` | low | Adicionar `character` preservando `jogador`. Adicionar `character` preservando `personagem`. |
| `Classes/Alquimista.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/Clérigo.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/Guerreiro.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/INDICE_DE_CLASSES.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/Ladrão.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/Mago.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Classes/Vampiro.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Factions/Culto dos Sussurrantes.md` | `antagonista` | `character` | `antagonista` | low | Adicionar `character` preservando `antagonista`. |
| `MAPA DE EARTHROPO.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `MAPA DE NIMALIA.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Races/INDICE_DE_RACAS.md` | `raca` | `race` | `raca` | low | Adicionar `race` preservando `raca`. |
| `Religion/Caminho dos Errantes.md` | `religiao` | `religion` | `religiao` | low | Adicionar `religion` preservando `religiao`. |
| `Religion/Fé dos Antigos.md` | `religiao` | `religion` | `religiao` | low | Adicionar `religion` preservando `religiao`. |
| `Religion/Igreja das Chamas.md` | `religiao` | `religion` | `religiao` | low | Adicionar `religion` preservando `religiao`. |
| `Religion/RELIGION.md` | `religiao` | `religion` | `religiao` | low | Adicionar `religion` preservando `religiao`. |
| `Templates/Characters/Antagonista.md` | `antagonista`, `personagem` | `character` | `antagonista`, `personagem` | low | Adicionar `character` preservando `antagonista`. Adicionar `character` preservando `personagem`. |
| `Templates/Characters/Criatura.md` | `criatura`, `personagem` | `character` | `criatura`, `personagem` | low | Adicionar `character` preservando `criatura`. Adicionar `character` preservando `personagem`. |
| `Templates/Characters/NPC Importante.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Templates/Characters/NPC Menor.md` | `npc`, `personagem` | `character` | `npc`, `personagem` | low | Adicionar `character` preservando `npc`. Adicionar `character` preservando `personagem`. |
| `Templates/Characters/Personagem Jogador.md` | `jogador`, `personagem` | `character` | `jogador`, `personagem` | low | Adicionar `character` preservando `jogador`. Adicionar `character` preservando `personagem`. |
| `Templates/Classes/Arquétipo Narrativo.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Templates/Classes/Classe Base.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Templates/Classes/Especialização.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Templates/RPG/Classe.md` | `classe` | `class` | `classe` | low | Adicionar `class` preservando `classe`. |
| `Templates/RPG/Raça.md` | `raca` | `race` | `raca` | low | Adicionar `race` preservando `raca`. |
| `Templates/RPG/Religião.md` | `religiao` | `religion` | `religiao` | low | Adicionar `religion` preservando `religiao`. |
| `Territories/Campos de Earthropo.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Territories/Floresta de Avenor.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Territories/INDICE_DE_TERRITORIOS.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Territories/Mar da Neblina.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Territories/Nimalia.md` | `territorio` | `territory` | `territorio` | low | Adicionar `territory` preservando `territorio`. |
| `Workflow/_audit/Class_Rules_Standardization/RULES_FOLDER_CONSOLIDATION_REPORT.md` | `raca` | `race` | `raca` | low | Adicionar `race` preservando `raca`. |

## Medio risco

Casos que envolvem `Category/*`, `settlement` ou interpretacao de tipo real da nota.

- Nenhum caso identificado.

## Alto risco

Reservado para casos que afetem diretamente Dataview/DataCards/Home ou tags de semantica ambigua severa.

- Nenhum caso identificado.

## Tags preservadas sem migracao automatica

- `story`: manter como eixo narrativo/capitulo por enquanto.
- `bside`: manter como tag narrativa especial.
- `old-dragon`: manter como tag de sistema/campanha.
- `Category/*`: preservar ate revisar consultas Dataview/DataCards.

## Proxima etapa recomendada

Revisar este plano com o Sage e aplicar apenas os casos de baixo risco em uma Fase B2,
com commit proprio e validacao de Dataview/DataCards depois.
