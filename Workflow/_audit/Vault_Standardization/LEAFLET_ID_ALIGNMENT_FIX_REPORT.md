# Omnisvera — Correção de IDs Persistidos do Leaflet

Gerado em: 2026-07-01

## Estado inicial

Branch:

- `devin/create-omnisvera-class-standard`

Arquivos modificados antes da tarefa:

- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`
- várias notas narrativas alteradas manualmente;
- várias imagens novas em `zz_media/`;
- `Workflow/_audit/Vault_Standardization/LEAFLET_MAP_DIAGNOSTIC_REPORT.md` ainda não commitado.

Arquivos fora do escopo não incluídos nesta correção:

- notas narrativas;
- notas de mapa;
- `Home.md`;
- `zz_media/*`;
- scripts de migração;
- frontmatter/tags/Dataview/DataCards.

## Obsidian

Não havia processo `Obsidian` detectado antes da alteração.

Mesmo assim, recomenda-se manter o Obsidian fechado durante qualquer edição manual de `.obsidian/plugins/obsidian-leaflet-plugin/data.json`, porque o plugin pode regravar esse arquivo ao salvar estado interno.

## Backup local

Backup criado antes da alteração:

- `.obsidian/plugins/obsidian-leaflet-plugin/data.before-id-alignment.json`

Este backup é local e não deve ser commitado.

## Estrutura detectada no `data.json`

O arquivo usa a chave principal:

- `mapMarkers`

Os grupos de mapa ficam em um array dentro de `mapMarkers`.

Cada grupo observado possui:

- `id`;
- `locked`;
- `lastAccessed`;
- `markers`;
- `overlays`;
- `shapes`;
- `files`.

## IDs encontrados antes

| id | files | markers | observação |
|---|---|---:|---|
| `tribucia-map` | vazio | 82 | grupo legado Disgraceland preservado, sem arquivo ativo |
| `nimalia-capital-map` | `MAPA DE NIMALIS.md` | 2 | grupo persistido antigo/desalinhado com o bloco atual |

## IDs esperados

| mapa | id esperado | imagem esperada |
|---|---|---|
| Earthropo | `earthropo-map` | `zz_media%2Fearthropo.png` |
| Reino de Nimalia | `nimalia-kingdom-map` | `zz_media%2Fmapa-de-nimalia.png` |
| Cidade de Nimalis | `nimalis-city-map` | `zz_media%2Fmapa-de-nimalis.png` |

## Mudanças aplicadas

### Entradas novas criadas

| id | files | markers | observação |
|---|---|---:|---|
| `earthropo-map` | `MAPA DE EARTHROPO.md` | 0 | entrada persistida criada para alinhar com o bloco Leaflet atual |
| `nimalia-kingdom-map` | `MAPA DE NIMALIA.md` | 0 | entrada persistida criada para alinhar com o bloco Leaflet atual |
| `nimalis-city-map` | `MAPA DE NIMALIS.md` | 2 | entrada criada a partir do estado antigo da capital |

### IDs legacy preservados

| id legado | files após correção | markers preservados | observação |
|---|---|---:|---|
| `tribucia-map` | vazio | 82 | preservado como legado sem arquivo ativo |
| `nimalia-capital-map` | vazio | 2 | preservado como legado, mas desassociado de `MAPA DE NIMALIS.md` para evitar conflito com `nimalis-city-map` |

## Paths de imagem

Antes da correção, o diagnóstico indicava ocorrência quebrada de:

- `zz_media%2Fnimalia.png`

Depois da correção:

- `zz_media%2Fnimalia.png` não aparece mais no `data.json`;
- os marcadores persistidos de Nimalis usam `zz_media%2Fmapa-de-nimalis.png`.

## Estado persistido após correção

| id | files | markers | layers |
|---|---|---:|---|
| `tribucia-map` | vazio | 82 | `zz_media%2FTribucia.png` |
| `earthropo-map` | `MAPA DE EARTHROPO.md` | 0 | — |
| `nimalia-kingdom-map` | `MAPA DE NIMALIA.md` | 0 | — |
| `nimalis-city-map` | `MAPA DE NIMALIS.md` | 2 | `zz_media%2Fmapa-de-nimalis.png` |
| `nimalia-capital-map` | vazio | 2 | `zz_media%2Fmapa-de-nimalis.png` |

## Validação

Comando executado:

```powershell
python -m json.tool .obsidian/plugins/obsidian-leaflet-plugin/data.json | Out-Null
```

Resultado:

- JSON válido.

## Arquivos alterados por esta correção

- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`
- `Workflow/_audit/Vault_Standardization/LEAFLET_ID_ALIGNMENT_FIX_REPORT.md`

## Instrução de teste no Obsidian

Abrir o Obsidian e testar:

1. `[[MAPA DE EARTHROPO]]`;
2. `[[MAPA DE NIMALIA]]`;
3. `[[MAPA DE NIMALIS]]`.

Se os mapas aparecerem, verificar se o plugin não regravou o `data.json` voltando para `nimalia-capital-map` ou `zz_media%2Fnimalia.png`.

Se ainda não aparecerem, o próximo teste seguro é deixar o plugin recriar o estado persistido a partir dos blocos Leaflet com o Obsidian aberto e depois comparar o novo `data.json`.

