---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Ativo
tags:
  - workflow
  - audit
  - padronizacao
---

# Backlog de Padronização do Vault

> [!NOTE]
> Este arquivo registra a direção atual de padronização do Omnisvera antes dos próximos lotes de migração de notas.

## Decisões Aplicadas Agora

- `EARTHROPO/01 - Ecos do Mundo Perdido.md` deve ser a versão pública/jogável do capítulo.
- `CAMPANHA/ESTADO_DA_CAMPANHA.md` deve conter a versão completa do mestre, com segredos, bastidores e controle de mesa.
- Histórias de origem dos personagens devem funcionar como **B-Sides**, não como capítulos numerados.
- Capítulos numerados continuam com tags `chapter`, `story`, `chapterXX`.
- Origens passam a usar `story`, `bside`, `origin-story` e tags específicas como `origin-vezemir`.
- `Home_Mestre.md` continua como navegação visual e aponta para o Estado da Campanha como painel central.

## Estrutura Atual por Pasta

| Pasta | Quantidade atual | Próxima ação |
|---|---:|---|
| `Characters/Individual` | 14 | Padronizar todos pelo template de personagem apropriado |
| `Locations` | 17 + índice | Padronizadas no Lote 8; revisar pins/mapas em lote próprio |
| `Territories` | 4 + índice | Padronizadas no Lote 9; fronteiras/pins ainda pendentes |
| `Factions` | 10 | Padronizadas no Lote 3; revisar apenas após decisões do Sage |
| `Lore` | 9 | Padronizadas no Lote 4; revisar cosmologia após decisões do Sage |
| `Items` | 9 | Padronizadas no Lote 5; revisar mecânicas após decisões do Sage |
| `Classes` | 6 | Manter classes confirmadas; sem `Homem de Armas` |
| `CAMPANHA/Quests` | índice + 1 quest | Base inicial criada; expandir quando houver decisão de mesa |
| `CAMPANHA/Rumors` | índice + 1 rumor | Base inicial criada; expandir quando houver decisão de mesa |
| `Templates/RPG` | 9 | Manter alinhado com capítulo público, B-Side e mesa |
| `Templates/Characters` | 5 | Alinhar com padrão real dos personagens existentes |

## Padrão de Story

### Capítulos Numerados

Usar para sessões/arcos principais da campanha.

Campos esperados:

- `type: story`
- `visibility: Jogadores` ou `Público`
- `spoiler_level: light` ou `none`
- `gm_secret: false`
- `tags: story`, `chapter`, `chapterXX`

Notas desse tipo devem evitar segredos pesados. O conteúdo secreto fica no `Estado da Campanha`.

### B-Sides / Origens

Usar para capítulos de origem de personagens.

Campos esperados:

- `type: story`
- `visibility: Mestre`
- `spoiler_level: medium` ou `heavy`
- `gm_secret: true`
- `tags: story`, `bside`, `origin-story`, `origin-personagem`

B-Sides podem conter conteúdo pessoal, passado sensível e revelações que não devem aparecer na Home dos Jogadores.

## Notas Criadas para Centralizar Menções

- `Territories/Mar da Neblina.md`
- `Characters/Individual/Unidade DORN-7.md`

## Próximos Lotes Recomendados

### Lote 1 — Personagens

Padronizar `Characters/Individual` primeiro, porque os personagens alimentam:

- capítulos;
- facções;
- relações pessoais;
- DataCards;
- Home do Mestre;
- Home dos Jogadores.

Prioridade:

1. Vezemir
2. Varkh Nimalis
3. Raziel
4. Mira Valen
5. Mestre Odran Veyl
6. Unidade DORN-7

### Lote 2 — Geografia Jogável

Padronizar:

1. Nimalis
2. Nimalia
3. Floresta de Avenor
4. Mar da Neblina
5. Ruínas de Valthor
6. Fortaleza de Gharok

### Lote 3 — Facções Ativas

Status: aplicado.

Padronizadas:

1. Coroa de Nimalia
2. Guarda Real de Nimalia
3. Conclave dos Errantes
4. Guilda dos Mercadores
5. Guardiões do Véu Cinzento
6. Clã Sanguinallis
7. Sentinelas de Leth'valora
8. Nobreza de Nimalia
9. Rede de Falsificadores de Maré Baixa
10. Culto dos Sussurrantes

Observação: `Clã Sanguinallis`, `Rede de Falsificadores de Maré Baixa` e `Culto dos Sussurrantes` permanecem como notas de mestre ou rascunho por conterem spoilers, suspeitas ou cânone ainda não confirmado.

### Lote 4 — Lore e Fenômenos

Status: aplicado.

Padronizadas:

1. Véu Cinzento
2. Criadores
3. Sangue Antigo
4. Remédios Falsos de Maré Baixa
5. Lore pública versus lore de mestre
6. Fenômenos, mitos e registros históricos
7. Eclipse de Obsidiana
8. O Fraturamento
9. Ancião Primordial
10. Vampiro Sanguinallis

Observação: lore sensível ligada a Raziel, Criadores, Fraturamento e Remédios Falsos permanece com `visibility: Mestre` até existir versão pública ou decisão do Sage.

### Lote 5 — Itens

Status: aplicado.

Padronizadas:

- itens de Vezemir;
- itens de Raziel;
- itens de Varkh;
- itens ligados ao primeiro capítulo;
- relíquias, artefatos, escudos, armas e objetos narrativos.

Observação: `O Frasco Afogado` permanece em `Items` por enquanto, mas pode migrar futuramente para `Locations` se o Sage preferir tratá-lo como estabelecimento jogável.

### Lote 6 — Classes e Regras

Status: aplicado.

Padronizadas:

- classes confirmadas;
- raças confirmadas;
- notas mecânicas próprias da campanha;
- evitar conteúdo protegido de livros;
- manter apenas estrutura, resumo próprio e campos operacionais.

Relatório: [[CLASSES_AND_RULES_STANDARDIZATION_REPORT]]

### Lote 7 — Quests e Rumores

Status: aplicado como base inicial.

Criados/ajustados:

- `Templates/RPG/Quest.md`
- `Templates/RPG/Rumor.md`
- `CAMPANHA/Quests/Quest 01 - Investigar Avistamentos de Dragões.md`
- `CAMPANHA/Rumors/Rumor 01 - Dragões ao Sul de Nimalia.md`

Consultas operacionais foram ajustadas para usar `CAMPANHA/Quests` e `CAMPANHA/Rumors`, evitando puxar templates por `#quest` ou `#rumor`.

Relatório: [[QUESTS_AND_RUMORS_STANDARDIZATION_REPORT]]

Próximos rumores/quests possíveis:

- remédios falsos;
- tremor na estrada;
- símbolo antigo nos frascos;
- rumor vindo do Mar da Neblina;
- investigação do Conclave dos Errantes.

### Lote 8 — Locations restantes

Status: aplicado.

Padronizados:

- bairros de [[Nimalis]];
- [[Maré Baixa]];
- [[Mercado Central]];
- [[Distrito Comercial]];
- [[Porto de Nimalia]];
- [[Casa da Moeda de Nimalia]];
- [[Leth'valora]];
- locais sensíveis de origem de [[Vezemir]].

Criado:

- `Locations/INDICE_DE_LOCAIS.md`

Consultas operacionais foram ajustadas para usar `FROM "Locations"` em vez de `FROM #location`.

Relatório: [[LOCATIONS_STANDARDIZATION_REPORT]]

### Lote 9 — Territories e Mapas

Status: aplicado.

Padronizados:

- `Territories/Nimalia.md`
- `Territories/Floresta de Avenor.md`
- `Territories/Mar da Neblina.md`
- `Territories/Campos de Earthropo.md`

Movidos conceitualmente para `Locations`:

- `Vale Dourado`
- `Bosque Sussurrante`

Criado:

- `Territories/INDICE_DE_TERRITORIOS.md`

Mapas oficiais confirmados:

- `MAPA DE EARTHROPO.md`
- `MAPA DE NIMALIA.md`
- `MAPA DE NIMALIS.md`

Relatório: [[TERRITORIES_AND_MAPS_STANDARDIZATION_REPORT]]

## Pendências de Decisão do Sage

- Se `Home_Mestre.md` deve continuar como Home visual separada ou virar apenas uma versão visual do `Estado da Campanha`.
- Se `Mar da Neblina` será território marítimo, fenômeno ou ambos.
- Se a Unidade DORN-7 deve ficar em `Characters/Individual` ou migrar futuramente para uma pasta de criaturas/entidades.
- Se os B-Sides devem manter nomes `00 - ...` ou ganhar prefixo novo como `B-Side - ...`.
- Se a Home dos Jogadores deve listar capítulos em preparação ou apenas capítulos já jogados.

## Critério de Prontidão

O vault estará pronto para o próximo lote quando:

- templates principais estiverem alinhados;
- capítulo público não contiver segredos pesados;
- Estado da Campanha concentrar os bastidores;
- B-Sides não aparecerem como capítulos numerados;
- links e mídia estiverem sem erros;
- `Sem título.md` for removido ou transformado em nota real.
