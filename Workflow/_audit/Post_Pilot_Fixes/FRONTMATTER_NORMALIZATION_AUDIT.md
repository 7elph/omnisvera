# Auditoria de Normalização de Frontmatter Pós-Piloto

Data: 2026-06-27

## Objetivo

Verificar se os arquivos obrigatórios possuem frontmatter YAML em formato válido, com delimitadores `---` em linhas próprias.

## Resultado

Nenhum frontmatter colapsado foi encontrado nos alvos obrigatórios. Não houve reescrita mecânica de YAML nesta etapa.

## Matriz de auditoria

| arquivo | classificação | ação |
|---|---|---|
| `Home.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Home_Mestre.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Characters/Individual/Vezemir.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Factions/Coroa de Nimalia.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Factions/Nobreza de Nimalia.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Factions/Sentinelas de Leth'valora.md` | `OK_FRONTMATTER` | Metadados operacionais complementados em validação do piloto. |
| `Territories/Floresta de Avenor.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Items/Grisalma.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Raça.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Classe.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Magia.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Item.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Monstro.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Quest.md` | `OK_FRONTMATTER` | Nenhuma. |
| `Templates/RPG/Rumor.md` | `OK_FRONTMATTER` | Nenhuma. |

## Observações

- O caminho `Templates/RPG/Raça.md` foi validado com Unicode explícito por causa de exibição inconsistente de acentos no terminal.
- Não houve conversão de `chapter` para `chapters` nem o inverso.
- Listas YAML existentes foram preservadas.
