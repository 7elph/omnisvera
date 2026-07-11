# Omnisvera Companion — Comparação da IA Fundamentada

## Escopo

Teste sanitizado com 15 perguntas em modo jogador. Nenhuma nota do vault foi alterada e nenhum conteúdo de mestre foi registrado neste relatório.

## Antes e depois

| Métrica | Antes | Depois |
|---|---:|---:|
| Perguntas | 15 | 15 |
| Tempo médio | 10,767 s | 3,436 s |
| Tempo máximo | 26,982 s | 4,747 s |
| Falhas ou insuficiências | 5 | 2 |
| Possíveis invenções detectadas | 0 | 0 |
| Possíveis vazamentos detectados | 0 | 0 |

As duas insuficiências restantes são corretas: não há conteúdo público suficiente sobre o interior da Biblioteca Real nem evidência de um imperador secreto de Nimalia.

## Modelos locais avaliados

| Modelo | Resultado resumido | Decisão |
|---|---|---|
| omnisvera-fast:latest | Melhor latência, mas o JSON bruto ainda pode inventar ou fugir do contrato | Selecionado com validação obrigatória no backend |
| qwen3:4b | Não concluiu o contrato dentro de aproximadamente 50–55 s | Mantido opcional para testes profundos |
| phi3:latest | Produziu JSON sintaticamente válido em parte dos casos, mas fora do contrato | Não selecionado |
| qwen2:1.5b | Rápido em perguntas curtas, porém inventou atributos e suspeitos | Não selecionado |

## Mudanças de segurança factual

- fatos exigem path recuperado e evidência literal existente no trecho;
- fatos com evidência ausente ou não relacionada são descartados;
- teorias só preservam fontes recuperadas;
- respostas com afirmações fora dos fatos e teorias validados são reconstruídas;
- consultas sem evidência retornam insuficiência, sem completar com fantasia genérica;
- conteúdo técnico, templates e auditorias ficam fora do contexto normal;
- modo jogador continua filtrado antes da recuperação e antes da resposta.

## Perfil recomendado

O modo fast é o padrão para este notebook. Ele usa entidades determinísticas, listas estruturadas e extração literal fundamentada. O modo grounded permanece disponível para experimentar um modelo de qualidade configurável, sempre submetido à mesma validação de evidência.
