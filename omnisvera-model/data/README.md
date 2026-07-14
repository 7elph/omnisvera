# Estágios locais do dataset

Os diretórios abaixo são criados automaticamente e ignorados pelo Git:

- `raw/`: importações sem validação;
- `captured/`: interações reais capturadas;
- `candidates/`: exemplos migrados ou sintéticos pendentes;
- `reviewed/`: exemplos corrigidos, ainda não aprovados;
- `approved/`: somente revisão humana explícita;
- `rejected/`: rejeitados com histórico local;
- `train/` e `eval/`: datasets derivados;
- `frozen_eval/`: cópias locais de avaliações publicadas.

`curated_examples.jsonl` é apenas a semente legada sanitizada. Sua migração produz 12 candidatos `pending`; ela não concede aprovação.
