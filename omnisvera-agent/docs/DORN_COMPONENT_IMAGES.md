# Imagens dos componentes de Dorn — 2026-10-08

Aplicadas pelo editor autenticado existente, em `image_path`, sem alterar classificações ou regras:

| Componente | Item persistente | Original importado em `zz_media/ui/icons/uploads/` |
| --- | --- | --- |
| Escritas Rúnicas | session-item:18 | escritas_runicas_d049fd2221.jpg |
| Malha Rúnica | session-item:19 | malha_runica_05ad221463.jpg |
| Compartimento interno | session-item:17 | compartimento_interno_73d982feed.jpg |
| Núcleo Rúnico | session-item:14 | nucleo_runico_7bc0fef279.jpg |
| Cristal de Memória danificado | session-item:16 | cristal_de_memoria_danificado_0e0329aac8.jpg |

Originais comparados byte a byte. Imagens registradas na biblioteca de itens do Vault e associadas aos itens da ficha atual. A API fornece `thumbnail`/`cover` usados pelos cards e descrições existentes; não houve alteração do código operacional, reinício ou substituição do bundle.

Nome, tipo, descrição, efeitos, slots e regras preservados. O editor normalizou campos opcionais ausentes para valores vazios/nulos; isto foi verificado, sem mudança do +2 CA das Escritas ou do dano 1d6+2 da Malha. Estado da ficha, PV e recursos iguais antes/depois. Nenhum descanso, equipar/guardar, gasto ou progressão executado.

Checks desta execução: backend 392/392; frontend 161/161; TypeScript e build isolado passaram (aviso de tamanho de chunks); `git diff --check` sem erros. QA dos componentes React reais e CSS compartilhado com os cinco originais, em desktop 1440×900 e mobile 390×844: ícones carregados, descrições abrem/fecham com imagem correta e nenhum overflow. Não representa ensaio multicliente completo.

Consulta autenticada de Dorn pela URL pública confirmou cinco imagens nos itens e HTTP 200 para todas as mídias.

Arquivos desta etapa: este relatório, `frontend/tests/morthak-images-visual.cjs` (fixture reutilizada para os componentes de Dorn) e os cinco JPEGs acima. As associações estão nos dados operacionais locais dos itens, não em código ou Git. Trabalho anterior preservado; sem commit/push/reset.
