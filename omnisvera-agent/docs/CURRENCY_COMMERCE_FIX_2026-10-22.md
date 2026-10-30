# Moedas, comércio e saque

- Compras/vendas não normalizam mais a bolsa inteira para platina. Pagamento
  usa moedas menores primeiro e só troca uma moeda maior quando falta troco.
  Recebimentos não criam platina; taxas existentes permanecem inalteradas.
- Saques com denominação explícita (`pc`, `pp`, `po`, `pl` ou nome inequívoco)
  entram diretamente na denominação correspondente da bolsa, na mesma transação
  da distribuição, com versionamento e auditoria. Retry não credita novamente.
- Moedas não têm encaixes nem podem ser equipadas. Moeda Misteriosa e outras
  relíquias não são dinheiro por terem “moeda” no nome; permanecem itens.
- Gemas, objetos valiosos e bolsas sem valor/denominação não são convertidos.
- `app/currency_recovery.py` é manutenção explícita, não automática no startup:
  exige distribuição original, quantidade restante e saldo esperado; zera apenas
  aquele registro de moeda e credita a bolsa atomicamente, com recibo por item.
  Uma recomposição opcional das denominações deve conservar exatamente o valor.

Caso observado: a compra da mochila de Raziel custou 5 PP. O saldo de 107 PO
foi reescrito como 1 platina + 7 PO; o recibo não indica perda de valor.
Os saques antigos identificados são 20 PO de Vezemir (`session-item:27`) e
13 PP de Raziel (`session-item:31`). A manutenção requer backup antes da aplicação.

Testes: `test_merchant`, `test_map_commerce`, `test_loot`,
`test_combat_loot_circuit`, `test_equip_slots`, `currency-inventory.test.cjs`.
Teste isolado não certifica compra real multicliente/mobile.

## Aplicação e validação

Recuperação aplicada após ensaio em cópia: Vezemir 125 PO + 25 PP; Raziel
105 PO + 33 PP. As duas entradas antigas ficam com quantidade zero, mantendo
o histórico. Nenhuma perda de valor na recomposição da platina; os únicos
créditos novos são os saques comprovados de 20 PO e 13 PP.
Backup privado: `TEMP/omni-currency-recovery-rny3t4yh/before.sqlite3`.
Hashes protegidos de fichas (exceto moedas), inventário restante, combate,
mapas, sessão e estoque ficaram iguais no ensaio e na manutenção.

- Backend focal: 42 testes PASS. Suíte completa tentada, mas interrompida
  antes de concluir; resultado completo INCONCLUSIVE, não PASS.
- Frontend: 384 testes PASS; typecheck e build PASS. Aviso preexistente de
  chunks acima de 500 kB permanece.
- Backend reiniciado preservando ambiente e credenciais; fichas HTTP 200 com
  os acessos dos próprios donos e saldos conferidos após reinício.
  Comparação pós-reinício encontrou somente `updated_at` renovado nos mapas
  oficiais Earthropo/Nimalia pelo startup; conteúdo, grid e pins inalterados.
- Frontend publicado sem remover chunks antigos; HTTPS externo 200 com HTML
  correspondente ao build. Nenhuma compra de QA nos personagens reais.
- Aceitação visual mobile/multicliente não executada neste corte.

Arquivos de produção: `merchant.py`, `loot.py`, `currency_recovery.py`,
`player_inventory.py`, guardas locais em `main.py`/`character_play.py`,
`pages/SessionWorkspace.tsx` e `pages/PlayableCharacterSheet.tsx`.
Cobertura: módulos backend citados acima, `test_current_sheet_inventory.py`
e `frontend/tests/currency-inventory.test.cjs`. Sem staging, commit ou push.
