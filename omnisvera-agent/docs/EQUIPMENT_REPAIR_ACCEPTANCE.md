# Equipamento, Reparo e seleção ilustrada — 07/10/2026

## Decisões de Sage

- Cinco acessórios para todos os personagens.
- Cinco kits para Dorn; Reparo consome um kit e cura 1d4 PV, sem limite diário. Descanso não repõe kits.
- Armas devem respeitar a modalidade selecionada ao equipar.
- Coruja, morcego e corvo aparecem com as imagens aprovadas dentro do dropdown da Forma da Noite.

## Causas e mudanças

1. Manto Primordial estava classificado como Armadura tanto no normalizador do backend quanto no heurístico do frontend, bloqueando-o junto da armadura de couro. Agora é Acessório, mantendo regras/efeitos existentes. Frontend respeita os slots informados pelo backend antes de inferir pelo nome. Limite de acessórios alterado de três para cinco em todas as fichas; sexto é bloqueado.
2. Backend e frontend tinham exceção explícita para Adagas de Espectro Fantasma: modalidade à distância era oferecida mesmo com slot corpo a corpo. Slots explícitos agora são exclusivos; armas antigas equipadas sem slot preservam o fallback de compatibilidade. Testes da antiga regra foram atualizados para a nova decisão, com verificações das duas modalidades.
3. Reparo reutiliza o endpoint idempotente existente: verifica um kit com quantidade positiva, reduz sua quantidade e aplica cura 1d4 limitada aos PV máximos na mesma transação. Retry não consome outro kit. Zero kits bloqueia. O card aparece em Recursos, mostrando a quantidade de kits e chamando Reparo, não decremento genérico. Retirado da lista genérica de habilidades para não duplicar controles. Magias não mudaram.
4. `NightFormSelector` é um dropdown recolhível com miniatura selecionada e três opções ilustradas. Botões acessíveis por teclado, seleção fecha o menu; não usa imagens dentro de `<option>`, que não é portável em celulares. Sem alterações globais de fonte/estilo.

## Arquivos

Backend: `app/main.py`, `player_inventory.py`, `character_play.py`, `construct_rules.py`, `dorn_mage.py`, `data/dorn7_mage3.json`.

Frontend: `src/pages/SessionWorkspace.tsx`, `src/components/NightFormSelector.tsx`.

Testes: `backend/test_attack_weapon_select.py`, `test_multiattack_effects.py`, `test_dorn_construct.py`, `test_equip_slots.py`, `test_equipment_updates.py`; `frontend/tests/raziel-vampire-powers.test.cjs`, `night-form-selector.test.cjs`, `night-form-visual.cjs`.

Alterações preexistentes, Vault e mídia preservados. Apenas linhas JSX extensas das áreas tocadas foram quebradas mecanicamente para permitir patches localizados.

## Checks executados

- Backend completo: `.venv-observer\Scripts\python.exe -W ignore::ResourceWarning -m unittest discover -s backend -p "test_*.py"`: **381/381 PASS**.
- Frontend completo: `node --test tests/*.test.cjs`: **147 PASS / 1 FAIL**, mesma falha preexistente de regex CSS de Mísseis Mágicos em `shared-attack-target.test.cjs`.
- `npx --no-install tsc --noEmit`: **PASS**.
- Build isolado em `C:\Users\delib\AppData\Local\Temp\equipment-resources-20261007-build`: **PASS**; aviso de chunks grandes.
- `git diff --check -- .`: **PASS**, apenas avisos LF/CRLF.
- QA do dropdown real com React/CSS e arquivos das imagens: **mobile 390×844 e desktop 1440×900 PASS**, todas as imagens carregadas, escolha das três formas, fechamento e ausência de overflow. Screenshot mobile também inspecionado. Evidências: `C:\Users\delib\AppData\Local\Temp\night-form-visual-NfATRu`.

## Operacional

Cinco kits registrados no inventário real de Dorn por ação autenticada GM de quantidade, sem cura. Backup: `C:\Users\delib\AppData\Local\Temp\dorn-five-kits-j7b6yc7r\before.sqlite3`.

O código novo e o build foram validados isoladamente, **não ativados no servidor operacional**. Backend em execução ainda usa a versão anterior e frontend servido não foi substituído. Limite novo, modo exclusivo, consumo/cura de Reparo e dropdown ilustrado dependem da atualização/reinício. Não houve commit, push ou reinício. Não declarar aceitação operacional/multicliente deste corte.
