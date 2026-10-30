# Forma da Noite: ativar e desativar no card

Um único liga/desliga no card, com estado acessível (`role=switch`, `aria-checked`). Quando desligada, escolher animal e ativar consome o uso diário existente. Quando ligada, mostra o animal atual e permite desativar mesmo com zero usos, sem cobrar nem devolver usos.

O desligamento chama `end_night_form`, persistindo o retorno e recarregando a ficha/mapa. A projeção do pin continua vindo do estado compartilhado; o retrato original não é substituído. O ícone do card prioriza a forma realmente ativa, não uma seleção anterior. A autorização de dono/Mestre e as regras existentes de turno são preservadas.

Alterados: `frontend/src/components/NightFormControl.tsx`, `pages/SessionWorkspace.tsx`, `styles.css`, `tests/night-form-control.test.cjs`, `tests/night-form-visual.cjs`; regressão adicionada em `backend/test_hemomante_techniques.py` para zero usos, retorno em dois mapas, persistência e repetição idempotente.

Diagnóstico somente-leitura da ficha real: Raziel permanecia em corvo; os três pins preservavam imagens normais no banco. Nenhuma transformação, recurso ou pin real foi alterado durante a verificação.
