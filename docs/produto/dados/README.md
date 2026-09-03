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

Dois arquivos e **duas** medições, que não devem ser confundidas:

- [`analise-horizonte.json`](analise-horizonte.json) — a base, versionada (`versao`,
  `data`, `sintetica`).
- [`medir-base.py`](medir-base.py) — valida a estrutura, aplica os critérios formais de
  UDE e imprime as contagens. **Nenhum número desta pasta ou da visão é digitado à mão**
  (regra R1 do [`../../../CLAUDE.md`](../../../CLAUDE.md)).

| Medição | O que é | O que ela prova | O que ela **não** prova |
|---|---|---|---|
| **Número autoral** | as oito checagens sobre os doze UDEs da Instituição Horizonte | que as checagens disparam sobre as patologias que a base traz | nada sobre a *correção* das checagens: base e checagens têm o mesmo autor |
| **Número de controle** | as mesmas oito checagens sobre nove enunciados de UDE colhidos da linhagem TOC-Builder, rotulados **pela fonte** | onde as checagens erram contra um gabarito alheio — e elas erram: um falso negativo | prevalência: nove enunciados didáticos não são uma oficina |

A segunda existe porque a primeira, sozinha, é circular — é o que as duas seções
"Por que o 3 de 12 não valida checagem nenhuma" e "O conjunto de controle" explicam.

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

  NÚMERO AUTORAL — UDEs medidos: 12  ·  passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03)  ·  reprovam: 9
  divergências entre o esperado na base e o medido: 0 — isto é acordo do autor consigo mesmo, não evidência: quem escreveu os enunciados
    escreveu as checagens. O que vale como evidência é o controle abaixo.
  fora do alcance de qualquer função pura (exigem julgamento):
    característica 1 — é queixa sobre um problema contínuo que limita o desempenho
    característica 4 — está dentro da área de responsabilidade ou influência
    característica 5 — algo pode ser feito a respeito
    característica 7 — não é uma causa especulada

── Conjunto de controle · enunciados NÃO escritos aqui ──
  enunciados: 9  ·  colhidos de 2 arquivo(s) da linhagem TOC-Builder, anteriores a estas checagens:
    tocbuilderv3/components/CanvasWelcome.tsx
    tocbuilderv3/constants.ts
  os oito de constants.ts aparecem com o mesmo texto nas quatro gerações:
    TOC-Builder/constants.ts:158,159,184,185,193,194
    TOC-Builder-V2/constants.ts:129,130,155,156,164,165
    TOC-Builder-APP/constants.ts:129,130,155,156,164,165
    tocbuilderv3/constants.ts:136,137,162,163,171,172
  rótulo de cada enunciado = o que a FONTE diz dele; nenhum resultado esperado foi declarado aqui

  K-01  PASSA   [fonte: bom]  Nosso desempenho de entrega no prazo é de 60%
            fonte: tocbuilderv3/constants.ts:136 — UDE de "existência de lacuna" — o tipo que o prompt manda PREFERIR
            ⚠ literal (sem ponto final) REPROVA — só a CD-1, por pontuação
  K-02  PASSA   [fonte: nao_preferido]  Recursos frequentemente não estão disponíveis
            fonte: tocbuilderv3/constants.ts:137 — UDE de "dificuldade em fechar a lacuna" — aceito, mas preterido
            ⚠ literal (sem ponto final) REPROVA — só a CD-1, por pontuação
  K-03  PASSA   [fonte: ruim]  Falta de treinamento causa erros.
            fonte: tocbuilderv3/constants.ts:162 — Exemplo Ruim: UDE + Causa
  K-04  PASSA   [fonte: bom]  A taxa de erros no processo X é de 15%.
            fonte: tocbuilderv3/constants.ts:162 — Bom UDE — a correção que a fonte propõe para K-03
  K-05  REPROVA  [fonte: ruim]  Precisamos de um novo software para gerenciar tarefas.
            fonte: tocbuilderv3/constants.ts:163 — Exemplo Ruim: Solução
            └ CD-5 solução disfarçada de efeito: "precisamos de"
  K-06  PASSA   [fonte: bom]  Tarefas frequentemente ultrapassam o prazo.
            fonte: tocbuilderv3/constants.ts:163 — Bom UDE — a correção que a fonte propõe para K-05
  K-07  PASSA   [fonte: bom]  O tempo médio de ciclo do pedido é de 10 dias.
            fonte: tocbuilderv3/constants.ts:171 — Exemplo de Lacuna (Preferível como UDE)
  K-08  PASSA   [fonte: nao_preferido]  Há muitos gargalos no processo de aprovação.
            fonte: tocbuilderv3/constants.ts:172 — Exemplo de Dificuldade (Pode ser uma causa)
  K-09  PASSA   [fonte: sem_rotulo]  O churn de clientes está alto.
            fonte: tocbuilderv3/components/CanvasWelcome.tsx:11 — texto de exemplo oferecido na tela de boas-vindas da ARA

  NÚMERO DE CONTROLE — enunciados: 9  ·  passam (texto normalizado): 8  ·  passam (texto literal, como citado): 6
  rotulados pela fonte como bom/ruim: 6  ·  concordância: 5 (K-01, K-04, K-05, K-06, K-07)
  FALSO POSITIVO (a fonte diz bom, a checagem reprova): 0 (—)
  FALSO NEGATIVO (a fonte diz ruim, a checagem aprova): 1 (K-03)
  sem veredito possível (a fonte não rotula bom/ruim): 3 (K-02, K-08, K-09)

── Autoral × controle ──
  autoral:  3/12 passam (25%) — base escrita para exercitar as checagens
  controle: 8/9 passam (89%) — enunciados escritos como material didático, a maioria para ser exemplar
  as duas taxas medem coisas diferentes e NENHUMA estima prevalência de oficina; a amostra de
  controle tem 9 enunciados e é pequena porque é tudo o que a linhagem escreveu.

✓ base válida (16 nós, 16 arestas, nuvem de 5 entidades e 7 premissas); veredito autoral bate com o documentado e o controle de 9 enunciados
  externos foi medido: 0 falso(s) positivo(s), 1 falso(s) negativo(s).
$ echo "exit=$?"
exit=0
```

**Doze UDEs escritos como um facilitador humano escreve; três passam nos oito critérios
decidíveis.** Esse 3 de 12 é o **número autoral**, e ele responde a uma pergunta estreita:
*as oito checagens de fato disparam sobre as patologias que a base traz?* Disparam. O que
ele **não** responde está na próxima seção.

## Por que o 3 de 12 não valida checagem nenhuma

Quem escreveu os doze enunciados da Instituição Horizonte é quem escreveu as oito
checagens, e escreveu-os de propósito "com as patologias típicas de oficina" — as mesmas
que as checagens procuram. A linha

```console
$ python3 docs/produto/dados/medir-base.py | grep "divergências entre o esperado"
  divergências entre o esperado na base e o medido: 0 — isto é acordo do autor consigo mesmo, não evidência: quem escreveu os enunciados
```

prova que o esperado e o medido coincidem — o que é **tautologia**, não evidência. Uma
base autoral **demonstra** as checagens; ela não pode **validá-las**, porque um erro da
checagem e um erro do enunciado se cancelam sem deixar rastro. A tautologia foi apontada
pela revisão independente do ciclo 001 e é a origem desta seção e do conjunto de controle.

## O conjunto de controle — enunciados que não escrevemos

Para que as checagens possam **errar**, é preciso medi-las contra enunciados de UDE que
existiam **antes e fora** deste repositório, rotulados por outra pessoa. Eles existem: a
linhagem TOC-Builder escreveu exemplos didáticos de UDE dentro do próprio texto de prompt
e numa tela, ao longo das quatro gerações — todas anteriores a estas checagens — e
**rotulou seis deles** explicitamente como "Bom UDE" ou "Exemplo Ruim". É esse rótulo
alheio — nunca o nosso — que serve de gabarito; os três restantes ficam sem veredito, e a
seção de resultado diz quais são e por quê.

O conjunto vive em `CONTROLE`, dentro do
[`medir-base.py`](medir-base.py), com três regras que preservam a independência:

1. **Nenhum enunciado foi redigido, corrigido ou parafraseado aqui** — são cópias
   literais, cada uma com caminho e linha.
2. **Nenhum item declara resultado esperado.** Não há campo `esperado_reprovado` no
   controle: se houvesse, a tautologia voltaria por outra porta.
3. **O rótulo é o da fonte.** Onde a fonte não rotula, o item fica "sem rótulo" e **não
   entra** na conta de concordância.

### Procedência, item a item

| # | Enunciado (cópia literal) | Origem | Rótulo escrito pela fonte |
|---|---|---|---|
| K-01 | "Nosso desempenho de entrega no prazo é de 60%" | `tocbuilderv3/constants.ts:136` | UDE de "existência de lacuna" — o tipo que o prompt manda PREFERIR |
| K-02 | "Recursos frequentemente não estão disponíveis" | `tocbuilderv3/constants.ts:137` | UDE de "dificuldade em fechar a lacuna" — aceito, mas preterido |
| K-03 | "Falta de treinamento causa erros." | `tocbuilderv3/constants.ts:162` | **Exemplo Ruim** (UDE + Causa) |
| K-04 | "A taxa de erros no processo X é de 15%." | `tocbuilderv3/constants.ts:162` | **Bom UDE** (a correção que a fonte propõe para K-03) |
| K-05 | "Precisamos de um novo software para gerenciar tarefas." | `tocbuilderv3/constants.ts:163` | **Exemplo Ruim** (Solução) |
| K-06 | "Tarefas frequentemente ultrapassam o prazo." | `tocbuilderv3/constants.ts:163` | **Bom UDE** (a correção que a fonte propõe para K-05) |
| K-07 | "O tempo médio de ciclo do pedido é de 10 dias." | `tocbuilderv3/constants.ts:171` | Exemplo de Lacuna (Preferível como UDE) |
| K-08 | "Há muitos gargalos no processo de aprovação." | `tocbuilderv3/constants.ts:172` | Exemplo de Dificuldade (Pode ser uma causa) |
| K-09 | "O churn de clientes está alto." | `tocbuilderv3/components/CanvasWelcome.tsx:11` | *sem rótulo* — texto de exemplo oferecido na tela de boas-vindas |

Os oito de `constants.ts` aparecem com **o mesmo texto** nas quatro gerações — o script
imprime os espelhos com linha, e o comando que os encontrou foi:

```console
$ grep -rn "Exemplo Ruim\|Exemplo de Lacuna\|Exemplo de Dificuldade\|existência de lacuna" /home/user/TOC-Builder/constants.ts /home/user/TOC-Builder-V2/constants.ts /home/user/TOC-Builder-APP/constants.ts /home/user/tocbuilderv3/constants.ts | wc -l
24
```

### Nove. É pouco, e é tudo o que existe

**São nove enunciados**, e a honestidade sobre esse número é parte do resultado. Nove
porque foi o que a busca encontrou, não porque nove bastasse:

- as quatro gerações da linhagem repetem os **mesmos oito** enunciados de `constants.ts`;
- a tela de boas-vindas contribui **um**;
- as skills locais de domínio (`toc-evaporating-cloud`, `toc-prt`) foram lidas e **não
  trazem enunciado de UDE nenhum** — zero, e zero é o número que entra aqui:

  ```console
  $ grep -c -i "efeito indesej\|UDE" /root/.claude/skills/synced/*/toc-evaporating-cloud/SKILL.md /root/.claude/skills/synced/*/toc-prt/SKILL.md
  /root/.claude/skills/synced/b6e1be5c-669c-482c-9514-0127da476f91_2985a601-e1f3-4a1c-b194-a365a60ae8c4/toc-evaporating-cloud/SKILL.md:0
  /root/.claude/skills/synced/b6e1be5c-669c-482c-9514-0127da476f91_2985a601-e1f3-4a1c-b194-a365a60ae8c4/toc-prt/SKILL.md:0
  ```

O que foi **deliberadamente deixado de fora**, para não engordar a amostra com o que não é
UDE: os textos de espaço reservado de formulário (`locales/pt.ts:157` e `:333` descrevem um
**projeto**, não um efeito) e as justificativas de aresta do exemplo de prompt
(`constants.ts:105-106` são `reason=` de conexão causal). Inventar enunciado para chegar a
vinte reintroduziria exatamente a autoria que o controle existe para remover.

### O resultado, inclusive o desfavorável

```console
$ python3 docs/produto/dados/medir-base.py | grep -E "^  (NÚMERO|rotulados|FALSO|sem veredito|autoral:|controle:)"
  NÚMERO AUTORAL — UDEs medidos: 12  ·  passam nos 8 critérios decidíveis: 3 (U-01, U-02, U-03)  ·  reprovam: 9
  NÚMERO DE CONTROLE — enunciados: 9  ·  passam (texto normalizado): 8  ·  passam (texto literal, como citado): 6
  rotulados pela fonte como bom/ruim: 6  ·  concordância: 5 (K-01, K-04, K-05, K-06, K-07)
  FALSO POSITIVO (a fonte diz bom, a checagem reprova): 0 (—)
  FALSO NEGATIVO (a fonte diz ruim, a checagem aprova): 1 (K-03)
  sem veredito possível (a fonte não rotula bom/ruim): 3 (K-02, K-08, K-09)
  autoral:  3/12 passam (25%) — base escrita para exercitar as checagens
  controle: 8/9 passam (89%) — enunciados escritos como material didático, a maioria para ser exemplar
```

Três divergências registradas, nenhuma apagada:

**Divergência 1 — falso negativo em K-03, e é o achado do exercício.** A fonte rotula
"Falta de treinamento causa erros." como **Exemplo Ruim**, porque o enunciado traz a
própria causa dentro da verbalização (característica 10). As oito checagens **aprovam**.
A causa raiz é concreta e corrigível: a CD-7 procura **conectivos** (`porque`, `devido a`,
`já que`…) e não procura o **verbo causal** — `causa`, `leva a`, `resulta em`, `provoca`,
`gera`. Os dois enunciados de `constants.ts:105-106`, que a própria linhagem escreveu como
justificativa de relação causal, usam justamente "levam a" e "resulta em". Isto vira
requisito de teste do épico E2.1 na spec 005: **o léxico da CD-7 tem de cobrir verbo
causal, e K-03 é o caso que hoje falha.** Sem o controle, esse buraco seguiria invisível —
a base autoral não tinha um único enunciado com verbo causal, porque quem a escreveu
tinha na cabeça a mesma lista de conectivos da CD-7.

**Divergência 2 — a CD-1 depende de pontuação, e isso aparece em K-01 e K-02.** Citados
literalmente, os dois vêm sem ponto final (estão dentro de parênteses num texto corrido) e
a CD-1 os reprova — 6 passam no texto literal contra 8 no normalizado. Parte disso é
artefato de citação, e por isso o script imprime **as duas contas** e marca a linha
`⚠ literal (sem ponto final) REPROVA — só a CD-1, por pontuação`; normalizar em silêncio
esconderia o resto, que é achado de verdade: **num produto, o facilitador que esquece o
ponto final é reprovado pelo motivo errado.** Requisito para a spec 005: a CD-1 sinaliza
pontuação como aviso de forma, separado das checagens de conteúdo.

**Divergência 3 — três dos nove não têm veredito possível.** K-02, K-08 e K-09 não são
rotulados bom/ruim pela fonte: os dois primeiros são "dificuldade em fechar a lacuna",
que o prompt aceita mas prefere não usar, e o terceiro é texto de tela. As oito checagens
aprovam os três e **não têm como distinguir** lacuna de dificuldade — essa distinção mora
na característica 1, uma das quatro declaradas indecidíveis. O controle confirma a
fronteira em vez de a contradizer.

### O que o controle permite, e o que continua não permitindo

**Permite** dizer, com gabarito alheio: das seis afirmações que a linhagem rotulou,
as checagens concordam com cinco e erram uma, e o erro é por omissão de léxico, não por
excesso de rigor — zero falso positivo em nove enunciados. **Não permite** dizer nada
sobre prevalência: 25% de aprovação na base autoral e 89% no controle **não são medidas
do mesmo fenômeno** — a base foi escrita para reprovar, o controle foi escrito para
ensinar, e nenhum dos dois foi colhido de uma oficina. Com nove enunciados e seis
rotulados, um único caso a mais move a taxa em mais de dez pontos. É o que a lacuna L-03
da visão passa a declarar.

## O que este arquivo não decide

- **O modelo de dados da ARA e da NC no produto** — é das specs 004 e 005 e 007
  (`specs/`), no formato do ADR 0004. Este JSON é base de exemplo, não esquema.
- **Se a validação bloqueia ou apenas avisa** o usuário ao criar um UDE reprovado — é
  requisito do épico E2.1 e vai à spec 005; a base só mede a taxa.
- **Qualquer capacidade de IA** — a assistência vem da fundação pelo catálogo de ações
  governadas (ADR 0007), e este script não chama modelo nenhum.
