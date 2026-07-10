# Omnisvera Companion — RAG Watchdog

- Atualizado em: 2026-07-10T09:52:32-03:00
- Base URL: `http://127.0.0.1:8787`
- Casos testados: 8
- OK: 8
- Falhas: 0
- Vault mudou desde a última execução: True
- Índice reconstruído: False

## Resumo

| Caso | Modo | Status | Pergunta | Fontes |
|---|---|---|---|---|
| `vezemir_age` | player | OK | Quantos anos tem Vezemir? | Characters/Individual/Vezemir.md |
| `vezemir_about` | player | OK | O que sabemos sobre Vezemir? | Characters/Individual/Vezemir.md |
| `varkh_about` | player | OK | Quem é Varkh? | Characters/Individual/Varkh Nimalis.md |
| `nimalis_about` | player | OK | O que sabemos sobre Nimalis? | Locations/Nimalis.md |
| `rumors_overview` | player | OK | Quais rumores estão ativos? | CAMPANHA/Rumors/01 - Dragões ao Sul de Nimalia.md<br>CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md<br>CAMPANHA/Rumors/03 - Caravana Acidentada na Estrada de Avenor.md<br>CAMPANHA/Rumors/04 - O Frasco Afogado Está Silencioso.md<br>CAMPANHA/Rumors/05 - A Guarda Real Está Fechando Rotas.md |
| `quests_overview` | player | OK | Quais missões estão ativas? | CAMPANHA/Quests/01 - Investigar Avistamentos de Dragões.md<br>CAMPANHA/Quests/02 - Investigar Remédios Falsos de Maré Baixa.md<br>CAMPANHA/Quests/03 - Explorar a Passagem Sob a Estrada.md |
| `dorn7_player_block` | player | OK | O que sabemos sobre DORN-7? | — |
| `frasco_player_block` | player | OK | Onde fica O Frasco Afogado? | — |

## Falhas e recomendações

Nenhuma falha detectada nos casos atuais.
## Próximos passos

- Adicionar novos casos sempre que o Sage encontrar uma resposta ruim.
- Manter correções automáticas limitadas a reindexação e diagnóstico.
- Fazer alterações de código do RAG em commits pequenos e rastreáveis.
