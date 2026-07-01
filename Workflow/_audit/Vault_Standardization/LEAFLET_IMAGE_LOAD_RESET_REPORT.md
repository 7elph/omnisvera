# Reset de carregamento de imagens do Leaflet

Data: 2026-07-01

## Objetivo

Fazer os mapas principais voltarem a carregar imagem base no Obsidian Leaflet, reduzindo os blocos `leaflet` ao mínimo necessário e removendo estado persistido antigo do plugin.

Esta etapa não tenta preservar marcadores. A prioridade é confirmar que as imagens carregam.

## Escopo autorizado

Arquivos operacionais alterados:

- `MAPA DE EARTHROPO.md`
- `MAPA DE NIMALIA.md`
- `MAPA DE NIMALIS.md`
- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`

Arquivo de relatório criado:

- `Workflow/_audit/Vault_Standardization/LEAFLET_IMAGE_LOAD_RESET_REPORT.md`

Arquivos fora do escopo não foram intencionalmente alterados nesta correção.

## Estado inicial observado

- Branch: `devin/create-omnisvera-class-standard`
- Obsidian não foi detectado em execução antes da alteração.
- O arquivo `.obsidian/plugins/obsidian-leaflet-plugin/data.json` já estava modificado localmente antes desta etapa.
- O `data.json` estava com JSON válido antes da alteração.
- Havia sujeira local fora do escopo em notas, imagens e relatórios; nada disso deve entrar neste commit.

## Referência do Disgraceland

O vault legado Disgraceland foi encontrado em:

- `C:\Users\delib\Desktop\DisgracelandOnline`

O arquivo de mapa legado usa bloco Leaflet com caminho direto da imagem:

```leaflet
id: tribucia-map
image: zz_media/Tribucia.png
```

Ou seja: o padrão funcional observado no legado usa caminho direto `zz_media/...`, não wikilink `[[...]]`.

## Imagens verificadas

| Imagem | Estado |
|---|---|
| `zz_media/earthropo.png` | existe |
| `zz_media/mapa-de-nimalia.png` | existe |
| `zz_media/mapa-de-nimalis.png` | existe |
| `zz_media/nimalia.png` | não existe |

## Blocos Leaflet aplicados

### Earthropo

```leaflet
id: earthropo-map
image: zz_media/earthropo.png
height: 700px
lat: 50
long: 50
minZoom: 1
maxZoom: 10
defaultZoom: 5
unit: meters
scale: 1
```

### Nimalia

```leaflet
id: nimalia-kingdom-map
image: zz_media/mapa-de-nimalia.png
height: 700px
lat: 50
long: 50
minZoom: 1
maxZoom: 10
defaultZoom: 5
unit: meters
scale: 1
```

### Nimalis

```leaflet
id: nimalis-city-map
image: zz_media/mapa-de-nimalis.png
height: 700px
lat: 50
long: 50
minZoom: 1
maxZoom: 10
defaultZoom: 5
unit: meters
scale: 1
```

## Marcadores removidos dos blocos Leaflet

Os marcadores declarados diretamente nos blocos das notas foram removidos para testar carregamento puro da imagem.

| Nota | Marcadores removidos do bloco |
|---|---:|
| `MAPA DE EARTHROPO.md` | 6 |
| `MAPA DE NIMALIA.md` | 6 |
| `MAPA DE NIMALIS.md` | 10 |

## Estado persistido do plugin

Antes do reset, o `data.json` ainda continha estado persistido para:

- `tribucia-map`
- `nimalia-capital-map`
- `nimalis-city-map`

Esses estados somavam 86 marcadores persistidos.

Comparado ao `HEAD`, o reset também limpa estados anteriores de trabalho para:

- `earthropo-map`
- `nimalia-kingdom-map`

A seção `mapMarkers` foi redefinida para uma lista vazia:

```json
"mapMarkers": []
```

Isso força o plugin a recriar estado limpo a partir dos blocos atuais.

## Marcadores removidos do estado persistido

Como autorizado, os marcadores antigos foram removidos nesta etapa. Eles deverão ser recriados manualmente dentro do Obsidian/Leaflet depois que a imagem base estiver funcionando.

| Mapa/estado antigo | Marcadores removidos |
|---|---:|
| `tribucia-map` | 82 |
| `nimalia-capital-map` | 2 |
| `nimalis-city-map` | 2 |
| Total | 86 |

## Validação técnica

- JSON do Leaflet validado com sucesso após o reset.
- Nenhuma imagem foi movida, renomeada ou alterada.
- Nenhuma nota narrativa foi migrada.
- Nenhum frontmatter de personagem, local, território, item ou lore foi alterado por esta etapa.

## Como testar no Obsidian

1. Fechar completamente o Obsidian.
2. Abrir o vault Omnisvera novamente.
3. Abrir:
   - `MAPA DE EARTHROPO.md`
   - `MAPA DE NIMALIA.md`
   - `MAPA DE NIMALIS.md`
4. Confirmar se a imagem base aparece em cada bloco Leaflet.
5. Se aparecer, recriar marcadores manualmente pelo plugin.

## Se ainda falhar

Se a imagem ainda não aparecer mesmo com blocos mínimos:

1. Testar temporariamente `image: [[zz_media/earthropo.png]]` em um mapa isolado.
2. Criar uma nota nova de teste com apenas um bloco Leaflet mínimo.
3. Criar um mapa novo pelo próprio plugin para observar o formato que ele gera.
4. Verificar o console de desenvolvedor do Obsidian em busca de erro de caminho, URI ou permissões.
5. Confirmar se o plugin está ativo e atualizado dentro do Obsidian.

## Observação

As seções textuais das notas de mapa ainda podem mencionar marcadores planejados ou antigos. Nesta etapa elas foram preservadas porque o objetivo foi corrigir o carregamento da imagem base, não revisar o conteúdo cartográfico.
