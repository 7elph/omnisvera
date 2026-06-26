# Vault Cleanup Index

Data da triagem: 2026-06-26

Objetivo: registrar uma limpeza segura do vault sem apagar nada permanentemente, sem mover mídia e sem arquivar conteúdo duvidoso.

## Resultado desta etapa

| item | resultado |
| --- | ---: |
| Arquivos analisados em varredura ativa de Markdown | 145 |
| Arquivos com termos legados fora de `Workflow/Legacy/Disgraceland` e fora das auditorias principais | 24 |
| Referências de mídia não resolvidas, total bruto da auditoria Omnisvera | 69 |
| Referências de mídia não resolvidas relevantes ao vault após excluir ruído de ferramentas locais | 35 |
| Mídias possivelmente órfãs reportadas pela auditoria Omnisvera | 35 |
| Arquivos arquivados nesta etapa | 0 |
| Mídias movidas nesta etapa | 0 |
| Arquivos apagados nesta etapa | 0 |

## Arquivos deste pacote

| arquivo | função |
| --- | --- |
| `OBSOLETE_CONTENT_CANDIDATES.md` | Lista candidatos obsoletos ou ambíguos e classificação. |
| `ARCHIVED_CONTENT_LOG.md` | Registra o que foi movido para `_archive`; nesta etapa nada foi movido. |
| `BROKEN_LINKS_AND_MEDIA_REFERENCES.md` | Registra referências quebradas e mídias possivelmente órfãs. |
| `DO_NOT_DELETE_REGISTER.md` | Lista conteúdo que não deve ser apagado/removido sem decisão explícita. |

## Critério usado

Um item só poderia ser arquivado automaticamente se atendesse a todos os critérios:

1. não aparece em links Markdown;
2. não aparece em YAML/frontmatter;
3. não aparece em Dataview/DataCards;
4. não aparece em Leaflet;
5. não aparece em Calendarium;
6. não aparece em CSS/snippets;
7. não aparece em configurações de plugin;
8. não está em `Workflow/Legacy/Disgraceland/_audit`;
9. não está em `Workflow/COMPATIBILITY_LAYER`;
10. não é nota canônica de Omnisvera.

Nenhum candidato passou nesses critérios com confiança suficiente. Portanto, esta etapa gerou relatório e não arquivou conteúdo.

## Classificações usadas

- `KEEP`
- `ARCHIVE_CANDIDATE`
- `ARCHIVED`
- `NEEDS_SAGE_REVIEW`
- `BROKEN_REFERENCE`
- `DO_NOT_DELETE`

## Diretório de quarentena preparado

Diretório local criado para uso futuro:

```text
Workflow/_archive/obsolete_review/2026-06-26
```

Observação: como nenhum arquivo foi movido, o diretório pode não aparecer no Git até receber conteúdo rastreável.

## Próxima ação segura

Revisar `OBSOLETE_CONTENT_CANDIDATES.md` e decidir quais itens podem ser arquivados manualmente em uma etapa posterior.
