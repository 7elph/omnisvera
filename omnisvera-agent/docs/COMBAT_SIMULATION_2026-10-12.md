# Ensaio de combate — 12/10/2026

Este é o ensaio inicial, anterior à aprovação dos novos poderes. O fechamento
posterior de Caixão, kits, modos das adagas e conexão dos poderes está em
`ACTION_COMPLETION_2026-10-12.md`; os bloqueios abaixo são evidência histórica,
não o estado final desses controles.

## Limites da evidência

Ensaio HTTP real e navegador Edge, somente numa cópia descartável do SQLite.
Não iniciou combate, concedeu itens, rolou PV ou alterou personagens na campanha.
Cada caso restaura PV/contadores na cópia: não representa usar todos os poderes
no mesmo turno ou sem descanso. O d20 físico foi digitado como 15 pelo teste,
não rolado por uma pessoa. Dano e JP continuam usando os mecanismos atuais.

Adversário: Hobgoblin do bestiário nativo Old Dragon 2 SRD, PV 6, CA 11,
JP 5, DV 1+1, movimento 9 m, ataque +3, dano 1d8+1. A fonte não traz
atributos numéricos: FOR/CON/DES/SAB 10 são declarações exclusivamente da
fixture para exercitar testes, não adições ao cânone.

## O que foi corrigido neste corte

- Lâmina de Sangue respeita modo Físico, envia d20 declarado e rejeita
  entradas inválidas; não força mais rolagem digital.
- Marca Rubra conserva request_id no retry, inclusive quando a ação foi
  aceita mas a atualização da tela falhou.
- Forma da Noite e demais ações genéricas com request_id têm recibo
  transacional: duas chamadas simultâneas gastam uma vez. Retorno da forma
  também é recuperável; retry não duplica mensagem pública. A ficha conserva
  esse request_id até a atualização da tela terminar, inclusive após erro de leitura.
- Diagnóstico de Dorn ignora apenas a versão de ficha derivada pelo servidor
  na identidade do comando. Retry recupera a mesma rolagem; mudar a
  dificuldade ou o assunto não pode reutilizar o recibo.
- Pinar novamente um personagem já colocado no grid não dispara conflito
  SQLite nem altera sua célula autoritativa.

## Cobertura e lacunas

| Personagem | Executado no ensaio nativo | Limites / pendências |
|---|---|---|
| Vezemir | Grisalma, movimento, Força Arcana, Velocidade e expiração, pulseira/JP, poção e ataque no mesmo turno | Ataque à distância sem dano configurado; especialização ainda sem escolha |
| Morthak | Cajado, Adaga de Osso, movimento, mísseis nv5, levantar esqueleto, animar cadáver, ataque da invocação, Toque Sombrio, Aterrorizar, poção | Ataque à distância genérico sem dano; passivas/racial e afastar mortos-vivos não certificados como automáticos |
| Raziel | Adagas e cura, movimento, Lâmina 1–5d4, Mordida/cura, regeneração, Marca Rubra, anel, ligar/desligar Forma da Noite, poção | Corpo a corpo comum sem dano; estatísticas/restrições da forma animal assistidas; Caixão do jogador tenta descanso reservado ao Mestre e é bloqueado |
| Dorn | Ataques, movimento, quatro magias, Guarda e expiração no próximo turno, Vanguarda, Diagnóstico, Reparo e ataque | Reparo exige Kit de Reparo: ausente no inventário real. Caso positivo usa kit só na fixture; Diagnóstico revela informação por arbitragem do Mestre |

O catálogo completo é exportado com classificação por habilidade: cenário
nativo, regra bloqueada, descanso bloqueado, ou passiva/assistida não
certificada. `mechanics_status=structured` sozinho não prova automação.

O worktree já contém Arma de Sangue, Garras Predatórias, Investida Predatória,
Sangue Defensivo e Faro, inclusive valores descritos como proposta. O ensaio
avalia esses caminhos existentes no backend, mas não aprova o balanceamento.
Os novos ataques e Sangue Defensivo ainda não têm encaminhamento específico
no `useAbility` da ficha; seu botão genérico pode apenas registrar texto.
Isso é uma lacuna, não um poder validado ponta a ponta. A proposta de formas
espada/lança/escudo está em `RAZIEL_BLOOD_WEAPONS_PROPOSAL.md` e não foi aplicada.

Mísseis atuais: uma resolução automática `1d4+min(nível,5)` por uso.
Morthak equipado tem quatro usos; Dorn três. Isso não prova quatro projéteis
por conjuração. Confirmar a intenção de “3 mísseis +1” antes de mudar dano.
Também permanecem nove rolagens de PV pendentes no nivelamento dos quatro.

## Como ver ação e consequência na mesa

1. Mestre: **Mesa → personagem no header**. Jogador: **Ficha**.
2. Leia o card e confira alvo, equipamento, recurso e disponibilidade do turno.
3. Em mesa Física, digite o d20 no ataque/poder que o solicita.
4. Clique **Usar** ou **Preparar magia → Conjurar**. Ataques abrem prévia;
   só **Confirmar** aplica dano/custo. Não clique de novo para refazer o dado.
5. No **Registro**, filtro **Ações**, clique **Ver resultado** para consultar
   consequências. Efeitos duradouros aparecem nos indicadores existentes.
6. Falha de leitura não significa ação rejeitada: recupere a prévia pendente
   e confira o registro antes de iniciar outro comando.

Mestre e proprietário compartilham dados de nível, atributos, ataques,
defesas, habilidades, recursos e inventário. O teste de navegador executou
Toque pelo proprietário em 390 px e Lâmina pelo Mestre em desktop, conferiu
um preview/custo, atualização em outro cliente sem refresh e persistência
após reload. Extras privados/administrativos do Mestre não são expostos.
Não se alegou prova de uma mesa em redes externas distintas.

### Resultado desta execução

- HTTP: **41 PASS, 0 FAIL, 5 EXPECTED_BLOCK**, 46 casos independentes,
  incluindo as técnicas existentes no backend de Raziel ainda propostas.
- Bloqueios: três ataques genéricos sem dano, Reparo sem kit real e descanso
  do Caixão pelo proprietário. Não foram convertidos em sucessos fictícios.
- Backend: **601 testes passaram**; há ResourceWarnings de conexões SQLite
  não fechadas em fixtures antigas da suíte. Não equivalem a falha de teste,
  mas permanecem como dívida de limpeza; não foram escondidos.
- Frontend: **242/242**. A execução intermediária encontrou cinco falhas do
  mock de React no seletor de alvo; corrigido o mock, sem remover as asserções.
  Os dois testes novos de recibo genérico também falharam antes da correção e
  passaram depois (RED/GREEN).
- Typecheck e build passaram; smoke Physical/Mestre-proprietário passou na
  versão final. Build mantém aviso de chunks maiores que 500 kB; sem
  refatoração de bundle.
- Backend operacional reiniciado por autorização já concedida, backup
  privado preservado. Comparação exata confirmou tokens e 13 tabelas de
  fichas/inventários/cenas/sessões/efeitos/pins/posições/grid/ledger intactos.
  GETs autenticados locais e públicos de Mestre e dos três proprietários
  responderam 200. Não executar ação de combate no operacional para QA.
- Ao fechar o ensaio, o lançamento inicial da produção também caiu. Foi
  restaurado com o inicializador oficial em processo destacado/grupo separado;
  repetidas verificações públicas e comparação das 13 tabelas passaram.
  O túnel não foi encerrado. A fixture 8871 foi desligada ao terminar.
- O log acumulado da fixture incluiu erros de imagem indisponível. A cópia
  de 64 assets e o smoke mecânico não certificam 100% da biblioteca de mídia.

## Arquivos deste corte

Alterações localizadas em arquivos que já continham outros trabalhos:

- `backend/app/character_play.py`, `combat_effects.py`, `main.py`,
  `session_workspace.py`.
- `frontend/src/pages/SessionWorkspace.tsx`.
- `frontend/tests/combat-controls.test.cjs`, `raziel-vampire-powers.test.cjs`,
  `target-select.test.cjs` (mocks/assertivas compatíveis com UI atual).

Novos arquivos:

- `backend/scripts/all_actions_simulation.py`.
- `backend/test_simulation_regressions.py`.
- `frontend/tests/blood-technique-physical.test.cjs`.
- `frontend/tests/state-action-retry.test.cjs`.
- `frontend/tests/combat-simulation-physical-smoke.cjs`.
- Este relatório e `docs/RAZIEL_BLOOD_WEAPONS_PROPOSAL.md`.

Worktree misto preservado na branch solicitada, base atual `1a07a84`.
Sem staging, commit ou push neste corte. Artefatos/backup/credenciais ficam
fora da publicação. Não atribuir ao corte todas as alterações do git diff.

## Reproduzir / entregar ao OpenCode

Na raiz do Companion, preparar banco em uma pasta nova dentro do TEMP:

```powershell
$simFolder = Join-Path $env:TEMP ('omnisvera-combat-' + [guid]::NewGuid().ToString('N'))
New-Item -ItemType Directory -Path $simFolder
$simDb = Join-Path $simFolder 'simulation.sqlite3'
.\.venv-observer\Scripts\python.exe backend/scripts/cf01_probe.py prepare --database $simDb
.\.venv-observer\Scripts\python.exe backend/scripts/cf01_probe.py serve --database $simDb --port 8871
```

O último comando permanece ligado. Em outro terminal, mesma pasta/banco:

```powershell
.\.venv-observer\Scripts\python.exe backend/scripts/all_actions_simulation.py --database $simDb --port 8871
```

O script recusa banco fora de TEMP e comprova que HTTP e SQLite apontam à
mesma fixture. Se 8871 estiver ocupado, inspecionar antes; não matar serviço
desconhecido. A cópia pode não conter mídia: o preparo copia banco/notas,
não todos os arquivos `zz_media`. Neste ensaio os 64 assets referenciados
foram copiados para o vault temporário; originais intactos.

Saídas privadas, fora de Git: `all-actions-evidence.json` com snapshots,
HTTP/recibos/ledger; `all-actions-log.md` com ações e deltas legíveis.
Para ensaio UI após o script, em `frontend`:

```powershell
$env:OMNISVERA_SIMULATION_EVIDENCE = Join-Path $simFolder 'all-actions-evidence.json'
# OMNISVERA_QA_MODULES deve apontar à pasta node_modules que contém Playwright.
node tests/combat-simulation-physical-smoke.cjs
```

O smoke usa somente loopback 8871 e credenciais públicas da fixture CF-01.
Para repetir após o smoke, execute novamente o ensaio HTTP (ele prepara um
novo encontro físico). Nunca usar tokens ou banco operacional nesses scripts.
