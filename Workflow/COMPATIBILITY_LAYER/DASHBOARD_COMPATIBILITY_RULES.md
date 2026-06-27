> [!WARNING]
> Documento histórico/anterior à taxonomia oficial atual do Sage.
> Não usar como fonte principal para novas migrações.
> Fonte atual: [[OMNISVERA_SYSTEM_TAXONOMY]] e [[OMNISVERA_SYSTEM_TAXONOMY_DECISIONS]].
# Dashboard Compatibility Rules

Estas regras definem como Home/dashboard deve operar durante a camada de compatibilidade.

## Regra principal

Home atual = dashboard do mestre.

Enquanto o modelo de visibilidade não estiver aplicado e validado, a Home não deve ser considerada segura para jogadores.

## Regras para dashboard do mestre

- Pode listar notas `visibility: Mestre`.
- Pode listar notas sem `visibility`, tratando ausência como mestre.
- Pode usar DataCards e Dataview herdados.
- Deve preservar campos atuais de banner e callouts.
- Não deve depender exclusivamente de campos ainda ausentes em massa.

## Regras para dashboard de jogadores

- Não criar antes de filtros seguros.
- Não exibir `visibility: Mestre`.
- Não exibir `gm_secret: true`.
- Não exibir `spoiler_level: heavy`.
- Não exibir notas sem `visibility`, salvo whitelist manual.
- Deve preferir `visibility: Público`, `visibility: Jogadores` ou `player_known: true`.

## Regras para DataCards públicos

DataCards públicos precisam filtrar visibilidade:

```dataview
TABLE thumbnail, status, location
FROM "Characters"
WHERE contains(tags, "character")
AND (visibility = "Público" OR visibility = "Jogadores" OR player_known = true)
SORT file.name ASC
```

## Regras para handouts

- Handout só aparece para jogadores se liberado.
- `handout_image` não deve ser exibido sem `visibility` segura.
- Conteúdo com `gm_secret: true` fica fora de cards públicos.

## Regras para mídia no dashboard

- `thumbnail` para cards compactos.
- `cover` para cards amplos.
- `portrait` não substitui `thumbnail`.
- `handout_image` exige filtro.

## Regras para campos ausentes

- Campo ausente não significa público.
- Campo ausente deve ser tratado como não classificado.
- Conteúdo não classificado deve ficar no dashboard do mestre.

## Anti-padrões

- Criar Home pública a partir da Home mestre sem filtros.
- Usar `FROM #character` em dashboard público sem `visibility`.
- Exibir `cover` ou `thumbnail` de notas secretas em cards públicos.
- Remover blocos antigos da Home antes de criar substitutos testados.
- Fazer dashboard depender de `sessions` antes de preencher o campo no piloto.
