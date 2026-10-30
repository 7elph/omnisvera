# Certificação das quatro fichas — primeiro corte

Ferramentas existentes `companion-tests`; sem painel novo para jogadores,
sem motor paralelo e sem ações no banco operacional. Leia `AI_TEST_TOOLS.md`.

## Contrato

- `verdict=PASS`: passaram os cenários realmente executados.
- `certification_ready`: prova por ação ativa, quatro atores e UI aprovada.
- `report.certification.gaps`: ator, chave da ação, status e verificações faltantes.
- Verificações: execução, persistência, idempotência, custo, alcance, expiração e UI.
  Custo e expiração são exigidos conforme os metadados/obrigações do teste.
- Só uma mutação aceita e persistida durante a ação comprova execução. Preparar
  a fixture, consultar alvos ou abrir um card não comprova aplicação.
- PASS de layout não certifica todos os cards: provas visuais são por ator/ação.
  O protocolo de UI não pode atribuir a si mesmo prova de custo backend.
- Falha nunca desaparece atrás de outro PASS. Bloqueios e disponibilidade são
  separados de defeitos. As notas privadas não entram na matriz pública do teste.
- Fingerprints ligam o resultado à ficha/inventário/nível carregados; recibo antigo
  não certifica alterações posteriores. Redes distintas/celular físico: INCONCLUSIVE.

Inventário, recursos e passivas continuam listados. `ASSISTED` é classificação
conservadora do executor, não prova de que uma passiva do produto seja manual.
`READY` cobre o contrato de testes declarado, nunca todas as combinações de RPG.
Regras não aprovadas de Raziel não são inventadas para fazer a matriz ficar verde.

## Cobertura adicionada

- Dorn: Reflexos, Teia, Força Arcana, Dissipar Magia; custo e efeito/encerramento.
- Vezemir: Frenesi manual/expiração e Provocação no grid/fim de combate.
- Morthak: Clonagem com componente real e Magia da Morte com custo de PV.
- Raziel: ficha animal aprovada nas três formas e retorno à ficha normal.
- A consulta de alcance é evidência de alcance, não de execução do ataque.
- Os oito scripts visuais existentes são aproveitados. Provas por ação só são
  anexadas quando o script realmente concluiu o fluxo correspondente.
- O ID histórico do cenário de Toque Sombrio foi preservado, embora o título
  agora diga dano inicial; não volta à perda de FOR antiga.

## Uso por outra IA

Iniciar os quatro atores com `ui: true`, aguardar conclusão e ler as lacunas.
Usar IDs exatos de cenário para repetir casos. Não conceder itens, restaurar
recursos, mudar níveis/regras ou reiniciar a mesa em consequência de um FAIL.
As declarações de atributos do monstro são somente da fixture do ensaio.

Referência anterior: MCP `test-1582e794393d40a5ae547ed997c8fe5b`,
70 PASS + 2 EXPECTED_BLOCK e oito scripts visuais PASS. Não era certificação
integral de cada ação. Resultados da versão ampliada registrados após validação.

O ensaio ampliado `test-44978914ac8a49cbbc66936c5c3d54f9` teve 79 PASS,
três rejeições previstas e oito scripts visuais PASS, mas a matriz permaneceu
INCOMPLETE. A investigação mostrou que os quatro casos antigos de consulta de
alcance retornavam modo assistido devido a pins antigos em outros mapas. Antes
eram PASS; a matriz nova corretamente não atribuía prova de alcance a eles.
O executor foi corrigido para enviar mapa/pin explícitos e rejeitar fallback
manual como prova de grid. Dois testes RED reproduziram a falha e ficaram GREEN.
O ensaio completo foi repetido após essa correção; histórico anterior preservado.

Checks de código: backend final 799 PASS; frontend 277 PASS; typecheck e build
PASS. Avisos existentes de SQLite não fechado e chunks >500 kB permanecem fora
deste corte. Não foi necessário reiniciar o backend operacional: nenhum módulo
de execução de regras ou rota do Companion foi modificado.

Arquivos alterados:
- `backend/scripts/{sheet_rehearsal,all_actions_simulation,run_sheet_test,agent_test_jobs,companion_test_mcp}.py`;
- `backend/test_sheet_certification.py`, `backend/test_sheet_rehearsal.py`, `backend/test_agent_test_tools.py`;
- `frontend/tests/{grid-action-flow,range-multitarget,approved-spells}-smoke.cjs`;
- `docs/AI_TEST_TOOLS.md`, `docs/CURRENT_COMPANION_CODE.md` e este guia.

## Resultado final

MCP `test-40f5a948809247f18df6b90bd817f0ff`: COMPLETED/PASS,
79 cenários PASS, três EXPECTED_BLOCK, oito scripts visuais PASS. Os quatro
casos de consulta de alcance agora comprovam grid real, com pin/mapa explícitos.
Capturas atuais de Morthak no celular e Vezemir no desktop foram inspecionadas.

`certification_ready=false`, status INCOMPLETE. Existem 45 entradas ativas no
catálogo das quatro fichas; três cumprem todas as exigências desta matriz hoje.
Isso **não significa que 42 falharam**: são lacunas de prova, bloqueios ou ações
cujo uso ainda não foi exercitado integralmente pelo frontend no mesmo contrato.

| Ficha | Entradas ativas | Contrato completo comprovado |
|---|---:|---:|
| Vezemir | 6 | 1 |
| Morthak | 11 | 0 |
| Raziel | 16 | 0 |
| Dorn | 12 | 2 |

Faltam provas por ação de UI (38 entradas), alcance (12), expiração (6), custo
(10) e execução/persistência/idempotência (5 cada); categorias podem se sobrepor.
O JSON/Markdown privado do ensaio identifica cada chave e seus requisitos faltantes.

As três rejeições esperadas foram Vezemir/Morthak sem arma à distância equipada
e Clonagem sem fragmento na ficha copiada. Não foram concedidos equipamentos ou
componentes à mesa para forçar aprovação. Corpo Predatório, Técnica de Predador
e Marca Rubra aprimorada continuam classificados conforme seus bloqueios de regra.

Limites: a fixture não contém toda a mídia do Vault, por isso retratos ausentes
nas capturas não certificam defeito da mídia operacional. Na revisão visual,
o resumo Base/equipamento/efeitos de alguns ataques não discrimina todos os bônus
do total exibido; fica registrado para o próximo corte de auditoria dos resultados.
Nenhuma regra/cálculo foi alterado por causa dessa observação.

Próximo corte seguro: ampliar a prova de UI e consequências das ações faltantes,
por famílias de mecânica, e padronizar o detalhamento de bônus. Não confundir a
certificação do ensaio com aprovação de estabilidade em redes externas.

Nenhuma ação foi executada na mesa real; sem commit ou push.
