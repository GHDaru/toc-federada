# ADR 0011 — A confirmação de proposta é uma transição atômica no banco, e a `idempotency_key` deduplica de verdade

- **Status**: Aceita
- **Data**: 2026-09-06 · **Ciclo**: 008 (segundo defeito grave achado por crítico hostil,
  no mesmo ciclo que instalou a trava do agregado Projeto)
- **Decisor**: agente construtor sob a regra R3 (ação reversível de baixo raio), com a
  quarta condição acionada — a decisão **acrescenta um código ao registro de erros da
  fronteira** (`IDEMPOTENCY_KEY_REUSED`), que é contrato com o cliente, e **muda o
  comportamento observável da confirmação repetida**, que é o APH-5.3 (Padrão APH —
  Aplicação ↔ Harness). As duas coisas são externas; por isso isto está escrito e
  argumentado contra a norma, e não apenas executado.
- **Sucede**: nenhum
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — "verbo mutador nasce `action_proposal`",
  e é exatamente essa garantia que o defeito quebrava: uma proposta confirmada uma vez
  executava N. O acréscimo de código entra no **mesmo registro único** que a fronteira já
  usa (`apps/api/src/toc_api/dominio/federacao/wire.py`), sob a permissão literal do §A.7
  do Anexo A ("PODE adicionar os seus", desde que documentados); nenhum segundo registro
  nasce aqui. Toca também o **Princípio III do Maestro (INEGOCIÁVEL)** — "gate humano
  proporcional ao risco" —, porque um gate humano multiplicável por uma corrida não é um
  gate; **P4** (o conserto começou pelo teste que reproduz, contra o PostgreSQL real);
  **P3** (a trava é do adaptador, a recusa é do domínio, a **ordem** é da aplicação); e
  **P5** (nada de novo a instrumentar: o traço já existia e voltou a contar uma execução
  por execução, que é o que ele afirmava contar).

## Contexto

O ADR 0010 instalou a trava otimista do agregado **Projeto** e fechou a perda de
atualização do Núcleo de Diagramas Lógicos (M1), da Árvore da Realidade Atual (M2) e da
Nuvem de Conflito (M3). Quem o instalou **declarou por escrito que a proposta de ação
ficara de fora**, como pendência. Um crítico hostil confirmou que a pendência era real, e
reproduziu:

```text
proposta `toc.criar_nos` com 30 alvos em `awaiting_approval`;
oito confirmações simultâneas do MESMO proposal_id, com a MESMA idempotency_key
→ {200: 8} · 49 nós para 30 pedidos · 13 títulos repetidos
→ OITO linhas de traço para uma proposta só.  Estável em oito repetições.
```

Reproduzido de novo aqui, em
`apps/api/tests/integracao/test_corrida_de_confirmacao_no_postgres.py`, antes de qualquer
linha de conserto — a saída colada do vermelho:

```text
corrida de confirmação · chave única · códigos {200: 8} · nós no banco 50 para 30 pedidos
  · títulos repetidos 22 · linhas de traço 8 · linha no banco: estado=failed execucoes=1
corrida de confirmação · sem chave · códigos {200: 8} · nós no banco 49 · linhas de traço 8
corrida de recusa · códigos {200: 8} · nós no banco 0
  · linhas de traço ['denied', 'denied', 'denied', 'denied', 'denied']
```

É grave por dois motivos **somados**. Quebra a deduplicação que o próprio padrão exige —
APH-5.3: *"a confirmação DEVERIA carregar `idempotency_key` com deduplicação real, isto é:
a mesma chave produz uma execução e quantas respostas idênticas forem pedidas"*. E
multiplica por uma corrida o **portão humano**, que o método trata como inegociável: uma
pessoa aprovou uma vez e o sistema executou oito.

## Diagnóstico: por que a máquina de estados não impediu

A pergunta é a que decide o conserto, e a resposta tem três partes, cada uma verificada no
código antes de escrever esta linha.

**1. A máquina de estados finitos (FSM) guardava o objeto, não a linha.**
`RepositorioDePropostasSQL.obter` reidrata um `PropostaDeAcao` **novo** a cada chamada, e
`transicionar` consulta `self.estado`, que é atributo de memória. Oito confirmações
simultâneas leem oito agregados, todos em `awaiting_approval`, e as oito transições
`awaiting_approval → confirmed → executing` são legítimas — cada uma no seu objeto. Havia
**uma linha e N agregados**; a tabela de transições nunca chegou a ver um conflito.

**2. A gravação era incondicional e vinha DEPOIS do efeito.** `salvar` era
`insert_pg(...).on_conflict_do_update(index_elements=["proposal_id"], set_=atualizaveis)`:
sobrescrevia `estado` fosse qual fosse o da linha, e não havia em `PropostaDeAcao` nada
equivalente a `Projeto.versao_lida` para condicionar nada. Pior: em
`DecidirProposta.executar`, `self._executar(...)` rodava **antes** de
`self._propostas.salvar(...)`. Mesmo uma escrita condicionada ali chegaria tarde — os 30
nós já estariam no banco quando a corrida se resolvesse. A prova está na própria linha do
banco depois do ataque: `estado=failed execucoes=1` **depois de oito execuções**, porque o
último a gravar escreveu o retrato dele por cima de tudo.

**A resposta, então:** a transição `confirmed → executing` **é** a serialização natural do
APH-5.1 — mas só quando ela existe **no banco e antes do efeito**. Enquanto ela fosse uma
atribuição a um atributo Python seguida de uma escrita posterior, ela serializava
exatamente nada.

**3. A `idempotency_key` era gravada e nunca consultada.** A coluna existe desde a migração
0004; `PropostaDeAcao.confirmar` a atribuía; e `grep -rn "idempotency_key"` mostrava
**apenas escritas** — o único leitor era `mesma_chave`, chamado só por um teste de domínio.
A deduplicação que existia era `decisao_ja_tomada` (RF-16), que exige o agregado já
terminal: serve para a repetição **sequencial** e não pode servir para a **concorrente**,
porque nenhum dos oito leitores tinha agregado terminal.

## Decisão

**1. A proposta passa a saber de que estado partiu.** `PropostaDeAcao.estado_lido`, com
`confirmar_gravacao()`, exatamente como `Projeto.versao_lida`. Não entra no construtor nem
na comparação: é estado de **sincronia com o repositório**, não de negócio.

**2. A gravação condiciona-se a ele.**
`UPDATE proposta_de_acao SET … WHERE proposal_id = :id AND tenant_id = :inq AND estado = :estado_lido`.
`rowcount == 0` relê o estado atual e levanta `CorridaDeDecisao`, que carrega
`estado_lido` e `estado_atual`. O bloqueio de linha do PostgreSQL faz a serialização: a
segunda escrita espera a primeira comitar, refaz o predicado sob READ COMMITTED, não casa
mais.

**3. A reserva acontece ANTES do efeito — e esta é a peça central.** `_reservar` grava
`executing` no banco entre a transição e a primeira chamada ao executor. **Quem não
escreve, não executa.** É a única das cinco peças cuja ausência é invisível numa varredura
de texto: a trava continuaria toda lá, correta, e inútil. Por isso o portão deste ADR
compara **números de linha**, e há uma sabotagem que só move a reserva de lugar.

**4. A chave de idempotência deduplica de verdade (APH-5.3).** Índice único **parcial** por
`(tenant_id, idempotency_key)` (migração 0007 — parcial porque a chave é opcional no §A.6 e
`NULL` não colide com `NULL`; por inquilino porque a chave é do cliente daquele inquilino).
A aplicação passa a **ler** a chave: a confirmação repetida com a mesma chave devolve o
desfecho da que venceu, sem reexecutar e sem novo traço, esperando por ela se ainda estiver
executando (`aguardar_desfecho`, limite declarado de 6 s).

**Sem chave, o perdedor recebe `409 INVALID_TRANSITION` — e é a resposta certa.** Quem não
pediu deduplicação recebe a verdade da FSM: a proposta não está mais em
`awaiting_approval`, e a decisão que executou não foi a dele. É isso que faz a chave
*significar* alguma coisa, que é literalmente o que o APH-5.3 quer dizer ao colocá-la
"além da proteção que a FSM já dá". Não é código novo: `INVALID_TRANSITION` é do registro
**mínimo** do §A.7, e a situação que ele nomeia é exatamente esta.

**5. Recusar também é decidir, e também reserva.** Fechar só a confirmação fecharia o caso
e não a classe: oito recusas simultâneas deixavam cinco linhas de traço `denied` para uma
decisão só. `negar` passa pela mesma escrita condicionada.

**6. O duplo em memória recebeu a mesma trava — e passou a devolver cópia.** O duplo
entregava o **objeto guardado** em `obter`, então dois leitores recebiam o mesmo agregado e
a corrida ficava invisível: o duplo mentia para melhor, e a suíte de contrato inteira roda
sobre ele. Além disso, `RepositorioDePropostasFalso` dos testes passou a **herdar** o duplo
de produção, para não haver terceira permissividade.

**7. Um código próprio, com motivo declarado: `IDEMPOTENCY_KEY_REUSED` (409).** É o caso da
chave reaproveitada em **outra** proposta do mesmo inquilino, que o índice único agora
recusa. `INVALID_TRANSITION` mandaria o cliente recarregar a proposta, quando o que ele tem
de fazer é sortear outra chave; `details` carrega `idempotency_key` e `proposal_id`, porque
o cliente discrimina por código e por dado, nunca por mensagem.

> **Nota de contagem, e por que ela está aqui e não no ADR 0010.** Com este acréscimo,
> `CODIGOS_PROPRIOS` tem 25 linhas com esta, e o registro inteiro, com o mínimo normativo,
> tem 32 códigos). O ADR 0010 escreveu 24 e 31, com honestidade na data dele. O corpo de um
> ADR não se reescreve
> (é a regra do método, e há guarda que a impõe): o número do 0010 é o número daquela
> decisão, e é este ADR que passa a carregar o número corrente — a aptidão
> `scripts/check-evidencia-colada.sh` foi reapontada para cá, e é ela que cobra a conta
> daqui em diante.

**8. Um portão com sabotagem própria.** `scripts/check-trava-da-proposta.sh` confere as
seis peças mais a classe inteira dos caminhos de escrita persistente, e
`scripts/tests/run-sabotagem.sh` prova, com **10** mutações, que ele reprova quando
qualquer uma sai.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| **Manter a transação da reserva aberta durante o efeito** (o perdedor bloqueia em `SELECT … FOR SHARE` e acorda com o desfecho pronto, sem espera ativa) | Elegante e sem *polling*, mas segura um bloqueio de linha pelo tempo inteiro da execução de um lote de 30 alvos, com o efeito rodando **noutra conexão**. É transação longa com dependência entre sessões — o caminho conhecido para esgotar o pool. Trocamos a elegância por um limite declarado (6 s) e visível |
| **Deduplicar só pela FSM, sem tocar na chave** | Resolveria a execução múltipla e deixaria o APH-5.3 como estava: uma coluna gravada que ninguém lê. O crítico apontou os dois defeitos porque são dois |
| **Devolver o desfecho do vencedor também a quem não mandou chave** | Uniformiza a resposta e apaga a diferença entre "eu decidi" e "outra pessoa decidiu igual". Some com a única informação que a corrida produz, e esvazia a chave de sentido |
| **Chave única global, sem inquilino** | Duas instituições que sorteiem o mesmo identificador não são a mesma decisão; seria vazamento de existência entre inquilinos, contra a fronteira que todo o resto do serviço mantém |
| **Serializar no processo (um `Lock` em memória)** | Só vale dentro de uma réplica. A aplicação nasce para rodar em Railway com mais de uma; um cadeado de processo daria verde na suíte e nada em produção |

## Consequências

- **Boas.** Uma aprovação humana executa uma vez, medido: 30 nós para 30 pedidos, zero
  títulos repetidos, **uma** linha de traço, `execucoes = 1`. A mesma chave devolve a mesma
  resposta oito vezes. A auditoria volta a contar o que aconteceu.
- **Custo aceito.** Uma escrita a mais por decisão (a reserva) e uma espera possível de até
  6 s para quem perdeu a corrida **com chave**. As duas são o preço de a decisão ser
  atômica; sem elas o efeito precede a serialização.
- **Dívida declarada.** A sessão de conversa (`SessaoDeConversa`, com o `seq` monotônico do
  §A.1) continua **em memória e por processo**, por decisão já registrada no cabeçalho de
  `apps/api/src/toc_api/infra/federacao/memoria.py`. Enquanto for uma réplica só, ela não é da classe deste ADR
  — não há linha a disputar. No dia de duas réplicas, a sessão precisa de armazenamento
  compartilhado e **entra nesta mesma classe**, com trava e portão próprios.

## Verificação

| O que | Como |
|---|---|
| A corrida não executa duas vezes | `apps/api/tests/integracao/test_corrida_de_confirmacao_no_postgres.py` — 8 fios, barreira, PostgreSQL real |
| A trava é regra e não disciplina | `apps/api/tests/federacao/test_trava_da_proposta.py` e `apps/api/tests/federacao/test_paridade_do_repositorio_de_propostas.py` |
| O portão vê o defeito | `scripts/check-trava-da-proposta.sh` + as 10 sabotagens de `scripts/tests/run-sabotagem.sh` |
| O índice único chega ao banco | `apps/api/src/toc_api/alembic/versions/0007_dedup_real_da_chave_de_idempotencia.py` e o teste de deriva de esquema |
