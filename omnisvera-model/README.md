# Llama 3.2 Omnisvera 3B

Este diretório prepara um modelo derivado e realmente treinado para o Omnisvera Companion.
O objetivo é um único motor conversacional, hoje como Arquivo Vivo e futuramente como
voz de NPCs controlada por cartões de persona.

## O que entra nos pesos

- português brasileiro natural;
- resposta fundamentada em cartões factuais;
- distinção entre fato, teoria e informação ausente;
- segurança entre Mestre e Jogadores;
- recusa natural quando falta evidência;
- interpretação de intenção sem transformar ação em cânone;
- obediência a uma persona de NPC e ao seu escopo de conhecimento.

Lore mutável, missões, relações e estado atual continuam no RAG. Treinar toda a lore nos
pesos faria o modelo envelhecer sempre que uma nota fosse editada.

## Hardware

O notebook atual é adequado para inferência do GGUF quantizado, construção do dataset e
testes. Um full fine-tuning de 3B precisa de uma GPU externa com aproximadamente 40 GB ou
mais de VRAM. LoRA normalmente exige bem menos, mas também deve ser treinado fora da
GeForce 920MX de 2 GB.

O modo `full` é o objetivo final. O modo `lora` permite validar o dataset mais barato;
depois o adapter pode ser mesclado ao modelo-base e exportado como um único modelo.

## Dataset

Os exemplos curados ficam em `data/curated_examples.jsonl`. Cada linha possui:

- `id` único;
- `category`;
- mensagens `system`, `user` e `assistant`;
- verificações de conteúdo obrigatório e proibido.

Gerar a divisão de treino e avaliação:

```powershell
python scripts/build_omnisvera_training_dataset.py
```

Enquanto houver menos de 1.000 exemplos curados, use apenas para validar a infraestrutura:

```powershell
python scripts/build_omnisvera_training_dataset.py --allow-small
```

## Treinamento

Em uma máquina Linux/CUDA com acesso autorizado ao modelo-base da Meta:

```bash
pip install -r omnisvera-model/requirements-train.txt
python scripts/train_omnisvera_model.py --mode full
```

Para uma prova de conceito LoRA:

```bash
python scripts/train_omnisvera_model.py --mode lora
python scripts/merge_omnisvera_adapter.py
```

## GGUF e Ollama

Depois do treino/merge, converter o diretório Hugging Face com o `llama.cpp`:

```bash
python /caminho/llama.cpp/convert_hf_to_gguf.py \
  omnisvera-model/artifacts/merged \
  --outfile omnisvera-model/artifacts/Llama-3.2-Omnisvera-3B-F16.gguf \
  --outtype f16

/caminho/llama.cpp/llama-quantize \
  omnisvera-model/artifacts/Llama-3.2-Omnisvera-3B-F16.gguf \
  omnisvera-model/artifacts/Llama-3.2-Omnisvera-3B-Q4_K_M.gguf \
  Q4_K_M
```

Copiar `.ollama/Modelfile.omnisvera-llama.template` para junto do GGUF, ajustar o caminho
e criar o modelo:

```powershell
ollama create llama-3.2-omnisvera:3b -f .ollama/Modelfile.omnisvera-llama.template
```

## NPCs

NPCs não exigirão um modelo por personagem. O mesmo motor recebe um cartão de persona
validado pelo backend, contendo voz, conhecimentos permitidos, atitude e limites. O RAG
continua decidindo quais fatos aquela voz pode conhecer.

## Regra editorial

Nenhum dado de Mestre deve entrar no dataset player-safe. Exemplos de segurança podem
ensinar a recusar um segredo, mas não devem incluir o segredo real na resposta esperada.
