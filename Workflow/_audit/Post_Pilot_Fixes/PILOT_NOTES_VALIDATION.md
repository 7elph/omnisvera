# Validação das Notas do Piloto

Data: 2026-06-27

## Escopo validado

- `Characters/Individual/Vezemir.md`
- `Factions/Coroa de Nimalia.md`
- `Factions/Nobreza de Nimalia.md`
- `Factions/Sentinelas de Leth'valora.md`
- `Territories/Floresta de Avenor.md`
- `Items/Grisalma.md`

## Resultado por nota

### `Characters/Individual/Vezemir.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; mantém ponte `character/player` e adiciona `personagem/jogador`
- `visibility_ok`: sim, `Jogadores`
- `gm_secret_ok`: sim, `false`
- `chapters_or_story_ok`: sim; preserva `chapter` e possui `chapters`
- `image_fields_ok`: sim
- `dataview_expected`: deve aparecer na Home dos Jogadores como personagem conhecido
- `supercharged_links_expected`: `conclave-dos-errantes` e `sentinelas-de-lethvalora`
- `issues`: mantém tags herdadas em inglês como ponte
- `recommendation`: usar como referência para PCs no lote 2

### `Factions/Coroa de Nimalia.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; `faction`, `faccao`, `coroa-de-nimalia`
- `visibility_ok`: sim, `Mestre`
- `gm_secret_ok`: sim, `false`
- `chapters_or_story_ok`: sim, `chapters: []`
- `image_fields_ok`: sim
- `dataview_expected`: deve aparecer em dashboards do Mestre
- `supercharged_links_expected`: `coroa-de-nimalia`
- `issues`: conteúdo político ainda sintético
- `recommendation`: expandir apenas quando houver decisão de lore

### `Factions/Nobreza de Nimalia.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; `faccao`, `nobreza-de-nimalia`
- `visibility_ok`: sim, `Mestre`
- `gm_secret_ok`: sim, `false`
- `chapters_or_story_ok`: sim, `chapters: []`
- `image_fields_ok`: campos vazios preservados
- `dataview_expected`: deve aparecer em consultas por `#faccao`
- `supercharged_links_expected`: `nobreza-de-nimalia`
- `issues`: nota intencionalmente mínima
- `recommendation`: manter mínima até decisão de casas nobres

### `Factions/Sentinelas de Leth'valora.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; `faction`, `faccao`, `sentinelas-de-lethvalora`
- `visibility_ok`: corrigido para `Mestre`
- `gm_secret_ok`: corrigido para `false`
- `chapters_or_story_ok`: corrigido com `chapters: []`
- `image_fields_ok`: sim
- `dataview_expected`: deve aparecer em consultas do Mestre
- `supercharged_links_expected`: `sentinelas-de-lethvalora`
- `issues`: destino da facção ainda em revisão narrativa
- `recommendation`: não expandir antes de decisão sobre Leth'valora pós-destruição

### `Territories/Floresta de Avenor.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; `territorio`, `earthropo`, `forest`
- `visibility_ok`: sim, `Público`
- `gm_secret_ok`: sim, `false`
- `chapters_or_story_ok`: sim, `chapters: []`
- `image_fields_ok`: sim
- `dataview_expected`: deve aparecer como território/local conhecido quando filtros permitirem
- `supercharged_links_expected`: `territorio`
- `issues`: classificação entre território/região florestal deve seguir guia novo
- `recommendation`: manter como território/região ampla por enquanto

### `Items/Grisalma.md`

- `frontmatter_ok`: sim
- `tags_ok`: sim; `item`, `artefato`, `vezemir`
- `visibility_ok`: sim, `Jogadores`
- `gm_secret_ok`: sim, `false`
- `chapters_or_story_ok`: sim, `chapters: []`
- `image_fields_ok`: sim
- `dataview_expected`: deve aparecer em consultas por item/artefato
- `supercharged_links_expected`: não depende de tag visual especial
- `issues`: divergência de dano já está registrada na própria nota
- `recommendation`: validar regra de dano em etapa mecânica, não nesta migração
