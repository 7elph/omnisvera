# RPG MIGRATION PRINCIPLES

Princípios para uma migração futura segura de arquitetura Disgraceland para um vault de RPG.

Não é plano de migração ainda. Não compara com Omnisvera. Não aplica mudanças.

## 1. Separar técnica de lore

Não misturar:

- criação de lore;
- renomeação de entidades;
- padronização de frontmatter;
- reorganização de mídia;
- ajustes visuais;
- mudança de plugins.

Cada lote deve ter objetivo técnico claro.

## 2. Não remover campo antigo ao criar campo novo

Regra:

1. adicionar campo novo;
2. preencher em pequeno lote;
3. criar consulta compatível;
4. validar visual;
5. só depois considerar remoção do campo antigo.

Exemplo:

- manter `chapters`;
- adicionar `sessions`;
- fazer consultas aceitarem ambos;
- validar aparições;
- só depois decidir destino de `chapters`.

## 3. Preservar tags visuais até criar equivalentes

Tags usadas por Supercharged Links devem continuar existindo até:

- nova tag definida;
- UID/selector criado;
- cor/peso configurado;
- dashboards atualizados;
- visual validado.

## 4. Não trocar `thumbnail` por `cover` sem atualizar DataCards

`thumbnail` e `cover` têm funções diferentes.

Regra:

- se `imageProperty: thumbnail`, nota precisa de `thumbnail`;
- se `imageProperty: cover`, nota precisa de `cover`.

## 5. Não remover `chapters` antes de criar compatibilidade

`chapters` alimenta aparições por `file.name`.

Migração futura deve:

- adicionar `sessions`;
- mapear capítulos antigos;
- criar consulta compatível;
- validar personagens;
- só depois discutir remoção.

## 6. Não editar CSS gerado automaticamente

`supercharged-links-gen.css` é gerado por plugin.

Regra:

- não editar diretamente;
- alterar via Supercharged Links/Style Settings;
- se for preciso CSS manual, copiar para outro snippet.

## 7. Não renomear notas usadas por Leaflet sem atualizar mapa

Marcadores Leaflet usam `link`.

Fluxo seguro:

1. listar marcadores;
2. mapear links;
3. renomear nota;
4. atualizar JSON/bloco;
5. validar mapa no Obsidian.

## 8. Não apagar mídia possivelmente órfã sem análise cruzada

Antes de apagar:

- Markdown;
- frontmatter;
- HTML;
- CSS;
- JSON de plugins;
- Canvas;
- Leaflet;
- DataCards;
- handouts futuros.

## 9. Não alterar Home antes de mapear dashboards

Home agrega muitos sistemas:

- DataCards;
- Dataview;
- Calendarium;
- callouts;
- imagens;
- tags;
- fields de personagens/territórios/locais.

Qualquer mudança deve ser validada visualmente.

## 10. Criar camada de compatibilidade

Migração segura deve aceitar por um tempo:

- `chapters` e `sessions`;
- `thumbnail` e `portrait`, sem confundir DataCards;
- tags antigas e tags novas;
- `status` e `life_status`;
- `cover` e campos especializados de mídia.

## 11. Validar visualmente no Obsidian depois de cada lote

Validação mínima:

- Home abre;
- cards renderizam;
- imagens aparecem;
- links coloridos mantêm função;
- mapa abre;
- calendário renderiza;
- Dataview não fica vazio por erro;
- dashboard mobile continua legível.

## 12. Commit pequeno e reversível

Cada etapa futura deve ser commit separado:

- auditoria;
- contratos;
- proposta;
- criação de templates;
- migração de campos;
- ajuste de mídia;
- validação.

## 13. Evitar migração em massa sem relatório

Antes de qualquer lote:

- listar arquivos afetados;
- listar campos afetados;
- listar consultas afetadas;
- listar tags afetadas;
- listar mídia afetada;
- definir rollback.

## 14. Critérios para avançar

Só avançar para migração real quando existirem:

- contratos do sistema legado;
- modelo RPG desejado;
- auditoria do vault atual;
- matriz de equivalência;
- plano de compatibilidade;
- checklist de validação visual.

## 15. Regra de segurança

Se uma alteração técnica puder quebrar visual, consulta, mapa, calendário, link ou mídia, ela precisa de validação antes e depois.
