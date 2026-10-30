# Imagens dos protocolos e passivas de Dorn — 2026-10-08

Imagens originais importadas pelo endpoint autenticado do Mestre, categoria items, com ícones compactos e imagens nos detalhes flutuantes:

| Ficha | Imagem |
| --- | --- |
| Protocolo de Guarda | `zz_media/ui/icons/uploads/protocolo_guarda_e51a549b42.jpg` |
| Protocolo de Vanguarda | `zz_media/ui/icons/uploads/protocolo_vanguarda_2c8a61c1c8.jpg` |
| Forma Imutável | `zz_media/ui/icons/uploads/forma_imutavel_8ca8772cb2.jpg` |
| Corpo Artificial | `zz_media/ui/icons/uploads/corpo_artificial_a3e38666fb.jpg` |

Removidos os textos visíveis “Posição permite interposição”, “gastar ação” do botão e “Exploração · até desativar ou encerrar cena”. A confirmação de posição continua acessível no checkbox com nome “Confirmar posicionamento para Guarda”; não há confirmação automática, alteração no custo da ação, duração ou permissões.

Arquivos: `frontend/src/components/DornProtocolControls.tsx`, `frontend/src/components/DornConstructDetails.tsx`, testes de protocolos e fixture visual de Dorn. Não alterados dados de PV, recursos ou inventário da campanha.

Checks: suíte backend completa, suíte frontend, TypeScript, build, renderer React real com CSS em 390×844 e 1440×900 (quatro imagens nos diálogos, rótulos removidos, ações mantidas, sem overflow). Verificação automatizada não substitui mesa multicliente. Sem commit/push ou reinício do backend.
