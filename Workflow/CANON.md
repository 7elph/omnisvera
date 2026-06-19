---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Active
status: Active
tags:
  - workflow
  - canon
  - omnisvera
  - earthropo
---

# Cânone de Omnisvera

Este documento é o registro central de continuidade da campanha. Ele existe para impedir que nomes, datas e conceitos sejam alterados silenciosamente durante edições feitas por IA.

Quando uma nota entrar em conflito com este arquivo, o conflito deve ser apontado antes de qualquer correção em massa.

## Estado das informações

| Estado | Significado |
|:--|:--|
| **Confirmado** | Definido diretamente pelo autor. Não alterar sem uma nova decisão explícita. |
| **Cânone de trabalho** | Aceito provisoriamente a partir das notas atuais. Pode ser refinado sem mudar sua essência. |
| **Em aberto** | Existe informação conflitante ou ainda não definida. Não escolher uma versão automaticamente. |
| **Fonte de template** | Material preservado por sua estrutura, formatação ou funcionamento técnico; não constitui cânone narrativo. |

## Confirmado

### Estrutura do cenário

- **Omnisvera** é o universo.
- **Earthropo** é o cenário principal onde a campanha acontece.
- **Nimalia** é a cidade central da campanha.
- O sistema utilizado é **Old Dragon 2E**.

### Núcleo de personagens

Existem três personagens de jogador nesta campanha:

1. [[Vezemir]]
2. [[Varkh Nimalis]]
3. [[Raziel]]

Nenhum personagem importado de Disgraceland deve ser apresentado como membro da campanha sem decisão explícita do autor.

### Disgraceland

Disgraceland não é um legado a ser descartado. É uma **fonte de templates** para Omnisvera.

Podem ser reaproveitados:

- estruturas de páginas;
- propriedades de frontmatter;
- layouts, callouts e consultas;
- snippets CSS;
- configurações e padrões de plugins;
- organização visual;
- ideias que forem deliberadamente adaptadas.

Não são automaticamente cânone de Omnisvera:

- nomes de personagens;
- lugares e facções;
- datas e calendários;
- acontecimentos;
- relações políticas;
- textos narrativos;
- marcadores de mapa;
- tags específicas de Disgraceland.

Um elemento de Disgraceland só passa a ser cânone quando for convertido conscientemente e registrado neste documento ou em uma nota consolidada.

## Cânone de trabalho

Estas informações formam a direção atual, mas ainda podem receber ajustes:

### Premissa

O [[Eclipse de Obsidiana]] criou ou revelou o Véu Cinzento, uma ruptura ligada a memórias perdidas, ruínas impossíveis e aos Criadores.

Earthropo vive uma estabilidade aparente. Coroa, religião, comércio e forças clandestinas disputam artefatos e informações enquanto o Véu começa a mudar.

### Vezemir

- Conhecido como **O Bastardo de Ferro**.
- É um guerreiro de origem humana e élfica.
- Foi criado por [[Elarion Vaelthor]].
- Carrega [[Grisalma]], [[Mulhara de Dorn]] e [[O Medalhão dos Guardiões do Véu Cinzento]].
- Busca o dragão de colar dourado ligado à morte de [[Mira Valen]].
- Sua origem e sua magia possuem relação ainda desconhecida com os Guardiões do Véu Cinzento.

### Varkh Nimalis

- Conhecido como **O Corvo da Maré Baixa**.
- É um kenku, ladrão e alquimista de rua.
- Foi treinado por Mestre Odran Veyl no Frasco Afogado.
- Investiga remédios falsos produzidos com o símbolo ou os métodos de Odran.
- Seu arco envolve identidade, voz, reputação e honra entre pessoas marginalizadas.

### Raziel

- Conhecido como **O Espectro da Névoa de Sangue**.
- É um personagem de jogador e um dos três protagonistas da campanha.
- É um vampiro ligado ao Clã Sanguinallis.
- Utiliza hemomancia e as Adagas de Espectro Fantasma.
- Foi traído e aprisionado por aproximadamente trezentos anos.
- Sua trajetória atual é movida por vingança contra Kaelen, Vandor e Lorde Malakar.
- A forma como sua história se encontra com Vezemir e Varkh ainda precisa ser definida.

### Ponto de encontro sugerido

O gancho mais desenvolvido nas notas atuais é:

1. um morto aparece carregando uma moeda de metal impossível;
2. uma autoridade religiosa tenta confiscar o corpo e os artefatos;
3. Varkh reconhece uma técnica alquímica ligada ao caso;
4. uma relíquia de Vezemir reage ao metal;
5. a investigação aponta para os Criadores ou para o Véu;
6. a entrada de Raziel nesse acontecimento ainda deve ser criada.

Esse gancho é uma proposta de trabalho, não uma sessão definitivamente aprovada.

## Decisões em aberto

Estas questões não devem ser resolvidas por inferência:

| Tema | Conflito atual |
|:--|:--|
| Natureza de Earthropo | Reino, continente ou ambos aparecem em notas diferentes. |
| Natureza de Nimalia | Cidade, capital e reino aparecem como conceitos sobrepostos. |
| Data atual | A linha do tempo usa 2100; o Calendarium e páginas importadas usam 2186. |
| Calendário | A nota `CALENDAR.md` e a configuração do Calendarium usam nomes diferentes. |
| Monarca | Augustus Terra Decimus e Alaric Valdris aparecem como governantes. |
| Religião dominante | Igreja das Chamas e Igreja das Sete Chamas aparecem como nomes concorrentes. |
| Geografia | Algumas regiões ainda usam nomes ou relações herdadas de versões anteriores. |
| Primeiro capítulo | O arquivo atual ainda contém a trama e a data de Disgraceland. |

## Hierarquia de fontes

Ao decidir qual informação prevalece, usar esta ordem:

1. decisão explícita mais recente do autor;
2. este documento;
3. notas consolidadas dos três personagens;
4. `EARTHROPO/EARTHROPO.md`, `TIMELINE.md` e `Workflow/OUTLINES.md`;
5. demais notas de Omnisvera;
6. conteúdo de Disgraceland, apenas como fonte de template.

## Regras para edições seguras

Antes de modificar uma nota:

1. Ler a nota inteira.
2. Verificar backlinks, embeds, consultas Dataview/DataCards e referências de mídia.
3. Identificar quais partes são conteúdo e quais são estrutura de template.
4. Preservar o frontmatter sempre que a tarefa não exigir sua alteração.
5. Alterar uma categoria de conteúdo por vez.
6. Validar o YAML e os wikilinks depois da edição.
7. Conferir o resultado no Obsidian quando a mudança envolver plugins ou CSS.
8. Criar um commit pequeno e descritivo.

### Proteção do frontmatter

- Não remover propriedades desconhecidas.
- Tratar propriedades como `NoteIcon` como parte potencial da taxonomia visual; não substituir seus valores por interpretação semântica.
- Não converter listas em texto simples ou texto simples em listas sem necessidade.
- Não mudar nomes, capitalização ou ordem de propriedades apenas por preferência estética.
- Manter wikilinks entre aspas quando já estiverem entre aspas.
- Não executar normalização em massa de YAML sem uma cópia de segurança e validação.
- Se uma propriedade estiver errada, corrigir somente essa propriedade.

### Proteção dos templates

- Não apagar snippets, plugins, configurações, mídias ou páginas de Disgraceland apenas porque contêm nomes antigos.
- Primeiro criar uma versão funcional equivalente para Omnisvera.
- Somente depois avaliar se o material substituído ainda precisa permanecer no vault.
- Arquivos de template devem ser separados de arquivos de cânone quando a migração estiver madura o suficiente.

## Método de trabalho

Cada etapa de consolidação seguirá este ciclo:

1. escolher uma área pequena;
2. mapear inconsistências;
3. apresentar decisões narrativas reais ao autor;
4. aplicar apenas as decisões confirmadas;
5. validar o Obsidian;
6. registrar a mudança no Git.

O objetivo não é apagar rapidamente os vestígios de Disgraceland. É transformar o vault gradualmente sem perder a estrutura que já funciona.
