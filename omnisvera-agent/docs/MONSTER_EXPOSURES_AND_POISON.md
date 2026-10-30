# Olhar, gás e venenos complexos

O corte reutiliza grid, confirmação, JP, PV, efeitos, relógio ficcional,
ledger, realtime e recibos existentes. Não cria outro sistema de turnos.
`monster_exposures.py` descreve exposições; `monster_poison_specs.py` interpreta
os textos locais; `monster_poison_runtime.py` aplica e acompanha os venenos.
O OpenCode implementou o parser e seus testes; a integração e a revisão usam
também os textos reais e cópias com IDs diferentes.

## Uso no combate

O Mestre clica no card da criatura, seleciona o pin no alcance e confirma.
Olhar exige confirmação explícita de contato visual direto; o Basilisco aceita
também o próprio reflexo. Estar perto não comprova contato visual. Esse comando
registra a exposição arbitrada pelo Mestre sem consumir a ação principal;
uma regra geral de custo ofensivo do olhar continua sem definição aprovada.
Não há detecção automática de visão, paredes ou reflexos.

Gás usa a ação normal e inclui todos os participantes vivos na área, inclusive
aliados, com imunidade/JP individuais. O raio é medido entre os centros lógicos
dos pins, em metros do mapa. A confirmação rejeita definição/posições alteradas.
Retry reutiliza o recibo: não repete dano, JP, condição ou carga.
O alcance consulta os PV atuais da ficha para personagens: uma cópia antiga
de PV no pin não torna um personagem recuperado um alvo morto, nem o contrário.

| Fonte | Automação |
| --- | --- |
| Basilisco | Olhar de 15 m; JPC; petrificação até remoção |
| Medusa | Olhar de 15 m aprovado; JPC; petrificação até remoção |
| Górgon | Gás de 10 m; JPC; petrificação até remoção mágica aprovada |
| Golem de Ferro | Gás de 6 m, 3d6, JPD reduz à metade; disponível após sete ataques confirmados |
| Centopeia/Vespa gigantes | Perda imediata de 1d4+2 CON após falhar a JP |
| Cérbero | Perda periódica de DEX; morte em zero conforme a fonte |
| Drider | Perda periódica de DEX até 3; sem morte inventada |
| Naga Negra | Perda periódica de INT; morte em zero conforme a fonte |
| Homúnculo/Sibilante | Atraso em rodadas, seguido de sono/paralisia pela duração em turnos |
| Roper | Atraso de 1d3 turnos, seguido de FOR pela metade por 2d4+1 turnos, conforme aprovação |
| Wyvern | Veneno mortal com prazo de 1d6+2 rodadas, conforme a fonte |

Os venenos ligados a ataques entram automaticamente no acerto confirmado;
não recebem um segundo botão de aplicação. Uma imagem ilusória interceptada
não recebe veneno. Infecção de Otyugh não é convertida em veneno.

## Relógio, atributos e persistência

Rodada = 10 segundos; turno de exploração = 600 segundos, conforme o relógio
atual. Não se converte turno de exploração em rodada de combate. Atraso e
duração são rolados uma vez na aplicação. Avançar um intervalo grande processa
início e fim em ordem; encerrar combate não apaga um veneno ainda vigente.
Remoção explícita ou descanso completo do personagem interrompe o efeito.

O dreno modifica atributos derivados, sem reescrever ficha ou progressão.
FOR afeta acerto/dano corpo a corpo, inclusive ataques numerados de NPCs com
atributos cadastrados; DEX afeta acerto à distância e os testes/JP
que já usam o atributo. A metade usa o piso inteiro do motor. Atributo ausente
em NPC produz aviso de arbitragem, sem presumir valor 10. Redução de atributo
não inventa alterações de PV máximo, CA, iniciativa manual ou outros sistemas
sem integração definida. O cálculo de JP lê atributos persistidos, overrides
e efeitos; não introduz uma nova leitura de bônus de atributo de equipamentos.

Efeitos, atrasos, dreno e cargas persistem em SQLite. O payload público expõe
status e consequências; omite blueprint do veneno e identificadores técnicos
da fonte. Ledger de criaturas ocultas continua privado do Mestre.

## Validação e limites

Testes determinísticos: contratos/fontes, imunidade/JP, relógio, limites do
dreno, preservação da ficha, privacidade, confirmação e retry. O lote isolado
`oct24` contém dois scripts fixos: regressão das quatro fichas e ensaio dos
novos efeitos no grid, em 1440/390 px. Conserva 300 s por script, teto de 20 min
e admissão de 1024 MB livres. Recibos e capturas ficam somente em TEMP.

A execução do ensaio e a inspeção das capturas são provas separadas. Código
do teste não certifica execução, ficha inteira, celular físico ou redes distintas.
O veneno das serpentes do cabelo da Medusa ainda exige um ataque/gatilho
configurado; não é aplicado pelo olhar nem pelo ataque de arma dela.
Conjuração completa dos monstros, doenças e textos sem parâmetros suficientes
continuam assistidos. Ícones de status existentes são reutilizados.

Arquivos do corte: contratos/runtime em `backend/app/monster_exposures.py`,
`monster_poison_specs.py`, `monster_poison_runtime.py`, `monster_runtime.py`,
`monster_conditions.py`, `monster_riders.py`, `monster_rules.py` e
`data/monster_condition_rules.json`; integração em `combat.py`,
`combat_effects.py`, `dorn_spells.py`, `action_range.py`, `main.py`, `spell_engine.py`.
Frontend: `api.ts`, `attackOutcome.ts`, `companionTheme.css`,
`pages/SessionWorkspace.tsx`, `components/MonsterAttackPanel.tsx` e `MonsterRules.tsx`.
Cobertura: quatro arquivos `test_monster_poison*`/`test_monster_exposures.py`,
`test_action_range.py`, `test_sheet_runner_batches.py`, `scripts/run_sheet_test.py`,
`frontend/tests/monster-conditions.test.cjs`, `monster-exposure-poison-smoke.cjs`.
Documentação: este registro, `CURRENT_COMPANION_CODE.md` e `AI_TEST_TOOLS.md`.

Validação executada: backend **1464 testes OK, 1 omitido**; frontend
**414 PASS**; TypeScript e build PASS. Lote nativo `oct24` PASS: regressão das
quatro fichas e novos efeitos em 1440/390 px, sem mutações operacionais.
Recibo: `TEMP/omnisvera-sheet-test-6emqbs11/sheet-test-report.json`;
aceitação visual separada, ligada ao hash do relatório: `visual-acceptance.json`.
Em mapas densos, os rótulos de PV ainda se sobrepõem em zoom 100%; a presença
dos pequenos ícones é testada, mas sua legibilidade em celular físico não foi
certificada. Este resultado não certifica toda habilidade ou toda ficha.

Ativação concluída no backend 8787: health, acesso das três fichas por seus
próprios tokens, Dorn pelo Mestre, índice HTTPS e novos bundles retornaram 200.
OpenCode preservado. Comparação de 23 tabelas preservou fichas, inventários,
sessão, efeitos e grid; apenas `updated_at` dos três mapas oficiais mudou.
Backup: `TEMP/omni-monster-rules-activation-r2snw9dj/before.sqlite3`.
Recibo: `TEMP/omni-exposure-activation-control-pybburd9/receipt.json`.
Nenhuma ficha real foi usada para ações de ensaio. Sem staging, commit ou push.
