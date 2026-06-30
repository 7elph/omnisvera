# Omnisvera — Padrão de Mídia

> [!IMPORTANT]
> Este documento segue a taxonomia oficial atual do Sage.
> Fonte da verdade: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].

## Função

Define como imagens e referências visuais devem ser usadas no vault.

## Campos de mídia ativos

| campo | função |
|---|---|
| `thumbnail` | Imagem pequena para cards, listas e DataCards. |
| `cover` | Imagem ampla para banners, capas e páginas principais. |

Outros campos de mídia não são padrão novo nesta taxonomia. Se existirem em documentos antigos, tratá-los como planejamento histórico até decisão nova.

## Regras para `thumbnail`

- Deve apontar para imagem leve e reconhecível.
- Deve ser preservado em personagens, facções, itens e cards.
- Não deve ser substituído por `cover`.

Exemplo:

```yaml
thumbnail: zz_media/vezemir.png
```

## Regras para `cover`

- Usar para capa, banner ou imagem de leitura ampla.
- Pode ser maior que `thumbnail`.
- Não deve substituir `thumbnail` em DataCards compactos.

Exemplo:

```yaml
cover: zz_media/avenor.png
```

## Pasta de mídia

`zz_media` continua sendo o repositório operacional de imagens.

Não mover, renomear ou apagar mídia sem:

1. checar Markdown;
2. checar YAML;
3. checar Leaflet;
4. checar Calendarium;
5. checar CSS/snippets;
6. checar configs de plugins.

## Mídia órfã

Mídia possivelmente órfã deve ser relatada, não apagada.

Classificações recomendadas:

- `referenciada`;
- `possivelmente órfã`;
- `usada por plugin`;
- `usada por mapa`;
- `precisa revisão do Sage`.

## Uso em dashboards

DataCards compactos devem preferir:

```dataview
TABLE thumbnail, status, location
FROM "Characters"
WHERE contains(tags, "personagem")
SORT file.name ASC
```

Dashboards de capa podem usar:

```dataview
TABLE cover, status, description
FROM "Territories"
SORT file.name ASC
```

## Regra de segurança

Não exibir imagem em dashboard de jogadores se a nota estiver marcada como:

```yaml
visibility: Mestre
gm_secret: true
```

ou se `spoiler_level` for `medium` ou `heavy`.
