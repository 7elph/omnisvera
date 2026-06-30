---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Aplicado
tags:
  - workflow
  - audit
  - padronizacao
  - personagens
---

# Relatório de Padronização — Characters/Individual

Status: aplicado em 2026-06-29.

## Objetivo

Padronizar a pasta `Characters/Individual` como primeiro lote estrutural do vault, sem reescrever biografias, sem inventar lore extensa e sem migrar outras categorias.

## Critério Aplicado

- Preservar `NoteIcon: magicitem` nos personagens, porque este é o padrão visual real observado no vault.
- Garantir `type: character`.
- Usar `role` como campo técnico:
  - `player` para personagens dos jogadores;
  - `npc` para personagens do mestre, antagonistas, criaturas e entidades.
- Mover função narrativa/título para `function` quando necessário.
- Garantir `visibility`, `spoiler_level`, `gm_secret`, `status` e `campaign_status`.
- Garantir `chapter` e `chapters` quando a nota tem vínculo de aparição.
- Usar B-Sides/origens com:
  - `bside`;
  - `origin-story`;
  - `origin-vezemir`, `origin-varkh` ou `origin-raziel`.
- Manter tags técnicas herdadas úteis, como `character` e `personagem`.
- Adicionar tags Omnisvera sem remover tags que ainda podem alimentar visual, Dataview ou DataCards.
- Não apagar conteúdo narrativo existente.

## Arquivos Padronizados

| personagem | papel técnico | vínculo principal | alterações principais |
|---|---|---|---|
| `Vezemir.md` | `player` | `00 - O Bastardo de Ferro` | Tags de B-Side/origem adicionadas; tags de classe/raça complementadas |
| `Varkh Nimalis.md` | `player` | `00 - O Corvo da Maré Baixa` | Tags de B-Side/origem, alquimista e Conclave reforçadas |
| `Raziel.md` | `player` | `00 - As Crônicas de Névoa de Sangue` | `chapters` corrigido; facção e território convertidos para wikilinks |
| `Augustus Terra Decimus.md` | `npc` | `01 - Ecos do Mundo Perdido` | `role` normalizado; função de rei movida para `function`; localização ajustada para Nimalis |
| `General Cassian Valerius.md` | `npc` | B-Side de Vezemir / Capítulo 01 | `role` normalizado; função militar movida para `function`; tags de Coroa reforçadas |
| `Elarion Vaelthor.md` | `npc` | B-Side de Vezemir | `chapters` preenchido; tags de Sentinelas e origem adicionadas |
| `Mira Valen.md` | `npc` | B-Side de Vezemir | `chapters` preenchido; capa adicionada; função narrativa registrada |
| `Padre Oric.md` | `npc` | B-Side de Vezemir | `chapters` preenchido; função de investigador dos Guardiões registrada |
| `Mestre Odran Veyl.md` | `npc` | B-Side de Varkh | `chapters` preenchido; thumbnail corrigida; função de mestre de Varkh registrada |
| `Dragão de Colar Dourado.md` | `npc` | B-Side de Vezemir | Visibilidade corrigida para mestre; tags e função narrativa ajustadas |
| `Kaelen, o Flagelo.md` | `npc` | B-Side de Raziel | Facção, território, raça, classe e origem preenchidos a partir da lore existente |
| `Lorde Malakar.md` | `npc` | B-Side de Raziel | Facção, localização, raça, classe e função de alvo final registrados |
| `Vandor, o Senhor das Bestas.md` | `npc` | B-Side de Raziel | Facção, localização, raça, classe e função de alvo de vingança registrados |
| `Unidade DORN-7.md` | `npc` | `01 - Ecos do Mundo Perdido` | Nota criada/normalizada como entidade secreta do mestre |

## Formatos Aplicados

As 14 notas em `Characters/Individual` foram conferidas contra os cinco formatos operacionais atuais:

| formato | notas | status |
|---|---:|---|
| Personagem Jogador | `Vezemir`, `Varkh Nimalis`, `Raziel` | OK |
| NPC Importante | `Augustus Terra Decimus`, `General Cassian Valerius`, `Elarion Vaelthor`, `Mira Valen`, `Padre Oric`, `Mestre Odran Veyl` | OK |
| Antagonista | `Kaelen, o Flagelo`, `Lorde Malakar`, `Vandor, o Senhor das Bestas` | OK |
| Criatura | `Dragão de Colar Dourado`, `Unidade DORN-7` | OK |
| NPC Menor | nenhuma nota atual | sem uso no lote |

Critério de validade usado nesta etapa:

- cada nota precisa manter frontmatter válido;
- cada nota precisa ter as seções obrigatórias do formato correspondente;
- conteúdo antigo não pode ficar preso em seção genérica de migração, como `Conteúdo preservado`;
- notas confidenciais podem existir, mas detalhes pesados devem continuar centralizados no [[CAMPANHA/ESTADO_DA_CAMPANHA|Estado da Campanha]];
- notas públicas/de jogador não devem receber spoilers pesados nesta etapa.

## Padrão Resultante

### Personagens dos Jogadores

Usam:

```yaml
type: character
visibility: Jogadores
spoiler_level: none
gm_secret: false
role: player
tags:
  - player
  - jogador
  - character
  - personagem
```

### NPCs, Antagonistas e Entidades

Usam:

```yaml
type: character
visibility: Mestre
spoiler_level: medium/heavy
gm_secret: true
role: npc
tags:
  - npc
  - character
  - personagem
```

### Origens / B-Sides

Usam tags:

```yaml
tags:
  - story
  - bside
  - origin-story
```

Nas notas de personagem, os vínculos correspondentes foram adicionados como tags de apoio (`origin-vezemir`, `origin-varkh`, `origin-raziel`).

## Validação

Resultado após o lote:

- Frontmatter inválido: `0`
- Wikilinks quebrados: `0`
- Referências de mídia quebradas: `0`
- Notas de `Characters/Individual` fora dos cinco formatos atuais: `0`

## Itens Fora do Escopo

- `Templates/RPG/Quest 1.md` e `Templates/RPG/Rumor 1.md` foram reconhecidos como primeiras notas reais da campanha ainda em rascunho. Não foram tratadas como lixo. A recomendação futura é movê-las para a área operacional correta de quests/rumores quando o lote correspondente começar.
- Mídias órfãs ainda existem, mas não foram apagadas.
- `Home_Mestre.md`, `Estado da Campanha`, templates de Story/B-Side e notas de Earthropo já possuem alterações locais de etapas anteriores e não foram commitados nesta operação.

## Próximo Lote Recomendado

Padronizar `Locations` e `Territories` juntos, porque os personagens agora dependem diretamente de:

- `Nimalis`;
- `Nimalia`;
- `Floresta de Avenor`;
- `Mar da Neblina`;
- `Ruínas de Valthor`;
- `Fortaleza de Gharok`;
- `Campos de Earthropo`;
- `Leth'valora`;
- `Maré Baixa`.
