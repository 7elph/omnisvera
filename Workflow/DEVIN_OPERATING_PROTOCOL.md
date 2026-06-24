# Protocolo de Operação para IAs/Agentes

Este documento define como Devin, Codex, Cline, MIA ou qualquer IA deve operar no vault Omnisvera.

## Regras fundamentais

### Branch e versionamento

- Sempre criar branch própria por tarefa
- Nunca trabalhar direto na `main`
- Nunca fazer merge sem autorização explícita do Sage
- Sempre fazer `git pull origin main` antes de criar nova branch
- Usar nomes de branch descritivos (ex: `devin/fix-broken-links`, `codex/add-new-location`)
- Fazer commits pequenos e claros com mensagens descritivas

### Leitura obrigatória antes de qualquer ação

- Sempre ler `Workflow/CANON.md` antes de responder sobre cânone
- Sempre ler `Workflow/LOCAL_ASSISTANT_PROTOCOL.md` antes de executar comandos
- Sempre ler `Workflow/RULES_SOURCES.md` antes de alterar regras mecânicas
- Sempre ler `Workflow/DEVIN_OPERATING_PROTOCOL.md` (este arquivo) antes de iniciar tarefa

### Preservação de estrutura

- Preservar frontmatter/YAML de todas as notas
- Preservar wikilinks existentes
- Preservar estrutura de pastas
- Não deletar notas sem justificativa documentada e aprovação
- Não alterar mapas/Leaflet sem auditoria completa
- Não alterar `.obsidian` sem motivo técnico crítico

### Limites de cânone

- Não inventar cânone
- Não resolver ambiguidades por inferência
- Não usar Disgraceland como cânone
- Não canonizar decisões em aberto
- Marcar incertezas como `Pendente de confirmação do Sage`

### Limites de regras mecânicas

- Não alterar regras mecânicas sem fonte oficial
- Consultar `Workflow/RULES_SOURCES.md` para hierarquia de fontes
- Regras autorais devem ser claramente marcadas
- Não misturar edições de Old Dragon sem justificativa

### Limites de mídia

- Não alterar imagens sem aprovação
- Não deletar imagens sem verificar referências
- Seguir padrões em `Workflow/AI_CONTEXT/04_MEDIA_RULES.md`
- Registrar novas imagens no relatório

## Fluxo de trabalho padrão

### 1. Início de tarefa

1. Ler `Workflow/CANON.md`
2. Ler `Workflow/LOCAL_ASSISTANT_PROTOCOL.md`
3. Ler `Workflow/DEVIN_OPERATING_PROTOCOL.md`
4. Criar branch própria
5. Ler arquivos de contexto relevantes em `Workflow/AI_CONTEXT/`

### 2. Execução

1. Respeitar escopo definido na tarefa
2. Usar `Workflow/AI_TASK_TEMPLATE.md` como guia
3. Preservar frontmatter e links
4. Não alterar cânone sem autorização
5. Documentar mudanças em `Workflow/AI_CHANGELOG.md`

### 3. Finalização

1. Rodar checklist de validação em `Workflow/AI_REVIEW_CHECKLIST.md`
2. Rodar checklist operacional em `Workflow/AI_CONTEXT/07_VALIDATION_CHECKLIST.md`
3. Gerar relatório final
4. Atualizar `Workflow/AI_CHANGELOG.md`
5. Commit com mensagem clara
6. Push para origin
7. Abrir PR para `main`

## Comandos permitidos

- `git checkout`, `git branch`, `git checkout -b`
- `git add`, `git commit`, `git push`
- `git pull`, `git fetch`, `git merge`
- `git status`, `git diff`, `git log`
- `git restore` (apenas para descartar mudanças locais)
- Comandos de leitura de arquivos
- Comandos de busca de texto (grep, find)
- Comandos de listagem de diretórios

## Comandos proibidos

- `git merge` para `main` sem autorização
- `git push --force`
- `git rebase` sem autorização
- `git reset --hard` sem autorização
- Comandos que deletam arquivos sem verificação
- Comandos que alteram `.obsidian` sem motivo crítico

## Relatórios

Sempre gerar relatório final incluindo:

- Arquivos alterados
- Tipo de alteração (cânone, estrutura, mídia, mecânica)
- Referências quebradas encontradas
- Pendências identificadas
- Recomendações

## Erros e incertezas

Em caso de erro ou incerteza:

- Parar e informar o Sage
- Não tentar resolver por conta própria
- Marcar como `Pendente de confirmação do Sage`
- Documentar o contexto do erro

## Responsabilidades

### IA é assistente, não decisora

- A IA auxilia na organização e manutenção
- A IA não toma decisões de cânone
- A IA não resolve conflitos narrativos
- A IA não inventa lore

### Sage é autoridade final

- Todas as decisões de cânone cabem ao Sage
- A IA sugere, o Sage decide
- Em caso de conflito, seguir decisão do Sage

## Referências

- `Workflow/CANON.md` - Cânone confirmado
- `Workflow/LOCAL_ASSISTANT_PROTOCOL.md` - Protocolo do assistente local
- `Workflow/RULES_SOURCES.md` - Fontes de regras
- `Workflow/AI_CONTEXT/` - Contexto operacional para IAs
- `Workflow/AI_CHANGELOG.md` - Registro de alterações por IA
