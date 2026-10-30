# Hemomancia — gatilhos e bordas das passivas

Regressão isolada em 20/10. Não altera regras aprovadas nem dados operacionais.

## Resultado

Execução delegada à conversa existente do OpenCode, sem mudar modelo/conectores.
Comandos sequenciais, sem outro ensaio pesado simultâneo:

- Backend, em `backend/`: `.venv/Scripts/python.exe -m unittest test_hemomancy_weapons -v`.
  **44 testes OK**, exit 0; 41,112 s no unittest (47,281 s incluindo lançamento).
- Frontend, em `frontend/`: `node --test tests/hemomancy-weapons.test.cjs tests/raziel-sections.test.cjs`.
  **9 PASS**, exit 0; 0,969 s no runner (1,449 s incluindo lançamento).

Há avisos existentes de depreciação Starlette/httpx e conexões SQLite não
fechadas coletadas pelo teardown. Não são falhas de asserção; permanecem dívida
de teste. O PowerShell formatou stderr como NativeCommandError, mas o comando
terminou com `OK` e exit 0.

## Cinco regressões novas

1. Revanche só dispara se os dois pontos de CA do escudo evitarem o acerto:
   abaixo da CA original, acerto normal, 1 natural, 20 natural e outro alvo
   não geram carga.
2. Erro consome Exposto/Revanche na confirmação, sem rolar dano extra;
   repetir a confirmação não gasta sangue novamente.
3. Ferroada concede um único d6 com Exposto, com sangramento ou com ambos;
   o bônus plano de Exposto continua separado.
4. Acerto de Marreta contra imunidade física não causa dano nem deixa Exposto.
5. Reaplicar Ceifa renova um sangramento, sem acumular; dois inícios de turno
   causam dois ticks no ledger, e retry do avanço não duplica dano.

Todos passaram na primeira execução. Não houve RED de defeito do produto nem
patch de mecânica: estes casos reforçam a cobertura do comportamento existente.
As mutações de preparação usam exclusivamente os bancos temporários dos testes.

## Cobertura existente também repetida

| Passiva | Prova backend no módulo |
| --- | --- |
| Mira Predatória | Crítico de 19 que acerta duplica só dados base; erro não rola bônus; modificador plano não duplica |
| Carrasco | Limiar de 25% usa PV anteriores ao golpe; finalização só após morte |
| Trauma Profundo | Marreta aplica Exposto; ataque seguinte consome; imunidade não gera efeito |
| Revanche Rubra | Ataque recebido nativo gera carga; ataque hemomântico consome; bordas e erro cobertos |
| Ferroada Arterial | Exposto/sangramento habilitam um d6, sem duplicar quando combinados |

Também repetidos custo, autorização, alcance/revalidação, concorrência, retry,
expiração do escudo, limpeza no descanso/fim e separação por mapa.

## Limites e arquivos

Somente `backend/test_hemomancy_weapons.py` e documentação mudaram nesta etapa.
Nenhuma alteração de código de aplicação, frontend ou ficha; sem restart,
staging, commit ou push. O lote nativo UI anterior permanece separado em
`HEMOMANCY_UI_CHECK_2026-10-20.md`: não se injeta esta evidência de unittest no
recibo MCP nem se marca certificação integral como pronta.

Sem ensaio visual novo dos gatilhos aleatórios, celular físico ou redes distintas.
Discover completo/typecheck/build não repetidos: etapa restrita a testes e docs;
havia cerca de 270 MB de RAM livre, e nenhum artefato de aplicação foi alterado.
Próximo fechamento: caminhos UI ainda sem prova, demais poderes vampíricos e
ensaio Mestre/jogadores em redes distintas, sem reabastecer produção para QA.
