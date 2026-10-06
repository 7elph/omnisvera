# Raziel — contrato aprovado de Mordida e Regeneração

Decisão de Sage nesta conversa, 2026-10-05. Este documento não altera o Vault nem concede progressão.

- Mordida é ataque próprio corpo a corpo: alvo explícito, acerto contra CA e 1d4 de dano. Usa bônus corpo a corpo sem bônus da arma equipada; consome o orçamento normal de ataque. Não custa sangue.
- Dano e cura são confirmados atomicamente; cura limitada aos PV efetivamente retirados do alvo (não PV temporários) e aos PV máximos de Raziel. Errar não cura. Repetir confirmação não reaplica efeitos.
- Regeneração usa uma ação completa e 1 ponto da reserva existente de 5 para curar 1d4, até o máximo. Não ocorre automaticamente, não recupera sangue e não levanta Raziel de 0 PV.
- Sentido do Sangue permanece bloqueado. A tabela racial de progressão continua uma referência em revisão; aumentos futuros dos dados não foram habilitados por este corte.
- Distância física corpo a corpo e presença de sangue em espécies exigem os limites do mapa/decisão de Mestre existentes: esta mudança não implementa alcance automático nem um catálogo de fisiologia.

Validação usa SQLite e perfis descartáveis. Sem alteração de PV, recursos, Vault ou combate operacional.

## Verificação deste corte

- Backend: `.venv-observer\Scripts\python.exe -B -m unittest discover -s backend -p 'test_*.py'` — 288/288 PASS.
- Frontend: `node --test tests/*.test.cjs` — 113/113 PASS.
- TypeScript: `npx --no-install tsc --noEmit` — PASS.
- Build Vite em diretório temporário: PASS; não substituiu `frontend/dist` operacional.
- `git diff --check -- backend frontend docs` — PASS.
- Catálogo efetivo de Raziel: alvo obrigatório da Mordida e Regeneração estruturada com reserva máxima 5 — PASS.

Avisos remanescentes: ResourceWarning de conexões SQLite nos testes e bundles Vite grandes. Nenhum foi tratado como falha nem ocultado.

## Ativação e limites

Código e testes concluídos. Ativado em 2026-10-05 após solicitação explícita de Sage: build em `frontend/dist` e reinício do backend pela configuração de `start_companion.ps1 -NoBuild -NoRebuild`, preservando o túnel existente. Health local `ok`; HTTPS público 200 com bundle `index-BoIFtlDV.js`; consulta autenticada como Raziel confirma Mordida com alvo obrigatório, Regeneração estruturada e Sentido do Sangue bloqueado.

O catálogo complementar `backend/app/data/raziel_vampire_powers.json` só é carregado pelo novo código, evitando que o processo antigo anuncie o contrato novo antes do reinício.

Atualização aprovada por Sage: Forma da Noite com 3 usos diários, dropdown de corvo/coruja/morcego, escolha registrada no evento e rejeição de animal inválido/usos esgotados. O consumo existente não converte automaticamente a ficha em ficha animal; adjudicação permanece com o Mestre. Regeneração não exibe contador duplicado, mantendo custo e validação na reserva compartilhada. Descrições comuns de habilidades abrem diálogo rolável via portal, evitando recorte por painéis ancestrais.

Checks desta atualização: backend 289/289, frontend 115/115, TypeScript, build e diff check PASS. Sem push. Sem ensaio visual real no celular; essa aceitação permanece pendente.

Ainda requer comprovação visual em celular e mesa multicliente. Nenhuma progressão futura foi habilitada; nenhuma alteração no banco real foi feita. Sem commit ou push.
