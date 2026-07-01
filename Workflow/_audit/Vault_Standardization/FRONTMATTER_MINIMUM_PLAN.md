# Omnisvera — Plano C0 de Frontmatter Mínimo

Gerado em: 2026-07-01 20:01

> [!IMPORTANT]
> Este relatório é dry-run. Nenhuma nota foi alterada.
> A futura Fase C1 deve adicionar campos Omnisvera mínimos preservando todos os campos legacy.

## Resumo geral

| métrica | valor |
|---|---:|
| notas Markdown analisadas | 330 |
| notas com frontmatter | 187 |
| notas sem frontmatter | 143 |
| YAML/frontmatter válido | 187 |
| YAML/frontmatter inválido | 0 |
| notas com type | 154 |
| notas sem type | 33 |
| notas com subtype | 25 |
| notas sem subtype | 162 |
| candidatos low | 32 |
| candidatos medium | 64 |
| candidatos high | 22 |
| pulados/skip | 212 |

## Campos mínimos ausentes

| campo | ocorrências |
|---|---:|
| `subtype` | 162 |
| `work_status` | 162 |
| `canon_status` | 162 |
| `requires_review` | 162 |
| `created_by` | 99 |
| `type` | 33 |
| `visibility` | 30 |

## Distribuição de `type` atual

| type | notas |
|---|---:|
| `lore` | 21 |
| `character` | 20 |
| `location` | 20 |
| `audit` | 16 |
| `faction` | 11 |
| `class` | 10 |
| `item` | 10 |
| `race` | 10 |
| `index` | 9 |
| `story` | 8 |
| `map` | 6 |
| `territory` | 5 |
| `quest` | 2 |
| `rumor` | 2 |
| `spell` | 1 |
| `monster` | 1 |
| `ai_npc` | 1 |
| `async_scene` | 1 |

## Distribuição de `subtype` atual

| subtype | notas |
|---|---:|
| `major_npc` | 6 |
| `player_character` | 2 |
| `noble_house` | 2 |
| `guild` | 2 |
| `religious` | 1 |
| `military` | 1 |
| `district` | 1 |
| `wilderness` | 1 |
| `settlement` | 1 |
| `port` | 1 |
| `ruin` | 1 |
| `controlled_npc` | 1 |
| `submitted_scene` | 1 |
| `magic_item` | 1 |
| `shop` | 1 |
| `concept` | 1 |
| `region` | 1 |

## Matriz por arquivo

| Arquivo | Type atual | Type sugerido | Subtype atual | Subtype sugerido | Campos ausentes | Risco | Ação recomendada | Observação |
|---|---|---|---|---|---|---|---|---|
| `Bestiary/INDICE_DE_MONSTROS.md` | `index` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `index` não tem regra de baixo risco. sem type sugerido com segurança. |
| `CALENDAR.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido por tag. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `CAMPANHA/ESTADO_DA_CAMPANHA.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `CAMPANHA/Quests/INDICE_DE_QUESTS.md` | `index` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `index` não tem regra de baixo risco. sem type sugerido com segurança. |
| `CAMPANHA/Quests/Quest 01 - Investigar Avistamentos de Dragões.md` | `quest` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `CAMPANHA/Rumors/INDICE_DE_RUMORES.md` | `index` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `index` não tem regra de baixo risco. sem type sugerido com segurança. |
| `CAMPANHA/Rumors/Rumor 01 - Dragões ao Sul de Nimalia.md` | `rumor` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Characters/Individual/Augustus Terra Decimus.md` | `character` | `character` |  | `major_npc` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag npc-importante. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Dragão de Colar Dourado.md` | `character` | `character` |  | `creature` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag criatura/monstro em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Elarion Vaelthor.md` | `character` | `character` | `major_npc` | `major_npc` |  | skip | no_action | inferido pela pasta Characters. tag npc-importante. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/General Cassian Valerius.md` | `character` | `character` | `major_npc` | `major_npc` |  | skip | no_action | inferido pela pasta Characters. tag npc-importante. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/Kaelen, o Flagelo.md` | `character` | `character` |  | `antagonist` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag antagonista em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Lorde Malakar.md` | `character` | `character` |  | `antagonist` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag antagonista em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Mestre Odran Veyl.md` | `character` | `character` | `major_npc` | `major_npc` |  | skip | no_action | inferido pela pasta Characters. tag npc-importante. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/Mira Valen.md` | `character` | `character` | `major_npc` | `major_npc` |  | skip | no_action | inferido pela pasta Characters. tag npc-importante. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/Padre Oric.md` | `character` | `character` | `major_npc` | `major_npc` |  | skip | no_action | inferido pela pasta Characters. tag npc-importante. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/Raziel.md` | `character` | `character` |  | `player_character` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag de personagem jogador. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Unidade DORN-7.md` | `character` | `character` |  | `creature` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag criatura/monstro em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Vandor, o Senhor das Bestas.md` | `character` | `character` |  | `antagonist` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Characters. tag antagonista em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Characters/Individual/Varkh Nimalis.md` | `character` | `character` | `player_character` | `player_character` |  | skip | no_action | inferido pela pasta Characters. tag de personagem jogador. frontmatter já contém campos mínimos auditados. |
| `Characters/Individual/Vezemir.md` | `character` | `character` | `player_character` | `player_character` |  | skip | no_action | inferido pela pasta Characters. tag de personagem jogador. frontmatter já contém campos mínimos auditados. |
| `Classes/Alquimista.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Classes/Clérigo.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Classes/Guerreiro.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Classes/INDICE_DE_CLASSES.md` | `index` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Classes/Ladrão.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Classes/Mago.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Classes/Vampiro.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Classes. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `CULTURE.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido por tag. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `EARTHROPO/00 - As Crônicas de Névoa de Sangue.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `EARTHROPO/00 - O Bastardo de Ferro.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `EARTHROPO/00 - O Corvo da Maré Baixa.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `EARTHROPO/01 - Ecos do Mundo Perdido.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `EARTHROPO/EARTHROPO.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido por tag. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `ECONOMY.md` |  |  |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Factions/Clã Sanguinallis.md` | `faction` | `faction` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Factions. subtype de facção precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Factions/Conclave dos Errantes.md` | `faction` | `faction` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Factions. subtype de facção precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Factions/Coroa de Nimalia.md` | `faction` | `faction` | `noble_house` | `noble_house` |  | skip | no_action | inferido pela pasta Factions. nobreza/casas nobres detectadas. frontmatter já contém campos mínimos auditados. |
| `Factions/Culto dos Sussurrantes.md` | `faction` | `faction` | `religious` | `religious` |  | skip | no_action | inferido pela pasta Factions. culto detectado; classificado como facção religiosa. frontmatter já contém campos mínimos auditados. |
| `Factions/Guarda Real de Nimalia.md` | `faction` | `faction` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Factions. subtype de facção precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Factions/Guardiões do Véu Cinzento.md` | `faction` | `faction` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Factions. subtype de facção precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Factions/Guilda dos Mercadores.md` | `faction` | `faction` | `guild` | `guild` |  | skip | no_action | inferido pela pasta Factions. guilda detectada. frontmatter já contém campos mínimos auditados. |
| `Factions/Nobreza de Nimalia.md` | `faction` | `faction` | `noble_house` | `noble_house` |  | skip | no_action | inferido pela pasta Factions. nobreza/casas nobres detectadas. frontmatter já contém campos mínimos auditados. |
| `Factions/Rede de Falsificadores de Maré Baixa.md` | `faction` | `faction` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Factions. subtype de facção precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Factions/Sentinelas de Leth'valora.md` | `faction` | `faction` | `military` | `military` |  | skip | no_action | inferido pela pasta Factions. força militar/guarda detectada. frontmatter já contém campos mínimos auditados. |
| `Home.md` |  |  |  |  | `type`, `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Home_Mestre.md` |  |  |  |  | `type`, `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Items/Adagas de Espectro Fantasma.md` | `item` | `item` |  | `artifact` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. artefato detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Items/Caderninho de Vozes.md` | `item` | `item` |  | `document` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. documento detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Items/Grisalma.md` | `item` | `item` |  | `artifact` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. artefato detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Items/INDICE_DE_ITENS.md` | `index` | `item` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido pela pasta Items. subtype de item precisa revisão. type atual conflita com sugestão; precisa revisão humana. |
| `Items/Manto Primordial do Ancião.md` | `item` | `item` |  | `artifact` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. artefato detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Items/Muralha de Dorn.md` | `item` | `item` |  | `artifact` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. artefato detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Items/Máscara de Médico da Peste de Varkh.md` | `item` | `item` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Items. subtype de item precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Items/O Frasco Afogado.md` | `item` | `location` |  | `shop` | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | Reclassificação futura: é a loja de alquimia do Mestre Odran em Maré Baixa, não item portátil. Reclassificação futura: é a loja de alquimia do Mestre Odran em Maré Baixa, não item portátil. type atual conflita com sugestão; precisa revisão humana. |
| `Items/O Medalhão.md` | `item` | `item` |  | `artifact` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Items. artefato detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `LATEST_NEWS.md` |  |  |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Locations/Antiga Estrada Esquecida.md` | `location` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Locations/Bairro dos Anões.md` | `location` | `location` |  | `district` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. bairro/distrito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Bairro dos Dragonborns.md` | `location` | `location` |  | `district` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. bairro/distrito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Bairro dos Elfos.md` | `location` | `location` |  | `district` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. bairro/distrito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Bairro dos Forasteiros.md` | `location` | `location` | `district` | `district` |  | skip | no_action | inferido pela pasta Locations. bairro/distrito detectado. frontmatter já contém campos mínimos auditados. |
| `Locations/Bairro dos Humanos.md` | `location` | `location` |  | `district` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. bairro/distrito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Bairro Nobre.md` | `location` | `location` |  | `district` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. bairro/distrito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Bosque Sussurrante.md` | `location` | `location` | `wilderness` | `wilderness` |  | skip | no_action | inferido pela pasta Locations. área selvagem detectada. frontmatter já contém campos mínimos auditados. |
| `Locations/Casa da Moeda de Nimalia.md` | `location` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Locations/Distrito Comercial.md` | `location` | `location` |  | `shop` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. loja/comércio detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Fortaleza Abandonada de Avenor.md` | `location` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Locations/Fortaleza de Gharok.md` | `location` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Locations/INDICE_DE_LOCAIS.md` | `index` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. type atual conflita com sugestão; precisa revisão humana. |
| `Locations/Leth'valora.md` | `location` | `location` | `settlement` | `settlement` |  | skip | no_action | inferido pela pasta Locations. assentamento detectado. frontmatter já contém campos mínimos auditados. |
| `Locations/Maré Baixa.md` | `location` | `location` | `port` | `port` |  | skip | no_action | inferido pela pasta Locations. porto detectado. frontmatter já contém campos mínimos auditados. |
| `Locations/Mercado Central.md` | `location` | `location` |  | `shop` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. loja/comércio detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Nimalis.md` | `location` | `location` |  | `city` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. capital/cidade detectada; plano futuro: `role: capital`; `territory: [[Nimalia]]`. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Porto de Nimalia.md` | `location` | `location` |  | `port` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Locations. porto detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Locations/Ruínas de Valthor.md` | `location` | `location` | `ruin` | `ruin` |  | skip | no_action | inferido pela pasta Locations. ruína detectada. frontmatter já contém campos mínimos auditados. |
| `Locations/Vale Dourado.md` | `location` | `location` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Locations. subtype de local precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Ancião Primordial.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Criadores.md` | `lore` | `lore` |  | `cosmology` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Lore. cosmologia detectada. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Lore/Eclipse de Obsidiana.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Guardiões do Véu Cinzento.md` | `lore` | `lore` |  | `mystery` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Lore. mistério detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Lore/O Fraturamento.md` | `lore` | `lore` |  | `cosmology` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Lore. cosmologia detectada. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Lore/Remédios Falsos de Maré Baixa.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Sangue Antigo.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Vampiro Sanguinallis.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Lore/Véu Cinzento.md` | `lore` | `lore` |  | `mystery` | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | low | plan_add_missing_fields | inferido pela pasta Lore. mistério detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `LORE.md` |  |  |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `` não tem regra de baixo risco. sem type sugerido com segurança. |
| `MAPA DE EARTHROPO.md` | `map` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag/NoteIcon. subtype para `territory` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `MAPA DE NIMALIA.md` | `map` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag/NoteIcon. subtype para `territory` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `MAPA DE NIMALIS.md` | `map` |  |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `map` não tem regra de baixo risco. sem type sugerido com segurança. |
| `NOTES.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `OMNISVERA.md` |  | `lore` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido por tag. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Races/Antropo.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Anão.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Dragonborn.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Elfo.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Halfling.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Humano.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/INDICE_DE_RACAS.md` | `index` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Races/Kenku.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Meio-Elfo.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Races/Vampiro.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Races. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Religion/Caminho dos Errantes.md` | `lore` | `religion` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido pela pasta Religion. subtype para `religion` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Religion/Fé dos Antigos.md` | `lore` | `religion` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido pela pasta Religion. subtype para `religion` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Religion/Igreja das Chamas.md` | `lore` | `religion` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido pela pasta Religion. subtype para `religion` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Religion/RELIGION.md` | `lore` | `religion` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido pela pasta Religion. subtype para `religion` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Rules/Spells/INDICE_DE_MAGIAS.md` | `index` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `index` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Templates/Characters/Antagonista.md` | `character` | `character` |  | `antagonist` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de personagem. tag antagonista em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/Characters/Criatura.md` | `character` | `character` |  | `creature` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de personagem. tag criatura/monstro em contexto de personagem. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/Characters/NPC Importante.md` | `character` | `character` |  | `major_npc` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de personagem. tag npc-importante. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/Characters/NPC Menor.md` | `character` | `character` |  | `minor_npc` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de personagem. tag npc-menor. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/Characters/Personagem Jogador.md` | `character` | `character` |  | `player_character` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de personagem. tag de personagem jogador. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/Classes/Arquétipo Narrativo.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de classe. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Templates/Classes/Classe Base.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de classe. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Templates/Classes/Especialização.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de classe. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/B-Side.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Templates/RPG/Classe.md` | `class` | `class` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de classe. subtype para `class` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Cultura.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Fenômeno.md` | `lore` | `lore` |  | `concept` | `subtype`, `work_status`, `canon_status`, `requires_review` | low | plan_add_missing_fields | inferido por tags de template de lore. fenômeno/conceito detectado. campos mínimos ausentes podem ser adicionados em lote futuro. |
| `Templates/RPG/Item.md` | `item` | `item` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de item. subtype de item precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Lore.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Magia.md` | `spell` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `spell` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Templates/RPG/Monstro.md` | `monster` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `monster` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Templates/RPG/Quest.md` | `quest` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `quest` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Templates/RPG/Raça.md` | `race` | `race` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de raça. subtype para `race` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Religião.md` | `lore` | `lore` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido por tags de template de lore. subtype de lore precisa revisão. subtype ausente sem inferência de baixo risco. |
| `Templates/RPG/Rumor.md` | `rumor` |  |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | não inferido com segurança. subtype para `rumor` não tem regra de baixo risco. sem type sugerido com segurança. |
| `Templates/RPG/Story.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Templates/TEMPLATE - AI NPC.md` | `ai_npc` | `ai_npc` | `controlled_npc` |  |  | skip | no_action | inferido pelo template-base AI NPC. subtype para `ai_npc` não tem regra de baixo risco. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Async Scene.md` | `async_scene` | `async_scene` | `submitted_scene` |  |  | skip | no_action | inferido pelo template-base Async Scene. subtype para `async_scene` não tem regra de baixo risco. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Character.md` | `character` | `character` | `major_npc` |  |  | skip | no_action | inferido por tags de template de personagem. subtype de personagem precisa revisão. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Faction.md` | `faction` | `faction` | `guild` |  |  | skip | no_action | inferido por tags de template de facção. subtype de facção precisa revisão. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Item.md` | `item` | `item` | `magic_item` | `magic_item` |  | skip | no_action | inferido por tags de template de item. NoteIcon magicitem. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Location.md` | `location` | `location` | `shop` |  |  | skip | no_action | inferido por tags de template de local. subtype de local precisa revisão. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Lore.md` | `lore` | `lore` | `concept` |  |  | skip | no_action | inferido por tags de template de lore. subtype de lore precisa revisão. frontmatter já contém campos mínimos auditados. |
| `Templates/TEMPLATE - Territory.md` | `territory` | `territory` | `region` |  |  | skip | no_action | inferido por tag/NoteIcon. subtype para `territory` não tem regra de baixo risco. frontmatter já contém campos mínimos auditados. |
| `Territories/Campos de Earthropo.md` | `territory` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | medium | review_before_apply | inferido pela pasta Territories. subtype para `territory` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Territories/Floresta de Avenor.md` | `territory` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Territories. subtype para `territory` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Territories/INDICE_DE_TERRITORIOS.md` | `index` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | high | review_before_apply | inferido pela pasta Territories. subtype para `territory` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Territories/Mar da Neblina.md` | `territory` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Territories. subtype para `territory` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `Territories/Nimalia.md` | `territory` | `territory` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Territories. subtype para `territory` não tem regra de baixo risco. subtype ausente sem inferência de baixo risco. |
| `TIMELINE.md` | `story` | `session` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | high | review_before_apply | inferido por tag narrativa; revisar porque `story` é mantida como ponte. subtype para `session` não tem regra de baixo risco. type atual conflita com sugestão; precisa revisão humana. |
| `Workflow/_archive/legacy_removal/DISGRACELAND_REMOVAL_SUMMARY.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_archive/obsolete_review/Home_Jogadores_ARCHIVED.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Character_Standardization/CHARACTERS_INDIVIDUAL_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Character_Structure/CHARACTER_ALIGNMENT_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Class_Rules_Standardization/CLASSES_AND_RULES_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Class_Rules_Standardization/RULES_FOLDER_CONSOLIDATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Cleanup/ARCHIVED_CONTENT_LOG.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Cleanup/BROKEN_LINKS_AND_MEDIA_REFERENCES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Cleanup/DELETION_CANDIDATES_CURRENT_REVIEW.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Cleanup/DO_NOT_DELETE_REGISTER.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Cleanup/HOME_DASHBOARD_CONSOLIDATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Cleanup/OBSOLETE_CONTENT_CANDIDATES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Cleanup/VAULT_CLEANUP_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/DATAVIEW_DATACARDS_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/DISGRACELAND_TO_OMNISVERA_GAP_ANALYSIS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/FRONTMATTER_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/MAP_CALENDAR_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/MEDIA_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/MIGRATION_DECISION_REGISTER.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/PLAYER_MASTER_VISIBILITY_GAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/RPG_MODEL_TO_OMNISVERA_GAP_ANALYSIS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/SAFE_MIGRATION_ROADMAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/TEMPLATE_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/TRIPLE_COMPARISON_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Comparison/VISUAL_TAG_COMPATIBILITY_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Dashboard_Standardization/MASTER_HOME_AND_CAMPAIGN_STATE_ALIGNMENT_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Dashboard_Standardization/PLAYER_HOME_OPERATIONAL_REVIEW.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Decision_Packet/BLOCKERS_BEFORE_COMPATIBILITY_LAYER.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Decision_Packet/DECISION_SUMMARY_TABLE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Decision_Packet/SAGE_DECISION_PACKET.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Decision_Packet/TECHNICAL_DEFAULT_RECOMMENDATIONS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Disgraceland_Removal/DISGRACELAND_OPERATIONAL_REMOVAL_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Earthropo_Standardization/EARTHROPO_STRUCTURE_STANDARDIZATION_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Faction_Standardization/FACTIONS_ACTIVE_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Faction_Structure/FACTION_STANDARDIZATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Folder_Migration/PTBR_FOLDER_MIGRATION_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Geography_Standardization/GEOGRAPHY_PLAYABLE_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Geography_Structure/GEOGRAPHY_STANDARDIZATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Healthcheck/LOCAL_PENDING_CHANGES_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Healthcheck/STRUCTURE_ALIGNMENT_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Healthcheck/VALIDATION_SUMMARY.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Healthcheck/YAML_FRONTMATTER_HEALTHCHECK.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Index_Standardization/OPERATIONAL_INDEX_REVIEW.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Item_Standardization/ITEMS_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Item_Structure/ITEM_STANDARDIZATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Leaflet_Map_Diagnostics/backups/MAPA DE EARTHROPO.before-map-reset.md` | `map` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Leaflet_Map_Diagnostics/backups/MAPA DE NIMALIA.before-map-reset.md` | `map` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Leaflet_Map_Diagnostics/backups/MAPA DE NIMALIS.before-map-reset.md` | `map` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Location_Standardization/LOCATIONS_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Lore_Standardization/LORE_AND_PHENOMENA_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Lore_Structure/LORE_CULTURE_STORY_FORMAT_STAGE_1.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Lore_Structure/LORE_CULTURE_STORY_FORMAT_STAGE_2.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Lore_Structure/LORE_PILLARS_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Media_Mapping/OPERATIONAL_DATACARDS_AND_MEDIA_FIX_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_CHARACTER_STRUCTURE_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_CSS_SNIPPET_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_DASHBOARD_MAP_SYSTEMS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_DATAVIEW_AND_DATACARDS_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_FACTION_TERRITORY_LOCATION_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_FRONTMATTER_FIELD_MATRIX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_MEDIA_REFERENCE_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_MIGRATION_RISK_REGISTER.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_OBSIDIAN_DEPENDENCY_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_PLUGIN_CONFIG_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_TEMPLATE_STRUCTURE_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Omnisvera/OMNISVERA_VISUAL_TAGS_AND_SUPERCHARGED_LINKS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Operational_Cleanup/CULTURE_RELIGION_CALENDAR_TIMELINE_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Operational_Cleanup/DISGRACELAND_PHYSICAL_REMOVAL_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Operational_Cleanup/NEWLINE_AND_FRONTMATTER_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Operational_Cleanup/OPERATIONAL_CLEANUP_VALIDATION.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Operational_Cleanup/WORKFLOW_CLEANUP_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Pending_Review/VAULT_PENDING_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Pending_Review/VAULT_STANDARDIZATION_BACKLOG.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Pilot_Migration/PILOT_MIGRATION_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Pilot_Migration/PILOT_READINESS_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Plugin_Migration/DATAVIEW_DATACARDS_TEMPLATE_MIGRATION_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Plugin_Migration/PLUGIN_TAG_MIGRATION_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/FRONTMATTER_NORMALIZATION_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/HOME_VALIDATION_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/NEXT_BATCH_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/PILOT_NOTES_VALIDATION.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/POST_PILOT_FIXES_VALIDATION.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Post_Pilot_Fixes/TEMPLATE_TABLE_USE_UPDATE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Quest_Rumor_Standardization/QUESTS_AND_RUMORS_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Religion_Structure/RELIGION_STANDARDIZATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Story_Standardization/STORY_AND_BSIDE_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Taxonomy_Alignment/LEGACY_STANDARD_DOCS_ALIGNMENT_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Taxonomy_Alignment/TAXONOMY_ALIGNMENT_VALIDATION.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Taxonomy_Alignment/TEMPLATE_ALIGNMENT_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Territory_Map_Standardization/TERRITORIES_AND_MAPS_STANDARDIZATION_REPORT.md` | `audit` | `workflow` |  |  | `subtype`, `work_status`, `canon_status`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/_audit/Urban_Structure/NIMALIS_URBAN_STANDARDIZATION_REVIEW.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_APPLIED_C1A.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_APPLIED_C1B_LOCATIONS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_APPLIED_C1C_FACTIONS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/FRONTMATTER_MINIMUM_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/LEAFLET_ID_ALIGNMENT_FIX_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/LEAFLET_IMAGE_LOAD_RESET_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/LEAFLET_MAP_DIAGNOSTIC_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/LEAFLET_MAP_FIX_REPORT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_APPLIED.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_IMPACT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/TAG_NORMALIZATION_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/_audit/Vault_Standardization/VAULT_STANDARDIZATION_AUDIT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CHANGELOG.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/00_README_FOR_AI.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/01_CANON_SUMMARY.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/02_ENTITY_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/03_OPEN_DECISIONS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/04_MEDIA_RULES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/06_TASK_TEMPLATES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/07_VALIDATION_CHECKLIST.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/08_DO_NOT_INVENT.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_CONTEXT/09_SESSION_STATE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_REVIEW_CHECKLIST.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/AI_TASK_TEMPLATE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/ASSISTANT_HANDOFF.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/CANON.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/CHARACTER_SCHEMA.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Charts.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/COMPATIBILITY_LAYER/COMPATIBILITY_LAYER_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/DASHBOARD_COMPATIBILITY_RULES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/DATACARDS_COMPATIBILITY_RULES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/DATAVIEW_COMPATIBILITY_RULES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/FRONTMATTER_COMPATIBILITY_SCHEMA.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/MEDIA_FIELD_COMPATIBILITY_MODEL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/PILOT_MIGRATION_PLAN.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/TAG_COMPATIBILITY_MAP.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/TEMPLATE_COMPATIBILITY_GUIDE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/COMPATIBILITY_LAYER/VISIBILITY_COMPATIBILITY_MODEL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/DEVIN_OPERATING_PROTOCOL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Format Audit Report.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/GEOGRAPHY.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/Legacy/Disgraceland/.trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 01.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Disgraceland/.trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 02.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Disgraceland/.trash/!Ep01 - The Black Marauder/Act 01/A1-Scene 03.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Call Out Box.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Flavor.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - GM Direction.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Left Section.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Magic Item.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Read Aloud.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out - Right Section.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Legacy/Disgraceland/.trash/Call Out Boxes/Call Out Boxes.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Disgraceland/.trash/City Forces/Blueforce.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Legacy - Archive Index.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Clérigo.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Homem de Armas.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Ladrão.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/Legacy/Old Dragon anterior/Legacy - Old Dragon anterior - Mago.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | skip | no_action | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. histórico/auditoria/legacy; não migrar automaticamente. |
| `Workflow/LOCAL_ASSISTANT_PROTOCOL.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/LOCAL_ENVIRONMENT_CHECKLIST.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/LOCAL_TOOLING.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/MIGRATION_LEDGER.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/MISSING_NOTES_BACKLOG.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/OMNISVERA_CHARACTER_TEMPLATE_GUIDE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_CLASS_STANDARD.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_FRONTMATTER_SCHEMA.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_LOCATION_TERRITORY_GUIDE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_NOTE_STANDARD.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_SYSTEM_TAXONOMY_DECISIONS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_TAG_BRIDGE_GUIDE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_VAULT_STANDARD.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OMNISVERA_VISIBILITY_AND_SPOILER_GUIDE.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/OUTLINES.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/Property Key Dashboard.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/README.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Reports/latest_vault_audit.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_DATAVIEW_DATACARDS_REQUIREMENTS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_FRONTMATTER_PROPOSAL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_MAP_AND_CALENDAR_REQUIREMENTS.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_MEDIA_AND_HANDOUT_MODEL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_MIGRATION_PRINCIPLES.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_PLAYER_MASTER_VISIBILITY_MODEL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_SYSTEM_INDEX.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_TEMPLATE_TAXONOMY.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_VAULT_OPERATING_MODEL.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RPG_SYSTEM_DESIGN/RPG_VISUAL_TAG_SYSTEM.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/RULES_SOURCES.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/Runtime Audit Report.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/Scratch Notes.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |
| `Workflow/Templates/Character Template.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Templates/Player Character Template.md` |  |  |  |  |  | skip | no_action | frontmatter ausente |
| `Workflow/Vault Report.md` |  | `workflow` |  |  | `type`, `subtype`, `work_status`, `canon_status`, `visibility`, `created_by`, `requires_review` | medium | review_before_apply | inferido pela pasta Workflow/documentação. subtype para `workflow` não tem regra de baixo risco. documento/sessão requer decisão de padrão antes de lote. |

## Casos especiais

- `Items/O Frasco Afogado.md`: marcar como reclassificação futura para `location/shop`; não aplicar como item.
- `Factions/Culto dos Sussurrantes.md`: manter como `faction`; não receber `character` automaticamente por causa da tag `antagonista`.
- `Workflow/_audit/*`: tratado como histórico/auditoria; não migrar automaticamente.
- `.obsidian/plugins/obsidian-leaflet-plugin/data.json`: ignorado; não é Markdown e está fora do escopo.

## Recomendação para Fase C1

Aplicar primeiro apenas os casos `low`, em lote pequeno, adicionando campos ausentes sem remover campos legacy.
Casos `medium` e `high` precisam revisão do Sage antes de qualquer alteração.
