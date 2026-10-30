# Teste de ficha completa — primeiro corte

O operador previsto agora é **outra IA**: ferramentas e contrato em
`AI_TEST_TOOLS.md`. Os comandos abaixo continuam disponíveis como fallback
de desenvolvimento; não são passos que o Mestre precisa executar na mesa.

## Usar

Na pasta do Companion, sem desligar a mesa:

```powershell
.\test_sheet.ps1
# Outro personagem ou todos os quatro:
.\test_sheet.ps1 -Personagens raziel,morthak,vezemir,dorn7
```

O padrão começa por Raziel e Morthak. Não é um teste rápido de poucos segundos:
os cenários fazem chamadas HTTP, confirmações e retries concorrentes reais.
O terminal informa `ISOLATED_EVIDENCE` e `REPORT`. Abra `sheet-test-report.md`
na pasta indicada para ler os resultados. JSON permite consumo por outra IA.

Equivalente sem PowerShell, com Python/dependências do backend:

```powershell
.\.venv-observer\Scripts\python.exe backend/scripts/run_sheet_test.py --actors raziel morthak
# Repetir um cenário específico usando seu scenario_id exato:
.\.venv-observer\Scripts\python.exe backend/scripts/run_sheet_test.py --actors vezemir --scenarios "vezemir:Poção de HP + ataque no mesmo turno"
```

Porta padrão 8871. Se ocupada, o comando recusa a execução, sem matar serviços.
Pode escolher `-Porta 8872` / `--port 8872`. 8787 e 8788 são recusadas.
O banco fonte só é aberto em modo leitura para backup consistente; banco,
vault e credenciais de ensaio são isolados no TEMP. O indexador externo é
desligado pela fixture CF-01 existente. Não lê tokens operacionais.
Ao terminar, encerra somente a árvore do servidor que o comando criou.
Evidências permanecem no TEMP para inspeção; não são incluídas no Git.

## O que o relatório significa

- **PASS:** os cenários citados daquela entrada passaram nesta execução.
- **FAIL:** ao menos um cenário associado falhou; sucesso em outro não o esconde.
- **PENDING:** entrada real da ficha ainda sem ensaio/contrato executável.
- **ASSISTED:** passiva sem ensaio; não é prova de automação.
- **RULE_BLOCKED:** habilidade cadastrada como bloqueada pela regra atual.
- **UNAVAILABLE:** houve rejeição esperada, não execução bem-sucedida.

Lista todos os ataques, habilidades visíveis, recursos e itens das fichas
selecionadas. Não interpreta `mechanics_status=structured` como implementação.
Equipamento/passiva sem cenário continua pendente, mesmo que conste na ficha.
Ataque pode comprovar o uso da arma indicada no breakdown nativo; isso não
certifica equipar/desequipar ou todas as propriedades do item. Cards de recurso
apontam aos cenários do contador correspondente, não a uma ação inventada.
`all_actions_certified` só é verdadeiro se todas as entradas tiverem PASS;
mesmo assim, PASS certifica os cenários citados, não todos os casos possíveis.

## Contrato de teste e evidência

`sheet_rehearsal.py` monta o inventário por allowlist a partir do DTO nativo
`GET /characters/{profile_id}`. Não cria catálogo paralelo de regras.
Cada cenário do executor existente declara `covers` (`attack:`, `ability:`,
`resource:`, `item:`), recebe um `scenario_id` e guarda comandos HTTP,
verificações efetivamente completadas, snapshots e resultado.

`all_actions_simulation.py` segue sendo o executor de ações nativas: não aplica
dano, custos ou duração em um segundo motor. SQL na fixture é apenas preparação
de casos independentes e leitura da persistência, nunca resolução alternativa.
HP/recursos são restaurados entre casos; isso não dá usos extras na campanha.

Verificações adicionais deste corte:

- erro crítico com d20=1, sem dano;
- dano/custo dos novos ataques de sangue contra os valores aprovados;
- prévia sem dano/custo e confirmação idempotente;
- drenagem limitada ao dano efetivo e PV máximos;
- ausência de recursos, incluindo diário/círculo de Toque, sem mutação;
- outro proprietário rejeitado e orçamento de ataque do turno respeitado;
- custos de consumíveis e ataque no mesmo turno;
- nova leitura por cliente HTTP, paridade Mestre/proprietário e PV/recursos no SQLite;
- cenários já existentes de efeitos/expiração, movimento, invocação e Caixão.

`sheet-test-report.json/.md`: inventário e resultado compacto.
`all-actions-evidence.json` e `all-actions-log.md`: consequências detalhadas.
São artefatos locais privados; o JSON detalhado pode conter dados do Mestre
da cópia. Não enviar esses arquivos aos jogadores nem publicá-los.

## Limites deliberados

Sem botão novo na produção, sandbox de Cenas, importação de PDFs ou IA autônoma.
O launcher suporta os quatro personagens com adaptadores existentes; uma ficha
arbitrária ou uma habilidade nova precisa de adaptador/cenário, não execução
por interpretação de texto. Sem balanceamento novo nem regras inventadas.
Monstro padrão: Hobgoblin do catálogo nativo. Seus atributos 10 são declaração
de fixture porque a entrada não traz escores; não alteram o bestiário/canon.

O ensaio HTTP não substitui a validação visual da ficha. O smoke de navegador
existente `frontend/tests/combat-simulation-physical-smoke.cjs` pode ser usado
com `--keep-server` em 8871 e `OMNISVERA_SIMULATION_EVIDENCE` apontando ao JSON
detalhado. Requer Playwright e mídia disponível na cópia; esse smoke é específico,
não testa automaticamente todas as entradas do inventário.
Sem prova de dados físicos rolados por pessoa ou endurance em redes distintas.

Nenhuma alteração nos handlers operacionais: não requer restart de 8787.
Próximo corte: adaptadores/casos para entradas PENDING, depois exposição privada
do relatório no laboratório, preservando cenas e APIs já existentes.
