# Imagens de Raziel — 2026-10-07

## Terceiro lote — traços passivos

Aplicadas na ordem dos anexos: Não-Vida Consciente (`nao_vida_consciente_vampiro_584701a3cb.jpg`), Visão no Escuro (`visao_no_escuro_vampiro_50a7c373b3.jpg`), Imunidades Vampíricas (`imunidades_vampiricas_a3c74b3a46.jpg`), Fotossensibilidade (`fotossensibilidade_6c735c8819.jpg`) e Cura Vampírica Invertida (`cura_vampirica_invertida_d66950f088.jpg`). Originais importados e comparados byte a byte; armazenados em `zz_media/ui/icons/uploads/`. Mantidos passivos, com todas as regras intactas. A arte de Não-Vida Consciente de Morthak permanece distinta.

Arquivos desta continuação: `backend/app/data/spell_images.json`, `backend/test_spell_images.py`, `frontend/tests/morthak-images-visual.cjs`, este relatório e os cinco JPEGs no Vault. Não foi necessária alteração do código operacional, reinício ou novo bundle servido: o backend consulta a configuração a cada leitura.

Checks executados neste lote: backend 391/391; frontend 154/155 (falha preexistente de layout de Mísseis Mágicos); TypeScript, build isolado e `git diff --check` passaram. Build com aviso de tamanho de chunks. QA dos componentes React reais, CSS e originais em desktop 1440×900 e mobile 390×844: ícones e descrições com imagens corretas, abertura/fechamento e nenhum overflow horizontal. Não constitui teste completo multicliente em mesa.

Confirmado no Companion atual com acesso do próprio Raziel pela URL pública: cinco habilidades com imagem e cinco respostas HTTP 200 para a mídia. Sem commit/push; alterações anteriores preservadas.

## Segundo lote — traços e poderes

Adicionadas, na ordem dos anexos: Regeneração Vampírica (`regeneracao_vampirica_cafaba68dd.jpg`), Fome de Sangue (`fome_de_sangue_7fd85cab10.jpg`), Medo (`medo_8cfeaf8766.jpg`, habilidade `medo-vampirico`), Sentido do Sangue (`sentido_do_sangue_b9be7aaba5.jpg`) e Corpo Predatório (`corpo_predatorio_a217923463.jpg`). Originais importados pelo endpoint autenticado e verificados byte a byte no Vault. Sem mudança de regras, custos ou bloqueios.

Arquivos alterados nesta continuação: `backend/app/data/spell_images.json`, `backend/test_spell_images.py`, `frontend/tests/morthak-images-visual.cjs`, este relatório e os cinco JPEGs em `zz_media/ui/icons/uploads/`.

Checks deste lote: backend 390/390; frontend 154/155 (mesma falha preexistente de layout de Mísseis Mágicos); TypeScript, build isolado e `git diff --check` passaram. Build apenas com aviso de tamanho de chunks. QA dos componentes reais e imagens originais em desktop 1440×900 e mobile 390×844: cinco ícones, descrições com imagens corretas, abertura/fechamento e nenhum overflow. Não é prova de uma sessão multicliente completa.

As cinco imagens estão ativas na ficha atual, verificadas pela URL pública com acesso de Raziel e HTTP 200 para cada mídia. A configuração de imagens é lida a cada consulta: não foi necessário reiniciar o backend ou substituir o bundle. Sem commit ou push; trabalho anterior preservado.

## Primeiro lote

Aplicadas as imagens originais aprovadas, na ordem: Reserva de Sangue, Lâmina de Sangue, Marca Rubra, Caixão e Mordida. Importadas pelo endpoint autenticado existente e armazenadas no Vault em `zz_media/ui/icons/uploads/`. As imagens baixadas após importação foram comparadas com os anexos originais.

O backend enriquece também técnicas e recursos com arte aprovada. A seção Recursos resolve a imagem e a descrição pela habilidade de recurso correspondente, mantendo o contador atual/máximo. Os cards reutilizam os ícones compactos e a descrição flutuante existentes. Não foram alterados custos, recuperação, dados, alvos ou efeitos.

Arquivos desta etapa:

- `backend/app/data/spell_images.json`
- `backend/app/character_play.py`
- `backend/test_spell_images.py`
- `frontend/src/pages/SessionWorkspace.tsx`
- `frontend/tests/spell-images.test.cjs`
- `frontend/tests/morthak-images-visual.cjs` (fixture reutilizada para Raziel)
- Este relatório e os cinco JPEGs importados no Vault.

Validação nesta execução: backend 389/389; frontend 154/155, com a falha preexistente `missiles reuse inventory card parts with compact target beside the name` (expectativa antiga de CSS). TypeScript sem erros. Build isolado e build servido concluídos, com aviso de tamanho de chunks. `git diff --check` sem erros.

QA com componentes React reais, CSS do projeto e imagens originais: desktop 1440×900 e mobile 390×844; cinco ícones carregados; descrições abrem/fecham com a imagem correspondente; nenhum overflow horizontal. A fixture de Reserva de Sangue é somente leitura e mostra o contador. Não equivale a uma sessão multiusuário em mesa.

Ativado no Companion atual pelo launcher oficial de backend, em janela oculta persistente. Verificado pela URL pública com autenticação do próprio Raziel: cinco habilidades com `image_path`, cinco imagens HTTP 200 e bundle `index-C8CdwXS_` servido. Sem commit ou push. Alterações anteriores e trabalho não relacionado preservados.
