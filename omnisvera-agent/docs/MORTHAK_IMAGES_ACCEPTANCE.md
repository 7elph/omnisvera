# Imagens de Morthak — 2026-10-07

Importados os cinco JPEGs originais, com conferência byte a byte pela API autenticada de mídia: Adaga de Osso; Levantar Esqueleto; Não-Vida Consciente; Animar Mortos; Memória Fraturada.

Os caminhos são metadados de apresentação em `backend/app/data/spell_images.json`. O enriquecimento existente agora atende também traços e ataques. Não altera descrição, usos, passividade, dano, recursos ou permissões. Imagens aparecem nos ícones compactos e na leitura flutuante existente; Adaga de Osso também resolve arte pelo ID no card de ataque principal.

Arquivos deste corte:

- `backend/app/data/spell_images.json`: cinco correspondências.
- `backend/app/character_play.py`: incluir tipos ability/attack na apresentação.
- `backend/test_spell_images.py`: preservar passivas, usos e descrições.
- `frontend/src/pages/SessionWorkspace.tsx`: arte do ataque próprio, sem alterar ação.
- `frontend/tests/spell-images.test.cjs`: regressão da arte do ataque.
- `frontend/tests/spell-images-visual.cjs`: limitar QA anterior às quatro magias de Dorn mesmo após expansão do catálogo.
- `frontend/tests/morthak-images-visual.cjs`: cinco imagens/descrições em mobile e desktop.
- Este relatório.

QA hidratado de componentes reais, imagens originais e CSS real, com fixtures sem ações no banco: PASS em 390×844 e 1440×900. Cinco ícones carregados, janelas abrem/fecham com a imagem correta, sem overflow. Screenshot mobile inspecionado; evidências `%TEMP%/morthak-images-visual-SBtz28`.

Frontend completo: 153/154 PASS. Falha preexistente do teste de CSS de Mísseis (`shared-attack-target.test.cjs`) mantida explícita, sem alterar o layout nesta tarefa. TypeScript PASS.

Backend completo: 387/387 PASS. Build isolado e operacional: PASS (aviso de chunks grandes). `git diff --check`: PASS.

Sem commit, push ou alteração de canon.

## Segundo lote — traços

Adicionadas as imagens originais de Chamado Necromântico, Ossos sem Carne, Repouso Imóvel, Corpo Quebradiço e Cura Antinatural. Download autenticado byte a byte igual aos anexos. Nenhuma regra/passividade alterada.

Arquivos deste lote: `backend/app/data/spell_images.json`, `backend/test_spell_images.py`, `frontend/tests/morthak-images-visual.cjs` (modo fixture para traços) e este relatório. Sem alterações de código de produto ou CSS.

Endpoint público de owner Morthak devolveu os cinco caminhos e `active=false`; todas as mídias responderam HTTP 200. Metadados carregam a cada leitura, portanto não exigiram reinício para ativação. O backend estava indisponível ao iniciar o lote e foi restabelecido pelo inicializador oficial, separado do ciclo do terminal de validação; PID 10988.

QA mobile 390×844 e desktop 1440×900: PASS nos cinco ícones e nas cinco descrições com imagem, abertura/fechamento e ausência de overflow. Screenshot mobile inspecionado em `%TEMP%/morthak-images-visual-2xncwt`.

Checks deste lote: frontend 153/154, com a mesma falha preexistente de Mísseis; TypeScript PASS; build isolado PASS (bundle idêntico ao operacional, `index-nkBm9A-x.js`); `git diff --check` PASS. Sem commit/push.

Backend completo deste lote: 388/388 PASS, executados em 101,670 s.

## Afastar Mortos-Vivos

Imagem `1000207629.jpg` importada sem alteração de bytes e vinculada a `afastar-mortos-vivos`. Confirmado no endpoint público com perfil owner de Morthak: caminho correto, mídia HTTP 200 e traço preservado como passivo. Ativo sem reinício, por leitura dinâmica do catálogo. Mesmo leitor flutuante e CSS existentes, sem novo código de interface.

Arquivos: `backend/app/data/spell_images.json`, `backend/test_spell_images.py` (ampliação da regressão de traços passivos) e este relatório. `git diff --check`: PASS. Sem commit/push.

Checks executados neste estado: imagens 7/7; backend completo 388/388 (99,332 s); TypeScript PASS; build isolado PASS, sem mudança de bundle frontend.
