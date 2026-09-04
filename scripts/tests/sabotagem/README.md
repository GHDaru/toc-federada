# Sabotagem — a prova de que os portões deste projeto sabem reprovar

> Siglas deste documento: **ADR** — Architecture Decision Record (Registro de Decisão
> Arquitetural) · **DoD** — Definition of Done (Definição de Pronto) · **TOC** — Teoria das
> Restrições · **RI** — requisito de interface.

A segunda lei da skill `verifiable-dod` é curta: **um check que nada consegue derrubar não
é um check**. Este diretório é a aplicação dela aos portões locais do projeto.

Rode tudo com:

```bash
scripts/tests/run-sabotagem.sh        # -v mostra a saída de cada execução
```

## O desenho: base válida + mutação declarada

Cada portão tem **uma base válida mínima** aqui — um repositório sintético em miniatura,
correto de propósito. O executor `scripts/tests/run-sabotagem.sh` roda cada portão **duas
vezes**:

1. **Contra a base**, que tem de sair `0`. Um portão que reprova a própria base válida
   reprovaria qualquer coisa, e um portão assim ensina as pessoas a ignorá-lo.
2. **Contra a base sabotada**, uma cópia com **uma** mutação declarada na tabela do
   executor, que tem de sair `≠ 0` **e** imprimir o motivo que a tabela exige.

A segunda exigência é o que impede a suíte de ser leniente: sem ela, um portão que
reprovasse por acidente — um caminho errado, um arquivo que faltou — passaria no teste sem
nada ter sido provado. É a mesma regra do `GHDaru/protocolos` (*"a suíte não pode ser
leniente: todo check executável precisa de sabotagem que o derrube"*).

A sabotagem **nunca toca o repositório**: cada execução copia o fixture para um diretório
temporário criado com `mktemp -d` e sabota a cópia.

## As bases

| Base | Portão que ela alimenta | O que ela contém |
|---|---|---|
| `caminhos/` | `scripts/check-caminhos.sh` | um caminho nosso que existe, um caminho isento declarado e um molde `NNN` |
| `adrs-sucessao/` | `scripts/check-adrs-sucessao.sh` | dois ADRs sintéticos, um sucedendo o outro, com o par declarado nos dois lados, índice e registro |
| `rounds/` | `scripts/check-rounds.sh` | dois rounds com os sete campos, uma dependência acíclica e dois defeitos com um destino cada |
| `specs/` | `scripts/check-specs.sh` | um ciclo sintético com os quatro artefatos, as quinze seções, as duas tabelas de Constitution Check, a cauda e nota 96,7 na régua de prontidão do ADR 0004 §5 |
| `vazamento/` | `scripts/check-vazamento.sh` | uma base sintética declarada (personas de papel, organização fictícia), uma jornada cuja coluna de responsável guarda **papel**, um gerador que lê só a base local — e, de propósito, um ADR com bloco de evidência **citando o caminho da base real da irmã**: é o controle de regressão do critério antigo, que confundia citação com vazamento |

Base 100% sintética, por regra do ADR 0006: personas fictícias (**Facilitadora TOC**,
"Instituição Horizonte"), nenhum nome, enunciado ou data de pessoa real. A regra vale aqui
como vale em spec e em captura — fixture é exatamente onde a dívida da irmã
`gestaodeprioridades` nasceu.

## As sabotagens

A tabela viva está em `scripts/tests/run-sabotagem.sh` (a mutação e o trecho exigido moram
juntos, para não divergirem). Em resumo, 27 mutações cobrindo:

- **`check-caminhos.sh`** — caminho nosso inexistente; caminho de repositório não isento.
- **`check-adrs-sucessao.sh`** — antigo sem `Superseded by`; ADR sem `Princípios tocados`;
  ADR sem `Sucede`; ADR fora do `docs/records/decisoes.jsonl`; ADR fora do índice;
  sucessão apontando para ADR inexistente.
- **`check-rounds.sh`** — campo obrigatório ausente; dependência circular; dependência para
  round inexistente; defeito sem destino; defeito em dois destinos.
- **`check-specs.sh`** — artefato do ciclo ausente; seção obrigatória renomeada; spec sem
  RI; spec sem `Status`; DoD sem coluna de verificação; plano com uma tabela só; linha de
  princípio vazia; artefato condicional não declarado; cauda incompleta; **tabela de DoD
  sem nenhuma linha executável** — esta última passa no piso mecânico e cai só na régua de
  prontidão, por Testabilidade.
- **`check-vazamento.sh`** — nome próprio de pessoa num campo de pessoa; nome próprio numa
  coluna de responsável de tabela; registro no formato da base real da irmã (quatro campos
  do esquema dela no mesmo registro, que é como enunciado de trabalho e data de desempenho
  viajam mesmo sem nome); base real da irmã lida por código `*.py` deste repositório.

### Os nomes plantados são inventados, e isso foi verificado

As quatro mutações do `check-vazamento.sh` plantam um vazamento **de verdade** — é a única
forma de provar que o portão o vê. Os nomes usados são **inventados**, e a não-colisão com
a base real da irmã foi executada antes de escrevê-los, comparando conjuntos e imprimindo
apenas booleanos (`False`, `False`): nenhum dado dela foi copiado para cá, que é o ADR 0006
aplicado ao próprio teste da regra.

O dado plantado vive na **linha de mutação** do executor, e cada uma dessas linhas carrega
o marcador `SABOTAGEM-SINTETICA`. Ele é a **única isenção** do `check-vazamento.sh`, e é
estreita nas duas pontas: vale só dentro de `scripts/tests/` e só na linha que o carrega.
Fora dali não isenta nada; dentro dali, uma linha sem ele é achado como qualquer outra —
foi assim que o portão pegou uma das próprias linhas de mutação enquanto esta suíte era
escrita.

## Um achado que este diretório já pagou

A base `adrs-sucessao/` derrubou o `check-adrs-sucessao.sh` **na primeira execução**, antes
de qualquer sabotagem: o portão procurava a frase `Superseded by` em **qualquer** linha do
ADR, e o corpo do fixture — que *explica* a regra — passava a declarar-se sucedido. Portão
que mede a frase em vez do fato é o anti-padrão 13. A correção foi ler a declaração só na
linha de `Status`, que é onde a regra R5 a põe. O achado é a justificativa deste diretório
existir: nenhum humano teria lido aquele `if` e visto o defeito.
