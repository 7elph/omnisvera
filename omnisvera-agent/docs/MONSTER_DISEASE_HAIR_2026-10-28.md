# Febre do Esgoto e serpentes da Medusa

Fonte: textos locais SRD OD2 de Rato, Rato Gigante e Medusa em
`backend/app/data/old_dragon_srd_monsters.json` (atribuição CC BY-SA 4.0 preservada).
Nenhuma ficha, ataque salvo ou dado de campanha é migrado por este corte.

Febre do Esgoto usa o texto completo revisado: mordida confirmada, chance de
1 em 1d6, JPC evita, Constituição limitada a 1 por 1d6 dias. O efeito modifica
atributos derivados no motor atual; preserva ficha base e PV máximos, expira
pelo relógio ficcional nativo e respeita descanso completo aprovado da campanha.
Doença não é veneno: imunidades explícitas de Constructo, Vampiro e da ficha
são verificadas antes da chance. Falha na chance não rola JP nem duração;
imagens interceptadas e erros de ataque não transmitem a doença. Retry da
confirmação recupera o recibo sem nova chance/JP/duração. Sem atributo cadastrado,
o resultado exige arbitragem. Reinfecção não renova silenciosamente o efeito:
essa regra não está definida e permanece assistida.

O veneno da Medusa só é vinculado a uma **Mordida das serpentes do cabelo**
explicitamente cadastrada pelo Mestre. A fonte só traz Arco na lista de ataques:
este corte não inventa BA, dano, alcance ou ação adicional das serpentes. Quando
esse ataque existe, usa JPC e morte após 1d3 turnos de exploração, pelo executor
nativo existente. Arco e mordida genérica não inoculam esse veneno.

Continuam pendentes: BA/dano das serpentes no encontro padrão da Medusa; escopo
de acumulação/reset das chances por mordida de Otyugh; regras de reinfecção;
outras doenças sem contrato revisado; Ferrugem quando falta material/encantamento
da unidade equipada. Não foram presumidos valores nem classificações de itens.

Regressões: `test_monster_disease_hair.py`, além dos módulos existentes de
poison specs/runtime, riders e conditions runtime. Rodar o lote MCP e inspecionar
capturas continua necessário; estes testes focais não certificam UI ou mesa externa.
`attackOutcome.ts` apresenta a chance de transmissão e a duração em dias, sem
converter dias em rodadas nem inventar JP quando a doença não foi transmitida.

Validação focal: 90 testes backend aprovados (13 novos), 8 testes frontend de
resultado aprovados (2 novos). RED anterior foi observado em ambos os cortes.
Suíte integral, build, navegador e ativação operacional pertencem à validação
integrada do lote principal; este documento não os declara concluídos.
