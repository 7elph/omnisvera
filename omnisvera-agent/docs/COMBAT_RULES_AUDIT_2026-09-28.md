# Conferência de combate — 28/09/2026

Este corte preserva fichas operacionais, Vault, adaptações existentes e alterações locais anteriores. Não é migração para OD2. Valores abaixo são uma fotografia conferida por API sobre cópia descartável do SQLite; podem mudar na campanha.

## Regras, estado e decisão

| Personagem / ação | Estado conferido | Referência / decisão | Tratamento neste corte |
| --- | --- | --- | --- |
| Vezemir / Grisalma | Nível 2; PV 17/17; corpo a corpo +2, 2d6; bônus de equipamento separado 0 | `Items/Grisalma.md` registra +2 de ataque da Sessão 4 | Não somar novamente sem reconciliar a origem do bônus atual. Ficha preservada. |
| Vezemir / distância | Sem arma e sem dano configurados | Ausência de ataque não autoriza inventar arma ou fórmula | Não criar ataque fictício. |
| Raziel / adagas | Nível 2; PV 16/16; corpo a corpo +1, distância +3; dano 1d4; bônus separado 0 | `Items/Adagas de Espectro Fantasma.md`: arremesso 3/6 e melhoria +2; drenagem ambígua | Preservar fórmulas; esclarecer bônus e drenagem antes de alterar. |
| Raziel / sangue | 4/5; Sentido de Sangue bloqueado | Decisão explícita do Mestre: máximo 5, Sentido bloqueado | Preservado. Recuperação de sangue e cura por drenagem ainda precisam de regra inequívoca. |
| Morthak / cajado | Nível 2; PV 3/4; ataque +0, 1d4 | Ficha e arma persistidas | Preservados; progressão de PV ainda requer escolha/rolagem prevista no fluxo existente. |
| Morthak / Mísseis Mágicos | Contador 1/3 na cópia operacional | `old-dragon-livro-basico-aprimorado-biblioteca-elfica.pdf`, página impressa 112: acerto automático, 1d4 + nível, novo projétil no nível 4 | Implementado no modo digital para níveis 1–3. No nível 2: **um** projétil, 1d4+2. Três usos não significam três projéteis. |
| Morthak / Adaga de Osso | Habilidade sem contrato suficiente de dano/acerto/alcance | Catálogo `backend/app/data/session_abilities.json` | Não inventar fórmula; permanece manual até decisão do Mestre. |
| Dorn 7 / Punho | Configuração aprovada: PV 20, CA 16, JP 16, movimento 6, ataque +3, 1d6+2 | `backend/app/data/dorn7_approved.json` | Painel do turno recebe alvos do mapa, permitindo atacar inimigos como aliado do Mestre. |
| Dorn 7 / Proteger | +2 CA adjacente, em lugar de ataque, até próximo turno de Dorn | Configuração aprovada | Sem ampliar silenciosamente a automação; reparo e incapacitação continuam pendências de regra. |

## Implementado

- Recuperação autenticada de prévias de ataque ainda válidas, sem nova rolagem. Jogador recebe somente próprias resoluções e alvos visíveis; Mestre pode recuperar resoluções da mesa.
- Mísseis: prévia sem consumo; confirmação aplica dano e debita um uso na mesma transação. Repetir confirmação não duplica benefícios/custos. Mudança da ficha invalida a prévia.
- Registro narrativo distingue acerto automático de ataque com d20.
- Componentes reutilizam classes existentes; sem redesign dos cards, fichas ou pins.

## Limites importantes

- Alcance, linha de visão e defesas mágicas específicas exigem conferência do Mestre. O mapa não mede/valida essas condições automaticamente.
- Mísseis físicos e múltiplos projéteis a partir do nível 4 não estão implementados neste corte: não se adivinha resultado.
- Demais habilidades não se tornam automaticamente ações completas por aparecerem no catálogo. Drenagem, Adaga de Osso e durações/efeitos adaptados exigem regras consolidadas.
- Nenhuma cura, progressão, reposição de usos ou alteração de inventário foi aplicada ao banco real.
- Ensaio HTTP sobre cópia do banco não equivale a ensaio visual nem a uma mesa com Mestre e jogadores em redes diferentes.
- Build de verificação foi direcionado a `.autonomy/runtime/combat-review-build`; não houve troca do frontend servido nem reinício do servidor operacional.

## Evidências reproduzíveis

Resultado deste corte: backend **203 testes PASS**; frontend **82 testes PASS**; TypeScript **PASS**; build isolado **PASS** (aviso de tamanho de chunks); `git diff --check` **PASS**. O total backend inclui testes herdados pela classe de recuperação, não representa 203 cenários distintos novos. Ensaio HTTP descartável: magia, recuperação após reconexão, confirmação idempotente e privacidade por proprietário **PASS**. QA visual e ensaio entre redes **NOT RUN**.

- Backend: `cd backend; ..\.venv-observer\Scripts\python.exe -m unittest discover -s . -p 'test_*.py' -q`.
- Frontend: `cd frontend; node --test tests/*.test.cjs`; `npx --no-install tsc --noEmit`.
- Build: `npm run build -- --outDir ../.autonomy/runtime/combat-review-build`.
- Ensaio descartável: `.\.venv-observer\Scripts\python.exe scripts/probe_action_recovery.py`. Usa SQLite temporário e credenciais de teste; não executa ataques na campanha.

Pendências antes de declarar combate fechado: confirmar regras ambíguas, QA visual do fluxo completo e ensaio com Mestre + pelo menos dois jogadores em redes diferentes. Não houve publicação, commit ou push neste corte.
