# 005 — para `GHDaru/protocolos`: o registro mínimo do §A.7 não tem código para conflito de versão de agregado

> Siglas, uma vez: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **HTTP** —
> *HyperText Transfer Protocol* · **FSM** — *Finite State Machine* (máquina de estados
> finitos) · **TOC** — Teoria das Restrições · **SQL** — *Structured Query Language*.

- **Destino**: `GHDaru/protocolos`
- **Data**: 2026-09-06
- **Commit lido**: `04eca6d4a267358be2e2a583f8ceef22deb137f5` (2026-08-14 — "Instantaneo
  regravado: a obrigacao (e) do APH-5.9 (spec 040)")
- **Estado**: aberta
- **Quem relata**: `GHDaru/toc-federada`, ao consertar uma perda de atualização (*lost
  update*) achada por revisão independente — 20 escritas concorrentes aceitas, 1
  persistida, 19 perdidas em silêncio.

## O achado, em uma frase

O registro mínimo do §A.7 tem código para **conflito de proposta** e nenhum para
**conflito de agregado**: uma aplicação multiusuário que implemente trava otimista precisa
inventar o seu, e cada uma vai inventar um nome diferente — que é exatamente o que um
registro de códigos estáveis existe para impedir.

## Evidência

1. `padrao/anexo-a-wire-format.md:98` — o código mais próximo é da FSM da proposta, não
   do agregado:

   ```text
   | `INVALID_TRANSITION` | confirmação ou transição fora da máquina de estados finitos (FSM) da proposta (APH-5.1) |
   ```

2. `padrao/anexo-a-wire-format.md:102` — o outro candidato é a tela, não o dado:

   ```text
   | 🧪 `PROPOSAL_CONTEXT_STALE` | a tela mudou entre proposta e confirmação (APH-5.4). […]
   ```

3. Nenhuma linha do registro mínimo nomeia "duas escritas concorrentes sobre o mesmo
   recurso". A busca no anexo inteiro, executada:

   ```text
   $ grep -icE 'version.?conflict|conflito de vers|lost update|optimistic' \
       padrao/anexo-a-wire-format.md
   0
   ```

## Consequência

Para **quem escreve a aplicação**: o §A.7 permite códigos próprios ("PODE adicionar os
seus"), então nada é violado — mas a decisão de nome fica com cada implementação. Nós
declaramos `VERSION_CONFLICT`; a fundação, se resolver o mesmo problema, pode declarar
`CONFLICT`, `STALE_VERSION` ou `PRECONDITION_FAILED`. O §A.8 já registra dois casos assim
(`FORBIDDEN` do laboratório B para `UNAUTHORIZED`, `STALE_CONTEXT` do laboratório A para
`PROPOSAL_CONTEXT_STALE`), e cada um deles é um mapeamento a fazer na adoção.

Para **quem escreve o cliente**: o cliente "discrimina por código e nunca por mensagem"
(§A.7). Um cliente federado que trate `VERSION_CONFLICT` numa aplicação e `CONFLICT` em
outra tem de conhecer as duas — e a recuperação é a mesma nas duas (recarregar a versão
atual, reaplicar a intenção, tentar de novo).

Para **quem opera**: esta é a classe de erro mais provável de aplicação federada
multiusuário — mais provável que proposta vencida ou contexto defasado, porque não depende
de assistência nenhuma: duas pessoas na mesma tela bastam.

## Sugestão (separada do achado, para poder ser recusada)

Acrescentar ao registro mínimo do §A.7, com marca 🧪 enquanto houver um emissor só:

| Código | Situação |
|---|---|
| 🧪 `VERSION_CONFLICT` | a escrita partiu de uma versão do recurso que já não é a corrente: outro escritor gravou antes (trava otimista). `details` traz a versão de que a escrita partiu e a versão corrente, para o cliente recarregar e refazer |

O lastro medido, se ele servir para a promoção: `GHDaru/toc-federada`,
`apps/api/src/toc_api/dominio/federacao/wire.py` (declaração) e
`apps/api/src/toc_api/http/erros.py` (emissão em HTTP 409), com o teste de reprodução em
`apps/api/tests/integracao/test_concorrencia_no_postgres.py` — 20 escritas concorrentes
contra PostgreSQL real, 1 aceita, 19 recusadas com o código, e o conjunto das aceitas
igual ao conjunto do que está no banco.

Também vale registrar, se a norma quiser cobrir o par: o `details` com os dois números é o
que separa uma recusa **recuperável pelo cliente** de uma recusa que obriga a pessoa a
recomeçar. Sem eles o cliente volta a ler a mensagem, que é o que o §A.7 proíbe.

## O que NÃO estamos pedindo

Não pedimos mudança em `conformidade/`, nem novo check, nem alteração de nível. O
acréscimo é compatível (código novo, §A.9: "código de erro novo […] sobe a versão MINOR"),
e enquanto ele não existir seguimos com o nosso próprio, **declarado** no registro único do
serviço com o motivo escrito ao lado — que é o que o §A.7 já autoriza hoje.
