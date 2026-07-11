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
| Chat local | `OLLAMA_MODEL` | `qwen3:4b` |
| Embeddings | `OMNISVERA_EMBEDDING_MODEL` | `nomic-embed-text` |
| Ollama | `OLLAMA_BASE_URL` | `http://localhost:11434` |

O backend chama o Ollama apenas em `localhost`. O celular conversa com o backend, não com o Ollama diretamente.

Use `qwen3:4b` como equilíbrio principal entre qualidade e velocidade. Use `omnisvera-fast:latest` quando a prioridade absoluta for velocidade e `omnisvera-local:latest` apenas quando a latência maior for aceitável.

No notebook atual, consultas exatas e listas estruturadas usam um caminho verificado sem geração para responder imediatamente. O Qwen 3 fica reservado para perguntas abertas. Seu raciocínio é mantido fora da resposta do jogador e possui limite de tempo e de geração para não travar o aplicativo.

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
