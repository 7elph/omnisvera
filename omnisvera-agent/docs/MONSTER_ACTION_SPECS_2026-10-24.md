# Monster action specs (baforadas/sopros) — 2026-10-24

## Escopo
Adaptador declarativo determinístico para **apenas** baforadas/sopros presentes nos 255 monstros. Sem banco, rede ou LLM. Não transforma toda habilidade em executor.

## Função
`monster_action_specs(monster: dict) -> list[dict]` em `backend/app/monster_action_specs.py`

Cada spec contém:
- `id` estável, `name`, `family` = `breath`
- `source` com `monster_id`, `edition`, `url`, `license` (proveniência)
- `damage_formula` explícita **apenas** se a fonte permitir (por DV numérico não ambíguo ou dado explícito). Nunca inventado.
- `save`, `save_effect` (`halves` ou `negates` quando explicitado)
- `geometry` `shape`/dimensões em metros (`width_m`, `depth_m`, `radius_m`, `height_m`)
- `uses.maximum` e `recharge` (`day`/`combat`/`at_will`/`every_n_attacks`) conforme fonte
- `automation_status`: `specification_complete` ou `assisted`; `execution_status=not_bound` com `reasons` objetivos
- `description_full` preservada

## Cobertura real
- **15 habilidades de 14 criaturas** inventariadas entre os 255 monstros.
- **Dragão Dourado**: `11d10`, `JPD`, `halves`, cone `width_m=9` `depth_m=27`, `3/day`, `specification_complete` (não é executor).

## Regras
- Fórmula por DV só resolvida com `hit_dice` numérico não ambíguo (ex.: `11+11` → `11d10` quando texto afirma "igual ao número de seus dados de vida em d10").
- `caster_level` **não** vira lista de magias.
- Dado de chance/sono não tratado como dano.
- Casos ambíguos → `assisted` com razões objetivas.
- Preserva descrição integral e proveniência.

## Teste executado
```powershell
cd backend
..\.venv-observer\Scripts\python.exe -B -m unittest discover -s . -p test_monster_action_specs.py
```
**Resultado após revisão Codex:** `Ran 5 tests ... OK`.

Arquivos deste adaptador: `backend/app/monster_action_specs.py`, `backend/test_monster_action_specs.py`, `docs/MONSTER_ACTION_SPECS_2026-10-24.md`. Integração geral descrita em MONSTER_RULEBOOK_2026-10-24.md.
