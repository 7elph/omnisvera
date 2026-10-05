# Checkpoint: rótulos de efeitos de combate

## Defeito e correção comprovados

`CombatEffectsPanel` exibia `undefined +3` para o modificador persistido
`strength_bonus`, embora o backend aplicasse o efeito corretamente. O problema
foi observado nas interfaces do jogador e do Mestre durante a aceitação S6.

A correção acrescenta somente os rótulos `Força` e `Multiplicador de movimento`
ao dicionário de apresentação. O segundo corresponde a `movement_multiplier`,
também permitido pelo backend e sem rótulo anterior. Não altera cálculos,
permissões, duração dos efeitos nem os cinco controles existentes do editor GM.

## Evidência já obtida

- Dois testes de renderização, GM/player, falharam antes e passaram após o patch.
- Testes verificam rótulos legíveis, ausência de `undefined`, ocultação de zero
  e preservação dos controles de edição.
- Repetição na UI com build descartável mostrou `Força +3` nas duas perspectivas.
- Última validação completa do frontend: 88/88 PASS; TypeScript, build e diff
  check PASS. A validação backend completa anterior passou 278/278.
- Esses resultados são de execuções anteriores documentadas; nenhum teste foi
  reexecutado apenas para este checkpoint.

## Limite do checkpoint

Inclui exclusivamente o componente, seus dois testes e esta nota. A autorização
do usuário desvinculou este checkpoint da confirmação visual do loot, que
continua UNPROVEN por limitação da automação do diálogo nativo. Loot e `confirm()`
não foram modificados. O relatório amplo S6 permanece separado, sem inclusão
neste commit. Sem push, publicação, Vault, mídia ou alterações de campanha.
