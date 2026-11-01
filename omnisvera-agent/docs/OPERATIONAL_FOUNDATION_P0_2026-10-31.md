# Fundação operacional — Fase 0 e P0

Base: `devin/create-omnisvera-class-standard`, SHA
`c3dc2819446c67c6be2e1d090508c4cf27670727`, inspecionada em 31/10/2026.
Código local validado no escopo abaixo; sem ativação, staging, commit ou push deste corte.

## Escopo e impacto

Manter carteira, inventário, combate, ledger, realtime e regras nativos.
Corrigir identidade do loot e proteção de comandos antes de compor viagens
ou decisões de monstros. Novas tabelas guardam somente identidade/recuperação
de comandos de loot, sem outra carteira ou inventário.

## Fase 0: mapa dos blocos

| Bloco | Autoridade e integração | Cobertura existente |
|---|---|---|
| Catálogo | `item_catalog.py`: fontes estáticas, referências e projeções por família | `test_item_families`, `test_item_offer_readiness` |
| Registro | `item_registry.py`: catálogo + notas indexadas + itens de sessão; valoração do Mestre | `test_market_registry`, `test_economy_completion` |
| Famílias | `item_families.py`, `item_specials.py`: armas/munição, defesa e adaptadores | Suites de famílias/especiais; não executam prosa arbitrária |
| Inventário | `player_inventory.py`: único por `(profile_id,item_path)`; slot, quantidade, cargas/recarga; condição em `inventory_item_conditions` | Equipamento, inventário e novos testes P0 |
| Mercado nativo | `map_commerce.py`, `commerce_routes.py`: orçamento → confirmação → recibo; dono/Mestre; preço/estoque no servidor | `test_map_commerce`, `test_economy_completion`, `test_market_followup` |
| Mercado GM antigo | `merchant.py`; `/gm/merchants/{id}/buy` e `/sell` em `main.py` | Novo request obrigatório e recuperação; preço manual restrito ao Mestre |
| Loot | `loot.py`; `/workspace/loot`, `/gm/workspace/loot/*`; `SessionWorkspace.tsx` | Geração, revelação, distribuição; novas regressões de identidade/atomicidade |
| Combate | `combat.py`, `combat_effects.py`, `battle_mode.py`; resolução/confirmação e orçamento existentes | `test_combat_loot_circuit` reutilizado; sem mudar regras |
| Viagem | `world_travel.py`, `/world/*` e `/gm/world/*`; `pages/WorldMapPage.tsx`, `api.ts` | Jornadas, versões, participantes, avanço/chegada e eventos existentes; composição completa não certificada |
| Auditoria/realtime | `session_ledger.py`, `session_realtime.py`, middleware nativo | Ledger único; nenhum WebSocket paralelo |

Identidades: `compendium:<id>`, caminho do Vault, `session-item:<id>` e aliases
legados `merchant:<loja>:<id>`. Coincidência parcial de nome não é identidade.
O inventário não comporta dois exemplares incompatíveis no mesmo caminho do
mesmo personagem: rejeitar esse merge preserva as propriedades dos dois.

## Diagnóstico por categoria

- **Divergência documental:** `../ECONOMY.md` diz 10 PO por platina;
  `merchant.py` usa 100 PO. O Mestre confirmou neste chat **1 platina = 100 ouro**
  em 31/10. `currency.py` registra a regra e novos recibos incluem sua fotografia.
  Não houve migração de saldos nem edição do Vault.
- **Bugs reproduzidos:** loot comum virava item de sessão sem mecânicas;
  identidade/cargas fornecidas eram perdidas; IDs de distribuição aceitavam
  outro conteúdo; aliases podiam ser reutilizados em outra distribuição;
  IDs de recompensa duplicados eram aceitos. Rotas GM antigas não tinham
  request e a chave antiga do ledger escondia compras distintas do mesmo estoque.
- **Bug adicional reproduzido:** falha na segunda solicitação de rolagem de
  loot deixava a primeira órfã. O criador nativo agora aceita a conexão
  transacional do loot, sem commit interno nesse caminho.
- **Lacunas confirmadas:** item narrativo, ambíguo ou não identificado continua
  assistido. Ausência de regra estruturada não equivale a item quebrado.
  Não foram encontrados testes dedicados de `world_travel` na descoberta atual.
- **Propostas/P1:** demais famílias, ciclo completo com viagem/suprimentos/eventos
  aprovados e decisões assistidas de monstros. Não implementadas neste corte.

## Contratos corrigidos

- Geração/distribuição vinculam request, origem/resolução e intenção. Reordenar
  alocações equivalentes não duplica; alterar intenção é conflito. Registros
  históricos distribuídos são comparados sem recreditar moedas.
- Correspondência exata e única concede o caminho nativo; referência explícita
  conflitante/desconhecida é rejeitada. Não identificado/ambíguo fica assistido.
  O ledger registra as transferências e a origem.
- `item_transfer.py` concede sobre o inventário existente; cargas, recarga ou
  condição incompatíveis impedem a transação inteira, sem descarte silencioso.
  Exemplares parcialmente usados não são empilhados: o contador nativo só
  representa uma cópia parcial seguida de cópias cheias. A munição mantém o
  tamanho de pacote definido no catálogo. Esse bloqueio evita criar cargas
  ou projéteis; casos não representáveis ficam para revisão individual.
- Compra/venda GM exige `request_id`, usa `merchant_commands` e registra
  saldo/estoque/inventário antes/depois. Equipado ou com propriedades de instância
  não é revendido como produto novo. Venda concreta repõe o estoque. Objeto sem
  identidade concreta precisa de cadastro/avaliação.
- Cliente GM reutiliza `createCommandRetry` e `writeJson`: resposta perdida e
  reload recuperam a intenção. O journal contém hashes/IDs, sem token ou ficha.
  Saldo esperado é uma pré-condição da primeira aplicação, não parte da intenção:
  um reload que atualize o saldo recupera o recibo anterior, sem nova compra.
  Orquestradores devem preferir orçamento/confirmação no mapa; a rota antiga
  continua uma operação de preço manual do Mestre.

## Validação

Baseline isolada: **75 aprovados, zero falhas/erros/skips**.
Reprodução inicial P0: 13 casos, nove falhas e três erros por contrato ausente;
o caso ambíguo já ficava narrativo. Três regressões frontend falharam contra
HEAD e passaram com a correção. A falha forçada de rolagem deixou um órfão
antes e zero depois. Os três casos de pacotes parciais falharam antes da
proteção e passaram depois; **30 regressões P0 aprovadas** no total.

- Backend geral final: **1.837 casos; 1.836 aprovados, zero falhas/erros e
  1 ignorado** por falta do privilégio de symlink no Windows (680,73 s).
  Os 30 testes específicos do P0 estão incluídos no total.
- Frontend: **498 aprovados**, zero falhas/skips; typecheck aprovado;
  build em TEMP aprovado, com o aviso conhecido de tamanho dos bundles.
- Smoke CF01 sintético: quatro atores, Mestre 1440 px e dono 390 px;
  compra/venda, valor e denominações, estoque no outro cliente sem reload,
  retry e autorização passaram. A cadeia HTTP loot → carteira/arma canônica →
  equipar → ataque com dano → guardar → vender → novas leituras/retries passou.
- Três capturas inspecionadas: **PASS_SCOPED_MARKET**. Sem overflow horizontal
  mobile, erros JS ou erros inesperados nas rotas de dados/ações. A fixture não forneceu o mapa canônico e dois ícones;
  seus 404 de mídia foram preservados no relatório, com fallback genérico no
  mercado. Não é certificação de arte, mapa, ficha completa ou redes distintas.
- Todos os bancos e tokens de QA são sintéticos em TEMP. O processo CF01 e o
  grupo do navegador foram encerrados por seus próprios handles; nenhuma
  chamada de ensaio foi enviada ao runtime operacional.

Artefatos locais em `foundation-*.log/json` e `foundation-ui-final/`, no diretório
de visualizações deste chat. `companion-tests` não está exposto como ferramenta
neste cliente; o smoke usou o CF01 nativo e um driver Playwright finito,
sem recarregar conectores nem abrir ensaios sobre a origem operacional.

Os artefatos preservam execuções intermediárias. Duas seleções manuais citaram
nomes de módulos inexistentes (`test_world_travel`, `test_dice_rolls`): erros do
comando de teste, não bugs do produto. A baseline corrigida usa módulos reais;
a suíte geral usa descoberta. Um teste HTTP intermediário abriu lifespan
desnecessariamente e falhou no cleanup da fixture; o teste final usa cliente
sem startup, token sintético e cleanup explícito.
O primeiro smoke tinha perfil auxiliar ausente e dados de ataque fora do formato
de persistência; a fixture foi corrigida, mantendo os FAIL nos artefatos.
A primeira suíte geral no Python do backend encontrou dois erros e um skip por
SDK MCP ausente; a repetição usa `.venv-observer`, já instalado com esse SDK.
O primeiro frontend no sandbox encontrou leitura ancestral negada pelo esbuild;
a repetição com essa leitura permitida passou, sem alterar o código por esse erro.

## Arquivos deste corte

- Backend novo: `app/currency.py`, `app/item_transfer.py`.
- Backend alterado: `app/merchant.py`, `map_commerce.py`, `item_registry.py`,
  `loot.py`, `dice_rolls.py`, `schemas.py`, `main.py`.
- Testes: `backend/test_foundation_p0.py` (novo), `test_merchant.py`,
  `test_item_offer_readiness.py`, `test_market_followup.py` (adaptação ao request obrigatório).
- Frontend: `src/api.ts`, `tests/foundation-commerce-retry.test.cjs` (novo).
- Documentação: este relatório. Artefatos temporários anteriores e preparações
  privadas continuam fora do escopo; não houve edição de Vault/Godot.

Ativação futura deve publicar frontend e backend juntos: clientes antigos das
rotas GM não fornecem o request obrigatório e serão rejeitados sem mutação.
Não foi feito rollout, commit ou push deste corte.

Gate P0: **PASS no escopo ensaiado**: conservação de valor, identidade concreta,
propriedades representáveis, atomicidade, replay, concorrência, recibos e
autorização dos caminhos de mercado/loot testados. Dados ambíguos e exemplares
incompatíveis continuam assistidos/rejeitados; não é certificação de todo o catálogo.

Na conclusão deste checkpoint, P1 não havia sido iniciada. Permaneciam a certificação das outras famílias, o cenário
Nimalia → viagem → encontro → combate → loot → equipamento/uso → venda →
persistência e as decisões assistidas de monstros. P2 não foi expandida.

Continuação autorizada: [composição P1 e evidências](OPERATIONAL_FOUNDATION_P1_2026-10-31.md).
