# Omnisvera — Correção Pontual de Mapas Leaflet

Gerado em: 2026-07-01

## Problema encontrado

O arquivo `.obsidian/plugins/obsidian-leaflet-plugin/data.json` estava modificado localmente com duas referências de camada apontando para:

- `zz_media%2Fnimalia.png`

Esse arquivo de mídia não existe no vault. As ocorrências estavam dentro do grupo persistido:

- `id`: `nimalia-capital-map`
- arquivo vinculado: `MAPA DE NIMALIS.md`

Portanto, as camadas pertencem ao mapa de Nimalis, não ao mapa geral do reino.

## Ocorrências encontradas

| ocorrência | grupo Leaflet | arquivo vinculado | caminho quebrado | caminho corrigido |
|---|---|---|---|---|
| 1 | `nimalia-capital-map` | `MAPA DE NIMALIS.md` | `zz_media%2Fnimalia.png` | `zz_media%2Fmapa-de-nimalis.png` |
| 2 | `nimalia-capital-map` | `MAPA DE NIMALIS.md` | `zz_media%2Fnimalia.png` | `zz_media%2Fmapa-de-nimalis.png` |

## Arquivos de mapa verificados

| arquivo | existe? | observação |
|---|---|---|
| `zz_media/mapa-de-nimalis.png` | sim | mapa oficial da capital |
| `zz_media/mapa-de-nimalia.png` | sim | mapa oficial do reino |
| `zz_media/earthropo.png` | sim | mapa oficial do continente |
| `zz_media/nimalia.png` | não | caminho quebrado removido da configuração Leaflet |

## Correções aplicadas

- Substituídas as duas camadas quebradas de `zz_media%2Fnimalia.png` por `zz_media%2Fmapa-de-nimalis.png`.
- Nenhuma coordenada foi alterada.
- Nenhum marcador foi removido.
- Nenhuma configuração de zoom, bounds, escala ou visual foi alterada.
- Nenhuma mídia foi movida, renomeada ou criada.

## Ocorrências não alteradas

Nenhuma ocorrência restante de `zz_media/nimalia.png` ou `zz_media%2Fnimalia.png` foi encontrada após a correção.

## Validação

O JSON foi validado com:

```powershell
python -m json.tool .obsidian/plugins/obsidian-leaflet-plugin/data.json | Out-Null
```

Resultado: JSON válido.

## Recomendação de teste no Obsidian

Abrir o Obsidian e testar:

1. `[[MAPA DE NIMALIS]]`;
2. `[[MAPA DE NIMALIA]]`;
3. `[[MAPA DE EARTHROPO]]`;
4. confirmar se os marcadores persistidos do mapa de Nimalis aparecem sobre `zz_media/mapa-de-nimalis.png`.

