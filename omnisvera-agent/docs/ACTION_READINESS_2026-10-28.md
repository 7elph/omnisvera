# Ações: integração visível e consulta confiável

A Cola de ações do Mestre passa a combinar a ficha efetiva com o manifest nativo
GM já existente. Os estados distinguem comando integrado, indisponibilidade atual,
arbitragem e passiva. Nenhum deles significa certificação de combate completo.
Em falha da consulta de automação, as descrições permanecem disponíveis com
“Automação não verificada”. Troca de personagem e fechamento descartam respostas
antigas. Ambas as leituras usam timeout existente; a ficha é consultada com
`read_only=true`, sem reconciliação/migração por consequência da consulta.

Os comandos conhecidos de uso de item são descritos pelos executores atuais:
Pulseira de Vinhas, Reparo via kit e itens utilizáveis com regras `on_use`
compatíveis com o consumidor nativo. Nome parecido ou mera existência de cargas
não promove um item desconhecido a automático. Equipamento, estoque e cargas
continuam limitando disponibilidade. Validação final pertence ao handler.

Custos explícitos da ficha efetiva, inclusive zero, prevalecem sobre o fallback
legado de sangue. As cinco armas, suas habilidades e passivas são projetadas na
Cola pelos metadados existentes da Hemomancia. Habilidades retiradas da ficha
ficam fora da consulta; não são removidas do banco ou do catálogo histórico.

Não há novo executor, regras de RPG, concessão de habilidades ou modificação de
fichas reais. Comando integrado não garante que todos os efeitos e condições
de uma passiva foram comprovados. A certificação continua em `sheet_rehearsal`
e nos recibos dos ensaios MCP, separada desta projeção de leitura.

Arquivos: `native_action_manifest.py`, `sheet_action_inventory.py`, rota de
leitura em `main.py`; `api.ts`, `actionReference.ts`,
`components/CharacterActionReference.tsx` e testes correspondentes.

O escudo compartilha um único comando e aparece na consulta como Bastião
Carmesim, acompanhando a habilidade atual; não ganha uma segunda ativação.
Ícones ausentes em `SheetDetail` deixam o nome legível e não exibem uma imagem
quebrada; trocar a imagem permite uma nova tentativa normalmente.

Validação específica: `action-reference-loading.test.cjs` e
`action-reference.test.cjs` cobrem consulta atrasada, falha parcial, descarte no
fechamento e apresentação conservadora; `test_native_action_manifest`,
`test_action_audit_routes`, `test_action_manifest_main` e
`test_sheet_certification` cobrem executores, estoque/custo e privacidade.
`action-readiness-smoke.cjs` é um smoke local da consulta em fixture TEMP;
não é um novo lote MCP nem prova de execução das ações de combate. O ensaio
nativo de combate continua usando `companion_test_start`, quatro atores e
`ui:true`, com recibo próprio e revisão explícita das capturas.

## Resultado

Disponível em **Mestre → Cola de ações**. A ficha principal mantém seus controles.

- Backend: suíte completa, 1600 testes, 1 skip, OK. Depois da revisão do nome
  do escudo e do teste de leitura imutável, 49 testes focados aprovados.
- Frontend: 437/437; typecheck e build aprovados. Aviso de chunks grandes já existente.
- MCP `test-d360439568c742cb85d9176da58c3d9a`: PASS; 89 cenários de API
  aprovados, 2 bloqueios esperados (ataques à distância sem arma equipada de
  Vezemir e Morthak), zero falhas. Os três scripts do lote combat passaram;
  execução visual explícita de dez ações de Vezemir/Morthak/Dorn, e identidade
  de Raziel. Capturas revisadas pelo agente.
- Consulta: PASS nas quatro fichas, em 1440/390 px, com falha/retry de manifest,
  privacidade e ausência de comandos de jogo; capturas revisadas.
- Ativação: backup e reinício somente do backend; 21 tabelas protegidas e tokens
  preservados. Somente `updated_at` de mapas variou, sem alteração de conteúdo.
  Frontend publicado mantendo os chunks anteriores para clientes abertos.

`certification_ready` continua **false**: o lote não prova todos os caminhos de
todas as passivas ou todo o catálogo. Não foi introduzido um motor universal de
magias neste corte. Celulares físicos e mesa com redes externas seguem sem prova.
Não houve staging, commit ou push; fichas reais não foram ajustadas pelos ensaios.
