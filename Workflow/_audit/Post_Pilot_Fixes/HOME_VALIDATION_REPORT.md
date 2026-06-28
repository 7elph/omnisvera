# Relatório de Validação das Homes Pós-Piloto

Data: 2026-06-27

## Resultado

`Home.md` e `Home_Mestre.md` permanecem consistentes com a decisão atual:

- `Home.md` = Home dos Jogadores;
- `Home_Mestre.md` = dashboard do Mestre;
- `Home_Jogadores.md` não existe na raiz.

## Validações

| verificação | resultado |
|---|---|
| `Home.md` contém `player_known` | Não. |
| `Home.md` contém `life_status` | Não. |
| `Home.md` contém `handout_image` | Não. |
| `Home.md` contém `#session` | Não. |
| `Home.md` contém `Home_Jogadores` | Não. |
| `Home.md` contém `Workflow/Legacy` | Não. |
| `Home.md` contém `Disgraceland` | Não. |
| `Home.md` contém `TRIBUCIA` | Não. |
| `Home_Mestre.md` trata Disgraceland como navegação operacional | Não. |
| `Home_Jogadores.md` está fora da raiz | Sim. |

## Ocorrências históricas

`Home_Jogadores` ainda aparece em relatórios históricos e auditorias. Isso é esperado e não representa Home operacional.

## Bloqueadores

Nenhum bloqueador encontrado nas Homes para o próximo lote.
