# Media Field Compatibility Model

Este modelo define a função de cada campo de mídia durante a compatibilidade.

## Campos de mídia

| campo | função | regra |
| --- | --- | --- |
| `thumbnail` | Imagem pequena para cards/listagens/DataCards. | Preservar; não substituir por `cover` ou `portrait`. |
| `cover` | Capa, banner ou imagem ampla para páginas/cards maiores. | Preservar separado de `thumbnail`. |
| `portrait` | Retrato principal de personagem/NPC. | Pode ser adicionado sem alterar `thumbnail`. |
| `map_image` | Imagem base de mapa. | Usar em notas de mapa ou locais com mapa. |
| `handout_image` | Imagem liberável aos jogadores. | Exige visibilidade/estado de handout. |
| `token_image` | Token de mesa/VTT. | Opcional; não obrigatório no primeiro lote. |
| `media_status` | Estado da mídia: provisória, final, órfã suspeita, revisar. | Opcional para indexação futura. |

## Regras absolutas

- Não trocar `thumbnail` por `cover`.
- Não trocar `thumbnail` por `portrait`.
- Não mover mídia.
- Não apagar mídia órfã.
- Não renomear imagens sem atualizar referências.
- Não assumir que mídia sem referência é inútil.

## Exemplo compatível para personagem

```yaml
thumbnail: zz_media/vezemir-thumb.png
cover: zz_media/vezemir-cover.png
portrait: zz_media/vezemir-portrait.png
```

## Exemplo compatível para mapa

```yaml
cover: zz_media/mapa-nimalia-cover.png
map_image: zz_media/mapa-nimalia.png
```

## Exemplo compatível para handout

```yaml
thumbnail: zz_media/carta-thumb.png
handout_image: zz_media/carta-antiga.png
visibility: Jogadores
player_known: true
gm_secret: false
```

## Política para mídia órfã

Antes de remover qualquer mídia, verificar:

- frontmatter (`thumbnail`, `cover`, `portrait`, `map_image`, `handout_image`, `token_image`);
- embeds Markdown;
- HTML manual;
- CSS/snippets;
- Leaflet;
- Calendarium;
- DataCards;
- Canvas ou outros plugins;
- uso futuro planejado.

## Política para referências quebradas

Referências quebradas devem ser classificadas antes de qualquer ação:

- arquivo realmente ausente;
- nome incorreto;
- caminho antigo;
- diferença de maiúsculas/minúsculas;
- referência herdada de template;
- referência usada por plugin.

## Regra para handouts

`handout_image` não deve aparecer em dashboard de jogadores sem filtro de visibilidade. A imagem só deve ser liberada quando a nota estiver marcada como pública/conhecida.
