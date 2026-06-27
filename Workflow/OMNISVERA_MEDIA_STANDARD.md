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
  - media
---

# Padrão de Mídia — Omnisvera

Este documento define o padrão de organização de mídia no vault Omnisvera.

## Estrutura de Pastas

Todas as imagens devem ser organizadas em `zz_media/` com subpastas por categoria:

```
zz_media/
├── characters/      # Imagens de personagens
├── classes/         # Imagens de classes
├── locations/       # Imagens de locais
├── factions/        # Imagens de facções
├── items/           # Imagens de itens
├── covers/          # Imagens de banner/capa
├── maps/            # Mapas
└── misc/            # Imagens diversas (logos, símbolos, etc.)
```

## Imagens de Classe

### Padrão de Nomes

Para classes, use este padrão:

```
zz_media/classes/nome.png
zz_media/classes/th_nome.png
zz_media/covers/nome_banner.png
```

**Exemplos:**

- `zz_media/classes/guerreiro.png` - Imagem principal
- `zz_media/classes/th_guerreiro.png` - Thumbnail
- `zz_media/covers/guerreiro_banner.png` - Banner

### Tipos de Imagem

#### Thumbnail

- **Propósito:** Imagem miniatura para cards e dashboards
- **Tamanho:** Recomendado 60-100px de largura
- **Uso:** Campo `thumbnail` no frontmatter
- **Exemplo:** `thumbnail: zz_media/classes/th_guerreiro.png`

#### Portrait

- **Propósito:** Imagem principal da classe para corpo da nota
- **Tamanho:** Recomendado 400px de largura
- **Uso:** Campo `portrait` no frontmatter e callout no corpo
- **Exemplo:** `portrait: zz_media/classes/guerreiro.png`

#### Cover

- **Propósito:** Imagem de banner ou capa
- **Tamanho:** Variável, dependendo do design
- **Uso:** Campo `cover` no frontmatter
- **Exemplo:** `cover: zz_media/covers/guerreiro_banner.png`

## Imagens de Personagem

### Padrão de Nomes

Para personagens, use este padrão:

```
zz_media/characters/nome.png
zz_media/characters/th_nome.png
zz_media/covers/nome_banner.png
```

**Exemplos:**

- `zz_media/characters/varkh.png` - Imagem principal
- `zz_media/characters/th_varkh.png` - Thumbnail
- `zz_media/covers/varkh_banner.png` - Banner

### Tipos de Imagem

#### Thumbnail

- **Propósito:** Imagem miniatura para cards e dashboards
- **Tamanho:** Recomendado 60-100px de largura
- **Uso:** Campo `thumbnail` no frontmatter
- **Exemplo:** `thumbnail: zz_media/characters/th_varkh.png`

#### Portrait

- **Propósito:** Imagem principal do personagem para corpo da nota
- **Tamanho:** Recomendado 400px de largura
- **Uso:** Campo `portrait` no frontmatter e callout no corpo
- **Exemplo:** `portrait: zz_media/characters/varkh.png`

#### Cover

- **Propósito:** Imagem de banner ou capa
- **Tamanho:** Variável, dependendo do design
- **Uso:** Campo `cover` no frontmatter
- **Exemplo:** `cover: zz_media/covers/varkh_banner.png`

## Imagens de Localização

### Padrão de Nomes

```
zz_media/locations/nome.png
zz_media/locations/th_nome.png
zz_media/covers/nome_banner.png
```

**Exemplos:**

- `zz_media/locations/nimalis.png` - Imagem principal
- `zz_media/locations/th_nimalis.png` - Thumbnail
- `zz_media/covers/nimalis_banner.png` - Banner

## Imagens de Facção

### Padrão de Nomes

```
zz_media/factions/nome.png
zz_media/factions/th_nome.png
```

**Exemplos:**

- `zz_media/factions/guardioes_veu_cinzento.png` - Imagem principal
- `zz_media/factions/th_guardioes_veu_cinzento.png` - Thumbnail

## Imagens de Item

### Padrão de Nomes

```
zz_media/items/nome.png
zz_media/items/th_nome.png
```

**Exemplos:**

- `zz_media/items/grisalma.png` - Imagem principal
- `zz_media/items/th_grisalma.png` - Thumbnail

## Imagens de Mapa

### Padrão de Nomes

```
zz_media/maps/nome.png
zz_media/maps/nome_detalhe.png
```

**Exemplos:**

- `zz_media/maps/earthropo.png` - Mapa principal
- `zz_media/maps/nimalia_detalhe.png` - Mapa detalhado

## Regras de Nomenclatura

1. **Use minúsculas** - Todos os nomes de arquivo devem estar em minúsculas
2. **Use underscores** - Separe palavras com underscores, não espaços ou hífens
3. **Seja descritivo** - Nomes devem ser claros e identificáveis
4. **Evite duplicatas** - Não use números sequenciais (ex: `imagem1.png`, `imagem2.png`)
5. **Use português** - Nomes de arquivo devem estar em português

**Exemplos corretos:**

- `varkh.png`
- `guardioes_veu_cinzento.png`
- `nimalis.png`
- `grisalma.png`

**Exemplos incorretos:**

- `Varkh.png` (maiúsculas)
- `varkh-nimalis.png` (hífens)
- `imagem1.png` (não descritivo)
- `varkh character.png` (espaços)

## Formatos de Arquivo

### Formatos Aceitos

- **PNG** - Recomendado para imagens com transparência
- **JPG** - Aceito para fotografias
- **WEBP** - Aceito para compressão eficiente

### Formatos Não Recomendados

- **GIF** - Use apenas para animações
- **BMP** - Não use (tamanho excessivo)
- **TIFF** - Não use (tamanho excessivo)

## Tamanhos Recomendados

### Thumbnails

- **Largura:** 60-100px
- **Altura:** Proporcional
- **Formato:** PNG
- **Propósito:** Cards e dashboards

### Portraits

- **Largura:** 400px
- **Altura:** Proporcional
- **Formato:** PNG
- **Propósito:** Corpo da nota

### Covers

- **Largura:** Variável (800-1200px)
- **Altura:** Proporcional
- **Formato:** PNG ou JPG
- **Propósito:** Banners e capas

### Mapas

- **Largura:** Variável (1200-2000px)
- **Altura:** Proporcional
- **Formato:** PNG ou JPG
- **Propósito:** Visualização geográfica

## Otimização

### Compressão

- Use compressão sem perda para PNG
- Use compressão com qualidade 80-90% para JPG
- Evite imagens maiores que 2MB quando possível

### Transparência

- Use PNG para imagens com transparência
- Use JPG para imagens sem transparência (menor tamanho)

## Integração com Frontmatter

### Campo thumbnail

```yaml
thumbnail: zz_media/characters/th_varkh.png
```

### Campo portrait

```yaml
portrait: zz_media/characters/varkh.png
```

### Campo cover

```yaml
cover: zz_media/covers/varkh_banner.png
```

## Uso em Notas

### Retrato Lateral

```markdown
> [!NOTE|clean no-i right]+ Retrato
> ![[portrait|400]]
```

### Imagem no Corpo

```markdown
![[zz_media/characters/varkh.png|600]]
```

### Imagem com Legenda

```markdown
![[zz_media/characters/varkh.png|Varkh Nimalis]]
```

## Evitar

- **Imagens soltas sem categoria** - Sempre coloque em subpasta apropriada
- **Nomes genéricos** - Use nomes descritivos
- **Imagens duplicadas** - Não tenha cópias da mesma imagem
- **Imagens muito grandes** - Otimize para web
- **Espaços em nomes** - Use underscores

## Migração Futura

Ao migrar imagens existentes:

1. **Crie estrutura de pastas** - Organize por categoria
2. **Renomeie arquivos** - Siga padrão de nomenclatura
3. **Otimize imagens** - Comprima se necessário
4. **Atualize frontmatter** - Atualize caminhos de imagem
5. **Atualize links** - Atualize wikilinks de imagem
6. **Teste** - Verifique se todas as imagens carregam corretamente

## Referência Disgraceland

O padrão de mídia de Disgraceland foi usado como referência para:

- Uso de thumbnails `th_*.png`
- Organização em `zz_media/`
- Separação por categorias
- Uso de campo `thumbnail` no frontmatter
- Uso de campo `cover` para banners

Omnisvera adapta esses elementos com estrutura mais organizada e nomenclatura em português.

## Documentos Relacionados

- `Workflow/OMNISVERA_NOTE_STANDARD.md` - Padrão geral de notas
- `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` - Esquema de frontmatter
- `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` - Sistema de dashboards
- `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` - Guia de templates
