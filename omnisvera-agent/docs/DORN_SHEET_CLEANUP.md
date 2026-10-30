# Ajuste da ficha de Dorn — 2026-10-08

- Removido da ficha o bloco de Diagnóstico, incluindo dificuldade, teste de INT e mensagem “Protocolo atualizado”. O endpoint histórico não foi apagado.
- Traços visíveis: somente Forma Imutável, Mente Artificial e Corpo Artificial. Nenhuma imunidade ou regra foi removida do backend.
- Guarda e Vanguarda usam SpellCard, o mesmo heading/summary do inventário; removidos os textos solicitados e o rótulo Aliado. Permissões, turno, posição e interposição permanecem.
- Removida a explicação “Base 10 · DES -1 · Escritas Rúnicas +2”, sem alterar CA.
- Reparo aparece nos consumíveis, não como habilidade duplicada. O item interno continua Kit de Reparo (session-item:15), com quantidade preservada em 5. Consome um kit, cura 1d4 PV até o máximo; operação idempotente e exclusiva do Mestre. Nenhum kit da campanha foi gasto nos testes.
- Cadastro do kit corrigido para consumível sem dano/slots de arma. Normalização não infere dados de cura de consumíveis como dano de arma.
- Imagens originais: `zz_media/ui/icons/uploads/reparo_d39ac13bb7.png` e `zz_media/ui/icons/uploads/mente_artificial_6180e87c7a.png`. Reparo usa associação persistente do item; Mente usa apresentação da passiva, com imagem no detalhe flutuante.

Arquivos: `DornConstructDetails.tsx`, `DornProtocolControls.tsx`, `SessionWorkspace.tsx`, `styles.css`, `player_inventory.py`, testes de protocolos/padrão/normalização e fixture visual de Dorn. Cadastro operacional atualizado via API autenticada do Mestre.

QA: 393 testes backend e 161 frontend aprovados, TypeScript e build aprovados; fixture React real com CSS em 390×844 e 1440×900 (dois cards, três passivas, abertura da imagem, protocolos, sem overflow). Imagens idênticas aos anexos (SHA256). Não equivale a validação de mesa multicliente em redes distintas. Sem commit/push.
