# Memória Comportamental — Guia do Sage

## O que mudou

Os exemplos aprovados na Curadoria da IA agora podem influenciar imediatamente a forma das respostas do Companion. Isso não é treinamento de modelo: nenhum peso foi alterado e o `qwen2:1.5b` continua ativo.

O Vault e o RAG permanecem como únicas fontes factuais. A memória comportamental orienta apenas tom, estrutura, prudência, comprimento, separação entre fato e teoria e tratamento natural de informação ausente.

## Fluxo diário

1. Use o chat normalmente no modo Mestre.
2. Com `OMNISVERA_TRAINING_CAPTURE_MODE=master_session`, a interação aparece como pendente na Curadoria da IA.
3. Revise a resposta ideal e os metadados sugeridos.
4. Aprove individualmente ou selecione vários itens seguros para aprovação em lote.
5. Uma aprovação invalida o índice em memória; a próxima resposta já pode usar o novo padrão, sem reiniciar o backend.

Conversas de jogadores não são capturadas automaticamente. Nada é aprovado automaticamente.

## Aprovação em lote

Somente pendentes válidos, sem segredo, vazamento, invenção, fonte incorreta, duplicata crítica e com qualidade mínima entram no lote. O painel mostra os bloqueios antes de qualquer escrita.

Para concluir, marque que revisou visualmente os itens e digite `APROVAR LOTE`. Cada aprovação produz seu próprio evento de auditoria.

## Como a sanitização funciona

Uma resposta aprovada não é copiada para o prompt. O sistema cria uma projeção como:

- padrão da pergunta;
- estrutura da resposta;
- tom;
- classe de comprimento;
- política de incerteza;
- política de fato versus teoria;
- demonstração genérica com marcadores como `[PERSONAGEM]`, `[LOCAL]` e `[ENTIDADE]`.

Nomes próprios, caminhos, links, fontes e fatos canônicos não fazem parte dessa projeção. O índice comportamental é separado do índice factual do Vault e nunca aparece em `notes_used`.

## Segurança

- player usa somente exemplos aprovados player-safe;
- Mestre pode usar padrões GM ou player compatíveis;
- pendentes, rejeitados, segredos, vazamentos e invenções não entram;
- persona incompatível não entra;
- exemplo comportamental nunca concede acesso a uma nota;
- o grounded validator continua rejeitando afirmações sem apoio no contexto factual.

## Configuração

```powershell
$env:OMNISVERA_TRAINING_CAPTURE_MODE="master_session" # off | manual | master_session
$env:OMNISVERA_BEHAVIOR_MEMORY_ENABLED="true"
$env:OMNISVERA_BEHAVIOR_MEMORY_MODE="sanitized"       # off | metadata_only | sanitized | raw_safe
$env:OMNISVERA_BEHAVIOR_MEMORY_AB_MODE="behavioral"   # baseline | behavioral
$env:OMNISVERA_BEHAVIOR_MEMORY_TOP_K="3"
$env:OMNISVERA_BEHAVIOR_MEMORY_MIN_SCORE="0.32"
```

`raw_safe` permanece desaconselhado e desativado por padrão. Para rollback imediato:

```powershell
$env:OMNISVERA_BEHAVIOR_MEMORY_ENABLED="false"
```

O chat volta ao RAG factual normal sem perder os exemplos aprovados.

## Marcos

| Aprovados | Classificação | Próxima ação permitida |
|---:|---|---|
| 25 | smoke | testar dataset e pipeline |
| 50 | experimental | LoRA pequeno experimental no Colab |
| 100 | alpha benchmark | benchmark experimental mais amplo |
| 250 | candidate alpha | avaliar candidato alpha |
| 500 | candidate beta | avaliar candidato beta |
| 1000 | production candidate | avaliar gates de treinamento de produção |

Os marcos não treinam nem promovem nada automaticamente. O gate de produção continua em 1.000 exemplos aprovados e validados.

## Comparação A/B

Use `OMNISVERA_BEHAVIOR_MEMORY_AB_MODE=baseline` para medir o chat sem influência comportamental e `behavioral` para ativá-la. Compare sempre factualidade, naturalidade, prudência, latência e vazamentos usando as mesmas perguntas.

## Estado correto

- influência comportamental: pode estar ativa;
- modelo treinado: não;
- Vault: fonte factual;
- aprovação: sempre humana;
- treino de produção: bloqueado até os gates serem atendidos.
