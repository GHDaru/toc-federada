# Fixture `acao-de-catalogo` — base VÁLIDA mínima de `scripts/check-acao-de-catalogo.sh`

Dois arquivos com a **forma** que o portão inspeciona, e só ela: um catálogo com três
ações (uma da Árvore da Realidade Atual, uma do projeto genérico, uma sem ferramenta) e
um executor com a tabela de despacho, o construtor que monta os casos de uso e as mãos
que os acionam.

Não é código executável nem uma cópia do serviço: o portão é uma leitura **estática**
(árvore sintática abstrata, AST) de dois arquivos, e o fixture existe para que as
sabotagens o derrubem em terreno controlado — sem tocar o serviço de verdade. As
sabotagens estão em `scripts/tests/run-sabotagem.sh`.
