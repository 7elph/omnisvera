# Curadoria da IA no Omnisvera Companion

O painel **Curadoria da IA** transforma respostas reais do Companion em exemplos revisados para o futuro `Llama-3.2-Omnisvera-3B`. Ele não treina, baixa ou promove modelos.

## Ativação

A curadoria exige o token de mestre configurado no backend. Sem ele, os endpoints administrativos negam acesso.

```powershell
$env:OMNISVERA_MASTER_TOKEN="seu-token-local"
$env:OMNISVERA_TRAINING_CAPTURE_MODE="manual"
$env:OMNISVERA_UNREVIEWED_RETENTION_DAYS="30"
```

Modos de captura:

- `off`: desativa captura e curadoria de novas interações;
- `manual`: padrão; persiste somente após uma ação explícita do mestre;
- `master_session`: mantém metadados temporários das respostas do chat do mestre para revisão posterior, sem criar exemplos automaticamente.

Jogadores não recebem os controles e não têm acesso aos endpoints `/gm/training/*`.

## Avaliar uma resposta

No chat do mestre, abra **Avaliar resposta**:

- **Boa** cria um candidato pendente com a resposta atual como ponto de partida;
- **Corrigir e aprovar** abre o editor, valida e só então aprova;
- **Rejeitar** registra o motivo e exclui o exemplo do conjunto de treino;
- **Inventou** bloqueia a resposta atual como target positivo;
- **Vazou** remove o texto sensível do registro, marca incidente e impede aprovação;
- **Incompleta** abre caminho para completar a resposta ideal;
- **Artificial** preserva os fatos para uma reescrita mais natural;
- **Fonte incorreta** bloqueia aprovação até a fonte e os metadados serem revistos.

Nenhuma dessas ações inicia treinamento. **Pendentes não são usados no treinamento.**

## Revisar e aprovar

Abra a aba **Curadoria** no acesso de mestre. A fila permite filtrar por status, perfil e falha. No editor:

1. confira pergunta, modelo, recuperação e resposta exibida;
2. revise a resposta ideal;
3. confirme categoria e qualidade de 1 a 5;
4. corrija flags e marque cânone/segredo corretamente;
5. salve como pendente ou escolha **Validar e aprovar**.

Uma aprovação exige resposta ideal, qualidade, reviewer, schema válido e ausência de falhas bloqueantes. Exemplos player com segredo nunca podem ser aprovados.

## Armazenamento local

Os dados reais ficam em diretórios ignorados pelo Git:

```text
omnisvera-model/data/captured/companion_interactions.jsonl
omnisvera-model/data/candidates/companion_examples.jsonl
omnisvera-model/data/approved/companion_examples.jsonl
omnisvera-model/data/rejected/companion_examples.jsonl
omnisvera-model/data/raw/companion_curation_audit.jsonl
```

As gravações são atômicas e mantêm três backups locais rotativos (`.bak1` a `.bak3`). Para backup manual, pare o backend e copie `omnisvera-model/data/` para armazenamento privado. Não envie essa pasta ao Git.

Interações `unreviewed` expiram conforme `OMNISVERA_UNREVIEWED_RETENTION_DAYS`. Candidatos pendentes podem ser excluídos no painel. Exemplos aprovados não são apagados silenciosamente; exigem um fluxo de versão/auditoria.

## Cobertura e treinamento futuro

O painel mostra apenas aprovados no progresso até 1.000. Ao aprovar, o arquivo em `data/approved/` fica imediatamente disponível para o builder, mas o dataset de treino não é reconstruído automaticamente.

Para conferir a cobertura pela linha de comando:

```powershell
python -m omnisvera_model coverage-report
```

Chegar a 1.000 exemplos apenas libera a avaliação dos gates mínimos. Treino, exportação e promoção continuam exigindo comandos e aprovação separados.

## Desativar completamente

```powershell
$env:OMNISVERA_TRAINING_CAPTURE_MODE="off"
```

Reinicie o backend. Os dados existentes permanecem preservados localmente, mas nenhuma nova captura é aceita.
