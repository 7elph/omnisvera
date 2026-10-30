# Oficina IA — medições iniciais e limites

Inspeção de 20/10/2026, sem gerar imagens, alterar fichas ou publicar conteúdo.
Estas medições não certificam disponibilidade futura nem a oficina pronta.

## Fontes e trabalho existente

- Sete sessões concluídas no cadastro. Referências de transcrição preenchidas
  nas sessões 1–4; 5–7 tinham lista vazia, apesar das fontes existirem em disco.
- Localizadas as sete transcrições originais por vínculos explícitos. Os hashes
  das quatro referências já cadastradas conferem. Índice privado criado em
  `.autonomy/runtime/ai-workshop-source-index.json`; não alterou o banco.
- Assets no banco inspecionado: 109 queued, 6 awaiting_approval, 6 failed,
  16 approved, 5 ignored, 1 ready. Isso não prova qualidade das saídas.
- A fila deve priorizar lacunas desses cadastros antes de criar variantes.
- Planejamento de texto: 276 janelas finitas de até 6.000 caracteres, cobrindo
  o conteúdo completo (sessões 7 a 1: 34/33/32/49/49/31/48). Nenhuma janela foi
  enviada a modelo nesta inspeção. Não equivale a análise já realizada.
- As 276 tarefas foram posteriormente enfileiradas pelo comando explícito
  `ai_workshop_seed_sources.py --enqueue` na fila **privada**
  `.autonomy/runtime/ai-workshop.sqlite3`; worker parado, zero gerações. SHA-256
  do banco operacional idêntico antes/depois. Replay validado em fixture.

## Tempos observados

| Canal | Amostra | Média | p50 | p95 | O que foi medido |
| --- | --- | --- | --- | --- | --- |
| OpenCode / DeepSeek V4.1 Flash Free | 14 etapas concluídas | 25,68 s | 14,898 s | 60,848 s | Etapas de agente **incluindo ferramentas**; não latência pura de inferência nem duração da tarefa completa |
| Ollama | 0 gerações | não medido | — | — | Porta 11434 recusou conexão; início do processo foi bloqueado pela proteção do ambiente |
| FLUX / fallback | 0 gerações novas | não medido | — | — | Código/filas encontrados; não usar timestamps de criação como duração de geração |

As 14 etapas reportaram 221.207 tokens somando entrada/saída. Não é consumo
líquido faturado: contexto repetido/cache não foram separados. O modelo é a
opção gratuita; não extrapolar tokens/minuto a partir desse agregado.

Um lote anterior ficou aguardando permissão de leitura de caminho incorreto
(`Desktop/Items`, em vez de `Desktop/OMNISVERA/Items`). A permissão foi rejeitada
com indicação do caminho certo, sem conceder acesso amplo. `busy` não significa
inferência; separar blocked/waiting_permission da latência e não duplicar jobs.

## Limites documentados versus conta real

- Cloudflare: franquia gratuita documentada de 10.000 neurônios/dia, reset
  00:00 UTC (21h em São Paulo), limite geral text-to-image de 720 pedidos/minuto.
  Isso **não** comprova saldo desta conta nem autoriza saturar esse teto.
  Fila oficial usa 9B; 4B só em teste explícito. Fallback independente configurado
  não desbloqueia a cota Cloudflare e deve registrar seu próprio uso/erro.
- Ollama: preços/planos atuais descrevem créditos mensais e concorrência 1/3/10
  conforme plano. Plano, saldo e reset desta conta não foram verificados.
  Não presumir reset semanal, nem comprar créditos automaticamente.
- OpenCode: catálogo conectado confirmou DeepSeek V4.1 Flash Free como ativo,
  entrada/saída com custo zero. Não há cota restante/reset comprovado nesta
  inspeção. Respeitar resposta real do serviço e não trocar conta/modelo para
  contornar cota compartilhada.
- Não prometer zero ociosidade: quota, permissão, memória, fonte ausente e
  sessão ativa justificam espera. Trabalho elegível deve usar o próximo slot;
  trabalho duplicado ou vazio não melhora a preparação da mesa.

Fontes oficiais consultadas em 20/10:
[Cloudflare preços](https://developers.cloudflare.com/workers-ai/platform/pricing/),
[Cloudflare limites](https://developers.cloudflare.com/workers-ai/platform/limits/),
[Ollama preços/uso](https://ollama.com/pricing),
[OpenCode modelos](https://opencode.ai/v2/docs/console/models/).

## Runtime e ativação

- Companion 8787 e Ollama 11434 não responderam à checagem local.
- Pinokio/pterm não resolvido pelos caminhos/configuração/controle local/PATH;
  controle 42000 recusou conexão. Não alegar serviço Pinokio ativo.
- Conector remoto antigo de autonomia retornou erro de probe SSE/404; não
  reconfigurado. Não depende dele para validar o código local.
- RAM livre observada: 176 MB de 8.105 MB. Não lançar carga pesada adicional.
- Nenhum worker contínuo foi ativado nesta inspeção. Dois lotes delimitados de
  OpenCode foram autorizados separadamente; execução não equivale a conclusão.
- A primeira inspeção do worker expôs dois defeitos, encaminhados ao OpenCode:
  URI de SQLite com caminho relativo e falso combate ativo por 67 recibos de
  ataque pendentes antigos. O estado nativo lido era `encounter.active=false`,
  `battle_mode=true` residual e zero sessões ativas. Não foram limpos recibos
  nem estado para contornar o bloqueio; a admissão precisa ser corrigida/testada.

## Implementação e validação do índice

`ai_workshop_sources.py`: leitura SQLite `mode=ro`, raízes explícitas, hashes,
limite de tamanho, recusa de links/traversal, relatório só de metadados e blocos
de texto com hash/offset. Texto de transcrição é dado, nunca comando.
`ai_workshop_source_index.py`: exportação privada sem reparo silencioso do cadastro.

RED reproduzido antes da implementação; 17 testes focados PASS. A primeira
tentativa GREEN expôs conexão SQLite de teste sem close no Windows; corrigida
na fixture e repetida. Suíte completa/typecheck/build ainda não repetidos neste
corte; evitar concorrência com o smoke visual do outro lote e memória escassa.

Sem staging/commit/push; sem alteração de regras, níveis, estoque ou cânone.

## Limites da entrega em andamento

O núcleo/CLI/adaptadores foram delegados ao OpenCode e seguem em revisão.
Revisão parcial encontrou invocação CLI OpenCode sem isolamento de ferramentas
e adaptador de imagem que somente enfileira, sem executar FLUX. Essas versões
não foram ativadas; foi exigido bloqueio seguro ou correção com testes antes
da entrega. Não apresentar os três canais como ativos nem a oficina como pronta.
