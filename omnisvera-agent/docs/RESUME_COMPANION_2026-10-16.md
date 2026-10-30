# Retomada: ativação, contratos e OpenCode

**Atualização de 17/10:** reinício manual do usuário confirmado; dez contratos
agora carregados no backend. Evidência no último bloco deste documento. Os
registros anteriores de bloqueio e ativação de sete contratos são históricos.

## Ativado

Backend 8787 reiniciado pelo launcher oficial, PID observado **235072**.
Backup consistente: `backend/data/backups/pre-activate-seven-20261016-170651`
(ignorado pelo Git). Túnel/Tailscale não reiniciado. Nenhum token girado.

Health e as quatro fichas responderam; os sete contratos foram consultados no
processo novo. Comparação posterior aos GETs verificou 27 tabelas protegidas,
tokens canônicos e configurações. Conteúdo preservado; apenas `updated_at` de
`official:nimalia` e `official:earthropo` mudou pelo seed de startup existente.
A checagem estrita inicial detectou essas datas e falhou; a segunda conferência
comparou todas as colunas e permitiu **somente** essas duas diferenças observadas.
Não houve ações/combate/entrega de itens operacionais para testar.

## Migração real deste corte

Acrescentados aos dois contratos anteriores:

- Dorn: Força Arcana, Teia, Dissipar Magia.
- Vezemir: Força Arcana, Velocidade.

Total **sete ações** com contrato tipado realmente consumido pelos handlers,
mesmas transações/recibos/RNG/ledger/turnos. DTO efetivo recebe metadata sem
conceder recursos. Prévia usa metros/células corretos e ignora overrides nas
quatro ações de Dorn dirigidas pelo grid. Teia aceita a própria âncora, já
aceita pelo executor. Alcance próprio zero não seleciona outras entidades.

Controles de magia de Dorn enviam revisão. O caminho direto em
`SessionWorkspace.tsx` permanece legado: falha de escrita nesse arquivo,
sem contornar ACL/proteção. Backend aceita clientes sem revisão. Os demais
poderes/invocações/ataques não foram todos migrados ao contrato novo; handlers
nativos existentes não foram desativados. Manifest não certifica automação.

## Checks e evidência

- Backend amplo no observer: **998 testes**, seis falhas de subteste restritas
  a `test_ai_component_map`: modelos internos confundidos com OpenAPI,
  placeholders de rota incorretos e contagem antiga. Índice corrigido e esse
  teste reexecutado: **PASS**. Não chamar o comando amplo anterior de verde.
- Último patch de alcance: **37/37 PASS** posteriores ao patch. Outros lotes
  focados: Dorn/Vezemir/DTO **18/18**; fronteira MCP **49/49**. São conjuntos
  sobrepostos, não somar como habilidades certificadas. A suíte ampla precede
  o último patch de alcance e a correção do índice.
- Primeira tentativa ampla usou o venv de aplicação sem SDK MCP e carregou
  código durante edições: 984 testes, 11 falhas/2 erros/2 skips. Foi preservada
  como diagnóstico, não usada como evidência verde.
- Frontend final **327/327 PASS**, typecheck e build PASS; warning de chunks
  grandes permanece. `git diff --check` PASS.
- Ensaio HTTP descartável `omni-resume-native-20261016-165119`: **6/6 PASS**
  (Velocidade; cinco magias Dorn). Quatro atores, `ui=true`, lote lightning.
  Readiness: seis contextos GM/jogador, 360/390/1440, PASS. As seis capturas
  foram abertas/revistas: leitura/layout principal aceitos parcialmente, mídia
  ainda incompleta. Multialvo excedeu 300 s: **UI geral INCONCLUSIVE**, exit 2.
  Não houve ampliação de timeout nem certificação de combate/mesa física.

## OpenCode: pendência real

Somente `companion-tests` foi desconectado/reconectado, mantendo sessão e modelo
Muse Spark por mensagem; configurações/modelo global e outros serviços intactos.
Tentativas adicionais reais: `test-31ec0018c266442cbba0cd7f71e462ad`,
`test-39e42396099c406787932f871e869a19`,
`test-58308541da1041419fe00ad71fc4f4e3`: **ERROR/INCONCLUSIVE no startup**.
Todos os recibos anteriores preservados. Nenhuma ação/API/UI executada nesses jobs.

Logs privados agora distinguem spawn/bootstrap/health sem ambiente/tokens.
MCP mantém SDK observer; ensaio usa apenas o Python existente em backend/.venv.
Mesmo assim, o child fica vivo sem chegar ao primeiro checkpoint do script.
O caminho direto inicia e executa APIs, mas isso não prova o conector.
Causa Windows/host não demonstrada. Após o usuário dizer Continue, a limpeza
oficial `/global/dispose` concluiu e os quatro conectores reconectaram; sessão
e modelo global preservados. O reinício do host foi tentado, mas Windows negou
`Stop-Process` no PID 38768. Não houve elevação, troca de host/storage ou caminho
alternativo para matar o processo. O host continua o mesmo. Nova tentativa
`test-44d7fb0eb84c4c9baa803d8c194fb5f7`: **ERROR/INCONCLUSIVE no startup**,
sem API/UI. Para repetir após um restart real, o usuário precisa fechar/reabrir
esse OpenCode. Isso não exige reiniciar Companion/Godot nem trocar o modelo.
O backup do banco OpenCode em `pre-opencode-host-20261016-200223` não concluiu
(origem ocupada); pasta incompleta preservada, não apresentada como backup válido.

## Lote seguinte: três contratos, sem regras novas

- Clonagem: componente consumível, uso diário, círculo separado do nível,
  alcance/posicionamento, PV e duração obtidos do contrato no handler nativo.
- Magia da Morte: alcance por nível, DV/JPC, quantidade 2d6, proximidade e
  custo de PV preservados. Consumo lê estado mais recente na mesma transação,
  evitando sobrescrever HP/flags alterados por hooks anteriores.
- Sangue Defensivo: +2 CA, uma rodada, custo 2, sem consumir ação principal.
  Retry recupera recibo antes de checar forma/revisão; autorização permanece.

Total em código: **dez ações**. Metadata não concede poderes nem componentes.
Os três contratos deste lote **ainda não estão ativados**. Backup consistente
concluiu em `backend/data/backups/pre-activate-ten-20261016-222121`, 27 tabelas,
combate inativo. O comando de reinício foi rejeitado pela política do ambiente
antes de executar; nenhum stop/start ocorreu. Não houve tentativa por caminho
alternativo. O backend anterior (sete contratos) foi mantido; falta reinício
permitido pelo ambiente ou manual pelo iniciador oficial. Não confundir build
atualizado com carregamento dos novos handlers.
Teste RED do catálogo real reproduziu `KeyError` na integração Raziel, corrigido
antes da ativação; testes de rota agora usam catálogo real, sem mock de resolver.
Lotes focados passaram. Suíte ampla repetida com código estável: **1025 testes,
OK, 1 skip**, 951 s; skip de privilégio Windows já conhecido. Frontend repetido:
**327/327 PASS**, typecheck e build PASS; warning de chunk grande permanece.
Ensaio HTTP/UI repetido nesta retomada, com limites abaixo.
Não afirmar que todos os ataques/retries de Raziel ou todas as fichas migraram.

O primeiro ensaio amplo desta continuação foi interrompido somente na árvore
criada pelo agente: memória livre medida em 157 MB e paginação em 19.763 páginas/s.
Logs/TEMP preservados: 35 PASS, 2 EXPECTED_BLOCK, 1 FAIL (timeout do alcance
de Raziel), sem aceitação UI. Não reclassificado como verde nem atribuído a uma
causa de código sem reprodução. A repetição seletiva roda sem suíte concorrente,
com os quatro atores, `ui=true`, alcances e três poderes deste lote. Sua API
terminou com **6 PASS, 0 FAIL, 1 EXPECTED_BLOCK**: quatro alcances, Sangue
Defensivo e Magia da Morte passaram; Clonagem bloqueada pela falta de cristal
copiada da ficha operacional. O timeout anterior permanece registrado, não foi
apagado nem escondido por aumento do limite.

UI do lote `combat`: **PASS**, readiness em seis contextos GM/jogador nas
larguras 360/390/1440 (120,9 s) e dez ativações pela ficha (224,6 s): buffs,
Frenesi/Provocação, Aterrorizar, Força/Reflexos/Teia/Dissipar/Guarda de Dorn.
Artefatos privados: `omni-ten-native-selected-20261016-02` no TEMP.
As seis capturas novas de readiness foram abertas e revistas: layout principal
legível, mas ícones faltantes/alt text de CA ainda visíveis. Aceitação visual
**parcial**, sem certificação de toda mídia/interface. Estes dez usos de UI não
são dez contratos novos nem prova visual de execução dos três novos poderes.
Não há prova de mesa física/multirrede; certificação integral continua falsa.
Também revistas as capturas de Aterrorizar, Velocidade e Reflexos após o uso:
contadores/estado consumido coerentes e cards legíveis; mesmas lacunas de ícones.
O runner terminou com exit 0 e encerrou sua fixture; porta 8871 ficou sem listener.
Após o bloqueio do reinício, backend PID 235072 e quatro GETs 200 foram novamente
confirmados, com as mesmas 27 tabelas, tokens e configurações preservados.

## Pendências concretas

- Carregar os três contratos novos no backend: reinício impedido pelo ambiente,
  apesar da autorização do usuário; processo anterior saudável preservado.
- Startup real do ensaio pelo OpenCode continua inconclusivo; precisa restart
  real do host que Windows impediu encerrar. Não mudar modelo, tokens ou storage.
- Migrar próximos grupos aos contratos, sem desativar seus handlers atuais:
  Toque/Aterrorizar, Mísseis/invocações; Frenesi/Provocação; ataques e demais
  poderes de Raziel; Reparo/protocolos de Dorn. Não estão todos migrados hoje.
- Revisão do acervo PDF, riders de monstros e mídias faltantes não concluídos.
  Laboratório continua proposta/revisão, não executor de código arbitrário.
- Faltam ensaios visuais por ação do lote novo e multicliente em redes reais.

## Arquivos por fronteira

- Contratos/handlers: action_contract, action_library, action_components já
  existente, dorn_spell_pack, vezemir_skills, main (blocos localizados), schemas,
  character_play, action_range, dados dorn7_mage3/session_abilities,
  morthak_action_contracts, morthak_high_spells e raziel_action_contracts.
- Regressões do lote novo: test_morthak_action_contracts,
  test_raziel_defense_contract, test_contract_sheet_projection; integração real
  de catálogo/DTO, replay, custo, turno, rollback e ausência de concessão em GET.
- UI: api.ts, nativeSpellRevision.ts, DornSpellControls.tsx e testes correspondentes.
- MCP: agent_test_jobs, run_sheet_test, cf01_probe e testes de bootstrap/runtime.
- Índice/guias: AI_COMPONENT_MAP, CURRENT_COMPANION_CODE, SHARED_ACTION_COMPONENTS,
  MCP_NATIVE_RUNTIME e este relatório. Testes adicionais identificam cada lote.

Branch/HEAD preservados: devin/create-omnisvera-class-standard / 1a07a84.
Worktree misto pré-existente preservado; sem staging, commit ou push.

## Nova tentativa de reinício, 16/10 às 23:07

Usuário solicitou tentar novamente. Leituras confirmaram Companion PID 235072
(redirector 230252), OpenCode PID 38768, ambos com listener ativo; OpenCode
health positivo e zero sessões ocupadas. Combate inativo. Backup consistente
novo: `backend/data/backups/pre-retry-ten-20261016-230713`, com 27 tabelas,
credenciais e configuração preservadas. RAM livre observada em 244.452 KiB.

Repetido o mesmo fluxo oficial do backend, sem rota alternativa: rejeitado
pela política antes da execução; nenhum processo encerrado ou novo iniciado.
OpenCode: tentativa direta de Stop-Process novamente retornou Acesso negado;
o início substituto não foi executado. Não houve elevação, troca de porta,
modelo, storage, credenciais ou uso de outro agente para contornar os bloqueios.
Os três novos contratos continuam aguardando carregamento no backend.
Conferência posterior estrita sinalizou três tabelas workspace. Comparação
coluna a coluna demonstrou somente `updated_at` (state/maps) e `last_seen_at`
(presence), sem linhas adicionadas/removidas ou conteúdo alterado. As outras
24 tabelas protegidas e os tokens canônicos permaneceram idênticos ao backup.
Ambos os processos conservaram os mesmos PIDs e horários de início.

## Reinício manual confirmado, 17/10 às 00:21

Usuário executou o bloco PowerShell e relatou mensagem passageira seguida de
janela azul sem texto. Verificação somente leitura confirmou novo backend:
PID 193024, redirector 202900, início 00:21:44, comando uvicorn oficial na porta
8787. Health autenticado e quatro fichas responderam 200. As dez descrições de
contrato retornaram revisões esperadas, incluindo Clonagem/Magia da Morte de
Morthak e Sangue Defensivo de Raziel: lote carregado, não apenas salvo em disco.

Comparação ao backup `pre-retry-ten-20261016-230713`: tokens canônicos e campos
de configuração idênticos; 24 tabelas protegidas idênticas. As três tabelas
workspace só diferiram em timestamps/presença e `view_scroll_top`; nenhuma
linha adicionada/removida ou mudança em fichas/inventários/combate. Combate
inativo. Sem casts operacionais, testes em campanha ou nova certificação UI.
OpenCode não foi reiniciado por esse bloco; seu startup segue pendente.

RAM livre medida em 75.704 KiB (aproximadamente 74 MiB de 8 GiB). É um risco
operacional observado, não prova da causa da janela azul ou do erro passageiro,
cujo texto não foi recuperado. Nenhum programa adicional foi encerrado.
