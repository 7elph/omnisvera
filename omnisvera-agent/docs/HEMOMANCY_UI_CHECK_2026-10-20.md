# Hemomancia — ensaio isolado de 20/10

Resultado: **PASS no escopo selecionado**, não certificação integral da ficha.

- Recibo: `test-cc6ecbce7ed04e6badad2b10c024568c`.
- Request idempotente: `codex-friday-hemomancy-ui-20261020-v1`.
- Quatro atores na fixture, `ui:true`, `ui_suite:hemomancy`.
- 9 cenários API PASS: básicos e habilidades de Arco, Foice, Marreta e Lança;
  Escudo. Sem FAIL ou bloqueio esperado neste lote.
- UI: `hemomancy-weapons-smoke.cjs` PASS (129,242 s) e
  `hemomancy-weapons-second-smoke.cjs` PASS (62,828 s).
- Total do job: 316,97 s, exit 0.

## Caminhos realmente exercitados pela interface

Arco básico, Tiro do Coração, Ceifa Rubra, Ruptura Óssea, Estocada Transfixante
e Bastião Carmesim. Marca Rubra também foi usada nos dois casos do Arco.
Não afirmar nove caminhos UI: são nove API e seis usos de Hemomancia UI.

Asserções: cancelar não gasta; uma confirmação gera um comando; custo de sangue
correto; confirmação automática de ataque; estado persiste após reload;
segunda página local observa o gasto sem reload explícito. Seções Habilidades
e Poderes têm os cinco botões ativos/passivas correspondentes; ler passiva
não executa ação. Capturas 390 px e 1440 px revisadas, sem sobreposição evidente
nos trechos verificados. A última passiva é acessível ao rolar.

## Operação e limites

Somente o conector MCP foi recarregado com autorização, pois o schema anterior
não aceitava a suíte. Companion e OpenCode não reiniciaram. Modelo, credenciais,
permissões e dados operacionais preservados. Sem código de aplicação alterado,
commit ou push. Fixture encerrada; nenhuma escuta 8871 após o teste.

Relatório estruturado: `all_actions_certified:false`; certificação INCOMPLETE.
Este lote não prova todos os gatilhos de passivas, crítico/sangramento em todos
os casos, todos os caminhos da ficha, imagens completas, celular físico ou
Mestre/jogadores em redes distintas. Evidências brutas e banco ficam no TEMP
privado do runner, fora do Git. Suítes completas/typecheck/build não repetidos
nesta etapa operacional/documental; não houve mudança de implementação.
