# Fixture `raiz-do-agregado` — base VÁLIDA mínima de `scripts/check-raiz-do-agregado.sh`

Um esqueleto de fonte com a forma que o portão inspeciona, e só ela: o `Projeto` do M1
(Núcleo de Diagramas Lógicos) com as oito guardas `_exigir_raiz`, as duas raízes de
ferramenta se registrando, um caso de uso da camada de aplicação que **não** toca a chave
`sob_a_raiz`, e um teste de domínio (que é a exceção declarada do portão).

Não é código executável: o portão é uma varredura de texto sobre o layout, e o fixture
existe para que as sabotagens o derrubem em terreno controlado — sem tocar o serviço de
verdade. As sabotagens estão em `scripts/tests/run-sabotagem.sh`.
