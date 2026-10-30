# Omnisvera: direcao de arte e escolha do modelo

## Decisao atual

O provider padrao agora usa `@cf/black-forest-labs/flux-2-klein-9b`,
conforme aprovacao de Sage em 2026-10-06. Timeout: 180 segundos.
Credenciais preservadas; sem fallback automatico ou upgrade para plano pago.
Backend operacional reiniciado pelo `start_companion.ps1 -NoBuild -NoRebuild`
em 2026-10-06, por autorizacao de Sage. Novo listener PID 21548;
health autenticado OK e HTTPS Tailscale respondeu 200. Tunel preservado.
Nao declarar que ele e o melhor modelo sem comparacao sobre os mesmos assets.
Nao regenerar centenas de entradas antes de verificar referencias e amostras.

### Amostra da invocacao com o novo padrao

Em 2026-10-06, o provider padrao 9B gerou em 4,37 segundos:
`zz_media/ui/icons/drafts/morthak-wood-skeleton-klein9b-v1.png`.
Referencia de estilo (nao de identidade): `zz_media/characters/morthak.jpg`.
Mesmo prompt do rascunho 4B; sem seed fixa, portanto comparacao exploratoria.
Referencia original preservada por SHA-256.
SHA-256 da saida: `6028c9da237bb07f907d827e88ed9c8a2c4f80c0e52709ae0b3422ce6ef3f467`.
QA real: madeira mais evidente no torax/bracos e silhueta clara, mas pes
cortados pelo enquadramento. Resultado PARCIAL; nao promovido ao catalogo
ou ao banco operacional. Proximo ajuste: enquadramento completo com margens.

### Primeiro lote publicado em 2026-10-06

Flux Klein 9B via integracao existente do Companion (nao imagegen/OpenAI).
Originais e variantes anteriores preservados. Duas geracoes, sem fallback:

- Esqueleto v2: 4,83 s; SHA-256
  `d3368a3d451c8eb1b4d24edf4ef5cd4cff57fe46ab44926864945304c5a3a578`.
  QA: corpo inteiro, pes presentes, madeira e ossos legiveis. Publicado pela
  API GM na biblioteca: `zz_media/ui/icons/uploads/esqueleto_de_madeira_de_morthak_klein_9b_f86009b1ee.jpg`.
  Um pin de invocacao existente recebeu essa imagem (antes sem imagem),
  mantendo PV e coordenadas. Nenhuma acao ou iniciativa executada.
- Misseis Magicos: 3,87 s; SHA-256
  `91eeaaa7accf2327eb83be397a17107dcc2038a403347df9c56ca53f062e477b`.
  QA: efeito arcano legivel, sem personagem ou equipamento extra.
  Biblioteca: `zz_media/ui/icons/uploads/misseis_magicos_klein_9b_d0b43a6e77.jpg`.
  Disponivel como imagem; ainda nao vinculado automaticamente ao card de magia.

Novas invocacoes de esqueleto ainda nao herdam essa imagem automaticamente.
Esse vinculo requer pequeno ajuste com regressao; nao foi improvisado no banco.

Prompt do esqueleto (referencia: rascunho 9B v1, identidade):
> Use case: precise-object-edit. Image 0 is the exact skeleton identity and material reference. Keep the same skull, pale bone anatomy, dark wood reinforcement around the rib cage and forearms, faint green aura and dark painterly style. Change ONLY framing: zoom out enough to show the entire body, BOTH FEET including toes, and all fingers completely inside the square image, with 12 percent empty margin below the feet and above the skull. One skeleton, no equipment, no text, no other figures.

Prompt de Misseis (referencia: morthak.jpg, estilo apenas):
> Use case: stylized-concept. Asset: square RPG spell icon for Magic Missiles. Image 0 is ONLY a reference for dark fantasy painterly rendering, textured shadows and restrained magical lighting; do NOT reproduce the necromancer or any skulls. Depict a compact cluster of luminous arcane projectiles with clear bright cores and curved energy trails moving across a dark unobtrusive background. This is generic arcane force, not blood or an undead summoning. Readable at small icon size, centered effect with margins, limited clean composition. The illustration does not encode a mechanical projectile count. No character, no staff, no skull, no creature, no UI, no letters, no watermark.

Segundo a documentacao BFL consultada em 2026-10-06, Klein prioriza velocidade;
Pro e Max priorizam qualidade de producao/edicao. Isso e posicionamento do
fabricante, nao evidencia de superioridade nas imagens desta campanha.
Fonte: https://bfl.ai/models/flux-2

## Contrato visual

- Referencia de identidade: preservar silhueta, anatomia, materiais, vestuario
  e detalhes reconheciveis. Nao acrescentar equipamento ou canon.
- Referencia de estilo: preservar tratamento pictorico e luz; nao copiar o
  personagem da referencia para uma magia ou invocacao.
- Itens: um objeto, inteiro, legivel em miniatura, sem personagem/texto/UI.
- Criaturas: anatomia legivel, silhueta clara, sem deformacoes ou membros extras.
- Magias: efeito legivel em miniatura; nao desenhar regras, alvos ou quantidades
  de disparos como se fossem mudancas mecanicas.
- Variantes reanimadas reutilizam o original e o filtro visual quando possivel.
- Arquivos originais nunca sao substituidos durante a avaliacao das amostras.

## Amostra de aceitacao

1. Grisalma: identidade precisa baseada em `zz_media/items/grisalma.png`.
2. Misseis Magicos de Morthak: efeito arcano, referencia de estilo do retrato,
   sem reproduzir Morthak ou transformar automaticamente a magia em necromancia.
3. Esqueleto de Madeira: invocacao distinta do necromante, amostra ja gerada.

Revisar identidade, enquadramento inteiro, silhueta em miniatura, anatomia,
ausencia de texto e coerencia com o Vault. Falha de identidade bloqueia a
promocao; uma imagem bonita sozinha nao basta.

## Promocao e sincronizacao

Geracoes ficam em `zz_media/ui/icons/drafts/`, com prompt, modelo e hashes de
referencias registrados. Somente assets revisados devem ser ligados ao catalogo.
Nenhuma amostra muda stats, ficha, inventario ou lore.

Vault: fonte de canon, regras aprovadas e referencias visuais.
Companion: fonte de estado operacional (PV, turnos, consumo e inventario em uso).
Resumo de sessao: projecao revisada da transcricao e dos registros operacionais.
Nao usar sincronizacao bidirecional cega que sobrescreva uma fonte com a outra.

## Resultado do piloto de 2026-10-06

- Grisalma: `zz_media/ui/icons/drafts/grisalma-reference-v1.png`, SHA256
  `aeb1fadbb043287d8e57122c82de5a58179c9259e75510e30afc51c4d9256683`.
  Original preservado (SHA256
  `86c5a52dfd3346355a164210258063bae939f3e6476c97280e75a7e858b56b97`).
  Inspecao visual real: silhueta geral reconhecivel, mas ornamentos e detalhes
  do cabo/punho foram simplificados. Identidade PARCIAL; nao promovida.
- Misseis Magicos: duas chamadas ao provider terminaram em ReadTimeout,
  sem arquivo salvo. Nao houve fallback para prompt sem referencia. Falha de
  transporte nao constitui avaliacao de qualidade da imagem/modelo.
- Prompts completos, papeis das referencias e hashes preservados no arquivo
  local ignorado `.observer-runtime/art-pilot-20261006.json`.
- Nenhuma imagem operacional substituida, banco alterado ou canon novo.

## Proxima etapa

### Klein 9B: preparacao do teste

O provider permite selecao explicita por instancia:
`FluxKleinProvider(model='flux-2-klein-9b', timeout_seconds=180)`.
Durante o piloto, o default permaneceu 4B, sem fallback automatico. Referencias e prompt do piloto
Grisalma devem ser mantidos identicos; salvar em novo arquivo e comparar com
o original e a amostra 4B. Nao promover imagens antes da revisao.

Consulta read-only ao plano Cloudflare retornou HTTP 403 (token sem permissao
para subscriptions). Isso NAO prova falha na geracao nem cota esgotada.
O usuario confirmou Workers Free. Teste real executado sem ativar plano pago,
creditos ou fallback. Primeira chamada: HTTP 500, sem arquivo; segunda chamada:
PASS em aproximadamente 4,5 segundos. O modelo aparece no catalogo consultado
com as credenciais existentes. Saldo exato de neurons nao foi consultado.

Arquivo: `zz_media/ui/icons/drafts/grisalma-klein9b-reference-v1.png`.
SHA256: `fe1763154101048de5563b62039ff472b35f571149466a69336a73078e3b6d64`.
Prompt e referencia identicos ao piloto Grisalma 4B em
`.observer-runtime/art-pilot-20261006.json`; apenas endpoint/modelo e timeout
mudaram. Sem seed fixo no piloto anterior: comparacao exploratoria, nao benchmark.
Original preservado por verificacao de SHA256 antes/depois.

Inspecao visual real do original, 4B e 9B: o 9B deixou a cabeca de dragao e olhos
mais legiveis e melhor separacao do metal/fundo. Ainda simplifica os ornamentos
e o cabo, alterando a identidade exata. Fundo mais uniforme e acabamento menos
texturizado que o original. Resultado PARCIAL para fidelidade; nao promovido ao
catalogo ou inventario. Naquele piloto o default global continuou 4B, sem reinicio operacional.

Validacao desta preparacao: backend completo 316/316 PASS, testes especificos
de referencias/provider 10/10 PASS, TypeScript PASS, build PASS e diff-check PASS.
Warnings preexistentes de conexoes SQLite nos testes e chunks grandes no Vite.
Esses checks usam mocks/fixtures. A inferencia real acima e evidencia separada;
nao foram reexecutados nesta rodada, que adicionou apenas amostra/documentacao.

Esquema de referencia do 9B conferido na documentacao oficial:
https://developers.cloudflare.com/changelog/post/2026-01-28-flux-2-klein-9b-workers-ai/

- Comparacao controlada com outro modelo, caso haja acesso autorizado.
- Consolidacao integral da S6 antes de publicar cronica ou novos NPCs.
- Reconciliacao dos nomes/aliases antes de gerar todas as entradas do inventario.
- Revisao das amostras e promocao para o pipeline existente do Companion.
