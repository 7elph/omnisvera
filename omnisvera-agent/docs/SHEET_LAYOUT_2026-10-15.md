# Ajuste compacto da ficha — 15/10/2026

## Comportamento

- Mesa/Ficha: somente ícones e saldos acima do inventário, sem título visível;
  ordem cobre, prata, ouro, platina. Jogadores não recebem controles de edição.
- Mestre: clicar nos saldos abre o editor da própria ficha, no diálogo padrão.
  Mantidos `set_currency`, saldo esperado, trava de envio e mensagem de erro.
  A ficha legada conserva o editor, mas não é necessária para acessá-lo.
- Registro: filtro pequeno à esquerda da contagem, fechado inicialmente.
  Fechar preserva os critérios; o ícone sinaliza filtro ativo. Sem nova consulta.
- JP e dados: botões no canto direito do cabeçalho de atributos, na mesma linha.
- Equipamentos: fundo decorativo usa `definition.cover` completo, com fallback
  para `portrait` e silhueta. Arte contida, sem recorte; slots continuam clicáveis.
  Nenhuma imagem gerada, alteração no Vault ou mudança de equipamento.

## Arquivos deste ajuste

- `frontend/src/components/CurrencyCounters.tsx`
- `frontend/src/components/EquipmentLoadout.tsx`
- `frontend/src/components/SheetDetail.tsx` (rótulo acessível opcional do gatilho)
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/src/companionTheme.css`
- `frontend/tests/currency-counters.test.cjs`
- `frontend/tests/sheet-presentation.test.cjs`
- `frontend/tests/compact-sheet.test.cjs`
- `frontend/tests/compact-sheet-smoke.cjs`
- `frontend/tests/action-reference-smoke.cjs`
- `frontend/tests/sheet-detail.test.cjs`
- Este documento.

## Validação

Testes RED antes da implementação: cinco falhas reproduziram ordem, posição,
resumo, cabeçalho e falta da arte. Após o ajuste: 801 testes backend e 291
frontend passaram; typecheck e build passaram. Avisos preexistentes: conexões
SQLite não fechadas em testes e bundles maiores que 500 kB.

Primeiro ensaio MCP `test-e7dcdaf5e5d54858abd4ab898b0a55ba`: quatro ataques
de API e dois scripts visuais passaram; o terceiro falhou no driver ao buscar
o filtro do registro na vista exclusiva da ficha de jogador. Corrigido o driver
para testar o registro na Mesa do Mestre, sem alterar a navegação do aplicativo.

Segundo ensaio `test-fd7e8ff07aa543b2af01aa219ac59a4e`: mesmos quatro ataques
e dois scripts visuais PASS; a verificação nova revelou que o gatilho de saldo
tinha somente os números como nome acessível. Adicionado rótulo opcional ao
diálogo compartilhado, sem alterar os nomes dos outros gatilhos; teste RED/GREEN.
Capturas dos três jogadores confirmaram artes completas e ícones alinhados.
Equipamentos/dados ausentes na fixture receberam somente cópias das imagens
públicas já cadastradas, sem tocar nos originais.

Aceitação visual explícita do corte: capturas finais em
`%TEMP%/omni-compact-sheet-VSzN7I`, inspecionadas pelo agente. Equipamentos dos
quatro personagens em 390 px, Dorn também em 1440 px: arte inteira, sem recorte
ou compressão; slots legíveis. Cabeçalho JP/dados horizontal; saldos em ordem
crescente, sem legenda ou caixas; filtro à esquerda da contagem. Editor do
Mestre abre, salva pela ação nativa e fecha; jogadores não recebem esse botão.

Terceiro ensaio `test-1a4c02825f3048029f2ba1b4eb055869`: quatro ataques e
dois scripts visuais PASS; o driver do editor tentou preencher `NaN` ao ler um
saldo legado ausente. Corrigido para zero, como o componente já faz. O diálogo
abriu corretamente e as capturas mostram arte completa e ícones de equipamento.

Quarto ensaio `test-51757adf7d6848cb9044857030bca7fd`: MCP COMPLETED/PASS,
um ataque de API e 9/9 scripts visuais PASS com os quatro atores. A inspeção
visual explícita das capturas pelo agente, contudo, encontrou equipamentos comprimidos
no desktop (o script ainda não verificava altura). Adicionado teste RED/GREEN
e `flex: 0 0 auto` somente nesse card. Nova rodada exigirá altura >150 px.
PASS de API/UI não substituiu essa inspeção visual.

Ensaio final `test-33ba651587df4b09ab6da4c0bba0e9f2`: **COMPLETED/PASS**,
`report.ui_smoke.status=PASS`, **9/9 scripts visuais**, quatro atores. Inclui
edição real de saldo apenas na fixture, filtros abrir/fechar/limpar, arte completa,
recarga, alternância das fichas, ações no grid e a nova altura desktop.
Replays anteriores desta mesma tarefa também passaram nos quatro ataques de API.
Sem certificação de todas as habilidades: `physical_actions=false` neste relatório;
os cenários de dado físico não foram a seleção deste corte de apresentação.

Frontend local e público responderam HTTP 200 após o último rebuild, servindo
`index-Bi_rwawM.js` e CSS `index-CXZjEmGZ.css`. Sem restart: backend não foi alterado neste corte.
Sem comandos de descanso, ataque ou edição de moedas no banco operacional.
Worktree misto preservado; nenhum staging, commit ou push.

Limite: viewport/toque emulados não comprovam aparelho físico ou redes distintas.
