# Monster passives — corte determinístico (2026-10-25)

O parser `passive_specs(monster)->dict` (schema_version 1) é puro, sem banco,
rede ou LLM. `monster_runtime.py` vincula os componentes aprovados ao combate
existente; parsing e automação completa continuam sendo estados distintos.

## Regras
- Imunidades apenas quando explícitas e positivas para um tipo canônico: `fire,cold,acid,lightning,poison,necrotic`. `imune a magia` com exceções vai para `pending`. Condicional/contexto desconhecido → `pending`. 
- Restrições baseadas em JP/saves ou "vantagem" não são mapeadas como resistência de dano.
- Resistências/vulnerabilidades só com fator quantitativo explícito (não inventado).
- Regeneração apenas valor positivo e intervalo "a cada rodada" explícitos; bloqueadores só quando declarados (fogo/ácido). Troll: `1/rodada` com `fire,acid` bloqueando. Sem automação de Falsa Morte/reconstituição em dias.
- Outros números na mesma descrição não viram cura. Sono/chance não viram dano.
- `sources` preserva nome/texto integral. `pending` registra as demais regras e razões. `coverage.family_complete` permanece false; 22 monstros têm algum componente suportado, não 22 fichas integralmente automáticas.

## Integração nativa

- `change_hp` aplica imunidade/resistência/vulnerabilidade de dano **tipado**.
  Neste corte, baforadas nativas e Relâmpago informam o elemento. Ataques e
  magias legados sem tipo declarado não passam a ganhar um elemento inferido.
- Regeneração ocorre antes do turno da criatura viva, uma vez por rodada do
  encontro. Dano não regenerável fica persistido no próprio `sheet_json`;
  fogo/ácido do Troll não voltam por regeneração, mas cura normal pode curá-los.
- Sem ressurreição automática, Falsa Morte, reconstrução de membros ou imunidade
  geral a magias/armas não mágicas. Essas cláusulas continuam assistidas.

## Baforadas

Seis fontes completas usam `combat_effects.monster_breath`: Dragões Azul,
Branco, Dourado, Negro, Verde e Vermelho. Dano, JP, geometria, alcance e três
usos diários vêm da descrição; o Negro explicitamente não causa dano regressivo.

No turno do monstro, clique no card e depois num pin para apontar a direção.
O servidor calcula a área, incluindo aliados; uma confirmação mostra todos os
afetados. Rola o dano uma vez e uma JP para cada criatura. Cancelar não gasta.
O comando valida versão, fonte, posições, turno e usos, persiste tudo numa
transação e reutiliza recibo, orçamento, ledger e realtime existentes.
Retry concorrente não repete dano/custo. Trocar de combate não recarrega usos;
somente o descanso geral explícito do Mestre os restaura.

Áreas usam centros dos tokens e metros do grid no plano 2D. Cones usam largura
e comprimento declarados; nuvem projeta seu retângulo (altura fica preservada
na especificação). Linha sem largura declarada usa provisoriamente centros
colineares no raio escolhido, sem inventar espessura. Não há paredes, cobertura,
altura, bloqueio de visão ou seleção de um ponto vazio neste corte.

Continuam assistidas: Cão Infernal/Destruidor/Drakold/Quimera (parâmetros ou
condições insuficientes), Dragão das Sombras (PV fracionário/sono), Dragão de
Ossos (Ghouls), Górgon (petrificação) e Golem de Ferro (contador de ataques e
geometria incompleta). UI informa pendências; não executa só parte dessas
baforadas fingindo resolução completa.

## Testes
```powershell
cd backend
..\.venv-observer\Scripts\python.exe -B -m unittest discover -s . -p test_monster_passives.py
```
Além do parser, `test_monster_runtime.py` cobre alcance/área, JP, dano, papéis,
turno, fonte/posição alteradas, usos/descanso, persistência e retry concorrente.
`frontend/tests/monster-combat-smoke.cjs`, no lote isolado `oct24`, exercita
card → grid → confirmação, cancelamento, efeitos, segunda página e reload.
Execução e revisão de capturas devem ser registradas separadamente: código de
teste não prova PASS, e duas páginas locais não certificam mesa multirrede.

## Arquivos e validação do corte

- Backend: novos `monster_runtime.py`/`monster_passives.py`; integração em
  `combat_effects.py`, `character_play.py`, `dorn_spells.py`, `main.py`,
  `schemas.py`, `action_range.py`, `spell_engine.py` e `monster_rules.py`.
- Frontend: `api.ts`, `attackOutcome.ts`, `pages/SessionWorkspace.tsx`,
  `components/MonsterAttackPanel.tsx` e `components/MonsterRules.tsx`.
- Testes: `backend/test_monster_runtime.py`, `test_monster_passives.py`,
  `test_monster_rules.py`; `frontend/tests/monster-combat-smoke.cjs`,
  `bestiary-rules-smoke.cjs`, `table-balance-oct24-smoke.cjs` e
  `attack-outcome.test.cjs`. Índice: `CURRENT_COMPANION_CODE.md`.
- Em 25/10: suíte backend **1.366 testes, OK, 1 skip**; frontend **410/410**;
  typecheck e build PASS. Permanecem avisos antigos de conexões SQLite em testes
  e de tamanho do bundle; não são falhas destes checks.
- Ensaio isolado `oct24` com os quatro atores: card/grid, cancelamento, uma
  confirmação, dados/JP/dano, imunidade, regeneração, retry, reload e segunda
  página local. Capturas 1440/390 exigem revisão explícita pelo agente; não
  certificam celular físico, redes externas nem a ficha inteira.

Ensaio final: **PASS**, com revisão visual explícita das quatro capturas de
confirmação/resultado em 1440 e 390 px. Evidência TEMP:
`omnisvera-sheet-test-_p77qtkj` e recibo
`omni-monster-automation-acceptance-20261025.json`.
Ativado em 25/10 após backup e comparação de 21 tabelas protegidas. As seis
tabelas de fichas/inventários/pins/combate também mantiveram os hashes de antes
dos ensaios. Apenas timestamps dos três mapas oficiais foram atualizados pelo
startup já existente. Acesso público/fichas 200, OpenCode saudável e build
servido conferido. Nenhum staging, commit ou push neste corte.
