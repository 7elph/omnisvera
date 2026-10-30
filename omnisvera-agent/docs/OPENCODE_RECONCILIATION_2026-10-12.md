# Companion — consolidação após OpenCode, 12/10/2026

## Estado recebido e conferido

Branch `devin/create-omnisvera-class-standard`, HEAD `1a07a84`, worktree misto.
Histórico local do OpenCode foi lido; decisões posteriores confirmam:
Vezemir/Morthak/Raziel/Dorn no nível 5, Varkh no 1; nove rolagens de PV
pendentes; Reserva de Sangue 10; magias exclusivas de Necromante com regras
oficiais; restauração de Força assistida pelo Mestre.

O OpenCode acrescentou tabelas e recalculação, escolha de especialização,
rolagens de PV na ficha, ataques de Dorn e módulos de Necromante. Confirmados
no SQLite operacional: níveis 5, Necromante em Morthak, nove solicitações de
PV, três usos de Mísseis em Dorn, quatro em Morthak, cenas arquivadas.
Nenhuma escolha de especialização foi feita por esta entrega.

## Falhas corrigidas nesta entrega

- Os cards de Toque Sombrio/Aterrorizar só consumiam o recurso genérico ou
  registravam texto. Agora abrem controles que chamam a técnica real.
- Toque: alcance declarado, alvo vivo, ataque de toque (+2, sem bônus da
  arma), prévia e confirmação; dano, consumo e dreno persistidos uma vez.
  d6/JPC são gerados dentro da transação da prévia, depois da checagem de retry.
- JP ausente deixou de ser falha automática. Dados incompletos rejeitam a
  conjuração antes de gastar; não fabricam resistência nem morte.
- DV da ficha prevalece sobre declaração. Só o Mestre fornece DV ausente;
  desconhecido exige configuração. DV fracionário e `1+1` são reconhecidos.
- Alvos ocultos, mapas privados, alvos repetidos e conjurador a 0 PV rejeitados.
- Aterrorizar aceita múltiplos alvos, aplica JP/efeito e gera registro público.
  Ataques e JP recebem -2; a adaptação existente dos testes de atributo ao
  sistema de rolagens do Companion foi preservada. Não se alterou a fórmula
  global dos testes de atributo para roll-under OD2.
- Mestre → Combate → Aterrorizar: avança turnos de exploração e encerra.
  Expiração é persistida e retira o ícone. Turnos de combate não reduzem essa
  duração. Dreno de Força continua manual até restauração pelo Mestre.
- Mísseis foi desbloqueado no nível 5. Contador mantido: 3 usos base, +1 pela
  Página de Grimório equipada em Morthak; Dorn continua com 3. Uma ativação
  consome um uso; não se multiplicou dano pelo contador diário. Fórmula anterior
  `1d4 + nível`, limitada a +5 conforme descrição existente, foi preservada.

Referências de ajuste de dificuldade:
[atributos](https://olddragon.com.br/livros/srd/capitulos/atributos),
[JP](https://olddragon.com.br/livros/srd/capitulos/personagem),
[ataques de toque e dificuldade](https://olddragon.com.br/livros/srd/capitulos/combate).
Não houve cópia de texto integral desses documentos.

## Validação

- Baseline recebido: 533 backend / 223 frontend PASS.
- Final: 550 backend / 227 frontend PASS; TypeScript PASS; build PASS.
- Novos testes reproduziram JP ausente, alvo oculto, DV adulterado e falta de
  registro público antes das correções. Testes adicionais cobrem retry, consumo,
  alvo morto-vivo, duração/expiração e custo de Mísseis no nível 5.
- Interface compilada, SQLite temporário 8871: Mestre + três jogadores,
  fichas mobile, reconexão sem reload, registro perdido e turno: PASS.
- Smoke Necromante em viewport 390×844: Toque → confirmação → custo,
  Aterrorizar → JP/efeito → persistência/reload → registro → expiração;
  Mísseis no nível 5 → um uso: PASS.
- Primeira execução do smoke esperou texto inexistente na confirmação;
  corrigido o teste para aguardar “Concluído” e reexecutado com sucesso.
- Assets da fixture copiados para Vault temporário, sem editar mídias reais.
  Isso não prova mídia total nem estabilidade em redes externas distintas.

## Como usar

Morthak → Ficha → Magias → Preparar magia. Selecione alvos e confirme alcance.
Toque abre a resolução normal de ataque; confirme para aplicar dano/dreno.
Aterrorizar resolve os selecionados; se o uso diário acabar, é necessário marcar
explicitamente o consumo de magia memorizada. Dados de DV/JP/FOR ausentes
exigem revisão da ficha do alvo pelo Mestre.

Mestre → Mesa → Combate → Aterrorizar: avançar um turno de exploração ou
encerrar efeito. PV pendentes: cada ficha → Rolar PV; Dorn é controlado pelo
Mestre. Vezemir escolhe a especialização na própria ficha, se desejar.

## Pendências de regras/conteúdo

| Área | Situação |
|---|---|
| Vezemir: Força/Velocidade, Pulseira | Comandos existentes; duração/consumo/JP automatizados; alcance assistido |
| Morthak: Adaga, Mísseis, invocações, duas novas magias | Fluxos operacionais; alcance e dados faltantes assistidos |
| Esqueleto: fogo 1d6 | Anotação aprovada sem +2; aplicação ainda manual, sem classificador de dano elemental |
| Raziel: Lâmina, Mordida, regeneração, forma, adagas | Fluxos existentes; Marca aprimorada e poderes bloqueados exigem regras da mesa |
| Dorn: ataques, Mísseis, demais magias, Reparo, protocolos | Fluxos existentes; geometria/peso/posição e algumas imunidades assistidos |
| Traços narrativos e memórias | Descrições/adjudicação, não comandos automáticos |
| Progressão além dos níveis conferidos | Propostas não aprovadas; não ativadas |
| Nove dados de PV | Permanecem pendentes; não rolados por agente |
| Vezemir: especialização | Escolha disponível; não escolhida automaticamente |
| Mesa em redes diferentes e todos os assets | Ainda sem prova completa |

## Arquivos alterados nesta entrega

`backend/app/combat.py`, `combat_effects.py`, `main.py`, `necromancer_spells.py`,
`schemas.py`; `backend/test_action_recovery.py`, `test_session8_necromancer.py`,
`test_necromancer_integrity.py`.

`frontend/src/api.ts`, `pages/SessionWorkspace.tsx`,
`components/NecromancerSpellControls.tsx`, `components/NecromancerEffects.tsx`;
`frontend/tests/necromancer-spells.test.cjs`, `necromancer-smoke.cjs`.

Documentos: este relatório, `CURRENT_COMPANION_CODE.md`,
`TABLE_CONTROLS_2026-10-11.md`, `PROGRESSION_16_20_PROPOSAL.md`.

## Ativação operacional

Backup anterior ao reinício:
`C:/Users/delib/AppData/Local/Temp/omnisvera-before-necromancer-fix-f10niai9`.
Backend 8787 reiniciado pelo lançador oficial: PID 18784, sem erros de startup.
Tailscale preservado; índice público HTTP 200 servindo `index-CsAP8NnV.js`.
Vezemir/Morthak/Raziel: GET pelo domínio público HTTP 200, acesso `owner`,
nível 5. Convidado: health 200, sem ficha associada. Varkh está marcado
`gm_controlled=true`, logo sua credencial de jogador é excluída pelo lançador
atual; não houve alteração desse estado. Dorn: ficha GM HTTP 200.

Comparação após restart confirmou igualdade de character_states,
character_definition_overrides, character_sheets, character_notes,
player_inventory, scenes, game_sessions, combat_effects e combat_effect_clock;
credenciais iguais ao backup. Combate inativo; só a cena 14 na lista.
As nove rolagens de PV e escolhas pessoais seguem pendentes.
Servidor QA 8871 encerrado. Warnings de bundle >500 kB e mídia incompleta
na fixture permanecem limites declarados; não são prova de falha no público.

Não atribuir todos os diffs desses arquivos a esta entrega: várias mudanças
anteriores já existiam. Sem commit/push.
