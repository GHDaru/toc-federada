# Como fechar um ciclo — o procedimento de promoção deste projeto

> Siglas deste documento: **ADR** — *Architecture Decision Record*, Registro de Decisão
> Arquitetural · **DoD** — *Definition of Done*, definição de pronto · **TOC** — Teoria das
> Restrições · **UDE** — Efeito Indesejável · **APH** — Aplicação ↔ Harness.
>
> **Escrito em 2026-09-04**, durante o fechamento do ciclo 001, por um agente que **não
> executou a promoção** e **não pode executá-la**. Toda saída de console abaixo é a saída
> literal do comando escrito na linha acima dela, executada nesta data (regra R1 do
> `CLAUDE.md`); onde a execução real foi impossível sem escrever, isso está dito com todas
> as letras em vez de simulado em prosa.

## 1 · Por que este documento existe, e por que ele para antes do último passo

Promover `dev` → `main` é **aprovar o merge**. No método Maestro isso é o **portão humano
indelegável**: o Princípio II (`docs/governance/principles.md`) diz que o *Accountable* é
sempre humano, e o Princípio III classifica a ação por irreversibilidade × raio — mover
`main` à força e empurrar para o repositório remoto é escrita irreversível de raio máximo.
Some-se a isso a regra que o mesmo princípio impõe do outro lado: **quem executou não
verifica nem aprova o que executou**. Os agentes deste ciclo construíram o corpus, rodaram
os portões e escreveram o relatório; se um deles rodasse `scripts/promote-main.sh`, o ciclo
inteiro passaria a ter uma única testemunha — ele mesmo.

Daí a divisão de trabalho que este arquivo materializa: **o agente deixa a promoção
pronta, com o comando exato, o estado real das branches e a rota de reversão medida; o
Product Steward puxa o gatilho.** O que falta não é conhecimento — é assinatura.

O que o agente pode fazer e fez: ler o script inteiro, descobrir o estado real das branches
por comandos de leitura, e **simular a promoção num clone temporário com um repositório
remoto falso**, para que o comportamento descrito aqui seja observado e não imaginado (§7).

## 2 · O que aguarda o Product Steward antes de qualquer promoção

Esta é a lista real do ciclo 001, tirada de
`specs/001-fundacao-e-planejamento/qa-report.md` §8 — sete itens, nenhum marcável por
agente. A promoção é o **item 7**, e é o último de propósito: ela é o efeito dos seis
anteriores, não um atalho para eles.

| # | O que decidir | Onde está a matéria |
|---|---|---|
| 1 | **Ratificar** a constituição do projeto v1.0.0 e os oito ADRs 0001–0008 | `docs/governance/constitution.md`, `docs/adr/` |
| 2 | **Responder** as cinco perguntas de produto — ou adiar cada uma explicitamente. A pergunta 1 (colaboração por projeto ou isolamento por usuário) é pré-condição declarada do ciclo 002 | `docs/produto/visao.md` §7 |
| 3 | **Responder** as três dúvidas declaradas do `## Clarify` da spec do ciclo | `specs/001-fundacao-e-planejamento/spec.md` |
| 4 | **Ratificar o critério 11 reescrito**: ele deixou de casar a *string do caminho* da base da irmã e passou a medir *conteúdo vazado*, pelo portão `scripts/check-vazamento.sh`. A troca está declarada na spec e provada por quatro sabotagens — falta a assinatura | `qa-report.md` §4.2 e §7 |
| 5 | **Autorizar a entrega** da mensagem externa ao método — levá-la a `GHDaru/maestro` é escrita fora da fronteira do P1 | `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md` |
| 6 | **Aceitar ou recusar** as sete dívidas do §9, com o dono declarado em cada uma | `qa-report.md` §9 |
| 7 | **Autorizar a promoção** — o gate de merge | este documento |

Enquanto os itens 1 a 6 não tiverem resposta, promover só antecipa a data: o ciclo 002 não
começa por causa da `main`, começa por causa da **pergunta 1** do item 2.

## 3 · O estado real das branches deste repositório (medido, não suposto)

O `scripts/promote-main.sh` traz `dev` e `main` como padrões. **Aqui os dois estão
errados** — e é por isso que este documento não pode ser "rode o script".

```text
$ git rev-parse --abbrev-ref HEAD
claude/toc-federada-roadmap-docs-rbtk5b

$ git branch -a
* claude/toc-federada-roadmap-docs-rbtk5b
  remotes/origin/claude/toc-federada-roadmap-docs-rbtk5b
  remotes/origin/main
```

Duas coisas nessa saída decidem o procedimento inteiro:

1. **A branch de trabalho não se chama `dev`.** Ela se chama
   `claude/toc-federada-roadmap-docs-rbtk5b`, e é preciso dizer isso ao script pela
   variável de ambiente `MAESTRO_DEV_BRANCH` (linha 12 do script).
2. **A branch `main` local não existe.** Só existe `remotes/origin/main`. O script
   verifica a existência de `main` com `git rev-parse --verify` (linha 25), que **não**
   resolve uma branch remota:

```text
$ git rev-parse --verify --quiet main; echo "exit=$?"
exit=1

$ git rev-parse --verify --quiet origin/main; echo "exit=$?"
e8afd8d1d8f0cf6a04db0efa01c4fa557069dff0
exit=0
```

Passar `MAESTRO_MAIN_BRANCH=origin/main` **não** é a saída: a linha 81 do script faz
`git branch -f "$MAIN" "$DEV"`, o que criaria uma branch local chamada literalmente
`origin/main`. A saída correta é **criar a `main` local rastreando a remota, uma vez**,
antes de promover (§5, passo 1).

O quanto a `main` está atrás, hoje:

```text
$ git rev-list --count origin/main..claude/toc-federada-roadmap-docs-rbtk5b
8

$ git merge-base --is-ancestor origin/main claude/toc-federada-roadmap-docs-rbtk5b; echo "exit=$?"
exit=0
```

Oito commits à frente, e a `main` é ancestral da branch de trabalho — ou seja, a promoção
é um **avanço rápido**, não uma reescrita de história alheia. Isso é o que torna a
reversão do §8 barata.

**Esse `8` é um número que anda.** Ele foi medido em 2026-09-04 com a ponta em `00c576e`, e
sobe a cada commit que o fechamento ainda acrescentar. Não o cite de memória: rode a linha
acima de novo antes de promover. O que **não** anda é o `e8afd8d` — o commit de onde a
`main` sai, e para onde ela volta se você se arrepender (§8).

## 4 · O que o script faz, na ordem, e onde ele para

Lido inteiro (`scripts/promote-main.sh`, 94 linhas), o script executa seis passos e
**decide nada** — ele remove erro de digitação de um ritual repetido:

| Passo | Linhas | O que faz | Aborta se |
|---|---|---|---|
| 1 | 18–21 | Exige árvore de trabalho limpa | há mudança não commitada |
| 2 | 24–30 | Exige que as duas branches existam e que a de trabalho esteja à frente | uma delas não existe, ou `main` já é igual |
| 3 | 37–46 | Roda `scripts/check-conformance.sh` **sem argumento** | a conformidade sai diferente de zero |
| 4 | 49–57 | Lista os commits que vão para a `main` e **pergunta** (a menos que `--yes`) | você responder qualquer coisa que não seja `y` |
| 5 | 63–78 | Grava o gate no índice de decisões e commita (só se a branch atual for a de trabalho) | nunca — só avisa e segue |
| 6 | 81–92 | `git branch -f main <trabalho>` e `git push origin <trabalho> main`, com cinco tentativas | o push falhar cinco vezes |

**O passo 3 é onde ele para hoje, e a causa é externa a este repositório.** O portão de
conformidade do método usa **pisos absolutos de número de ciclo** calibrados para a
história do repositório canônico; um repositório que começa no ciclo 001 nunca os alcança.
É o vermelho diagnosticado no `qa-report.md` §4.1 e relatado em
`mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md`. Sem argumento — que é exatamente
como o script o chama — ele nem chega ao conteúdo:

```text
$ scripts/check-conformance.sh; echo "exit=$?"
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
──
✗ no cycle in range (floor 42) — the gate checked nothing.
exit=1
```

O ciclo 001 existe; o que o portão diz é que **nenhum ciclo cai na faixa dele** — o piso é
42 e o ciclo mais novo daqui é 012. O próprio script prevê esse caso e nomeia a rota
(linhas 40–43): *"Fix it above, or promote by hand if you have decided the debt is
acceptable and recorded why."* A dívida **já está decidida e registrada** — é a Dv-3 do
`qa-report.md` §9, com dono e com a mensagem externa escrita —, o que autoriza a rota
manual do §5, passo 3b. Nada aqui afrouxa o portão: ele continua vermelho, continua
relatado, e a conta é paga no método, não escondida aqui.

## 5 · A promoção, passo a passo

> Faça isto **na sua máquina**, com a árvore limpa, depois de assinar os itens 1 a 6 do §2.

**Passo 1 — criar a `main` local, uma única vez.**

```bash
git fetch origin
git branch main origin/main        # cria a main local apontando para a remota
```

**Passo 2 — declarar a branch de trabalho ao script.** Ela não se chama `dev`:

```bash
export MAESTRO_DEV_BRANCH="claude/toc-federada-roadmap-docs-rbtk5b"
# MAESTRO_MAIN_BRANCH não precisa ser exportada: o padrão "main" já está certo
# depois do passo 1. Se um dia a branch de destino mudar, é essa a variável.
```

**Passo 3a — a rota do script** (tente esta primeiro; ela pergunta antes de agir):

```bash
scripts/promote-main.sh
```

Hoje ela aborta no passo 3 do §4, com a mensagem de conformidade colada acima. **Se um dia
o método corrigir os pisos** (Dv-3), esta passa a ser a rota única e o §5 inteiro se
resume a esta linha.

**Passo 3b — a rota manual, que o próprio script autoriza enquanto a dívida existir.** São
os passos 5 e 6 do script, escritos à mão, na mesma ordem e com o mesmo efeito:

```bash
DEV="claude/toc-federada-roadmap-docs-rbtk5b"
SHORT=$(git rev-parse --short "$DEV")
TITLE=$(git log -1 --format=%s "$DEV" | tr '"' "'")
TODAY=$(date +%Y-%m-%d)
LINE=$(python3 -c "import json;print(json.dumps({'id':'gate-main-$SHORT','data':'$TODAY','titulo':'Gate de merge: $TITLE','status':'aceita','registro':'commit $SHORT'},ensure_ascii=False))")

scripts/record-decision.sh "$LINE"                       # grava o gate no índice
git add docs/records/decisoes.jsonl
git commit -m "chore(records): merge gate gate-main-$SHORT"

git branch -f main "$DEV"                                # move a main
git push origin "$DEV" main                              # publica as duas juntas
```

Antes de rodar o bloco acima, **olhe o que vai para a `main`** — é o passo 4 do script, o
único que existe para você mudar de ideia:

```bash
git --no-pager log --oneline main.."$DEV"
```

## 6 · O que fica gravado em `docs/records/decisoes.jsonl`

O passo 5 do script acrescenta **uma linha** ao índice de decisões — e acrescentar é a
única operação permitida: o arquivo é *append-only* e um guarda `PreToolUse` recusa a
reescrita. Esta é a linha real que a promoção do estado de hoje gravaria, produzida pela
mesma expressão do script (executada no clone de simulação do §7):

```text
$ echo "$LINE"
{"id": "gate-main-bb9e006", "data": "2026-09-04", "titulo": "Gate de merge: docs(001): fecha o ciclo — escopo declarado, base validada por controle e evidência da DoD", "status": "aceita", "registro": "commit bb9e006"}

$ scripts/record-decision.sh "$LINE"
ok: decision 'gate-main-bb9e006' recorded in docs/records/decisoes.jsonl (9 decisions).
exit=0
```

Três leituras dessa linha, para que ninguém se surpreenda depois:

- **O `id` carrega o commit curto da ponta da branch** no momento da promoção. Se mais
  commits entrarem antes de você promover, o `id` e o `titulo` serão outros — o `titulo`
  é o assunto do último commit, não do ciclo.
- **O campo `registro` aponta para um commit, não para um arquivo.** Quando aponta para um
  arquivo, o `scripts/record-decision.sh` recusa a linha se o arquivo ainda tiver
  marcadores de rascunho — a defesa contra citar evidência que não existe.
- **O gate fica gravado antes do push.** O commit do registro entra na branch de trabalho
  e, por isso, entra na `main` — o registro do portão viaja junto com o que ele aprovou.

## 7 · O que foi verificado, e como

**Não existe modo de inspeção.** O `scripts/promote-main.sh` aceita um único argumento,
`--yes` (linha 15), que **pula a pergunta** — é o contrário de um ensaio. Não há
`--dry-run`. Por isso a verificação foi feita do único jeito seguro: **um clone temporário
em `/tmp`, com o repositório remoto trocado por um repositório vazio local**, para que
nenhum push pudesse alcançar o GitHub. O repositório de trabalho **não foi tocado**:
nenhum comando de escrita do git rodou nele.

**A · sem variáveis de ambiente** — o script procura a branch `dev`, que não existe:

```text
$ scripts/promote-main.sh --yes
aborted: branch 'dev' does not exist.
exit=1
```

**B · com a branch de trabalho declarada, `main` local ainda ausente** — a confirmação
executável do §3:

```text
$ MAESTRO_DEV_BRANCH=claude/toc-federada-roadmap-docs-rbtk5b scripts/promote-main.sh --yes
aborted: branch 'main' does not exist.
exit=1
```

**C · com a `main` local criada** — a bateria avança e para no portão de conformidade,
que é o comportamento descrito no §4:

```text
$ MAESTRO_DEV_BRANCH=claude/toc-federada-roadmap-docs-rbtk5b scripts/promote-main.sh --yes
── Conformance: did the method survive into the artifacts? ──
   (floor: cycle 42; older cycles carry declared debt — see the roadmap)
──
✗ no cycle in range (floor 42) — the gate checked nothing.

aborted: conformance is red — a cycle is being promoted with its method missing
         from its own artifacts. Fix it above, or promote by hand if you have
         decided the debt is acceptable and recorded why.
exit=1
```

**D · a rota manual do §5, passo 3b, executada inteira no clone** — os passos 5 e 6 do
script, contra o repositório remoto falso:

```text
$ git add docs/records/decisoes.jsonl && git commit -q -m "chore(records): merge gate gate-main-bb9e006" && git log --oneline -1
351f6e2 chore(records): merge gate gate-main-bb9e006

$ git branch -f main "$DEV" && git push origin "$DEV" main
fatal: expected 'acknowledgments', received 'packfile'
warning: push negotiation failed; proceeding anyway with push
To /tmp/claude-0/-home-user/b2603f40-b2f9-5d61-8392-43569c8c8606/scratchpad/falso-origin.git
 * [new branch]      claude/toc-federada-roadmap-docs-rbtk5b -> claude/toc-federada-roadmap-docs-rbtk5b
 * [new branch]      main -> main
exit=0

$ git log --oneline -2 main
351f6e2 chore(records): merge gate gate-main-bb9e006
bb9e006 docs(001): fecha o ciclo — escopo declarado, base validada por controle e evidência da DoD
```

As duas primeiras linhas dessa saída são da simulação, não do procedimento: o `push` para
um caminho local negocia diferente e o git avisa antes de seguir. Estão coladas porque a
regra R1 pede a saída **literal**, e uma saída "limpa" que ninguém viu é pior que um aviso
explicado.

**O que a simulação não prova.** Ela roda contra um repositório remoto local e vazio: a
autenticação com o GitHub, a proteção de branch e o *backoff* exponencial do push (linhas
82–92) **não foram exercitados** e não podem ser, sem escrever no remoto real. Se a `main`
do GitHub estiver protegida contra `force-push`, o passo 6 falha cinco vezes e sai 1 —
sem ter desfeito o commit de registro do passo 5, que já estará na branch de trabalho.

**Duas pré-condições a conferir na hora.**

*A árvore tem de estar limpa.* O passo 1 do script (linhas 18–21) aborta com qualquer
mudança não commitada, e durante um fechamento a árvore fica suja o tempo todo — lotes
paralelos ainda escrevem. As duas medições abaixo foram feitas com poucos minutos de
intervalo, no mesmo dia, e mostram exatamente isso:

```text
$ git status --porcelain | head
 M scripts/tests/run-sabotagem.sh
 M scripts/tests/sabotagem/README.md
 M specs/001-fundacao-e-planejamento/qa-report.md
 M specs/001-fundacao-e-planejamento/spec.md
?? scripts/check-vazamento.sh
?? scripts/tests/sabotagem/vazamento/
```

```text
$ git status --porcelain | wc -l
1
```

*A ponta da branch se move.* A simulação acima rodou com a ponta em `bb9e006`; quando ela
terminou, o lote do critério de vazamento já tinha commitado `00c576e` por cima. É por isso
que o `id` do §6 (`gate-main-bb9e006`) **não** é o que a sua promoção vai gravar: ele traz o
commit curto da ponta no instante em que o comando roda. Rode `git rev-parse --short HEAD`
na hora e confira.

## 8 · Como reverter, se o Product Steward se arrepender

A promoção tem **duas metades com reversibilidades diferentes**, e é isso que precisa
ficar claro antes de assinar.

**A `main` volta.** Ela é um ponteiro, e o commit anterior está anotado no §3
(`e8afd8d`, o `origin/main` de hoje). Testado no clone de simulação:

```text
$ git branch -f main e8afd8d && git push --force-with-lease origin main
To /tmp/claude-0/-home-user/b2603f40-b2f9-5d61-8392-43569c8c8606/scratchpad/falso-origin.git
 + 351f6e2...e8afd8d main -> main (forced update)
exit=0
```

Guarde o commit **antes** de promover, para não depender de memória:

```bash
git rev-parse origin/main > /tmp/main-antes-da-promocao.txt
```

**A linha do índice de decisões não volta.** O arquivo é *append-only* por decisão do
método, e o `scripts/record-decision.sh` recusa tanto a repetição de um `id` quanto a
reescrita de uma linha. A rota é **acrescentar a retratação**, com o `status` dizendo o que
aconteceu — as duas coisas, executadas no clone:

```text
$ scripts/record-decision.sh '{"id":"gate-main-bb9e006-revogado","data":"2026-09-04","titulo":"Gate de merge revogado","status":"superseded by gate-main-bb9e006","registro":"commit e8afd8d"}'
ok: decision 'gate-main-bb9e006-revogado' recorded in docs/records/decisoes.jsonl (10 decisions).
exit=0

$ scripts/record-decision.sh '{"id":"gate-main-bb9e006","data":"2026-09-04","titulo":"repetido","status":"aceita","registro":"commit bb9e006"}'
error: id 'gate-main-bb9e006' already recorded — use a new id (or a new line with status 'superseded by gate-main-bb9e006').
exit=1
```

Isso é desenho, não defeito: o registro de um portão que foi aberto e depois fechado de
novo é **história**, e história que se apaga deixa de ser evidência. O commit
`chore(records): ...` também permanece na branch de trabalho — reverter a `main` não o
desfaz, e não deve.

**Classificando o risco, nos termos do Princípio III.** Mover a `main` é irreversível *em
princípio* e reversível *na prática* aqui, porque a promoção é um avanço rápido (§3) e o
commit anterior fica anotado. Isso **baixa a classe de risco**, mas não a zera: a linha do
índice é definitiva, e quem já tiver puxado a `main` promovida verá uma reescrita. Por isso
a assinatura continua sendo do humano.

## 9 · Fechamento de ciclos futuros

Do ciclo 002 em diante, o procedimento é este mesmo, com três diferenças que já dá para
antecipar:

- **A lista do §2 muda a cada ciclo.** Ela sai do §8 do `qa-report.md` daquele ciclo,
  não daqui. Este documento descreve a **mecânica**; o que aguarda assinatura é sempre do
  relatório do ciclo.
- **A branch de trabalho pode ter outro nome.** Confira com `git rev-parse --abbrev-ref
  HEAD` antes de exportar `MAESTRO_DEV_BRANCH` — não copie a string do §5 sem olhar.
- **O passo 3a pode voltar a funcionar sozinho.** Se o método aceitar a
  `mensagens/002-para-maestro-pisos-absolutos-de-ciclo.md` e trocar os pisos absolutos por
  pisos relativos, o portão de conformidade passa a medir conteúdo aqui e a rota manual do
  passo 3b deixa de ser necessária. Quando isso acontecer, **apague o 3b** em vez de
  deixá-lo como atalho: rota manual que sobrevive à sua justificativa vira o caminho por
  onde o portão é contornado.
