# Fechamento para sexta, 23/10

Inventário de evidências, não certificado de mesa pronta. Preservar os sistemas
existentes; não abrir outra arquitetura antes do ensaio das quatro fichas.

Continuação focal mais recente: `REST_UI_CHECK_2026-10-20.md`.
Descanso V3 COMPLETED/PASS: dois API + dois scripts UI; PV/Status/contadores
das quatro fichas e reload em 1440/390, estoques e efeito de NPC preservados.
Capturas focais revisadas. Corrigido carregamento de Assets IA enquanto fechado;
V1/V2 FAIL preservados. Frontend 354 PASS, typecheck/build PASS, novo bundle
`index-BTITC67R.js` servido local/público 200. Backend focal: 47 nativos OK e
48 observer OK (seleções sobrepostas). Discover geral não iniciado por RAM
abaixo do piso; não substitui o resultado geral anterior. Sem novo restart.

Continuação focal anterior: `NECROMANCY_UI_CHECK_2026-10-20.md`.
Lote Morthak V6 COMPLETED/PASS: cinco API PASS, um bloqueio esperado e seis
usos UI em três scripts, capturas 390/1440 revisadas. Corrigidos pin fantasma de
invocação dispensada (backend ativado em 20/10, 17:18, worker 253068) e bloqueio de reabertura do
controle após usar a ação (frontend servido). Build PASS, novo index-BJC6UolP.js.
Tentativas FAIL/CANCELLED e limites preservados no relatório. Checks finais:
1.172 PASS nativos, dois erros SDK e um skip; 30 testes no observer OK cobrem
os pontos MCP. Frontend 348 PASS; typecheck, build e diff check PASS.
O comando discover nativo continua exit 1 por SDK ausente, não PASS integral.
Restart somente 8787 autorizado, backup consistente preservado; 77 tabelas
comparadas, sem mudança de dados salvo timestamps de bootstrap de dois mapas
oficiais. Tokens idênticos; home e três fichas, locais e públicas, 200.
OpenCode e túnel não reiniciados. Detalhes e limites no relatório focal.

| Frente | Já existe / verificado em 20/10 | Lacuna real |
| --- | --- | --- |
| Conexão | Timeout de leitura, descarte de resposta antiga, ledger independente; regressões frontend passaram | Ensaio Mestre + jogadores em redes distintas continua sem prova |
| Descanso e efeitos | V3 focal PASS: limpeza, PV, contadores, cargas diárias e reload das quatro fichas; capturas 390/1440 revisadas | Não certifica todos os efeitos especiais nem celular físico/redes distintas |
| Grid e movimento | Backend autoritativo, persistência e orçamento com testes | Aceitação mobile física e zoom durante combate |
| NPCs e comércio | Estoque, compra/venda, barganha, entrega e hospedagem nativos | Preparar o conteúdo concreto; serviços arbitrários não são automáticos |
| Quatro fichas | Lote combat: 88 cenários API PASS, quatro fichas e dez usos UI. Hemomancia: 9 API/seis usos UI PASS; passivas: 44 backend + 9 frontend PASS. Vampíricos V2: 6 API/quatro usos UI PASS | Certificação por ação ainda incompleta; gatilhos das passivas pela UI, demais poderes/traços e mesa multirrede não comprovados por estes lotes |
| Cenas | Oficina privada, fila e prévia textual; um texto real anterior | Prévia visual integrada de NPC/mapa/combate e importação revisada não concluídas |
| IA de texto | Gateway Ollama Cloud; duas amostras reais, segunda com as quatro fichas atuais | Revisão gerada, mas qualidade insuficiente: ainda classifica ruído ASR e confunde papéis; sem aprovação |
| IA de imagem/código | Fila de assets; adapter de código bloqueado com segurança | Fila não é geração FLUX; sandbox de código ainda não certificada |

## Correção deste corte

`ai_preparation_context` usa apenas id, nome, raça, classe e nível do roster
autorizado. Seleciona Morthak, Raziel, Vezemir e DORN-7 (aliado controlado pelo
Mestre); não envia inventário, notas privadas, objetivos ou credenciais.
Exige os quatro registros sem duplicações. Níveis e identidades atuais têm
precedência sobre observações históricas. Não infere aliases de ASR.

O comando abaixo planeja sem escrever nem chamar modelo. `--enqueue` cria UMA
revisão na fila privada nativa. Hash determinístico evita duplicação por retry
e muda quando contexto/evidência mudam. O texto gerado anteriormente nunca é
reutilizado como fonte; originais continuam preservados para auditoria.

```powershell
backend\.venv\Scripts\python.exe backend/scripts/ai_workshop_party_context.py --db .autonomy/runtime/ai-workshop.sqlite3 --source-job 1
```

Execução operacional: quatro fichas atuais lidas; job **277** enfileirado com
contexto, após backup da fila privada. Duas tentativas de tick nativo foram
pausadas por RAM insuficiente (383 e 138 MB livres, guarda de 512 MB preservada),
antes de chamar o provedor. Banco da campanha com SHA inalterado. Sem restart necessário:
este corte acrescenta ferramenta de preparação, não altera rotas em execução.
Worker contínuo permanece parado; não reenfileirar as outras 275 janelas sem
primeiro revisar a qualidade desta amostra. Nenhuma aprovação/publicação.

## Validação desta etapa

- RED: módulo de contexto ausente reproduzido antes da implementação.
- 112 regressões backend de descanso, mapas, comércio e combate: PASS.
- 6 testes novos de contexto + 25 de adapters: 31 PASS.
- Seleção ampliada oficina/fontes/rotas/contexto: 90 PASS (inclui os 31 acima).
- 21 regressões frontend de timeout, mapa e oficina: PASS.
- Há avisos de depreciação e conexões SQLite não fechadas nos testes existentes.
- Discover completo não certificado: tentativa da etapa anterior esgotou RAM.
- Typecheck: PASS nesta execução. Build não iniciado: havia 279 MB livres,
  abaixo do piso preventivo de 768 MB usado para esse comando. O build PASS
  da etapa anterior não foi reexecutado. Nenhum frontend foi editado neste corte.
- Sem prova nova de mesa multirrede ou aceitação visual em celular físico.

## Ordem curta de fechamento

1. Concluir e revisar UM texto contextualizado, quando a guarda de RAM permitir.
2. Ensaiar cada ação/passiva nas quatro fichas, em fixture, incluindo inspeção
   visual; corrigir somente falhas reproduzidas. Não reabastecer recurso real
   apenas para transformar bloqueio legítimo em PASS.
3. Preparar blocos concretos a partir das sete sessões: local, NPC com voz e
   serviço, encontro executável, loot com ícones e consequências das escolhas.
   Cada bloco é proposta privada, não lore automaticamente canônica.
4. Publicar somente correções validadas e fazer ensaio multirrede antes da mesa.
   Pausar geração/testes pesados durante sessão ativa.

## Continuação — revisão visual e execução real

- Capturas anteriores mostraram texto alternativo da armadura invadindo a CA.
  A falha também foi reproduzida no componente atual, antes do patch.
  `ArmorClassValue` agora tenta a imagem cadastrada, depois o catálogo e por
  fim um escudo vetorial de 24 px. Nome acessível preservado, sem imprimir
  nome longo quando a imagem falha; valor e bônus de CA não mudam.
- 11 testes frontend de apresentação/ficha compacta: PASS. Typecheck e build:
  PASS nesta continuação, apenas aviso preexistente de chunks grandes. Home
  local e pública retornaram 200 com o novo bundle `index-CYOspoEy.js`.
  Não houve mudança de código backend nem restart operacional nesta continuação.
  Discover backend e suíte frontend completa não foram reexecutados.
- Quatro árvores ociosas dos conectores Godot foram encerradas conforme
  autorização anterior; processos Companion/OpenCode/Ollama preservados.
  Isso não é correção permanente do reaparecimento dos conectores.
- SDK MCP respondeu capacidades, mas start recebeu BUSY: o conector existente
  do OpenCode detinha a trava. Não se removeu lock nem criou executor paralelo.
  A execução foi delegada à conversa existente do OpenCode.
- Os cinco pedidos antigos da pasta de evidências autorizada pelo Mestre foram
  aprovados com `once`, nunca `always`. Novos pedidos para outra fixture não
  foram concedidos; o diagnóstico foi fornecido diretamente ao agente.
- Ensaio `test-bbe3294e747146b2ad56daa1ab2573dd`, quatro atores, `ui:true`,
  `ui_suite:combat`: ERROR/INCONCLUSIVE antes dos cenários. A fixture não ficou
  pronta em 45 s e o log do servidor permaneceu vazio. Só a árvore de processo
  criada pelo runner foi encerrada. Sem provas novas de habilidade ou UI.
  Checagem mínima direta do Python com ambiente de fixture: 0,23 s; entrada
  `cf01_probe --help`: 0,41 s. Isso não reproduziu o timeout e não prova sua
  causa. Não se aumentou prazo nem reclassificou o resultado como PASS.
- Com RAM admitida pelo guard nativo, o job 277 finalmente concluiu em 13,53 s,
  produzindo 5.321 caracteres. SHA do banco da campanha inalterado. O resultado
  continua `awaiting_approval`, sem publicação: a revisão encontrou classificação
  indevida de ruído ASR e confusão entre membro do grupo e personagem de jogador.
  Identidades/níveis melhoraram, mas qualidade ainda insuficiente para produção
  em massa. Worker contínuo parado; nenhuma imagem ou código gerado neste corte.

O bloqueio de inicialização desta tentativa foi superado na continuação abaixo.
O resultado inconclusivo anterior permanece histórico, sem reclassificação.

## Continuação — fixture iniciada e lote combat concluído

Um teste RED demonstrou que a fixture herdava stdin do host MCP. O lançamento
agora usa DEVNULL, mantendo o ambiente, logs privados, timeout e cleanup originais.
Seleção backend: 26 testes OK (1 skip por SDK); contrato MCP repetido no observer:
1 PASS. Nenhum restart do conector ou do Companion foi necessário.

Novo recibo `test-d5191e1dc8014e7b82ee76e158fb8273`: COMPLETED/PASS, exit 0,
88 cenários API PASS, três bloqueios esperados, três scripts UI PASS. As quatro
fichas foram lidas em desktop/celular; dez ativações de Vezemir/Morthak/Dorn
confirmaram consumo, consequência e reload pela UI. Capturas novas revisadas.

Limites preservados: 35 lacunas de certificação, mídia derivada ainda incompleta
na fixture, Hemomancia UI não incluída neste lote e nenhuma mesa em redes distintas.
O ensaio durou 1.199,86 s, muito próximo do teto. Próximos lotes visuais devem
selecionar explicitamente cenários API já observados, sem aumentar o timeout,
apagar falhas antigas ou fundir evidências de fixtures diferentes silenciosamente.

Detalhes e arquivos: `FIXTURE_STDIN_ISOLATION_2026-10-20.md`.

## Continuação — conector atualizado e Hemomancia verificada

Com autorização, somente o MCP `companion-tests` foi desconectado/reconectado
pelo OpenCode (HTTP 200). O schema antigo não aceitava `ui_suite:hemomancy`.
Companion PID 253460 e OpenCode PID 38768 permaneceram inalterados; não houve
mudança de modelo, tokens, permissões ou fichas operacionais.

Recibo separado `test-cc6ecbce7ed04e6badad2b10c024568c`: COMPLETED/PASS,
9 cenários API e dois scripts UI PASS, em 316,97 s. Seis usos cobriram as cinco
armas; Marca Rubra também foi acionada nos casos do Arco. Cancelamento, comando
único por confirmação, gasto, reload e atualização numa segunda página local
foram verificados. Capturas desktop/390 px revisadas. Fixture 8871 encerrada.

Não fundir este escopo com certificação integral: `all_actions_certified:false`,
certificação INCOMPLETE. Sem prova de celular físico ou redes distintas.
Nenhum código de aplicação foi alterado nesta continuação; apenas documentação.
Detalhes: `HEMOMANCY_UI_CHECK_2026-10-20.md`.

## Continuação — bordas das passivas

Cinco regressões novas passaram junto com o módulo existente: 44 backend OK
e 9 frontend PASS, executados sequencialmente pelo OpenCode. Reforçam consumo
de Exposto/Revanche ao errar, limiar de CA da Revanche, Ferroada sem bônus
duplicado, imunidade sem Exposto e renovação de Ceifa sem ticks duplicados.
Nenhum defeito do produto foi reproduzido nesses casos; não houve patch de regra.
Somente teste/documentação alterados, sem restart ou dados reais modificados.

Isto não substitui provas UI por ação nem certificação multirrede. Detalhes e
limites: `HEMOMANCY_PASSIVES_CHECK_2026-10-20.md`.

## Continuação — poderes vampíricos e seletor animal

Lote aditivo `vampiric` no MCP/executor existente: Regeneração, Mordida, Caixão
e Forma da Noite, quatro atores, dois scripts fixos, mesmos limites. V1 passou
em seis cenários API e quatro usos UI; revisão das capturas revelou nomes
cortados no seletor animal. Teste de meia largura reproduziu RED; ajuste CSS
mínimo passou em 390/1440. Build novo servido local/público, HTTP 200.

Typecheck/build PASS; frontend completo 342 PASS. Backend geral: 1.171 entradas,
1.167 PASS, dois erros por SDK MCP ausente e dois skips. Observer existente:
30 OK, incluindo pontos de erro e skip MCP; resta skip de symlink do Windows.
Não apresentar a execução nativa isolada como PASS nem esconder suas dependências.

Conector recarregado uma vez com autorização; Companion/OpenCode preservados.
Leitor de evidência de Cenas ganhou allowlist do novo lote somente em disco;
não foi reiniciado/ativado no backend operacional. Fichas/regras inalteradas.
V2 integrada no build corrigido: COMPLETED/PASS, seis API e quatro usos UI,
258,114 s. Seletor e forma ativa revisados nas novas capturas; fixture encerrada.
Detalhes e limites em `VAMPIRIC_UI_CHECK_2026-10-20.md`. Mesa multirrede ainda
sem prova. Próximo lote natural: invocações/magias de Morthak pela UI, mantendo
bloqueios legítimos por recurso ausente e sem reabastecer produção para QA.
