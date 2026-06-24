# Template de Tarefa para IA

Use este template para definir e executar tarefas no vault Omnisvera.

## Campos da tarefa

### Objetivo
Descreva claramente o objetivo da tarefa em uma frase.

### Escopo
Defina o que está incluído e o que está fora do escopo.

### Arquivos permitidos
Liste os diretórios e arquivos que podem ser alterados.

### Arquivos proibidos
Liste os diretórios e arquivos que não podem ser alterados.

### Comandos permitidos
Liste os comandos Git e de sistema que podem ser usados.

### Comandos proibidos
Liste os comandos que não podem ser usados.

### Critérios de sucesso
Defina como saber quando a tarefa foi concluída com sucesso.

### Riscos
Liste riscos potenciais e como mitigá-los.

### Relatório esperado
Descreva o formato do relatório final.

## Exemplo de uso

### Objetivo
Corrigir referências quebradas de imagens em notas ativas.

### Escopo
- Incluído: Notas ativas fora de Workflow/Legacy
- Excluído: Notas em Workflow/Legacy, documentação

### Arquivos permitidos
- Classes/*.md
- Locations/*.md
- Factions/*.md
- Religion/*.md
- Players/*.md

### Arquivos proibidos
- Workflow/Legacy/*
- Workflow/Templates/*
- .obsidian/*

### Comandos permitidos
- git status, git diff, git log
- Comandos de busca de texto
- Comandos de listagem de arquivos

### Comandos proibidos
- git merge
- git push --force
- Comandos que deletam arquivos

### Critérios de sucesso
- Todas as referências quebradas em notas ativas foram corrigidas
- Nenhuma referência válida foi alterada
- Relatório gerado com lista de correções

### Riscos
- Alterar referências válidas acidentalmente
- Deletar arquivos por engano
- Mitigação: Verificar cada alteração antes de commit

### Relatório esperado
- Lista de referências quebradas encontradas
- Lista de correções aplicadas
- Arquivos alterados
- Pendências identificadas
