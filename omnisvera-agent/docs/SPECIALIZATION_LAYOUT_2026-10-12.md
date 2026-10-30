# Especialização — correção visual

A seção herdava duas divisões de grid: a coluna da ficha e o catálogo de
cards. No desktop, as opções chegavam a 63 px de largura, com texto e
controles sobrepostos.

`SpecializationSection.tsx` agora usa uma classe própria, ocupa as colunas
disponíveis e mantém cada opção em uma coluna. Nome e status têm área
própria; seletor de arma e botão ficam em linhas separadas. Benefícios,
restrições e habilidades futuras abrem no detalhe existente ao clicar no nome.
Não foram alteradas regras, escolhas, fichas nem endpoints.

Verificação na interface compilada com banco temporário: reprodução antes
da correção falhou por overflow; depois passou em 1440×1000, 1024×768 e
390×844, incluindo abertura/fechamento do detalhe. Screenshots foram
inspecionados. Largura dos cards: 290 / 240 / 328 px, sem overflow.

Backend: 550 testes PASS. Frontend: 227 testes PASS; TypeScript PASS;
build PASS. Bundle atualizado `index-BGF0WfWc.js`. Só frontend
alterado; backend operacional permaneceu em execução.

Arquivos: `frontend/src/components/SpecializationSection.tsx`,
`frontend/src/styles.css`, `frontend/tests/specialization-layout-smoke.cjs`
e este documento. Mudanças anteriores nesses arquivos foram preservadas.
Sem commit/push. Aviso de bundle >500 kB permanece.
Fixture usa mídia parcial; os checks visuais certificam esta seção, não todos
os assets do Companion. O backend operacional não foi reiniciado neste corte.
