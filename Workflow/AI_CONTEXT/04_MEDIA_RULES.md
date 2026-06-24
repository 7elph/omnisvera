# Regras de Mídia

Padrões e regras para gerenciamento de imagens no vault Omnisvera.

## Localização

- Todas as imagens ficam em `zz_media/`
- Usar subpastas organizadas por tipo:
  - `zz_media/characters/` - retratos de personagens
  - `zz_media/characters/thumbnails/` - miniaturas de personagens
  - `zz_media/factions/` - símbolos, estandartes e imagens de facções
  - `zz_media/items/` - artefatos e equipamentos
  - `zz_media/locations/` - paisagens, cidades, ruínas e construções
  - `zz_media/lore/` - eventos, fenômenos e conceitos de lore
  - `zz_media/maps/` - mapas usados pelas notas e pelo Leaflet
  - `zz_media/territories/` - imagens de territórios
  - `zz_media/ui/` - cartões, banners e imagens de navegação

## Nomenclatura

- Usar kebab-case (ex: `padre-oric.webp`, `sentinelas-de-leth-valora.png`)
- Evitar acentos em nomes de arquivo
- Evitar espaços em nomes de arquivo
- Usar extensões apropriadas (.png, .jpg, .webp)
- Manter nomes descritivos e curtos

## Referências em notas

- `cover` deve apontar para arquivo existente
- `thumbnail` deve apontar para arquivo existente
- Embeds `![[ ]]` devem apontar para arquivos existentes
- Usar caminhos relativos a partir da raiz do vault
- Exemplo: `zz_media/characters/padre-oric.webp`

## Deleção de imagens

- Não deletar imagem sem verificar referências
- Buscar referências em todas as notas .md antes de deletar
- Verificar referências em Workflow/Legacy antes de considerar legado
- Documentar imagens deletadas no relatório

## Imagens legadas

- Material de Disgraceland deve ficar separado
- Não usar imagens de Disgraceland como cânone
- Converter apenas imagens deliberadamente aprovadas pelo Sage
- Manter imagens legadas em subpastas separadas se necessário

## Imagens novas

- Imagens novas devem seguir padrão de nomenclatura
- Imagens novas devem ser colocadas em subpastas apropriadas
- Registrar novas imagens no relatório da tarefa
- Atualizar covers de notas ao adicionar imagens

## Formatos

- Preferir .webp para UI e cartões (compressão eficiente)
- Usar .png para transparências
- Usar .jpg para fotos sem transparência
- Evitar formatos proprietários

## Tamanhos

- Thumbnails: até 200px de largura
- Covers: até 800px de largura
- Mapas: conforme necessário para Leaflet
- UI: conforme necessário para layout

## Validação

- Verificar que todas as referências apontam para arquivos existentes
- Verificar que não há imagens órfãs (sem referências)
- Verificar que não há duplicatas desnecessárias
- Verificar que nomes seguem padrão estabelecido
