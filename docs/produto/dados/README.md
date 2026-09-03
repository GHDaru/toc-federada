# Base sintética do domínio — Instituição Horizonte

> Siglas deste documento: **TOC** — Teoria das Restrições (*Theory of Constraints*);
> **UDE** — Efeito Indesejável (*Undesirable Effect*); **ARA** — Árvore da Realidade Atual
> (*Current Reality Tree*); **NC** — Nuvem de Conflito (*Evaporating Cloud*); **ADR** —
> Registro de Decisão Arquitetural (*Architecture Decision Record*); **IA** — inteligência
> artificial.

- **Status**: rascunho do ciclo 001 (aprovação: gate humano do ciclo)
- **Data**: 2026-09-03 · **Decisor**: Product Steward (ghdaru)
- **Decisão que a exige**: [`../../adr/0006-base-sintetica-desde-o-dia-1.md`](../../adr/0006-base-sintetica-desde-o-dia-1.md)

## O que é

Uma análise TOC **inteira e fictícia** de uma instituição de ensino inventada, a
**Instituição Horizonte**: a ARA com os seus UDEs, as causas e a causa raiz; as arestas
causais que as ligam; e a NC derivada da causa raiz, com as cinco entidades, as sete
arestas com premissa escrita e as injeções que atacam duas delas.

Ela existe porque a visão do produto ([`../visao.md`](../visao.md)) mede exaustivamente a
**linhagem** — o que quatro gerações de protótipo fizeram — e não tinha um único número
sobre o **domínio**: o que conta como um UDE aceitável, e quantos dos que aparecem numa
oficina real de fato são. Sem uma base, "a regra de negócio central vive num prompt"
(defeito D-08) é observação de arquitetura; com ela, vira número, e o número vira critério
de aceite do épico E2.1 na spec 005 (defeito D-12).

Dois arquivos:

- [`analise-horizonte.json`](analise-horizonte.json) — a base, versionada (`versao`,
  `data`, `sintetica`).
- [`medir-base.py`](medir-base.py) — valida a estrutura, aplica os critérios formais de
  UDE e imprime as contagens. **Nenhum número desta pasta ou da visão é digitado à mão**
  (regra R1 do [`../../../CLAUDE.md`](../../../CLAUDE.md)).

## Ela é sintética por decisão, não por acaso

O ADR 0006 proíbe dado real de pessoa em fixture, captura, spec ou exemplo — é o que
permite este repositório ser aberto, e é a dívida que a irmã `gestaodeprioridades` paga
por ter nascido com a base real do dono. Aqui:

- A organização é inventada; as personas são **papéis**, não pessoas: Facilitadora TOC,
  Participante, Gestora. Nenhum nome próprio, nenhuma data de desempenho de ninguém.
- Os UDEs descrevem uma instituição de ensino que não existe, com números escolhidos para
  exercitar o domínio.
- A decisão nº 3 do ADR 0006 exige base sintética **com assimetrias deliberadas**, porque
  o valor de teste de uma base real está nas suas patologias. Aqui a assimetria é o
  ponto: dos doze UDEs, a maioria está escrita **errado** — errado do jeito que um
  facilitador humano erra.

## As patologias deliberadas

Os UDEs foram redigidos como saem de uma oficina de verdade, não como saem de um manual.
Cada nó traz o campo `patologia` documentando o defeito de redação (campo documental — o
critério não o lê; o que o script confere contra ele é apenas o booleano
`esperado_reprovado`, para o critério não ser afrouxado em silêncio até "dar certo"):

| UDE | Como está escrito | Patologia |
|---|---|---|
| U-04 | "Reduzir o tempo de resposta…" | ação, não estado — a tarefa que se quer ver feita |
| U-05 | "…abandonam o curso **porque** a coordenação não responde" | traz a causa presumida dentro da verbalização |
| U-06 | "**Falta um** sistema integrado de matrícula" | solução disfarçada de efeito |
| U-07 | "A equipe é **desleixada** … **e** o aluno fica sem resposta" | culpa pessoas, junta duas entidades, julga |
| U-08 | "O atendimento ao aluno é **péssimo**" | juízo subjetivo, sem fato observável |
| U-09 | "Os professores chegam atrasados **e** as salas não têm projetor" | duas entidades numa frase |
| U-10 | "A evasão **aumentará** no próximo semestre" | previsão, não realidade atual |
| U-11 | "A instituição **perdeu** 120 matrículas" | fato passado e encerrado |
| U-12 | "Alta evasão" | rótulo de post-it, não frase |

U-01, U-02 e U-03 estão escritos como o método pede — os três são UDEs de "existência de
lacuna", com número, no presente.

## Os critérios formais, e de onde eles vêm

A 4ª geração da linhagem escreveu onze características de um UDE bem articulado **dentro
de um texto de prompt** de modelo de linguagem (`tocbuilderv3/constants.ts:122-133`).
O script traduz **sete** dessas onze em **oito** funções puras (a característica 2 vira
duas: frase completa e tempo presente) — sem rede, sem modelo, sem estado. As outras
quatro (1, 4, 5 e 7) dependem de julgamento sobre o sistema analisado e são declaradas
como fora do alcance de qualquer função: é essa fronteira que o épico E2.1 implementa.

| Checagem | Característica de origem | O que reprova |
|---|---|---|
| CD-1 | 2 (parte 1) | não é frase completa (maiúscula inicial, ponto final, ≥ 4 palavras) |
| CD-2 | 2 (parte 2) | verbo fora do presente |
| CD-3 | 3 | a frase começa por verbo no infinitivo (ação, não estado) |
| CD-4 | 6 | léxico de culpa a pessoas |
| CD-5 | 8 | léxico de solução disfarçada ("falta um…", "precisamos de…") |
| CD-6 | 9 | conector de coordenação ligando duas orações |
| CD-7 | 10 | conector causal dentro da frase ("porque", "devido a"…) |
| CD-8 | 11 | léxico de juízo de valor |

**Limites declarados** (uma checagem léxica não é um analisador sintático): CD-6 marcaria
um falso positivo numa enumeração de substantivos escrita como "… e os …"; CD-2 depende de
lista de exceções para não confundir substantivo com verbo ("céu", "seu"). São limites de
uma função pura, e é por isso que a spec 005 mantém o julgamento — o que o modelo faz por
proposta, nunca por decisão — para as quatro características indecidíveis.

## As contagens — medidas, não declaradas

```console
$ python3 docs/produto/dados/medir-base.py
── Base sintética · Instituição Horizonte · versão 1.0.0 ──
  arquivo: analise-horizonte.json  ·  sintética: True  ·  personas: 3
  ARA: 16 nós (12 UDEs, 4 causas) · 16 arestas causais
  Nuvem de Conflito: 5 entidades · 7 arestas com premissa · 2 injeções
  validação estrutural: 0 falha(s)

── Critérios formais de UDE (tocbuilderv3/constants.ts:122-133) ──
  características do prompt: 11  ·  decidíveis por função pura: 8 checagens cobrindo 7  ·  dependentes de julgamento: 4

  U-01  PASSA   O intervalo médio da matrícula até a primeira aula é de 43 dias.
  U-02  PASSA   Um terço das turmas abertas encerra o semestre com menos de dez alunos.
  U-03  PASSA   A taxa de conclusão dos cursos técnicos é de 54%.
  U-04  REPROVA  Reduzir o tempo de resposta às solicitações dos alunos matriculados.
            └ CD-3 a frase começa pela ação "Reduzir" (verbo no infinitivo)
  U-05  REPROVA  Os alunos abandonam o curso porque a coordenação não responde às mensagens.
            └ CD-7 traz a própria causa: "porque"
  U-06  REPROVA  Falta um sistema integrado de matrícula na secretaria.
            └ CD-5 solução disfarçada de efeito: "falta um"
  U-07  REPROVA  A equipe da secretaria é desleixada com os prazos e o aluno fica sem resposta.
            └ CD-4 atribui culpa a pessoas: "desleixad"
            └ CD-6 duas entidades na mesma frase: "e o"
            └ CD-8 juízo de valor: "desleixad"
  U-08  REPROVA  O atendimento ao aluno é péssimo.
            └ CD-8 juízo de valor: "péssim"
  U-09  REPROVA  Os professores chegam atrasados e as salas não têm projetor.
            └ CD-6 duas entidades na mesma frase: "e as"
  U-10  REPROVA  A evasão aumentará no próximo semestre.
            └ CD-2 verbo fora do presente: "aumentará"
  U-11  REPROVA  A instituição perdeu 120 matrículas no último semestre.
            └ CD-2 verbo fora do presente: "perdeu"
  U-12  REPROVA  Alta evasão
            └ CD-1 não é frase completa (maiúscula inicial, ponto final, ≥4 palavras)

  UDEs medidos: 12  ·  passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03)  ·  reprovam: 9
  divergências entre o esperado na base e o medido: 0
  fora do alcance de qualquer função pura (exigem julgamento):
    característica 1 — é queixa sobre um problema contínuo que limita o desempenho
    característica 4 — está dentro da área de responsabilidade ou influência
    característica 5 — algo pode ser feito a respeito
    característica 7 — não é uma causa especulada

✓ base válida (16 nós, 16 arestas, nuvem de 5 entidades e 7 premissas) e veredito dos critérios bate com o documentado.
$ echo "exit=$?"
exit=0
```

**Doze UDEs escritos como um facilitador humano escreve; três passam nos oito critérios
decidíveis.** É esse 3 de 12 que o defeito D-12 da visão publica e que a spec 005 herda
como critério de aceite executável.

## O que este arquivo não decide

- **O modelo de dados da ARA e da NC no produto** — é das specs 004 e 005 e 007
  (`specs/`), no formato do ADR 0004. Este JSON é base de exemplo, não esquema.
- **Se a validação bloqueia ou apenas avisa** o usuário ao criar um UDE reprovado — é
  requisito do épico E2.1 e vai à spec 005; a base só mede a taxa.
- **Qualquer capacidade de IA** — a assistência vem da fundação pelo catálogo de ações
  governadas (ADR 0007), e este script não chama modelo nenhum.
