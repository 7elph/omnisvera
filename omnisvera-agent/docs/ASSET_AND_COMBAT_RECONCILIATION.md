# Arte e combate - acompanhamento de 2026-10-06

O pedido inclui substituicao de arte, consolidacao da sessao 6 e defeitos de combate.
Nao confundir correcoes locais com validacao operacional ou substituicao de todas as imagens.

## Corte de combate

- Preservar posicoes de pins existentes ao iniciar combate.
- Nao publicar movimentos/edicoes de pins ocultos no registro publico.
- Linha de ataque confirmado compartilhada pelo ledger autorizado, limitada ao turno.
- Resultado de ataque/magia em painel nao modal e compacto.
- Alvo de Misseis Magicos acessivel na propria linha da magia.
- Contador do registro distingue eventos visiveis de registros carregados.

## Arte e conteudo - ainda nao concluidos

- Inventariar 255 entradas do bestiario, itens do indice e da sessao, NPCs e magias.
- Vincular referencias originais do Vault a cada entidade; evitar referencia generica.
- Gerar variantes novas com Flux; nao substituir arquivos originais silenciosamente.
- Conferir identidade, anatomia, legibilidade em celular e licencas das referencias.
- Preparar imagem do esqueleto de madeira de Morthak e visual reutilizavel de reanimacao.
- Consolidar transcricao jogada da sessao 6, separando fatos, meta e decisoes.
- Companion conserva estado operacional; Vault conserva lore e registro consolidado.
- Importacao/exportacao deve ter fontes, idempotencia e conflitos explicitos.
- Nao publicar notas privadas, tokens, transcricoes brutas ou segredos no GitHub.

## Evidencia da inspeccao

A sessao 6 existe no banco e esta concluida, mas resumo e cronica publicos sao nulos.
O pacote de sessao 6 do Vault ainda diz preparacao nao jogada.
O ledger tem 1757 eventos no banco observado; o contador anterior nao representava esse total.
O pipeline atual aceita capas de cena/sessao, alguns itens especiais e pocoes,
nao todo o bestiario/NPCs/magias. Essa extensao permanece pendente.

Flux enviava referencias por multipart, mas as descartava silenciosamente em erro 400.
Essa degradacao foi removida; referencia invalida deve bloquear, nao gerar arte sem identidade.

## Entregas adicionais desta rodada

- `scripts/audit_art_inventory.py`: inventario read-only com hashes de referencias,
  sem chamadas externas e sem exportar conteudo bruto das notas.
- Inventario local: `.observer-runtime/art-inventory-20261006.json` (434 entradas).
- Amostra Flux: `zz_media/ui/icons/drafts/morthak-wood-skeleton-v1.png`.
  Referencia de estilo: `zz_media/characters/morthak.jpg`; nao substitui o original.
  Prompt: esqueleto unico, ossos e reforcos de madeira, estilo fantasia escura,
  brilho necromantico verde discreto, corpo inteiro, sem roupas/cajado/texto/personagens extras.
  Amostra inspecionada, ainda nao vinculada aos pins existentes.
- Filtro CSS reutilizavel nos pins/ficha de criaturas reanimadas; nao altera a imagem.
- Fonte original da S6 copiada para `CAMPANHA/Fontes/Sessao_06_transcricao_original.txt`,
  com hash identico ao arquivo enviado e indice privado de Mestre no Vault.
- Nenhum resumo publico da S6 foi publicado sem consolidar a transcricao.

## Validacao final deste corte

- Backend: `.venv-observer/Scripts/python.exe -B -m unittest discover -s backend -p test_*.py`: 314/314 PASS.
- Frontend: `node --test tests/*.test.cjs`: 135/135 PASS.
- TypeScript: `npx --no-install tsc --noEmit`: PASS.
- Build: `npm run build`: PASS; aviso existente de chunks acima de 500 kB.
- `git diff --check -- .`: PASS.
- QA visual mobile/desktop e sincronizacao multicliente: ainda nao comprovados.
- Backend operacional nao reiniciado; sem commit/push.
- O numero antigo de 80/100 eventos nao permite concluir exclusao: havia filtros,
  limite de exibicao de 250 e janela de leitura do ledger. O banco conserva 1757
  eventos de auditoria; isso nao equivale ao numero de acontecimentos narrativos.
- A leitura do ledger continua limitada pela API; nao foi implementada paginacao
  completa de todo o historico nesta rodada.
