# Raziel — separação de armas, habilidades e poderes

## Organização solicitada

- Hemomancia: seletor das cinco armas e uso básico, sem seletor de ações nem
  bloco repetido de habilidade/passiva.
- Habilidades: Caixão, Mordida, Forma da Noite, Regeneração Vampírica, Marca Rubra,
  Tiro do Coração, Ceifa Rubra, Ruptura Óssea, Bastião Carmesim e Estocada Transfixante.
- Poderes vampíricos: Mira Predatória, Carrasco, Trauma Profundo, Revanche Rubra
  e Ferroada Arterial. São automáticas, com descrição e sem comando de uso.
- Traços e fraquezas raciais, equipamentos e outras fichas preservados.

`razielSheetAbilities` projeta estas seções usando o pacote privado já fornecido
pelo backend. Não concede habilidades quando o pacote não está disponível e não
altera catálogo, inventário, recursos persistidos ou regras. Cards legados das
duas seções são ocultados, não apagados do servidor. A regeneração continua ativa.

Cada card novo usa o comando nativo da arma correspondente, seleciona alvo no
grid e confirma pelo fluxo existente. A invocação/custo continuam validados pelo
backend; usar Ceifa, por exemplo, não exige selecionar Foice antes no outro card.
O custo mostrado inclui invocação se a arma ainda não estiver ativa. Escudo e
Bastião são duas entradas para a mesma defesa existente, não dois bônus cumulativos.

Complemento solicitado depois da separação: Marca Rubra foi recolocada como
décima ativa, com contador da Reserva de Sangue. Tiro do Coração mantém +2 de
acerto contra o alvo marcado. Comando, validações e evidências novas em
`RUBRA_MARK_2026-10-18.md`; resultados abaixo são do corte anterior, com nove ativas.

## Verificação

- RED/GREEN: projeção exata de nove ativas e cinco passivas, quatro mantidas,
  ausência de mutação dos dados/alteração das outras fichas e custo de invocação.
- Testes focados: 13 PASS.
- Backend: 1.067 testes OK, um skip de symlink por permissão do Windows.
- Frontend: 336 testes PASS; typecheck e build PASS (aviso pré-existente de bundle).
- UI isolada `xe0v_22i`: quatro cenários API PASS e dois blocos UI PASS
  (235,564 s / 116,401 s), seis ativações nas cinco armas. Os especiais foram
  disparados pelos novos cards em Habilidades, inclusive com outra arma
  selecionada inicialmente. Leitura das passivas não executou ações; zero comandos
  de ativação em Poderes. Cancelamento, custo, confirmação nativa, reload e
  segundo cliente local preservados. Capturas desktop/390 px e das seções com
  nove ativas/cinco passivas revisadas explicitamente. Mídia legada não certificada.
- Bundle novo servido no Companion e endereço público HTTP 200.
- Somente frontend; nenhum restart ou alteração do banco operacional necessário.

## Arquivos

`frontend/src/components/hemomancySelection.ts`, `pages/SessionWorkspace.tsx`,
`companionTheme.css`, `frontend/tests/raziel-sections.test.cjs`,
`hemomancy-weapons.test.cjs`, `hemomancy-weapons-smoke.cjs`,
`raziel-blood-resource.test.cjs` e documentação relacionada.

Sem staging, commit ou push. Teste isolado não certifica mesa em redes distintas.
