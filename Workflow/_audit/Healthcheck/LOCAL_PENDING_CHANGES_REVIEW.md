# Local Pending Changes Review

Data: 2026-06-27

Objetivo: classificar pendências locais antigas antes de continuar o piloto de migração.

## Estado encontrado

`git status --short` indicou pendências locais fora do healthcheck:

| arquivo/pasta | estado | tema |
| --- | --- | --- |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | modificado | documentação de dashboard/classes |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` | modificado | padrão de mídia |
| `Workflow/OMNISVERA_CLASS_STANDARD.md` | não rastreado | padrão de classes/Old Dragon |
| `Templates/Classes/` | não rastreado | templates de classes |

## Classificação

| item | classificação | decisão/recomendação |
| --- | --- | --- |
| `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | `NEEDS_SAGE_REVIEW` / `MOVER_PARA_OUTRO_DOC` | As alterações remanescentes adicionam seções sobre índice/consultas de Classes. Não devem ser misturadas com Homes ou healthcheck. Recomendo revisar depois e decidir se ficam neste documento ou se migram para o padrão de Classes. |
| `Workflow/OMNISVERA_MEDIA_STANDARD.md` | `COMMIT_SEPARADO_AGORA` | A alteração adiciona padrão de imagens de Classe e está alinhada com a camada de compatibilidade de mídia. Pode virar commit documental separado. |
| `Workflow/OMNISVERA_CLASS_STANDARD.md` | `COMMIT_SEPARADO_AGORA` | Documento novo de padrão de Classes/Old Dragon. Pode virar commit documental separado se mantido como referência técnica, sem aplicar templates em massa. |
| `Templates/Classes/` | `COMMIT_SEPARADO_AGORA` | Templates novos de Classe Base, Especialização e Arquétipo Narrativo. Podem virar commit separado de templates, sem aplicar nas notas existentes. |

## Observações técnicas

### `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`

Diferença remanescente não commitada:

- seção `Índice de Classes`;
- consulta para Classes por `campaign_status`;
- consulta para Classes por `rules_status`;
- consulta de personagens por Classe;
- consulta de especializações por Classe-base;
- consulta de Classes pendentes de revisão.

Risco: baixo como documentação, mas médio como arquitetura porque mistura dashboard geral com padrão de Classes. Por isso ficou fora dos commits automáticos desta etapa.

### `Workflow/OMNISVERA_MEDIA_STANDARD.md`

Diferença remanescente:

- adiciona `zz_media/classes/`;
- define `thumbnail`, `portrait` e `cover` para classes;
- não move mídia;
- não apaga mídia;
- não altera notas existentes.

Risco: baixo.

### `Workflow/OMNISVERA_CLASS_STANDARD.md`

Documento técnico novo:

- define princípios para notas de Classe;
- separa classe de facção/cargo social;
- propõe campos `work_status`, `rules_status`, `campaign_status`, `canon_status`;
- mantém Old Dragon como referência mecânica;
- não aplica mudanças em massa.

Risco: médio se virar obrigatório antes do piloto. Seguro como documento de referência.

### `Templates/Classes/`

Arquivos encontrados:

- `Templates/Classes/Arquétipo Narrativo.md`;
- `Templates/Classes/Classe Base.md`;
- `Templates/Classes/Especialização.md`.

Risco: baixo enquanto forem apenas templates novos e não forem aplicados em massa.

## Decisão operacional

Seguro commitar separadamente:

1. `Workflow/OMNISVERA_MEDIA_STANDARD.md`;
2. `Workflow/OMNISVERA_CLASS_STANDARD.md`;
3. `Templates/Classes/`.

Não seguro commitar automaticamente:

- alterações remanescentes em `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md`.

Motivo: precisam decisão se pertencem ao documento de dashboard ou ao sistema de Classes.
