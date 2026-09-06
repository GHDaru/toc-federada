# 006 — para `GHDaru/maestro`: um colchete no texto anula a razão de um artefato condicional, e o portão diz "sem razão" sobre 401 caracteres de razão

> Siglas deste documento: **ADR** — *Architecture Decision Record* (Registro de Decisão
> Arquitetural); **P1** — princípio "fronteira de escrita única" da constituição deste
> projeto; **R1** — regra "verifique antes de afirmar"; **R4** — regra "caminho citado é
> caminho aberto"; **TOC** — Teoria das Restrições; **M6** — módulo Focalização desta
> aplicação.

- **Destino**: `GHDaru/maestro`, arquivo `scripts/check-conformance.sh`
- **Commit lido**: `534a088e62bcd2deb50353d5a6c60606a37e4e5f` — clone lido em
  `/home/user/maestro`, somente leitura (`.git/refs/heads/claude/toc-federada-roadmap-docs-rbtk5b`)
- **Origem do achado**: ciclo 009 da `toc-federada`, ao fechar os artefatos condicionais do
  módulo M6 e rodar `scripts/check-conformance.sh 009`
- **Data**: 2026-09-06 · **Estado**: **aberta**

## Por que esta mensagem existe

O princípio **P1** deste projeto proíbe escrever fora de `GHDaru/toc-federada`. Lacuna
encontrada em repositório de leitura vira artefato de mensagem, com evidência por
`arquivo:linha` — nunca correção silenciosa no destino, nunca aviso que morre na conversa.

Este achado tem um agravante que o torna urgente: **o remédio óbvio é piorar a
documentação**. Um agente apressado, vendo o portão dizer "razão ausente", apaga o link e a
referência entre colchetes do texto da razão — e o portão fica verde tendo tornado a razão
pior. Um portão que premia a piora é o oposto do que ele existe para fazer.

## O achado

`is_skeleton()` reprova qualquer texto que contenha o caractere `[`:

```
scripts/check-conformance.sh:202-205
is_skeleton() {  # $1 = candidate text
  local t="${1//[\`|*_ ]/}"
  [[ -z "$t" || "$t" == *"<"* || "$t" == *"["* ]]
}
```

A intenção é clara e correta: pegar o esqueleto do molde, cujos campos vêm como
`<preencha aqui>` e `[TÍTULO]`. O efeito colateral é que **a forma como a documentação
madura mais cita coisas** — o link em markdown `[texto](caminho)` e a referência a uma
lacuna ou dúvida numerada, `[DÚVIDA] 5`, `[L-05]` — passa a ser sinal de esqueleto.

Isso vale para as três chamadas, mas a que dói é a razão de um artefato condicional
(`scripts/check-conformance.sh:317-322`): quanto melhor a razão — porque cita o documento
do ciclo anterior que ela estende, ou a dúvida do Clarify que a decide —, maior a chance
de ela ser recusada.

## Como reproduzir (executado neste repositório, em 2026-09-06)

O trecho abaixo é a própria lógica do portão, aplicada às três declarações do `plan.md` do
ciclo 009 desta aplicação:

```text
$ for a in research data-model ux-design; do
    line="$(grep -m1 "ART:${a}=" specs/009-focalizacao/plan.md)"
    reason="$(sed -E "s/.*ART:${a}=[A-Za-z]*//" <<<"$line" | tr -d '|')"
    t="${reason//[\`|*_ ]/}"
    echo "$a  len=${#reason}  colchete=$([[ "$t" == *"["* ]] && echo SIM || echo NAO)"
  done
research  len=265  colchete=SIM
data-model  len=401  colchete=SIM
ux-design  len=343  colchete=SIM
```

E a saída do portão sobre exatamente essas três razões:

```text
$ ./scripts/check-conformance.sh 009
• 009-focalizacao
    ✗ research: declared ART:research=no with no reason — a declaration without a why is silence
    ✗ data-model: declared ART:data-model=yes with no reason — a declaration without a why is silence
    ✗ ux-design: declared ART:ux-design=yes with no reason — a declaration without a why is silence
```

401 caracteres de razão escrita, e o veredito é "with no reason". O que há de `[` nelas:

- `research`: `as dúvidas restantes são de produto ([DÚVIDA] 1–5)`;
- `data-model`: a razão cita, em link markdown, o `data-model.md` do ciclo 004 que ela estende;
- `ux-design`: `o [DÚVIDA] 5 confirma o arranjo no gate`.

Nenhuma delas é esqueleto. Todas as três são exatamente o que o comentário do portão pede:
"a declaração com o porquê".

O achado **não é do ciclo 009**: os ciclos 006 e 007 desta aplicação, já promovidos,
reprovam pelo mesmo motivo — `006` nas três declarações, `007` em `data-model`.

## A consequência

1. **O portão ensina a apagar a citação.** Corrigir a reprovação sem entender a causa
   significa remover o link e a referência numerada da razão. A `toc-federada` tem uma
   regra própria nascida de retrospectiva — **R4, "caminho citado é caminho aberto"** — que
   existe justamente para que a documentação cite arquivo por caminho. Os dois portões,
   lidos juntos, dizem coisas opostas.
2. **O ruído desmonta o portão inteiro.** Um repositório que vê três `✗` permanentes e
   sabe que são falsos deixa de ler a saída — e o dia em que aparecer um `✗` verdadeiro
   ninguém vai distinguir. É o anti-padrão do aviso que ninguém lê, produzido pela própria
   função de aptidão.
3. **A `is_placeholder()` herda o problema** (`scripts/check-conformance.sh:207-209`), com o
   mesmo teste de `[`, aplicado a evidência de cauda — onde prosa boa cita ainda mais.

## Sugestão — separada do achado, e é do método decidir

O que se quer pegar é **campo de molde não preenchido**, não a presença do caractere. Duas
formas de dizer isso sem apanhar prosa legítima:

- reconhecer o **par vazio ou de molde** em vez do caractere solto: `[ ]`, `[...]`, ou
  `[MAIÚSCULAS]` / `[TÍTULO]` — isto é, `\[[A-ZÀ-Ú _-]{2,}\]` —, deixando passar
  `[texto](caminho)` e `[DÚVIDA] 5`;
- ou, mais simples e provavelmente suficiente: **apagar links markdown antes do teste**
  (`s/\[([^]]*)\]\([^)]*\)/\1/g`) e só então procurar o colchete restante.

Qualquer das duas precisa da sabotagem correspondente na suíte do método — um `plan.md`
com razão de molde de verdade tem de continuar reprovando —, porque um remédio que só
afrouxa o portão troca um falso positivo por um falso negativo.

## O que este projeto fez enquanto isso

**Nada no código do portão, e nada no texto das razões.** As três razões do
`specs/009-focalizacao/plan.md` ficaram como estão, com os links e as referências, porque
apagá-las para agradar o portão seria exatamente o comportamento que esta mensagem denuncia.
O `✗` fica registrado como pendência declarada no `specs/009-focalizacao/qa-report.md`, com
esta mensagem citada — dívida com dono e endereço, não silêncio.
