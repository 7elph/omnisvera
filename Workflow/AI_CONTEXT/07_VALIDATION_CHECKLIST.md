# Checklist Operacional para IAs

Checklist operacional para IAs antes de finalizar tarefa.

## Git

- [ ] `git status` - sem alterações não commitadas
- [ ] Branch correta está ativa
- [ ] Commits têm mensagens claras
- [ ] Nenhum arquivo não intencional foi alterado

## Markdown

- [ ] Sintaxe Markdown válida
- [ ] Wikilinks funcionam
- [ ] Headers estão corretos
- [ ] Listas estão formatadas corretamente
- [ ] Callouts estão formatados corretamente

## YAML

- [ ] Sintaxe YAML válida
- [ ] Indentação correta
- [ ] Aspas estão balanceadas
- [ ] Campos obrigatórios presentes
- [ ] Valores não foram alterados sem motivo

## Links

- [ ] Wikilinks apontam para notas existentes
- [ ] Links externos funcionam (se aplicável)
- [ ] Nenhum link quebrado foi introduzido
- [ ] Referências cruzadas estão corretas

## Mídia

- [ ] `cover` aponta para arquivo existente
- [ ] `thumbnail` aponta para arquivo existente
- [ ] Embeds `![[ ]]` apontam para arquivos existentes
- [ ] Caminhos estão corretos
- [ ] Nenhuma imagem foi deletada sem verificação

## Cânone

- [ ] CANON.md não foi alterado sem autorização
- [ ] Nenhum cânone foi inventado
- [ ] Nenhuma decisão em aberto foi canonizada
- [ ] Disgraceland não foi usado como cânone
- [ ] Conflitos foram marcados como pendentes

## Mapas

- [ ] Leaflet não foi alterado sem auditoria
- [ ] Mapas não foram perdidos
- [ ] Marcadores não foram removidos acidentalmente
- [ ] Configurações permanecem válidas

## Mecânica

- [ ] Regras mecânicas não foram alteradas sem fonte
- [ ] Valores numéricos não foram alterados sem motivo
- [ ] Regras autorais foram marcadas
- [ ] RULES_SOURCES.md foi consultado

## Relatório

- [ ] Relatório final foi gerado
- [ ] Arquivos alterados foram listados
- [ ] Tipo de alteração foi documentado
- [ ] Pendências foram identificadas
- [ ] Recomendações estão claras
- [ ] AI_CHANGELOG.md foi atualizado

## Critérios de bloqueio

Não finalizar se:

- Houver alterações não commitadas
- YAML estiver inválido
- Referências estiverem quebradas
- Cânone foi alterado sem autorização
- AI_CHANGELOG.md não foi atualizado
- Relatório não foi gerado
