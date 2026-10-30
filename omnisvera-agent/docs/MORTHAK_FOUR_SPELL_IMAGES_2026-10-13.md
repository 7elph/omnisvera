# Morthak — quatro imagens de magias

Imagens fornecidas pelo Mestre, copiadas sem edição para
`frontend/public/companion-assets/` e vinculadas pelo catálogo existente
`backend/app/data/spell_images.json`:

| Anexo | Magia | Arquivo |
| --- | --- | --- |
| 1000209132.jpg | Clonagem | morthak-clonagem.jpg |
| 1000209133.jpg | Magia da Morte | morthak-magia-da-morte.jpg |
| 1000209137.jpg | Toque Sombrio | morthak-toque-sombrio.jpg |
| 1000209136.jpg | Aterrorizar | morthak-aterrorizar.jpg |

O card usa ícone compacto de 27 px; clicar no nome abre a imagem maior
na descrição existente. O mesmo metadado alimenta os controles de conjuração.
Não foram alterados usos, dano, alcance, efeitos, inventário ou fichas persistidas.
As cópias foram verificadas por SHA-256. API operacional e quatro arquivos
públicos foram conferidos por leitura: vínculos corretos e conteúdo original.
O catálogo é lido dinamicamente; não foi necessário reiniciar o backend.

Arquivos de suporte: `backend/test_spell_images.py`,
`frontend/tests/morthak-new-spell-art-smoke.cjs`,
`backend/scripts/run_sheet_test.py` (inclui o smoke nos ensaios de quatro atores).
O smoke usa somente fixture temporária, verifica ícones, abertura/fechamento
das quatro imagens e ausência de overflow nas visões Mestre desktop/Jogador mobile.

Não houve commit, push, geração de imagens ou alteração no Vault.
Celulares físicos e redes de jogadores distintas não são certificados pelo smoke.

## Evidências e limites

- Frontend: 264 testes PASS; typecheck e build PASS.
- Backend completo após correção da expectativa do novo teste: 734 testes PASS.
  Permanecem avisos legados de conexões SQLite, depreciação `on_event` e
  chunk grande do Vite; nenhum foi apresentado como falha funcional resolvida.
- Regressão de imagens: 11 testes PASS. A primeira versão do novo teste usava
  uma descrição fictícia, mas o enriquecimento existente normaliza descrições
  aprovadas; a expectativa foi corrigida para a descrição canônica existente.
- Smoke específico: PASS nas oito combinações de quatro magias × duas visões
  (Mestre 1440 px, Morthak 390 px); capturas revisadas, nenhuma ação de jogo.
  Evidência privada: `TEMP/omni-morthak-art-visual-3ejh58ot/ui.private.log`.
- Ensaio MCP ampliado `test-2f1d664ee69e4585aee76a7cd60c29a0`: FAIL no script
  de combate físico, por `socket hang up` em uma leitura da ficha na fixture.
  A aceitação básica da ficha passou. Esse resultado não certifica combate;
  não foi alterada uma regra de jogo para contornar a falha de conexão.
- Imagens confirmadas na API operacional e no endereço público por leitura,
  com comparação de hash, independentemente da fixture do ensaio ampliado.
