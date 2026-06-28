# Earthropo — Relatório de Padronização Estrutural

Data: 2026-06-28  
Escopo: `EARTHROPO/`

## Objetivo

Padronizar a pasta `EARTHROPO/` para funcionar como uma página de campanha no estilo técnico herdado de Disgraceland, mas com vocabulário, tags, consultas e conteúdo de Omnisvera.

Esta etapa não executou migração em massa de notas. O foco foi:

- transformar `EARTHROPO/EARTHROPO.md` em página-motor do continente;
- impedir que DataCards puxem conteúdo de `Workflow/` ou legado;
- corrigir frontmatter das crônicas;
- corrigir discrepâncias óbvias de geografia e personagem;
- manter `story` e `chapters` como eixo funcional;
- preparar `Capítulo 01` sem canonizar eventos ainda não jogados.

## Arquivos alterados

| Arquivo | Ação |
|---|---|
| `EARTHROPO/EARTHROPO.md` | Reestruturado como homepage de Earthropo com capa, sinopse, crônicas de origem, capítulos, personagens em foco, eixos ativos e pendências. |
| `EARTHROPO/00 - O Bastardo de Ferro.md` | Frontmatter padronizado; tag `chapter0` corrigida para `chapter00`; adicionadas tags de origem; resumo ajustado para não tratar Elarion como simples exilador. |
| `EARTHROPO/00 - O Corvo da Maré Baixa.md` | Frontmatter padronizado; adicionadas tags de origem; localização ligada a `[[Maré Baixa]]`; correção da maioria antropo para Nimalia, não Earthropo inteiro. |
| `EARTHROPO/00 - As Crônicas de Névoa de Sangue.md` | Frontmatter padronizado; adicionadas tags de origem; localização de Raziel ajustada para norte de Earthropo; DataCards ampliado para incluir antagonistas relacionados. |
| `EARTHROPO/01 - Ecos do Mundo Perdido.md` | Reescrito como nota operacional de preparação do primeiro capítulo coletivo, sem canonizar eventos ainda não jogados. |

## Estrutura aplicada em `EARTHROPO.md`

O arquivo agora segue o padrão funcional do exemplo de Disgraceland:

- frontmatter com `cover`, `cssclasses`, `type`, `visibility`, `spoiler_level`, `gm_secret` e tags;
- imagem centralizada;
- callout `[!world]- SINOPSE`;
- separador visual com `homepage`;
- bloco `[!infobox]` com DataCards das crônicas de origem;
- bloco `[!world]+ CAPÍTULOS` com DataCards dos capítulos em `EARTHROPO/`;
- cards de personagens em foco;
- tabelas e seções de controle de cânone.

## Tags funcionais adicionadas

| Tag | Uso |
|---|---|
| `origin-story` | Marca crônicas de origem de personagem. |
| `origin-vezemir` | Alimenta o card de origem de Vezemir em `EARTHROPO.md`. |
| `origin-varkh` | Alimenta o card de origem de Varkh em `EARTHROPO.md`. |
| `origin-raziel` | Alimenta o card de origem de Raziel em `EARTHROPO.md`. |
| `chapter00` | Mantém compatibilidade do capítulo 00. |
| `chapter01` | Marca o primeiro capítulo coletivo planejado. |
| `story` | Mantida conscientemente como eixo de crônicas/capítulos. |

## Correções de consistência aplicadas

| Tema | Correção |
|---|---|
| Earthropo | Mantido como continente, não mundo inteiro. |
| Nimalia | Mantida como reino dos antropos. |
| Nimalis | Tratada como capital de Nimalia. |
| Varkh | A maioria antropo foi atribuída a Nimalia, não a Earthropo inteiro. |
| Vezemir | A saída de Leth'valora foi suavizada para decisão de Elarion para salvá-lo, não “exílio” simples. |
| Mira | Mantida como filha do chefe humano de Leth'valora. |
| Leth'valora | Tratada como vila pequena de Avenor, não reino élfico. |
| Raziel | Mantido com tormento de mais de trezentos anos; a prisão foi posicionada genericamente no norte de Earthropo. |
| Valthor/Gharok | Links curtos quebrados foram substituídos por `[[Ruínas de Valthor|Valthor]]` e `[[Fortaleza de Gharok|Gharok]]`. |

## DataCards e Dataview

As consultas foram ajustadas para evitar vazamento de `Workflow/` e conteúdo técnico:

- `EARTHROPO.md` usa `FROM "EARTHROPO"` para capítulos.
- Crônicas de origem usam tags específicas (`origin-vezemir`, `origin-varkh`, `origin-raziel`).
- Blocos de personagens importantes usam `FROM "Characters/Individual"`.
- `Capítulo 01` usa Dataviews de `#quest` e `#rumor`, sem criar `sessions` nem `#session`.

## Validação executada

Resultados:

- todos os arquivos `.md` em `EARTHROPO/` possuem frontmatter com abertura e fechamento em linhas próprias;
- nenhuma ocorrência encontrada em `EARTHROPO/` para:
  - `Disgraceland`;
  - `TRIBUCIA`;
  - `Eryndor`;
  - `Nimalis|nome em aberto`;
  - `Em Earthropo, os antropos`;
  - `exilado por seu mentor`;
  - `#session`;
  - `sessions`;
  - `player_known`;
  - `life_status`;
  - `handout_image`;
- nenhum wikilink quebrado encontrado dentro de `EARTHROPO/`;
- imagens usadas como capas existem em `zz_media/`.

## Pendências restantes

| Pendência | Motivo |
|---|---|
| `Mar da Neblina` | Ainda não há nota ativa encontrada; foi mantido como texto simples em `Capítulo 01` para evitar link quebrado. |
| Ponto de encontro dos personagens | Ainda depende de decisão de preparação da primeira sessão. |
| Bordas de Nimalia | Ainda dependem de mapa e decisão do Sage. |
| Posição final de Gharok | Mantida em aberto conforme documentação canônica atual. |
| Relação exata entre Criadores, Véu, dragão e sangue antigo | Mantida como segredo do mestre, sem exposição total no capítulo 01. |

## Recomendação

Antes de mexer em lote 2, revisar visualmente no Obsidian:

1. `EARTHROPO/EARTHROPO.md`;
2. os três cards de crônicas de origem;
3. o grid de capítulos;
4. a nota `01 - Ecos do Mundo Perdido.md`;
5. se as capas aparecem corretamente nos DataCards.

Depois disso, o próximo passo seguro é padronizar o conteúdo relacionado diretamente a Earthropo que aparece nos cards e links:

- `Locations/Maré Baixa.md`;
- `Locations/Nimalis.md`;
- `Territories/Nimalia.md`;
- `Locations/Ruínas de Valthor.md`;
- `Locations/Fortaleza de Gharok.md`;
- `Factions/Clã Sanguinallis.md`;
- `Factions/Sentinelas de Leth'valora.md`.
