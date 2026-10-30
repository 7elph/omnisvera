# Imagens e Forma da Noite — 07/10/2026

Cinco anexos do usuário foram carregados pelo endpoint GM existente de ícones, categoria `map`, sem reprocessamento. Arquivos no Vault:

- Fungo: `zz_media/ui/icons/uploads/fungo_bc5c66fd73.jpg`
- Dragão: `zz_media/ui/icons/uploads/dragao_0fc8c61089.jpg`
- Coruja: `zz_media/ui/icons/uploads/raziel_coruja_969cca62e9.jpg`
- Morcego: `zz_media/ui/icons/uploads/raziel_morcego_82a3c8733e.jpg`
- Corvo: `zz_media/ui/icons/uploads/raziel_corvo_ae9c2df01e.jpg`

Todas retornaram HTTP 200 e bytes idênticos aos anexos. Vault: `Bestiary/Fungo.md`, `Bestiary/Dragão.md`, `Bestiary/Formas da Noite de Raziel.md`, verificadas no índice. Não foram inferidas estatísticas, identidades de dragões ou acontecimentos novos.

## Função backend

O consumo existente de `forma_da_noite` valida a escolha e um uso diário antes de persistir `animal_form` na mesma transação dos recursos. `list_workspace_tokens` projeta a imagem aprovada nos pins de personagem vinculados a Raziel. O campo original da imagem no banco não é substituído. Funciona em todos os mapas, inclusive pins criados depois do uso, e persiste após refresh. Outros pins e coordenadas não mudam.

`end_night_form` é exclusivo do controlador de Raziel/Mestre, remove a forma sem reembolsar recursos e registra evento; repetir após encerramento não muda o estado. A UI mostra a forma ativa e botão de retorno no padrão inline existente. Descanso padrão também encerra a substituição visual. Não foi automatizada a ficha animal, ataques, voo ou retorno por 0 PV neste corte: pedido limitado à imagem.

Arquivos de produto: `backend/app/night_form.py`, `character_play.py`, `session_workspace.py`, `schemas.py`; `frontend/src/api.ts`, `frontend/src/pages/SessionWorkspace.tsx`. Regressões: `backend/test_hemomante_techniques.py`. Arquivos com alterações anteriores tiveram essas alterações preservadas.

## Validação

- Backend completo: `.venv-observer\Scripts\python.exe -W ignore::ResourceWarning -m unittest discover -s backend -p "test_*.py"`: 378/378 PASS.
- Suite específica Hemomante: 28/28 PASS, incluindo imagens das três formas, persistência, coordenadas, pin de outro personagem, imagem original no banco, retorno sem reembolso, animal inválido e autorização.
- TypeScript: `npx --no-install tsc --noEmit` PASS.
- Build isolado: `npm run build -- --outDir C:\Users\delib\AppData\Local\Temp\raziel-night-form-20261007-build` PASS.
- Frontend completo: `node --test tests/*.test.cjs`: 145 PASS / 1 FAIL preexistente em `shared-attack-target.test.cjs`, regex de layout do card de Mísseis Mágicos. Não enfraquecido nem alterado.
- `git diff --check -- . ../Bestiary`: PASS, apenas avisos LF/CRLF.

Imagens/notas já disponíveis operacionalmente. Código de transformação **ainda não ativado no servidor operacional**: necessário publicar o build local e reiniciar o backend pelo launcher existente, sem mudar tokens. Nenhum commit/push/reinício foi realizado neste corte. Não se declara smoke test operacional ou multicliente da transformação.
