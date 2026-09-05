# As árvores de planejamento — o produto comendo a própria comida

> Siglas deste documento: **TOC** — Teoria das Restrições · **ARF** — Árvore da Realidade
> Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **ARA** —
> Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **S&T** — Árvore de Estratégia
> & Táticas · **UDE** — Efeito Indesejável (*Undesirable Effect*) · **OI** — Objetivo
> Intermediário · **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **DoD** — Definition of Done (Definição de Pronto) · **IA** —
> inteligência artificial.

- **Data**: 2026-09-05 · **O que este documento cobre**: o método das três árvores e o
  índice do que existe. As árvores das specs **001 a 006** — três cada, **18 documentos** —
  são o lote descrito aqui em detalhe; as das specs 007 a 012 são **lote paralelo desta
  mesma fase de construção**, e a tabela ao fim diz como conferir o estado real em vez de
  confiar nesta linha.

## Por que este projeto planeja com as ferramentas que ele vende

O produto que este repositório constrói é um aplicativo dos Processos de Pensamento da
TOC. Planejar a construção dele com **outra** coisa — uma lista de tarefas genérica, um
quadro de cartões — seria a admissão silenciosa de que as ferramentas não servem para
trabalho de verdade.

Há três razões, e nenhuma delas é cerimônia.

**Primeira: é o teste mais barato que existe do domínio.** Uma APR escrita sobre um ciclo
real força a distinção entre obstáculo, tarefa e risco — a mesma distinção que a
ferramenta vai pedir da Facilitadora TOC. Se ela é difícil de fazer aqui, com o domínio
que melhor conhecemos, ela vai ser impossível na tela. As dezoito árvores já produziram
esse retorno: verbalizar "não existe teste algum neste repositório" como **condição
presente**, e não como "precisamos escrever testes", é exatamente o exercício que a
interface vai ter de tornar natural.

**Segunda: ARF, APR e AT nunca existiram na linhagem.** Quatro gerações de protótipo
entregaram ARA e NC maduras e deixaram as três árvores de futuro como botão cinza — é o
defeito **D-04** de `docs/produto/visao.md`, e a lacuna **L-03** da spec 001 registra que
não há implementação de referência a extrair. Escrevê-las **à mão, sobre matéria real**,
antes de o ciclo 008 as implementar, é a única forma de descobrir o que a ferramenta
precisa dar antes de descobrir na tela.

**Terceira: a APR é o único formato que obriga a olhar para o obstáculo.** Um plano
comum lista o que se vai fazer. Uma APR obriga a escrever **o que está no caminho hoje**,
com evidência — e é aí que aparecem as coisas que um plano esconde: um portão que sai
vermelho, uma dívida com dono, um bloqueio que vive em repositório alheio e que o P1
proíbe consertar.

## Como ler as três árvores

As três respondem a perguntas diferentes e usam **lógicas diferentes**. Trocar uma pela
outra é o erro mais comum de quem começa.

| Árvore | Pergunta que responde | Lógica | Elementos |
|---|---|---|---|
| **ARF** — Árvore da Realidade Futura | *O que passa a ser verdade quando esta spec fechar?* | causa **suficiente** — "se a injeção, então o efeito" | injeções (I-NN), efeitos desejáveis (ED-NN), ramos negativos (RN-NN) **com a poda escrita** |
| **APR** — Árvore de Pré-Requisitos | *O que está no caminho hoje, e o que precisa existir para deixar de estar?* | condição **necessária** — "sem isto, o objetivo não existe" | objetivo, obstáculos (OB-NN), objetivos intermediários (OI-NN), sequenciamento por dependência |
| **AT** — Árvore de Transição | *Que passos, nesta ordem, e com que resultado verificável?* | condição necessária com ação | passos (P-NN), cada um com necessidade, ação e resultado esperado |

### A ordem de leitura que funciona

1. **ARF primeiro**, para saber o que se ganha. Comece pelos **ramos negativos**: eles
   dizem o que o ciclo pode piorar, e a coluna da poda diz o que já foi decidido a
   respeito. Ramo negativo sem poda escrita é risco aceito em silêncio, e nenhuma destas
   dezoito árvores tem um.
2. **APR depois**, para saber o que impede. A coluna "Evidência" é o que distingue um
   obstáculo de um desabafo: cada linha aponta um `arquivo:linha`, uma saída de portão,
   uma dívida numerada no relatório de qualidade do ciclo 001, ou um bloqueio externo
   declarado em `docs/produto/rounds.md`.
3. **AT por último**, para saber a ordem. Toda AT é **amarrada ao `tasks.md`** do seu
   ciclo: cada passo é uma tarefa daquele arquivo, e onde os dois divergirem, o
   `tasks.md` manda. Onde a AT precisa registrar algo que o `tasks.md` ainda não tem — o
   caso das dívidas herdadas no ciclo 002 — isso está declarado como tal, com o motivo.

### O que nenhuma delas faz

Nenhuma árvore decide. Elas **modelam**: o que se ganha, o que impede, em que ordem. As
decisões vivem nos ADRs (`docs/adr/`), nas specs e no gate humano — e cada árvore fecha
com uma seção "O que esta árvore não decide" dizendo para onde ir.

## O que ancora cada elemento

A regra que governa estes dezoito documentos é a mesma **R1** do `CLAUDE.md`: número em
documento só depois de executado, com a saída colada. Aplicada às árvores, ela vira uma
exigência específica — **obstáculo genérico é lixo**. "Falta de tempo" e "complexidade
técnica" não são obstáculos: são desculpas com aparência de análise. Cada obstáculo,
efeito e passo destas árvores aponta para uma destas quatro fontes:

- **`arquivo:linha` verificado**, aqui ou nos repositórios de leitura (a linhagem
  TOC-Builder, a fundação, a norma);
- **saída de portão executada**, colada na seção "Evidência" da própria árvore;
- **dívida numerada** `Dv-1` a `Dv-7` do §9 de
  `specs/001-fundacao-e-planejamento/qa-report.md`, com o dono que o relatório lhe deu;
- **bloqueio externo declarado** em `docs/produto/rounds.md`, ou **lacuna `L-NN`** da
  própria spec, com o risco que ela declarou.

Toda árvore traz uma seção **"Evidência"** com os comandos e as saídas — para que a
próxima pessoa possa reexecutá-los e ver se ainda são verdade. Uma árvore cuja evidência
envelheceu é uma árvore para revisar, e isso é uma propriedade, não um defeito.

## O formato

Cada arquivo é markdown com **tabela e um bloco `mermaid`** que renderiza o grafo. A
tabela carrega a substância — evidência, dependência, poda; o grafo carrega a forma —
quem precede quem. As convenções visuais seguem a literatura:

- **ARF**: lê-se de baixo para cima; injeções na base, efeitos acima, o objetivo no topo.
  Ramos negativos aparecem em linha tracejada, com o nó da poda apontando para eles.
- **APR**: lê-se de baixo para cima; o **obstáculo é o rótulo da aresta**, não um nó — é a
  convenção de Dettmer e Scheinkopf, e ela deixa visível que o obstáculo é o que **está
  entre** um objetivo intermediário e o seguinte.
- **AT**: lê-se de cima para baixo, na ordem de execução.

## As árvores deste lote — specs 001 a 006

| Spec | Ciclo | ARF | APR | AT |
|---|---|---|---|---|
| 001 — Fundação e planejamento | executado, aguardando gate | [`arf.md`](001-fundacao-e-planejamento/arvores/arf.md) | [`apr.md`](001-fundacao-e-planejamento/arvores/apr.md) | [`at.md`](001-fundacao-e-planejamento/arvores/at.md) |
| 002 — Protótipo de interfaces | planejado | [`arf.md`](002-prototipo-de-interfaces/arvores/arf.md) | [`apr.md`](002-prototipo-de-interfaces/arvores/apr.md) | [`at.md`](002-prototipo-de-interfaces/arvores/at.md) |
| 003 — Esqueleto federado | planejado (raia infra) | [`arf.md`](003-esqueleto-federado/arvores/arf.md) | [`apr.md`](003-esqueleto-federado/arvores/apr.md) | [`at.md`](003-esqueleto-federado/arvores/at.md) |
| 004 — Núcleo de diagramas | planejado | [`arf.md`](004-nucleo-de-diagramas/arvores/arf.md) | [`apr.md`](004-nucleo-de-diagramas/arvores/apr.md) | [`at.md`](004-nucleo-de-diagramas/arvores/at.md) |
| 005 — Árvore da Realidade Atual | planejado | [`arf.md`](005-arvore-da-realidade-atual/arvores/arf.md) | [`apr.md`](005-arvore-da-realidade-atual/arvores/apr.md) | [`at.md`](005-arvore-da-realidade-atual/arvores/at.md) |
| 006 — Ações governadas e snapshot | planejado | [`arf.md`](006-acoes-governadas-e-snapshot/arvores/arf.md) | [`apr.md`](006-acoes-governadas-e-snapshot/arvores/apr.md) | [`at.md`](006-acoes-governadas-e-snapshot/arvores/at.md) |

As specs **007 a 012** — Nuvem de Conflito, árvores de futuro, focalização, Estratégia &
Táticas, fundações da aplicação e fechamento — recebem as suas três árvores em **lote
paralelo desta mesma fase**, no mesmo formato descrito acima. Esta linha declara o que
sabe e não mais: quem escreveu este índice não escreveu aquele lote, e afirmar o estado
dele de memória seria exatamente o que a regra **R1** proíbe.

### Como conferir o estado real, sem confiar nesta tabela

Índice escrito à mão envelhece em silêncio. Este comando devolve a verdade do momento em
que for executado:

```bash
for d in specs/0*/; do
  n=$(basename "$d"); linha=""
  for t in arf apr at; do
    [ -f "$d/arvores/$t.md" ] && linha="$linha $t" || linha="$linha  -"
  done
  echo "$n :$linha"
done
ls specs/*/arvores/*.md | wc -l    # quantas existem ao todo, de 36
```

Executado em **2026-09-05 20:03**, ele devolveu as seis specs deste lote completas (três
árvores cada) e o lote paralelo em curso. Reexecute antes de citar qualquer número: o
comando é a fonte, esta frase é só o registro de uma execução.

## Uma nota sobre método

As duas skills de domínio deste ambiente — a de Árvore de Pré-Requisitos e a de Nuvem de
Conflito — descrevem o método e foram seguidas. A skill da APR pede um diagrama
interativo em HTML; aqui o formato é markdown com `mermaid`, porque estes documentos
vivem no repositório, ao lado das specs que descrevem, e precisam ser lidos por quem abre
um arquivo — e verificados por `scripts/check-caminhos.sh` como qualquer outro documento
do corpus. A **substância** do método — obstáculo como condição presente, objetivo
intermediário como estado conquistado, sequenciamento por dependência, teste
obstáculo × objetivo intermediário — está inteira.

## O que este documento não decide

- **A prioridade entre os ciclos** — é do `docs/roadmap.md` e de `docs/produto/rounds.md`.
- **Quando cada árvore é revisada** — candidato natural é a abertura do ciclo
  correspondente, junto com a re-medição das lacunas daquela spec: é lá que a evidência
  colada em cada árvore volta a ser conferida.
- **Se uma árvore está certa** — é matéria de revisão independente, como qualquer outro
  artefato deste repositório. Quem escreveu não verifica (Princípio II do método).
