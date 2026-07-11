# Omnisvera Companion — RAG local

Este backend usa uma busca híbrida para responder perguntas do vault sem expor o Ollama diretamente para a rede.

## Modos

Configure com:

```powershell
$env:OMNISVERA_RAG_MODE="hybrid"
```

Valores aceitos:

| Valor | Comportamento |
|---|---|
| `lexical` | Usa apenas busca por título, alias, tags e palavras do conteúdo. |
| `semantic` | Usa apenas embeddings locais quando o índice existir. |
| `hybrid` | Combina título/alias exato, busca lexical e embeddings. Padrão. |

## Modelos usados

| Função | Variável | Padrão |
|---|---|---|
| Chat rápido | `OMNISVERA_FAST_MODEL` | `omnisvera-fast:latest` |
| Chat fundamentado | `OMNISVERA_QUALITY_MODEL` | `omnisvera-fast:latest` |
| Embeddings | `OMNISVERA_EMBED_MODEL` | `nomic-embed-text` |
| Modo de resposta | `OMNISVERA_RESPONSE_MODE` | `fast` |
| Ollama | `OLLAMA_BASE_URL` | `http://localhost:11434` |

O backend chama o Ollama apenas em `localhost`. O celular conversa com o backend, não com o Ollama diretamente.

O benchmark local mostrou que `qwen3:4b` não conclui o contrato JSON no tempo aceitável desse notebook. O perfil padrão usa extração fundamentada e `omnisvera-fast:latest`; o backend valida caminhos e evidências antes de aceitar qualquer afirmação. Para experimentar análise mais lenta, configure `OMNISVERA_QUALITY_MODEL=qwen3:4b` e `OMNISVERA_RESPONSE_MODE=grounded`.

Consultas exatas e listas estruturadas continuam determinísticas. No modo `fast`, perguntas abertas usam trechos recuperados com evidência literal. No modo `grounded`, o modelo recebe o contrato JSON rigoroso e toda afirmação sem evidência é descartada.

```powershell
$env:OMNISVERA_RESPONSE_MODE="fast"       # recomendado no notebook atual
$env:OMNISVERA_RESPONSE_MODE="grounded"   # usa o modelo de qualidade configurado
```

## Índice semântico

O índice semântico reaproveita o formato local já existente:

```text
.local-index/vault.jsonl
```

Cada linha possui:

```json
{"path": "Nota.md", "text": "trecho", "embedding": [0.1, 0.2]}
```

Esse índice não contém regras de visibilidade. Por isso, a busca híbrida sempre cruza cada `path` com o SQLite atual do Companion e aplica filtro player-safe antes de montar contexto para o chat.

## Atualização automática do corpo das notas

O SQLite do Companion pode se atualizar automaticamente quando você salva notas no Obsidian:

```powershell
$env:OMNISVERA_AUTO_REFRESH_INDEX="true"
$env:OMNISVERA_AUTO_REFRESH_INTERVAL_SECONDS="12"
```

Isso atualiza título, frontmatter e corpo das notas no app sem apertar “reindexar” manualmente. O intervalo evita que o backend escaneie o vault a cada clique.

Importante: isso não recalcula embeddings. Quando muitas notas mudarem e o chat semântico parecer antigo, reconstrua `.local-index/vault.jsonl` manualmente.

## Reconstruir índice

Se o índice estiver velho:

```powershell
python .local-tools/vault_tools.py --root . index
```

Depois reconstrua o índice SQLite do Companion pelo backend:

```powershell
Invoke-WebRequest -Method POST http://localhost:8787/index/rebuild -Headers @{ "X-Omnisvera-Token" = "<TOKEN_MESTRE>" }
```

## Ranking híbrido

Cada resultado recebe:

- `exact_score`: título, stem do arquivo ou alias igual/contendo a pergunta.
- `lexical_score`: correspondência em título, path, tags, alias e conteúdo.
- `semantic_score`: similaridade por cosseno entre a pergunta e chunks do índice semântico.
- `final_score`: soma ponderada para ordenar resultados.

O app não mostra scores para jogadores. Scores aparecem apenas em relatório técnico.

## Resposta fundamentada

No fallback RAG, o backend pede ao modelo um JSON com:

```json
{
  "fatos_confirmados": [{"fato": "texto", "fonte": "caminho da nota"}],
  "teorias": [{"teoria": "texto", "base": ["caminho da nota"]}],
  "informacoes_insuficientes": ["texto"],
  "fontes_usadas": ["caminho da nota"],
  "resposta_ao_jogador": "texto final"
}
```

Regras:

- fato precisa estar nas fontes enviadas;
- inferência vira teoria;
- ausência de contexto vira `informacoes_insuficientes`;
- modo jogador nunca recebe notas bloqueadas;
- JSON inválido tenta reparo uma vez e depois cai em fallback seguro.

## Testar

Validação completa:

```powershell
python scripts/validate_companion_hybrid_rag.py
```

Validação sem chamar o chat do Ollama:

```powershell
python scripts/validate_companion_hybrid_rag.py --no-chat
```

Relatório gerado:

```text
Workflow/_audit/App_RAG/HYBRID_RAG_VALIDATION.md
```

## Fallback lexical

Se a busca semântica ficar lenta ou o índice quebrar:

```powershell
$env:OMNISVERA_RAG_MODE="lexical"
```

Reinicie o backend depois de mudar variáveis.

## Limites de desempenho

Variáveis úteis:

```powershell
$env:OMNISVERA_RAG_CONTEXT_LIMIT="8"
$env:OMNISVERA_RAG_CONTEXT_CHARS="5200"
```

Para o notebook atual, prefira 5 a 8 trechos e contexto curto. Não gere embeddings de todo o vault a cada pergunta.
