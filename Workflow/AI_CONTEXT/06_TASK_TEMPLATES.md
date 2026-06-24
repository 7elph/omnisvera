# Modelos de Prompt para Tarefas

Modelos de prompt para tarefas futuras no vault Omnisvera.

## Auditar vault

**Objetivo:** Identificar inconsistências e problemas no vault.

**Prompt:**
Audite o vault Omnisvera buscando:
- Referências quebradas de imagens
- Wikilinks quebrados
- Notas sem frontmatter
- Notas com frontmatter inválido
- Imagens sem referências
- Duplicatas de notas
- Notas em Draft há muito tempo

**Saída esperada:**
- Lista de problemas encontrados
- Classificação por severidade
- Recomendações de correção

## Integrar imagens

**Objetivo:** Adicionar novas imagens ao vault seguindo padrões.

**Prompt:**
Integre as seguintes imagens ao vault:
- [Lista de imagens]
- Siga padrões em Workflow/AI_CONTEXT/04_MEDIA_RULES.md
- Organize em subpastas apropriadas
- Atualize covers de notas relevantes
- Verifique referências quebradas

**Saída esperada:**
- Caminhos das imagens adicionadas
- Notas atualizadas
- Relatório de referências verificadas

## Padronizar frontmatter

**Objetivo:** Padronizar frontmatter de notas.

**Prompt:**
Padronize frontmatter das notas em [diretório]:
- Siga proposta em Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md
- Preserve valores existentes
- Adicione campos ausentes apenas se apropriado
- Não altere valores sem motivo

**Saída esperada:**
- Lista de notas alteradas
- Campos adicionados
- Campos preservados

## Criar nota nova como Draft

**Objetivo:** Criar nova nota como Draft.

**Prompt:**
Crie uma nova nota como Draft:
- Tipo: [Character/Location/Faction/etc]
- Nome: [nome]
- Use template apropriado em Workflow/Templates/
- Siga schema em Workflow/AI_CONTEXT/05_FRONTMATTER_SCHEMA.md
- Não invente cânone
- Marque campos em aberto

**Saída esperada:**
- Caminho da nota criada
- Conteúdo inicial
- Campos em aberto identificados

## Revisar links

**Objetivo:** Verificar integridade de wikilinks.

**Prompt:**
Revisar todos os wikilinks no vault:
- Identificar links quebrados
- Identificar links para notas deletadas
- Identificar links para notas em Workflow/Legacy
- Verificar duplicatas de notas

**Saída esperada:**
- Lista de links quebrados
- Lista de links para legado
- Recomendações de correção

## Revisar mídia

**Objetivo:** Verificar integridade de referências de mídia.

**Prompt:**
Revisar todas as referências de mídia:
- Verificar que cover aponta para arquivo existente
- Verificar que thumbnail aponta para arquivo existente
- Verificar que embeds apontam para arquivos existentes
- Identificar imagens sem referências

**Saída esperada:**
- Lista de referências quebradas
- Lista de imagens órfãs
- Recomendações de correção

## Preparar resumo para jogador

**Objetivo:** Criar resumo de informações para jogador.

**Prompt:**
Crie resumo para jogador sobre [tópico]:
- Use apenas informações confirmadas em CANON.md
- Não revele segredos do mestre
- Respeite visibility das notas
- Não invente informações

**Saída esperada:**
- Resumo formatado
- Fontes das informações
- Informações omitidas (secrets)

## Atualizar sessão

**Objetivo:** Registrar estado após sessão de jogo.

**Prompt:**
Atualize Workflow/AI_CONTEXT/09_SESSION_STATE.md:
- Adicione eventos jogados na sessão
- Atualize ganchos ativos
- Atualize rumores ativos
- Não invente eventos não jogados
- Marque informações pendentes

**Saída esperada:**
- Seções atualizadas
- Eventos registrados
- Pendências identificadas

## Criar relatório de inconsistências

**Objetivo:** Gerar relatório de inconsistências encontradas.

**Prompt:**
Crie relatório de inconsistências:
- Liste inconsistências por categoria
- Classifique por severidade
- Sugira correções
- Não corrija automaticamente
- Marque decisões necessárias do Sage

**Saída esperada:**
- Relatório estruturado
- Lista de inconsistências
- Recomendações
- Decisões pendentes
