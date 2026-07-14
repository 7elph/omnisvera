# Auditoria da infraestrutura do modelo

| Componente | Existe | Executável | Testado | Falta |
|---|---:|---:|---:|---|
| Schema canônico 1.0 | sim | sim | sim | ampliar exemplos curados |
| Migração dos 12 legados | sim | sim | sim | revisão humana |
| Captura e curadoria | sim | sim | sim | uso contínuo no chat real |
| Aprovação/rejeição segura | sim | sim | sim | 1.000 aprovações |
| Duplicatas/conflitos/split agrupado | sim | sim | sim | dados reais suficientes |
| Frozen eval v1 | sim | sim | sim | revisão humana antes do treino real |
| Cobertura configurável | sim | sim | sim | metas ainda zeradas |
| LoRA/QLoRA | sim | condicionado | preflight | GPU, dependências e pesos licenciados |
| Full training | sim | protegido | preflight | máquina de cerca de 40 GB VRAM |
| Checkpoint/resume | sim | condicionado | configuração validada | execução real em GPU |
| Manifesto reproduzível | sim | sim | sim | manifesto de treino real |
| Merge | sim | condicionado | simulação | adapter real |
| GGUF/quantização | sim | condicionado | simulação | llama.cpp e modelo merged |
| Ollama/Modelfile | sim | sim | validação estática | GGUF candidato |
| Registro/promoção/rollback | sim | sim | sim | métricas candidatas |
| Integração baseline/candidate/production | sim | sim | testes do backend | modelo candidato real |

## Lacunas corrigidas

O pipeline anterior usava schema legado, split aleatório, `--allow-small`, full training como padrão, caminhos de scripts desconectados e nenhuma promoção segura. Esses pontos foram substituídos por schema estrito, curadoria explícita, split agrupado, confirmação experimental inequívoca, LoRA como padrão, CLI única, gates e rollback.

## Limites honestos

O notebook atual não possui CUDA nem dependências de treino. Nenhum loop real, checkpoint real, merge real ou GGUF real foi produzido. Os comandos foram validados até o preflight e por simulação segura; a execução pesada deve ocorrer em hardware adequado.

## Benchmark local curto

Três casos do frozen eval foram executados contra `qwen2:1.5b` e `llama3.2:3b`. O qwen passou 2/3 no verificador lexical em média de 17,19 s, mas inventou referências externas; o Llama-base passou 1/3 em média de 19,48 s e omitiu evidências. Portanto nenhum dos dois resultados justifica promoção. O avaliador passou a sinalizar nomes próprios ausentes do contexto e mantém revisão humana obrigatória para naturalidade, coerência e inferências sem correspondência lexical.
