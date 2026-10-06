# DORN-7 — três protocolos aprovados

## A. Estado e preservação

HEAD inicial: `eb20a2c4e6f396032d7a89f778e2ab1d509713de`.
Branch: `devin/create-omnisvera-class-standard`.
Working tree já continha o corte de identidade de Dorn e alterações anteriores de combate/Raziel/invocações. Nenhum staging, commit, push, migração de personagem ou reinício operacional nesta etapa. Vault, CAMPANHA, .autonomy, mídia e banco operacional não editados.

O corte anterior foi preservado: traços, sistemas, componentes, efeitos e navegação para Magias. Protocolos entram somente na ficha com `approved_build` da família `dorn-mage`; a promoção legada mantém Proteger e seu contrato anterior.

## B. Infraestrutura reutilizada

- `combat_effect_commands`: request_id, fingerprint, versão e transação SQLite.
- `combat_effects`: efeitos sem modificadores, com metadados de protocolo.
- `combat_effect_clock`: participante atual, ação comprometida, orçamento e sequência de turno.
- Resolver/confirmador de ataques: CA efetiva, dados, dano, efeitos e persistência existentes.
- `resolve_character_roll` e `roll_formula`: fórmula real de INT. O resultado do diagnóstico é persistido no comando e ledger GM, não em um novo subsistema de dados.
- `require_master` e controle GM da ficha. Nenhuma reescrita de permissões.

## C–D. Comportamento automático e assistido

### Guarda

Somente no turno de Dorn, com ação inteira disponível, sem ataque pendente válido e com aliado personagem vivo na iniciativa. Mestre confirma posição plausível. Gasta a ação e persiste um efeito sem bônus.

No painel de ataque do inimigo, selecionar o aliado protegido permite marcar **Interpor Dorn** antes de rolar. O backend valida a Guarda, troca o alvo para Dorn, usa sua CA efetiva e consome o efeito na mesma transação que grava a resolução. A confirmação aplica dano em Dorn pelo fluxo normal. Repetição da mesma requisição não rerrola; outro ataque não reutiliza a Guarda consumida.

Expira ao início do próximo turno de Dorn ou ao encerrar o combate. Não depende de diminuir uma duração global de uma rodada. Ataques adicionais devem ser resolvidos separadamente; uma interposição protege apenas um ataque.

Posicionamento, elegibilidade espacial e consequências não automatizadas pela ficha continuam sob decisão do Mestre. Resistências passivas anteriormente assistidas não ganharam um mecanismo novo.

### Vanguarda

Ativação em exploração; pode ser desativada inclusive depois de começar combate. Persiste como efeito de cena sem modificadores. Expira pelo comando existente de encerramento de efeitos de cena; não foi criado um gancho novo de formação/cena. O Mestre continua responsável por declarar a primeira exposição física e por perigos em área. Não detecta armadilhas nem modifica ficha.

### Diagnóstico

Mestre informa mecanismo/componente e dificuldade. Backend usa o teste de INT da definição atual, rola e registra total, dificuldade e sucesso/inconclusivo. Em combate exige turno e consome ação; em exploração não utiliza orçamento de combate. Nenhuma informação narrativa é produzida automaticamente; o campo `information` permanece vazio e o Mestre decide a informação objetiva revelada.

## E. Arquivos deste corte

Criados:

- `backend/app/dorn_protocols.py`: catálogo aprovado e execução na transação de efeitos.
- `backend/test_dorn_protocols.py`: regressões de protocolos e ensaio HTTP descartável.
- `frontend/src/components/DornProtocolControls.tsx`: controles compactos com lock/retry.
- `frontend/tests/dorn-protocols.test.cjs`: regras de disponibilidade e comandos da UI.
- `docs/DORN_PROTOCOLS_REVIEW.md`: este relatório.

Alterados, preservando diffs anteriores:

- `backend/app/character_play.py`: catálogo condicionado à ficha aprovada.
- `backend/app/combat_effects.py`: execução, autorização, expiração e resultado persistido.
- `backend/app/combat.py`: interposição explícita, consumo atômico e replay protegido.
- `backend/app/main.py`: definição de INT confiável e validação/troca de alvo GM.
- `backend/app/schemas.py`: comandos e campo opcional de interposição.
- `frontend/src/api.ts`: metadados e resultado de protocolo.
- `frontend/src/components/DornUnitIdentity.tsx`: integra controles e estado ativo sem duplicar catálogo.
- `frontend/src/components/MonsterAttackPanel.tsx`: confirmação antes da rolagem e alvo resolvido.
- `frontend/src/components/CombatEncounterPanel.tsx`: fornece efeitos somente ao painel GM.
- `frontend/src/pages/SessionWorkspace.tsx`: atualização da ficha e exclusão dos protocolos do botão genérico de técnicas.
- `frontend/src/styles.css`: inputs sem overflow, botões mobile e layout compacto.
- `frontend/tests/dorn-unit-visual.cjs`: QA de estados ativos/desabilitados.

## F. Verificação

14 testes novos de backend e 6 de frontend. Cobrem consumo, replay, orçamento real de batalha, alvo/CA de Dorn, dano confirmado, segundo ataque, expiração, autorização, Vanguarda sem bônus e Diagnóstico sem lore.

Comandos executados nesta etapa:

```powershell
.\.venv-observer\Scripts\python.exe -B -m unittest discover -s backend -p 'test_*.py'
cd frontend
node --test tests/*.test.cjs
npx --no-install tsc --noEmit
npm run build -- --outDir "$env:TEMP\companion-dorn-protocol-build"
node tests/dorn-unit-visual.cjs
git diff --check -- backend frontend docs
```

Resultados executados novamente: backend **303/303 PASS** (última execução: 85,330 s); frontend **126/126 PASS**; TypeScript **PASS**; build isolado **PASS**; `git diff --check` **PASS**. Não reutilizar números desta etapa como validação futura. Avisos já observados de conexões SQLite não fechadas em outros testes e chunks grandes do Vite permanecem fora deste corte.

## G. QA

Navegador Edge headless, componente React real com CSS real e fixtures, sem API operacional: 390×844 e 1440×900. Cinco seções recolhidas; expansão, Guarda ativa, duração, botões bloqueados e ausência de overflow horizontal observados. Screenshots em `%TEMP%/companion-dorn-visual-5V1Afq`.

Isto é QA isolado da ficha, não prova de mesa multicliente nem teste em aparelho físico. Backend/API foram exercitados separadamente com SQLite e identidades descartáveis.

## H. Fora do corte

Reparo, memória, núcleo, comunicação, novas imunidades/resistências, ataques antigos, grid e morte continuam sem implementação. Nenhuma regra nova desses assuntos foi decidida.

## I. Balanceamento

Nenhum protocolo aumenta permanentemente PV, CA, dano, atributos, slots, resistências ou imunidades. Guarda e Diagnóstico gastam a ação em combate; não concedem ataques adicionais. Vanguarda é um estado de exploração assistida, sem modificadores. Servidor e frontend operacional não foram substituídos: pronto em código/testes para revisão, ainda não ativado na mesa.
