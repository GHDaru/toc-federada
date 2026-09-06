# Fixture `jornadas` — base VÁLIDA do portão `scripts/check-jornadas.sh`

Uma jornada, uma captura citada uma vez, um manifesto com data e um gerador que existe.
Nada aqui descreve sistema real: a jornada é sintética e a imagem é um PNG de 1×1 pixel.

A base tem de sair **verde**; as sabotagens declaradas em `scripts/tests/run-sabotagem.sh`
mutam uma cópia dela e cada uma tem de sair **vermelha pelo motivo declarado**:

| Sabotagem | O que planta | Invariante |
|---|---|---|
| `jornada-captura-orfa` | uma captura em disco que nenhuma jornada cita | J1 |
| `jornada-imagem-citada-inexistente` | apaga o arquivo que a jornada cita | J2 |
| `jornada-sem-heuristica-datada` | tira a data do cabeçalho da avaliação | J3 |
| `jornada-heuristica-mais-velha-que-a-captura` | data da heurística anterior à das capturas | J3 |
| `jornada-sem-comando-de-regeneracao` | tira o comando que regenera as capturas | J4 |
