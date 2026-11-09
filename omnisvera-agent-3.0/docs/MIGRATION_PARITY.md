# Migração funcional Companion 2.0 → 3.0

Referências: frontend/src/components e scripts Godot inspecionados em 07/11/2026. O 3.0 é parcial. Mapa renderizado e ficha legível não certificam paridade funcional. Aceitação requer abrir a UI nativa, executar o contrato autorizado, observar o resultado, recarregar e verificar permissões em fixture isolada. Mesa em redes distintas continua uma validação separada.

| Fluxo existente no 2.0 | Situação observada no Godot | Próxima entrega |
|---|---|---|
| Identidade Mestre/Jogador, presença e privacidade | Conectado, cobertura parcial | Expiração, reconexão e dois clientes em rede real |
| Ficha, recursos e inventário | Leitura visual parcial | Edição autorizada, usos, equipamento, moedas e estados |
| Ataques, magias e poderes | Guarda/Relâmpago conectados; restante parcial | Seletor de ação genérico baseado no contrato executável, alvos e resultado |
| Combate, iniciativa e turnos | Iniciar/encerrar/passar turno básicos | Comandos por participante, invocações, passivas e estados completos |
| Mapas e pins | Biblioteca e sprites parciais | Seleção persistida, NPCs/monstros/objetos, visibilidade, zoom e navegação |
| Fog e geometria | Sem editor nativo equivalente ao 2.0 | Ferramentas e persistência existentes, filtragem do jogador |
| Ferramentas do Mestre | Link ao legado substituído neste corte por navegação nativa | Ferramentas completas abaixo; navegação não equivale a implementação |
| Sessões e histórico | Leitura conectada; controle de status implementado neste corte | Edição de resumo, transcrições/mídia e gestão completa |
| Cenas e preparação | Cards de leitura nativos; envio seletivo ainda pendente | Cards, prévias, seleção e colocar na mesa usando SceneLab/scene selection |
| NPCs e monstros | Marcadores parciais | Bibliotecas, ficha, colocação, ações, magias, movimento e turnos |
| Catálogos/compêndios | Sem equivalência nativa | Busca, filtros, detalhes e ações validadas |
| Comércio | Sem equivalente jogável nativo | MerchantPanel: compras/vendas/barganha/serviços/estoque/recibos |
| Itens, loot e transferências | Inventário de leitura | Equipar/guardar/usar/cargas/recipientes, baús e divisão do grupo |
| Progressão e descanso | Sem controles completos nativos | XP/nível, rolagens pendentes e descanso pelos contratos existentes |
| Dados, JP e resultados | Parcial | Bandeja, JP, resultados legíveis e ledger, sem resolver regras no cliente |
| Assets, Sprite Studio e editor | Sprites Dorn/Morthak e edição local de terreno | Biblioteca/importação/associações e edição compartilhada |

## Corte atual: Mestre e sessão

O painel Mestre oferece acessos nativos a Sessões, Combate e turnos, Biblioteca de mapas, Personagens, Registro e Editor. O detalhe da sessão oferece iniciar, pausar, retomar e encerrar conforme o estado. Toda mudança pede confirmação e usa POST /gm/sessions/{id}/status já existente. Notas privadas continuam condicionadas ao Mestre e filtradas no servidor. Nenhuma mudança na sessão real é necessária para validar.

Arquivos: scripts/main.gd; tools/serve_preview.py (somente rota de status explicitamente permitida); tests/gm_controls.gd; tests/rom2_browser.cjs. Correção adicional de erro de campo no movimento em scripts/game_commands.gd: pos.cell.y → pos.cell_y. Nenhuma regra de combate reimplementada.

Verificações nativas: COMPANION3_GM_SESSION_CONTROLS_PASS, COMPANION3_UI_CONTRACT_PASS. Exportação Web concluída. Ensaio Web verifica ciclo de status no banco descartável, resposta 403 do jogador e ocultação de notas privadas, além da movimentação e layout horizontal já cobertos. Resultado final do ensaio e ativação devem ser registrados abaixo.

## Ordem de continuidade

1. Fechar o fluxo do Mestre: sessão → cena preparada → mapa/NPCs/monstros na mesa.
2. Fechar combate de ponta a ponta para as quatro fichas com contratos genéricos, inclusive invocações.
3. Itens/economia/loot e gerenciamento de fichas/descanso/progressão.
4. Catálogos, biblioteca de assets e editores; validação de paridade e redes reais.

Não remover o 2.0 até concluir os fluxos e suas permissões. Não converter descrição de catálogo em autorização automática de ação. Não declarar paridade pelo número de painéis ou botões.


Resultado: ensaio Web PASS em TEMP/omni-companion3-9fe4w3q_, ciclo planned/active/paused/active/completed persistido na fixture; jogador bloqueado pelo contrato nativo (401), leitura pública sem notas privadas. 9 testes Python de fundação PASS. Publicado com backup %LOCALAPPDATA%/Omnisvera/backups/gm-controls-20261107-210025; reiniciado somente o servidor Web 8872 após revalidar identidade do processo. Backend e sessão real não foram alterados. Paridade completa e mesa em redes distintas continuam pendentes.


## Gavetas compactas e arte ROM2

Gavetas de navegação e detalhes ajustam a altura ao conteúdo, limitadas ao viewport; listas longas mantêm rolagem. Moldura original graphics.res/interface/t_border.256 convertida pelo leitor independente do laboratório em PNG com transparência e aplicada como nine-patch, preservando os cantos e sem capturar cliques. Proveniência e SHA-256 em assets/rom2_local/ui/provenance.json; arquivos locais excluídos do Git. Não foram inventados formatos: shopframe.256 foi rejeitado por dados finais não interpretados e não foi utilizado. Os ícones atuais permanecem; as peças lm extraídas não tiveram função semântica confirmada.

Cenas aparecem como cards na gaveta Mestre, carregados da rota /scenes com autorização original. Ainda falta seleção de elementos, visualizador completo e envio à mesa; não há botão que simule essa entrega. Fluxo de Cenas continua parcial.

Arquivos deste corte: scripts/ui_style.gd, main.gd; tools/serve_preview.py; tests/compact_drawers.gd, gm_controls.gd, test_foundation.py; assets/rom2_local/ui e esta documentação. Backend e React não foram modificados; suas suítes completas não foram repetidas. Sem commit ou push.

Checks: COMPANION3_COMPACT_DRAWERS_PASS (janela curta, limite de janela longa, moldura sem interceptar clique); COMPANION3_GM_SESSION_CONTROLS_PASS; nove testes Python PASS incluindo encaminhamento autorizado de cenas. Captura nativa inspecionada. Ensaio Web intermediário PASS em TEMP/omni-companion3-9ed76wsv; ajuste posterior de posicionamento da moldura submetido ao ensaio final antes da publicação.

## Correção de origem da UI

A inspeção visual do ensaio it38ldee identificou offsets (-1,97) no Control Screen da cena principal. Foram zerados os quatro offsets para restaurar a origem (0,0) e os cliques corretos. tests/compact_drawers.gd agora exige Screen.position == Vector2.ZERO. scenes/main.tscn integra a lista de arquivos alterados deste corte. Não basta usar o PASS de API desse ensaio como prova de alinhamento: suas capturas revelaram a falha e motivaram nova exportação e novo ensaio.

Ensaio final PASS: TEMP/omni-companion3-7bjzm0gr. Capturas de editor desktop/mobile inspecionadas, origem correta e janela compacta com moldura. Publicação com backup %LOCALAPPDATA%/Omnisvera/backups/rom2-drawers-20261107-211148. Reiniciado somente o servidor Web 8872; nenhum comando mutável enviado à campanha real. PCK público comparado com a exportação validada.


## Seleção de preparação → Mesa

Implementado no Godot: abrir preparação, buscar os dados atuais e pins autorizados do mapa, selecionar elementos/pins, incluir mapa opcionalmente, pré-visualizar o mapa e confirmar o envio. A confirmação informa que os selecionados serão revelados. Seleção vazia não envia comandos. O contrato existente /gm/scenes/{id}/selection-on-table exige sessão ativa e valida pertencimento/combate. O cliente não cria regras ou publicação paralela.

O comando usa o retry existente, com request_id e payload congelados para repetição segura em timeout. Respostas de preparação/pins são ignoradas se o Mestre já trocou de cena. Reconexão limpa a preparação e a confirmação. Somente o Mestre dispõe desses controles; servidor continua responsável pela privacidade. Resposta com mapa abre o visualizador de mapas/pins já existente; a importação de cada cenário como terreno nativo do mundo Godot segue uma etapa separada.

Arquivos: scripts/scene_preparation.gd, scripts/main.gd, tools/serve_preview.py; tests/scene_selection.gd, create_fixture.py, rom2_browser.cjs. Nenhum arquivo backend/React alterado. 10 testes backend de test_scene_selection_oct24 PASS, todos em SQLite temporário. COMPANION3_SCENE_SELECTION_UI_PASS: seleção vazia bloqueada, confirmação antes de enviar, cancelamento e bloqueio de jogador. Resultado Web/ativação abaixo. Sem commit/push.

Ensaio Web seletivo PASS em TEMP/omni-companion3-trvdqj6l, com publicação parcial, privacidade, autorização e replay. Captura nativa de preparação inspecionada. Removida uma conexão de sinal que retinha recursos; teste nativo repetido sem vazamentos reportados. Exportação final e publicação com backup %LOCALAPPDATA%/Omnisvera/backups/scene-selection-20261107-211832. Reiniciado somente servidor Web 8872. Nenhuma cena, ficha ou pin operacional foi alterado nos testes.
