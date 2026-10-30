# Fronteira de runtime do conector de ensaios

O servidor MCP continua usando `.venv-observer`, com o SDK já fixado.
O ensaio de aplicação passa a usar exclusivamente o intérprete local existente
`backend/.venv/Scripts/python.exe` no Windows ou `backend/.venv/bin/python`
nos demais sistemas. O runner, a fixture HTTP e os adaptadores herdam esse
runtime nativo, em vez do intérprete do SDK observador.

O caminho é interno e fixo: não aceita entrada do agente, não procura no PATH,
não instala dependências e não troca a configuração/modelo do OpenCode.
Sem esse arquivo, o recibo termina em `ERROR/INCONCLUSIVE`, com
`RUNTIME_UNAVAILABLE`, antes de criar processo. Repetir o mesmo `request_id`
recupera o recibo; após corrigir a dependência, um novo ensaio exige novo ID.

Motivo: o CLI com o ambiente nativo concluiu o ensaio, enquanto a tentativa MCP
instrumentada `test-39e42396099c406787932f871e869a19` criou um processo de fixture
que permaneceu vivo por 45 segundos sem alcançar sequer `cf01_module_entry`.
A causa Windows/host subjacente **não está demonstrada**. Alinhar o runtime é
uma fronteira arquitetural explícita, não uma declaração de causa raiz resolvida.

Os logs privados existentes registram checkpoints `FIXTURE_STARTUP` com etapa,
PID, PID pai, caminho do intérprete, versão e liveness do filho. Não registram
ambiente, argumentos, tokens, banco, conteúdo das fichas ou resposta de health.
Importar os módulos pelo MCP não imprime esses checkpoints no transporte stdio.

Não foram alterados timeouts, limite de um ensaio por checkout, lease,
cancelamento da árvore própria, critérios de relatório ou certificação. Recibos
inconclusivos anteriores permanecem inconclusivos. A ativação e o próximo
ensaio MCP devem ser coordenados pelo agente principal; testes unitários
mockados não comprovam que o problema de startup desapareceu.

Verificação real posterior: `test-58308541da1041419fe00ad71fc4f4e3` também
terminou ERROR/INCONCLUSIVE no startup. Fronteira de runtime sozinha **não
resolveu** o caminho OpenCode. Detalhes e próximos limites de autorização em
`RESUME_COMPANION_2026-10-16.md`; recibos antigos não foram reclassificados.

Após autorização para continuar, limpeza oficial do host retornou sucesso e
os conectores voltaram. Windows negou o encerramento do PID OpenCode; não houve
restart real nem tentativa de contornar essa negativa. O ensaio posterior
`test-44d7fb0eb84c4c9baa803d8c194fb5f7` falhou no mesmo startup. Reabrir a aba
web não reinicia o host; falta um fechamento/reabertura real pelo usuário.
