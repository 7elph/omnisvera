# Fundação operacional — composição P1 (31/10/2026)

Continuação do [checkpoint P0](OPERATIONAL_FOUNDATION_P0_2026-10-31.md), sobre
`devin/create-omnisvera-class-standard`, HEAD `c3dc2819446c67c6be2e1d090508c4cf27670727`.
Alterações locais; nenhum rollout, commit, push ou edição do Vault/banco real.

## Bugs reproduzidos e correções

- **Reposição de munição:** um pacote aberto fazia a compra de um pacote novo
  falhar por incompatibilidade de cargas. O modelo nativo já representa um
  pacote parcial e reservas completas. `item_transfer.grant_item` agora permite
  somente essa reposição, preservando o contador aberto, condição e recarga.
  Exemplo ensaiado: 13 flechas + pacote de 20 = 33; retry continua com 33.
  Dois pacotes parciais, condições incompatíveis ou metadados corrompidos
  continuam bloqueados. Não se criou inventário nem instância paralelos.
- **Retry de viagem:** o mesmo pedido podia ser reutilizado em outra viagem,
  outro avanço ou autor sem erro. Início/pausa/retomada/cancelamento, avanço e
  chegada conferem o evento nativo. Avanços novos guardam o valor pedido;
  eventos antigos verificam o mesmo resultado. Mudança de motivo também é
  rejeitada no cancelamento/falha. As três operações tomam a trava de escrita
  antes de ler versão/estado: dois avanços na mesma versão aplicam só um.
  O replay continua devolvendo a projeção atual da viagem, não um novo evento.
- **Privacidade de cenas:** a projeção da viagem já escondia vínculos privados,
  mas o evento de vínculo ainda expunha o identificador da cena ao jogador.
  Um teste reproduziu o vazamento. Os eventos agora reutilizam o mesmo filtro
  de visibilidade das cenas: o Mestre conserva o vínculo e o jogador só recebe
  eventos vinculados a cenas públicas/da mesa.

## Cobertura por família

| Família | Evidência deste corte | Limite |
| --- | --- | --- |
| Armas/munição | Espada curta inicia combate; espada longa recebida no loot equipa, causa dano e é vendida. Flechas repostas preservam contagem e retry. | Não certifica cada efeito especial do catálogo. |
| Armaduras/escudos | Compra → recompensa → equipar → CA → guardar → vender; venda enquanto equipado bloqueada. | Carga/encumbrância universal não acrescentada. |
| Consumíveis | Poção de HP adquirida, usada pela ação nativa, cura aplicada uma vez e saldo restante vendido. | Demais efeitos exigem contratos estruturados existentes. |
| Exploração | Corda mantém identidade/quantidade em compra, loot e venda. | Descrição física não vira ação artificial. |
| Transporte/montarias | Carroça e cavalo de montaria no mesmo circuito de propriedade/comércio. | Capacidade, velocidade de viagem e logística continuam assistidas. |
| Mágicos | Talismã sintético exercita PV temporários, carga/recarga e revenda individual preservada. Tapete voador exercita comércio/loot. | O talismã é dado de QA; não foi cadastrado na campanha. Voo do tapete não foi automatizado. |

O gate é **representativo dos contratos**, não de todos os cadastros físicos.
`item_registry.audit_items` conserva `automation_status=not_certified` e as
lacunas por item. Arte ausente, descrição para revisão e executor ausente são
coisas diferentes; não foram inventados preços, regras ou efeitos para fechar
contagens.
Pilhas de vários exemplares mágicos com cargas individuais não foram
certificadas; o teste do talismã usa uma única instância nativa.

## Circuito composto e viagens

O ensaio encadeia, no mesmo SQLite TEMP: Nimalia sintética → planejamento e
participante → início → avanço → pausa para encontro → combate → derrota →
revelação e distribuição idempotente de loot canônico → equipamento e ataque
com a arma recebida → retomada/chegada → guardar → venda → nova leitura.
Uma cena privada vinculada à etapa fica ausente da projeção do jogador.
Retries não repetem dano, entrega, chegada, estoque ou pagamento.

Continuam sendo ações explícitas do Mestre. Progresso não foi convertido em
dias, nem foram inventados consumo de rações, encontros, custos ou teleporte
entre mapas. Chegada reutiliza localização/estado/evento do personagem.
Criação/edição dos demais registros de mundo conserva seus contratos atuais;
este corte reforça especificamente as transições, avanço e chegada.

## Primeiro planejador assistido de monstros

`GET /gm/combat/tokens/{token_id}/action-proposals?target_token_ids=...`
aceita até 20 pins candidatos escolhidos pelo Mestre. Acesso somente GM;
SQLite aberto em modo somente leitura. Nenhum dado, recurso ou turno é alterado.

Reutiliza definição de ataque, restrições do turno, alvo vivo, Provocação,
regra de distância e posições do grid existentes. Ordena propostas por
distância, ataque e identidade; devolve a rota nativa de resolução e os
parâmetros do alvo/alcance. O chamador fornece `request_id` ao executar e usa
a confirmação existente. A resolução continua sendo autoritativa.

Este primeiro planejador cobre ataques estruturados; efeitos adicionais
assistidos e alcances de distância ausentes são bloqueados. Não escolhe
facções/alvos sozinho, não movimenta criaturas e não executa prosa.
Baforadas, contatos e magias continuam com seus controles nativos; incluí-los
na seleção tática é uma evolução, não um resultado já implementado.
Não foi adicionado botão novo na ficha nem certificada uma UI de propostas.

## Validação e evidências

- Frontend: **498 aprovados**, zero falhas/skips; typecheck aprovado; build
  em TEMP aprovado (aviso conhecido de bundles acima de 500 kB). Nenhum
  código frontend adicional foi alterado neste lote.
- CF01 sintético + driver finito Playwright: PASS. Quatro atores lidos por API;
  Mestre 1440 px e jogador 390 px no mercado; compra/venda, retry, reload,
  saldo/denominações, privacidade e estoque no outro cliente sem reload.
  Cadeia HTTP loot → equipamento → dano → venda também passou.
- As três capturas foram inspecionadas explicitamente: **PASS_SCOPED_MARKET**.
  Sem overflow horizontal ou erros inesperados nas ações/dados. Há quatro
  caminhos de mídia ausentes na fixture (mapa, dados, espada e inventário),
  com fallback preservado; não há certificação de arte/mapas/ficha completa.
- Os cenários P1 de viagem/circuito usam comandos nativos e as rotas de
  ficha/combate via TestClient no mesmo banco sintético. Não é prova de toda
  a jornada por navegador ou redes distintas.
- Suíte geral backend final: **1.860 casos; 1.859 aprovados, zero falhas/erros
  e 1 ignorado** pelo privilégio de symlink ausente no Windows (874,25 s).
  Inclui os **23 novos testes P1**. Descoberta completa no `.venv-observer`
  já instalado, com ambiente SQLite/Vault/credenciais sintéticos do harness.
  A primeira geral passou antes da última correção de privacidade; o novo
  RED de cena privada motivou a repetição completa sobre o código final.

O MCP `companion-tests` não está exposto neste cliente. Foi usado o CF01
nativo com driver próprio; não foi fabricado `report.ui_smoke` do conector.
Evidências em `foundation-p1-*.log/json` e `foundation-p1-ui-final/`, no
diretório de visualizações deste chat. Backend/navegador de QA encerrados
pelos próprios handles/grupo, sem fechar Companion/OpenCode operacionais.

As execuções intermediárias permanecem nos artefatos `foundation-p1-*`.
O primeiro teste de reposição não tinha dinheiro para dois pacotes; a fixture
foi corrigida e o RED foi repetido contra a implementação P0 sem a reposição.
Outros ajustes foram exclusivamente de fixture: IDs completos do catálogo,
mapa explícito do pin, inventário vazio na leitura, ataque base cadastrado e
guardar a arma anterior antes de equipar a recebida. Esses erros de ensaio
não foram tratados como bugs do produto.

Gate da composição: **PASS no escopo representativo descrito**. Não é
certificação individual do catálogo, de todas as decisões de monstros ou de
uma mesa real. Não houve ativação. `git diff --check` aprovado; sem staging,
commit ou push. Mudanças anteriores, inclusive P0, foram preservadas.

## Arquivos deste lote

- Alterados: `backend/app/item_transfer.py`, `world_travel.py`, `main.py`.
- Novo: `backend/app/monster_proposals.py`.
- Novos testes: `backend/test_foundation_p1_items.py`,
  `test_foundation_p1_journeys.py`, `test_monster_proposals.py`.
- Documentação: este relatório e referências no checkpoint P0 e em
  `CURRENT_COMPANION_CODE.md`.
- Frontend: nenhum código adicional alterado neste lote; os arquivos locais
  do P0 permanecem preservados e são incluídos nos checks.

Não há certificação de mesa real em redes distintas. Ainda faltam cobertura
individual dos itens/efeitos não estruturados, logística e as demais evoluções
P2. Ativação no Companion continua dependendo de autorização específica.
