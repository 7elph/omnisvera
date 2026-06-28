# Omnisvera — Guia de Tags-Ponte

Fonte da verdade relacionada: [[OMNISVERA_SYSTEM_TAXONOMY]]

## Objetivo

Durante a migração, algumas tags antigas/inglesas podem continuar como ponte para manter Dataview, DataCards e Supercharged Links funcionando.

## Tags-ponte permitidas temporariamente

| Tag antiga/ponte | Tag Omnisvera | Status |
|---|---|---|
| `faction` | `faccao` | ponte temporária |
| `location` | `local` | ponte temporária |
| `race` | `raca` | ponte temporária |
| `class` | `classe` | ponte temporária |
| `story` | `story` | mantida conscientemente |

## Tags antigas já migradas

| Antiga | Nova |
|---|---|
| `loyalist` | `coroa-de-nimalia` |
| `rancher` | `guilda-dos-mercadores` |
| `pirate` | `conclave-dos-errantes` |
| `widow` | `guardioes-do-veu-cinzento` |
| `third` | `sentinelas-de-lethvalora` |
| `murray` | `nobreza-de-nimalia` |
| `steeltown` | `nimalia` |
| `water` | `mar-da-neblina` |
| `individual` | `personagem` |
| `religion` | `religiao` |
| `territory` | `territorio` |

## Regra prática

Em notas novas, preferir tags Omnisvera.

Durante transição, é aceitável usar:

```yaml
tags:
  - faction
  - faccao
  - coroa-de-nimalia
```

Depois da estabilização, as tags-ponte podem ser removidas em lote próprio.
