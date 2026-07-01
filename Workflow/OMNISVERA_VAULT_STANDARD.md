# Omnisvera — Padrão Global do Vault

> [!IMPORTANT]
> Este documento é a fonte oficial de padronização global do vault Omnisvera.
>
> Ele não substitui automaticamente notas antigas, não apaga compatibilidade com Disgraceland e não autoriza migração destrutiva.
>
> Use este padrão para criar notas novas, auditar notas existentes e planejar migrações futuras por lote.

## 1. Princípios de compatibilidade

- Preservar a compatibilidade visual e técnica herdada do template Disgraceland.
- Não traduzir campos estruturais usados por plugins, Dataview, DataCards, CSS, snippets ou configurações do Obsidian.
- Não remover campos legacy sem auditoria explícita.
- Não mover mídia sem plano de impacto.
- Não renomear imagens em massa.
- Não alterar links internos em massa sem relatório.
- Toda migração deve ser reversível ou revisável.
- Toda alteração de estrutura deve ser pequena, rastreável e registrada em Git.
- O mestre/Sage é a autoridade final do cânone.
- A IA pode sugerir, auditar e preparar, mas não canoniza conteúdo sem marcação de revisão.

## 2. Camadas do vault

### Camada Legacy / Disgraceland

Camada herdada que mantém compatibilidade com:

- visual do Obsidian;
- snippets CSS;
- Supercharged Links;
- Dataview;
- DataCards;
- banners, covers e thumbnails;
- padrões de Home/dashboard;
- tags antigas que ainda possam alimentar visual ou consultas.

Essa camada não deve ser apagada conceitualmente enquanto houver dependências técnicas.

### Camada Omnisvera

Camada semântica do mundo e da campanha.

Controla:

- tipos de nota;
- subtipos;
- status editorial;
- status canônico;
- visibilidade mestre/jogadores;
- relações entre personagens, locais, facções, itens, lore e capítulos;
- organização progressiva do cânone.

### Camada App/IA

Camada futura para:

- cenas assíncronas;
- NPCs com IA;
- acesso de jogadores;
- respostas pendentes de aprovação;
- separação entre conteúdo público, revelado e secreto;
- integração com sistemas externos.

Essa camada deve ser adicionada por cima da camada Omnisvera, sem quebrar a camada Legacy.

## 3. Campos legacy permitidos

Campos herdados que podem permanecer por compatibilidade:

| campo | uso |
|---|---|
| `obsidianUIMode` | modo visual no Obsidian |
| `NoteIcon` | ícone/cor/visual de nota |
| `NoteStatus` | status herdado de templates/visual |
| `cover` | imagem ampla, capa ou card visual |
| `thumbnail` | imagem pequena para cards/listagens |
| `status` | estado operacional herdado |
| `tags` | infraestrutura técnica do Obsidian |
| `cssclasses` | classes CSS aplicadas à nota |
| `cssclass` | forma singular herdada; revisar antes de alterar |
| `banner` | banner visual |
| `banner-x` | posição do banner |
| `banner-y` | posição do banner |
| `banner-height` | altura do banner |
| `content-start` | início visual do conteúdo |
| `banner-fade` | fade visual do banner |
| `chapters` | aparições/capítulos/seções da campanha |
| `chapter` | capítulo atual ou referência curta |

Regra: esses campos podem coexistir com campos Omnisvera. Não remover em lote.

## 4. Campos Omnisvera oficiais

Campos oficiais para novas notas e migrações graduais:

| campo | uso |
|---|---|
| `type` | tipo estrutural da nota |
| `subtype` | subtipo estrutural |
| `work_status` | status de trabalho editorial |
| `canon_status` | status canônico |
| `visibility` | Mestre / Jogadores / Público |
| `created_by` | origem/autoria da nota |
| `requires_review` | indica necessidade de revisão humana |
| `name` | nome canônico |
| `aliases` | nomes alternativos |
| `origin` | origem narrativa/geográfica |
| `location` | local/ponto jogável |
| `territory` | região ampla/reino/continente |
| `faction` | facção relacionada |
| `faith` | religião/fé relacionada |
| `thumbnail` | imagem compacta |
| `portrait` | retrato específico, quando necessário |
| `cover` | imagem ampla |
| `related_characters` | personagens relacionados |
| `related_factions` | facções relacionadas |
| `related_items` | itens relacionados |
| `arcs` | arcos narrativos |
| `chapters` | capítulos/seções/aparições |

Regra: campos Omnisvera devem ser adicionados de forma incremental. Não substituir campos legacy no mesmo passo.

## 5. Tipos oficiais

Valores oficiais para `type`:

- `character`
- `location`
- `territory`
- `faction`
- `item`
- `lore`
- `religion`
- `race`
- `class`
- `session`
- `async_scene`
- `ai_npc`
- `workflow`

## 6. Subtipos recomendados

### `character`

- `player_character`
- `major_npc`
- `minor_npc`
- `antagonist`
- `creature`

### `location`

- `city`
- `district`
- `shop`
- `port`
- `ruin`
- `temple`
- `wilderness`
- `dungeon`
- `settlement`

### `faction`

- `political`
- `military`
- `religious`
- `criminal`
- `guild`
- `noble_house`
- `cult`

### `item`

- `mundane`
- `magic_item`
- `artifact`
- `weapon`
- `armor`
- `document`
- `consumable`

### `lore`

- `event`
- `concept`
- `secret`
- `system`
- `cosmology`
- `mystery`

## 7. Status editoriais

Valores recomendados para `work_status`:

- `Em desenvolvimento`
- `Revisão`
- `Finalizado`

## 8. Status canônicos

Valores recomendados para `canon_status`:

- `Draft`
- `Working Canon`
- `Confirmed`
- `Deprecated`
- `Non Canon`
- `Pending`

## 9. Visibilidade

Valores oficiais para `visibility`:

- `Mestre`
- `Jogadores`
- `Público`

Regra mínima:

| conteúdo | visibility |
|---|---|
| conteúdo público e seguro | `Público` |
| conteúdo conhecido pelo grupo | `Jogadores` |
| preparação, segredos e spoilers | `Mestre` |

## 10. Tags oficiais

Para novas notas, tags técnicas devem preferir inglês, minúsculas, sem acento e com `_` quando necessário:

- `character`
- `location`
- `territory`
- `faction`
- `item`
- `lore`
- `religion`
- `race`
- `class`
- `session`
- `workflow`
- `async_scene`
- `ai_npc`

Observação: tags em português já existentes podem permanecer como ponte Omnisvera até migração auditada. Não remover `personagem`, `local`, `territorio`, `faccao`, `religiao`, `raca`, `classe` ou similares sem relatório de impacto.

## 11. Tags legacy aceitas

Tags antigas ou híbridas que podem permanecer temporariamente por compatibilidade:

- `Category/Location`
- `Category/Settlement`
- `Category/Lore`
- `Category/Character`
- `story`
- `bside`
- `old-dragon`
- `personagem`
- `local`
- `territorio`
- `faccao`
- `religiao`
- `raca`
- `classe`
- `capitulo`
- `origem`
- `npc`
- `jogador`
- `antagonista`
- `criatura`

Regra: tags legacy aceitas não são necessariamente desejadas para notas novas; elas existem para não quebrar plugins, consultas ou histórico.

## 12. Regras de mídia

Nesta fase, o padrão oficial aceito é:

```yaml
cover: zz_media/nome-do-arquivo.png
thumbnail: zz_media/th_nome-do-arquivo.png
portrait: zz_media/nome-do-arquivo.png
```

E embeds continuam válidos:

```md
![[arquivo.png]]
![[zz_media/arquivo.png]]
```

Subpastas futuras são desejáveis, mas não devem ser implementadas agora sem auditoria:

- `zz_media/characters/`
- `zz_media/locations/`
- `zz_media/factions/`
- `zz_media/items/`
- `zz_media/covers/`
- `zz_media/maps/`

Regra: `zz_media` permanece plana nesta fase.

## 13. Regra especial de case-sensitive

O Git em Windows pode não registrar corretamente mudanças que alteram apenas maiúsculas/minúsculas.

Renomeações como:

```txt
mira.PNG → mira.png
```

devem usar rename intermediário:

```txt
mira.PNG → mira_temp.png → mira.png
```

Antes de qualquer rename, atualizar referências no vault e validar links de mídia.

## 14. Regras para App/IA futura

Campos recomendados para integração futura:

| campo | uso |
|---|---|
| `player_visible` | define se a nota pode aparecer para jogadores |
| `app_enabled` | permite uso por app externo |
| `ai_access` | define nível de acesso da IA |
| `npc_access` | define se NPCs IA podem consultar a nota |
| `known_by_players` | registra se o grupo conhece a informação |
| `can_reveal_secrets` | define se a IA pode revelar segredos |
| `can_modify_canon` | define se a IA pode alterar cânone |

Valores sensíveis devem começar conservadores:

```yaml
player_visible: false
app_enabled: false
ai_access: restricted
npc_access: false
known_by_players: false
can_reveal_secrets: false
can_modify_canon: false
```

## 15. Regras para cenas assíncronas

Cenas assíncronas não entram direto no cânone.

Valores recomendados para `work_status` ou campo específico de cena:

- `submitted`
- `answered`
- `pending_review`
- `canonized`
- `rejected`

Fluxo recomendado:

```txt
submitted → answered → pending_review → canonized
```

ou:

```txt
submitted → answered → rejected
```

Regra: uma cena assíncrona só altera cânone quando o Sage marcar explicitamente como `canonized`.

## 16. Regra de migração

Toda migração deve seguir esta ordem:

1. auditar;
2. documentar;
3. aplicar em lote pequeno;
4. validar Dataview/DataCards;
5. validar links;
6. validar mídia;
7. commit separado;
8. revisar no Obsidian;
9. repetir.

Nunca misturar migração técnica com criação de lore extensa.
