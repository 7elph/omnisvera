# Pilot Migration Plan

Plano de migração piloto. Não executar ainda.

Objetivo: validar a camada de compatibilidade em um lote pequeno antes de qualquer migração ampla.

## Tamanho do lote piloto

Sugestão:

- 1 personagem;
- 1 facção;
- 1 território ou local;
- 1 lore ou handout.

## Critérios de seleção

Escolher notas que:

- sejam importantes o suficiente para validar visual real;
- tenham imagem ou campo de mídia;
- usem tags;
- apareçam em Dataview/DataCards;
- tenham links para outras notas;
- representem tipos comuns do vault.

Evitar no piloto:

- notas muito quebradas;
- notas com muita lore indefinida;
- notas que exigem renomeação;
- notas dependentes de mapa complexo;
- mídia com referência não resolvida.

## Campos a adicionar no piloto

Adicionar sem remover campos antigos:

```yaml
type:
subtype:
visibility:
spoiler_level:
player_known:
gm_secret:
revealed_in:
sessions:
portrait:
life_status:
```

Adicionar apenas quando fizer sentido:

```yaml
map_image:
handout_image:
token_image:
old_dragon_class:
old_dragon_race:
level:
danger_level:
hooks:
rumors:
```

## Campos que não podem ser removidos

- `thumbnail`
- `cover`
- `status`
- `location`
- `territory`
- `district`
- `faction`
- `religion`
- `role`
- `chapters`
- `tags`
- `cssclasses`
- `NoteIcon`
- `NoteStatus`

## Tags que não podem ser removidas

- `loyalist`
- `rancher`
- `third`
- `pirate`
- `widow`
- `murray`
- `steeltown`
- `water`
- `story`
- `individual`
- `lore`
- `religion`
- `territory`

## Validação Dataview

Verificar:

- consultas antigas continuam retornando a nota;
- consultas por `chapters` não quebram;
- consultas novas podem ler `sessions`;
- queries por tags antigas continuam funcionando;
- queries por tags novas funcionam quando adicionadas;
- dashboard público, se testado, filtra `visibility`.

## Validação DataCards

Verificar:

- card com `thumbnail` renderiza;
- card com `cover` renderiza;
- `portrait` não quebrou cards;
- cards por tags antigas continuam funcionando;
- cards por tags novas funcionam apenas onde foram adicionadas;
- cards públicos não exibem conteúdo de mestre.

## Validação visual no Obsidian

Verificar:

- nota abre em preview;
- banner/capa não quebrou;
- callouts continuam renderizando;
- links coloridos continuam funcionando;
- imagens aparecem;
- cards não ficam vazios;
- visual mobile continua aceitável se usado em mesa.

## Validação de links

Verificar:

- wikilinks principais;
- backlinks;
- links usados por Dataview;
- links usados por Leaflet, se houver;
- links para sessão/capítulo;
- links para mídia.

## Validação de mídia

Verificar:

- `thumbnail` resolve;
- `cover` resolve;
- `portrait` resolve, se usado;
- `map_image` resolve, se usado;
- `handout_image` resolve, se usado;
- nenhum arquivo de mídia foi removido, movido ou renomeado.

## Critérios de sucesso

O piloto só é bem-sucedido se:

- nenhum Dataview antigo quebrar;
- nenhum DataCards antigo quebrar;
- notas antigas continuarem visualmente legíveis;
- campos novos forem aceitos sem remover antigos;
- dashboard mestre continuar funcional;
- nenhum segredo aparecer em consulta pública de teste;
- links e mídia forem preservados.

## Próximo passo após piloto

Se o piloto for validado:

1. registrar achados;
2. ajustar templates se necessário;
3. criar segundo lote pequeno por tipo de nota;
4. só depois planejar migração semi-automatizada.
