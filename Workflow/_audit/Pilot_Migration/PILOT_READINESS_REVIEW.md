# Revisão de Prontidão para Piloto — Omnisvera

Data: 2026-06-27

## Classificação

`READY_FOR_PILOT`

O vault está pronto para um micro-piloto controlado de até 4 notas. A conclusão se limita ao piloto técnico; não autoriza migração em massa.

## Checklist obrigatório

| item | resultado | evidência |
|---|---|---|
| `Home_Jogadores.md` foi removido da raiz? | Sim | `git ls-files` e listagem da raiz mostram apenas `Home.md` e `Home_Mestre.md`. |
| `Home.md` está sem campos rejeitados? | Sim | Não há `player_known`, `life_status` ou `handout_image` em `Home.md`. |
| `Home.md` está sem `#session`? | Sim | Consulta usa `#story`; não usa `#session`. |
| `Home_Mestre.md` está sem links operacionais para Disgraceland? | Sim | Links históricos ficaram recolhidos e marcados como anteriores à taxonomia atual. |
| `#territory` foi substituído por `#territorio` em dashboards ativos? | Sim | `Home_Mestre.md` usa `#territorio`. |
| `third` foi resolvido? | Sim | `third` foi substituído por `sentinelas-de-lethvalora` em Supercharged Links e documentação ativa. |
| `murray` foi resolvido? | Sim | `murray` foi substituído por `nobreza-de-nimalia` em Supercharged Links e documentação ativa. |
| `story` está mantido conscientemente? | Sim | `story` permanece como eixo temporário de história/capítulo/campanha. |
| Templates RPG existem? | Sim | Existem templates em `Templates/RPG` para raça, classe, magia, item, monstro, quest e rumor. |
| Índices de raças/classes/magias/monstros existem? | Sim | Existem índices em `Rules/Races`, `Rules/Classes`, `Rules/Spells` e `Bestiary`. |
| Categorias RPG aprovadas existem? | Sim | Existem `Rules`, `Items`, `Bestiary`, `CAMPANHA/Quests` e `CAMPANHA/Rumors`. |
| Há bloqueador antes do piloto? | Não | Restam pendências históricas/documentais e uma alteração local de Leaflet por `lastAccessed`, fora do escopo. |

## Validações executadas

```powershell
rg -n "Home_Jogadores" . --glob '!**/.git/**' --glob '!**/node_modules/**' --glob '!Workflow/_archive/**'
rg -n "player_known|life_status|handout_image|#session" Home.md Home_Mestre.md Templates
rg -n "Workflow/Legacy/Disgraceland|Disgraceland|TRIBUCIA" Home.md Home_Mestre.md Templates
rg -n "#territory|#religion|#individual" Home.md Home_Mestre.md Templates
rg -n "third|murray" .obsidian Home.md Home_Mestre.md Templates Factions Characters Territories Locations Lore Religion --glob '!**/main.js' --glob '!**/*.map' --glob '!copilot-index-*.json'
```

## Observações

- Ocorrências de `Home_Jogadores` permanecem apenas em relatórios históricos/auditorias e no arquivo arquivado.
- O índice/cache local do plugin Copilot não está versionado e não foi alterado.
- `.obsidian/plugins/obsidian-leaflet-plugin/data.json` permanece fora do escopo porque a alteração local conhecida é apenas `lastAccessed`.
- Este resultado permite apenas micro-piloto. Migração em massa continua bloqueada até revisão do relatório do piloto.
