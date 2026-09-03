# Rounds sintéticos — base válida da sabotagem de `check-rounds.sh`

Base 100% sintética (ADR 0006 — Registro de Decisão Arquitetural nº 6). Persona:
**Facilitadora TOC** (Teoria das Restrições) da "Instituição Horizonte". Nada aqui é
planejamento real do produto: é a entrada verdadeira que o portão precisa ter para provar
que sabe reprovar a entrada falsa.

## Round 002 — Primeiro round sintético

- **Apetite**: um ciclo do método.
- **Entrega**: a coisa mínima que o round entrega, escrita como entrega e não como tarefa.
- **Fora**: tudo o que parece caber e não cabe neste apetite.
- **Aptidão executável**: um comando que responde verde ou vermelho sem julgamento humano.
- **Depende de**: nenhum
- **Sai primeiro**: o item de menor valor. **Nunca sai**: o item que dá sentido ao round.
- **Defeitos**: **D-01** (o defeito sintético alocado morre aqui).

## Round 003 — Segundo round sintético

- **Apetite**: um ciclo do método.
- **Entrega**: a continuação mínima do 002.
- **Fora**: o que pertence a rounds posteriores.
- **Aptidão executável**: outro comando verde/vermelho.
- **Depende de**: 002
- **Sai primeiro**: o acessório. **Nunca sai**: o essencial.
- **Defeitos**: nenhum — *declaração, não esquecimento*: o D-01 já morreu no round 002.

## Defeitos não corrigidos em round próprio

- **D-02 · Defeito sintético sem round** — não vira round porque o princípio já o cobre em
  todos os rounds; um round de "fazer o que o princípio manda" seria admitir a violação.

Conferência de exaustividade: D-01 (002) · D-02 (não corrigido em round, motivo acima).
**Dois defeitos, dois destinos, nenhum em dois lugares.**
