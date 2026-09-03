# 002 — para `GHDaru/maestro`: os pisos de retroatividade do `check-conformance.sh` são absolutos e reprovam todo repositório recém-instalado

> Siglas deste documento: **DoD** — *Definition of Done* (definição de pronto);
> **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural);
> **P1** — princípio "fronteira de escrita única" da constituição deste projeto;
> **R1** — regra "verifique antes de afirmar"; **R2** — regra "portão verde declara
> quanto examinou"; **TOC** — Teoria das Restrições.

- **Destino**: `GHDaru/maestro`, arquivo `scripts/check-conformance.sh`
- **Commit lido**: `534a088e62bcd2deb50353d5a6c60606a37e4e5f` (2026-08-23) — clone lido em `/home/user/maestro`, somente leitura
- **Origem do achado**: ciclo 001 da `toc-federada`, no fechamento da DoD, ao rodar o portão
  que o próprio `CLAUDE.md` instalado manda rodar quando alguém pergunta se o método está
  sendo seguido
- **Data**: 2026-09-03 · **Estado**: **aberta**

## Por que esta mensagem existe

O princípio **P1** deste projeto proíbe escrever fora de `GHDaru/toc-federada`: lacuna
encontrada em repositório de leitura vira artefato de mensagem, com evidência por
`arquivo:linha`, nunca correção silenciosa nem aviso em conversa. O achado abaixo é do
método, não deste repositório, e por isso está aqui em vez de num commit lá.

## O achado

O `check-conformance.sh` é o portão que responde, de forma executável, à pergunta "estou
seguindo o método?" — o `CLAUDE.md` que o instalador escreve diz, em todas as instalações:
*"Asked 'are you following the method?' — do NOT answer from memory. Run
`scripts/check-conformance.sh <NNN>`"*. Ele carrega quatro pisos de retroatividade, e o
raciocínio deles é correto: uma regra vale a partir do ciclo que a introduziu, e a dívida
dos ciclos anteriores é declarada, não apagada.

O problema é que os pisos são **números absolutos de ciclo**, vindos da história do
repositório canônico:

```text
$ grep -nE '^(FLOOR|CRIT_FLOOR|ABSENCE_FLOOR|MUT_FLOOR)=' /home/user/maestro/scripts/check-conformance.sh
52:FLOOR="${MAESTRO_MIN_CYCLE_CONFORMANCE:-42}"
54:CRIT_FLOOR="${MAESTRO_MIN_CYCLE_CRITERIA:-45}"
77:ABSENCE_FLOOR="${MAESTRO_MIN_CYCLE_ABSENCE:-61}"
91:MUT_FLOOR="${MAESTRO_MIN_CYCLE_MUTATION:-55}"
```

Um repositório que acabou de instalar o método pelo caminho oficial (`maestro init`) começa
no ciclo **001** e abre os ciclos seguintes com `new-cycle.sh`. Ele levará **42 ciclos** para
alcançar o primeiro piso e **61** para alcançar o último. Até lá, o portão que existe para
dizer se o método está sendo seguido não olha para quase nada — e ainda assim reprova.

## Como reproduzir (executado neste repositório, em 2026-09-03)

O repositório tem 12 ciclos planejados, o ciclo 001 fechado com a cauda completa e evidência
colada, e os quatro portões locais verdes. Mesmo assim:

```text
$ scripts/check-conformance.sh 001 ; echo "exit=$?"
cycles checked: 1
✗ mutation floor 55 is above the newest cycle 012 — TAIL:mutation was charged to nobody.
✗ declared-absence floor 61 is above the newest cycle 012 — 'pendente' would pass as evidence everywhere.
✗ the method did not survive into the artifacts of at least one cycle.
exit=1
```

As três linhas de reprovação não falam do ciclo 001: falam de que o ciclo **mais novo do
repositório** (012) é menor que os pisos. O portão está reprovando o repositório por ser
novo, e o texto que ele imprime diz exatamente o que isso custa — *"TAIL:mutation was
charged to nobody"*, *"'pendente' would pass as evidence everywhere"*.

Apertando os pisos até o rigor máximo — os botões do próprio script só admitem apertar,
nunca afrouxar, o que é uma decisão boa e que preservamos —, o mesmo repositório passa:

```text
$ MAESTRO_MIN_CYCLE_CONFORMANCE=1 MAESTRO_MIN_CYCLE_CRITERIA=1 \
  MAESTRO_MIN_CYCLE_MUTATION=1 MAESTRO_MIN_CYCLE_ABSENCE=1 \
  scripts/check-conformance.sh 001 ; echo "exit=$?"
──
cycles checked: 1
✓ every cycle checked declares its artifacts and carries the closing tail with evidence.
exit=0
```

Ou seja: sob a leitura **mais severa possível** do método, o ciclo 001 passa; sob a leitura
padrão, reprova. Um portão cuja saída padrão é mais frouxa **e** mais vermelha que a sua
leitura severa ensina o leitor novo a ignorá-lo — e o primeiro repositório a instalar o
método é justamente onde a instrução "não responda de memória, rode o portão" mais importa.

## A consequência

Toda instalação nova do Maestro nasce com o portão de conformidade vermelho por um motivo
que não tem relação com a qualidade do trabalho dela, e verde-por-omissão nas regras que os
pisos protegem. Quem instala o método hoje tem três saídas, e nenhuma boa: ignorar o
vermelho (que era o que o portão existia para impedir), fixar os botões em toda invocação
(o que este repositório fez, e está registrado no `qa-report.md` do ciclo 001), ou apagar
o portão da sua DoD.

## Sugestão — separada do achado, e é do método decidir

O achado acima é fato verificável; o que segue é opinião de quem o encontrou.

Os pisos parecem querer dizer "a partir de quando esta regra vale", e isso é uma pergunta
sobre a **história do repositório onde o script roda**, não sobre um número universal. Duas
formas de dizer a mesma coisa sem quebrar a instalação nova:

1. Piso relativo à instalação: gravar no `.maestro/install-options.json` (que o instalador
   já escreve) o ciclo a partir do qual o método está instalado, e comparar com ele. Num
   repositório novo o piso vira 001 e todas as regras valem desde o começo, que é o
   comportamento que se quer de quem começa hoje.
2. Piso por marcador de regra: em vez de um número, a data ou o ciclo da regra ficarem no
   artefato que a introduziu, e o script perguntar ao repositório.

A alternativa "abaixar os números" não resolve: eles voltam a envelhecer no ciclo seguinte.

## O que este projeto fez enquanto isso

Nada no `maestro` — é leitura (P1). Aqui, o ciclo 001 registrou no seu `qa-report.md` a
reprovação **como vermelha**, com a causa raiz e a medição dos dois lados, em vez de
esconder o vermelho ou de declarar verde o que não é. O veredito substantivo foi obtido
apertando os pisos, nunca afrouxando.
