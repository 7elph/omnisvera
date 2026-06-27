# Correção de DataCards Operacionais e Mídia Existente

Data: 2026-06-27

## Objetivo

Corrigir vazamentos de `Workflow`/legado em consultas operacionais e aproveitar imagens já existentes em `zz_media` quando a correspondência com a nota era direta.

## Consultas ajustadas

| arquivo | ajuste |
|---|---|
| `Home.md` | Consultas por `#location`, `#faction` e `#story` agora excluem `Workflow/`. |
| `Home_Mestre.md` | Consultas por `#home`, `#story`, `#territorio`, `#location`, `#race` e recentes agora excluem `Workflow/` e/ou `Templates/`. |
| `NOTES.md` | Consulta de modificados recentes agora exclui `Workflow/` e `Templates/`. |
| `EARTHROPO/EARTHROPO.md` | DataCards de capítulos agora exclui `Workflow/` e `Templates/`. |

## Conteúdo legado removido da camada operacional

- `Home.md`, `Home_Mestre.md`, `NOTES.md` e `EARTHROPO/EARTHROPO.md` não mencionam mais `Disgraceland`, `TRIBUCIA` ou `Tribucia` como conteúdo operacional.
- Documentação em `Workflow` pode continuar mencionando legado, porque é contexto técnico/histórico.

## Imagens aplicadas

### Facções

| nota | imagem |
|---|---|
| `Factions/Coroa de Nimalia.md` | `zz_media/coroa-de-nimalia.png` |
| `Factions/Conclave dos Errantes.md` | `zz_media/conclave-dos-errantes.png` |
| `Factions/Guardiões do Véu Cinzento.md` | `zz_media/os-guardioes-do-veu-cinzento.png` |
| `Factions/Guilda dos Mercadores.md` | `zz_media/guilda-dos-mercadores.png` |
| `Factions/Guarda Real de Nimalia.md` | `zz_media/guarda-real-nimalia.png` |
| `Factions/Culto dos Sussurrantes.md` | `zz_media/culto-dos-sussurrantes.png` |
| `Factions/Sentinelas de Leth'valora.md` | `zz_media/sentinelas-de-leth'valora.png` |

### Locais

| nota | imagem |
|---|---|
| `Locations/Maré Baixa.md` | `zz_media/mare-baixa.png` |
| `Locations/Casa da Moeda de Nimalia.md` | `zz_media/casa-da-moeda-exterior.png` |
| `Locations/Nimalis.md` | `zz_media/mapa-de-nimalis.png` |
| `Locations/Ruínas de Valthor.md` | `zz_media/ruinas-de-valthor.png` |
| `Locations/Fortaleza de Gharok.md` | `zz_media/fortaleza-de-gharok.png` |
| `Locations/Leth'valora.md` | `zz_media/sentinelas-de-leth'valora.png` como substituição provisória para referência quebrada. |

### Lore, religião e itens

| nota | imagem |
|---|---|
| `Lore/O Fraturamento.md` | `zz_media/o-fraturamento.png` |
| `Lore/Eclipse de Obsidiana.md` | `zz_media/eclipse-obsidiana.png` |
| `Religion/Fé dos Antigos.md` | `zz_media/fe-dos-antigos.png` |
| `Religion/Igreja das Chamas.md` | `zz_media/igreja-das-chamas.png` |
| `Religion/Caminho dos Errantes.md` | `zz_media/caminho-dos-errantes.png` |
| `Religion/RELIGION.md` | `zz_media/fe-dos-antigos.png` como capa provisória do índice. |
| `Items/Adagas de Espectro Fantasma.md` | `zz_media/adagas-de-espectro-fantasma.png` |
| `Items/Manto Primordial do Ancião.md` | `zz_media/manto-primordial.png` |
| `Items/O Medalhão dos Guardiões do Véu Cinzento.md` | Corrigido embed `med.png` → `med.PNG`. |

## Validação

Resultado da checagem de referências de mídia em arquivos operacionais auditados:

```text
refs 95
missing 0
```

## Pendências

- `Locations/Leth'valora.md` precisa de imagem própria se o Sage quiser separar visualmente vila e facção dos Sentinelas.
- Algumas notas ainda têm imagens possíveis em `zz_media`, mas não foram alteradas porque a correspondência não era inequívoca.
- `.obsidian/plugins/obsidian-leaflet-plugin/data.json` segue fora de escopo; alteração local observada é apenas `lastAccessed`.
