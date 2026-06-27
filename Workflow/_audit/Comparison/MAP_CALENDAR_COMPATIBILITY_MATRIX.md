> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Map and Calendar Compatibility Matrix

Comparação de Leaflet, mapas, Calendarium e calendário entre Disgraceland, modelo RPG desejado e Omnisvera atual.

## Mapas

| item | Disgraceland | RPG desejado | Omnisvera atual | status | risco |
| --- | --- | --- | --- | --- | --- |
| Plugin Leaflet | Ativo e configurado. | Reusar para continente, reino, região, cidade e dungeon. | Ativo. | preservado parcialmente | Configs precisam validação visual. |
| Arquivo de mapa | `TRIBUCIA MAP.md`. | Notas de mapa por escala. | `MAPA DE NIMALIA.md` auditado. | modificado | Links/marcadores podem depender de nomes. |
| Imagem base | `zz_media/Tribucia.png` no legado. | `map_image` ou config Leaflet clara. | Imagem atual auditada, refs precisam validação. | preservado parcialmente | Mover/renomear quebra mapa. |
| Marcadores | 82 no legado. | Marcadores para territórios, locais, ruínas, cidades. | Marcadores auditados no Omnisvera. | preservado parcialmente | Links podem quebrar com renomeação. |
| Grupos de marcadores | Presentes no legado. | Grupos por tipo/escala/visibilidade. | Parcial/desconhecido. | desconhecido | Pode exigir reorganização futura. |
| Links para notas | Dependência crítica. | Requisito central. | Existe, mas precisa validação. | precisa validação visual | Alto se notas forem renomeadas. |
| Mapas secretos | Não formalizado. | Necessário para mestre. | Não contratado. | lacuna | Pode vazar informação. |

## Calendário

| item | Disgraceland | RPG desejado | Omnisvera atual | status | risco |
| --- | --- | --- | --- | --- | --- |
| Plugin Calendarium | Ativo. | Reusar para calendário diegético. | Ativo. | preservado parcialmente | Configs precisam revisão. |
| Arquivo de calendário | `CALENDAR.md`. | Calendário de campanha e timeline. | `TIMELINE.md` e calendário auditados. | modificado | Vínculo com sessão incompleto. |
| Dias/meses | Definidos no legado. | Definir para mundo/campanha. | Parcial/desconhecido. | desconhecido | Pode afetar eventos e datas. |
| Eventos | 22 eventos no legado. | Eventos históricos, futuros e sessões. | Eventos atuais auditados. | preservado parcialmente | Datas podem não mapear sessões. |
| Capítulos/sessões | Capítulos ligados por `chapters` e eventos. | Sessões e arcos. | `chapters` existe; `sessions` ausente. | lacuna | Alto |
| Feriados/religiões | Não central no legado. | Desejado para lore RPG. | Não contratado. | lacuna | Médio |
| Timeline | Narrativa estruturada. | História, campanha e eventos futuros. | `TIMELINE.md` auditado. | suporta parcialmente | Precisa contrato com Calendarium. |

## Riscos técnicos

- Renomear nota usada por marcador Leaflet quebra navegação.
- Renomear imagem base quebra mapa.
- Trocar a estrutura de calendário sem migrar eventos perde timeline.
- Usar mapas com segredo sem campo de visibilidade pode revelar locais.
- `chapters` ainda é a ponte mais segura para aparições; `sessions` precisa ser adicionado sem remoção imediata.

## Requisito futuro mínimo

Antes de migrar mapas/calendário:

1. Exportar lista de marcadores e links.
2. Validar imagem base no Obsidian.
3. Definir se notas de mapa terão `map_image`.
4. Definir como sessões se ligam ao calendário.
5. Definir filtro de visibilidade para marcadores/handouts secretos.
