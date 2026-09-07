# ADR 0014 — A categoria da linhagem é **portada como rótulo opcional**, e a transição de status da S&T é **livre entre os quatro valores**

> Siglas, uma vez neste documento: **ADR** — *Architecture Decision Record* (Registro de
> Decisão Arquitetural) · **S&T** — Estratégia & Táticas (*Strategy & Tactics*) · **TOC** —
> Teoria das Restrições · **M5** — o módulo Estratégia & Táticas · **VCD** — *Value
> Creating Deliverable* (entregável gerador de valor, jargão da linhagem) · **RF/RN/RI** —
> requisito funcional / regra de negócio / requisito de interface · **FSM** — *Finite State
> Machine* (máquina de estados finitos) · **APH** — Aplicação ↔ Harness · **UI** —
> interface de usuário.

- **Status**: Aceita
- **Data**: 2026-09-06
- **Ciclo**: 010 — Estratégia & Táticas
  ([`../../specs/010-estrategia-e-taticas/spec.md`](../../specs/010-estrategia-e-taticas/spec.md))
- **Princípios tocados**: **P3** (as duas decisões são regra de **domínio puro** —
  `CategoriaDoPasso` e `StatusDoPasso` são vocabulário fechado do agregado, testável sem
  rede, e não configuração de borda) · **P4** (as duas nasceram como teste vermelho:
  `test_a_categoria_da_linhagem_e_opcional_e_carrega_os_seis_valores` e
  `test_as_doze_transicoes_entre_valores_distintos_sao_livres` existiam antes de o enum e a
  regra de transição existirem) · **P2 (INEGOCIÁVEL)**: **tocado apenas no sentido estreito
  de que ambos os vocabulários fechados aparecem no registro de telas do M5** — os campos
  `categoria` e `status` são declarados `ai_visible` como `select` de vocabulário fechado
  (INT-02 da spec 010). Nenhuma das duas decisões cria protocolo, identidade ou
  autorização, e **nenhuma ação de catálogo `toc.*` nasce neste módulo** (INT-04 da spec
  010). Declarado por extenso porque a regra R3 exige que um ADR diga qual princípio
  inegociável encosta na matéria — a omissão é o sintoma, não a discordância.
- **Sucede**: nenhum ADR. Este **resolve duas `[DÚVIDA]` declaradas** na spec 010
  (a 1, sobre a categoria, e a 2, sobre a política de transição) e acrescenta ao
  [ADR 0005](0005-escopo-do-dominio-v1.md), que manteve a S&T na v1 sem decidir a forma do
  passo. Não contradiz nenhuma decisão anterior.

## Contexto

A árvore de S&T é a **única ferramenta que regrediu na linhagem TOC-Builder**, e a
regressão está medida por arquivo e linha:

| Geração | Arquivo | Estado |
|---|---|---|
| 1ª | `TOC-Builder/components/Sidebar.tsx:44` | habilitada (sem `disabled`) |
| 2ª | `TOC-Builder-APP/components/Sidebar.tsx:44` | habilitada |
| 3ª | `TOC-Builder-V2/components/Sidebar.tsx:56` | `disabled: true` |
| 4ª | `tocbuilderv3/components/Sidebar.tsx:58` | `disabled: true` |

Desligada duas vezes, **sem uma linha de decisão registrada em lugar nenhum** — que é
exatamente o que um ADR existe para impedir. O modelo de dados, porém, continuou inteiro no
código: `tocbuilderv3/types.ts:270-311` traz o enum de status com quatro valores já
portugueses, o enum de categoria com seis valores, os três campos de premissa e o
`stepNumber` digitado.

Ao trazer a ferramenta de volta, duas escolhas do modelo eram reais, e a spec 010 as deixou
declaradas como `[DÚVIDA]` em vez de as decidir sozinha — porque as duas mudam o modelo
persistido, e o custo de mudá-las depois das migrações é outro.

## Decisão

### 1. `CategoriaDoPasso` é **portada**, como rótulo **opcional** de seis valores

O enum entra verbatim da linhagem (`tocbuilderv3/types.ts:277-284`):
`nenhuma` · `estrategia` · `tatica` · `vcd` · `build` · `leverage`. O padrão é `nenhuma`, o
campo **nunca é obrigatório** e ele **não bloqueia gravação** (RN-06).

A spec 010 tinha assumido o contrário (L-01: "a categoria **não portada**"), com um
argumento bom: com estratégia e tática como campos distintos do passo, classificar o nó como
"Estratégia" ou "Tática" perde a função que tinha quando existia um texto só
(`strategyText`). O argumento continua bom **para esses dois valores** — e não alcança os
outros quatro. `VCD`, `BUILD` e `LEVERAGE` não descrevem o conteúdo do passo: descrevem o
**papel dele no plano**, que é vocabulário que o método usa em sala e que a linhagem
carregou desde a primeira geração.

A assimetria de custo decide o resto: acrescentar um campo opcional agora é uma coluna com
valor padrão e uma restrição `CHECK`; descobrir a falta dele depois de migrado é uma
migração sobre árvores já escritas. E o campo opcional **não disputa função** com
`estrategia` e `tatica` — os dois continuam sendo o quê e o como, obrigatório o primeiro e
pendência o segundo (RF-11).

O que a decisão custa, dito por extenso: mais um `select` na ficha do passo, mais uma coluna
no banco, mais seis chaves em cada idioma. Se o rótulo não for usado, ele fica `nenhuma` em
100% das linhas e sai numa migração de uma linha — a porta de volta continua aberta.

### 2. A transição de status é **livre entre os quatro valores**, com autor e data

`nenhum` · `validado` · `nao_validado` · `em_execucao` (os quatro da linhagem,
`tocbuilderv3/types.ts:270-275`). Qualquer um vai para qualquer outro: são **doze**
transições, e o teste conta as doze.

A alternativa era uma FSM — a mais óbvia sendo "`em_execucao` exige `validado` antes". Ela
descreve o mundo que se gostaria de ter e não o que acontece numa reunião de
acompanhamento, onde o plano com frequência **já está em execução** quando a validação
lógica formal sai. Uma ferramenta que recusasse marcar "em execução" o que a sala inteira
sabe estar em execução ensinaria a mentir para o instrumento, e um instrumento em que se
mente não mede nada.

O que **é** recusado, e por isso a transição não é "qualquer coisa":

| Recusa | `motivo` | Por quê |
|---|---|---|
| mudar para o valor que já está | `sem_mudanca` | evento sem fato é ruído na auditoria |
| mudar sem dizer quem | `autor_obrigatorio` | é o que a linhagem **não** tinha (RN-03) |
| valor fora dos quatro | `ValueError` do enum, traduzido em `422` na borda | vocabulário fechado |

A autoria é a parte que não se negocia, e ela **não vem do corpo do pedido**: vem do
principal da introspecção. `MudarStatusDoPassoDaSnT.executar` não tem parâmetro `autor`, e um
teste confere a assinatura — na quarta geração da linhagem, mudar status não registrava
absolutamente nada sobre quem mudou.

## Alternativas descartadas

1. **Não portar a categoria** (a assunção original da spec, L-01). Descartada pelo motivo
   do item 1: o argumento cobre `estrategia`/`tatica` e não cobre `vcd`/`build`/`leverage`,
   e o custo de acrescentar depois é maior que o de acrescentar agora.
2. **Portar a categoria como campo obrigatório.** Descartada por contradizer a RN-06 do
   próprio módulo: nada na S&T trava gravação, e um enum obrigatório com valor `nenhuma`
   como saída é um campo obrigatório fingido.
3. **FSM de status com ordem imposta.** Descartada pelo motivo do item 2. Se algum dia for
   preciso, ela entra como **política de projeto** (a instituição escolhe), nunca como
   invariante do domínio — e por ADR novo.
4. **Manter a S&T fora da v1.** Já descartada no [ADR 0005](0005-escopo-do-dominio-v1.md):
   cortá-la faria a sucessora nascer menor que o protótipo que ela aposenta, e nesta
   ferramenta especificamente significaria **regressão sobre regressão**.

## Consequências

- O `snt_passo` ganha as colunas `categoria` e `status`, as duas com vocabulário fechado
  imposto por `CHECK` no banco (migração `0009`) além do enum no domínio — invariante que só
  vive no código é invariante que a próxima ferramenta viola sem perceber.
- A ficha do passo ganha um `select` de categoria e quatro botões de status; os quatro
  valores e as seis categorias entram no mecanismo de internacionalização com chave estável,
  em português e em inglês (RNF-08).
- O registro de telas do M5 declara `categoria` e `status` como `select` **visível** para a
  assistência (são vocabulário fechado, não texto de pessoa) e mantém `estrategia`, `tatica`
  e as três premissas **invisíveis** — texto de usuário é sempre camada não-confiável (item
  7 da constituição, INT-02).
- A regressão D-05 fica desfeita **com decisão registrada**, que é a diferença entre o que
  este ciclo fez e o que a linhagem fez.

## Verificação

```text
$ apps/api/.venv/bin/python -m pytest -q tests/dominio/test_status_do_passo.py -k transicoes -s
  transições entre valores distintos examinadas: 12 · recusadas: 0
```

O restante da evidência — as doze transições, as três recusas nomeadas e o enum de seis
valores — está no `qa-report.md` do ciclo 010, com a saída colada (regra R1).

## A contagem corrente do registro do §A.7

O corpo de um ADR não se reescreve, então a **contagem corrente** do registro de códigos de
erro passa a ser cobrada do ADR mais novo — este —, e a do
[ADR 0013](0013-taxonomia-fechada-da-restricao-e-heranca-que-volta-a-mesa.md) fica sendo o
número da data dele. É a mesma regra que o 0013 herdou do 0012. O M5 acrescentou dois
códigos próprios (`INVALID_SNT_STEP` e `INVALID_MOVE`), pelo critério do §A.7: a **correção
do cliente é diferente** — recarregar a árvore num caso, escolher outro destino no outro.
Executado em 2026-09-06:

```text
$ grep -cE '^    "[A-Z][A-Z0-9_]*": ' apps/api/src/toc_api/dominio/federacao/wire.py
42
$ W=apps/api/src/toc_api/dominio/federacao/wire.py; echo $(( $(grep -cE '^    "[A-Z][A-Z0-9_]*",$' $W) + $(grep -cE '^    "[A-Z][A-Z0-9_]*": ' $W) ))
49
```

O `CODIGOS_PROPRIOS` tem 42 linhas com esta forma, e o registro §A.7 inteiro (mínimo
normativo mais os próprios) tem 49 códigos. O portão que mantém esta conta viva é
`scripts/check-evidencia-colada.sh`.

A conta subiu **três** desde o ADR 0013, e só duas são deste módulo: o terceiro é
`IMPORT_REFUSED` (`apps/api/src/toc_api/dominio/federacao/wire.py:244`), usado por
`apps/api/src/toc_api/http/roteadores/portabilidade.py`, que é trabalho do ciclo 011 e
entrou no arquivo depois desta decisão. Fica dito aqui porque a regra cobra a contagem
**corrente** — e contagem corrente de arquivo compartilhado inclui o que os outros
escreveram nele.
