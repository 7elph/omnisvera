# Rotas de imagem

- Oficial (default): Cloudflare `flux-2-klein-9b`.
- Teste explícito: Cloudflare `flux-2-klein-4b`, sem fallback para não mascarar o teste.
- Fallback oficial: Space `black-forest-labs/FLUX.2-klein-9B`, ZeroGPU, modo Distilled (4 steps).

O fallback ocorre somente após cota diária confirmada, indisponibilidade de capacidade ou HTTP 5xx. Erros de autenticação, referências inválidas, 429 desconhecido e timeout não disparam outra geração. Não há terceiro provider nem fallback pago. O Space recebe o mesmo pedido e até quatro referências; não há repetição silenciosa sem imagens. Prompt upsampling/VLM fica desabilitado.

Cada job registra `context_json.generation`: modo solicitado, rota realmente usada e tentativa de fallback. A imagem anterior continua preservada e a nova versão exige aprovação do Mestre.

ZeroGPU tem fila e cota independente, não garantida. A renovação do Cloudflare às 00 UTC não prevê a disponibilidade do Hugging Face. Acesso anônimo pode sofrer limites mais baixos; opcionalmente configurar `OMNISVERA_HF_TOKEN` no ambiente do backend, com token de conta autorizada. Não grave token no repositório, prompt, job ou mensagem de chat. Nenhuma conta, assinatura ou cobrança é criada pelo Companion.

Timeout: até 180 segundos por rota (oficial + fallback até aproximadamente seis minutos). Após timeout remoto, a tarefa pode continuar no Space; não repetir automaticamente. Falhas preservam a imagem anterior. Somente downloads HTTPS do host fixo e endpoint de arquivos do Space são aceitos; referências usam nomes neutros e downloads têm limite de 20 MB.

## Verificação operacional inicial

O endpoint público foi conferido contra `/gradio_api/info` e o código oficial do Space. Duas chamadas sintéticas (com referência e controle somente texto) terminaram em `event:error` / `data:null`. O Space está `RUNNING`, mas usa `show_error=false`: a causa interna não foi publicada. Isso NÃO comprova cota esgotada nem autenticação obrigatória. A integração local é testável; geração real pelo fallback permanece não comprovada até o serviço voltar a responder ou fornecer diagnóstico.

Após o reinício autorizado, o backend e o túnel responderam HTTP 200; o hash do arquivo de tokens permaneceu idêntico. Um controle adicional via a fila Gradio (`queue/join` + `queue/data`), sem referência e sem prompt upsampling, entrou em `process_starts`, publicou progresso e terminou em `process_completed`, `success=false`, `output.error=RuntimeError`. Portanto a falha reproduzida ocorre na execução remota do Space, não no download do Companion. Logs internos retornaram HTTP 401: o traceback detalhado depende do proprietário. Relatos públicos correlatos: https://huggingface.co/spaces/black-forest-labs/FLUX.2-klein-9B/discussions/3 e /4. Não modificar nem reiniciar Space de terceiros.

## Diagnóstico posterior e correção local

A fila nativa revelou a recusa atual: `You have exceeded your ZeroGPU quota (85s requested vs. 73s left). Try again in 22:17:09. Authenticate with a Hugging Face token for more quota`. O decorator do Space exige reserva fixa de 85 segundos, mesmo que a imagem demore menos. Essa evidência explica a recusa atual, mas não estabelece a causa do RuntimeError anterior.

O adaptador passou a usar `queue/join` + `queue/data`, buscando o ID de `generate` no config público. Agora captura o erro real, exibindo somente campos seguros de reserva/saldo e tempo informado pelo provider, sem vazar respostas brutas ou tokens. O teste real do adaptador confirmou 85s exigidos/73s disponíveis e a renovação informada. Sem token configurado, a geração continua bloqueada pela quota remota; não declarar fallback funcional até obter imagem válida. Um único clone sem LoRA foi testado e também recusou; não foi ativado. O Space Dishku foi descartado por incorporar LoRA de estilo.
