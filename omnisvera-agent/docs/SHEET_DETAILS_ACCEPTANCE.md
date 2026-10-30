# Fichas: imagens e leitura flutuante — 2026-10-07

- Imagens originais de Força Arcana e Velocidade importadas pela API de ícones. Downloads autenticados conferidos byte a byte; mapeamento compartilhado em `spell_images.json`, agora também para poderes, sem alterar regras ou usos.
- Descrições de habilidades/magias exibem a imagem real quando disponível, inclusive o animal selecionado da Forma da Noite.
- `SheetDetail` oferece leitura compacta em portal no body, imagem, texto, fechar/Escape e rolagem vertical. Usado nos nomes/ícones de ataques, recursos, traços, componentes, efeitos e protocolos de Dorn. Abrir descrição não executa ações. Inventário continua com seu leitor existente.
- Forma da Noite tem uma coluna própria: título acima do contador, seletor e botão. Não foram alteradas as regras de transformação ou seus três usos.
- Sem aumento global de fonte ou novos poderes. Elementos operacionais como atributos, rolagens, equipar e usar mantêm suas ações próprias.

## Checks

- Backend completo: 386/386 PASS.
- Frontend completo: 152/153 PASS. Única falha preexistente: teste `shared-attack-target.test.cjs` exige CSS antigo com alvo ao lado do nome de Mísseis; não alterado aqui.
- TypeScript: PASS.
- Build isolado: PASS (`%TEMP%/sheet-detail-20261007-build`), aviso de chunks grandes.
- `git diff --check`: PASS.
- QA com componentes reais hidratados e CSS real em 390×844 e 1440×900: PASS. Duas artes de Vezemir e animal selecionado carregam nas janelas; fechar e Escape funcionam; título da Forma da Noite acima do seletor; sem overflow horizontal. Dados fixture, sem ações no banco real.
- Screenshots em `%TEMP%/sheet-detail-visual-pOYhnz`; imagens mobile de Força Arcana e Forma da Noite inspecionadas.

Nenhum canon, bônus, duração, custo ou permissão alterado. Sem commit/push.

## Arquivos deste corte

- `backend/app/data/spell_images.json`: duas artes de Vezemir.
- `backend/app/character_play.py`: arte de poderes além de magias.
- `backend/test_spell_images.py`: regressão para Vezemir.
- `frontend/src/components/SheetDetail.tsx`: leitor compartilhado.
- `frontend/src/components/DornConstructDetails.tsx`: traços/componentes/efeitos clicáveis.
- `frontend/src/components/DornProtocolControls.tsx`: leitura dos protocolos, preservando ações.
- `frontend/src/pages/SessionWorkspace.tsx`: imagens nas descrições e leitura de ataques/recursos.
- `frontend/src/styles.css`: imagem flutuante e layout específico da Forma da Noite.
- `frontend/tests/sheet-detail.test.cjs`, `sheet-detail-visual.cjs`: cobertura e QA.
- Este relatório.

Ativado pelo inicializador oficial: frontend servido com `index-_s9blX2i.js`, backend PID 13476. HTTPS público respondeu; ficha owner de Vezemir devolveu as duas artes. Tokens preservados. Nenhuma ação de combate ou consumo executado no banco operacional durante QA.
