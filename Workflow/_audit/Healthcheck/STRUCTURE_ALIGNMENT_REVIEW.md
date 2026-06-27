# Structure Alignment Review

Data: 2026-06-27

Objetivo: comparar o estado estrutural atual do Omnisvera com os contratos técnicos do Disgraceland, o modelo RPG planejado, o pacote de decisões e a camada de compatibilidade.

## Resumo por área

| área | classificação | avaliação |
| --- | --- | --- |
| Homes | `SAUDÁVEL` | `Home.md` é Home dos Jogadores; `Home_Mestre.md` é área do Mestre; `Home_Jogadores.md` está arquivado. |
| Plugin Homepage | `SAUDÁVEL` | Continua apontando para `Home`, o que agora é correto. |
| Campos herdados | `ACEITÁVEL` | Campos como `thumbnail`, `cover`, `status`, `tags`, `NoteIcon`, `NoteStatus` continuam preservados. |
| `chapters` / `sessions` | `HÍBRIDO_CONTROLADO` | `chapters` deve continuar; `sessions` ainda é campo futuro/piloto. Não bloquear por enquanto. |
| Tags visuais antigas | `HÍBRIDO_CONTROLADO` | Tags antigas devem ser mantidas como ponte. Não remover. |
| Tags RPG novas | `RISCO_MÉDIO` | Ainda não estão completas/consistentes em todo o vault. Deve ser tratado no piloto, não em massa. |
| Templates atuais | `RISCO_MÉDIO` | Existem templates em evolução; não devem ser aplicados em massa antes do piloto. |
| Dataview/DataCards | `RISCO_MÉDIO` | Consultas dependem de campos e tags parcialmente preenchidos. Evitar mudanças de campo/tag sem compatibilidade. |
| Home dos Jogadores | `ACEITÁVEL` | Usa filtros conservadores contra mestre/segredo/spoiler. Pode mostrar pouco até notas receberem visibilidade. |
| Mídia | `RISCO_ALTO` | Auditorias indicam referências quebradas e possíveis órfãs; não apagar nem mover mídia. |
| Mapa/Calendário | `RISCO_MÉDIO` | Leaflet/Calendarium existem; não renomear notas/imagens sem auditoria específica. |
| Frontmatter/YAML | `ACEITÁVEL` | Não foram encontrados delimitadores quebrados; dois arquivos usam `tags` escalar e precisam revisão. |
| Pendências locais antigas | `RISCO_MÉDIO` | Mídia e Classes podem ser commitadas separadamente; dashboard/classes precisa revisão. |

## Pontos alinhados

- A decisão final de Homes está refletida operacionalmente:
  - `Home.md` = jogadores;
  - `Home_Mestre.md` = mestre;
  - `Home_Jogadores.md` = arquivado.
- O plugin Homepage aponta para `Home`.
- A camada de compatibilidade preserva campos antigos e recomenda adição gradual de campos novos.
- A estratégia de tags antigas como ponte permanece válida.
- Não houve remoção de campos antigos nem de tags visuais.

## Pontos ainda híbridos

- `chapters` permanece como compatibilidade; `sessions` ainda não foi distribuído.
- `visibility` ainda não está aplicado em todas as notas.
- `type`/`subtype` existem parcialmente.
- Tags RPG novas ainda não substituem tags antigas.
- Templates de Classes foram criados como pendência local, mas ainda não aplicados ao vault.

## Riscos principais

### Dataview/DataCards

Classificação: `RISCO_MÉDIO`.

Motivo: consultas dependem de `thumbnail`, `cover`, `status`, `tags`, `location`, `territory`, `faction`, `chapters`, `type` e `subtype`.

Regra: não trocar campos antigos por novos sem consulta compatível.

### Home dos Jogadores

Classificação: `ACEITÁVEL`.

Motivo: a Home dos Jogadores é conservadora. A ausência de `visibility` em muitas notas significa que ela pode mostrar pouco, mas não deve vazar conteúdo do mestre.

### Mídia

Classificação: `RISCO_ALTO`.

Motivo: relatórios anteriores apontam referências de mídia não resolvidas e mídias possivelmente órfãs.

Regra: não mover, renomear ou apagar mídia antes de análise cruzada.

### Frontmatter

Classificação: `ACEITÁVEL`.

Motivo: não foram detectados casos de frontmatter colapsado, delimitador ausente ou campos duplicados no escopo auditado. Dois arquivos têm `tags` em formato escalar.

## Bloqueadores para migração em massa

| bloqueador | status |
| --- | --- |
| Aplicação consistente de `visibility` | pendente |
| Estratégia piloto de `sessions` sem remover `chapters` | pendente |
| Política de mídia quebrada/órfã | pendente |
| Revisão de `CULTURE.md` e `LATEST_NEWS.md` quanto a `tags` escalar | pendente |
| Decisão sobre alterações remanescentes em `Workflow/OMNISVERA_DASHBOARD_SYSTEM.md` | pendente |

## Liberação para piloto

Classificação geral: `ACEITÁVEL PARA PILOTO`.

O vault não está pronto para migração em massa por templates, mas está suficientemente organizado para um lote piloto pequeno, desde que:

1. não remova campos antigos;
2. não remova tags antigas;
3. não mova mídia;
4. aplique campos novos em poucas notas;
5. valide Dataview/DataCards/Home visualmente no Obsidian.
