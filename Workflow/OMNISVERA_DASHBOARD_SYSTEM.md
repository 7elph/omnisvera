---
type: workflow
subtype: standard
work_status: Active
canon_status: Reference
visibility: Mestre
created_by: IA
requires_review: true
tags:
  - workflow
  - standard
  - dashboard
  - dataview
---

> [!IMPORTANT]
> Este arquivo é documentação técnica do sistema de dashboards do Omnisvera.
> Ele não é uma Home operacional.
> Existem somente duas Homes operacionais:
> - [[Home]] — Home dos Jogadores e entrada do plugin Homepage.
> - [[Home_Mestre]]
>
> `Home_Jogadores.md` foi arquivado e não é Home ativa.

# Sistema de Dashboards — Omnisvera

Este documento define o sistema de dashboards e consultas Dataview para o vault Omnisvera.

## Visão Geral

Omnisvera usa Dataview para criar dashboards interativos que facilitam a navegação e gestão do vault. O sistema é inspirado em Disgraceland, mas com schema mais limpo e adaptado ao contexto de fantasia medieval.

## Dashboards Principais

### 1. Home

**Arquivo:** `Home.md`

**Função:** Home dos Jogadores. Deve mostrar apenas conteúdo público, conhecido pelos jogadores ou explicitamente liberado.

**Elementos:**
- Calendário e mapa liberados
- Personagens dos jogadores
- Locais conhecidos
- Facções conhecidas
- Handouts liberados
- Sessões jogadas
- Filtros contra `visibility: Mestre`, `gm_secret: true` e spoilers médios/pesados

### Área do Mestre

**Arquivo:** `Home_Mestre.md`

**Função:** Home/área operacional do mestre. Pode conter preparação, spoilers, relatórios técnicos, Workflow, auditorias, camada de compatibilidade e links administrativos.

**Exemplo de Dataview para últimos personagens:**

```dataview
TABLE 
  "<img src='" + thumbnail + "' width='60' style='border-radius:4px;' />" as "IMAGEM",
  subtype as "TIPO",
  role as "PAPEL",
  life_status as "ESTADO",
  "<span style='font-size: 0.85em;'>" + date(file.mtime) + "</span>" as "MODIFICADO"
FROM "Characters"
WHERE type = "character"
SORT file.mtime DESC
LIMIT 5
```

### 2. Índice de Personagens

**Arquivo:** `Characters/ÍNDICE.md`

**Função:** Índice completo de todos os personagens

**Elementos:**
- Lista de personagens por subtipo
- Filtros por localização
- Filtros por facção
- Filtros por status vital

**Exemplo de Dataview por subtipo:**

```dataview
TABLE thumbnail, role, life_status, location
FROM "Characters"
WHERE type = "character" AND subtype = "player_character"
SORT file.name ASC
```

### 3. Índice de Facções

**Arquivo:** `Factions/ÍNDICE.md`

**Função:** Índice de todas as facções com membros

**Elementos:**
- Lista de facções
- Cards de membros por facção
- Status de cada facção

**Exemplo de Dataview para membros por facção:**

```dataview
TABLE thumbnail, role, life_status, location
FROM "Characters"
WHERE contains(faction, this.file.link)
SORT file.name ASC
```

### 4. Índice de Capítulos

**Arquivo:** `EARTHROPO/ÍNDICE.md`

**Função:** Índice de todos os capítulos com personagens presentes

**Elementos:**
- Lista de capítulos em ordem
- Personagens presentes em cada capítulo
- Data de cada capítulo

**Exemplo de Dataview para personagens por capítulo:**

```dataview
TABLE thumbnail, role, life_status, faction
FROM "Characters"
WHERE contains(chapters, this.file.name)
SORT file.name ASC
```

### 5. Painel do Mestre

**Arquivo:** `Workflow/PAINEL_DO_MESTRE.md`

**Função:** Dashboard exclusivo para o Sage

**Elementos:**
- Notas pendentes de revisão
- Personagens com canon_status Draft
- NPCs sem localização definida
- Itens pendentes de confirmação
- Links rápidos para ferramentas

**Exemplo de Dataview para notas pendentes:**

```dataview
TABLE type, subtype, work_status, canon_status
FROM ""
WHERE requires_review = true
SORT file.mtime DESC
```

## Consultas Dataview Reutilizáveis

### Personagens por Capítulo

**Uso:** Em notas de capítulo para listar personagens presentes

```dataview
TABLE thumbnail, role, life_status, faction
FROM "Characters"
WHERE contains(chapters, this.file.name)
SORT file.name ASC
```

**Campos exibidos:**
- `thumbnail` - Imagem miniatura
- `role` - Papel do personagem
- `life_status` - Estado vital
- `faction` - Facção principal

### Membros por Facção

**Uso:** Em notas de facção para listar membros

```dataview
TABLE thumbnail, role, life_status, location
FROM "Characters"
WHERE contains(faction, this.file.link)
SORT file.name ASC
```

**Campos exibidos:**
- `thumbnail` - Imagem miniatura
- `role` - Papel do personagem
- `life_status` - Estado vital
- `location` - Local atual

### Personagens por Local

**Uso:** Em notas de localização para listar personagens presentes

```dataview
TABLE thumbnail, role, life_status
FROM "Characters"
WHERE location = this.file.link OR origin = this.file.link
SORT file.name ASC
```

**Campos exibidos:**
- `thumbnail` - Imagem miniatura
- `role` - Papel do personagem
- `life_status` - Estado vital

### Notas Pendentes de Revisão

**Uso:** No Painel do Mestre para identificar notas que precisam de atenção

```dataview
TABLE type, subtype, work_status, canon_status
FROM ""
WHERE requires_review = true
SORT file.mtime DESC
```

**Campos exibidos:**
- `type` - Tipo da nota
- `subtype` - Subtipo (se aplicável)
- `work_status` - Estado editorial
- `canon_status` - Estado canônico

### Personagens por Status Vital

**Uso:** Para filtrar personagens por estado vital

```dataview
TABLE thumbnail, role, location
FROM "Characters"
WHERE type = "character" AND life_status = "Morto"
SORT file.name ASC
```

**Campos exibidos:**
- `thumbnail` - Imagem miniatura
- `role` - Papel do personagem
- `location` - Localização

### Personagens por Subtipo

**Uso:** Para listar personagens de um subtipo específico

```dataview
TABLE thumbnail, role, life_status, location
FROM "Characters"
WHERE type = "character" AND subtype = "antagonist"
SORT file.name ASC
```

**Campos exibidos:**
- `thumbnail` - Imagem miniatura
- `role` - Papel do personagem
- `life_status` - Estado vital
- `location` - Localização

## Aparições em Personagens

**Uso:** Em notas de personagem para listar capítulos onde aparece

```dataview
LIST
FROM "EARTHROPO"
WHERE contains(this.chapters, file.name)
SORT file.name ASC
```

**Nota:** Esta consulta deve ser incluída em todas as notas de personagem com o campo `chapters` preenchido.

## Cards Visuais

Omnisvera pode usar Data Cards para criar cards visuais, similar a Disgraceland. Isso requer o plugin Data Cards.

### Exemplo de Cards de Territórios

```dataview
TABLE cover, leader, population
FROM "Territories"
WHERE type = "territory"
SORT file.name ASC

// Settings
preset: portrait
columns: 3
imageProperty: cover
cardSpacing: 4
```

### Exemplo de Cards de Facções

```dataview
TABLE thumbnail, location, status
FROM "Factions"
WHERE type = "faction"
SORT file.name ASC

// Settings
preset: compact
columns: 4
imageProperty: thumbnail
showImageOnHover: true
cardSpacing: 4
```

## Implementação Futura

### Fase 1: Dataview Básico

- Implementar consultas Dataview em personagens
- Implementar consultas Dataview em facções
- Implementar consultas Dataview em capítulos
- Criar Índice de Personagens
- Criar Índice de Facções
- Criar Índice de Capítulos

### Fase 2: Home Dashboard

- Criar Home.md com cards de territórios
- Adicionar lista de últimos personagens modificados
- Adicionar notícias da campanha
- Adicionar links para dashboards específicos

### Fase 3: Painel do Mestre

- Criar Painel do Mestre
- Implementar consulta de notas pendentes
- Implementar consulta de personagens Draft
- Adicionar links rápidos para ferramentas

### Fase 4: Data Cards (Opcional)

- Instalar plugin Data Cards
- Implementar cards visuais de territórios
- Implementar cards visuais de facções
- Implementar cards visuais de capítulos

## Boas Práticas

1. **Use propriedades do frontmatter** - Dataview deve ler de propriedades, não de tags
2. **Seja consistente com nomes de campos** - Use sempre os mesmos nomes definidos no schema
3. **Filtre por type** - Sempre inclua `WHERE type = "character"` em consultas de personagens
4. **Ordene resultados** - Use `SORT file.name ASC` para consistência
5. **Limite resultados quando necessário** - Use `LIMIT` para evitar listas muito longas
6. **Use wikilinks em propriedades** - Facilita navegação bidirecional
7. **Documente consultas complexas** - Adicione comentários explicando consultas não triviais

## Referência Disgraceland

O sistema de dashboards de Disgraceland foi usado como referência para:

- Estrutura de Home.md
- Consultas Dataview para personagens por capítulo
- Consultas Dataview para membros por facção
- Uso de Data Cards para visualização
- Padrão de thumbnails em tabelas

Omnisvera adapta esses elementos com schema mais limpo e focado em fantasia medieval.

## Documentos Relacionados

- `Workflow/OMNISVERA_NOTE_STANDARD.md` - Padrão geral de notas
- `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` - Esquema de frontmatter
- `Workflow/OMNISVERA_MEDIA_STANDARD.md` - Padrão de mídia
- `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` - Guia de templates
