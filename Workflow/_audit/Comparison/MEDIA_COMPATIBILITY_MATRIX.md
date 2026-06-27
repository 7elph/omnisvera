> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Media Compatibility Matrix

Comparação da camada de mídia entre Disgraceland, modelo RPG desejado e Omnisvera atual.

## Resumo

| camada | mídia auditada | referências quebradas | possíveis órfãs | observação |
| --- | ---: | ---: | ---: | --- |
| Disgraceland | 425 em `zz_media` | Não tratadas como ação de limpeza nesta comparação. | 148 possíveis órfãs na auditoria original. | Base grande, com thumbnails/covers/embeds/mapa. |
| Omnisvera atual | 75 em `zz_media` | 69 | 35 | Alto risco de limpeza prematura. |
| RPG desejado | Não aplica | Não aplica | Não aplica | Exige política de mídia por uso e visibilidade. |

## Matriz por tipo de mídia

| tipo | Disgraceland | RPG desejado | Omnisvera atual | risco | regra futura |
| --- | --- | --- | --- | --- | --- |
| `zz_media` | Repositório central de imagens/áudio. | Repositório central preservado. | Existe com 75 mídias. | Alto | Não mover sem atualizar refs. |
| `thumbnail` | Campo crítico para cards compactos. | Usar em cards/personagens/facções. | Presente e usado. | Alto | Não substituir por `cover`. |
| `cover` | Campo crítico para cards grandes e páginas. | Usar em territórios, lore, locais. | Presente e usado. | Alto | Manter separado de thumbnail. |
| `portrait` | Geralmente imagem embutida/callout, não campo padrão. | Campo desejado para retrato RPG. | Parcial/desconhecido. | Médio | Adicionar como complemento. |
| `map_image` | Mapa via Leaflet/config e embeds. | Campo desejado para notas de mapa. | Não contratado. | Alto | Validar com Leaflet antes de aplicar. |
| `handout_image` | Não central. | Campo desejado para handouts. | Não contratado. | Alto | Exige visibilidade/status. |
| `token_image` | Não central. | Campo opcional para mesa/VTT. | Não contratado. | Médio | Novo campo opcional. |
| embeds `![[...]]` | Muito usados. | Continuam úteis. | Presentes. | Alto | Atualizar refs se mídia for movida. |
| HTML manual | Presente em alguns templates/callouts. | Evitar onde possível, preservar onde existe. | Presente parcial. | Médio | Não converter automaticamente. |
| imagem pública | Não separada formalmente. | Necessária. | Não contratada. | Alto | Precisa `visibility`/`handout_status`. |
| imagem secreta | Não separada formalmente. | Necessária para mestre. | Não contratada. | Alto | Não incluir em dashboard público. |

## Referências não resolvidas

A auditoria do Omnisvera atual apontou 69 referências não resolvidas. Isso impede qualquer limpeza automática de mídia porque o problema pode estar em:

- nome de arquivo incorreto;
- caminho antigo;
- mídia ausente;
- referência herdada de template;
- diferença entre embed, YAML e HTML;
- case/nome incompatível.

## Mídias possivelmente órfãs

A auditoria do Omnisvera atual apontou 35 mídias possivelmente órfãs. Isso não significa que podem ser apagadas. Antes disso é necessário cruzar:

- frontmatter (`thumbnail`, `cover`, futuros `portrait`, `map_image`, `handout_image`);
- embeds markdown;
- HTML manual;
- Leaflet;
- CSS/snippets;
- documentos de workflow;
- uso planejado ainda não linkado.

## Política futura de mídia

- Nunca apagar mídia sem validação cruzada.
- Padronizar nomes apenas depois de mapear referências.
- Preferir registrar uso técnico antes de mover.
- Criar campo ou índice de `media_status` se o volume crescer.
- Separar mídia pública e secreta antes de gerar dashboards para jogadores.
- Manter `zz_media` como base até existir motivo técnico para mudar.
