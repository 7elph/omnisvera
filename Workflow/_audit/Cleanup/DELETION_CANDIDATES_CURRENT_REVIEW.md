---
obsidianUIMode: preview
NoteIcon: workflow
NoteStatus: Active
type: audit
visibility: Mestre
spoiler_level: none
gm_secret: true
status: Revisão
tags:
  - workflow
  - audit
  - cleanup
---

# Revisão Atual — Candidatos a Exclusão ou Arquivamento

> [!IMPORTANT]
> Este relatório lista candidatos. Nada foi excluído nesta etapa.
>
> Regra: apagar somente em commit próprio, depois de confirmação do Sage.

## Resposta rápida — Disgraceland antigo

Ainda existe acesso local a `Workflow/Legacy/Disgraceland`, mas o conteúdo que sobrou ali não está rastreado pelo Git.

Estado observado:

| Item | Estado |
|---|---|
| `Workflow/Legacy/Disgraceland` | existe localmente |
| Rastreado pelo Git | não |
| Conteúdo observado | `.trash`, `.smtcmp_json_db`, `.smtcmp_vector_db.tar.gz` |
| Tamanho aproximado | 4,36 MB |
| Uso operacional | nenhum encontrado |
| Recomendação | excluir localmente em etapa própria, se o Sage quiser limpar espaço |

O material técnico útil do Disgraceland já foi extraído para relatórios, taxonomia, templates e histórico de commits. O que restou localmente parece ser sobra de cache/lixeira do vault legado, não vault operacional.

## Candidatos locais ignorados pelo Git

Esses itens estão ignorados por `.gitignore`, então não são enviados ao GitHub, mas ocupam espaço local e podem poluir o vault no Obsidian.

| Caminho | Motivo | Git | Recomendação |
|---|---|---|---|
| `DisgracelandOnline.zip` | Backup grande local do legado; cerca de 372 MB. | ignorado | Pode excluir localmente se não for mais necessário. |
| `Workflow/Legacy/Disgraceland/` | Sobra local do legado, não rastreada; contém cache/lixeira. | não rastreado | Pode excluir localmente em limpeza própria. |
| `.smtcmp_json_db/` | Cache/índice local. | ignorado | Pode excluir; será regenerado se a ferramenta usar de novo. |
| `.smtcmp_vector_db.tar.gz` | Cache vetorial local. | ignorado | Pode excluir se não estiver usando a ferramenta de busca local. |
| `.tmp_refs/` | Dependências temporárias. | ignorado | Pode excluir se nenhum processo local estiver usando. |
| `.trash/` | Lixeira local do Obsidian. | ignorado | Pode esvaziar depois de revisar. |
| `.local-index/` | Índice local. | ignorado | Pode excluir se for regenerável. |
| `.local-proposals/` | Propostas locais antigas. | ignorado | Revisar antes de excluir. |

## Itens rastreados que NÃO recomendo apagar sem nova decisão

| Caminho | Motivo |
|---|---|
| `.local-tools/` | Validadores e ferramentas que estamos usando para manter o vault saudável. |
| `.ollama/` | Configuração local de IA opcional; não pesa muito e documenta o setup. |
| `.vscode/` | Recomendações de ambiente. |
| `.obsidian/` | Configuração funcional do vault. |
| `Workflow/Legacy/Old Dragon anterior/` | Referência mecânica antiga; pequena, rastreada e ainda citada por notas/classes como histórico. |
| `Workflow/_archive/` | Arquivo histórico de migração; pequeno e rastreado. |
| `Workflow/_audit/` | Relatórios de decisão e validação; útil enquanto a migração ainda está em andamento. |

## Mídia possivelmente órfã

O validador operacional reporta `38` ocorrências por contar variações de caminho curto, caminho completo e maiúsculas/minúsculas.

Arquivos reais em `zz_media` sem referência operacional direta encontrados nesta revisão:

| Arquivo |
|---|
| `zz_media/area-comercial-1.png` |
| `zz_media/area-comercial-2.png` |
| `zz_media/area-comercial-3.png` |
| `zz_media/distrito-comercial.png` |
| `zz_media/elfs.PNG` |
| `zz_media/prop_anao.PNG` |
| `zz_media/smoke.mp3` |
| `zz_media/sound.png` |

Recomendação: não apagar mídia ainda. Algumas imagens podem ser úteis para notas futuras de Nimalis, comércio, distritos, raças ou ambiência sonora.

## Candidatos conceituais já resolvidos operacionalmente

| Item | Estado |
|---|---|
| `Rules/Classes` | Removido/consolidado em `Classes/`. Não recriar. |
| `Rules/Races` | Removido/consolidado em `Races/`. Não recriar. |
| `Races/Dragonbourn.md` | Substituído por `Races/Dragonborn.md`. Não recriar; manter `Dragonbourn` apenas como alias textual quando necessário. |
| `Classes/Homem de Armas.md` | Não existe como classe ativa. Usar `Guerreiro`. |
| `Home_Jogadores.md` | Não existe na raiz. A Home dos jogadores é `Home.md`. |

## Próxima limpeza segura sugerida

Ordem conservadora:

1. Excluir localmente caches ignorados (`.tmp_refs`, `.smtcmp_*`, `.local-index`) se o Sage quiser reduzir ruído local.
2. Excluir ou mover para backup externo `DisgracelandOnline.zip`.
3. Excluir localmente `Workflow/Legacy/Disgraceland/`, pois não está rastreado e não é operacional.
4. Fazer uma etapa separada para mídia órfã, revisando imagem por imagem antes de apagar.

Classificação: `NEEDS_SAGE_CONFIRMATION_BEFORE_DELETE`

## Validação executada

Comandos usados nesta revisão:

```powershell
git ls-files "DisgracelandOnline.zip" ".smtcmp_vector_db.tar.gz" ".smtcmp_json_db/**" ".tmp_refs/**" ".trash/**" ".local-index/**" ".local-proposals/**" "Workflow/Legacy/Disgraceland/**"
git check-ignore -v DisgracelandOnline.zip .smtcmp_vector_db.tar.gz .smtcmp_json_db .tmp_refs .trash .local-index .local-proposals Workflow/Legacy/Disgraceland
python .local-tools/validate_media.py . --ignore-legacy
```

Resumo:

- `DisgracelandOnline.zip`, `.smtcmp_*`, `.tmp_refs`, `.trash`, `.local-index` e `.local-proposals` estão ignorados pelo Git.
- `Workflow/Legacy/Disgraceland` existe localmente, mas não possui arquivos rastreados pelo Git nesta revisão.
- A mídia ativa não tem referências quebradas.
- A lista de mídia órfã real deve ser revisada manualmente antes de exclusão.
