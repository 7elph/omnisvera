# Marca Rubra — habilidade e contador nativos

- Habilidades de Raziel: dez ativas, incluindo Marca Rubra. Poderes continuam
  com cinco passivas; Hemomancia continua sendo o seletor de armas.
- Contador do card é a Reserva de Sangue persistida, não um novo uso diário.
  Aplicar custa 1 sangue. Cancelar ou rejeitar não custa; retry do mesmo comando
  recupera o recibo, mesmo após cura do alvo ou outra ação no turno.
- Mesmo fluxo: card → grid → alvo → confirmação. Mantido o alcance de contato
  já usado pelo grid, agora também validado no servidor. Não foi criado alcance
  de 9 m. Mapas antigos sem grid continuam com arbitragem do Mestre.
- Alvo deve estar vivo e ferido, ter sangue e estar disponível no mesmo mapa.
  Pins de personagens resolvem para a ficha, não para uma cópia dos PV.
- Mantida ativação sem consumir ataque, antes da ação principal, com validação
  do turno existente. Não concede outro turno/ataque nem atravessa ataque pendente.
- Tiro do Coração recebe +2 de acerto no alvo marcado; não é dano extra.
  Novas marcas são vinculadas ao mapa e limpas no encerramento/descanso nativo.
  Fonte legada continua reconhecida, sem empilhar bônus ou ícones ao renovar.
- Efeito, custo, recibo e ledger compartilham a transação de `effect_command`;
  projeção Mestre/Jogador e transporte realtime existentes preservados.

## Verificação deste corte

RED reproduziu ocultação da habilidade, retry rejeitado depois da cura e ausência
das validações de alvo/alcance. GREEN: dez testes novos específicos da Marca;
77 testes focados passaram antes dos quatro últimos casos acrescentados.

- Backend completo: 1.077 testes OK, um skip de symlink por permissão do Windows.
- Frontend: 336 PASS, typecheck e build PASS; aviso pré-existente de bundle.
- Fixture `fvgkkc5e`: quatro cenários API PASS; dois scripts UI PASS
  (270,391 s / 121,002 s). Marca foi usada no celular e no desktop GM, custo e
  contador conferidos; Tiro confirmou o bônus +2. Seis usos de armas, cancelamento,
  persistência/reload e segunda página local preservados. Capturas de Habilidades
  em 390 px e uso de Marca/Tiro em 1440 px revisadas explicitamente.
- Duas tentativas visuais anteriores falharam: espera de resposta iniciada antes
  de a ficha estar pronta e tentativa de clique de teste no botão interno oculto.
  O ensaio passou a aguardar comando habilitado e clicar no card, sem alterar
  regra, aumentar timeout ou remover casos. Relatórios anteriores preservados.
- Backend ativado com backup; PID 232704, launcher 237544. Comparação das 27
  tabelas protegidas preservou os dados de jogo; somente `maps.updated_at` mudou
  no startup. Tokens, configurações, fichas e ausência de combate preservados.
  Quatro fichas HTTP 200; separação do pacote privado de Raziel conferida.
- Consulta somente leitura em mapa já posicionado confirmou contato de uma
  célula, mesmo com tentativa de declarar alcance de 9 m na query.
- Endereço público e bundle novo HTTP 200 a partir deste host. Isso não é prova
  de mesa em redes distintas ou celular físico. Ícones legados da fixture não
  estão certificados. Nenhuma ativação operacional de habilidade foi realizada.

## Arquivos deste complemento

Backend: `app/main.py`, `app/combat_effects.py`, `app/hemomancy.py`,
`test_rubra_mark.py` e fixture compartilhada em `test_hemomancy_weapons.py`.
Frontend: `src/components/hemomancySelection.ts`, `src/pages/SessionWorkspace.tsx`,
`tests/raziel-sections.test.cjs`, `tests/hemomancy-weapons-smoke.cjs`.
Documentação: este resumo, `CURRENT_COMPANION_CODE.md` e
`RAZIEL_SHEET_SECTIONS_2026-10-18.md`. Sem staging, commit ou push.
