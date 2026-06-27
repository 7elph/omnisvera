# Plano de Migração de Pastas para Português BR

Data: 2026-06-27

Objetivo: planejar renomeação de pastas para português BR sem executar renomeação nesta etapa.

## Decisão

Não renomear pastas agora.

Motivo: nomes de pasta aparecem em Dataview, DataCards, links Markdown, templates, configs de plugins e possivelmente Leaflet/Calendarium. Renomear sem lote controlado quebraria consultas.

## Mapeamento inicial proposto

| pasta atual | pasta PT-BR proposta | migrar agora? | risco |
|---|---|---:|---|
| `Characters` | `Personagens` | não | Alto: consultas `FROM "Characters"` e links. |
| `Factions` | `Faccoes` | não | Médio/alto: consultas e links. |
| `Territories` | `Territorios` | não | Alto: Home, DataCards, tags e links geográficos. |
| `Locations` | `Locais` | não | Médio/alto: links e consultas. |
| `Religion` | `Religiao` | não | Médio: links e tags visuais. |
| `Items` | `Itens` | não | Médio: já há notas canônicas. |
| `Bestiary` | `Bestiario` | não | Baixo/médio: estrutura nova. |
| `Rules` | `Regras` | não | Baixo/médio: estrutura nova. |
| `Templates` | `Templates` | não | Alto: Templater/uso manual. |
| `Workflow` | `Workflow` ou `Fluxo` | não | Muito alto: auditorias, documentação e automação. |
| `Maps` | `Mapas` | não | Médio: Leaflet e links. |
| `CAMPANHA` | `CAMPANHA` | não | Baixo: já está em português/operacional. |

## Links que quebrariam

Categorias de links afetados:

- links explícitos para `Characters/*`;
- links explícitos para `Factions/*`;
- links explícitos para `Territories/*`;
- links explícitos para `Locations/*`;
- embeds de imagens ou cards com paths relativos;
- links em `Home_Mestre.md`, `Home.md`, templates e relatórios operacionais.

## Dataviews afetados

Padrões observados ou esperados:

```dataview
FROM "Characters"
FROM "Factions"
FROM "Territories"
FROM "Locations"
FROM "Religion"
FROM "Items"
FROM "Classes"
```

Esses padrões precisam ser localizados e atualizados em lote no momento da renomeação.

## DataCards afetados

DataCards usam os mesmos padrões `FROM "..."` e campos como `thumbnail`, `cover`, `status`, `location`, `territory`, `faction`.

Renomeação só deve ocorrer depois de:

1. inventário de todos os blocos DataCards;
2. atualização de `FROM`;
3. validação visual no Obsidian.

## Plugins afetados

| plugin/config | impacto |
|---|---|
| Dataview | Alto: queries por pasta quebram. |
| DataCards | Alto: queries por pasta quebram. |
| Templater | Médio: paths de templates podem quebrar. |
| Homepage | Baixo: se links forem atualizados. |
| Leaflet | Médio/alto: marcadores podem linkar notas por path/nome. |
| Calendarium | Médio: eventos podem linkar notas. |
| Icon Folder | Médio: ícones por pasta podem quebrar. |

## Recomendação

Não migrar pastas nesta etapa.

Ordem segura futura:

1. congelar templates e tags;
2. exportar lista de links por pasta;
3. atualizar Dataview/DataCards em lote pequeno;
4. renomear uma pasta por commit;
5. validar no Obsidian;
6. só então seguir para a próxima pasta.

## Risco final

Estado atual: `HÍBRIDO_CONTROLADO`.

As pastas em inglês são aceitáveis temporariamente porque preservam funcionamento. A migração para PT-BR é desejável, mas deve ser etapa própria.
