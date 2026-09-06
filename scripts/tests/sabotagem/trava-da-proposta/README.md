# Fixture `trava-da-proposta` — base VÁLIDA mínima de `scripts/check-trava-da-proposta.sh`

Um esqueleto de fonte com a forma que o portão inspeciona, e só ela: o agregado da proposta
com `estado_lido` e `confirmar_gravacao`, o adaptador SQL (*Structured Query Language*)
gravando sob `UPDATE … WHERE estado = :estado_lido`, o duplo em memória com a mesma recusa e
com cópia na leitura, o caso de uso **reservando antes do efeito**, o índice único da chave
de idempotência no modelo e em migração, e o registro do §A.7 do Anexo A do Padrão APH
(Aplicação ↔ Harness) declarando `IDEMPOTENCY_KEY_REUSED`.

Não é código executável: o portão é uma varredura de texto (e de **ordem de linhas**) sobre
o layout, e o fixture existe para que as sabotagens o derrubem em terreno controlado — sem
tocar o serviço de verdade.

As sabotagens estão em `scripts/tests/run-sabotagem.sh`, e cada uma reabre uma peça da
correção: a escrita sem `WHERE estado =`, o `rowcount` ignorado, a reidratação sem
`estado_lido`, o **efeito antes da reserva** (a peça central), o duplo em memória sem trava,
o duplo devolvendo o objeto guardado, a chave de idempotência nunca consultada, o índice
único removido, o código fora do registro, e o traço deixando de ser somente-acréscimo.
