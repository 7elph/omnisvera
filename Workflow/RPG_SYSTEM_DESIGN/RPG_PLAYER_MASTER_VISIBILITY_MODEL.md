# RPG PLAYER MASTER VISIBILITY MODEL

Modelo de visibilidade para separar informação de mestre e jogador sem duplicar o vault.

Não aplica mudanças. Não compara com Omnisvera.

## 1. Problema operacional

Um vault de RPG precisa conter informações que não devem ser vistas pelos jogadores antes da hora:

- identidade de antagonistas;
- segredos de NPCs;
- mapas completos;
- pistas futuras;
- rumores falsos;
- mecânicas ocultas;
- consequências planejadas;
- handouts ainda não liberados.

Ao mesmo tempo, o mestre precisa consultar tudo rapidamente.

## 2. Estados de visibilidade

Proposta:

| valor | significado |
| --- | --- |
| `Mestre` | informação privada do mestre |
| `Jogadores` | informação já liberada para os jogadores |
| `Público` | informação segura para qualquer visualização |

Campo:

```yaml
visibility: Mestre
```

## 3. Nível de spoiler

```yaml
spoiler_level: none
```

Valores propostos:

- `none`: sem spoiler.
- `light`: revela contexto menor.
- `medium`: revela informação importante.
- `heavy`: revela segredo central.

## 4. Conhecido pelos jogadores

```yaml
player_known: false
```

Uso:

- filtrar dashboards de jogador;
- listar segredos não revelados;
- controlar handouts;
- atualizar após sessão.

## 5. Revelado em

```yaml
revealed_in:
  - Sessão 03
```

Pode apontar para:

- sessão;
- capítulo;
- data;
- evento;
- handout.

## 6. Notas do mestre

```yaml
gm_notes: "Resumo privado ou ponte para seção interna."
```

Recomendação: para textos longos, manter campo curto e seção separada:

```markdown
## GM Notes
```

Essa seção deve ser tratada como conteúdo privado por convenção operacional.

## 7. Handout liberado

```yaml
handout_status: hidden
```

Valores:

- `hidden`
- `ready`
- `revealed`
- `retired`

## 8. Informação mecânica vs narrativa

Campos:

```yaml
mechanical_info: true
narrative_info: true
```

Ou por seção:

```markdown
## Mechanics

## Narrative
```

Uso:

- separar regra de história;
- evitar mostrar estatísticas ocultas;
- preparar encontros.

## 9. Modelo mínimo por nota sensível

```yaml
---
visibility: Mestre
spoiler_level: heavy
player_known: false
revealed_in:
gm_secret:
handout_status:
---
```

## 10. Como funciona com Dataview

Dashboard do mestre:

```dataview
TABLE spoiler_level, location, faction, revealed_in
FROM "/"
WHERE visibility = "Mestre"
AND player_known = false
SORT spoiler_level DESC
```

Dashboard de jogador:

```dataview
TABLE type, location, description
FROM "/"
WHERE visibility = "Jogadores" OR visibility = "Público"
WHERE player_known = true
SORT file.name ASC
```

## 11. Como funciona com DataCards

Handouts prontos para liberar:

```datacards
TABLE handout_image, description FROM #handout
WHERE handout_status = "ready"

// Settings
preset: grid
imageProperty: handout_image
```

Handouts já liberados:

```datacards
TABLE handout_image, revealed_in, description FROM #handout
WHERE handout_status = "revealed"
```

## 12. Sem quebrar o sistema visual

Regras:

- Não usar apenas tags `secret`/`public` como segurança.
- Tags podem ajudar visualmente, mas campos controlam consulta.
- DataCards de jogador devem filtrar `visibility` e `player_known`.
- Se um campo antigo não tem visibilidade, tratar como `Mestre` por segurança até classificação.

## 13. Informação pública

Informação pública é aquela segura para abrir na mesa:

```yaml
visibility: Público
spoiler_level: none
player_known: true
```

## 14. Conhecido pelos jogadores

Informação conhecida não é necessariamente pública. Pode ser conhecida só por um personagem ou grupo. Se isso for necessário:

```yaml
known_by:
  - Vezemir
  - Varkh
```

Esse campo é candidato, não obrigatório.

## 15. Riscos

- Vazamento por dashboard sem filtro.
- Handout marcado como revelado antes da hora.
- Nota com segredo mas `visibility: Público`.
- Campo `gm_secret` exposto em DataCards.
- Tags visuais confundidas com permissão real.

## 16. Regra de segurança

Em dúvida, tratar como `Mestre` até revisão.
