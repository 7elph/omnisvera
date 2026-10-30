# Itens por família — primeiro corte executável

## Implementação

O catálogo continua sendo a fonte de identidade/preço. `app/item_families.py`
projeta seus números para o inventário e motores existentes, sem criar outro
sistema de itens. Os metadados são identificados por `family_schema: 1`.
São 71 entradas de armas (incluindo lançadores e casos especiais), 5 de
munição, 13 de armadura e 7 de escudo. Isso não significa 96 itens integralmente
automatizados: as limitações abaixo continuam válidas.

- Armas: dano numérico, modalidades, alcance, margem/multiplicador de crítico.
  Grisalma e exceções existentes continuam nos adaptadores nativos.
- Arcos/bestas: dano da munição compatível; prioridade determinística para
  munição normal antes da improvisada, depois pelo caminho do item.
  Um projétil por disparo, gasto ao confirmar, inclusive em erro.
  Retry da resolução/confirmação não gasta novamente. Sem munição não dispara.
- Bestas: recarga automática aprovada pelo Mestre; exige ainda não ter se
  movido e gasta todo o deslocamento do turno. Usa o orçamento nativo, inclusive
  na iniciativa antiga. Não permite agrupar dois disparos em uma única recarga.
  Fora de combate não há gasto de deslocamento de turno.
- Armaduras/escudos: encaixes corretos, CA, penalidade de deslocamento e teto
  do bônus de Destreza. As restrições explícitas das proteções Samurai usam
  o contexto de classe. Madu mantém o +1 CA expresso em seu cadastro.
- Uma referência defensiva é capturada no primeiro equipar/guardar intencional
  de proteção, para substituir equipamento incorporado à CA antiga sem somar
  duas vezes. Buffs temporários não viram base permanente. Não há migração
  automática de fichas; alterações posteriores de CA pelo Mestre são preservadas.
- Consumíveis: `on_use` estruturado do Vault usa o consumidor transacional
  existente: cura, restauração de recurso, PV temporários, condição simples.
  Mantém validações raciais, um consumível por turno, custos, auditoria e retry.
  Regras desconhecidas/condicionais não são interpretadas a partir da prosa.
- Inventário mantém ícones compactos. Munições mostram os projéteis restantes
  somando pacotes e não oferecem equipar; outros itens mantêm sua quantidade.

Os números básicos foram conferidos no PDF local **Old Dragon Aprimorada**,
pp. 54–55 e 58; as expansões conservam a atribuição já presente no catálogo.
Os campos fonte e `family_gaps` ficam disponíveis no registro/auditoria.
`runtime_support` informa projeção nativa básica; não certifica cada item.

## Limites explícitos

Não foi inventada uma terceira faixa de alcance: a prosa do livro fala em três
faixas, mas sua tabela fornece dois números. O alcance máximo é validado no
grid; penalidades por faixa continuam assistidas enquanto não houver decisão.
Mapas sem grid/posições preservam o comportamento assistido existente.

Continuam pendentes efeitos especiais sem contrato completo (rede, garrote,
dardos especiais, bloqueio direcional do escudo torre, ricochete do Vibranium),
escolha de tipo de dano em armas com tipos alternativos, recuperação física de
armas arremessadas e carga/encumbrância universal. Peso é metadado, não uma
certificação de carga automática. Condições simples por texto não equivalem
à automação de todas as durações mágicas. Não foram geradas novas artes.

Reparo mágico, revenda de objetos usados com condição e as demais famílias
continuam fora deste corte. A economia inteira do mundo não está certificada.

## Ensaios

Regressões em `backend/test_item_families.py` e
`frontend/tests/item-family-inventory.test.cjs`. O lote nativo
`--ui --ui-suite item_families`, com quatro atores, compra pelo jogador,
equipa proteções/arma, usa o consumível, dispara com munição, confirma retry,
recarrega e confere persistência. `inventory_summons` inclui também esse lote
após compra/venda/barganha/serviços e invocação em outro mapa.

Tudo usa `simulation.sqlite3` em TEMP, credenciais sintéticas e processos
pertencentes ao runner. Não autoriza mutações em fichas reais.
Resultados finais e ativação: em validação; atualizar após as verificações.
