# Trabalho de habilidades: Codex + OpenCode

Os dois agentes editam o mesmo Companion; não criar outro motor de regras.
Antes de cada lote, ler AGENTS.md, CURRENT_COMPANION_CODE.md e AI_TEST_TOOLS.md,
inspecionar o worktree e combinar arquivos distintos para evitar sobrescrita.

1. Escolher uma ação da ficha ativa, com fonte e regra aprovada. Descrever alvo,
   alcance, custo, duração, dano/JP, cancelamento e retry. Pendência de regra não
   pode virar escolha silenciosa de implementação.
2. Criar teste RED, conectar catálogo/card ao comando autoritativo existente e
   reutilizar ledger, realtime, orçamento de turno e seleção no grid.
3. Rodar checks e `companion-tests` com os quatro atores e `ui: true` na fixture.
   Conferir recibo, consequências, permissões e capturas. PASS seletivo não
   certifica toda a ficha nem redes distintas.
4. Entregar arquivos, testes e limites; separar código testado de runtime ativado.
   Não publicar, alterar fichas reais ou mudar regras por iniciativa do ensaio.

## REA como apoio, não como árbitro

Referência: https://github.com/morluto/rea/blob/main/docs/readme/README_pt-BR.md

Executado localmente `rea-agents@6.5.0`, CLI temporário via npm exec com
`--ignore-scripts`, sem setup global nem alteração de configuração dos agentes.
Análise estática de `api.ts`, `SessionWorkspace.tsx` e `MapCommerce.tsx`:
3 arquivos parseados, zero falhas de parse; 105 arquivos inventariados ficaram
fora da seleção. As 652 observações não são 652 bugs nem prova de runtime.
Relatório privado: `%TEMP%/omni-rea-companion-analysis.json`.

Comando reproduzível (diretório frontend analisado, nenhum bootstrap executado):

```powershell
npm exec --yes --ignore-scripts --package=rea-agents@6.5.0 -- rea analyze-javascript-application frontend/src --artifact-format directory --source-path api.ts --source-path pages/SessionWorkspace.tsx --source-path components/MapCommerce.tsx --analysis-timeout-ms 20000 --max-heap-mb 512 --max-semantic-nodes 4000 --max-semantic-nodes-per-file 1200 --format json
```

Usar para localizar chamadas e dependências; os contratos nativos, testes e
observação visual continuam sendo a evidência de funcionamento. Nenhuma mensagem
foi enviada ao OpenCode e nenhum modelo/plugin foi reconfigurado neste corte.
