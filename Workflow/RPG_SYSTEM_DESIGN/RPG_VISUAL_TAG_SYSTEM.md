> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# RPG VISUAL TAG SYSTEM

Modelo abstrato para reinterpretar o sistema de tags visuais do Disgraceland em um vault de RPG.

Não compara com Omnisvera. Tags finais só devem ser decididas após mapear o vault atual que receberá o sistema.

## 1. Princípio central

No Disgraceland, tags não são apenas organização. Elas são infraestrutura:

- controlam Supercharged Links;
- alimentam DataCards;
- filtram Dataview;
- organizam dashboards;
- carregam identidade visual.

Um vault RPG deve manter esse princípio: tags são API visual e operacional.

## 2. Famílias de tags

### Tags de tipo de nota

Proposta abstrata:

- `character`
- `player`
- `npc`
- `antagonist`
- `faction`
- `territory`
- `region`
- `settlement`
- `location`
- `dungeon`
- `lore`
- `religion`
- `session`
- `arc`
- `quest`
- `item`
- `encounter`
- `rumor`
- `handout`
- `map`
- `media`

Uso:

- filtros Dataview;
- cards do dashboard;
- cor/ícone via Supercharged Links;
- validação de template.

### Tags de facção

Proposta:

- uma tag por facção relevante;
- tags estáveis, curtas e sem ambiguidade;
- nunca remover tag antiga no mesmo passo em que criar tag nova.

Uso:

- personagens por facção;
- cards de facção;
- cor de links;
- mapa de relações.

### Tags de região

Proposta:

- uma tag por região/território;
- opcionalmente tags por cidade ou distrito importante;
- não substituir `territory`/`region` no frontmatter; a tag complementa.

Uso:

- filtros rápidos;
- dashboards regionais;
- mapa;
- listas de rumores/quests por região.

### Tags de status narrativo

Proposta:

- `active`
- `inactive`
- `dead`
- `missing`
- `hidden`
- `revealed`
- `secret`
- `public`
- `draft`
- `canon`

Observação: campos como `life_status`, `visibility` e `canon_status` são mais precisos para Dataview. Tags de status devem ser usadas quando o status também precisa ter cor visual.

## 3. Tags visuais mínimas propostas

Base abstrata para RPG:

- `character`
- `player`
- `npc`
- `antagonist`
- `faction`
- `territory`
- `location`
- `lore`
- `religion`
- `session`
- `quest`
- `item`
- `handout`
- `secret`
- `public`

Essas tags correspondem a tipos que precisam aparecer visualmente no grafo, nos links e nos dashboards.

## 4. Como evitar quebrar Supercharged Links

Regras:

1. Não remover tag antiga sem criar seletor equivalente.
2. Não renomear tag visual sem mapear UID, cor e peso.
3. Não editar `supercharged-links-gen.css` diretamente.
4. Alterar cores/pesos via plugin/Style Settings, não via CSS gerado.
5. Manter uma tabela de tags antigas -> tags novas quando houver migração.
6. Validar links em preview, file explorer, backlinks e graph.

## 5. Como criar tags novas

Fluxo seguro:

1. Criar tag nova em documentação.
2. Definir função: tipo, facção, região, status, visibilidade ou sistema.
3. Definir cor/peso desejados.
4. Criar seletor Supercharged Links.
5. Atualizar dashboards se necessário.
6. Aplicar em pequeno lote de notas.
7. Validar visualmente.
8. Só depois expandir.

## 6. Separação entre tag e frontmatter

Tags são boas para:

- visual;
- agrupamento rápido;
- filtros simples;
- compatibilidade com DataCards;
- Supercharged Links.

Frontmatter é melhor para:

- valores estruturados;
- booleanos;
- listas de sessões;
- status de revelação;
- nível de perigo;
- datas;
- visibilidade mestre/jogador.

Exemplo:

```yaml
visibility: Mestre
player_known: false
tags:
  - npc
  - secret
```

## 7. Tags públicas e secretas

Tags como `secret` e `public` podem ajudar visualmente, mas não são mecanismo de segurança real. O controle operacional deve vir de campos:

- `visibility`
- `spoiler_level`
- `player_known`

Tag visual é aviso, não proteção.

## 8. Riscos

- Tag de facção pode estar ligada a DataCards.
- Tag de tipo pode alimentar Home/dashboard.
- Tag visual pode alterar Supercharged Links.
- Tags antigas podem existir em notas e consultas mesmo depois de “parecerem obsoletas”.
- Remover tags sem auditoria gera falhas silenciosas: cards vazios, links sem cor, consultas incompletas.

## 9. Decisão adiada

As tags finais do RPG só devem ser definidas depois da próxima auditoria do vault atual. Este documento define o modelo de famílias e regras de segurança, não a lista final aplicada.
