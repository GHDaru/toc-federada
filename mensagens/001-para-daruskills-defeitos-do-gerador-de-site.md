# 001 — para `GHDaru/daruskills`: sete achados no gerador `spec-to-code-docs`

> Siglas deste documento: **TOC** — Teoria das Restrições; **ADR** — *Architecture Decision
> Record* (Registro de Decisão Arquitetural); **RF** — requisito funcional; **RI** —
> requisito de interface; **RNF** — requisito não funcional; **P1** — princípio "fronteira
> de escrita única" da constituição deste projeto; **R1** — regra "verifique antes de
> afirmar"; **HTML** — *HyperText Markup Language*.

- **Destino**: `GHDaru/daruskills`, skill `spec-to-code-docs`
- **Commit lido**: `da96a89c6a36fa58a33c6e7428ec780e08694d6d` (2026-09-03, *Initial:
  spec-to-code-docs skill*) — clone lido em `/home/user/daruskills`, somente leitura
- **Somas de verificação dos arquivos lidos** (`md5sum`, executado em 2026-09-03):
  `7e5e3daf2d881dea50b261671387edd2  daruskills/spec-to-code-docs/generate.py` ·
  `30c8d8218f3487a3a9426291b53e94e7  daruskills/spec-to-code-docs/render.py` ·
  `f23215aa36c63563b60dfb8cd7cce005  daruskills/spec-to-code-docs/templates/styles.css`
- **Origem do achado**: ciclo 001 da `toc-federada`, vendorização do gerador em
  `tools/product-site/` (ADR 0008)
- **Data**: 2026-09-03 · **Estado**: **aberta**

## Por que esta mensagem existe

O princípio **P1** proíbe escrever fora de `GHDaru/toc-federada`, e a nota de terceiros
deste repositório assume o compromisso explícito: *"correção de defeito de interesse geral
é **relatada** à origem (`mensagens/`, regra P1), nunca corrigida só aqui em silêncio"*
([`../THIRD-PARTY-NOTICES.md`](../THIRD-PARTY-NOTICES.md), §3). Ao adaptar a cópia
vendorizada, sete defeitos apareceram — cinco deles fazem o site **afirmar o que não leu**,
que é o oposto do que um gerador de rastreabilidade existe para fazer. Todos foram
reproduzidos rodando o gerador **de origem, sem alteração**, contra este repositório:

```
$ python3 /home/user/daruskills/spec-to-code-docs/generate.py /home/user/toc-federada --output orig.json
JSON written to orig.json
```

O corpus real, contado pela cópia adaptada e conferido por `grep -cE '^RF-[0-9]+:'` spec a
spec: **12 specs · 359 RF · 114 RI · 105 RNF · 176 fontes declaradas**.

## Achados

### A1 · Requisitos de interface não são extraídos (nenhum tipo além de RF e RNF)

`daruskills/spec-to-code-docs/generate.py:75-109` conhece duas famílias, `rf_pattern` e `rnf_pattern`.
Uma spec com `RI-NN` (requisito de interface), `RN-NN` (regra de negócio) ou `INT-NN`
(integração) perde tudo isso sem aviso.

- **Evidência**: a saída de origem não tem sequer a chave `ris`
  (`'ris' in spec` → `False`), e **114 requisitos de interface** ficaram invisíveis.
- **Consequência**: para qualquer projeto com taxonomia mais rica que RF/RNF, o site
  documenta uma fração do corpus e não diz que fração.
- **Sugestão**: parametrizar a expressão regular por prefixo (foi o que a cópia adaptada
  fez, em `tools/product-site/generate.py`, com a mesma família de padrão para todos os
  prefixos e a âncora de parada listando todos).

### A2 · Os princípios da constituição são injetados como RNF em **todas** as specs

`generate.py:606-611` copia os P1–P7 extraídos da constituição para dentro da lista de RNF
de cada spec.

- **Evidência**: a spec 004 volta com
  `['RNF01' … 'RNF10', 'P1', 'P2', 'P3', 'P4', 'P5', 'P6', 'P7']`; o total de RNF do
  repositório sai **189** na origem contra **105** reais — 84 requisitos inventados
  (7 princípios × 12 specs).
- **Consequência**: toda métrica de RNF do site fica inflada, e a matriz de rastreabilidade
  mostra o mesmo princípio sete vezes em doze lugares. Um número inflado num site de
  rastreabilidade é pior que número ausente: parece medido.
- **Sugestão**: extrair os princípios uma vez, como seção própria ("aplicam-se a todas as
  specs"), e mantê-los fora da contagem por spec.

### A3 · A fronteira das features é dividida por média, não pelo texto

`generate.py:277-282` usa os sub-cabeçalhos `###` que o autor escreveu (bom), mas mapeia
requisitos a eles por fatia de tamanho fixo: `chunk_size = len(rfs) // len(subheadings)`.

- **Evidência**, spec 004 (36 RF, 7 sub-cabeçalhos, `36 // 7 = 5`):

  | Feature | Origem diz | O texto diz |
  |---|---|---|
  | Nós no canvas | RF11–RF15 | **RF-11–RF-16** |
  | Arestas causais | RF16–RF20 | **RF-17–RF-20** |
  | Edição direta, desfazer e reverter | RF21–RF25 | **RF-21–RF-26** |
  | Vista tabular equivalente | RF26–RF30 | **RF-27–RF-31** |
  | Exportação e importação JSON | RF31–RF36 | **RF-32–RF-36** |

  Cinco das sete features carregam fronteira errada — e o `RF-16` aparece sob
  "Arestas causais" sendo que fala de exclusão de nó.
- **Consequência**: a associação requisito → feature, que é a espinha do site, fica errada
  sempre que os grupos tiverem tamanhos diferentes — ou seja, quase sempre.
- **Sugestão**: atribuir cada requisito ao último `###` que o precede (a posição já está
  disponível em `m.start()`).

### A4 · A expressão regular de fontes não aceita dígito no nome do arquivo

`generate.py:155` e `generate.py:486` procuram caminhos com esta expressão:

```
docs/[a-z_]+/[a-z_-]+\.md
```

A classe do nome do arquivo não inclui dígitos, então **nenhum ADR** é reconhecido como
fonte: `docs/adr/0002-stack-herdada-da-irma.md` não casa.

- **Evidência**: a origem devolve **87 fontes** contra as **176 declaradas** nas seções
  `## Fontes` das mesmas specs, e nenhum ADR entre elas.
- **Consequência**: a coluna "fonte legada" do site fica pela metade, e a porcentagem
  "rastreiam ao legado" mede o defeito, não o corpus.
- **Sugestão**: incluir `0-9` na classe. Sugestão maior: ler a seção `## Fontes` da própria
  spec quando ela existir — é lá que o autor declara o que consultou, com linha e trecho.

### A5 · Texto vindo do repositório entra em `innerHTML` sem escape

`render.py:956-957` interpola a descrição do requisito direto no template literal
(`${r.d||""}`), que vai para `innerHTML`.

- **Evidência**: o requisito RF-03 da spec 001 deste projeto cita o formato
  `NNN-para-<repo>-<assunto>.md`. No site gerado pela origem, `<repo>` e `<assunto>`
  **desaparecem** — o navegador os lê como etiquetas HTML desconhecidas. Neste corpus são
  15 requisitos com `<`.
- **Consequência**: perda silenciosa de conteúdo (e superfície de injeção, se algum dia o
  texto vier de fora do repositório).
- **Sugestão**: escapar o texto e só então reintroduzir a marcação desejada — a cópia
  adaptada tem `_md()` em `tools/product-site/render.py`, que escapa e devolve apenas
  `<code>` e `<b>`.

### A6 · O renderizador descarta os portões reais e inventa `F0✓ … F5○`

`render.py:1128-1147`: se algum portão do ciclo tiver texto com mais de cinco caracteres,
`needs_fix` fica verdadeiro e **todos** os portões são substituídos por uma tira fixa
`F0✓ F1✓ F2○ F3○ F4○ F5○`.

- **Consequência**: os portões que o roadmap descreve por extenso ("a junta fecha contra a
  `ghdaru` real", "migração aplicada e revertida sem resíduo") somem, e no lugar aparecem
  seis marcas de fases que ninguém executou. É dado inventado num site que promete
  rastreabilidade.
- **Sugestão**: renderizar o texto do portão. Se a tira compacta for desejável, que ela
  saia dos portões lidos, não de um molde.

### A7 · Taxonomia e workflow são fixos, e são de outro projeto

`render.py:63-79` fixa 15 termos e `render.py:270-276` os impõe **sempre**
(`# ALWAYS use the 15 fixed taxonomy terms`); `render.py:93-101` traz sete fases e
`render.py:265-266` as impõe quando o projeto declara menos de sete.

- **Evidência**: o termo "Aggregate Root" é mapeado, em qualquer repositório, para
  `"Partner, CatalogueItem, ASN, Auction, Billing"` (`render.py:75`) — os agregados do
  PROJETO_ECS. As fases citam "213 tabelas" e "Neon/Railway/Vercel" do mesmo projeto.
- **Consequência**: o site de um projeto qualquer afirma, com ar de dado, o vocabulário e o
  processo de **outro**. É o defeito de A2 e A6 em terceira forma: conteúdo que o gerador
  não leu, apresentado como se tivesse lido.
- **Sugestão**: manter os 15 termos e as fases como **exemplo do formato**, exigindo que o
  projeto os forneça (a cópia adaptada os escreve para a TOC e para as oito fases do método
  Maestro instalado aqui).

## O que **não** é achado

O `daruskills/spec-to-code-docs/templates/styles.css` foi mantido **byte a byte idêntico** na cópia vendorizada
(`md5sum` igual, colado acima): a régua de design é boa e não foi tocada. A estrutura de
quatro páginas, a casca compartilhada, o tema triplo (claro, escuro por preferência do
sistema, escuro por escolha) e a navegação lateral também foram preservados — o valor do
gerador está inteiro nessas escolhas.

## Como isto chega ao destino

Pelo caminho da convenção ([`README.md`](README.md)): esta mensagem **não é copiada** para
`daruskills`. O que atravessa a fronteira é o aviso de que ela existe, aberto pelo Product
Steward, caso a caso (P1). Até lá, a correção vive apenas na cópia vendorizada
(`tools/product-site/`), declarada como divergência conhecida da origem.
