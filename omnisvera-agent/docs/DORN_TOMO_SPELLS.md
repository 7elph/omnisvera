# Dorn — automação das magias do Tomo Arcano

## Fonte e escopo

Sage escolheu explicitamente o Tomo Arcano. Fonte lida: `C:\Users\delib\Downloads\Tomo de Magia Arcana - OD2.pdf`, páginas físicas 56, 58–59, 82; cegueira na página 53. Não se substituiu esse contrato pela versão divergente do LB1/SRD.

Estado inicial: branch `devin/create-omnisvera-class-standard`, HEAD `8f6444c13cbb55603d9e97699d47b0cbd0ba2a4d`, árvore já modificada, incluindo o corte anterior de progressão/Dorn e mudanças externas. Nenhum commit, push, reinício operacional ou atualização da campanha real neste corte.

## Implementação

Reutiliza `combat_effects`, o relógio/turnos, `effect_command`, a transação/cache de request_id, os recursos preparados de Dorn, o resolvedor de dados/JP e `change_hp`. Sem novas tabelas ou subsistema de habilidades. Comandos são exclusivos do Mestre. Em combate, conjurar exige o turno e a ação de Dorn; não pode coexistir com ataque pendente. Falhas tardias revertem dano/efeitos e consumo na mesma transação.

| Magia | Backend automático | Declaração do Mestre |
| --- | --- | --- |
| Levitação | Alcance 20 m/nível e peso 50 kg/nível validados; JPC para receptor involuntário; duração 600 s/nível; altura, subida/descida até 2 m/rodada; instabilidade de ataque à distância de personagem, de -1 até -5; estabilização; consumo | Peso, distância e receptor, movimento vertical por comando; plausibilidade espacial |
| Escuridão | Alcance 10 m/nível; raio registrado 4,5 m; duração 600 + 10 s/nível; cegueira/infravisão bloqueada registradas; penalidades de ataque/JP -5 e +5 contra alvo afetado; penalidades iguais não se empilham; expiração | Criaturas dentro da área, entrada/saída e encerramento/cancelamento do efeito |
| Relâmpago | Alcance inicial 40 + 10 m/nível; escolha 3×12 m ou 1,5×24 m; dano compartilhado 1d6/nível até 10d6; JPD por contato; metade arredondada para baixo se todas as JP passarem; dano normal máximo por criatura mesmo após reflexão; PV e uso persistidos | Trajetória, reflexões, alvos e número de contatos; consequências ambientais |

No nível 3: Levitação até 150 kg/60 m por 30 minutos; Escuridão até 30 m por 10 minutos e 30 segundos; Relâmpago até 70 m de ponto inicial, 3d6. Tempo é **ficcional**, não relógio real: rodada completa = 10 s; interface também permite avanço explícito de exploração. Repetir a mesma request não repete benefícios, consumo nem dano.

As descrições/status das três magias no build Dorn-3 são atualizados na leitura, sem sobrescrever recursos nem reaplicar a migração da ficha.

## Limites comprovados — não chamar de automação total

- Sem inferência geométrica, escala de mapa, colisão, fog ou área dinâmica. A marca de visão bloqueada não gera máscara gráfica no mapa.
- Levitação atualmente aceita criaturas com ficha/PV, não objetos sem ficha. Não calcula dano de queda, apoio em paredes nem bloqueio de armar bestas médias/pesadas. Instabilidade automática está ligada ao ataque `ranged` de personagem; ataques particulares de monstros não receberam essa classificação.
- Escuridão não detecta automaticamente passagem pela borda nem conjuração de Luz/Luz Contínua. Mestre encerra o efeito existente quando essa interação ocorre. Não foi criado sistema de iluminação paralelo.
- JP usa JP e atributos persistidos da ficha. Este ensaio não comprovou modificadores de equipamento para receptores das novas magias.
- Sem ativação no banco operacional. É necessário validar o build aprovado de Dorn no ambiente real antes de uso na mesa. Nenhuma migração é executada em leitura/startup.

## Arquivos deste corte

- `backend/app/dorn_spells.py`: resolvedores e comandos transacionais.
- `backend/app/combat_effects.py`: relógio, modificadores e dispatch dos comandos.
- `backend/app/combat.py`: alvo afetado por escuridão e rastreamento de ataque à distância sob levitação.
- `backend/app/schemas.py`: comandos novos no contrato existente.
- `backend/app/data/dorn7_mage3.json`, `backend/app/character_play.py`: descrições/status aprovados das magias; demais alterações nesses arquivos pertencem ao corte anterior e foram preservadas.
- `frontend/src/components/DornSpellControls.tsx`, `DornSpellEffects.tsx`: seleção, confirmação, resultado e controles dos efeitos.
- `frontend/src/pages/SessionWorkspace.tsx`, `frontend/src/api.ts`: integração GM e campos de efeitos; preservadas mudanças anteriores.
- `backend/test_dorn_spells.py`, `frontend/tests/dorn-spells.test.cjs`, `frontend/tests/dorn-spells-visual.cjs`: regressões e QA descartável.

## Validação executada

- `.venv-observer\Scripts\python.exe -W ignore::ResourceWarning -m unittest discover -s backend -p "test_*.py"`: **375/375 PASS** (97,635 s).
- `node --test tests/*.test.cjs` em frontend: **145 PASS / 1 FAIL**. Única falha preexistente: `shared-attack-target.test.cjs`, regex de CSS que exige formatação antiga do card de Mísseis Mágicos. Não alterada/enfraquecida neste corte.
- Testes específicos: backend **14/14 PASS**; frontend **4/4 PASS**.
- `npx --no-install tsc --noEmit`: **PASS**.
- `npm run build -- --outDir C:\Users\delib\AppData\Local\Temp\dorn-tomo-spells-20261007-final`: **PASS**, aviso existente de chunks grandes.
- `git diff --check -- .` no Companion: **PASS**, avisos LF/CRLF não são erros de whitespace.
- `node tests/dorn-spells-visual.cjs` com runtime Playwright disponível: **PASS** mobile 390×844 e desktop 1440×900. Componentes React reais hidratados e CSS do produto, três formulários, campos, confirmação, resultado, controles de efeito e ausência de overflow horizontal. API fixture: não equivale a teste operacional/multicliente. Primeiro ensaio falhou por `crypto.randomUUID` ausente em about:blank da fixture; corrigida somente a fixture, não produto.
- Screenshots: `C:\Users\delib\AppData\Local\Temp\dorn-spells-visual-RjgiNl`; mobile de Relâmpago também inspecionado visualmente.

Resultado: automação de resolução e estado implementada; geometria, interações ambientais e os limites listados permanecem assistidos. Não há evidência para declarar aceitação operacional ou suíte frontend integralmente verde.
