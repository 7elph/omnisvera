# Relatório do Micro-Piloto de Taxonomia — Omnisvera

Data: 2026-06-27

## Escopo

Micro-piloto técnico limitado a 4 notas. Não houve migração em massa, renomeação de pastas, remoção de campos antigos ou reescrita de lore.

## Notas alteradas

| nota | tipo testado | alteração aplicada |
|---|---|---|
| `Characters/Individual/Vezemir.md` | Personagem jogador | Adicionados campos `type`, `visibility`, `spoiler_level`, `gm_secret`, `campaign_status`, `chapters` e tags compatíveis. |
| `Factions/Coroa de Nimalia.md` | Facção | Adicionados campos de visibilidade, estado operacional, território, mídia vazia preservada, `chapters` e tags `faccao`/`coroa-de-nimalia`. |
| `Territories/Floresta de Avenor.md` | Território/local | Adicionados campos de visibilidade, status operacional, `thumbnail` compatível e `chapters`. |
| `Items/Grisalma.md` | Item/artefato | Adicionados campos de visibilidade, estado de campanha, `chapters` e tag `artefato`. |

## Campos aplicados

- `type`;
- `visibility`;
- `spoiler_level`;
- `gm_secret`;
- `campaign_status`;
- `chapters`;
- `thumbnail`, quando já havia imagem equivalente segura;
- `status`, preservado quando já existia.

## Tags aplicadas

- `personagem`;
- `jogador`;
- `conclave-dos-errantes`;
- `sentinelas-de-lethvalora`;
- `faccao`;
- `coroa-de-nimalia`;
- `territorio`;
- `artefato`.

## Consultas afetadas

- `Home.md` deve conseguir exibir notas com `visibility: Jogadores` ou `visibility: Público`, sem depender de `player_known`.
- `Home_Mestre.md` deve continuar enxergando facções, territórios e atualizações recentes.
- Supercharged Links deve aplicar cor às novas tags `sentinelas-de-lethvalora` e `nobreza-de-nimalia`, preservando os UIDs antigos.

## Links quebrados encontrados

Não foi feita varredura completa de links quebrados nesta etapa. O piloto preservou links existentes e adicionou apenas links já usados no vault, exceto `[[Reino de Nimalia]]` em notas de facção, que já fazia parte do padrão proposto e deve ser validado no próximo lote.

## Comportamento esperado no Obsidian

- Vezemir passa a ser elegível para consultas seguras da Home dos Jogadores.
- Grisalma passa a ser elegível como item conhecido dos jogadores.
- Coroa de Nimalia permanece conteúdo do mestre por padrão.
- Floresta de Avenor passa a ter metadados mínimos compatíveis com território público.

## Problemas pendentes

- Ainda existem campos herdados em notas piloto, como `chapter`, `state`, `Alignment` e `Government`. Eles foram preservados por compatibilidade.
- Não houve padronização visual completa dos corpos das notas.
- Não houve validação visual dentro do Obsidian aberto.
- A alteração local de Leaflet por `lastAccessed` permanece fora do escopo.

## Recomendação para próximo lote

Se a validação visual no Obsidian estiver correta, o próximo lote pode migrar entre 8 e 12 notas relacionadas ao eixo inicial da campanha:

1. os três personagens jogadores;
2. facções diretamente citadas por eles;
3. territórios/localizações já conhecidos;
4. itens já revelados;
5. rumores públicos ou de mestre claramente separados por `visibility`.
