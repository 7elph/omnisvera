# Padrão de imagens do vault

## Estrutura

- `zz_media/characters/`: retratos completos.
- `zz_media/characters/thumbnails/`: miniaturas de personagens.
- `zz_media/factions/`: símbolos, estandartes e imagens de facções.
- `zz_media/items/`: artefatos e equipamentos.
- `zz_media/locations/`: paisagens, cidades, ruínas e construções.
- `zz_media/lore/`: eventos, fenômenos e conceitos de lore.
- `zz_media/maps/`: mapas usados pelas notas e pelo Leaflet.
- `zz_media/ui/`: cartões, banners e imagens de navegação.

## Convenções

- Nomes em minúsculas, sem acentos e separados por hífens.
- Mapas permanecem em PNG.
- Ilustrações, retratos e cartões usam WebP.
- As notas devem referenciar o caminho completo a partir de `zz_media/`.
- Uma imagem compartilhada por mais de uma nota não deve ser duplicada.

## Imagens incorporadas da conversa “Imagens a Gerar Repositório”

- `locations/fortaleza-de-gharok.webp`
- `locations/ruinas-de-valthor.webp`
- `lore/veu-cinzento.webp`
- `lore/eclipse-de-obsidiana.webp`
- `factions/guardioes-do-veu-cinzento.webp`
- `factions/guilda-das-trevas.webp`

Foram usadas somente as versões finais aprovadas antes da mudança para o próximo pedido da conversa.

## Pendências visuais

Algumas imagens antigas continuam no vault porque ainda são referenciadas por notas ativas. Elas devem ser substituídas quando houver arte nova aprovada:

- `ui/card-guia.webp`: ainda contém o título de Disgraceland.
- `ui/card-cultura.webp`: ainda contém identidade visual da TTV.
- `ui/card-religiao.webp`: arte herdada do template.
- `ui/card-linha-do-tempo.webp`: captura de uma linha do tempo antiga.
- `locations/mare-baixa.webp`: ainda contém o texto “Gutter Row”.

Esses arquivos não foram apagados para evitar capas e cartões quebrados.

## Gerações ainda não incorporadas

- **O Fraturamento:** a imagem “Paisagem apocalíptica de tormenta roxa” já foi gerada e aprovada na conversa, mas ainda precisa ser baixada para substituir `lore/o-fraturamento.webp`.
- **Porto da Maré Baixa:** a primeira geração ainda estava em andamento durante esta limpeza. Ela só deve ser incorporada depois das variações e da aprovação final.

## Limpeza de 21 de junho de 2026

- 445 arquivos sem referência ativa foram removidos.
- Aproximadamente 400,98 MB foram liberados.
- O repositório ativo ficou com 43 arquivos de mídia, totalizando aproximadamente 14,65 MB.
