# Vezemir, Morthak e Dorn — matriz de fechamento

Escopo: revisar as três fichas atuais, corrigir defeitos reproduzidos e separar
funcionamento de lacuna de prova. Nenhum balanceamento ou poder novo de Raziel.
Ensaios usam SQLite/vault temporários e as rotas nativas; não a mesa real.

## Defeitos reproduzidos e correções

1. **Dorn / mapa e alcance:** a escolha do primeiro pin de personagem podia usar
   uma cena antiga. Força Arcana recusava aliado adjacente; Teia podia atingir
   outro mapa. Agora usa o mapa do combate ativo, ou o mapa atual fora dele,
   preservando o pin selecionado e a escala desse mesmo mapa.
2. **Morthak / Aterrorizar:** distância declarada pelo cliente podia prevalecer
   sobre o grid. Agora usa distância lógica real e rejeita outro mapa quando há
   grid atual. Mapas legados sem grid mantêm o modo assistido existente.
3. **Vezemir / Força Arcana simultânea:** uma segunda chamada podia ler a FOR já
   alterada após a primeira confirmação e receber conflito de conteúdo no retry.
   O handler recupera o recibo da mesma técnica/ator/alvo se o comando concorrente
   já concluiu, sem outra execução, custo ou rolagem. Comando diferente e erro
   sem recibo correspondente continuam rejeitados.

Testes RED anteriores ao patch: cinco casos de Dorn, três de Necromante e
interleaving determinístico de duas threads em Força Arcana. Regressões incluem
escala por mapa, prioridade do combate, ausência de custo/rolagem em rejeição,
recibo de outro ator/técnica e preservação do erro original sem recibo.

## Matriz funcional

`Implementado` não significa todos os caminhos certificados. A fonte das regras
continua sendo o catálogo/handler existente; a matriz não redefine RPG.

| Ficha | Ação / família | Situação e limite |
|---|---|---|
| Vezemir | Corpo a corpo / Grisalma | Implementado; ataque, dano, bônus, confirmação e orçamento nativos |
| Vezemir | Ataque genérico à distância | Bloqueio correto na ficha copiada: arma não equipada |
| Vezemir | Força Arcana | Implementado; custo diário e expiração; retry simultâneo corrigido |
| Vezemir | Velocidade | Implementado; movimento, CA e ataque extra; duração e custo nativos |
| Vezemir | Frenesi | Implementado; manual/automático, FOR, duração e limite diário da sobrevida |
| Vezemir | Provocação | Implementado; grid, JP no turno, alvo forçado, penalidade e recuperação de uso |
| Vezemir | Pulseira de Vinhas | Item equipado; carga/JP/imobilização/consumível independentes do ataque |
| Vezemir | Maestria | Passiva calculada enquanto Grisalma está equipada; sem botão de uso |
| Vezemir | Visão / portas / descanso élfico | Traços cadastrados; portas/fog continuam sob controle do Mestre; sem motor de visão automática |
| Morthak | Corpo a corpo / Cajado | Implementado; segue equipamento, BA e orçamento nativos |
| Morthak | Ataque genérico à distância | Bloqueio correto na ficha copiada: arma não equipada; não confundir com Adaga de Osso |
| Morthak | Adaga de Osso | Ataque específico implementado, alcance aprovado de 9 m |
| Morthak | Mísseis Mágicos | Implementado; cálculo por nível e consumo nativo |
| Morthak | Levantar Esqueleto | Implementado; uma instância viva dessa técnica, controle/dispensa nativos |
| Morthak | Animar Mortos | Implementado; cadáver elegível autorizado; pode coexistir com o esqueleto |
| Morthak | Toque Sombrio | Implementado; dano inicial, perda de PV no turno, morte e encerramento; não drena FOR |
| Morthak | Aterrorizar | Implementado; DV/JP, alcance de grid, penalidade e duração por turno individual |
| Morthak | Clonagem | Implementado; exige fragmento consumível, ausente no inventário copiado; ensaio visual pode conceder somente na fixture |
| Morthak | Magia da Morte | Implementado; área, DV/JP e custo de PV; inclui aliados elegíveis conforme regra aprovada |
| Morthak | Traços raciais/classe | Oito entradas inventariadas; cadastro não certifica execução automática de cada traço narrativo/passivo |
| Dorn | Corpo a corpo / distância | Implementados conforme armas/equipamentos atuais |
| Dorn | Mísseis / Relâmpago | Implementados; Relâmpago com até três alvos da campanha, JP por alvo e dano compartilhado |
| Dorn | Reflexos | Implementado; imagens, interceptação por acerto, duração; não intercepta área |
| Dorn | Teia | Implementada; área, CA/JP de DES e custo de movimento no grid; mapa corrigido |
| Dorn | Força Arcana | Implementada; alvo adjacente, FOR original e escala do mapa corrigida |
| Dorn | Dissipar Magia | Implementada; exige efeito arcano com círculo/nível de origem cadastrados |
| Dorn | Guarda | Implementada; aliado adjacente no grid e redirecionamento de ataques; expira no turno de Dorn |
| Dorn | Vanguarda | Protocolo de exploração; sem aumento permanente de atributos |
| Dorn | Reparo | Kit consumível e um consumível por turno; não repor estoque real por causa do ensaio |
| Dorn | Diagnóstico / magias antigas | Diagnóstico permanece em catálogo legado, mas foi retirado da UI a pedido; Levitação/Escuridão não voltam à ficha |

## Evidências e lacunas

Ensaio inicial MCP `test-c16d7793caa6485491aac7e3959e6a54`: 48 PASS,
três EXPECTED_BLOCK e um FAIL real (retry de Força Arcana). Histórico preservado;
o FAIL não foi substituído por uma declaração de que tudo já estava funcionando.

Repetição completa após os patches: MCP
`test-0e82396a46b842b7847e20d28fce96d1`, COMPLETED/PASS,
**49 PASS, três EXPECTED_BLOCK, zero FAIL**. Paridade Mestre/proprietário,
persistência e retries nativos permanecem nos cenários do executor.

Ensaio visual estendido independente: nove ações concluídas pela ficha — quatro
buffs de Vezemir, Aterrorizar e Força Arcana/Teia/Dissipar/Guarda de Dorn.
Custo, consequência, uma chamada por ativação e releitura após reload: PASS.
Capturas inspecionadas em `%TEMP%/omni-three-sheet-ui-91KKAH/` (desktop e 390 px).
Foram corrigidos problemas do próprio ensaio: seleção de cards sem comando e
limpeza de efeitos entre casos; não foram tratados como falhas de regras.
O smoke nativo usa três dessas ações para permanecer no limite de tempo;
`OMNISVERA_QA_EXTENDED_ACTIONS=1` permite repetir as nove na fixture independente.

O primeiro MCP visual `test-8fc4a99a5ddc4e5f8855e011042f9c44` registrou FAIL
no novo smoke, após os onze anteriores passarem. A investigação do DOM e das
leituras HTTP mostrou contador de Aterrorizar em 0/1, mas o teste dependia do
botão de ativação, retirado corretamente após o jogador gastar a ação. Corrigido
o locator para inspecionar o card/contador sem exigir esse botão. Repetição
isolada de Morthak PASS; captura final inspecionada em
`%TEMP%/omni-three-sheet-ui-YBiibu/morthak-aterrorizar.png`. Não foi necessário
alterar o frontend de produção para corrigir esse falso negativo do ensaio.

Repetição integrada final MCP `test-23348575d41847a2b5dc1cff5fdc624d`:
COMPLETED/PASS, quatro atores, cenário de concorrência/expiração selecionado
PASS e **12/12 scripts visuais PASS**. O novo smoke concluiu Força Arcana de
Vezemir, Aterrorizar e Força Arcana de Dorn; contadores atualizados e reload
confirmados. Capturas inspecionadas em `%TEMP%/omni-three-sheet-ui-BOJEIJ/`.
Mídia ausente na fixture não certifica defeito da biblioteca operacional.

`certification_ready=false`: este PASS seletivo não certifica todas as ações
das quatro fichas. As lacunas por ação permanecem no relatório nativo;
`physical_actions=false`, sem rolagem humana nem prova em redes distintas.

Os três bloqueios são ausência de arma genérica à distância nas duas fichas e
ausência de fragmento para Clonagem. Não foram concedidos itens na campanha.
Recursos/itens/passivas sem cenário não viram automação por estarem cadastrados.

Checks finais: **830 testes backend PASS**, **300 frontend PASS**, typecheck,
build e `git diff --check` PASS. A primeira suíte iniciada antes de concluir o
patch de concorrência falhou nesse teste RED; não foi apresentada como verde.
Avisos existentes de conexões SQLite não fechadas e chunks grandes permanecem.

## Ativação operacional

Backend 8787 reiniciado pelo lançador oficial: PID 169960 → 162980; túnel
Tailscale PID 6196 preservado. Backup privado consistente:
`backend/data/backups/pre-three-sheet-20261015-195525/`.
Credenciais iguais por comparação semântica; health e frontend público HTTP 200.
Fichas próprias de Vezemir/Morthak/Raziel HTTP 200 e `access_level=owner`, sem
expor tokens. Raziel só foi consultado como regressão de acesso; nenhuma regra
ou ficha dele foi alterada.

Quinze tabelas duráveis conferidas iguais ao backup. Comparação das 78 tabelas
também preservou os demais dados: a exceção foi `sqlite_sequence` (contadores
internos de autoincremento). `updated_at` dos mapas foi excluído do hash por ser
renovado pelo seed nativo; imagem, configuração e conteúdo dos mapas comparados.
Nenhum ataque, conjuração, descanso ou transação de QA foi aplicado à produção.

## Arquivos deste corte

- Runtime: `backend/app/dorn_spell_pack.py`, `necromancer_spells.py`, trecho
  de Força Arcana/Velocidade em `main.py`.
- Regressões: `backend/test_dorn_spell_map_scope.py`,
  `test_necromancer_grid_authority.py`, `test_vezemir_buff_concurrency.py`.
- Ensaio: `frontend/tests/three-sheet-actions-smoke.cjs` e registro no runner
  nativo `backend/scripts/run_sheet_test.py`.
- Este relatório, `CURRENT_COMPANION_CODE.md` e `AI_TEST_TOOLS.md`.

Worktree anterior misto preservado. Sem staging, commit, push, novos poderes,
alteração do Vault ou testes de combate na produção. Celular físico e estabilidade
em redes diferentes continuam INCONCLUSIVE.
