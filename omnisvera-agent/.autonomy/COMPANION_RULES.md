# Contrato de autonomia

Leia AGENTS.md. Esta autorização específica permite uma worktree isolada para
o ciclo, sem substituir ou modificar o checkout funcional original.

## GREEN — pode implementar uma melhoria comprovada

CSS/responsividade, acessibilidade, mensagens, estados de UI, bug localizado,
teste e duplicação trivial, somente preservando comportamento e contratos.
Evidência de falha e verificação objetiva são obrigatórias. TODO, tamanho de
arquivo e opinião estética são pistas, não bugs comprovados.
Limite de revisão: 5 arquivos de produto e 200 linhas adicionadas+removidas.
Acima disso, parar e propor; nunca dividir uma mudança para contornar o limite.

## YELLOW — proposta somente

Endpoint, API, fluxo relevante, componente estrutural, persistência ou refactor
significativo. Não implementar. Explicar evidência, impacto e alternativa menor.

## RED — proibido autonomamente

Auth, permissões Mestre/Jogador (inclusive visibilidade no frontend), secrets,
migrations, bancos operacionais, deleções, regras centrais, MCP/Core, Vault,
Godot, arquitetura ampla e qualquer mudança difícil de reverter.
Não alterar AGENTS.md, esta política, o inspector ou os próprios limites.
Não ler credenciais, .env, tokens, configurações privadas, logs crus ou bancos.
Não iniciar providers, APIs pagas, imagens, predições, serviços ou túneis.

## Gates

1. Checkout dirty: STOP. Não stash/reset/clean, copiar alterações, commitar
   trabalho alheio nem partir de HEAD antigo sem autorização humana explícita.
2. Inspeção e verificação devem corresponder ao mesmo HEAD e fingerprint atual.
3. Checks ausentes, timeout ou dependência ausente: INCONCLUSIVE, nunca PASS.
4. Só depois de baseline limpa e verde, criar branch `codex/companion-<cycle_id>`
   em worktree irmã nova (recusar caminho existente). Não fazer checkout no original.
5. Selecionar no máximo UMA melhoria. Sem evidência GREEN: NO_CHANGE e parar.
6. Sem rede externa necessária ao ciclo; não instalar dependências silenciosamente.
7. Sem commit, push, PR remoto, merge ou agendamento automáticos. Entregar diff
   local, relatório e texto de PR. A publicação requer autorização posterior.
8. Diff acima do limite, regressão não relacionada ou baixa confiança: revisão
   Codex, sem invocá-lo automaticamente. RED: Sage.

Estes são limites processuais, não sandbox de segurança. Um OpenCode com shell
amplo pode tecnicamente violá-los. Não vender esta v0.1 como execução confinada.
