# Operação manual — sem agente iniciado automaticamente

Na pasta canônica, usando o ambiente já disponível:

```powershell
.\.venv-observer\Scripts\python.exe -B scripts/companion_maintainer.py inspect
.\.venv-observer\Scripts\python.exe -B scripts/companion_maintainer.py verify
.\.venv-observer\Scripts\python.exe -B scripts/companion_maintainer.py inspect
```

`inspect` lê Git e arquivos-fonte permitidos, grava somente o relatório em
`.autonomy/runtime/inspection.json`. Não roda checks, não lê logs/DB/.env,
não instala nada nem inicia OpenCode. TODO/FIXME gera apenas localização,
nunca linha de código. `issues=[]` não significa ausência de bugs.

`verify` é separado e executa código de teste/build do projeto confiável.
Não é uma sandbox: não impede que um teste mal escrito tenha efeitos.
Usa Python -B, captura stdout/stderr sem persistir texto, verifica fingerprint
do produto antes/depois e produz build em TemporaryDirectory, não em dist.
O fingerprint cobre código e configs principais; não prova ausência de
qualquer efeito externo. Não roda automaticamente contra código não revisado.
Os comandos completos são definidos em `commands()` no script.

Relatório retorna contagem/exit code/status; falhas precisam de reprodução
local focada para evidência detalhada, sem publicar logs crus. Dependências
ausentes e timeout são INCONCLUSIVE. Não fazer install automático.

Depois de baseline limpa, verificação atual verde e ambiente da worktree
preparado, o operador abre uma sessão nova OpenCode nessa worktree e entrega
OPENCODE_MAINTAINER_PROMPT.md. Nenhum ciclo foi autorizado para esta preparação.
O launcher web existente não equivale a isolamento.

Histórico futuro:
`python scripts/companion_maintainer.py record <relatorio-sanitizado.json>`.
Validação de formato e detecção de alguns padrões de credenciais não são um
scanner completo de secrets. Revisão humana continua necessária antes de
publicar qualquer relatório. Arquivos JSON locais ficam fora do Git.

Antes de qualquer commit autorizado, stage somente estes arquivos explícitos.
Não incluir alterações preexistentes do monorepo nem runtime/history.
