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
- [x] Criar a branch `codex/vault-consolidation` para o trabalho em massa.
- [ ] Criar também um backup completo fora do vault antes das exclusões.
- [ ] Não quero commit ou branch agora. Fazer apenas backup externo.

Observação:

> 

## 0.2 Política de exclusão

Escolha uma:

- [ ] **RECOMENDADO:** arquivar primeiro tudo que for removido e excluir definitivamente somente depois da revisão final.
- [x] Excluir definitivamente do vault, confiando no Git e no backup externo.
- [ ] Não excluir arquivos; apenas movê-los para uma pasta de arquivo.

Destino preferido para arquivos arquivados:

> 

## 0.3 Limite da autorização

- [x] Autorizo o Codex a renomear, mover, consolidar e excluir arquivos conforme este checklist.
- [x] Autorizo a correção automática de links internos após renomes e mudanças de pasta.
- [x] Autorizo a padronização de frontmatter, desde que os templates aprovados sejam respeitados.
- [x] Autorizo a remoção de conteúdo herdado de Disgraceland quando não tiver uso em Omnisvera.
- [x] Autorizo a limpeza de imagens órfãs somente após verificar que não são referenciadas.
- [x] Quero revisar uma lista de exclusões antes de qualquer arquivo ser removido.

Exceções — arquivos ou pastas que nunca devem ser removidos:

> 

---

# 1 — IDENTIDADE, PÚBLICO E TOM DO VAULT

## 1.1 Quem terá acesso ao vault?

Escolha uma:

- [ ] **RECOMENDADO:** este será o vault privado do mestre, contendo informações públicas e segredos.
- [ ] Este vault será compartilhado integralmente com os jogadores.
- [x] Manter uma área privada do mestre e uma área separada para jogadores. (criar um acesso igual a home, sendo a home do mestre. Então ficaria a home original para os jogadores e uma para o mestre.)
- [ ] DELEGAR AO CODEX a melhor estrutura, mas nenhum segredo pode vazar para notas de jogadores.

## 1.2 Segredos e informações desconhecidas

- [x] Usar callouts recolhidos do tipo `gm` dentro das notas comuns.
- [x] Criar notas separadas para informações do mestre.
- [x] Usar propriedades no frontmatter para controlar visibilidade.
- [ ] DELEGAR AO CODEX.

## 1.3 Tom principal da campanha

Confirme ou edite:

- [x] Exploração e descoberta.
- [x] Mistério e ruínas antigas.
- [x] Fantasia medieval.
- [x] Política apenas como pano de fundo, sem dominar a campanha.
- [ ] Intriga leve.
- [x] Horror ocasional.
- [ ] Conflitos de facções.
- [x] Viagens e descoberta do mapa pelos jogadores.

Outros tons desejados:

> 

Temas que devem ser removidos ou evitados:

> 

## 1.4 Idioma

- [x] Todo conteúdo visível deve ficar em português.
- [x] Termos técnicos internos podem permanecer em inglês: tags, `NoteStatus`, propriedades de plugins.
- [x] Traduzir também tags e propriedades sempre que os plugins permitirem.
- [ ] DELEGAR AO CODEX.

---

# 2 — CONFIRMAÇÃO DOS AJUSTES MANUAIS RECENTES

Esta seção existe para que a consolidação não desfaça alterações que você já realizou.

## 2.1 Nimalis

- [x] **Nimalis é o nome definitivo da capital do Reino de Nimalia.**
- [ ] Nimalis é provisório; manter marcado como cânone de trabalho.
- [ ] O nome ainda está em aberto.

População de `750.000`:

- [x] É a população de todo o Reino de Nimalia.
- [ ] É a população da capital Nimalis.
- [ ] É apenas um valor provisório.
- [x] DELEGAR AO CODEX uma estimativa coerente.

Distritos atuais de Nimalis:

- [x] Manter todos.
- [x] Revisar todos.
- [ ] DELEGAR AO CODEX.

Comentários sobre os distritos:

> 

## 2.2 Elarion Valthor

Grafia:

- [x] **Elarion Valthor** é a grafia definitiva.
- [ ] Voltar para Elarion Vaelthor.
- [ ] Outra grafia:

> 

Raça:

- [x] Meio-Elfo.
- [ ] Elfo.
- [ ] Outra:

> 

Confirme:

- [x] Altura de 2,30 m.
- [x] Alinhamento Neutro.
- [x] Estado atual: desaparecido.
- [x] Nível desconhecido.
- [ ] DELEGAR AO CODEX a revisão desses dados com base na história.

## 2.3 O Medalhão

- [x] O arquivo deve se chamar `O Medalhão`, mas o título completo pode ser “O Medalhão dos Guardiões do Véu Cinzento”.
- [ ] Tanto o arquivo quanto o título devem ser apenas “O Medalhão”.
- [ ] Manter o nome completo em arquivo e título.
- [ ] DELEGAR AO CODEX.

## 2.4 Magias de Vezemir

As notas `Força Arcana`, `Velocidade` e `Magic` foram criadas recentemente:

- [ ] Manter as três.
- [x] Manter apenas `Força Arcana` e `Velocidade`; remover `Magic`.
- [x] `Magic` deve virar um índice da pasta.
- [ ] DELEGAR AO CODEX.

Esses poderes:

- [x] São habilidades mágicas disponíveis para Vezemir no nível 1.
- [ ] São poderes futuros e ainda não estão disponíveis no nível 1.
- [ ] São elementos narrativos, não regras mecânicas.
- [x] Precisam ser adaptados às regras de Old Dragon 2.
- [ ] DELEGAR AO CODEX a adaptação, sem aumentar o poder inicial do personagem.

## 2.5 Vezemir

Confirme:

- [x] Alinhamento definitivo: Neutro-Bom.
- [x] Persegue os responsáveis há 60 anos.
- [x] Theron não deve aparecer como inimigo conhecido atualmente.
- [x] “Desconhecido” é o inimigo correto no momento.
- [x] A localização atual não deve listar Leth’valora, pois a vila foi destruída.
- [x] A Floresta de Avenor pode permanecer como localização ou região atual.
- [ ] DELEGAR AO CODEX a consolidação da localização atual.

Observações:

> 

## 2.6 Mira

Confirme:

- [x] Alinhamento: Bom.
- [x] Classe atual registrada na nota está correta.
- [x] Afiliação aos Sentinelas de Leth’valora está correta.
- [x] Ela é filha do chefe humano de Leth’valora.
- [x] O pai morreu no ataque à vila.
- [x] O sobrenome dela deve indicar essa origem ou posição.

Sobrenome definitivo ou orientação para criá-lo:

> 

## 2.7 Padre Oric

Confirme:

- [x] Origem: Nimalis.
- [x] Território ou região atual: Desconhecido
- [x] Facção atual: desconhecida.
- [x] A religião dele ainda precisa ser decidida.
- [ ] DELEGAR AO CODEX a consolidação da nota sem inventar religião.

## 2.8 Outros ajustes manuais

Liste aqui mudanças que não podem ser revertidas:

> 

---

# 3 — SISTEMA DE TEMPLATES E FRONTMATTER

## 3.1 Regra geral

- [x] **RECOMENDADO:** primeiro criar e aprovar todos os templates; depois migrar as notas.
- [x] Criar os templates e migrar cada categoria imediatamente.

## 3.2 Vocabulário de `NoteStatus`

Proposta:

- `Active` — nota consolidada e em uso.
- `Draft` — conteúdo em desenvolvimento.
- `Placeholder` — nota mínima para preservar um conceito ou link.
- `Reference` — material de referência, não necessariamente cânone.
- `Template` — arquivo de modelo.
- `Archived` — conteúdo retirado do vault ativo.

- [x] Aprovar essa lista.
- [ ] Alterar a lista:
- [x] DELEGAR AO CODEX.

Alterações:

> 

## 3.3 Propriedade `status`

- [x] Usar `status` em português para o estado narrativo: Ativo, Morto, Desaparecido, Destruída etc.
- [ ] Remover `status` quando ele duplicar `NoteStatus`.
- [x] Manter ambos, mas com funções claramente diferentes.
- [ ] DELEGAR AO CODEX.

## 3.4 Convenções globais

Confirme:

- [x] Propriedades técnicas em inglês e minúsculas.
- [x] Usar `level`, nunca `Level`.
- [x] Usar `chapters`, nunca `chapter`, em personagens.
- [x] Usar `role: player` ou `role: npc`; títulos e profissões ficam em propriedades separadas.
- [x] Wikilinks em propriedades devem usar o mesmo formato em todas as notas.
- [x] Toda nota visual deve ter `cover` e/ou `thumbnail` quando houver imagem adequada.(Mesmo não tendo adequada, eu vou criar depois, não se preocupe com ter ou não)
- [x] Toda nota deve ter tags de categoria consistentes.
- [x] Os nomes de arquivos devem usar capitalização normal, não CAIXA ALTA obrigatória.
- [x] DELEGAR AO CODEX as convenções não respondidas.

## 3.5 Idioma das tags

- [x] **RECOMENDADO:** tags técnicas em inglês; títulos e conteúdo em português.
- [ ] Tags em português.
- [ ] Preservar tags existentes e apenas corrigir erros.

## 3.6 Templates necessários

Marque os que devem ser criados. A referência indicada será usada apenas como base visual e estrutural.

| Criar | Tipo de nota | Referência proposta | Sua decisão |
|---|---|---|---|
| [x] | Personagem jogador | Vezemir, sem atributos por enquanto |ficha padrão |
| [x] | NPC completo | Elarion Valthor e Mira |padrão |
| [x] | NPC mínimo / placeholder | Theron e Mestre Odran |padrão |
| [x] | Facção | Guardiões do Véu Cinzento |padrão minimo |
| [x] | Item ou artefato | Grisalma e A Muralha de Vezemir |padrão |
| [x] | Localização | Leth’valora | padrão|
| [x] | Território, reino ou região | Reino de Nimalia | padrão|
| [x] | Lore, conceito ou evento | Véu Cinzento |padrão |
| [x] | Religião | Igreja das Chamas |padrão |
| [x] | Raça — lore | Antropo / Kenku |padrão |
| [x] | Raça — regras | Raças oficiais de Old Dragon 2 |padrão, sem precisar mencionar de qual versão do old dragon ta usando |
| [x] | Classe | Guerreiro |padrão |
| [x] | Magia ou poder | Força Arcana / Velocidade |padrão |
| [x] | História de personagem | Capítulo 00 de Vezemir |já existe alguns capitulos, da pra pegar um padrão |
| [x] | Capítulo ou sessão da campanha | Ecos de Um Mal Antigo |ecos de um mal antigo deve ser a unica historia então, não ecos de um mundo perdido   |
| [x] | Mapa | Mapa de Earthropo |já tem, tem que fazer os outros |
| [x] | Linha do tempo ou evento datado | Timeline atual |deve ter algumas informações, que ja da pra utilizar |
| [x] | Página de índice | Home e LORE | como disse, uma pagina home para o mestre e uma para o jogador|

Tipos de nota que estão faltando:

> 

## 3.7 Personagens jogadores

- [x] Todos os jogadores devem seguir a estrutura de Vezemir.
- [ ] Varkh e Raziel podem ter campos adicionais específicos, mas a estrutura-base deve ser idêntica.
- [ ] A seção de atributos fica fora do template por enquanto.
- [ ] A seção de atributos atual de Vezemir deve ser preservada apenas na nota dele.
- [x] O template deve conter seções vazias para personalidade, objetivos, vínculos, equipamento, história e capítulos.

Seções que devem ser obrigatórias:

> deixe a parte de atributos mais pra cima, nao no final, reuna todos eles e deixe a formatação melhorada, dando pra usar ele em outras notas, como wikilinks ou como se fosse função do excel

---

# 4 — CÂNONE FUNDAMENTAL DO MUNDO

## 4.1 Hierarquia geográfica

Confirme:

- [x] O nome do mundo não será revelado nem inventado agora.
- [x] Earthropo é o continente.
- [x] Nimalia é um reino de antropos.
- [x] Nimalis é a capital de Nimalia.
- [x] A Floresta de Avenor faz fronteira com Nimalia.
- [x] Leth’valora era uma pequena vila élfica dentro de Avenor.
- [x] Leth’valora não era um reino.
- [x] Leth’valora foi destruída.
- [x] Os reinos das demais raças serão apresentados aos poucos.

Correções:

> 

## 4.2 Premissa maior

Para cada conceito, escolha uma ação:

| Conceito | MANTER | REVISAR | REMOVER | EM ABERTO | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Véu Cinzento | [ ] | [x] | [ ] | [ ] | [x] |
| Guardiões do Véu Cinzento | [ ] | [x] | [ ] | [ ] | [x] |
| Criadores | [ ] | [x] | [ ] | [ ] | [x] |
| Eclipse de Obsidiana | [ ] | [x] | [ ] | [ ] | [x] |
| O Fraturamento | [ ] | [x] | [ ] | [ ] | [x] |
| Seis mundos-cópia | [ ] | [x] | [ ] | [ ] | [x] |
| Seis artefatos ligados aos mundos | [ ] | [x] | [ ] | [ ] | [x] |

O que os jogadores podem saber no início:

> pouca coisa, quase nada

O que deve permanecer segredo do mestre:

> tudo, so informação minima deve ser compartilhada. se possivel, crie notas falando sobre elas e as wikilinks, com dataviews e etcs, nas notas que já discutimos e que puxam conteudo de historia, lore no caso

## 4.3 Véu Cinzento

- [ ] É uma barreira.
- [ ] É uma região.
- [x] É um fenômeno.
- [ ] É uma entidade ou força consciente.
- [x] Sua natureza deve permanecer desconhecida.
- [x] DELEGAR AO CODEX uma versão coerente, mantendo o mistério.

Elementos obrigatórios:

> 

Elementos proibidos:

> 

---

# 5 — GEOGRAFIA E MAPAS

## 5.1 Reino de Nimalia

- [x] Posicionar o reino aproximadamente no mapa de Earthropo.
- [x] Definir fronteiras naturais provisórias.
- [ ] Manter as fronteiras imprecisas para incentivar exploração.
- [x] Definir fronteiras políticas completas nos bastidores do mestre.
- [x] DELEGAR AO CODEX uma proposta geográfica.

Limites ou elementos obrigatórios:

> 

## 5.2 Avenor e Leth’valora

- [x] Avenor está fora de Nimalia e faz fronteira com o reino.
- [ ] Avenor fica parcialmente dentro de Nimalia.
- [ ] O ponto exato da fronteira deve permanecer indefinido.
- [x] Leth’valora será marcada no mapa como ruína.
- [ ] Leth’valora não aparecerá no mapa inicial dos jogadores.

## 5.3 Outras regiões

| Lugar | Manter | Revisar | Remover | Posição ou decisão |
|---|---:|---:|---:|---|
| Gharok | [ ] | [x] | [ ] | |
| Valthor | [x] | [ ] | [ ] | Sudeste de Earthropo / outro: |
| Campos de Earthropo | [ ] | [x] | [ ] | |
| Bosque Sussurrante | [ ] | [x] | [ ] | |
| Vale Dourado | [ ] | [x] | [ ] | |
| Colinas do Urso | [ ] | [ ] | [x] | |
| Mar da Neblina | [ ] | [x] | [ ] | |
| Ashmoor | [ ] | [ ] | [x] | |
| Libervale | [ ] | [ ] | [x] | |
| Maré Baixa | [ ] | [x] | [ ] | |

## 5.4 Futuros reinos raciais

- [x] Reino élfico na maior região florestal.
- [x] Reino anão ao norte ou nordeste, próximo de montanhas e vulcões.
- [ ] Não nomear esses reinos ainda.
- [x] Criar nomes provisórios apenas nas notas privadas do mestre.
- [x] Posicionar também territórios de outras raças.
- [x] DELEGAR AO CODEX posições aproximadas sem revelar demais.

Raças que precisam de território próprio:

> 

## 5.5 Pins do Leaflet

- [x] Criar pins somente para lugares já confirmados.
- [x] Criar pins provisórios visíveis apenas ao mestre.
- [x] Cada pin deve abrir a nota correspondente.
- [ ] Separar mapas do mestre e dos jogadores.
- [ ] Manter áreas desconhecidas sem pins.
- [x] DELEGAR AO CODEX a convenção de pins e ícones.

---

# 6 — PERSONAGENS

## 6.1 Varkh

Preencha ou delegue:

- Idade definitiva:
  > 35 anos
- Altura:
  > 1,70
- Alinhamento:
  > neutro
- Classe mecânica em Old Dragon 2:
  > alquimista.
- Classe ou identidade narrativa:
  > alquimista

Confirme:

- [x] Varkh é jogador.
- [x] facção é o conclave dos errantes
- [x] A fonte de referência do personagem está correta.
- [ ] Humanos são maioria no cenário de Old Dragon usado na campanha.
- [x] Mestre Odran deve permanecer na história.
- [x] A identidade do falsificador do remédio deve permanecer um mistério.
- [x] DELEGAR AO CODEX a revisão completa, sem inventar respostas para mistérios.

A ficha chamada “Ficha do Jão”:

- [x] Pertence a Varkh e deve ser consolidada na nota dele.
- [ ] É apenas referência mecânica.
- [ ] Não pertence a Varkh.
- [ ] Não sei; investigar antes de alterar.

## 6.2 Raziel

Confirme:

- [x] A versão atual de Raziel, ladrão, substitui completamente a versão de mago.
- [x] A história antiga com mais de 300 anos deve permanecer.
- [x] A história deve ser ajustada para ficar coesa, sem reduzir a idade.
- [x] A classe-base mecânica é Ladrão.
- [x] Assassino será usado como especialização.
- [ ] Assassino ainda não foi aprovado.
- [x] Vampiro e Hemomante são conceitos autorais a serem desenvolvidos.
- [x] O local de origem ainda precisa ser posicionado com base na lore.
- [x] DELEGAR AO CODEX a proposta de localização.

Onde Raziel deve encontrar ou integrar o grupo:

> em nimalis

Elementos da história que não podem ser alterados:

> mestre, o grupo dele e a vingança, bem como o mestre que ajuda ele.

## 6.3 Vezemir

Além da seção 2.5:

- [x] A nota de Vezemir é a referência principal para todas as fichas de jogadores.
- [x] Kaer Varyn foi substituído por Leth’valora em todo o cânone.
- [x] Guilda dos Aventureiros foi substituída por Conclave dos Errantes.
- [ ] Clã dos Guardiões foi criado intencionalmente e deve permanecer.
- [x] O dragão destruiu Leth’valora.
- [x] DELEGAR AO CODEX a remoção de todas as versões contraditórias.

## 6.4 NPCs

| NPC | Manter | Revisar | Remover | DELEGAR | Observação obrigatória |
|---|---:|---:|---:|---:|---|
| Augustus Terra Decimus | [x] | [x] | [ ] | [x] | Rei soberano de Nimalia |
| Mira | [x] | [ ] | [ ] | [x] | |
| Elarion Valthor | [x] | [ ] | [ ] | [x] | |
| Padre Oric | [ ] | [x] | [ ] | [x] | |
| Mestre Odran | [ ] | [x] | [ ] | [x] | |
| Theron | [ ] | [x] | [ ] | [x] | personagem sem muita importância|
| Cassian | [ ] | [x] | [ ] | [x] | |

Augustus deve ser tratado como:

- [ ] Rei legítimo e aliado ou neutro.
- [x] Rei legítimo, mas potencial antagonista.
- [ ] Antagonista principal.
- [ ] Papel político ainda em aberto.
- [x] DELEGAR AO CODEX sem transformá-lo em vilão automaticamente.

---

# 7 — FACÇÕES

Escolha uma ação para cada facção:

| Facção | MANTER | REVISAR | REMOVER | ARQUIVAR | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Conclave dos Errantes | [x] | [x] | [ ] | [ ] | [x] |
| Coroa de Nimalia | [x] | [x] | [ ] | [ ] | [x] |
| Culto dos Sussurrantes | [ ] | [x] | [ ] | [ ] | [x] |  guilda das trevas
| Guarda Real | [ ] | [x] | [ ] | [ ] | [x] |
| Guardiões do Véu Cinzento | [ ] | [x] | [ ] | [ ] | [x] |  grupo antigo de herois, mas ninguem sabe mais nada sobre
| Guilda dos Mercadores | [ ] | [x] | [ ] | [ ] | [x] |
| Sentinelas de Leth’valora | [ ] | [x] | [ ] | [ ] | [x] |

## 7.1 Conclave dos Errantes

- [x] Nome definitivo.
- [ ] É uma companhia ou associação, não uma guilda genérica.
- [x] Precisa de sede.
- [x] Precisa de liderança.
- [x] Precisa de objetivos.
- [ ] Deve permanecer deliberadamente pouco organizado.
- [x] DELEGAR AO CODEX.

## 7.2 Coroa de Nimalia

- [x] Manter política apenas como pano de fundo.
- [ ] Remover ideias de revoltas e repressão se não tiverem base no cânone.
- [x] Manter controle sobre o Véu como possível segredo.
- [ ] Reescrever a facção em torno da administração do reino.
- [ ] DELEGAR AO CODEX.

## 7.3 Guardiões do Véu Cinzento

Defina o mínimo obrigatório:

> 

O restante:

- [x] Pode ser desenvolvido pelo Codex.
- [ ] Deve permanecer desconhecido.
- [x] Precisa de aprovação antes de ser escrito.

## 7.4 Sentinelas de Leth’valora

- [x] Foram destruídos junto com a vila.
- [ ] Há sobreviventes.
- [ ] Mira é uma sobrevivente.
- [ ] Vezemir possui ligação formal com eles.
- [x] A situação deve permanecer incerta.
- [ ] DELEGAR AO CODEX.

---

# 8 — RELIGIÕES

## 8.1 Nome da igreja

Escolha uma:

- [x] Igreja das Chamas.
- [ ] Igreja das Sete Chamas.
- [ ] São organizações diferentes.
- [ ] Substituir por outro nome:
- [ ] DELEGAR AO CODEX uma solução que preserve as referências úteis.

Novo nome ou explicação:

> 

## 8.2 Religiões existentes

| Religião ou culto | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Igreja das Chamas | [x] | [ ] | [ ] | [x] |
| Igreja das Sete Chamas | [ ] | [ ] | [x] | [ ] |
| Fé dos Antigos | [x] | [ ] | [ ] | [x] |
| Caminho dos Errantes | [ ] | [x] | [ ] | [x] |
| Culto dos Sussurrantes | [ ] | [x] | [ ] | [x] |

## 8.3 Estrutura religiosa

- [x] Os Criadores são deuses reais.
- [ ] Os Criadores são uma interpretação religiosa, sem verdade confirmada.
- [x] Existem vários deuses.
- [x] Existem crenças raciais ou regionais distintas.
- [x] A verdade religiosa deve permanecer desconhecida.
- [x] DELEGAR AO CODEX a organização sem confirmar a cosmologia.

Religião de Padre Oric:

> igreja das chamas

---

# 9 — LORE E EVENTOS ANTIGOS

## 9.1 Eclipse de Obsidiana

- [x] Manter a ideia de que parte do continente desapareceu.
- [x] Manter o nome, mas reescrever o evento.
- [ ] Remover o evento.
- [x] Transformar em mito ou versão não confirmada.
- [x] DELEGAR AO CODEX.

## 9.2 O Fraturamento

- [x] Manter os seis mundos-cópia.
- [x] Manter o evento, mas remover o número e os detalhes fixos.
- [x] Transformar em teoria de estudiosos.
- [ ] Remover.
- [x] DELEGAR AO CODEX.

## 9.3 Os Criadores

- [x] Criar uma nota própria.
- [ ] Manter apenas como conceito citado.
- [x] Tratar como mito.
- [x] Tratar como verdade secreta do mestre.
- [ ] Não desenvolver agora.
- [x] DELEGAR AO CODEX.

## 9.4 Regra para lore incompleta

- [x] Usar linguagem de rumor: “dizem”, “segundo as crônicas”, “alguns acreditam”.
- [x] Marcar no frontmatter como `Draft` ou `Placeholder`.
- [ ] Não transformar hipótese em fato.
- [x] Separar “Conhecimento público” de “Verdade do mestre”.
- [x] DELEGAR AO CODEX.

---

# 10 — CALENDÁRIO E LINHA DO TEMPO

## 10.1 Calendário

Escolha uma:

- [x] Manter os nomes atuais de dias, meses, estações e feriados.
- [x] Manter meses e dias, mas revisar feriados.
- [ ] Manter apenas o ano de 2100 e reconstruir o restante.
- [ ] Arquivar o calendário atual e criar outro.
- [x] DELEGAR AO CODEX uma versão consistente.

O calendário é:

- [x] Mundial.
- [x] Usado em todo Earthropo.
- [ ] Específico de Nimalia.
- [ ] Uma convenção narrativa para organizar sessões.

Data inicial exata da campanha:

> Dia: 03
>
> Mês: 07
>
> Ano: 2377

## 10.2 Linha do tempo

Escolha uma:

- [ ] Manter as datas exatas existentes.
- [ ] Manter apenas eventos confirmados e retirar datas inventadas.
- [ ] Converter datas antigas em eras ou períodos aproximados.
- [ ] Reconstruir a linha do tempo do zero usando as histórias dos personagens.
- [ ] DELEGAR AO CODEX.

Confirme ou corrija:

- [x] Vezemir nasceu em 1900.
- [x] Vezemir deixou Leth’valora por volta de 1940.
- [x] Leth’valora foi destruída por volta de 2040.
- [x] Vezemir perseguiu os responsáveis por aproximadamente 60 anos.
- [ ] A campanha começa em 2377

Eventos que precisam obrigatoriamente de data:

> 

Eventos que devem permanecer sem data:

> as guerras que vezemir lutou

---

# 11 — REGRAS, RAÇAS, CLASSES E MAGIA

## 11.1 Sistema

- [x] Old Dragon 2 é a base oficial.
- [ ] Livros e PDFs de versões anteriores servem apenas como referência.
- [ ] Regras autorais precisam ser identificadas claramente.
- [ ] Nenhuma habilidade autoral entra em jogo sem aprovação.
- [x] DELEGAR AO CODEX adaptações equilibradas.

## 11.2 Raças

Escolha o formato:

- [x] Uma nota por raça contendo lore e regras.
- [x] Separar lore da raça e estatísticas mecânicas.
- [ ] Lore no vault; regras apenas por referência aos livros.
- [x] DELEGAR AO CODEX.

| Raça | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Antropo | [x] | [x] | [ ] | [x] |
| Anão | [x] | [x] | [ ] | [x] |
| Dragonborn | [x] | [x] | [ ] | [x] |
| Elfo | [x] | [x] | [ ] | [x] |
| Halfling | [x] | [x] | [ ] | [x] |
| Humano | [x] | [x] | [ ] | [x] |
| Kenku | [x] | [x] | [ ] | [x] | raça que faz parte dos Antropos

Grafia definitiva:

- [x] Dragonborn.
- [ ] Dragonbourn.
- [ ] Outro:

> 

Os antropos:

- [x] São beastfolks e constituem a população principal de Nimalia.
- [x] São uma raça única com várias linhagens animais.
- [ ] São um conjunto de povos ou raças diferentes.
- [x] DELEGAR AO CODEX a taxonomia, preservando Nimalia como reino antropo.

## 11.3 Classes

| Classe | MANTER | REVISAR | REMOVER | DELEGAR |
|---|---:|---:|---:|---:|
| Guerreiro | [x] | [x] | [ ] | [x] |
| Ladrão | [x] | [x] | [ ] | [x] |
| Mago | [x] | [x] | [ ] | [x] |
| Clérigo | [x] | [x] | [ ] | [x] |
| Assassino | [ ] | [x] | [ ] | [x] |
| Alquimista | [x] | [x] | [ ] | [x] |

- [x] Classes oficiais devem ser copiadas ou resumidas dos materiais de Old Dragon 2.
- [ ] Classes não oficiais devem ser marcadas como opcionais ou autorais.
- [x] Alquimista será classe independente.
- [ ] Alquimista será apenas identidade narrativa ou profissão.
- [x] Assassino será uma especialização de Ladrão.
- [x] DELEGAR AO CODEX.

## 11.4 Magia

- [x] Criar um template único para magias e poderes.
- [x] Separar magia de classe, habilidade racial e poder narrativo.
- [x] Registrar fonte e versão da regra.
- [ ] Marcar claramente conteúdo autoral.
- [x] DELEGAR AO CODEX a estrutura.

---

# 12 — PÁGINAS GERAIS E CONTEÚDO HERDADO

Escolha a ação para cada página ou grupo:

| Conteúdo | MANTER | REVISAR | REMOVER | ARQUIVAR | DELEGAR |
|---|---:|---:|---:|---:|---:|
| Home | [x] | [x] | [ ] | [ ] | [x] |
| LORE | [x] | [x] | [ ] | [ ] | [x] |
| CULTURE | [x] | [x] | [ ] | [ ] | [x] |
| ECONOMY | [x] | [x] | [ ] | [ ] | [x] | adicionar todo o estoque de itens e armas dos livros PDFs de referencia
| RELIGION | [x] | [x] | [ ] | [ ] | [x] |
| TIMELINE | [x] | [x] | [ ] | [ ] | [x] |
| CALENDAR | [x] | [x] | [ ] | [ ] | [x] |
| LATEST_NEWS | [x] | [x] | [ ] | [ ] | [x] |
| OUTLINES | [x] | [x] | [ ] | [ ] | [x] |
| Scratch Notes | [x] | [x] | [ ] | [ ] | [x] |
| Material de Disgraceland | [ ] | [ ] | [x] | [ ] | [ ] |
| Relatórios antigos de migração | [ ] | [ ] | [x] | [ ] | [ ] |

## 12.1 Home

- [x] Manter o tom atual de exploração e mistério.
- [x] Remover qualquer tom jornalístico moderno herdado de Disgraceland.
- [x] Evitar política como foco.
- [x] Manter cards, Dataview e estrutura visual.
- [x] Atualizar links, nomes e textos depois da consolidação.
- [x] DELEGAR AO CODEX.

## 12.2 Disgraceland

- [x] Preservar somente como referência de template e formatação.
- [x] Remover nomes, lore, personagens, lugares e textos de Disgraceland do vault ativo.
- [x] Preservar snippets e configurações que ainda forem necessários para a aparência.
- [ ] Arquivar uma cópia completa fora do vault ativo.
- [x] Remover totalmente depois da migração.

Elementos específicos que deseja preservar:

> 

---

# 13 — PLUGINS, ARQUIVOS TÉCNICOS E MÍDIA

## 13.1 Plugins

- [ ] Manter somente plugins realmente usados.
- [x] Não alterar configurações de plugins sem backup.
- [x] Validar Dataview, Leaflet, Calendarium e banners depois da migração.
- [x] Remover configurações herdadas que apontem para Disgraceland.
- [x] DELEGAR AO CODEX a auditoria técnica.

Plugins ou comportamentos que não podem ser alterados:

> 

## 13.2 `zz_media`

- [x] Não varrer imagens durante análises de lore.
- [x] Varrer somente nomes, referências e arquivos órfãos durante a limpeza final.
- [ ] Não apagar nenhuma imagem.
- [ ] Arquivar imagens órfãs.
- [x] Excluir imagens órfãs somente após relatório e confirmação.

## 13.3 Capas e imagens

- [x] Manter as capas atuais quando estiverem funcionando.
- [ ] Corrigir apenas referências quebradas e nomes incorretos.
- [x] Padronizar `cover`, `thumbnail` e `banner`.
- [ ] Não renomear imagens manualmente corrigidas.
- [x] DELEGAR AO CODEX.

---

# 14 — ORDEM DA CONSOLIDAÇÃO

Numere ou marque a ordem desejada:

- [x] 1. Segurança, Git e backup.
- [x] 2. Templates e convenções de frontmatter.
- [x] 3. Cânone fundamental.
- [x] 4. Geografia e mapas.
- [x] 5. Personagens jogadores.
- [x] 6. NPCs.
- [x] 7. Facções.
- [x] 8. Religiões.
- [x] 9. Lore e eventos históricos.
- [x] 10. Regras, raças, classes e magia.
- [x] 11. Calendário e linha do tempo.
- [x] 12. Home e páginas gerais.
- [x] 13. Remoção e arquivamento.
- [x] 14. Validação de links, plugins, mapas e Dataview.
- [x] 15. Commit, relatório final e push.

Outra ordem:

> 

---

# 15 — AUTORIZAÇÃO FINAL

Preencha somente depois das demais seções:

- [x] Respondi todas as decisões que considero obrigatórias.
- [x] Itens marcados como DELEGAR podem ser decididos pelo Codex.
- [x] Itens marcados como MANTER EM ABERTO não devem receber respostas inventadas.
- [x] Quero receber uma proposta resumida antes das alterações em massa.
- [x] Autorizo começar as alterações em massa assim que o backup e os templates estiverem prontos.
- [ ] Quero revisar e aprovar os templates antes da migração das notas.
- [ ] Quero revisar a lista de exclusão antes da limpeza.
- [x] Autorizo commit e push ao terminar cada grande etapa.

Instruções finais:

> 

