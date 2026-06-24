# Checklist de Revisão para IA

Use este checklist antes de abrir PR ou fazer merge.

## Verificações Git

- [ ] `git status` - confirmar que não há alterações não commitadas
- [ ] `git diff --stat` - revisar estatísticas de alterações
- [ ] `git diff --name-status` - revisar lista de arquivos alterados
- [ ] Confirmar que branch correta está ativa
- [ ] Confirmar que commits têm mensagens claras

## Verificações de arquivos deletados

- [ ] Verificar se arquivos deletados não são críticos
- [ ] Verificar se arquivos deletados não têm referências ativas
- [ ] Confirmar que deletões foram intencionais
- [ ] Verificar se deletões estão documentadas no changelog

## Verificações de referências quebradas

- [ ] Buscar referências a imagens deletadas
- [ ] Buscar referências a notas deletadas
- [ ] Verificar wikilinks quebrados
- [ ] Verificar links externos quebrados (se aplicável)

## Verificações de YAML/frontmatter

- [ ] Verificar sintaxe YAML válida
- [ ] Verificar campos obrigatórios presentes
- [ ] Verificar que campos não foram removidos acidentalmente
- [ ] Verificar que valores não foram alterados sem motivo

## Verificações de imagens inexistentes

- [ ] Verificar que `cover` aponta para arquivo existente
- [ ] Verificar que `thumbnail` aponta para arquivo existente
- [ ] Verificar que embeds `![[ ]]` apontam para arquivos existentes
- [ ] Verificar que caminhos estão corretos

## Verificações de CANON.md

- [ ] Verificar se CANON.md foi alterado
- [ ] Se alterado, confirmar que mudanças foram autorizadas
- [ ] Verificar que seções críticas não foram removidas
- [ ] Verificar que diretrizes de IA não foram enfraquecidas

## Verificações de .obsidian

- [ ] Verificar se .obsidian foi alterado
- [ ] Se alterado, confirmar que mudanças são técnicas críticas
- [ ] Verificar que configurações de plugins não foram quebradas
- [ ] Verificar que Leaflet não foi alterado sem auditoria

## Verificações de mapas/Leaflet

- [ ] Verificar se data.json do Leaflet foi alterado
- [ ] Se alterado, confirmar que mapas não foram perdidos
- [ ] Verificar que marcadores não foram removidos acidentalmente
- [ ] Verificar que configurações de mapas permanecem válidas

## Verificações de cânone

- [ ] Verificar se houve alteração de cânone
- [ ] Se alterado, confirmar que foi autorizado pelo Sage
- [ ] Verificar que não houve invenção de lore
- [ ] Verificar que decisões em aberto não foram canonizadas

## Verificações de mecânica

- [ ] Verificar se houve alteração de regras mecânicas
- [ ] Se alterado, confirmar que fonte foi citada
- [ ] Verificar que valores numéricos não foram alterados sem motivo
- [ ] Verificar que regras autorais foram marcadas

## Verificações de AI_CHANGELOG.md

- [ ] Verificar se AI_CHANGELOG.md foi atualizado
- [ ] Confirmar que entrada tem todos os campos obrigatórios
- [ ] Confirmar que status está correto
- [ ] Confirmar que pendências foram documentadas

## Verificações finais

- [ ] Relatório final foi gerado
- [ ] Relatório inclui arquivos alterados
- [ ] Relatório inclui tipo de alteração
- [ ] Relatório inclui pendências identificadas
- [ ] Recomendações estão claras

## Critérios de bloqueio

Não abrir PR se:

- Houver alterações não commitadas
- CANON.md foi alterado sem autorização
- .obsidian foi alterado sem motivo crítico
- Leaflet foi alterado sem auditoria
- Referências quebradas foram introduzidas
- Cânone foi alterado sem autorização
- AI_CHANGELOG.md não foi atualizado
