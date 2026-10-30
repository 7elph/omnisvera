# Fechamento das ações e base para IA — 12/10/2026

## Implementado e ativado

| Área | Resultado |
|---|---|
| Arma de Sangue | Alvo/d20/preview/confirm na ficha; 1d8, custo 2 |
| Garras Predatórias | Alvo/d20/preview/confirm; 1d6, custo 1 |
| Investida Predatória | Alvo/d20/preview/confirm; +2 no ataque, 2d4, custo 2; não move automaticamente |
| Sangue Defensivo | Comando real, custo 2, +2 CA, expiração nativa em 1 rodada |
| Caixão | Jogador usa fora de combate, restaura a própria ficha atomicamente e gasta o uso; só descanso do Mestre recarrega |
| Adagas espectrais | Corpo a corpo e arremesso conforme fonte existente; slot escolhido não apaga o outro modo |
| Vezemir | Adaga já possuída preparada à distância (1d4); Grisalma conserva corpo a corpo (2d6+2) |
| Morthak | Adaga de Osso funcional; card genérico de arremesso sem arma é oculto, não recebe dano inventado |
| Dorn | Cinco Kits de Reparo repostos; consome um por reparo e ainda pode atacar no mesmo turno |

Os valores dos quatro poderes de Raziel foram aprovados explicitamente nesta
conversa. A proposta alternativa de espada/lança/escudo não foi aplicada.
Caixão não revive com 0 PV, não funciona em combate, não restaura outra ficha,
não recarrega o próprio uso e não dispensa recurso por retry.

## Uso

Na ficha do jogador ou **Mesa → personagem** pelo Mestre:

1. Ataque de sangue: selecionar alvo válido, digitar d20 se a mesa for Física,
   **Usar → prévia → Confirmar**. O custo de sangue é aplicado na confirmação,
   inclusive no erro. Não gera ataque adicional nem cura de adaga.
2. Sangue Defensivo: **Usar** aplica o escudo real; observar CA/efeitos e expiração.
3. Caixão: fora de combate, **Usar** restaura a ficha e deixa contador 0/1. Após
   o descanso concedido pelo Mestre, volta a 1/1. Sem confirmação individual.
4. Dorn: em **Recursos → Reparo**, usar consome um kit. Um consumível por turno;
   o ataque principal continua disponível se ainda não foi usado.
5. Morthak: ataque à distância pelo card **Adaga de Osso** em Magias.
6. Registro: filtro Ações e **Ver resultado** para consequência; não confundir
   prévia com dano aplicado. Em falha de conexão, recuperar o mesmo recibo/prévia.

## Evidência

- Backend: **611/611 testes**.
- Frontend: **245/245 testes**.
- Typecheck, build e `git diff --check`: passaram.
- HTTP nativo contra cópia: **45 PASS, 0 FAIL, 1 EXPECTED_BLOCK**. A rejeição é
  o slot genérico sem arma de Morthak; seu ataque correto, Adaga de Osso, passou.
- Navegador Edge real: Mestre/proprietário com mesmos dados mecânicos; Toque
  Sombrio, Lâmina e três novos ataques com d20 físico; custo/expiração do escudo;
  Caixão pelo jogador, bloqueio de repetição e recarga pelo Mestre; Reparo e
  ataque de Dorn no mesmo turno; segundo cliente atualizado e reload persistido.
- Fixtures usam banco/vault descartáveis e tokens CF-01; 84 mídias referenciadas
  copiadas sem faltar arquivo na origem. Isso não certifica todo catálogo de mídia.
- Não foi rolado dado físico por uma pessoa nem comprovada mesa prolongada em
  redes externas distintas. Há ResourceWarnings de fixtures SQLite e aviso de
  tamanho de chunks no build; não ocultados nem tratados como resultados de jogo.

Falhas intermediárias: regressões RED de Caixão/modo das adagas/conexão dos
novos botões; assertiva textual antiga do filtro da Adaga de Osso; e seletores
do smoke que presumiam aba persistida e classe CSS antiga de Recursos.
Correções foram reexecutadas. Não foram removidas verificações de custo/estado.

Backend reiniciado com backup, sem girar tokens ou abrir combate na produção.
Tentativas de inicialização em segundo plano não permaneceram ativas; retomado
com `start_backend.ps1` no processo de execução persistente. Verificação posterior:
Mestre e três proprietários com HTTP 200 local/público; bundle atual confirmado;
13 tabelas e tokens iguais ao snapshot feito após as duas alterações de
inventário autorizadas. Túnel preservado. Fixture 8871 encerrada separadamente.
Não foi configurado novo serviço de autostart após reiniciar o Windows.

## Base para IA e próximo corte

`AI_COMPONENT_MAP.json`: índice de dez blocos com arquivos, contratos,
rotas, dados e limites. O teste confere referências reais; não é outro formato
de campanha. `AI_COMPANION_FOUNDATION.md` descreve como reaproveitar cenas
privadas/rascunhos, fichas, bibliotecas, combate e histórico.

Próximo corte: contrato de ação executável e executor de testes por ficha,
antes de ligar o laboratório de propostas à aba Cenas. Rascunho não pode
publicar/iniciar mesa por si só. Inferências de roleplay são alternativas,
não decisões ou falas dos jogadores. Importador completo de PDFs, tela nova
de sandbox e fichas universais detalhadas de NPCs ainda não foram implementados.

## Arquivos deste corte

- Backend: `app/character_play.py`, `app/player_inventory.py`, `app/main.py`,
  `app/data/session_abilities.json`, `scripts/all_actions_simulation.py`.
- Testes backend: `test_coffin_rest.py`, `test_attack_weapon_select.py`,
  `test_ai_component_map.py`.
- Frontend: `src/pages/SessionWorkspace.tsx`, `src/api.ts`.
- Testes frontend: `blood-technique-physical.test.cjs`,
  `sheet-standard.test.cjs`, `combat-simulation-physical-smoke.cjs`.
- Documentação: este relatório, índice/base para IA e atualizações dos guias
  de código, ensaio anterior e proposta de armas.

Branch solicitada preservada, HEAD `1a07a84`, worktree misto preservado.
Sem staging, commit ou push. Bancos, tokens, backups, logs e screenshots não
foram incluídos na entrega de código. Não atribuir todo o git diff a este corte.
