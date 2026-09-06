# Fixture `trava-otimista` — base VÁLIDA mínima de `scripts/check-trava-otimista.sh`

Um esqueleto de fonte com a forma que o portão inspeciona, e só ela: o adaptador SQL
(*Structured Query Language*) com as três portas de escrita passando pela trava, o duplo
em memória com a mesma recusa, o agregado com `versao_lida` e `confirmar_gravacao`, o
registro do §A.7 do Anexo A do Padrão APH (Aplicação ↔ Harness) declarando
`VERSION_CONFLICT`, e a borda HTTP (*HyperText Transfer Protocol*) emitindo-o com os dois
números no `details`.

Não é código executável: o portão é uma varredura de texto sobre o layout, e o fixture
existe para que as sabotagens o derrubem em terreno controlado — sem tocar o serviço de
verdade. As sabotagens estão em `scripts/tests/run-sabotagem.sh`, e cada uma reabre uma
peça da correção: a escrita sem `WHERE versao =`, a reidratação sem `versao_lida`, o
`rowcount` ignorado, um caminho de escrita fora da trava, o duplo em memória mais
permissivo que o banco, e o código de erro fora do registro.
