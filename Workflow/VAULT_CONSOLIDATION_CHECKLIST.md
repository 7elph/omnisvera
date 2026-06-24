---
obsidianUIMode: preview
NoteIcon: outline
NoteStatus: Archived
status: Respondido
visibility: gm
tags:
  - workflow
  - consolidation
  - decisions
---

# CHECKLIST MESTRE — CONSOLIDAÇÃO DO VAULT

> [!important] Como preencher
> - Marque **uma opção** em cada decisão.
> - Quando não quiser escolher os detalhes, marque **DELEGAR AO CODEX**.
> - Se quiser preservar algo sem torná-lo cânone ainda, marque **MANTER EM ABERTO**.
> - Item sem resposta significa: **não mexer ainda**.
> - Nenhuma exclusão em massa deve começar antes da seção **0 — Segurança e autorização** estar preenchida.

## Legenda rápida

- **MANTER** — preservar conteúdo e estrutura.
- **REVISAR** — preservar a ideia, mas reescrever e consolidar.
- **REMOVER** — excluir do vault ativo depois do backup.
- **ARQUIVAR** — retirar do vault ativo, mas preservar em arquivo de referência.
- **DELEGAR AO CODEX** — permitir que o Codex decida seguindo o cânone confirmado.
- **MANTER EM ABERTO** — registrar como mistério ou informação ainda não definida, sem inventar resposta.

---

# 0 — SEGURANÇA E AUTORIZAÇÃO

## 0.1 Estado atual

- [ ] Criar um commit contendo **somente o estado manual atual do vault**, antes da consolidação.
- [ ] Criar a branch `codex/vault-consolidation` para o trabalho em massa.
- [ ] Criar também um backup completo fora do vault antes das exclusões.
- [ ] Não quero commit ou branch agora. Fazer apenas backup externo.

Observação:

> 

## 0.2 Política de exclusão

Escolha uma:

- [ ] **RECOMENDADO:** arquivar primeiro tudo que for removido e excluir definitivamente somente depois da revisão final.
- [ ] Excluir definitivamente do vault, confiando no Git e no backup externo.
- [ ] Não excluir arquivos; apenas movê-los para uma pasta de arquivo.

Destino preferido para arquivos arquivados:

> 

## 0.3 Limite da autorização

- [ ] Autorizo o Codex a renomear, mover, consolidar e excluir arquivos conforme este checklist.
- [ ] Autorizo a correção automática de links internos após renomes e mudanças de pasta.
- [ ] Autorizo a padronização de frontmatter, desde que os templates aprovados sejam respeitados.
- [ ] Autorizo a remoção de conteúdo herdado de Disgraceland quando não tiver uso em Omnisvera.
- [ ] Autorizo a limpeza de imagens órfãs somente após verificar que não são referenciadas.
- [ ] Quero revisar uma lista de exclusões antes de qualquer arquivo ser removido.

Exceções — arquivos ou pastas que nunca devem ser removidos:

> 

---

# 1 — IDENTIDADE, PÚBLICO E TOM DO VAULT

## 1.1 Quem terá acesso ao vault?

Escolha uma:

- [ ] **RECOMENDADO:** este será o vault privado do mestre, contendo informações públicas e segredos.
- [ ] Este vault será compartilhado integralmente com os jogadores.
- [ ] Manter uma área privada do mestre e uma área separada para jogadores.
- [ ] DELEGAR AO CODEX a melhor estrutura, mas nenhum segredo pode vazar para notas de jogadores.

## 1.2 Segredos e informações desconhecidas

- [ ] Usar callouts recolhidos do tipo `gm` dentro das notas comuns.
- [ ] Criar notas separadas para informações do mestre.
- [ ] Usar propriedades no frontmatter para controlar visibilidade.
- [ ] DELEGAR AO CODEX.

## 1.3 Tom principal da campanha

Confirme ou edite:

- [ ] Exploração e descoberta.
- [ ] Mistério e ruínas antigas.
- [ ] Fantasia medieval.
- [ ] Política apenas como pano de fundo, sem dominar a campanha.
- [ ] Intriga leve.
- [ ] Horror ocasional.
- [ ] Conflitos de facções.
- [ ] Viagens e descoberta do mapa pelos jogadores.

Outros tons desejados:

> 

Temas que devem ser removidos ou evitados:

> 

## 1.4 Idioma

- [ ] Todo conteúdo visível deve ficar em português.
- [ ] Termos técnicos internos podem permanecer em inglês: tags, `NoteStatus`, propriedades de plugins.
- [ ] Traduzir também tags e propriedades sempre que os plugins permitirem.
- [ ] DELEGAR AO CODEX.

---

# 2 — CONFIRMAÇÃO DOS AJUSTES MANUAIS RECENTES

Esta seção existe para que a consolidação não desfaça alterações que você já realizou.

## 2.1 Nimalis

- [ ] **Nimalis é o nome definitivo da capital do Reino de Nimalia.**
- [ ] Nimalis é provisório; manter marcado como cânone de trabalho.
- [ ] O nome ainda está em aberto.

População de `750.000`:

- [ ] É a população de todo o Reino de Nimalia.
- [ ] É a população da capital Nimalis.
- [ ] É apenas um valor provisório.
- [ ] DELEGAR AO CODEX uma estimativa coerente.

Distritos atuais de Nimalis:

- [ ] Manter todos.
- [ ] Revisar todos.
- [ ] DELEGAR AO CODEX.

Comentários sobre os distritos:

> 

## 2.2 Elarion Valthor

Grafia:

- [ ] **Elarion Valthor** é a grafia definitiva.
- [ ] Voltar para Elarion Vaelthor.
- [ ] Outra grafia:

> 

Raça:

- [ ] Meio-Elfo.
- [ ] Elfo.
- [ ] Outra:

> 

Confirme:

- [ ] Altura de 2,30 m.
- [ ] Alinhamento Neutro.
- [ ] Estado atual: desaparecido.
- [ ] Nível desconhecido.
- [ ] DELEGAR AO CODEX a revisão desses dados com base na história.

## 2.3 O Medalhão

- [ ] O arquivo deve se chamar `O Medalhão`, mas o título completo pode ser “O Medalhão dos Guardiões do Véu Cinzento”.
- [ ] Tanto o arquivo quanto o título devem ser apenas “O Medalhão”.
- [ ] Manter o nome completo em arquivo e título.
- [ ] DELEGAR AO CODEX.

## 2.4 Magias de Vezemir

As notas `Força Arcana`, `Velocidade` e `Magic` foram criadas recentemente:

- [ ] Manter as três.
- [ ] Manter apenas `Força Arcana` e `Velocidade`; remover `Magic`.
- [ ] `Magic` deve virar um índice da pasta.
- [ ] DELEGAR AO CODEX.

Esses poderes:

- [ ] São habilidades mágicas disponíveis para Vezemir no nível 1.
- [ ] São poderes futuros e ainda não estão disponíveis no nível 1.
- [ ] São elementos narrativos, não regras mecânicas.
- [ ] Precisam ser adaptados às regras de Old Dragon 2.
- [ ] DELEGAR AO CODEX a adaptação, sem aumentar o poder inicial do personagem.

## 2.5 Vezemir

Confirme:

- [ ] Alinhamento definitivo: Neutro-Bom.
- [ ] Persegue os responsáveis há 60 anos.
- [ ] Theron não deve aparecer como inimigo conhecido atualmente.
- [ ] “Desconhecido” é o inimigo correto no momento.
- [ ] A localização atual não deve listar Leth’valora, pois a vila foi destruída.
- [ ] A Floresta de Avenor pode permanecer como localização ou região atual.
- [ ] DELEGAR AO CODEX a consolidação da localização atual.

Observações:

> 

## 2.6 Mira

Confirme:

- [ ] Alinhamento: Bom.
- [ ] Classe atual registrada na nota está correta.
- [ ] Afiliação aos Sentinelas de Leth’valora está correta.
- [ ] Ela é filha do chefe humano de Leth’valora.
- [ ] O pai morreu no ataque à vila.
- [ ] O sobrenome dela deve indicar essa origem ou posição.

Sobrenome definitivo ou orientação para criá-lo:

> 

## 2.7 Padre Oric

Confirme:

- [ ] Origem: Nimalis.
- [ ] Território ou região atual: Floresta de Avenor.
- [ ] Facção atual: desconhecida.
- [ ] A religião dele ainda precisa ser decidida.
- [ ] DELEGAR AO CODEX a consolidação da nota sem inventar religião.

## 2.8 Outros ajustes manuais

Liste aqui mudanças que não podem ser revertidas:

> 

---

# 3 — SISTEMA DE TEMPLATES E FRONTMATTER

## 3.1 Regra geral

- [ ] **RECOMENDADO:** primeiro criar e aprovar todos os templates; depois migrar as notas.
- [ ] Criar os templates e migrar cada categoria imediatamente.

## 3.2 Vocabulário de `NoteStatus`

Proposta:

- `Active` — nota consolidada e em uso.
- `Draft` — conteúdo em desenvolvimento.
- `Placeholder` — nota mínima para preservar um conceito ou link.
- `Reference` — material de referência, não necessariamente cânone.
- `Template` — arquivo de modelo.
- `Archived` — conteúdo retirado do vault ativo.

- [ ] Aprovar essa lista.
- [ ] Alterar a lista:
- [ ] DELEGAR AO CODEX.

Alterações:

> 

## 3.3 Propriedade `status`

- [ ] Usar `status` em português para o estado narrativo: Ativo, Morto, Desaparecido, Destruída etc.
- [ ] Remover `status` quando ele duplicar `NoteStatus`.
- [ ] Manter ambos, mas com funções claramente diferentes.
- [ ] DELEGAR AO CODEX.

## 3.4 Convenções globais

Confirme:

- [ ] Propriedades técnicas em inglês e minúsculas.
- [ ] Usar `level`, nunca `Level`.
- [ ] Usar `chapters`, nunca `chapter`, em personagens.
- [ ] Usar `role: player` ou `role: npc`; títulos e profissões ficam em propriedades separadas.
- [ ] Wikilinks em propriedades devem usar o mesmo formato em todas as notas.
- [ ] Toda nota visual deve ter `cover` e/ou `thumbnail` quando houver imagem adequada.
- [ ] Toda nota deve ter tags de categoria consistentes.
- [ ] Os nomes de arquivos devem usar capitalização normal, não CAIXA ALTA obrigatória.
- [ ] DELEGAR AO CODEX as convenções não respondidas.

## 3.5 Idioma das tags

- [ ] **RECOMENDADO:** tags técnicas em inglês; títulos e conteúdo em português.
- [ ] Tags em português.
- [ ] Preservar tags existentes e apenas corrigir erros.

## 3.6 Templates necessários

Marque os que devem ser criados. A referência indicada será usada apenas como base visual e estrutural.

| Criar | Tipo de nota | Referência proposta | Sua decisão |
|---|---|---|---|
| [ ] | Personagem jogador | Vezemir, sem atributos por enquanto | |
| [ ] | NPC completo | Elarion Valthor e Mira | |
| [ ] | NPC mínimo / placeholder | Theron e Mestre Odran | |
| [ ] | Facção | Guardiões do Véu Cinzento | |
| [ ] | Item ou artefato | Grisalma e A Muralha de Vezemir | |
| [ ] | Localização | Leth’valora | |
| [ ] | Território, reino ou região | Reino de Nimalia | |
| [ ] | Lore, conceito ou evento | Véu Cinzento | |
| [ ] | Religião | Igreja das Chamas | |
| [ ] | Raça — lore | Antropo / Kenku | |
| [ ] | Raça — regras | Raças oficiais de Old Dragon 2 | |
| [ ] | Classe | Guerreiro | |
| [ ] | Magia ou poder | Força Arcana / Velocidade | |
| [ ] | História de personagem | Capítulo 00 de Vezemir | |
| [ ] | Capítulo ou sessão da campanha | Ecos de Um Mal Antigo | |
| [ ] | Mapa | Mapa de Earthropo | |
| [ ] | Linha do tempo ou evento datado | Timeline atual | |
| [ ] | Página de índice | Home e LORE | |

Tipos de nota que estão faltando:

> 

## 3.7 Personagens jogadores

- [ ] Todos os jogadores devem seguir a estrutura de Vezemir.
- [ ] Varkh e Raziel podem ter campos adicionais específicos, mas a estrutura-base deve ser idêntica.
- [ ] A seção de atributos fica fora do template por enquanto.
- [ ] A seção de atributos atual de Vezemir deve ser preservada apenas na nota dele.
- [ ] O template deve conter seções vazias para personalidade, objetivos, vínculos, equipamento, história e capítulos.

Seções que devem ser obrigatórias:

> 

---

# 4 — CÂNONE FUNDAMENTAL DO MUNDO

## 4.1 Hierarquia geográfica

Confirme:

- [ ] O nome do mundo não será revelado nem inventado agora.
- [ ] Earthropo é o continente.
- [ ] Nimalia é um reino de antropos.
- [ ] Nimalis é a capital de Nimalia.
- [ ] A Floresta de Avenor faz fronteira com Nimalia.
- [ ] Leth’valora era uma pequena vila élfica dentro de Avenor.
- [ ] Leth’valora não era um reino.
- [ ] Leth’valora foi destruída.
- [ ] Os reinos das demais raças serão apresentados aos poucos.

Correções:

> 

## 4.2 Premissa maior

Para cada conceito, escolha uma ação:

| Conceito | MANTER | REVISAR | REMOVER | EM ABERTO | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Véu Cinzento | [ ] | [ ] | [ ] | [ ] | [ ] |
| Guardiões do Véu Cinzento | [ ] | [ ] | [ ] | [ ] | [ ] |
| Criadores | [ ] | [ ] | [ ] | [ ] | [ ] |
| Eclipse de Obsidiana | [ ] | [ ] | [ ] | [ ] | [ ] |
| O Fraturamento | [ ] | [ ] | [ ] | [ ] | [ ] |
| Seis mundos-cópia | [ ] | [ ] | [ ] | [ ] | [ ] |
| Seis artefatos ligados aos mundos | [ ] | [ ] | [ ] | [ ] | [ ] |

O que os jogadores podem saber no início:

> 

O que deve permanecer segredo do mestre:

> 

## 4.3 Véu Cinzento

- [ ] É uma barreira.
- [ ] É uma região.
- [ ] É um fenômeno.
- [ ] É uma entidade ou força consciente.
- [ ] Sua natureza deve permanecer desconhecida.
- [ ] DELEGAR AO CODEX uma versão coerente, mantendo o mistério.

Elementos obrigatórios:

> 

Elementos proibidos:

> 

---

# 5 — GEOGRAFIA E MAPAS

## 5.1 Reino de Nimalia

- [ ] Posicionar o reino aproximadamente no mapa de Earthropo.
- [ ] Definir fronteiras naturais provisórias.
- [ ] Manter as fronteiras imprecisas para incentivar exploração.
- [ ] Definir fronteiras políticas completas nos bastidores do mestre.
- [ ] DELEGAR AO CODEX uma proposta geográfica.

Limites ou elementos obrigatórios:

> 

## 5.2 Avenor e Leth’valora

- [ ] Avenor está fora de Nimalia e faz fronteira com o reino.
- [ ] Avenor fica parcialmente dentro de Nimalia.
- [ ] O ponto exato da fronteira deve permanecer indefinido.
- [ ] Leth’valora será marcada no mapa como ruína.
- [ ] Leth’valora não aparecerá no mapa inicial dos jogadores.

## 5.3 Outras regiões

| Lugar | Manter | Revisar | Remover | Posição ou decisão |
|---|---:|---:|---:|---|
| Gharok | [ ] | [ ] | [ ] | |
| Valthor | [ ] | [ ] | [ ] | Sudeste de Earthropo / outro: |
| Campos de Earthropo | [ ] | [ ] | [ ] | |
| Bosque Sussurrante | [ ] | [ ] | [ ] | |
| Vale Dourado | [ ] | [ ] | [ ] | |
| Colinas do Urso | [ ] | [ ] | [ ] | |
| Mar da Neblina | [ ] | [ ] | [ ] | |
| Ashmoor | [ ] | [ ] | [ ] | |
| Libervale | [ ] | [ ] | [ ] | |
| Maré Baixa | [ ] | [ ] | [ ] | |

## 5.4 Futuros reinos raciais

- [ ] Reino élfico na maior região florestal.
- [ ] Reino anão ao norte ou nordeste, próximo de montanhas e vulcões.
- [ ] Não nomear esses reinos ainda.
- [ ] Criar nomes provisórios apenas nas notas privadas do mestre.
- [ ] Posicionar também territórios de outras raças.
- [ ] DELEGAR AO CODEX posições aproximadas sem revelar demais.

Raças que precisam de território próprio:

> 

## 5.5 Pins do Leaflet

- [ ] Criar pins somente para lugares já confirmados.
- [ ] Criar pins provisórios visíveis apenas ao mestre.
- [ ] Cada pin deve abrir a nota correspondente.
- [ ] Separar mapas do mestre e dos jogadores.
- [ ] Manter áreas desconhecidas sem pins.
- [ ] DELEGAR AO CODEX a convenção de pins e ícones.

---

# 6 — PERSONAGENS

## 6.1 Varkh

Preencha ou delegue:

- Idade definitiva:
  > 
- Altura:
  > 
- Alinhamento:
  > 
- Classe mecânica em Old Dragon 2:
  > 
- Classe ou identidade narrativa:
  > 

Confirme:

- [ ] Varkh é jogador.
- [ ] Não possui guilda ou facção definida atualmente.
- [ ] A fonte de referência do personagem está correta.
- [ ] Humanos são maioria no cenário de Old Dragon usado na campanha.
- [ ] Mestre Odran deve permanecer na história.
- [ ] A identidade do falsificador do remédio deve permanecer um mistério.
- [ ] DELEGAR AO CODEX a revisão completa, sem inventar respostas para mistérios.

A ficha chamada “Ficha do Jão”:

- [ ] Pertence a Varkh e deve ser consolidada na nota dele.
- [ ] É apenas referência mecânica.
- [ ] Não pertence a Varkh.
- [ ] Não sei; investigar antes de alterar.

## 6.2 Raziel

Confirme:

- [ ] A versão atual de Raziel, ladrão, substitui completamente a versão de mago.
- [ ] A história antiga com mais de 300 anos deve permanecer.
- [ ] A história deve ser ajustada para ficar coesa, sem reduzir a idade.
- [ ] A classe-base mecânica é Ladrão.
- [ ] Assassino será usado como especialização.
- [ ] Assassino ainda não foi aprovado.
- [ ] Vampiro e Hemomante são conceitos autorais a serem desenvolvidos.
- [ ] O local de origem ainda precisa ser posicionado com base na lore.
- [ ] DELEGAR AO CODEX a proposta de localização.

Onde Raziel deve encontrar ou integrar o grupo:

> 

Elementos da história que não podem ser alterados:

> 

## 6.3 Vezemir

Além da seção 2.5:

- [ ] A nota de Vezemir é a referência principal para todas as fichas de jogadores.
- [ ] Kaer Varyn foi substituído por Leth’valora em todo o cânone.
- [ ] Guilda dos Aventureiros foi substituída por Conclave dos Errantes.
- [ ] Clã dos Guardiões foi criado intencionalmente e deve permanecer.
- [ ] O dragão destruiu Leth’valora.
- [ ] DELEGAR AO CODEX a remoção de todas as versões contraditórias.

## 6.4 NPCs

| NPC | Manter | Revisar | Remover | DELEGAR | Observação obrigatória |
|---|---:|---:|---:|---:|---|
| Augustus Terra Decimus | [ ] | [ ] | [ ] | [ ] | Rei soberano de Nimalia |
| Mira | [ ] | [ ] | [ ] | [ ] | |
| Elarion Valthor | [ ] | [ ] | [ ] | [ ] | |
| Padre Oric | [ ] | [ ] | [ ] | [ ] | |
| Mestre Odran | [ ] | [ ] | [ ] | [ ] | |
| Theron | [ ] | [ ] | [ ] | [ ] | |
| Cassian | [ ] | [ ] | [ ] | [ ] | |

Augustus deve ser tratado como:

- [ ] Rei legítimo e aliado ou neutro.
- [ ] Rei legítimo, mas potencial antagonista.
- [ ] Antagonista principal.
- [ ] Papel político ainda em aberto.
- [ ] DELEGAR AO CODEX sem transformá-lo em vilão automaticamente.

---

# 7 — FACÇÕES

Escolha uma ação para cada facção:

| Facção | MANTER | REVISAR | REMOVER | ARQUIVAR | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Conclave dos Errantes | [ ] | [ ] | [ ] | [ ] | [ ] |
| Coroa de Nimalia | [ ] | [ ] | [ ] | [ ] | [ ] |
| Culto dos Sussurrantes | [ ] | [ ] | [ ] | [ ] | [ ] |
| Guarda Real | [ ] | [ ] | [ ] | [ ] | [ ] |
| Guardiões do Véu Cinzento | [ ] | [ ] | [ ] | [ ] | [ ] |
| Guilda dos Mercadores | [ ] | [ ] | [ ] | [ ] | [ ] |
| Sentinelas de Leth’valora | [ ] | [ ] | [ ] | [ ] | [ ] |

## 7.1 Conclave dos Errantes

- [ ] Nome definitivo.
- [ ] É uma companhia ou associação, não uma guilda genérica.
- [ ] Precisa de sede.
- [ ] Precisa de liderança.
- [ ] Precisa de objetivos.
- [ ] Deve permanecer deliberadamente pouco organizado.
- [ ] DELEGAR AO CODEX.

## 7.2 Coroa de Nimalia

- [ ] Manter política apenas como pano de fundo.
- [ ] Remover ideias de revoltas e repressão se não tiverem base no cânone.
- [ ] Manter controle sobre o Véu como possível segredo.
- [ ] Reescrever a facção em torno da administração do reino.
- [ ] DELEGAR AO CODEX.

## 7.3 Guardiões do Véu Cinzento

Defina o mínimo obrigatório:

> 

O restante:

- [ ] Pode ser desenvolvido pelo Codex.
- [ ] Deve permanecer desconhecido.
- [ ] Precisa de aprovação antes de ser escrito.

## 7.4 Sentinelas de Leth’valora

- [ ] Foram destruídos junto com a vila.
- [ ] Há sobreviventes.
- [ ] Mira é uma sobrevivente.
- [ ] Vezemir possui ligação formal com eles.
- [ ] A situação deve permanecer incerta.
- [ ] DELEGAR AO CODEX.

---

# 8 — RELIGIÕES

## 8.1 Nome da igreja

Escolha uma:

- [ ] Igreja das Chamas.
- [ ] Igreja das Sete Chamas.
- [ ] São organizações diferentes.
- [ ] Substituir por outro nome:
- [ ] DELEGAR AO CODEX uma solução que preserve as referências úteis.

Novo nome ou explicação:

> 

## 8.2 Religiões existentes

| Religião ou culto | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Igreja das Chamas | [ ] | [ ] | [ ] | [ ] |
| Igreja das Sete Chamas | [ ] | [ ] | [ ] | [ ] |
| Fé dos Antigos | [ ] | [ ] | [ ] | [ ] |
| Caminho dos Errantes | [ ] | [ ] | [ ] | [ ] |
| Culto dos Sussurrantes | [ ] | [ ] | [ ] | [ ] |

## 8.3 Estrutura religiosa

- [ ] Os Criadores são deuses reais.
- [ ] Os Criadores são uma interpretação religiosa, sem verdade confirmada.
- [ ] Existem vários deuses.
- [ ] Existem crenças raciais ou regionais distintas.
- [ ] A verdade religiosa deve permanecer desconhecida.
- [ ] DELEGAR AO CODEX a organização sem confirmar a cosmologia.

Religião de Padre Oric:

> 

---

# 9 — LORE E EVENTOS ANTIGOS

## 9.1 Eclipse de Obsidiana

- [ ] Manter a ideia de que parte do continente desapareceu.
- [ ] Manter o nome, mas reescrever o evento.
- [ ] Remover o evento.
- [ ] Transformar em mito ou versão não confirmada.
- [ ] DELEGAR AO CODEX.

## 9.2 O Fraturamento

- [ ] Manter os seis mundos-cópia.
- [ ] Manter o evento, mas remover o número e os detalhes fixos.
- [ ] Transformar em teoria de estudiosos.
- [ ] Remover.
- [ ] DELEGAR AO CODEX.

## 9.3 Os Criadores

- [ ] Criar uma nota própria.
- [ ] Manter apenas como conceito citado.
- [ ] Tratar como mito.
- [ ] Tratar como verdade secreta do mestre.
- [ ] Não desenvolver agora.
- [ ] DELEGAR AO CODEX.

## 9.4 Regra para lore incompleta

- [ ] Usar linguagem de rumor: “dizem”, “segundo as crônicas”, “alguns acreditam”.
- [ ] Marcar no frontmatter como `Draft` ou `Placeholder`.
- [ ] Não transformar hipótese em fato.
- [ ] Separar “Conhecimento público” de “Verdade do mestre”.
- [ ] DELEGAR AO CODEX.

---

# 10 — CALENDÁRIO E LINHA DO TEMPO

## 10.1 Calendário

Escolha uma:

- [ ] Manter os nomes atuais de dias, meses, estações e feriados.
- [ ] Manter meses e dias, mas revisar feriados.
- [ ] Manter apenas o ano de 2100 e reconstruir o restante.
- [ ] Arquivar o calendário atual e criar outro.
- [ ] DELEGAR AO CODEX uma versão consistente.

O calendário é:

- [ ] Mundial.
- [ ] Usado em todo Earthropo.
- [ ] Específico de Nimalia.
- [ ] Uma convenção narrativa para organizar sessões.

Data inicial exata da campanha:

> Dia:
>
> Mês:
>
> Ano: 2100

## 10.2 Linha do tempo

Escolha uma:

- [ ] Manter as datas exatas existentes.
- [ ] Manter apenas eventos confirmados e retirar datas inventadas.
- [ ] Converter datas antigas em eras ou períodos aproximados.
- [ ] Reconstruir a linha do tempo do zero usando as histórias dos personagens.
- [ ] DELEGAR AO CODEX.

Confirme ou corrija:

- [ ] Vezemir nasceu em 1900.
- [ ] Vezemir deixou Leth’valora por volta de 1940.
- [ ] Leth’valora foi destruída por volta de 2040.
- [ ] Vezemir perseguiu os responsáveis por aproximadamente 60 anos.
- [ ] A campanha começa em 2100.

Eventos que precisam obrigatoriamente de data:

> 

Eventos que devem permanecer sem data:

> 

---

# 11 — REGRAS, RAÇAS, CLASSES E MAGIA

## 11.1 Sistema

- [ ] Old Dragon 2 é a base oficial.
- [ ] Livros e PDFs de versões anteriores servem apenas como referência.
- [ ] Regras autorais precisam ser identificadas claramente.
- [ ] Nenhuma habilidade autoral entra em jogo sem aprovação.
- [ ] DELEGAR AO CODEX adaptações equilibradas.

## 11.2 Raças

Escolha o formato:

- [ ] Uma nota por raça contendo lore e regras.
- [ ] Separar lore da raça e estatísticas mecânicas.
- [ ] Lore no vault; regras apenas por referência aos livros.
- [ ] DELEGAR AO CODEX.

| Raça | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Antropo | [ ] | [ ] | [ ] | [ ] |
| Anão | [ ] | [ ] | [ ] | [ ] |
| Dragonborn / Dragonbourn | [ ] | [ ] | [ ] | [ ] |
| Elfo | [ ] | [ ] | [ ] | [ ] |
| Halfling | [ ] | [ ] | [ ] | [ ] |
| Humano | [ ] | [ ] | [ ] | [ ] |
| Kenku | [ ] | [ ] | [ ] | [ ] |

Grafia definitiva:

- [ ] Dragonborn.
- [ ] Dragonbourn.
- [ ] Outro:

> 

Os antropos:

- [ ] São beastfolks e constituem a população principal de Nimalia.
- [ ] São uma raça única com várias linhagens animais.
- [ ] São um conjunto de povos ou raças diferentes.
- [ ] DELEGAR AO CODEX a taxonomia, preservando Nimalia como reino antropo.

## 11.3 Classes

| Classe | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Guerreiro | [ ] | [ ] | [ ] | [ ] |
| Ladrão | [ ] | [ ] | [ ] | [ ] |
| Mago | [ ] | [ ] | [ ] | [ ] |
| Clérigo | [ ] | [ ] | [ ] | [ ] |
| Assassino | [ ] | [ ] | [ ] | [ ] |
| Alquimista | [ ] | [ ] | [ ] | [ ] |

- [ ] Classes oficiais devem ser copiadas ou resumidas dos materiais de Old Dragon 2.
- [ ] Classes não oficiais devem ser marcadas como opcionais ou autorais.
- [ ] Alquimista será classe independente.
- [ ] Alquimista será apenas identidade narrativa ou profissão.
- [ ] Assassino será uma especialização de Ladrão.
- [ ] DELEGAR AO CODEX.

## 11.4 Magia

- [ ] Criar um template único para magias e poderes.
- [ ] Separar magia de classe, habilidade racial e poder narrativo.
- [ ] Registrar fonte e versão da regra.
- [ ] Marcar claramente conteúdo autoral.
- [ ] DELEGAR AO CODEX a estrutura.

---

# 12 — PÁGINAS GERAIS E CONTEÚDO HERDADO

Escolha a ação para cada página ou grupo:

| Conteúdo | MANTER | REVISAR | REMOVER | ARQUIVAR | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Home | [ ] | [ ] | [ ] | [ ] | [ ] |
| LORE | [ ] | [ ] | [ ] | [ ] | [ ] |
| CULTURE | [ ] | [ ] | [ ] | [ ] | [ ] |
| ECONOMY | [ ] | [ ] | [ ] | [ ] | [ ] |
| RELIGION | [ ] | [ ] | [ ] | [ ] | [ ] |
| TIMELINE | [ ] | [ ] | [ ] | [ ] | [ ] |
| CALENDAR | [ ] | [ ] | [ ] | [ ] | [ ] |
| LATEST_NEWS | [ ] | [ ] | [ ] | [ ] | [ ] |
| OUTLINES | [ ] | [ ] | [ ] | [ ] | [ ] |
| Scratch Notes | [ ] | [ ] | [ ] | [ ] | [ ] |
| Material de Disgraceland | [ ] | [ ] | [ ] | [ ] | [ ] |
| Relatórios antigos de migração | [ ] | [ ] | [ ] | [ ] | [ ] |

## 12.1 Home

- [ ] Manter o tom atual de exploração e mistério.
- [ ] Remover qualquer tom jornalístico moderno herdado de Disgraceland.
- [ ] Evitar política como foco.
- [ ] Manter cards, Dataview e estrutura visual.
- [ ] Atualizar links, nomes e textos depois da consolidação.
- [ ] DELEGAR AO CODEX.

## 12.2 Disgraceland

- [ ] Preservar somente como referência de template e formatação.
- [ ] Remover nomes, lore, personagens, lugares e textos de Disgraceland do vault ativo.
- [ ] Preservar snippets e configurações que ainda forem necessários para a aparência.
- [ ] Arquivar uma cópia completa fora do vault ativo.
- [ ] Remover totalmente depois da migração.

Elementos específicos que deseja preservar:

> 

---

# 13 — PLUGINS, ARQUIVOS TÉCNICOS E MÍDIA

## 13.1 Plugins

- [ ] Manter somente plugins realmente usados.
- [ ] Não alterar configurações de plugins sem backup.
- [ ] Validar Dataview, Leaflet, Calendarium e banners depois da migração.
- [ ] Remover configurações herdadas que apontem para Disgraceland.
- [ ] DELEGAR AO CODEX a auditoria técnica.

Plugins ou comportamentos que não podem ser alterados:

> 

## 13.2 `zz_media`

- [ ] Não varrer imagens durante análises de lore.
- [ ] Varrer somente nomes, referências e arquivos órfãos durante a limpeza final.
- [ ] Não apagar nenhuma imagem.
- [ ] Arquivar imagens órfãs.
- [ ] Excluir imagens órfãs somente após relatório e confirmação.

## 13.3 Capas e imagens

- [ ] Manter as capas atuais quando estiverem funcionando.
- [ ] Corrigir apenas referências quebradas e nomes incorretos.
- [ ] Padronizar `cover`, `thumbnail` e `banner`.
- [ ] Não renomear imagens manualmente corrigidas.
- [ ] DELEGAR AO CODEX.

---

# 14 — ORDEM DA CONSOLIDAÇÃO

Numere ou marque a ordem desejada:

- [ ] 1. Segurança, Git e backup.
- [ ] 2. Templates e convenções de frontmatter.
- [ ] 3. Cânone fundamental.
- [ ] 4. Geografia e mapas.
- [ ] 5. Personagens jogadores.
- [ ] 6. NPCs.
- [ ] 7. Facções.
- [ ] 8. Religiões.
- [ ] 9. Lore e eventos históricos.
- [ ] 10. Regras, raças, classes e magia.
- [ ] 11. Calendário e linha do tempo.
- [ ] 12. Home e páginas gerais.
- [ ] 13. Remoção e arquivamento.
- [ ] 14. Validação de links, plugins, mapas e Dataview.
- [ ] 15. Commit, relatório final e push.

Outra ordem:

> 

---

# 15 — AUTORIZAÇÃO FINAL

Preencha somente depois das demais seções:

- [ ] Respondi todas as decisões que considero obrigatórias.
- [ ] Itens marcados como DELEGAR podem ser decididos pelo Codex.
- [ ] Itens marcados como MANTER EM ABERTO não devem receber respostas inventadas.
- [ ] Quero receber uma proposta resumida antes das alterações em massa.
- [ ] Autorizo começar as alterações em massa assim que o backup e os templates estiverem prontos.
- [ ] Quero revisar e aprovar os templates antes da migração das notas.
- [ ] Quero revisar a lista de exclusão antes da limpeza.
- [ ] Autorizo commit e push ao terminar cada grande etapa.

Instruções finais:

> 
