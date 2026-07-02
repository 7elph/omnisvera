# Protocolo de Geração de Conteúdo — Omnisvera

Este protocolo orienta como a IA/Codex deve transformar respostas do Sage em conteúdo jogável para o vault.

## Ordem de autoridade

1. Respostas recentes do Sage.
2. Conteúdo já existente no vault.
3. Relações explícitas entre notas.
4. Padrões técnicos do vault.
5. Sugestões da IA, sempre marcadas como sugestão quando não forem confirmadas.

## Regras

- Usar primeiro informações existentes no vault.
- Preservar cânone já estabelecido.
- Não contradizer notas relacionadas.
- Separar conhecimento público de segredo do mestre.
- Não inventar nomes importantes sem necessidade.
- Quando inventar algo, marcar como sugestão.
- Manter tom fantasia medieval.
- Manter utilidade em mesa de RPG.
- Gerar conteúdo jogável, não enciclopédia morta.
- Preservar frontmatter e campos legacy.
- Não remover tags, links, imagens ou metadados sem autorização.

## Estrutura recomendada para nota desenvolvida

```md
# Nome da Nota

## Resumo

## O que os jogadores podem perceber

## Descrição

## Pessoas ou grupos ligados

## Rumores

## Ganchos de aventura

## Segredos do Mestre

## Relações

## Uso em jogo
```

## Como usar uma resposta do Sage

1. Ler a nota alvo.
2. Ler as notas relacionadas.
3. Ler o brief em `Workflow/Content_Development/Briefs/`.
4. Comparar respostas do Sage com o conteúdo existente.
5. Gerar apenas conteúdo compatível.
6. Se houver contradição, não resolver sozinho: marcar em `Pendências para o Sage`.

## Tom e forma

O texto deve ser direto, evocativo e útil em mesa.

Boa nota de RPG não é apenas uma explicação: ela precisa sugerir cenas, conflitos, rumores, escolhas e consequências.
