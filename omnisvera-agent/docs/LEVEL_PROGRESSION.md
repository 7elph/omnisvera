# Progressão conferida — 26/09/2026

## Fontes e limites

- Guerreiro de Vezemir: nome operacional de Homem de Armas, OD1 Aprimorada 2017, pp. 32–34, T3-3; Classes/Guerreiro.md. Não migrar para OD2 automaticamente.
- Mago de Morthak: OD1 Aprimorada, pp. 13–15 e 40–42, T1-1/T3-6. A tabela da nota Classes/Mago.md coincide com essa edição, apesar do cabeçalho OD2. Raça: Races/Morto-Vivo Esqueleto.md; atributos da ficha já incluem adaptações raciais.
- Raziel: Classes/Hemomante.md + decisão explícita do Mestre: sangue máximo 5 e Sentido do Sangue bloqueado. Não liberar técnicas ou reinterpretar essas decisões por nível.
- Automação conferida: níveis 2–4 de Vezemir e Morthak; nível 2 de Raziel. Outros avanços retornam erro explícito, sem escrita. Especializações, técnicas novas e escalonamento de habilidades autorais continuam dependendo de revisão.

## Operação

Na ficha do Mestre, usar **Subir para nível N**. Se o número já foi alterado manualmente sem progresso confirmado, aparece **Conferir nível N**.

O backend prepara a prévia e exige a rolagem natural de PV quando devida. A confirmação inclui alvo e fingerprint, revalida a ficha e grava definição, estado e evento numa transação. Repetir a mesma confirmação é idempotente, inclusive depois de outro avanço. O histórico guarda o nível realmente confirmado, separado do número exibido.

Ataques recebem apenas a diferença de BA; JP segue a tabela. CA, atributos, itens, raça, recursos autorais e habilidades existentes não são reaplicados. XP não é inventado: a promoção é decisão do Mestre.

Capacidade de magias usa círculos e bônus de Inteligência da fonte. Isso não ensina automaticamente novas magias, não altera contadores próprios das magias adaptadas e não realiza descanso. PV atuais e recursos gastos permanecem; os limites persistem após recarregar a ficha.

A correção administrativa de nível/XP continua disponível e explicitamente não concede benefícios. Não usar como botão de progressão.

## Reconciliação da campanha

- Vezemir: nível 2 previamente registrado; PV máximo 17 e BA 2 preservados.
- Raziel: nível 2 previamente registrado; PV máximo 16, BA 1 e sangue 5 preservados.
- Morthak: evento 215 alterou nível 1 → 2 mantendo máximo 4. O avanço requer d4 natural; não presumir que a vida foi concedida só porque aparece nível 2. INT 20: capacidade de 1º círculo prevista 4 (2 classe + 2 INT); contadores adaptados separados não são multiplicados.

Nenhuma confirmação de progresso foi aplicada à campanha nesta implementação.

## Verificação

- Backend: `python -m unittest discover -s backend -p "test_*.py"`.
- Frontend: `node --test tests/*.test.cjs`, `npx --no-install tsc --noEmit`, `npm run build`.
- `scripts/probe_level_progression.py` cria backup SQLite temporário, testa prévia/commit/repetição/negação ao jogador nas fichas reais copiadas. Rolagens de ensaio não são decisões de mesa.
- Testes cobrem atomicidade, estado obsoleto, preservação de recursos, recarga, bônus cumulativo, saltos inválidos, escolhas não conferidas e confirmação dupla.

Limite conhecido: contadores de magias adaptadas não foram redesenhados como um sistema de preparação compartilhada. Isso exige conciliar a regra específica da campanha antes de mudar consumo das ações existentes.
