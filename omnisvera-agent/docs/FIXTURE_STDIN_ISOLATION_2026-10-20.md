# Isolamento da entrada da fixture — 20/10

Escopo: ferramentas de QA; sem alterações de regra, fichas ou runtime operacional.

## Evidência e corte

O ensaio MCP anterior expirou em 45 s antes de `cf01_module_entry`, com log
do servidor vazio. Probes diretos do Python e `cf01_probe --help` iniciaram,
portanto isso não comprovava defeito de ficha nem ausência de dependência.

O `Popen` da fixture herdava stdin do runner, por sua vez lançado pelo host MCP
de longa duração. O servidor de teste não precisa ler entrada. A alteração mínima
define `stdin=subprocess.DEVNULL` somente nesse lançamento, mantendo stderr/stdout
no log privado existente, ambiente isolado, porta, timeout e cleanup originais.
Não há detach novo, shell alternativo, remoção de lock ou reload de conector.

Teste RED capturou os argumentos do lançamento sem criar processo, socket ou
copiar banco operacional; antes, stdin era herdado (`None`). Após o patch,
26 testes focados concluíram com 1 skip do SDK no ambiente backend. O contrato
MCP foi repetido no ambiente observer com o SDK instalado e passou.

Repetição nativa pelo mesmo conector OpenCode, request
`codex-friday-combat-ui-20261020-v2-stdin`, quatro atores, `ui:true`, lote `combat`:
`test-d5191e1dc8014e7b82ee76e158fb8273`. A fixture chegou a
`fixture_health_ready` dentro do prazo e avançou aos cenários API. Isso comprova
que o bloqueio anterior não reapareceu nessa tentativa; não isola sozinho toda
causa de uma falha intermitente em máquina com RAM pressionada.

## Resultado terminal

`COMPLETED/PASS`, exit 0, duração 1.199,86 s, dentro do teto de 20 minutos
(muito próximo do limite; não ampliar o prazo). API: 88 PASS, zero FAIL e três
EXPECTED_BLOCK: ataques ranged genéricos sem arma de Vezemir/Morthak e Clonagem
sem cristal. Não se entregou componente na campanha para eliminar bloqueio legítimo.

UI `combat`: PASS nos três scripts, sem retirar casos:

- Readiness das quatro fichas, Mestre/jogador, 360/390/1440 px: 176,667 s.
- Vezemir: Força Arcana, Velocidade, Frenesi e Provocação; Morthak:
  Aterrorizar: 102,918 s.
- Dorn: Força Arcana, Reflexos, Teia, Dissipar Magia e Guarda: 148,264 s.

Os dez usos foram realizados pela UI, com comando único, consequência,
consumo quando aplicável e estado mantido após reload. Não atribuir esse
resultado às demais habilidades por associação.

Capturas novas foram explicitamente inspecionadas: identidade/CA/dados de
Morthak, Vezemir, Raziel e Dorn; ações Provocação, Aterrorizar e Guarda.
Retratos e CA não apresentam a antiga sobreposição. Existem ainda imagens
derivadas do catálogo ausentes na fixture (ex.: ícones de Adaga/Relâmpago e
alguns itens com fallback). Não certificar toda a mídia a partir do PASS.

`certification_ready=false`: o relatório preserva 35 lacunas de evidência por
ação, não 35 defeitos comprovados. Este lote não executa armas de Hemomancia
pela UI, comércio, mapas/zoom completos, todas as passivas ou mesa multirrede.
Para o próximo lote UI, selecionar explicitamente cenários API já observados
em vez de repetir os 13 minutos de API: resultados anteriores ficam preservados
e não podem ser fundidos silenciosamente numa certificação integral.

Discover backend completo e typecheck/build não repetidos neste corte de QA;
nenhum frontend ou código da API operacional mudou. Último typecheck/build
PASS é da correção de CA da etapa anterior. `git diff --check` restrito: limpo.

## Arquivos deste corte

- `backend/scripts/run_sheet_test.py`: somente stdin da fixture.
- `backend/test_fixture_startup_checkpoints.py`: regressão do lançamento.
- Este relatório e atualização do quadro de fechamento.

Sem restart operacional, edição de banco/ficha, commit ou push.
