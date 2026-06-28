# Omnisvera — Pente Fino e Pendências Gerais

Data: 2026-06-28  
Escopo: estado atual do vault após ajustes manuais do Sage e correções técnicas recentes.

> [!IMPORTANT]
> Este relatório não é um commit e não congela decisões.
> Ele serve como lista de controle para decidir o que resolver antes do próximo lote de padronização.

## Resumo executivo

O vault está em estado utilizável para continuar a consolidação, mas ainda não está “fechado” para uma migração ampla. A base operacional melhorou: Home, mapas principais, imagens críticas e links óbvios estão mais coerentes. O próximo risco real não é técnico puro; é misturar correção estrutural com decisão de lore sem perceber.

## Decisões do Sage aplicadas neste pente fino

| Tema | Decisão aplicada |
|---|---|
| Mapas | Três camadas oficiais: `MAPA DE EARTHROPO.md` para continente, `MAPA DE NIMALIA.md` para reino e `MAPA DE NIMALIS.md` para capital. |
| Nimalis | Capital do Reino de Nimalia, população aproximada de 450.000, governada por [[Augustus Terra Decimus]]. |
| Bairros de Nimalis | Criadas notas para bairros/regiões principais: humanos, elfos, anões, dragonborns, nobre, mercado, distrito comercial, forasteiros e porto. |
| Avenor | Região próxima a Nimalia; pode abrigar o futuro reino élfico mais adiante. |
| Gharok | Antiga fortaleza anã ao norte de Nimalia, ligada à região do futuro reino anão. |
| Valthor | Ruínas a sudeste de Nimalia; antigo reino próspero. |
| Reinos racializados | Élfico no sudoeste, anão no nordeste, dragonborn no noroeste. |
| Theron Elensar | Remoção confirmada. |
| Varkh | Alquimista, 30 anos, origem em Nimalis/Maré Baixa, membro do Conclave dos Errantes. |
| Raziel | Classe operacional Vampiro; Sangue Antigo será mecânica própria de Omnisvera. |
| Vezemir | Poderes especiais ficam sob controle do mestre durante o nível 1. |
| Mira Valen | Estado atual aprovado. |
| Mestre Odran | Imagem aprovada; thumbnail criada. |
| Dragão de Colar Dourado | Informação será revelada aos poucos em jogo. |
| Criadores | Mito de criação; deuses antigos que moldaram o mundo e estiveram ligados a guerras de magia antiga. |
| Véu Cinzento | Fenômeno de névoa branca espessa, com referência visual próxima a Silent Hill, mas mais branco e denso. |
| Guardiões do Véu Cinzento | Ordem antiquíssima da época dos Criadores; conhecida por registros posteriores, membros desconhecidos. |
| Sentinelas de Leth'valora | Guardas locais da vila, mortos no incidente do dragão. |
| Nobreza de Nimalia | Facção ativa cobrindo todos os nobres do reino. |
| Guilda dos Mercadores | Guilda econômica/comercial com alcance por Earthropo. |
| Clã Sanguinallis | Integrado conforme lore atual de Raziel, Gharok, Valthor e Sangue Antigo. |
| O Medalhão | Nome oficial do item de Vezemir é apenas `O Medalhão`. |
| Muralha de Dorn | Confirmado como item/escudo. |
| Homem de Armas | Remoção operacional confirmada; Guerreiro permanece oficial. |
| Antropos | Raça própria de Omnisvera; substitui beastfolks e predomina em Nimalia. |
| Humanos | Não são maioria no universo de Omnisvera, apesar da premissa de Old Dragon. |

Minha recomendação é continuar em lotes pequenos:

1. fechar decisões pendentes deste relatório;
2. commitar as correções atuais em grupos rastreáveis;
3. padronizar `Characters/Individual`;
4. validar visualmente `EARTHROPO/EARTHROPO.md`, `Home.md`, `Home_Mestre.md`, `MAPA DE EARTHROPO.md` e `MAPA DE NIMALIS.md` no Obsidian;
5. só depois avançar para lote 2 de notas.

## Estado dos 7 pontos pedidos

| Ponto | Estado | Observação |
|---|---|---|
| 1. Thumbnail aparecendo como caminho | Resolvido tecnicamente | `Home.md` agora usa HTML no Dataview para renderizar `thumbnail` como imagem. |
| 2. Recriar mapa de Earthropo | Feito | `MAPA DE EARTHROPO.md` foi recriado como mapa continental. `MAPA DE NIMALIS.md` fica como mapa urbano/capital. `MAPA DE NIMALIA.md` não deve voltar como terceiro mapa operacional, salvo decisão contrária. |
| 3. Ajustar mapa/Leaflet de Nimalis | Feito | Configuração do Leaflet passou a apontar para `zz_media/mapa-de-nimalis.png`, não para `zz_media/nimalia.png`. |
| 4. Guerreiro no lugar de Homem de Armas | Feito | `Guerreiro` é a classe operacional. `Homem de Armas` deve ficar apenas como referência histórica, se necessário. |
| 5. Criar notas correspondentes | Parcialmente feito | Criadas notas para `Criadores` e `Vampiro Sanguinallis`; outras ainda dependem de decisão/lista abaixo. |
| 6. Pente fino | Em andamento | Links e mídias operacionais principais foram verificados; ainda há pendências narrativas e arquivos antigos para decidir. |
| 7. Lista completa de pendências | Este relatório | Pendências separadas por decisão do Sage, ajuste técnico e validação visual. |

## Validações executadas

### Frontmatter operacional

Foi feita uma validação customizada nos arquivos operacionais principais, ignorando a limitação do validador antigo.

Resultado:

| Métrica | Resultado |
|---|---:|
| Arquivos operacionais com frontmatter válido | 121 |
| Arquivos operacionais sem frontmatter | 0 |
| Arquivos operacionais com frontmatter quebrado | 0 |

Observação: `.local-tools/validate_frontmatter.py` foi corrigido para validar frontmatter com mais de 10 linhas e ignorar documentação interna no modo operacional.

### Mídia operacional

Foi feita uma validação customizada para embeds, HTML `src` e campos YAML como `thumbnail`, `cover` e `banner`.

Resultado:

| Métrica | Resultado |
|---|---:|
| Referências de mídia operacionais encontradas | 181 |
| Referências resolvidas | 181 |
| Referências quebradas | 0 |

Observação: `.local-tools/validate_media.py` foi corrigido para resolver `zz_media/`, embeds, HTML e campos YAML. Ainda há 36 mídias possivelmente órfãs para revisão futura, mas nenhuma referência operacional quebrada.

### Wikilinks operacionais

| Métrica | Resultado |
|---|---:|
| Wikilinks operacionais encontrados | 759 |
| Wikilinks resolvidos | 759 |
| Wikilinks quebrados | 0 |

### Homes e vazamento operacional

Busca em `Home.md`, `Home_Mestre.md` e `Templates` não encontrou:

- `Home_Jogadores`;
- `player_known`;
- `life_status`;
- `handout_image`;
- `#session`;
- `Workflow/Legacy/Disgraceland`;
- `TRIBUCIA`;
- `Disgraceland`.

Ocorrências antigas ainda existem em relatórios de auditoria e arquivos históricos, mas não na navegação operacional principal.

## Pendências que precisam de decisão do Sage

> [!IMPORTANT]
> As decisões já aplicadas nesta rodada estão registradas na seção “Decisões do Sage aplicadas neste pente fino”.
> Se alguma linha antiga abaixo parecer pedir confirmação de algo já decidido, considerar a decisão aplicada como fonte mais recente.
> As pendências realmente abertas são as que ainda indicam refinamento futuro, como fronteiras exatas, nomes de reinos racializados, detalhes de casas nobres, estado atual do Clã Sanguinallis e balanceamento final de regras.

### Geografia e mapas

| Pendência | Decisão necessária | Risco se ignorar |
|---|---|---|
| Mapas oficiais | Confirmar que ficam apenas `MAPA DE EARTHROPO.md` e `MAPA DE NIMALIS.md`. | Voltar a ter 3 mapas concorrentes: Earthropo, Nimalia e Nimalis. |
| `MAPA DE NIMALIA.md` | Confirmar remoção definitiva da raiz operacional. | Reaparecer como mapa oficial confuso. |
| `zz_media/nimalia.png` | Confirmar remoção/aposentadoria da imagem antiga. | Leaflet ou notas antigas podem voltar a apontar para imagem errada. |
| Fronteiras de Nimalia | Definir limites aproximados do reino no continente. | Dificulta pins, facções, viagens e conflitos geopolíticos. |
| Nimalis | Confirmar bairros, função urbana, porto, nobreza, população e relação com a Coroa. | Capital fica visualmente criada, mas narrativamente oca. |
| Avenor | Confirmar se é floresta/região fronteiriça fora de Nimalia ou parcialmente conectada. | Leth'valora, Sentinelas e Vezemir podem se contradizer. |
| Gharok | Posicionar aproximadamente no mapa e decidir se é fortaleza anã, ruína ou domínio ativo. | Afeta anões, norte/nordeste, montanhas e ganchos. |
| Valthor | Confirmar sudeste de Earthropo e natureza das ruínas. | Afeta Raziel e a linha antiga/vampírica. |
| Região de Raziel | Escolher onde fica a origem/prisão/tormento de Raziel. | Pode contradizer Valthor, Sangue Antigo e Sanguinallis. |
| Reinos racializados | Posicionar, mesmo que em rascunho, regiões élficas, anãs e outras. | Jogadores podem perguntar “onde ficam os povos?” e o vault ainda não sustenta. |

### Personagens

| Pendência | Decisão necessária | Risco se ignorar |
|---|---|---|
| `Theron Elensar.md` | Confirmar se continua removido, volta como NPC, ou vai para archive. | Links/documentos antigos podem ficar sem destino narrativo. |
| Varkh — classe | Confirmar se a ficha operacional dele é `Alquimista`, `Ladrão`, híbrido narrativo, ou outra coisa. | Contradição entre história, mecânica e nota de classe. |
| Varkh — afiliação | Confirmar se ele pertence ao `Conclave dos Errantes`, tem vínculo indireto, ou não tem facção. | Home/DataCards podem agrupá-lo na facção errada. |
| Varkh — idade e origem | Revisar idade e origem com o jogador. | Contradição de timeline. |
| Raziel — natureza | Confirmar como `Vampiro Sanguinallis`, `Sangue Antigo`, hemomancia e classe mecânica convivem. | Pode quebrar tom e balanceamento de mesa. |
| Raziel — antiguidade | Confirmar a versão “mais de 300 anos” como cânone. | Timeline pode oscilar entre versões antigas e novas. |
| Vezemir — poderes | Confirmar como Força Arcana/Velocidade aparecem no nível 1 sem virar vantagem solta. | Pode gerar precedente mecânico difícil de controlar. |
| Mira Valen | Confirmar sobrenome, papel como filha do chefe de Leth'valora e estado atual. | Afeta motivação de Vezemir e política local. |
| Mestre Odran Veyl | Confirmar se a imagem `mestre-odran.jpeg` é definitiva. | Nota já está apontando para ela. |
| Dragão de Colar Dourado | Confirmar natureza, nome e relação com o ataque a Leth'valora. | É eixo forte de Vezemir; precisa ser consistente. |

### Facções e lore

| Pendência | Decisão necessária | Risco se ignorar |
|---|---|---|
| Criadores | Definir quanto é cânone público, segredo do mestre ou mito distorcido. | O mistério pode aparecer cedo demais. |
| Véu Cinzento | Definir se é plano, fenômeno, ordem, entidade ou metáfora. | Várias notas usam o termo de formas diferentes. |
| Guardiões do Véu Cinzento | Confirmar papel como facção ativa, antiga ordem ou culto. | Pode confundir com Sentinelas e com o Dragão. |
| Sentinelas de Leth'valora | Confirmar se são antigos guardiões da vila, ordem atual ou memória histórica. | Tag `sentinelas-de-lethvalora` já substitui `third`. |
| Nobreza de Nimalia | Confirmar se será facção operacional ampla. | Tag `nobreza-de-nimalia` já substitui `murray`. |
| Conclave dos Errantes | Confirmar escopo: guilda de aventureiros, ordem viajante, mercenários ou rede informal. | Afeta Varkh, Vezemir e estrutura de quests. |
| Guilda dos Mercadores | Confirmar se é facção forte de Nimalia ou apenas estrutura econômica. | Afeta economia, rotas e Maré Baixa. |
| Clã Sanguinallis | Confirmar relação com Raziel, Sangue Antigo e Vampiro Sanguinallis. | Pode virar lore paralela sem integração. |

### Itens

| Pendência | Decisão necessária | Risco se ignorar |
|---|---|---|
| `Items/O Medalhão.md` | Confirmar título final: `O Medalhão` ou `O Medalhão dos Guardiões do Véu Cinzento`. | Nome do arquivo e título interno podem divergir. |
| Arquivo antigo do medalhão | Confirmar remoção de `Items/O Medalhão dos Guardiões do Véu Cinzento.md`. | Duplicidade de item. |
| Grisalma | Confirmar se a imagem e o conteúdo atual são definitivos. | Item já entrou no micro-piloto. |
| Muralha de Dorn | Confirmar se é item, local, artefato ou lenda. | Atualmente pode aparecer como item, mas o nome sugere algo maior. |

### Mecânica / Old Dragon

| Pendência | Decisão necessária | Risco se ignorar |
|---|---|---|
| Classes oficiais | Confirmar lista operacional: Guerreiro, Clérigo, Mago, Ladrão, Alquimista etc. | Templates/classes podem divergir dos personagens. |
| `Homem de Armas` | Confirmar remoção operacional definitiva. | Voltar como classe duplicada de Guerreiro. |
| Raças | Confirmar lista de raças jogáveis/canônicas para Earthropo. | Personagens e população de Nimalia/Avenor podem contradizer. |
| Antropos | Definir se “antropos” é raça, conjunto de beastfolks ou termo cultural. | Nimalia depende disso. |
| Humanos | Confirmar regra: humanos são maioria em Old Dragon, mas em Nimalia antropos são dominantes. | Evita contradição entre sistema e reino. |

## Pendências técnicas que posso resolver sem decisão narrativa

| Tarefa | Status | Observação |
|---|---|---|
| Corrigir `.local-tools/validate_frontmatter.py` | Feito | O limite de 10 linhas foi removido. |
| Corrigir `.local-tools/validate_media.py` | Feito | Agora resolve `zz_media/`, embeds, HTML e campos YAML comuns. |
| Corrigir `.local-tools/validate_links.py` | Feito | Agora ignora embeds de mídia e resolve caminhos de notas com normalização básica. |
| Atualizar `Workflow/Reports/latest_vault_audit.md` | Pendente | Está histórico/desatualizado e ainda lista falsos problemas. |
| Separar commits | Pendente | Há muitas mudanças locais; ideal é commitar por tema. |
| Verificar `.obsidian/snippets/supercharged-links-gen.css` | Pendente | Parece alteração pequena de newline; não incluir sem confirmar. |
| Validar visualmente DataCards da Home | Pendente | Precisa abrir no Obsidian para confirmar renderização de imagem. |
| Validar Leaflet no Obsidian | Pendente | Confirmar se `MAPA DE EARTHROPO.md` e `MAPA DE NIMALIS.md` renderizam. |
| Atualizar relatórios históricos com aviso | Pendente | Alguns relatórios ainda mencionam Disgraceland como achado antigo. |
| Padronizar `Characters/Individual` | Próximo passo recomendado | Usar `Vezemir.md` como referência, sem mexer pesado em atributos. |
| Padronizar conteúdo ligado a `EARTHROPO/` | Próximo passo recomendado | Já existe relatório em `Workflow/_audit/Earthropo_Standardization/`. |

## Arquivos alterados/deletados que precisam de confirmação antes de commit

| Arquivo | Estado no Git | Recomendação |
|---|---|---|
| `MAPA DE NIMALIA.md` | Deletado | Confirmar remoção operacional. |
| `zz_media/nimalia.png` | Deletado | Confirmar aposentadoria da imagem antiga. |
| `Classes/Homem de Armas.md` | Deletado | Confirmar remoção operacional; `Guerreiro` fica oficial. |
| `Characters/Individual/Theron Elensar.md` | Deletado | Confirmar se sai mesmo ou se deve ir para archive. |
| `Items/O Medalhão dos Guardiões do Véu Cinzento.md` | Deletado | Confirmar se foi substituído por `Items/O Medalhão.md`. |
| `Items/O Medalhão.md` | Novo | Revisar título interno e lore mínima antes de commit. |
| `Lore/Criadores.md` | Novo | Revisar nível de segredo/cânone. |
| `Lore/Vampiro Sanguinallis.md` | Novo | Revisar relação com Raziel e Clã Sanguinallis. |
| `MAPA DE NIMALIS.md` | Novo | Validar visualmente no Leaflet. |
| `zz_media/culture.png` | Novo | Confirmar uso definitivo em `CULTURE.md`. |
| `zz_media/mestre-odran.jpeg` | Novo | Confirmar uso definitivo em `Mestre Odran Veyl.md`. |
| `zz_media/sangue.png` | Novo | Confirmar uso em Sanguinallis/Sangue Antigo. |
| `zz_media/vila-de-leth'valora.png` | Novo | Confirmar uso em `Locations/Leth'valora.md`. |

## Estado específico de `EARTHROPO/`

Existe relatório dedicado em:

- `Workflow/_audit/Earthropo_Standardization/EARTHROPO_STRUCTURE_STANDARDIZATION_REPORT.md`

Resumo do estado:

- `EARTHROPO/EARTHROPO.md` foi estruturado como página-motor do continente;
- as crônicas foram alinhadas como `story`/origem, sem criar `sessions`;
- DataCards foram ajustados para não puxar `Workflow/`;
- Earthropo está tratado como continente;
- Nimalia está tratada como reino;
- Nimalis está tratada como capital;
- Leth'valora está tratada como vila de Avenor;
- Raziel foi mantido com antiguidade de mais de 300 anos;
- pendem Mar da Neblina, Gharok, fronteiras e relação Criadores/Véu/Dragão/Sangue Antigo.

## Riscos restantes

| Risco | Gravidade | Como evitar |
|---|---|---|
| Commitar tudo junto | Alta | Separar commits: Home/mapas, personagens, Earthropo, imagens, relatórios. |
| Resolver lore no automático | Alta | Tudo que muda motivação, origem, facção ou cosmologia precisa confirmação. |
| Voltar `MAPA DE NIMALIA.md` | Média | Manter só Earthropo + Nimalis, salvo decisão contrária. |
| Validador local gerar pânico falso | Média | Corrigir scripts antes de usar números como verdade. |
| Templates puxarem Workflow/relatórios | Média | Manter filtros `!contains(file.path, "Workflow/")`. |
| Imagem aparecer como texto em DataCards | Baixa/Média | Usar HTML em Dataview ou DataCards com `imageProperty` correto. |
| Duplicar classe Guerreiro/Homem de Armas | Média | Manter `Homem de Armas` apenas histórico. |
| Varkh/Raziel ficarem mecanicamente indefinidos | Alta | Decidir classe e natureza antes de ficha final. |

## Próxima ordem recomendada

1. Sage confirma os itens críticos: mapas oficiais, remoções deletadas, Varkh, Raziel, Theron, Medalhão.
2. Corrigir os validadores locais para parar de produzir falsos positivos.
3. Fazer commits separados das correções já aplicadas.
4. Padronizar `Characters/Individual` com base em `Vezemir.md`.
5. Validar visualmente `Home.md`, `Home_Mestre.md`, `EARTHROPO/EARTHROPO.md`, `MAPA DE EARTHROPO.md` e `MAPA DE NIMALIS.md`.
6. Padronizar notas diretamente ligadas a Earthropo/Nimalia/Avenor.
7. Só então executar o próximo lote real de notas.
