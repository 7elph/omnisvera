# Omnisvera — Vocabulário Técnico / Fonte da Verdade

> [!IMPORTANT]
> Este arquivo é a fonte da verdade técnica revisada pelo Sage.
> Ele deve orientar migração de plugins, tags, templates, Dataview, DataCards, pastas e notas.
>
> Disgraceland não é mais conteúdo operacional do vault.
> Apenas o motor funcional herdado será reaproveitado.

## Princípios aprovados

| área | decisão aprovada |
|---|---|
| Idioma visual | Português BR. |
| Tags técnicas | Minúsculas, sem acento, com hífen. |
| Campos YAML herdados | Manter em inglês quando já existirem. |
| Campos YAML novos | Preferir inglês técnico, salvo decisão posterior em contrário. |
| Pastas | Migrar para português BR somente depois de plano de impacto e atualização de links/configurações. |
| Disgraceland | Não é conteúdo operacional. Apenas a lógica funcional pode ser reaproveitada. |
| `thumbnail` | Manter para cards/listagens/DataCards. |
| `cover` | Manter separado de `thumbnail`. |
| `sessions` | Remover/não usar em novos padrões. |
| `chapters` | Manter e reinterpretar como capítulos/seções/partes da campanha RPG. |
| Plugins | Alterar configurações fonte quando a mudança for segura; não apenas notas. |
| Tags antigas | Substituir depois de auditar plugins e consultas. |
| `tags` | Não remover globalmente; usar como infraestrutura técnica, não como campo narrativo principal. |

## Mapa inicial Disgraceland → Omnisvera

| tag legada | decisão Omnisvera | status | observação |
|---|---|---|---|
| `loyalist` | `coroa-de-nimalia` | aprovado | Migração segura para cor/facção ligada à Coroa. |
| `rancher` | `guilda-dos-mercadores` | aprovado | Migração segura para agrupamento mercantil. |
| `pirate` | `conclave-dos-errantes` | aprovado | Migração segura para agrupamento errante/aventureiro. |
| `widow` | `guardioes-do-veu-cinzento` | aprovado | Migração segura para facção/culto do Véu Cinzento. |
| `third` | `sentinelas-de-lethvalora` | aprovado | Usar a facção existente `[[Factions/Sentinelas de Leth'valora|Sentinelas de Leth'valora]]`; não usar `terceira-fileira`. |
| `murray` | `nobreza-de-nimalia` | aprovado | Usar como ponte técnica para a nobreza do Reino de Nimalia. |
| `steeltown` | `nimalia` | aprovado com ressalva | `nimalia` não deve representar tudo se `nimalis` for capital; revisar contexto. |
| `water` | `mar-da-neblina` | aprovado | Migração segura para território/tema marítimo. |
| `individual` | `personagem` | aprovado | Migração segura para categoria visual de personagens. |
| `lore` | `lore` | aprovado | Manter. |
| `religion` | `religiao` | aprovado | Migrar para português técnico sem acento. |
| `territory` | `territorio` | aprovado | Migrar para português técnico sem acento. |
| `story` | `story` | aprovado temporariamente | Manter como eixo de história/capítulo/campanha; não virar `sessao` e não criar `sessions`. |

## Facções fora da migração oficial

Estas facções não entram na migração oficial como conteúdo operacional.

| item | decisão |
|---|---|
| `resistencia-de-libervale` | Remover da migração oficial. Se existir, arquivar/revisar, não apagar direto. |
| `tripulacao-de-libervale` | Remover da migração oficial. Se existir, arquivar/revisar, não apagar direto. |
| `igreja-de-mirella` | Remover da migração oficial. Se existir, arquivar/revisar, não apagar direto. |
| `palavra-da-estrela-nascida-morta` | Remover da migração oficial. Se existir, arquivar/revisar, não apagar direto. |

Se uma nota atual usar esses nomes, o tratamento seguro é:

```yaml
status: Arquivado
visibility: Mestre
gm_secret: true
```

ou mover para revisão, conforme contexto.

## Territórios fora da migração oficial

| item | decisão |
|---|---|
| `eryndor` | Remover da migração oficial; provável substituição por Earthropo conforme contexto. |
| `libervale` | Remover da migração oficial; classificar antes de arquivar. |
| `ashmoor` | Remover da migração oficial; classificar antes de arquivar. |
| `terras-de-morghul` | Remover da migração oficial; classificar antes de arquivar. |
| `montanhas-do-dragao` | Remover da migração oficial; classificar antes de arquivar. |

Classificações permitidas para notas atuais com esses nomes:

- `REMOVER`;
- `ARQUIVAR`;
- `FUNDIR`;
- `SUBSTITUIR`;
- `NEEDS_SAGE_REVIEW`.

## Geografia e termos estruturais

| termo | decisão |
|---|---|
| `earthropo` | Continente. |
| `reino-de-nimalia` | Território/reino. |
| `nimalia` | Contexto/reino, mas precisa revisão para não conflitar com capital. |
| `nimalis` | Capital/localização a criar/considerar. |
| `vale-dourado` | Localização, não território. |
| `porto-de-zevran` | Revisar; possível `porto-de-nimalis`. |
| `farmland` | Virar equivalente de vila remota, não vale agrícola. |
| `wasteland` | Virar ruínas. |
| `region` | Revisar em relação a `location`. |
| `district` | Revisar em relação a escala urbana/local. |

## Campos YAML

### Remover ou não usar em novos padrões

| campo | decisão |
|---|---|
| `sessions` | Não usar. Preservar apenas se existir legado, mas não criar novo padrão. |
| `player_known` | Não usar em novos padrões. |
| `subtype` | Não usar em novos padrões. |
| `portrait` | Não usar em novos padrões. |
| `token_image` | Não usar em novos padrões. |
| `map_image` | Não usar em novos padrões. |
| `handout_image` | Não usar em novos padrões. |
| `life_status` | Não usar em novos padrões. |
| `old_dragon_class` | Não usar em novos padrões. |
| `old_dragon_race` | Não usar em novos padrões. |
| `requires_review` | Não usar em novos padrões. |
| `work_status` | Não usar em novos padrões. |
| `canon_status` | Não usar em novos padrões. |
| `source` | Não usar em novos padrões. |
| `state` | Não usar em novos padrões. |

### Manter ou adicionar

| campo | decisão |
|---|---|
| `visibility` | Campo de separação mestre/jogador. |
| `spoiler_level` | Campo de risco de revelação. |
| `gm_secret` | Campo booleano para segredo do mestre. |
| `revealed_in` | Campo para registrar quando algo foi revelado. |
| `level` | Permitido para RPG/mecânica. |
| `danger_level` | Permitido para locais, monstros, quests e facções. |
| `hooks` | Permitido para ganchos. |
| `rumors` | Permitido para rumores. |
| `created_by` | Permitido para autoria/controle de origem. |
| `campaign_status` | Permitido para status operacional de campanha. |
| `quest_status` | Permitido para quests. |
| `handout_status` | Permitido, mas handouts não serão criados agora como categoria principal. |
| `thumbnail` | Preservar. |
| `cover` | Preservar. |
| `status` | Preservar como campo herdado/operacional. |
| `chapters` | Preservar e reinterpretar como capítulos/seções/partes da campanha. |
| `tags` | Preservar como infraestrutura técnica. |

### Revisar antes de padronizar

| campo | motivo |
|---|---|
| `type` | Útil, mas precisa conviver com tags técnicas. |
| `population` | Útil para territórios/assentamentos; revisar formato. |
| `Government` | Herdado com maiúscula; revisar se mantém ou vira campo técnico novo. |
| `politics` | Revisar utilidade real. |
| `region` | Revisar relação com `location` e `territory`. |
| `district` | Revisar escala e uso em consultas. |
| `chapter` / `chapters` | Consolidar sem quebrar histórico. |
| `cssclass` / `cssclasses` | Revisar uso visual antes de alterar. |
| `tag` / `tags` | Converter singular para compatibilidade somente se seguro. |

## Categorias RPG aprovadas agora

| categoria | criar agora? | pasta operacional inicial |
|---|---:|---|
| Raças | sim | `Races` |
| Classes | sim | `Classes` |
| Magias | sim | `Rules/Spells` |
| Itens | sim | `Items` |
| Monstros | sim | `Bestiary` |
| Quests | sim | `CAMPANHA/Quests` |
| Rumores | sim | `CAMPANHA/Rumors` |
| Handouts | não agora | planejar depois. |
| Encontros | não agora | planejar depois. |

## Regra de copyright para material de regras

Notas de raças, classes, magias, monstros e regras devem conter estrutura, índice e resumo próprio.

Não reproduzir conteúdo integral ou trechos extensos de livros do Old Dragon ou qualquer material protegido.
