# Imagens das magias — 2026-10-07

Pedido: quatro PNGs originais para Mísseis Mágicos, Levitação, Escuridão e Relâmpago de Dorn; compartilhar Mísseis Mágicos com Morthak. Sem alterar regras.

As imagens foram importadas pela API existente de ícones. Os quatro downloads autenticados retornaram bytes idênticos aos anexos. Caminhos persistidos em `backend/app/data/spell_images.json`; nenhum token foi incluído no código.

`attach_spell_images` enriquece somente a apresentação das magias, inclusive as habilidades aprovadas de Dorn armazenadas anteriormente. Não altera usos, consumo, círculos, inventário ou efeitos. Morthak e Dorn compartilham arte, não recursos.

A ficha dá prioridade à imagem da magia, em vez de mostrar a imagem do equipamento exigido. Os cards usam as mesmas classes de cabeçalho/resumo do inventário, com ícones quadrados de 27 px. Controles existentes de alvo e uso de Mísseis permanecem preservados. Nenhuma alteração global de tipografia.

## Validação

- `python -m unittest discover -s backend -p test_spell_images.py`: 4/4 PASS.
- Backend completo: 385/385 PASS, executados neste estado.
- `node --test tests/*.test.cjs`: 149/150 PASS. Falha preexistente: `shared-attack-target.test.cjs`, teste que ainda exige alvo ao lado do nome via seletores CSS antigos; o layout atual anterior a este corte empilha controles. Não alterado nesta tarefa de imagens.
- `npx --no-install tsc --noEmit`: PASS.
- Build isolado em `%TEMP%/spell-images-20261007-build`: PASS; aviso de chunks grandes, não erro.
- `git diff --check`: PASS; avisos existentes de LF/CRLF.
- `node tests/spell-images-visual.cjs` com Playwright do runtime: PASS em 390×844 e 1440×900. Componentes reais hidratados, stylesheet real e PNGs originais, sem chamadas ao banco operacional. Quatro imagens carregadas; ícones 27×27; seleção/uso do alvo; botão bloqueado sem alvo e após consumo; sem overflow horizontal.
- Screenshots: `%TEMP%/spell-images-visual-4fkPRV/mobile.png` e `desktop.png`. Mobile inspecionado visualmente.

As imagens estão importadas no catálogo operacional. O vínculo e a apresentação novos dependem da próxima ativação do backend/frontend. Nenhum reinício, commit ou push realizado neste corte. QA de componentes não é comprovação multicliente em mesa.
