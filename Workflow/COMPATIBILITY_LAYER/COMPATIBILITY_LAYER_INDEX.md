> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Omnisvera Compatibility Layer Index

Esta pasta define a camada de compatibilidade técnica do Omnisvera antes de qualquer migração em massa.

Objetivo: permitir que o vault evolua para o modelo RPG operacional sem quebrar a infraestrutura herdada de Disgraceland: Dataview, DataCards, Supercharged Links, Style Settings, Leaflet, Calendarium, Home/dashboard, mídia em `zz_media` e campos antigos de frontmatter.

Esta camada ainda não migra notas. Ela define regras oficiais para migrações futuras.

## Decisões aprovadas usadas como base

| decisão | regra aprovada |
| --- | --- |
| `chapters` / `sessions` | Manter `chapters` e adicionar `sessions` em paralelo. |
| Tags visuais antigas | Preservar tags antigas como ponte; adicionar tags RPG novas em paralelo. |
| Campos de mídia | Manter `thumbnail`, `cover`, `portrait`, `map_image` e `handout_image` separados. |
| Mestre/jogador | Criar modelo de visibilidade; Home atual é dashboard do mestre por enquanto. |
| `status` / `life_status` | Manter `status`; adicionar `life_status` quando fizer sentido. |
| `type/subtype` / tags | Adicionar `type` e `subtype` sem substituir tags visuais. |
| Old Dragon | Criar campos opcionais, não obrigatórios no primeiro lote. |
| Home/dashboard | Não criar dashboard de jogadores antes de filtros seguros. |
| Mídia órfã | Não apagar; classificar antes. |
| Templates prioritários | Personagem, Facção, Território/Região, Local, Sessão, Lore, Handout, Quest/Gancho. |

## Arquivos da camada

| arquivo | função |
| --- | --- |
| `FRONTMATTER_COMPATIBILITY_SCHEMA.md` | Define campos herdados preservados e novos campos RPG permitidos. |
| `TAG_COMPATIBILITY_MAP.md` | Mapeia tags antigas, função técnica e tags RPG futuras. |
| `VISIBILITY_COMPATIBILITY_MODEL.md` | Define campos e regras de visibilidade mestre/jogador. |
| `MEDIA_FIELD_COMPATIBILITY_MODEL.md` | Define uso de `thumbnail`, `cover`, `portrait`, `map_image`, `handout_image`, `token_image` e `media_status`. |
| `DATAVIEW_COMPATIBILITY_RULES.md` | Define regras para consultas Dataview compatíveis. |
| `DATACARDS_COMPATIBILITY_RULES.md` | Define regras para DataCards sem quebrar cards existentes. |
| `TEMPLATE_COMPATIBILITY_GUIDE.md` | Guia de evolução de templates prioritários. |
| `DASHBOARD_COMPATIBILITY_RULES.md` | Regras para Home/dashboard mestre e futuro dashboard de jogadores. |
| `PILOT_MIGRATION_PLAN.md` | Plano de piloto pequeno, sem execução. |

## Escopo permitido

- Adicionar documentação técnica.
- Planejar campos novos.
- Planejar tags novas.
- Planejar consultas compatíveis.
- Planejar templates prioritários.
- Planejar piloto pequeno.

## Fora do escopo

- Editar notas originais em massa.
- Remover campos antigos.
- Remover tags antigas.
- Editar CSS.
- Editar JSON de plugins.
- Editar mídia.
- Mover ou renomear arquivos.
- Alterar Home/dashboard real.
- Alterar mapas, calendários ou templates existentes.

## O que pode ser feito depois desta camada

1. Criar ou ajustar templates novos em área controlada.
2. Criar queries compatíveis que aceitem campos antigos e novos.
3. Selecionar um lote piloto pequeno.
4. Adicionar campos novos sem remover campos antigos.
5. Validar Dataview, DataCards e visual no Obsidian.

## O que ainda não pode ser feito

- Remover `chapters`.
- Trocar `thumbnail` por `cover`.
- Remover tags antigas.
- Criar dashboard público sem filtro de visibilidade.
- Apagar mídia órfã.
- Renomear notas usadas por Leaflet ou Calendarium.
- Migrar o vault inteiro de uma vez.

## Ordem segura para próxima etapa

1. Revisar esta camada.
2. Criar templates prioritários compatíveis.
3. Criar consultas de teste que aceitem `chapters` e `sessions`.
4. Criar filtro de visibilidade para dashboards.
5. Selecionar lote piloto.
6. Migrar o piloto manualmente ou por script controlado.
7. Validar Obsidian visualmente.
8. Só depois expandir para outros lotes.
