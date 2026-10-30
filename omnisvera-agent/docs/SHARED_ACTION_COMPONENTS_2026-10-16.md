# Segundo contrato: Reflexos

Reflexos usa metadata em `dorn7_mage3.json:action_contracts.reflexos`, separada
de `SPEC.abilities`: ler a definição não concede magia, item ou recurso.
`native_action_contract('technique:dorn7:reflexos', nível)` resolve o contrato.
O lookup de descrição pode consultar `dorn_abilities()` sem reconciliar fichas.

Contrato strict com executor allowlisted `dorn_reflexos`, alvo próprio único,
alcance zero, recurso `dorn_reflexos`1/descanso, duração `fictional_time` e efeito
`mirror_images`. Não há dano ou JP fabricados. A definição produz:

- `resolution.images = {dice: '1d4', add: 1, multiplier: 1}`;
- `resolution.lifetime = {dice: '1d6', add: nível, multiplier: 600}`;
- interceptação nativa existente: 50% de um ataque que acerta, nunca área.

Campos extras, binding estranho, tipos JSON trocados e fórmulas fora dos limites
são rejeitados. Sem eval, código, SQL ou execução de texto de PDF.

## Componentes e compatibilidade

`action_components.py` oferece verificação de revisão, rolagem limitada com RNG
nativo e consumo de recurso dentro da mesma conexão/transação do comando.
O consumo relê o estado mais recente, preserva PV e demais campos, incrementa
versão, rejeita overspend e nunca faz commit nem cria recibo paralelo.
Relâmpago e o pacote Dorn reutilizam esse consumidor. Os handlers continuam
responsáveis por autorização, turno, grid, efeitos, ledger e realtime.

Reflexos verifica `definition_revision` antes de RNG/consumo. Sem o campo,
clientes antigos continuam no fluxo nativo. Retry é recuperado pelo recibo
existente antes de executar novamente. O resultado inclui
`protocol_result.action_contract = {ref, revision, level}`.
Describe retorna contrato e bloco de condição, mas `executable=false` na rota
genérica: só o comando autorizado `dorn_spell_cast` executa.

Os quatro RED iniciais reproduziram ausência de contrato, metadata, bloqueio de
revisão e consumidor. Testes extras cobrem metadata sem concessão, schema strict,
rollback/versão e custo inválido. Validação focada inclui Relâmpago, pacotes Dorn,
escala/mapa e biblioteca. Integração da ficha/UI e ensaios HTTP/visuais são do
coordenador; não houve ativação operacional neste lote.

Resultado focado final: **55/55 PASS** em `test_shared_action_components`,
`test_lightning_contract`, `test_dorn_approved_pack`, `test_dorn_spell_map_scope`,
`test_dorn_spells` e `test_action_library`. `git diff --check` limpo. Avisos
preexistentes de depreciação FastAPI permanecem. Sem suíte completa ou UI neste
subcorte.

## Continuação: sete ações com contrato nativo

O lote seguinte acrescenta Força Arcana, Teia e Dissipar Magia de Dorn,
mais Força Arcana e Velocidade de Vezemir. São **sete ações**, não a migração
integral das fichas/catálogos. Os handlers passam a consumir metadados resolvidos
para suas fórmulas, duração, escala/alcance e custos, sem um executor paralelo.

- Dorn: Força usa FOR original/5, toque de uma célula; Teia preserva área
  3×3×6 m e duração nativa; Dissipar preserva JP/teste e valida efeito arcano.
  Mesmo orçamento principal, transação, ledger e recibos.
- Vezemir: ambos os buffs continuam em si mesmo, com recurso diário e
  `native_resource_turn_gate`. A descrição antiga de toque não amplia o handler
  para aliados; tampouco se inventou consumo de ação principal neste corte.
- Revisão divergente é rejeitada antes de rolar/consumir. Em Vezemir, também
  antes da leitura legada que poderia reconciliar recursos. Retry confirmado
  continua recuperando o recibo anterior antes de interpretar a revisão.
- A ficha efetiva projeta os mesmos contratos para habilidades já presentes;
  a projeção não concede habilidades. Controles de magia de Dorn enviam revisão.
  O caminho direto de `SessionWorkspace.tsx` ainda é legado: a tentativa de editar
  esse arquivo falhou na escrita, sem mudança de ACL ou outra forma de contorno.
  O backend mantém compatibilidade com comandos sem revisão.

Novos testes determinísticos cobrem rejeição precoce, custo, preservação de PV,
rollback, concorrência/retry, orçamento e ausência de concessão por leitura.
Ativação e ensaio MCP são marcos separados, registrados no relatório da retomada.

## Continuação: dez ações, quatro fichas

Clonagem e Magia da Morte usam `morthak_action_contracts.py`; Sangue Defensivo
usa `raziel_action_contracts.py`. Definições seguem no catálogo existente.
Não há interpretação de prosa, novo sistema de turnos ou concessão em GET.

Clonagem conserva componente consumível e contagem por círculo, não por nível
de personagem; os novos efeitos congelam alcance/duração validados. Efeitos
legados conservam os valores anteriores. Magia da Morte mantém aliados
elegíveis, JPC, DV e proximidade. Consumo usa estado mais recente na transação,
sem sobrescrever consequências de hooks. Sangue Defensivo mantém +2 CA/custo 2/
uma rodada e não gasta ação principal; replay autorizado precede forma/revisão.

Testes de integração com catálogo e DTO reais detectaram e corrigiram metadata
ausente em Raziel. Os testes de rota não substituem o resolver por um mock.
Migração dos demais ataques, riders, passivas e técnicas permanece incompleta;
handlers nativos continuam disponíveis. Checks e ativação: relatório da retomada.
