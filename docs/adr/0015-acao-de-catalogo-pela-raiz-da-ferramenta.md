# ADR 0015 — A ação de catálogo é **declarada de uma ferramenta** e despacha pela **raiz dela**; a Árvore da Realidade Atual ganha as ações que a spec 005 já lhe prometia

> Siglas, uma vez neste documento: **ADR** — *Architecture Decision Record* (Registro de
> Decisão Arquitetural) · **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **TOC** —
> Teoria das Restrições · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito ·
> **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore
> de Transição · **S&T** — Estratégia & Táticas · **UDE** — Efeito Indesejável · **M1** —
> Núcleo de Diagramas Lógicos · **M2** — a ARA · **IA** — inteligência artificial ·
> **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) · **AST** — *Abstract Syntax
> Tree* (árvore sintática abstrata) · **RF/RN/RNF** — requisito funcional / regra de negócio /
> requisito não funcional.

- **Status**: Aceita
- **Data**: 2026-09-07
- **Ciclo**: 006 — Ações governadas e snapshot
  ([`../../specs/006-acoes-governadas-e-snapshot/spec.md`](../../specs/006-acoes-governadas-e-snapshot/spec.md)),
  corrigindo a execução da assistência declarada no ciclo 005
  ([`../../specs/005-arvore-da-realidade-atual/spec.md`](../../specs/005-arvore-da-realidade-atual/spec.md))
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — a matéria é o catálogo `toc.*`, que é a
  superfície executável da federação, e a decisão muda **quais ações existem** e **por onde
  elas escrevem**. Declarado por extenso porque é exatamente o caso que a regra R3 nomeia:
  o alcance do P2 vai até "verbo mutador nasce `action_proposal`" e "autorização fora do
  modelo", e **nada aqui os afrouxa** — toda ação nova é `risk: confirm`, nasce proposta,
  atravessa a máquina de estados e espera o gate humano; a capability continua derivada da
  classe de risco. O que muda é o **destino** do despacho, não a governança dele ·
  **P3** — a decisão é sobre agregado e camada: a raiz da ferramenta volta a ser o único
  caminho para o estado dela, agora também pelo lado do catálogo · **P4** — nasceu de um
  teste vermelho que reproduz o achado ferramenta por ferramenta
  (`apps/api/tests/federacao/test_catalogo_sobre_as_ferramentas.py`) · **P5** — o
  `proposta_id` viaja até o caso de uso da ARA e entra no span, que é o que torna a
  mutação vinda de modelo distinguível de edição humana um mês depois.
- **Sucede**: nenhum ADR — nenhuma decisão anterior é revogada. Ele **corrige a execução**
  do ciclo 006 e **completa** o [ADR 0007](0007-ia-somente-pela-fundacao.md) (a assistência
  é da fundação, pelo catálogo governado) e o
  [ADR 0003](0003-federacao-aph-nivel-2-embedded.md) (Nível 2, `mode: embedded`). Não
  contradiz nenhum ADR; contradiz um **pedaço de código** que nunca teve decisão escrita.

## Contexto

### O defeito, medido

As quatro ações mutadoras genéricas do catálogo — `toc.criar_nos`, `toc.criar_arestas`,
`toc.atualizar_no`, `toc.excluir_nos` — nasceram no ciclo 006 anunciando
`ui_route: /toc/ara` e ligadas aos casos de uso **genéricos** do M1 (`AdicionarNo`,
`LigarNos`, `EditarNo`, `ExcluirNo`). Enquanto o `Projeto` aceitava mutação de quem o
carregasse cru, elas *pareciam* servir as ferramentas — e mutilavam: uma ação governada,
aprovada por gate humano, apagava a aresta D↯D′ de uma Nuvem de Conflito por fora das
invariantes dela.

A correção daquele defeito foi certa e cara: `Projeto._exigir_raiz` passou a recusar toda
mutação de grafo de um projeto de ferramenta que não venha de dentro da raiz, e
`scripts/check-raiz-do-agregado.sh` é o portão. Só que **ninguém voltou para olhar o outro
lado**: as mesmas quatro ações continuaram no catálogo, apontadas para os mesmos casos de
uso genéricos. Elas passaram a falhar **para sempre** em `ara`, `nc`, `arf`, `apr`, `at` e
`focalizacao`.

Consequência medida, reproduzida de ponta a ponta contra o PostgreSQL real: criar uma ARA,
propor `toc.criar_nos` com dois alvos, aprovar no gate humano — e o desfecho voltar
`failed`, com "o grafo de um projeto da ferramenta 'ara' só muda pela raiz". Ou seja: a
assistência de IA da fundação, que é o motivo de a aplicação ser federada, não conseguia
tocar em **nenhuma** ferramenta do produto. Só funcionava em projeto genérico, que é o caso
menos interessante.

### A pergunta certa

A pergunta errada é "como faço a ação genérica passar pela guarda" — a resposta a isso
reabre a porta dos fundos que custou caro fechar, com outro nome e a mesma consequência.

A pergunta certa é **qual é a superfície certa para o catálogo mexer numa ferramenta**. E a
resposta já estava escrita em dois lugares:

1. **A spec 005 declarou o contrato da ARA e adiou a execução** (RF-32..RF-35,
   INT-02..INT-06): as ações mutadoras da ARA são `toc.suggest_udes`, `toc.suggest_causes`
   e `toc.suggest_relations`, mais a reformulação da RF-34 — "cada sugestão mutadora
   nascendo `action_proposal`; aceitar cria o nó/aresta com traço correlacionado à
   proposta". O ciclo 006 executou **outra coisa**: as quatro genéricas.
2. **O M3, o M4 e o M6 já faziam certo.** `toc.suggest_assumptions` chama
   `RegistrarPremissa`, que entra pela `NuvemDeConflito`; `toc.suggest_obstacles` chama
   `AdicionarNoDaAPR`, que entra pelo `ProjetoAPR`; `toc.suggest_constraint` chama
   `RegistrarRestricao`, que entra pela `AnaliseDeFocalizacao`. O padrão existia; a ARA
   é que ficou de fora dele, porque a "ação da ARA" que existia era a genérica com
   `ui_route: /toc/ara`.

A lacuna, portanto, era de **uma** ferramenta — e é essa a medida honesta do achado, não
"seis ferramentas quebradas". As outras cinco tinham ação própria e ela funcionava; o que
falhava nelas era a ação genérica, que nunca deveria ter sido oferecida a elas.

## Decisão

**1. Toda ação do catálogo declara a ferramenta cuja raiz de agregado governa o projeto que
ela toca.** Campo novo `ferramenta` em `AcaoDoCatalogo` (o `ActionSpec` do §4.4 do Padrão
APH). Invariante de domínio: **ação `risk: confirm` sem `ferramenta` não entra no
catálogo**; o valor aceito é a genérica ou uma ferramenta cuja raiz se registrou em
`registrar_raiz_de_ferramenta` — ferramenta que esquecer de se registrar fica **bloqueada**,
nunca liberada (fail-closed, a mesma disciplina do `RAIZ_POR_FERRAMENTA`). Ação de
**leitura** que serve qualquer projeto (`toc.listar_projetos`, `toc.exportar_projeto`) deixa
o campo vazio, e isso é declaração, não omissão.

**2. A ARA ganha as quatro ações que a spec 005 lhe prometeu**, despachadas para os casos de
uso da raiz (`AdicionarEfeito`, `MarcarUde`, `LigarNaARA`, `ReformularUde`):

| Ação | Requisito | Casos de uso da raiz | O que a raiz garante que o genérico não garantia |
|---|---|---|---|
| `toc.suggest_udes` | RF-32, INT-02 | `AdicionarEfeito` + `MarcarUde` | o UDE nasce **com ficha**, e marcar dispara a validação formal dos critérios (função pura) |
| `toc.suggest_causes` | INT-03 | `AdicionarEfeito` + `LigarNaARA` | a causa nasce **ligada**, e o elo nasce com exame `nao_examinado` (RF-22); o nó alvo é conferido **antes** de a causa ser criada, para um alvo inexistente não deixar nó solto e elo nenhum |
| `toc.suggest_relations` | INT-04 | `LigarNaARA` | idem — todo elo da ARA nasce por examinar |
| `toc.suggest_reformulation` | RF-34 | `ReformularUde` | mudar o texto de um UDE **reexecuta** a validação formal (RF-10) |

**3. As quatro genéricas param de se anunciar como se fossem da ARA.** Passam a declarar
`ferramenta: generico`, `ui_route: /toc/projetos`, e a descrição diz por extenso que servem
o rascunho livre e aponta a ação certa de cada ferramenta. As `intent_keywords` deixam de
capturar intenção da ARA (`ude`, `causa`, `efeito` saem).

**4. O executor recusa cedo o desencontro de ferramenta, com mensagem acionável.** Se a
ação declara uma ferramenta e o projeto é de outra, o desfecho é `failed` dizendo as duas
ferramentas e **listando as ações mutadoras daquela ferramenta que aquele principal pode
usar**. Isso é conveniência de borda, **não** é o que protege: quem protege continua sendo
`Projeto._exigir_raiz`, no domínio. A prova disso é um teste que desarma a guarda de borda
(um catálogo que declara `toc.criar_nos` como sendo da NC) e mostra a invariante recusando
do mesmo jeito — `test_a_recusa_do_dominio_sobrevive_ao_catalogo_mentir`.

**5. Nasce o portão `scripts/check-acao-de-catalogo.sh`.** Leitura estática (AST) do par
catálogo × executor, sem importar nem executar nada, com cinco verificações e cinco
sabotagens: ação mutadora sem `ferramenta`; ferramenta com raiz acionando caso de uso
genérico do M1; ação genérica acionando caso de uso de ferramenta; ação mutadora sem
entrada no despacho; e mão mutadora que não aciona caso de uso nenhum.

### O que **não** nasce, e por quê

- **Exclusão assistida em ferramenta.** A spec 005 declara a assistência da ARA em
  RF-32..RF-35 e **não** inclui apagar. Apagar continua gesto humano, pelas rotas da
  ferramenta. `toc.excluir_nos` fica restrita ao projeto genérico.
- **Ação de catálogo para a S&T.** Ausência **declarada**, não esquecimento: a spec 010,
  INT-04, diz que nenhuma ação `toc.*` nasce naquele ciclo, e a DoD 12 de lá é a prova
  negativa. Um teste afirma a ausência para ela não virar dívida silenciosa.
- **Renomear `toc.sugerir_udes`** (a ação de **leitura** que rascunha candidatos a partir de
  uma narrativa, sem gravar nada). Ela e `toc.suggest_udes` convivem, e o par é o fluxo
  real: rascunhar é leitura, registrar é proposta. O risco de confusão é reconhecido e
  mitigado por três coisas — classes de risco diferentes, descrições disjuntas, e o fato de
  que para um principal só com `toc:read` **só uma das duas existe**.

## Alternativas consideradas

**A. Fazer a ação genérica despachar por ferramenta** (um `if` no executor que escolhe a
raiz certa conforme o projeto). Recusada por duas razões, e a segunda é a decisiva:
(i) o `input_schema` genérico **mente** para as outras ferramentas — o enum de tipo
`ude|causa|causa_raiz` não tem sentido numa Nuvem de Conflito, que tem exatamente cinco
entidades e sete arestas que nascem juntas e não se destroem (RN-01 da spec 007), e a APR
precisa de `papel`, e a AT precisa da tripla; (ii) uma fonte, três projeções (APH-4.4) só
funciona se a fonte for honesta: um schema que declara o que a ferramenta recusa produz
proposta aceita que morre na invariante, que é a experiência que o achado descreve.

**B. Namespace no `action_id` por ferramenta** (`toc.ara.criar_nos`). Recusada por
**Princípio I**: a spec 005 já nomeou as ações da ARA, e inventar uma terceira convenção de
nome (o catálogo já mistura português no M1/M2 e inglês no M3/M4/M6) resolveria de forma
pior o que o campo `ferramenta` resolve de forma explícita e legível por máquina. O
namespace continua disponível se um dia duas ferramentas quiserem o mesmo verbo.

**C. Não fazer nada e documentar a limitação.** Recusada: a limitação é o produto inteiro.
Uma aplicação federada cuja assistência não alcança nenhuma das sete ferramentas não é uma
aplicação federada com uma lacuna — é uma aplicação federada que não funciona.

## Consequências

**Positivas.** A assistência da fundação escreve em todas as seis ferramentas que têm ação
declarada, provado ferramenta por ferramenta contra o PostgreSQL real. A guarda da raiz
continua fechada, provada em separado e sem depender da borda. O catálogo passou de 16 para
20 ações, e o manifesto continua válido contra o schema normativo do Anexo B com as sete
sabotagens repelidas. Uma recusa por ferramenta errada agora **ensina a acertar**, o que
transforma um beco sem saída em uma correção de uma chamada.

**Negativas, declaradas.** (i) O catálogo ficou maior, e catálogo maior é mais superfície
para a fundação escolher errado — mitigado pelas descrições que apontam a ação certa e pelo
roteamento determinístico por palavra declarada. (ii) `toc.sugerir_udes` e
`toc.suggest_udes` são nomes próximos; a mitigação está declarada acima e o custo de trocar
um `action_id` já publicado no manifesto é maior que o risco. (iii) A verificação de
ferramenta no executor lê o projeto uma vez a mais por **alvo** de ação com `projeto_id` —
numa proposta de oito Efeitos Indesejáveis são oito leituras a mais. É leitura, sem escrita,
e acompanha o carregamento por alvo que os casos de uso já fazem (cada alvo carrega e grava
o agregado); não muda a ordem de grandeza do que a ação já custava.

**Sobre lote (regra R5 — decisão que contradiz decisão tem de se declarar).** A RF-32 da
spec 005 pede "uma `action_proposal` individual por sugestão"; a US-07 e o fluxo 6.4 da spec
006 pedem oito UDEs numa proposta só, com desfecho por alvo e **uma** confirmação ("para o
rigor não virar oito cliques que ensinam a não ler"). As duas são "Aceita" e apontam para
lados diferentes. A leitura adotada: as três ações de criação da ARA nascem de lote com
`batch_atomicity: per_item` e `minItems: 1` — uma proposta por invocação, um desfecho por
alvo, e a fundação continua livre para propor um de cada vez. É a spec 006 que descreve o
fluxo com a tela, e é a mais recente. Fica registrado aqui para a contradição não atravessar
mais portões verdes sem ninguém a nomear.
