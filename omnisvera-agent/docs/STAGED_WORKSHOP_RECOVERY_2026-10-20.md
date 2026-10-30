# Recuperação por etapas — Companion e oficina

## 1. Runtime recuperado

Backend 8787 iniciado com tokens já salvos, sem reinstalação, rotação de acessos,
rebuild de índice ou alteração de regras. Backup SQLite íntegro e cópia dos
arquivos de acesso/provedor em `.autonomy/runtime/recovery-*`.
Mestre/Morthak/Vezemir: `/characters` 200; anônimo: 401; home pública: 200.
Fichas, estados, pins, posições, fog, sessão, efeitos e cenas comparados ao backup.
Startup modificou somente `updated_at` de Nimalia/Earthropo nos mapas existentes.

## 2. Oficina visível em Cenas

`SceneWorkshopPanel` aparece somente na administração GM, inclusive sem cena.
Leitura preguiçosa, atualização manual, descarte de respostas atrasadas, cards
compactos e prévia textual sem editor JSON. Nenhuma geração disparada ao abrir.
GET `/gm/ai-workshop` e `/gm/ai-workshop/jobs/{id}` reutilizam a fila separada,
sem devolver transcrições, payloads de entrada ou registros de autenticação.
As rotas não criam banco ausente nem oferecem execução/publicação.

## 3. Ainda não ativado

### Atualização — primeiro texto real confirmado

Após o Mestre abrir o Ollama, o gateway retornou 200 e reconheceu
`gpt-oss:120b-cloud`. Um único pedido foi concluído em 13,02 s (12.192 ms
medidos pelo adapter), gerando o job 1 com 6.984 caracteres em
`awaiting_approval`. Fila atual: 275 pendentes e 1 para revisão; worker parado.
Resumo/detalhe privados confirmados por HTTP 200; jogador recebe 401.
SHA do banco da campanha permaneceu igual durante a execução.

A revisão do texto encontrou nomes de PCs tratados como NPCs e ruído de ASR
interpretado como possíveis locais/itens. O prompt agora exige português,
distinção entre discussão de interface e ficção, offsets em caracteres e
menções não classificadas quando não há evidência. O primeiro texto foi
preservado para auditoria, sem aprovação; não houve segunda geração nem prova
de qualidade do prompt revisado. Não iniciar a produção em massa antes disso.
Os parágrafos abaixo preservam os bloqueios encontrados antes dessa atualização.

Correção após confirmação do Mestre: o provedor é **Ollama Cloud / GPT-OSS
120B**, não inferência local. A oficina agora reutiliza `get_settings()` para
não perder o adaptador nem escolher silenciosamente o modelo fast. Três novas
regressões cobrem baseline cloud, fast não substituindo cloud e override explícito.
O intermediário HTTP local continua indisponível; nenhuma API key para acesso
cloud direto está configurada nas variáveis verificadas. O limite de RAM protege
o aplicativo/worker, não representa memória necessária para carregar o modelo cloud.

276 trabalhos de texto continuam na fila, worker parado. A tentativa de iniciar
o serviço Ollama foi bloqueada pela política de execução: não contornar com
outro lançador. Não houve geração real, fallback silencioso nem download de modelo.
Geração efetiva de imagens e sandbox automática de código continuam pendentes.
Próximo passo: liberar o provedor de texto, comprovar UM job real com fontes,
custo/tempo e saída em rascunho; só então habilitar consumo contínuo com orçamento
real e guarda de RAM. Depois, imagem e integração dos assets nativos, uma etapa
por vez. Prévia de lore não certifica mecânica de monstro/ataque ou ficha.

## Validação deste corte

- 80 testes backend focados (oficina/fontes/rotas/laboratório): PASS.
- 20 testes frontend relevantes: PASS; typecheck e build: PASS.
- Discover completo foi interrompido ao restarem 25 MB livres: INCONCLUSIVE.
- Nenhuma certificação visual em browser/celular físico ou mesa multirrede.
- OpenCode preservado; sem commit, push ou publicação automática de rascunhos.

Ativação confirmada por HTTP: resumo e detalhe da oficina retornam 200 para
Mestre e 401 para jogadores/anônimo; 276 pendentes, 12 cards no lote de leitura,
sem resultado inventado. `/health`, `/characters` e home pública respondem 200.
Credenciais e tabelas protegidas foram comparadas novamente ao backup inicial.

## Arquivos deste corte

- `backend/app/ai_workshop_routes.py`, `backend/test_ai_workshop_routes.py`;
- registro da rota em `backend/app/main.py`;
- `frontend/src/sceneWorkshop.ts`, `components/SceneWorkshopPanel.tsx`;
- `frontend/src/api.ts`, `pages/ScenePanel.tsx`, `companionTheme.css`;
- `frontend/tests/scene-workshop.test.cjs`;
- este relatório e `docs/CURRENT_COMPANION_CODE.md`.

Alterações anteriores/mistas preservadas. A oficina de leitura está ativada,
mas não há aceitação visual em browser nem automação de geração certificada.
