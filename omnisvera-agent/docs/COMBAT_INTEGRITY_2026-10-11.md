# Correções do combate após a Sessão 7

Regras confirmadas pelo Mestre: um consumível por turno, sem impedir atacar;
Morthak mantém apenas um esqueleto ativo. Nenhuma ficha real foi reescrita por
esta entrega. Testes e ensaios usam bancos temporários.

## O que mudou

- Ataques: rolagem, prévia e reserva do turno acontecem na mesma transação.
  Fechar a janela, mudar request_id ou usar outra aba não cria outro resultado.
  Confirmação repetida não aplica dano/custo novamente. Prévias antigas não
  podem ser confirmadas em um turno posterior, mesmo do mesmo personagem.
- Retomar: “Ataques aguardando confirmação” fica aberto quando há uma prévia.
  Confirme o resultado, incluindo erros. Se ela expirou, passe o turno; fechar
  a janela não devolve a ação. Encerrar o combate invalida prévias desse combate.
- Consumíveis: cura/recurso, gasto de quantidade/carga, recibo e narrativa são
  atômicos no inventário/ledger existentes. O slot é independente do ataque e
  limpa no próximo turno. Um retry usa a mesma chave e não bebe outra dose.
- Dorn: Reparo usa o mesmo slot de consumível, nunca a ação principal. Protocolos
  e magias verificam a reserva do turno atual, não prévias abandonadas de turnos
  anteriores. Reparo externo fora de combate pode reativá-lo; acima de 0 PV a
  condição Desativado é removida. A 0 PV ele não age/repara a si mesmo em combate.
- 0 PV: personagens, criaturas e invocações não atacam, conjuram ou usam ações
  de combate. Isto não decide morte definitiva de Morthak nem substitui suas
  características passivas. Intervenções administrativas do Mestre continuam.
- Raziel: Mordida exige alvo com sangue; Morthak, Dorn e invocações necromânticas
  não fornecem cura. Adagas espectrais preservam sua drenagem mágica após o
  ataque, limitada ao dano real e PV máximos. Erro não cura.
- Morthak: outro esqueleto vivo impede nova invocação, em qualquer mapa. Retry
  não gasta outro uso nem cria token; esqueleto a 0 PV pode ser substituído.
  Summons existentes continuam no sistema nativo de pins/combate.
- Vezemir: Força Arcana e Velocidade recuperam a ativação original após perda
  de resposta. Duração é rolada dentro da transação, apenas uma vez; retry não
  recalcula o bônus sobre a própria Força Arcana nem consome outro uso.
- Conexão: mutações de ataques, técnicas, turnos e itens têm limite de 30 s,
  inclusive leitura do corpo da resposta. Nunca repetem automaticamente escritas.
  Falha no refresh depois da aplicação não é apresentada como falha da ação.
- Dorn/JP: resultados das proteções do Relâmpago são mostrados junto do dano,
  inclusive cada contato. Continua usando as estatísticas e rolagens nativas.

## Validação reproduzível

Na raiz do Companion:

```powershell
.\.venv-observer\Scripts\python.exe -W ignore::ResourceWarning -m unittest discover -s backend -p "test_*.py"
cd frontend
node --test tests/*.test.cjs
npx --no-install tsc --noEmit
npm run build
```

Backend: 499 testes aprovados. Frontend: 221 testes aprovados. Typecheck/build
aprovados; build avisa sobre chunks >500 kB, sem falhar.

Ensaios: `frontend/tests/table-recovery-smoke.cjs` abriu o frontend compilado no
Edge com Mestre + Vezemir/Raziel/Morthak em contextos separados (players 390×844),
validou fichas próprias, combate, perda/recuperação de rede e próximo turno sem
reload. `backend/scripts/combat_integrity_probe.py` validou por HTTP poção+
ataque, Força Arcana/Velocidade com replay da duração, tentativa de rerrolar,
replay de confirmação, Mordida, esqueleto único,
ataque controlado, mísseis de Dorn e persistência após reconectar. Porta 8871,
credenciais de fixture e SQLite temporário obrigatório; nunca dados da mesa.

Limites: ensaio multicliente local não prova estabilidade em redes externas
durante uma mesa longa. Efeitos adicionais marcados como manuais continuam
dependendo de adjudicação; não se inventaram CDs/regras faltantes. Consumíveis
sem regras cadastradas não ganham cura por inferência. Esqueletos excedentes já
salvos não são apagados automaticamente. Alterações anteriores do worktree são
preservadas e não houve push/commit nesta entrega. O banco isolado não contém
todos os arquivos de imagem do Vault; erros de preview dessas mídias não
atestam falha no combate, mas a mídia completa não foi validada nesse ensaio.

## Ativação operacional

Reinício do backend 8787 autorizado e concluído em 11/10/2026. Backup SQLite
consistente e cópia das credenciais preservados em
`C:/Users/delib/AppData/Local/Temp/omnisvera-before-combat-fix-8d5516eea3fe4ca89d52eb64e8ce57a6/`.
Comparação de 70 tabelas: apenas `session_workspace_maps.updated_at` e
`session_workspace_presence.last_seen_at` mudaram; fichas, inventários,
sessões/cenas, combate, ledger, pins, fog e posições permaneceram iguais.
`PRAGMA quick_check = ok`; todos os tokens individuais e do Mestre iguais.

GET pelo domínio público retornou ficha `owner` para Vezemir, Raziel e
Morthak (520/166/150 ms nesta amostra). Frontend HTTP 200 servindo o bundle
validado `index-CQj_EN3l.js`. Esses checks partem desta máquina: não são prova
de conectividade dos celulares em redes externas nem de estabilidade prolongada.

## Arquivos desta correção

Backend: `app/battle_mode.py`, `app/combat.py`, `app/combat_effects.py`,
`app/combat_consumables.py`, `app/construct_rules.py`, `app/dorn_protocols.py`,
`app/dorn_spells.py`, `app/main.py`, `app/schemas.py`, `app/summons.py`;
`test_combat_integrity.py`, `test_dorn_construct.py`,
`test_hemomante_techniques.py`, `test_spectral_dagger_drain.py`;
`scripts/combat_integrity_probe.py`.

Frontend: `src/api.ts`, `src/writeJson.ts`, `src/pages/SessionWorkspace.tsx`,
`src/components/combatActionAvailability.ts`, `src/components/PendingAttacks.tsx`,
`src/components/DornSpellControls.tsx`, `src/components/MonsterAttackPanel.tsx`;
`tests/combat-integrity.test.cjs`, `tests/combat-controls.test.cjs`,
`tests/pending-attacks.test.cjs`, `tests/raziel-vampire-powers.test.cjs`,
`tests/workspace-read-timeout.test.cjs`. Este documento completa a lista.
