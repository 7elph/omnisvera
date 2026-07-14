# Llama-3.2-Omnisvera-3B — guia operacional

Estado atual: **infraestrutura pronta para coleta; dataset insuficiente; treinamento real bloqueado**.

O modelo aprende comportamento, não o cânone mutável. O vault e o RAG continuam sendo a fonte da verdade. Pesos, adapters, GGUF, checkpoints, caches e datasets reais não entram no Git.

## Arquitetura

- `omnisvera_model/`: pacote executável e modular.
- `omnisvera-model/config/`: configurações de smoke, LoRA e full training.
- `omnisvera-model/schemas/`: schemas canônicos de exemplos e personas.
- `omnisvera-model/data/`: estágios locais ignorados (`captured`, `approved`, `train` etc.).
- `omnisvera-model/evaluation/`: avaliação congelada sanitizada e gates.
- `omnisvera-model/ollama/`: Modelfile sem lore.
- `omnisvera-model/artifacts/`: manifests, adapters e modelos locais ignorados.

## Regra dos 1.000 exemplos

Treino real exige simultaneamente:

- 1.000 exemplos explicitamente aprovados;
- metas de cobertura atendidas;
- frozen eval publicado;
- zero vazamento conhecido;
- zero conflito crítico, duplicação grave ou contaminação;
- preflight de hardware e dependências aprovado.

Não existe `--force`. O smoke test usa a confirmação exata `I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION`; seus artefatos são inelegíveis para promoção.

## 1. Migrar e validar os 12 exemplos antigos

```powershell
python -m omnisvera_model migrate-legacy
python -m omnisvera_model validate-data --source omnisvera-model/data/candidates/legacy_seed_v1.jsonl
```

Eles entram como `pending`, nunca como aprovados.

## 2. Capturar uma resposta real

Exporte um diagnóstico player-safe do chat para JSON (veja `examples/capture_payload.example.json`) e rode:

```powershell
python -m omnisvera_model capture-example --input captura.json
```

Uma captura registra pergunta, perfil, contexto autorizado, respostas bruta/final, fatos, teorias, modelo, tempo e avaliação. Captura não entra no treino.

## 3. Corrigir, aprovar ou rejeitar

```powershell
python -m omnisvera_model review-example --source omnisvera-model/data/captured/chat_examples.jsonl --id ID --action edit --reviewer Sage --ideal-response "Resposta corrigida"
python -m omnisvera_model approve-example --source omnisvera-model/data/reviewed/examples.jsonl --id ID --reviewer Sage --quality-score 2
python -m omnisvera_model review-example --source omnisvera-model/data/captured/chat_examples.jsonl --id ID --action reject --reviewer Sage
```

Exemplo player com segredo ou marcador reservado é bloqueado. Aprovação exige revisor, resposta ideal e nota de qualidade.

## 4. Construir dataset e consultar cobertura

```powershell
python -m omnisvera_model coverage-report
python -m omnisvera_model build-dataset --version v0.1.0
```

O builder detecta duplicatas, quase duplicatas, conflitos e vazamentos; agrupa o split por entidade/persona/família; mantém o frozen eval separado; e gera manifesto. A divisão não é puramente aleatória.

## 5. Avaliação congelada

```powershell
python -m omnisvera_model freeze-eval
python -m omnisvera_model evaluate --models qwen2:1.5b llama3.2:3b --validate-only
```

Após publicação, não edite `frozen_eval_v1.json`; publique uma nova versão. Avaliação real usa o mesmo comando sem `--validate-only` e pode incluir base, adapter importado, merged/GGUF e modelo atual.

## 6. Preflight e treinamento

```powershell
python -m omnisvera_model preflight --config omnisvera-model/config/lora-production.json
python -m omnisvera_model train-lora --config omnisvera-model/config/lora-production.json
python -m omnisvera_model resume --config omnisvera-model/config/lora-production.json --checkpoint /caminho/checkpoint
```

O caminho principal é LoRA/QLoRA. Full training é avançado:

```powershell
python -m omnisvera_model train-full --config omnisvera-model/config/full-production.json --acknowledgement I_UNDERSTAND_FULL_TRAINING_REQUIRES_PRODUCTION_HARDWARE
```

Configs não baixam pesos automaticamente (`allow_model_download: false`). Em máquina remota, instale `requirements-train.txt`, obtenha acesso licenciado ao modelo-base e disponibilize os pesos no cache local. Cada execução cria preflight e manifesto com base/revisão, dataset/hash, seed, hiperparâmetros, ambiente, commit, checkpoints e métricas — sem texto secreto.

## 7. Smoke técnico

Prepare o ZIP experimental para Google Colab sem iniciar treinamento:

```powershell
python -m omnisvera_model prepare-colab --output omnisvera-model/dist/omnisvera-smoke.zip --acknowledgement I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION
```

O pacote contém somente exemplos aprovados e sanitizados, configuração smoke,
schemas, frozen eval e `colab/runner.py`. O diretório `dist/` permanece fora do Git.

Somente quando pesos e dependências já existirem localmente:

```powershell
python -m omnisvera_model train-lora --config omnisvera-model/config/smoke.json --acknowledgement I_UNDERSTAND_THIS_IS_EXPERIMENTAL_NOT_FOR_PRODUCTION
```

O resultado deve ser rotulado `EXPERIMENTAL_NOT_FOR_PRODUCTION` e não pode ser promovido.

## 8. Merge, GGUF e quantização

Os comandos são dry-run até receberem `--execute`:

```powershell
python -m omnisvera_model merge --base-model meta-llama/Llama-3.2-3B-Instruct --adapter /adapter --output /merged
python -m omnisvera_model export-gguf --model-dir /merged --converter /llama.cpp/convert_hf_to_gguf.py --output /Omnisvera-F16.gguf
python -m omnisvera_model quantize --source /Omnisvera-F16.gguf --quantizer /llama.cpp/llama-quantize --output /Omnisvera-Q4_K_M.gguf --type Q4_K_M
```

Também é suportado `Q5_K_M`. Tokenizer, chat template, BOS/EOS, contexto, hash e inferência devem ser validados antes de registrar o artefato.

## 9. Ollama

Coloque o GGUF ao lado de uma cópia do Modelfile e ajuste `FROM`:

```powershell
python -m omnisvera_model ollama-create --model llama-3.2-omnisvera-3b --modelfile omnisvera-model/ollama/Modelfile --execute
python -m omnisvera_model ollama-test --model llama-3.2-omnisvera-3b --execute
python -m omnisvera_model ollama-list --execute
python -m omnisvera_model ollama-remove --model llama-3.2-omnisvera-3b --execute
```

O Modelfile não contém lore. Personas alteram estilo, nunca conhecimento ou acesso.

## 10. Registro, promoção e rollback

Registre metadados locais do artefato e métricas. O registro fica em `artifacts/model_registry.json`:

```powershell
python -m omnisvera_model register --model-id omnisvera-3b-lora-v0.1.0 --metadata metadata.json
python -m omnisvera_model promote --model-id omnisvera-3b-lora-v0.1.0 --gates omnisvera-model/evaluation/promotion_gates.example.json
python -m omnisvera_model rollback
```

Promoção exige 100% de segurança, 30/30, nenhuma fonte inventada/vazamento, factualidade não pior, naturalidade melhor e fallback funcional. Experimental nunca pode virar produção.

## 11. Integração com o Companion

```powershell
$env:OMNISVERA_FAST_MODEL="qwen2:1.5b"
$env:OMNISVERA_QUALITY_MODEL="llama-3.2-omnisvera-3b"
$env:OMNISVERA_EMBED_MODEL="nomic-embed-text"
$env:OMNISVERA_MODEL_MODE="baseline" # baseline | candidate | production
```

- `baseline`: usa qwen2 atual.
- `candidate`: teste controlado do Omnisvera.
- `production`: somente após promoção; sem registro `approved`, o backend volta ao baseline.
- falha do Omnisvera: tenta qwen2;
- falha do Ollama: resposta factual determinística.

## 12. Personas

Crie arquivo conforme `schemas/npc_persona.schema.json`. `knowledge_policy` é sempre `rag_only`. A persona fornece voz, vocabulário, tom e comprimento; não concede acesso e não injeta fatos.

## Testes

```powershell
python -m unittest discover -s omnisvera-model/tests -p "test_*.py" -v
python scripts/test_grounded_response_validation.py
python scripts/test_narrative_composer.py
python scripts/test_chat_question_battery.py
```

## Primeiro treinamento real

Falta: curar 1.000 exemplos, cobrir as dez categorias, publicar a versão final do frozen eval, preparar máquina Linux/CUDA com VRAM adequada e dependências compatíveis. Até lá a classificação correta é **pronto para coleta**, não “modelo treinado”.
