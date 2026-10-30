# Sete etapas — execução e limites (16/10/2026)

**Atualização posterior:** sete contratos ativados; lote seguinte amplia para
dez ações em código. Ativação e checks finais constam na retomada.
Migração integral e startup MCP continuam pendentes. Evidência atual, inclusive
falhas e limitações: [retomada](RESUME_COMPANION_2026-10-16.md).

Branch: `devin/create-omnisvera-class-standard`, base local `1a07a84`.
Worktree já misto antes deste corte, preservado; sem staging, commit ou push.
Nada foi ensaiado na mesa operacional. Não se alteraram Vault, Godot ou modelos.

## Entregas históricas anteriores à retomada

1. **Ativação do piloto:** Relâmpago já tinha contrato, testes e ensaio isolado.
   Reinício operacional anterior foi bloqueado pelo ambiente antes da execução;
   não houve nova tentativa por outro caminho. O processo operacional não foi
   reiniciado neste corte. Código em disco/build não prova backend atualizado.
2. **Segunda magia:** Reflexos recebeu contrato tipado self/mirror_images,
   custo e dados resolvidos pelo mesmo backend. Reutiliza efeito, relógio,
   confirmação, orçamento e recibo nativos; não concede magia ou recurso em GET.
3. **Componentes:** validação estrita, fórmulas limitadas por nível, revisão,
   rolagem com RNG nativo e consumidor de recurso na transação existente.
   Alvo/grid/JP/dano/duração permanecem nos handlers atuais, não num segundo
   motor. Dois contratos são provas de famílias distintas, não de todo o acervo.
4. **Quatro fichas:** manifesto aditivo sobre o DTO efetivo, incluindo
   overrides/nível/especialização. Expõe bindings nativos, disponibilidade,
   passivas, assistidas e bloqueadas; itens utilizáveis não desaparecem.
   Auditoria não cria/reconcilia ficha/estado. Inicializadores legados ainda
   podem criar schema. Apenas duas magias migraram para o contrato novo;
   manifestar os demais handlers não significa reimplementá-los/certificá-los.
5. **NPCs/monstros:** usa `sheet` do token e executor nativo de ataques para
   validar o manifest. Dados inválidos/tipos de pin indevidos não ganham binding;
   riders e habilidades textuais ficam assistidos. Sem banco paralelo de NPC.
6. **Cenas:** laboratório GM privado/recolhido, propostas/revisões imutáveis,
   histórico, decisão manual e recibos. Edição invalida aprovação/evidência
   atual. Rotas verificam relatório MCP local; retry aceita o recibo original
   antes de reler arquivo. O relatório cobre **código existente**, não execução
   do JSON proposto. Aprovação nunca publica, executa ou concede poderes.
7. **PDFs:** primeiro lote de quatro referências conferidas, com hash, edição,
   licença/atribuição e páginas físicas/impressas no catálogo existente.
   Fonte OD2 não substitui regra OD1/campanha. `execution_approved=false`.
   Não foi importado/revisado todo o acervo de centenas de magias/itens.

## Divisão de trabalho

OpenCode, sessão existente e Muse Spark 1.3 Free por mensagem (sem mudar modelo
global): `scene_lab_store.py`, testes e documento do armazenamento; depois
endurecimento de JSON/limites/intenção e leitura das revisões. Codex revisou,
integrou rotas/UI, acrescentou recuperação de recibo e coordenou contratos,
manifests, proveniência e testes. Nenhum agente tinha autorização para mudar
regras de RPG, tocar fichas operacionais, publicar ou reiniciar serviços por QA.

## Verificação

Suíte backend completa: **953 testes, OK, 1 skip** (875,4 s). Após os últimos
ajustes de manifests/recibos/runner, **113 testes focados, OK, 1 skip** (58,9 s).
O skip é criação física de symlink sem privilégio Windows; rejeição de
componentes symlink também tem teste determinístico aprovado.

Frontend completo: **317/317 PASS**. Após o ajuste final de histórico da UI,
**12/12 focados PASS**; typecheck e build repetidos passaram. Warning de chunks
grandes e ResourceWarnings legados permanecem. A suíte completa precedeu esse
último ajuste, coberto pela repetição focada; não somar contagens como ações
certificadas. Ensaios HTTP/browser são registrados após seus resultados reais.

REDs focados cobrem ausência dos componentes, metadata, revisão obsoleta,
falsos bindings, privacidade, concorrência, replay e estados assíncronos da UI.
A fixture recebe cópias limitadas de imagens referenciadas: faltantes/limites
são expostos, nunca usados como prova de arte alinhada. Screenshots exigem
aceitação explícita; mobile emulado não prova celular físico/redes distintas.

## Limites que continuam reais

- Ativação operacional não confirmada; não contornar bloqueio de reinício.
- Migração integral de cada habilidade das quatro fichas ainda não concluída.
- Habilidades genéricas e riders de monstros não ganham automação por regex.
- Catálogo completo ainda precisa revisão em lotes; quatro fontes não são 854.
- Laboratório não executa JSON arbitrário, não prevê escolhas como fatos,
  não gera imagens automaticamente e não publica propostas aprovadas.
- Regras pendentes continuam bloqueadas/assistidas; falta de teste nunca vira
  `certification_ready=true`. Mesa real multirrede continua INCONCLUSIVE.
- Cliente legado de Reflexos continua aceito; a UI atual ainda não envia sua
  revisão no comando. Backend resolve o contrato vigente e testa revisão quando
  recebida. Relâmpago mantém o comando versionado do piloto.

## Arquivos por fronteira

- Contratos: `action_contract.py`, `action_components.py`, `action_library.py`,
  `dorn7_mage3.json`, `dorn_spells.py`, `dorn_spell_pack.py`, `character_play.py`.
- Inventário/fontes: `native_action_manifest.py`, `action_audit_routes.py`,
  `catalog_provenance.py`, `data/catalog_provenance.json`, registro em `main.py`.
- Cenas: `scene_lab_store.py`, `scene_lab_routes.py`, `test_run_evidence.py`,
  `SceneLabPanel.tsx`, `sceneLabApi.ts`, `api.ts`, montagem em `ScenePanel.tsx`.
- QA: testes focados de cada fronteira, `scripts/fixture_media.py`, integração
  em `run_sheet_test.py`, `cf01_probe.py`, metadata em `agent_test_jobs.py`,
  smoke privado de Cenas e runner isolado correspondente.
- Guias: este documento, `AI_COMPONENT_MAP.json`, `AI_TEST_TOOLS.md`,
  `CURRENT_COMPANION_CODE.md` e documentos curtos dos lotes.

## Receita para a próxima IA (não é tarefa para o Mestre)

1. Leia AGENTS/guia e manifesto autorizado do ator/token. Separe disponibilidade
   de cobertura; escolha família já suportada, sem interpretar texto como código.
2. Crie proposta privada numa cena existente: `kind=action`, conteúdo com
   `native_ref`, revisão do contrato, fonte/edição/páginas quando houver,
   `proposed_changes` e testes esperados. Não duplique uma ficha/catálogo.
3. Mudanças de regra exigem aprovação explícita; propostas continuam dados,
   nunca scripts, shell, SQL ou chamadas aceitas dinamicamente pelo executor.
4. Implemente o menor adaptador no handler nativo, começando por RED
   determinístico. Não desative hooks de PV, custos, idempotência ou privacidade.
5. Rode MCP com quatro atores e `ui=true`, guarde `run_id`, interprete os gaps
   e revise imagens. `POST .../evidence` recebe só ID do run/versão/request;
   não inventar summary nem usar `PASS` como autorização para aplicar proposta.
6. Peça revisão/publicação separadamente. Dados de proposta, código testado,
   backend ativo e mesa física comprovada são quatro marcos diferentes.

## Evidência de navegador — laboratório

`run_scene_lab_visual.py`, fixture TEMP, resultado **PASS**: criar proposta,
editar v2, consultar conteúdo v1 preservado, aprovar revisão sem publicar,
recarregar e reencontrar v2, largura 390 px sem overflow, API/UI negadas ao
jogador. Combate, estado e inventário de Morthak permaneceram iguais.
As capturas 1440/390 foram abertas e revistas explicitamente pelo Codex:
painel legível/compacto, revisões separadas e botões alcançáveis dentro da largura.
Aceitação restrita ao laboratório; mídia dos mapas dessa fixture estava ausente
e não foi certificada. Celular físico/redes distintas continuam INCONCLUSIVE.
Artefatos privados em TEMP: `omni-scene-lab-final-20261016-01`.

OpenCode executou dois starts MCP reais com os quatro atores e `ui=true`:
`test-944f780974384a93b5177f8a5e27cf98` e
`test-b5598cb53a2747368b9894a5b4ab3111`. Ambos terminaram
**ERROR/INCONCLUSIVE no startup**, antes de qualquer cenário/API/browser:
45 s sem health, log do child vazio. Não são FAIL de magia nem PASS de combate.
Mantidos sem apagar/reclassificar; a causa específica não foi demonstrada.
O runner independente de Cenas iniciou a fixture nativa e passou; isso não
certifica o caminho MCP. Nova execução nativa de combate é registrada à parte.

### Ensaio nativo completo

Fixture `omni-seven-native-combat-20261016-01`: **82 cenários**, sendo
**79 PASS, 0 FAIL, 3 EXPECTED_BLOCK**. Bloqueios comprovados: Vezemir/Morthak
sem arma equipada no slot ranged genérico (Adaga de Osso tem ataque próprio)
e Clonagem sem fragmento de cristal no estoque copiado. Não se concederam armas,
componentes, níveis ou PV operacionais para tornar o ensaio artificialmente verde.

`ui_suite=combat`: **PASS** em readiness (6 contextos GM/jogador, quatro atores,
360/390/1440 px, 81,9 s) e ações (10 ativações, 288,2 s): buffs, Frenesi,
Provocação, Aterrorizar, Força Arcana/Reflexos/Teia/Dissipar/Guarda de Dorn.
O runner terminou com código 0 e parou somente sua fixture. Não há dado humano
ou redes externas envolvidos. `certification.ready=false` permanece correto.

As seis capturas de readiness foram revistas: cards/identidade sem a sobreposição
antiga, ações e contadores legíveis nas larguras ensaiadas. Algumas imagens de
itens/habilidades ainda faltam nessa cópia de mídia; não foi aceita a completude
visual de todas as fichas. 66 referências de mídia do banco foram copiadas
(66.594.276 bytes, sem faltantes nesse conjunto). O helper passou a incluir
também mídia de identidade das notas ligadas aos quatro atores, nunca texto ou
notas privadas/não relacionadas: RED reproduzido, **12 testes OK, 1 skip**.
Isso não certifica todo ícone derivado dinamicamente dos catálogos.

O bootstrap dos children foi endurecido com `cf01_probe.fixture_environment`:
allowlist de variáveis do sistema e credenciais fictícias da fixture; não
herda hooks/paths Python, proxies, senhas OpenCode ou tokens operacionais do
host. Servidor/API/browser e runner de Cenas reutilizam a mesma fronteira.
RED de ausência do helper; **24/24 testes focados PASS** incluindo isolamento,
porta ocupada sem kill, startup/timeout, limpeza apenas dos children próprios
e preservação de aceitação visual pendente. Não atribuir a falha anterior a
uma variável específica sem evidência; hardening não substitui novo ensaio.

Última tentativa MCP com ambiente de child limpo e apenas cinco cenários
exatos: `test-0be1dea60bc64c73970c9c8eb7c2f4f0`, também
**ERROR/INCONCLUSIVE no startup**. O mesmo runner via CLI passou; portanto
não declarar o conector pronto nem trocar o modelo/configuração para esconder
a diferença. OpenCode terminou sua tarefa sem editar outras fontes.
Solicitada autorização para recarregar **somente companion-tests**, mantendo
Companion/modelo/fichas intactos; não efetuado sem resposta.

Checks finais do adapter/ambiente/mídia/runners: **54 testes OK, 1 skip**.
Sem commit/push/staging; HEAD continua `1a07a84`, branch preservada e índice
sem arquivos deste corte. A ativação operacional e a migração integral ainda
estão pendentes: este documento registra entregas e não sete etapas completas.
