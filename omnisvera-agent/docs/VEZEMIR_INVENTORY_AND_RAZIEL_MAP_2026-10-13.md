# Vezemir: organização; Raziel: mapa real de capacidades

## Alterações de Vezemir

- Nome exibido: **Especialista em Armas**, junto de raça/classe. O ID
  `guerreiro-arma`, a escolha de arma e os bônus continuam iguais.
- Removido «Detalhar Força» da ficha de Vezemir; cálculo do atributo preservado.
- Pulseira de Vinhas permanece no inventário, equipada ou guardada.
- Só aparece em Recursos quando equipada. Recursos mostram cargas, alvo e
  «Usar»; equipar/guardar fica exclusivamente no inventário.
- Não mudou quantidade, cargas, descanso, economia de ações ou regra das vinhas.
- Moeda Misteriosa continua no inventário; não foi criada uma regra nova para ela.

Arquivos de implementação: `frontend/src/specializationLabel.ts`,
`components/SpecializationBadge.tsx`, `components/SpecializationSection.tsx`,
`components/VineBraceletControl.tsx`, `pages/SessionWorkspace.tsx`.
Regressões: `vezemir-inventory-layout.test.cjs`, `session6-rewards.test.cjs`,
`specialization*.test.cjs`, seletores nos smokes de especialização/NPC/ficha,
`vezemir-inventory-smoke.cjs`. O ensaio de quatro atores inclui esse smoke
em `backend/scripts/run_sheet_test.py`.

## Raziel: observado agora, sem alterar sua ficha

API operacional lida em 13/10/2026: nível 5; PV 22/22; CA 16; JP 14;
FOR 10 (+0), DES 15 (+2), BA da classe +2. Ataques com as adagas:
corpo a corpo +4, à distância +6, dano 1d4. Reserva 10/10, Forma da Noite
3/3, Caixão 1/1. Sem especialização escolhida. Faltam **duas rolagens de PV**,
dos níveis 4 e 5; não três. Não foi rolado nem aplicado PV por este trabalho.

| Capacidade | O que faz no código atual | Situação |
| --- | --- | --- |
| Adagas de Espectro Fantasma | 1d4, corpo a corpo/arremesso; cura limitada ao dano realmente drenado e ao máximo | Implementada, item equipado |
| Reforçar arma equipada | +1d4 por sangue, até a reserva; confirma custo mesmo no erro | Implementada, regra aprovada |
| Lâmina de Sangue | 1–10d4 conforme sangue disponível; melee/ranged; custa N na confirmação | Implementada |
| Arma de Sangue | 1d8, melee, custa 2 | Implementada |
| Garras Predatórias | 1d6, melee, custa 1 | Implementada |
| Investida Predatória | 2d4, bônus +2, custa 2; não move o token automaticamente | Implementada |
| Mordida | 1d6 no nv5; ataque contra criatura com sangue; cura limitada ao dano drenado; custo 0 sangue | Implementada |
| Regeneração | Custa 1 sangue e ação; cura 1d4; não levanta de 0 PV | Implementada |
| Sangue Defensivo | Custa 2 sangue; +2 CA por uma rodada | Implementada |
| Faro de Sangue | +1 nos ataques de sangue do handler contra alvo ferido | Implementado como cálculo, card precisa revisão |
| Marca Rubra | Custa 1, exige alvo ferido, mantém efeito até encerrar cena | Marca automática; rastreamento assistido |
| Forma da Noite | Corvo/coruja/morcego: 1 PV, CA 14, JP 4, voo 9 m; bloqueia ataques/poderes; retorna a 0 com excedente | Implementada; base provisória aprovada |
| Caixão | Fora de combate, restaura a própria ficha; só descanso do Mestre recarrega o uso | Implementado |
| Anel Rúnico | Item equipado, cura 4 PV, uma carga diária; descanso do Mestre recarrega | Implementado |
| Visão no escuro | Texto racial: 12 m | Descrita; não há visão individual/LOS |
| Medo | Texto: JP de SAB, controle por 1d4 horas, 2 usos no nv5 | Sem executor específico/contador adequado |
| Imunidades, fotossensibilidade, cura invertida | Regras raciais descritas | Não certificadas como automação; precisam regra tipada/exposição solar/cura por origem |
| Não-Vida/Fome | Não respirar/envelhecer; necessidade narrativa de alimentação | Arbitragem/narrativa |
| Corpo Predatório | Bônus ainda indefinidos | Bloqueado |
| Técnica de Predador | Marco nv5, efeito ainda não escolhido | Bloqueado |
| Marca Rubra aprimorada | Marco nv3, regra ainda indefinida | Bloqueada |

«Implementada» identifica ligação no código/contrato; não afirma que todos
esses casos foram executados nesta rodada nem que a mesa em redes distintas
está certificada. Um cadastro `mechanics_status: structured` não substitui
executor e teste de consequência.

## Revisão de balanceamento: achados, não regras novas

Leitura do kit atual: Raziel concentra recursos em **explosão de dano e
recuperação por drenagem**, mas o ataque básico é 1d4 e a reserva é finita.
Isso ajuda a explicar a diferença entre um pico forte e DPS sustentado fraco;
não é uma decisão sobre como o jogador deve usá-lo nem uma aprovação de buffs.

1. **Finalizar PV 4/5 antes de avaliar fragilidade.** Hoje Raziel ainda usa o
   máximo de PV anterior às duas rolagens pendentes.
2. **Arma vs Investida:** mesmo custo 2; Arma média 4,5 e Investida média 5,
   ainda com +2 no ataque e sem condição de deslocamento aplicada. A Investida
   tende a dominar a Arma. Definir papéis/condição antes de mudar valores.
3. **Adagas reforçadas vs Lâmina:** uma adaga pode somar 1d4 + Nd4 e drenar PV;
   a Lâmina dá Nd4 sem essa cura. O Faro favorece os ataques de sangue em +1.
   A economia/drenagem do reforço é aprovação existente, não deve ser retirada
   silenciosamente para equilibrar o personagem.
4. **BA dos poderes:** alguns handlers partem do ataque da ficha com bônus
   da arma equipada; Mordida explicitamente remove esse bônus. Conferir se
   técnicas de sangue devem herdar o +2 das adagas antes de padronizar.
5. **Alcance:** adagas e ataques à distância estão sem alcance preenchido.
   O grid não limita ataques ranged sem `max_range_m`; melee exige adjacência.
   Definir a distância aprovada antes de tratar ataque ranged como ilimitado.
6. **Faro duplicado/inconsistente:** existem «Sentido do Sangue» e «Faro de
   Sangue»; o recurso antigo ainda diz «bloqueado», mas o bônus é automático.
   O botão genérico não é evidência de uma ativação mecânica nova.
7. **Texto da reserva:** ainda menciona duas técnicas/uma ativa por cena,
   enquanto o catálogo tem mais técnicas aprovadas. Conciliar descrição,
   técnicas instantâneas vs efeitos persistentes e limites reais.

Próximo corte natural de Raziel: fechar ficha e documentação, corrigir
representações duplicadas, definir os três poderes bloqueados e aprovar uma
matriz de dano/custo/alcance/duração. Depois implementar/testar cada executor
usando os comandos, orçamento, confirmação, efeitos e ledger atuais.
Nenhuma proposta de balanceamento foi aplicada neste trabalho.

## Checks e aceitação

- Backend: **762 PASS**; frontend: **267 PASS**; typecheck e build: **PASS**.
- Endereço público HTTP **200**, bundle `index-oq6tYFGy.js` confirmado com o
  novo nome «Especialista em Armas». Não foi necessário restart do backend:
  mudaram apresentação e executor de testes, não handlers operacionais.
- MCP `test-dd2b9c824a3d4260acd96045bb5c58d6`: **70 cenários API PASS**,
  **2 EXPECTED_BLOCK** (ataque genérico ranged de Vezemir/Morthak sem arma).
  **28 cenários de Raziel PASS**, incluindo acerto/erro, falta de sangue,
  Faro, Mordida/cura, Marca, Caixão, anel, regeneração e Sangue Defensivo.
- As cinco primeiras checagens UI passaram: ficha, combate físico,
  pacote aprovado de magias, padrão visual e quatro novas imagens de Morthak.
  O job ficou **FAIL** na sexta: o teste de inventário procurou a Pulseira
  após reload sem selecionar novamente a ficha de Vezemir.
- Inspeção da SQLite descartável confirmou que o equipamento persistiu.
  O smoke foi corrigido para escolher a ficha certa e verificar também o
  estado autoritativo da API. **Recheck PASS**: Mestre 1440 px e Vezemir
  390 px; equipar/guardar, reload, quantidade/cargas/PV preservados; captura
  revisada. Evidência privada: `TEMP/omni-vezemir-inventory-visual-d773_amx/ui.private.log`.
  Esse recheck não apaga nem renomeia o FAIL do job anterior.
- Sem alterações operacionais de ficha, rolagens de PV, descanso ou combate;
  equipar/guardar no ensaio aconteceu somente na cópia temporária.
- Sem commit/push. Avisos legados de SQLite/depreciação e bundle grande
  permanecem; não houve validação com jogadores em redes diferentes.
