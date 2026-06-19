---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - workflow
  - schema
  - template
  - character-system
---

# Schema de Personagens

Este documento define o contrato de compatibilidade das páginas de personagem. Ele não substitui o conteúdo narrativo e não exige que todas as notas sejam normalizadas imediatamente.

O objetivo é permitir correções graduais sem quebrar Dataview, DataCards, estilos, links ou filtros.

## Personagens centrais

| Personagem | Arquivo | Classificação atual | Ponto a revisar |
|:--|:--|:--|:--|
| Vezemir | [[Vezemir]] | `role: player`, tags `player` e `character` | Localização do frontmatter difere da localização descrita no corpo. |
| Varkh Nimalis | [[Varkh Nimalis]] | `role: player`, tags `player` e `character` | `territory` aponta para uma nota inexistente; valores relacionados a lugar não seguem o mesmo formato. |
| Raziel | [[Raziel]] | `role: player`, tags `player` e `character` | Classificação corrigida; conteúdo e conexões com a campanha ainda precisam ser desenvolvidos. |

Essa tabela registra o estado encontrado. Ela não autoriza correções automáticas.

## Dependências observadas no vault

As páginas e consultas atuais esperam principalmente:

- `thumbnail` para retratos em tabelas e cartões;
- `status` para estado do personagem;
- `role` para função narrativa;
- `location` para localização atual;
- `territory` para agrupamento geográfico;
- `faction` para afiliação;
- `religion` em algumas consultas;
- `class` e `race` para identificação;
- `chapter` ou tags de capítulo para aparições;
- a tag `character` para o personagem aparecer nas consultas gerais.

Uma propriedade não deve ser removida apenas porque está vazia. Campos vazios ainda funcionam como parte do contrato do template.

## Propriedades-base

| Propriedade | Formato preferido | Obrigatória | Observação |
|:--|:--|:--|:--|
| `obsidianUIMode` | texto | Não | Normalmente `preview`. |
| `NoteIcon` | texto | Sim | Usar `character`. |
| `NoteStatus` | texto | Não | Estado editorial da nota, não do personagem. |
| `thumbnail` | caminho de mídia | Sim | Preferir `zz_media/nome-do-arquivo.ext`. |
| `status` | texto | Sim | Ex.: Vivo, Falecido, Desaparecido. |
| `location` | texto ou wikilink entre aspas | Sim | Não mudar o tipo de uma nota existente sem necessidade. |
| `territory` | texto ou wikilink entre aspas | Recomendável | Deve apontar para uma nota real quando for wikilink. |
| `faction` | texto ou wikilink entre aspas | Recomendável | Pode ser `Nenhuma` quando aplicável. |
| `religion` | texto ou wikilink entre aspas | Não | Manter se consultas ou narrativa utilizarem. |
| `class` | texto | Sim | Classe mecânica ou descrição funcional. |
| `race` | texto | Sim | Raça do personagem. |
| `role` | texto | Sim | A taxonomia definitiva ainda precisa ser decidida. |
| `chapter` | lista | Não | Manter como lista quando já existir como lista. |
| `tags` | lista | Sim | Deve incluir `character`. |

## Tipos que devem ser preservados

### Lista

```yaml
chapter:
  - 00 - Nome do Capítulo
  - 01 - Outro Capítulo
```

```yaml
tags:
  - character
  - player
```

### Wikilink como texto

```yaml
location: "[[Nimalia]]"
faction: "[[Coroa de Nimalia]]"
```

O uso de aspas evita que os colchetes sejam interpretados incorretamente pelo YAML.

## Taxonomia narrativa pendente

Outros arquivos do vault ainda podem misturar:

- `player`;
- `npc`;
- `antagonist`;
- descrições livres em `role`.

Para os três protagonistas, `role` representa o controle na mesa:

- `player`: personagem de jogador;
- `npc`: personagem controlado pelo mestre.

Função dramática, profissão e título não devem substituir `role`. Esses conceitos podem continuar no texto, nas tags existentes ou ganhar propriedades separadas quando isso for deliberadamente definido.

Vezemir, Varkh e Raziel são personagens de jogador e agora compartilham `role: player` e a tag `player`.

## Processo de migração de uma página

1. Copiar a nota ou garantir que o estado atual esteja commitado.
2. Comparar seu frontmatter com este schema.
3. Adicionar somente propriedades necessárias.
4. Corrigir links inexistentes apenas após confirmar o destino correto.
5. Não reordenar todas as propriedades.
6. Não trocar tags em massa.
7. Validar o YAML.
8. Abrir a nota no Obsidian.
9. Verificar Home, DataCards, Dataview e backlinks.
10. Criar um commit exclusivo para a nota ou para um conjunto pequeno e relacionado.

## Regra para templates de Disgraceland

Ao converter uma página de Disgraceland:

- preservar a estrutura que produz o visual desejado;
- substituir completamente nomes, tags e links narrativos antigos;
- revisar consultas embutidas;
- verificar imagens e thumbnails;
- remover referências semânticas a Disgraceland da nova cópia;
- manter o arquivo-fonte disponível enquanto o novo template não tiver sido validado.
