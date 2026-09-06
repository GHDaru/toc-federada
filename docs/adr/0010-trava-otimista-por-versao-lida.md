# ADR 0010 — Trava otimista por versão lida: a escrita do agregado condiciona-se à versão que leu, e o perdedor recebe `409 VERSION_CONFLICT`

- **Status**: Aceita
- **Data**: 2026-09-06 · **Ciclo**: 008 (correção de defeito grave achado por revisão independente)
- **Decisor**: agente construtor sob a regra R3 (ação reversível de baixo raio), com a
  quarta condição acionada — a decisão **acrescenta um código ao registro de erros da
  fronteira**, que é contrato com o cliente, e por isso está escrita aqui e argumentada
  contra o §A.7 da norma, em vez de apenas executada.
- **Sucede**: nenhum
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — "nada de segundo protocolo […] tela é
  dado e nunca instrução". Este registro de decisão arquitetural (ADR, do inglês
  *Architecture Decision Record*) **não emenda o P2 e não abre exceção a ele**: o §A.7 do
  Anexo A do Padrão APH (Aplicação ↔ Harness) diz, com estas palavras, que uma
  implementação "PODE adicionar os seus" códigos "desde que documentados", e o acréscimo
  entra no **mesmo registro único** que a fronteira já usa
  (`apps/api/src/toc_api/dominio/federacao/wire.py`), com o motivo declarado ao lado dos
  outros. Nenhum segundo registro nasce aqui — nascer um segundo foi um defeito anterior
  deste mesmo serviço, e o teste que o impede continua valendo. Também toca **P4** (o
  conserto começou pelo teste que reproduz) e **P3** (a trava é do adaptador, a recusa é
  do domínio).

## Contexto

A revisão independente reproduziu, contra o PostgreSQL real, uma **perda de atualização
silenciosa** (*lost update*) — e ela é grave exatamente porque esta aplicação se vende
como multiusuário: a Árvore da Realidade Atual (ARA) e a Nuvem de Conflito (NC) existem
para **um grupo** analisar junto.

`RepositorioDeProjetosSQL.salvar` gravava o **retrato** do agregado que estava em memória,
e `_reconciliar_grafo` apagava do banco toda linha fora desse retrato
(`delete(tabela_aresta).where(… id.notin_(ids_de_aresta))`, e o mesmo para os nós). Com um
retrato por vez isso é correto e preserva dado alheio, que é por que a reconciliação foi
escolhida. Com **dois** retratos é destruição: duas facilitadoras abrem a mesma análise,
as duas leem a versão 7, cada uma acrescenta o seu nó, e a segunda gravação apaga o nó da
primeira.

A coluna `versao` existia (`apps/api/src/toc_api/infra/persistencia/tabelas.py`), era
incrementada a cada mutação (`apps/api/src/toc_api/dominio/projeto.py`, `_avancar`) e o teste de domínio
`test_toda_mutacao_avanca_a_versao_e_o_instante` — que diz, no seu próprio docstring,
"bloqueio otimista (Clarify 2 da spec 004)" — passava. **E não protegia nada**, porque a
versão nunca aparecia num `WHERE`. Era um contador, não uma trava.

### A reprodução, com o que voltou colado (R1)

Vinte escritas concorrentes de nó, cada uma na sua sessão contra o PostgreSQL real, todas
lendo antes de qualquer uma gravar:

```text
$ DATABASE_URL='postgresql+psycopg://toc@/toc_federada?host=/var/run/postgresql&port=5433' \
  python /tmp/.../reproduz.py
projeto criado, versao = 1
escritas aceitas (sem exceção): 20   recusadas: 0
versões lidas pelas 20: [1]
nós no banco depois: 1   versao final: 2
TRABALHO PERDIDO EM SILÊNCIO: 19 nó(s)
```

`versao final: 2` é o resumo do defeito numa linha: as vinte escritas partiram da versão
1, as vinte gravaram a 2, e nenhuma soube da outra.

O mesmo, pela suíte, antes da correção — as três portas de escrita do serviço mais a
borda HTTP (*HyperText Transfer Protocol*), cada uma com a sua medida:

```text
concorrência M1: 20 escritas · aceitas 20 · recusadas 0 · nós no banco 1
concorrência M2 (ARA): 20 escritas · aceitas 20 · recusadas 0 · nós no banco 1
concorrência M3 (NC): 20 escritas · aceitas 20 · recusadas 0 · premissas no banco 1
AssertionError: 20 resposta(s) 201 e 1 nó(s) no banco
```

### O diagnóstico (skill `diagnostico-antes-do-fix`)

A causa raiz tem **duas** metades, e é por isso que "acrescentar um `WHERE`" não bastava:

1. **A escrita era incondicional.** O `UPDATE` filtrava por `id` e `tenant_id`, que casam
   sempre para um registro que existe. Sob `READ COMMITTED` o PostgreSQL não impede nada
   aqui: as duas transações não disputam a mesma linha ao mesmo tempo — a segunda
   simplesmente **vê** as linhas que a primeira acabou de comitar e as apaga pelo
   `notin_`.
2. **O agregado não sabia de que versão tinha partido.** `versao` é incrementada em
   memória a cada mutação, então na hora de gravar ela já não é mais o número contra o
   qual o `WHERE` teria de casar. Sem guardar a versão **lida**, o adaptador não teria
   contra o que condicionar — e é por isso que a coluna existia, era incrementada, e não
   protegia.

## Decisão

**1. O agregado guarda a versão que leu.** `Projeto.versao_lida` (com `init=False`,
`compare=False`, `repr=False`, como o contador `_profundidade_da_raiz`) é preenchido pelo
adaptador ao reidratar e sincronizado por `Projeto.confirmar_gravacao()` **depois** do
commit. `0` significa "nunca foi gravado", e é ele que distingue inserção de atualização.
Não é estado de negócio: é estado de sincronia com o repositório, e por isso não entra na
comparação do agregado.

**2. A escrita condiciona-se a ela.**
`UPDATE projeto SET … WHERE id = :id AND tenant_id = :inq AND versao = :versao_lida`.
Quem não casa recebe `rowcount == 0`, o adaptador relê a versão atual e levanta
`ConflitoDeVersao(versao_lida=…, versao_atual=…)`; a transação inteira volta atrás, sem
efeito parcial. O bloqueio de linha do PostgreSQL faz a serialização: a segunda escrita
espera a primeira comitar, refaz o predicado, não casa mais.

**3. Fecha a CLASSE, não o caso.** As três portas de escrita — `salvar` (M1, Núcleo de
Diagramas Lógicos), `salvar_ara` (M2) e `salvar_nuvem` (M3) — gravam pelo **mesmo**
`_gravar_projeto`, e nenhuma alcança as reconciliações sem passar pela trava primeiro.
O duplo em memória (`apps/api/src/toc_api/infra/persistencia/memoria.py`) recebeu a mesma
regra, porque um duplo mais permissivo que o adaptador real deixa a suíte de contrato verde sobre uma
perda de atualização que o banco de verdade recusa.

**4. A recusa é audível, com código estável.** `409` com `VERSION_CONFLICT` e
`details: {agregado, versao_lida, versao_atual}`. **Por que um código próprio, e não um do
registro mínimo do §A.7**: os dois candidatos nomeiam outra coisa — `INVALID_TRANSITION` é
"confirmação ou transição fora da máquina de estados finitos da proposta (APH-5.1)" e
`PROPOSAL_CONTEXT_STALE` é "a tela mudou entre proposta e confirmação (APH-5.4)". Nenhum
deles é "duas escritas concorrentes sobre o MESMO agregado", que é o que uma ferramenta de
facilitação em grupo encontra o tempo todo; usar um deles mandaria o cliente tratar um caso
que não é o dele. O acréscimo entra no registro único, com motivo declarado, como os
outros vinte e três (`CODIGOS_PROPRIOS` tem 24 linhas com esta, e o registro inteiro,
com o mínimo normativo, tem 31 códigos).

**Os dois números viajam no `details` de propósito.** Sem eles o cliente não tem como se
recuperar sozinho (recarregar a `versao_atual`, reaplicar a intenção, tentar de novo) e
voltaria a ler a mensagem — que é o que o §A.7 proíbe: "o cliente discrimina por código e
nunca por mensagem".

**5. Um portão com sabotagem própria.** `scripts/check-trava-otimista.sh` confere as seis
peças (a versão lida, o `WHERE`, o `rowcount` que reclama, as três portas de escrita, o
duplo em memória e o código no registro), e `scripts/tests/run-sabotagem.sh` prova, com
8 mutações, que ele reprova quando qualquer uma delas é removida — um portão que nada
derruba não é portão.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| **Trava pessimista** (`SELECT … FOR UPDATE` na leitura) | Segura um registro pelo tempo de uma pessoa pensando na tela. Numa oficina de Teoria das Restrições (TOC) com um grupo diante do canvas, é a ferramenta travando em vez de facilitar |
| **Mesclar automaticamente** os dois retratos | Some com a intenção: "acrescentei um nó" e "removi um nó" produzem retratos incompatíveis, e mesclar às cegas inventa uma terceira análise que ninguém fez. A TOC é um método de raciocínio explícito — a decisão de como conciliar é humana |
| **Serializable** como nível de isolamento | Resolve a corrida e troca o silêncio por `SerializationFailure` genérico, sem os dois números e sem código estável. E paga o custo em toda transação do serviço para resolver um caso |
| **Versão vinda do cliente** (`If-Match`) | Fecha uma janela **maior** (a pessoa que ficou meia hora com a tela aberta) e é complementar, não alternativa: sem a trava do servidor ela não impede nada, porque o `UPDATE` continuaria incondicional. Fica registrado como trabalho seguinte |

## Consequências

- Escritas concorrentes sobre o mesmo projeto passam a **falhar em voz alta** para quem
  perde a corrida, em vez de destruir o trabalho de quem ganhou. É uma mudança visível de
  comportamento na interface: quem recebe `409 VERSION_CONFLICT` precisa recarregar.
- A interface ainda **não** recarrega e refaz sozinha — ela só passa a discriminar o
  código (`apps/web/src/api/erros.ts`). Fechar esse laço na tela é trabalho seguinte, e
  está declarado como pendência no relatório do ciclo em vez de descrito como pronto.
- `RepositorioDePropostasSQL` (federação) **não** entra nesta trava: ele é um
  inserção-ou-atualização por chave, sem retrato que apague linha alheia. A corrida entre
  duas confirmações da mesma proposta é matéria da máquina de estados
  (`INVALID_TRANSITION`) e fica declarada como pendência a medir, não como resolvida.

## Fontes

- Reprodução e testes: `apps/api/tests/integracao/test_concorrencia_no_postgres.py`,
  `apps/api/tests/contrato/test_http_conflito_de_versao.py`,
  `apps/api/tests/dominio/test_projeto.py`
- Correção: `apps/api/src/toc_api/infra/persistencia/repositorio_projetos.py`,
  `apps/api/src/toc_api/infra/persistencia/memoria.py`,
  `apps/api/src/toc_api/dominio/projeto.py`, `apps/api/src/toc_api/dominio/erros.py`,
  `apps/api/src/toc_api/dominio/federacao/wire.py`, `apps/api/src/toc_api/http/erros.py`
- Portão: `scripts/check-trava-otimista.sh`, `scripts/tests/run-sabotagem.sh`
- Norma: `/home/user/protocolos/padrao/anexo-a-wire-format.md` (§A.7)
