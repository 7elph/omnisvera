---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - workflow
  - assistant
  - handoff
  - backup
---

# Handoff dos Assistentes - Omnisvera

Este arquivo e a memoria operacional curta para outra IA continuar o trabalho no vault.

> [!IMPORTANT]
> Ler este arquivo antes de alterar notas.
> O vault esta em transicao ativa e possui mudancas locais ainda nao commitadas.

## Estado Atual do Repositorio

- Repositorio: `7elph/omnisvera`
- Branch atual: `devin/create-omnisvera-class-standard`
- Data deste handoff: 2026-07-05
- Nao assumir que o GitHub esta atualizado; ha mudancas locais importantes no working tree.
- Nao usar `git add .` nem `git add -A`.
- Separar commits por tema.

## Mudancas Locais Importantes Ainda Nao Consolidadas

### Resumo Executivo Para Outra IA

O vault esta em uma fase de transicao entre infraestrutura e conteudo de campanha.

Prioridade atual:

1. Preservar as mudancas manuais do Sage.
2. Nao fazer migracao massiva sem plano.
3. Manter notas publicas/player-safe leves.
4. Concentrar segredos pesados no `CAMPANHA/ESTADO_DA_CAMPANHA.md` e nos dossies.
5. Validar links, imagens e DataCards antes de mexer em lote grande.

Mudanca mais importante para classes:

```txt
Vampiro nao e mais classe principal.
Vampiro = raca / condicao.
Hemomante = classe.
Vampiro Sanguinallis = linhagem / lore.
Sangue Antigo = camada especial de campanha.
```

Essa decisao afeta principalmente `Raziel`, notas de `Classes/`, `Races/` e lore de sangue/vampiros.

### Estado da Campanha

`CAMPANHA/ESTADO_DA_CAMPANHA.md` foi reduzido para funcionar como cockpit de mestre.

Material pesado foi dividido em:

- [[DOSSIE - Capitulo 01 e DORN-7]]
- [[DOSSIE - Remedios Falsos e Odran]]
- [[DOSSIE - Coroa Augustus e Nimalis]]
- [[DOSSIE - Personagens Jogadores e Arcos Pessoais]]
- [[DOSSIE - Cosmologia Veu Criadores e Religioes]]
- [[DOSSIE - Segredos Centrais e Pendencias]]

Esses arquivos ficam em:

```txt
CAMPANHA/Dossies/
```

Regra: `ESTADO_DA_CAMPANHA` deve ser painel de consulta rapida; dossies guardam bastidores longos.

### Rumores e Quests

O conteudo "Remedios Falsos de Mare Baixa" deixou de ser lore e virou rumor/campanha.

O arquivo antigo foi removido:

```txt
Lore/Remedios Falsos de Mare Baixa.md
```

Novo alvo real no vault:

```txt
CAMPANHA/Rumors/02 - Remedios Falsos da Mare Baixa.md
```

Observacao: o nome real do arquivo usa acentos no Windows/Obsidian:

```txt
CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md
```

Links antigos foram atualizados para apontar para o novo rumor com alias visual:

```md
[[02 - Remédios Falsos da Maré Baixa|Remédios Falsos de Maré Baixa]]
```

Tambem ha renome local de:

```txt
CAMPANHA/Quests/Quest 01 - Investigar Avistamentos de Dragoes.md
-> CAMPANHA/Quests/01 - Investigar Avistamentos de Dragoes.md

CAMPANHA/Rumors/Rumor 01 - Dragoes ao Sul de Nimalia.md
-> CAMPANHA/Rumors/01 - Dragoes ao Sul de Nimalia.md
```

Os nomes reais desses arquivos tambem usam acentos no vault.

### Mudanca Principal de Classes/Racas

Decisao atual do Sage:

```txt
Vampiro = raca / condicao
Hemomante = classe
Vampiro Sanguinallis = linhagem / lore
Sangue Antigo = camada unica de campanha
```

Arquivos relevantes:

- `Races/Vampiro.md`
- `Classes/Hemomante.md`
- `Lore/Sangue Antigo.md`
- `Lore/Vampiro Sanguinallis.md`
- `Characters/Individual/Raziel.md`

Estado esperado de Raziel:

```yaml
class: Hemomante
race: Vampiro
```

No corpo da nota:

```md
**Classe:** [[Hemomante]]
**Raca:** [[Vampiro]]
**Linhagem:** [[Vampiro Sanguinallis]]
**Camada especial:** [[Sangue Antigo]]
```

Nao tratar `Vampiro` como classe nova.

`Classes/Hemomante.md` e a nova nota mecanica principal para a tecnica de sangue.

Estado atual dos arquivos:

```txt
Races/Vampiro.md
- Deve explicar a raca/condicao vampirica.
- Nao deve funcionar como classe.

Classes/Hemomante.md
- Deve explicar a classe/mecanica de manipulacao de sangue.
- Deve ser usada para Raziel.
- Regras ainda em revisao de mesa.

Lore/Vampiro Sanguinallis.md
- Deve representar linhagem/lore, nao classe.

Lore/Sangue Antigo.md
- Deve representar camada especial da campanha.
- Nao substitui raca nem classe.

Characters/Individual/Raziel.md
- Deve usar race: Vampiro.
- Deve usar class: Hemomante.
```

Separacao conceitual recomendada:

| Camada | Arquivo | Funcao |
|---|---|---|
| Raca / condicao | `Races/Vampiro.md` | O que Raziel e biologica/sobrenaturalmente |
| Classe | `Classes/Hemomante.md` | O que Raziel faz em termos mecanicos |
| Linhagem | `Lore/Vampiro Sanguinallis.md` | Origem/sangue/familia/lore |
| Mistério de campanha | `Lore/Sangue Antigo.md` | Camada especial, rara e progressiva |

Regra para outra IA:

- Nao recriar `Vampiro` como classe ativa.
- Nao commitar PDFs de regras no repositorio.
- Pode trazer tabelas numericas e consulta mecanica para as notas quando o Sage pedir, preservando fonte e evitando texto integral desnecessario.
- Se precisar expandir regras de classe, expandir `Classes/Hemomante.md`.
- Se precisar expandir a condicao vampirica, expandir `Races/Vampiro.md`.
- Segredos profundos sobre `Sangue Antigo` devem ficar em `ESTADO_DA_CAMPANHA`/dossies, nao na nota publica de Raziel.

## Pendencias Tecnicas Imediatas

Validacao mais recente:

- Frontmatter/YAML: 0 problemas.
- Wikilinks quebrados restantes: 3.

Links quebrados conhecidos:

```txt
[[Paladino]] em Characters/Individual/Augustus Terra Decimus.md
[[Paladino]] em Characters/Individual/General Cassian Valerius.md
[[Kenkus]] em Characters/Individual/Varkh Nimalis.md
```

Recomendacao:

- Trocar `[[Kenkus|Antropo Kenku]]` por `[[Kenku|Antropo Kenku]]`.
- Para `[[Paladino]]`, decidir entre:
  - criar `Classes/Paladino.md`; ou
  - transformar em texto simples; ou
  - apontar para classe existente, se houver.

## Dataview / DataCards

Problema provavel detectado:

Muitos campos de imagem estao como caminho puro:

```yaml
cover: zz_media/...
thumbnail: zz_media/...
```

Em alguns DataCards isso pode aparecer como texto em vez de imagem.

Padrao possivelmente necessario para DataCards:

```yaml
cover: [[zz_media/...]]
thumbnail: [[zz_media/...]]
```

Nao aplicar globalmente sem lote proprio. Fazer dry-run antes.

## Notas Modificadas Manualmente pelo Sage

Ha alteracoes locais em varias notas de personagens, Home, Home_Mestre, itens e classe Alquimista.

Antes de qualquer commit, revisar por grupos:

1. Estado da Campanha + Dossies.
2. Vampiro/Hemomante/Raziel/Sangue Antigo.
3. Rumores/Quests renomeados.
4. Personagens alterados manualmente.
5. Home/Home_Mestre.
6. Itens de Vezemir.
7. Backups Leaflet - deixar fora.

Arquivos de backup Leaflet nao devem ser commitados automaticamente:

```txt
.obsidian/plugins/obsidian-leaflet-plugin/data.before-id-alignment.json
.obsidian/plugins/obsidian-leaflet-plugin/data.before-map-reset.json
```

## Principios Atuais do Vault

- O vault deve ser player-safe por padrao.
- Segredos pesados ficam em `CAMPANHA/ESTADO_DA_CAMPANHA.md` ou dossies do mestre.
- Notas principais devem ser completas, bonitas, jogaveis e sem revelar bastidor pesado.
- Disgraceland e referencia tecnica/visual, nao canon.
- Nao migrar em massa sem relatorio.
- Nao apagar midia.
- Nao remover campos legacy sem auditoria.
- Nao remover tags antigas/ponte sem lote proprio.

## Proxima Sequencia Recomendada

1. Corrigir os 3 wikilinks quebrados.
2. Validar a nova estrutura de `Vampiro` / `Hemomante`.
3. Revisar `CAMPANHA/Rumors/02 - Remédios Falsos da Maré Baixa.md`:
   - corrigir `name: Remédio Falsos...` para `Remédios Falsos...`;
   - corrigir titulo com espacos duplos.
4. Separar commits:
   - `content: split campaign state into master dossiers`
   - `content: split vampire race and hemomancer class mechanics`
   - `content: checkpoint manual campaign note updates`
   - `content: rename first quest and rumor notes`
5. Depois disso, revisar DataCards/imagens em lote tecnico.

## Comandos Uteis

Validar frontmatter:

```powershell
python .local-tools/validate_frontmatter.py . --ignore-legacy
```

Validar wikilinks:

```powershell
python .local-tools/validate_links.py . --ignore-legacy
```

Ver estado do Git:

```powershell
git status --short
```

Ver arquivos staged antes de commit:

```powershell
git diff --cached --name-only
```
