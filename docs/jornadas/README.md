# Jornadas vivas — o que mora aqui, e o que ainda não pode morar

> **Siglas**, na primeira ocorrência: **TOC** — Teoria das Restrições · **ARA** — Árvore da
> Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
> **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Árvore de
> Estratégia & Táticas · **UDE** — Efeito Indesejável (*Undesirable Effect*) · **OI** —
> Objetivo Intermediário · **APH** — Aplicação ↔ Harness, o padrão da fronteira · **P6** —
> o princípio "Jornada viva" da constituição do projeto · **ADR** — Registro de Decisão
> Arquitetural · **API** — interface de programação de aplicações.

- **Status**: quatro jornadas vivas · **Capturas geradas em**: 2026-09-06

## A regra que manda aqui

A Iron Law da skill `living-journey` é curta: **jornada sem captura do build real é
ficção — e heurística sem data é ficção vencida.** Um documento desta pasta só existe
quando as suas capturas foram geradas do build por script versionado, com avaliação
heurística datada, tudo no mesmo pull request (P6).

Enquanto o ciclo 001 escreveu este arquivo, não havia build nenhum e a pasta abriu com um
README e nenhuma jornada. Agora há build: serviço FastAPI em
[`../../apps/api`](../../apps/api), interface React em [`../../apps/web`](../../apps/web),
PostgreSQL de verdade. As jornadas abaixo nasceram desse build.

**Nunca entra**: dado real de pessoa. Toda jornada usa a base sintética da Instituição
Horizonte ([`../produto/dados/`](../produto/dados/README.md) — ADR 0006), com personas que
são papéis e não pessoas. É essa regra que mantém o repositório apto a ser aberto, e
`scripts/check-vazamento.sh` é o portão.

## Como as capturas nascem

Um script só, versionado, sobe **tudo** e percorre a aplicação com um navegador de verdade:

```bash
PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node docs/jornadas/scripts/capturar-telas.mjs
```

Pré-requisito único: o PostgreSQL de desenvolvimento de pé. O script sobe o `toc-api` com
os seis parâmetros de admissão do §B.4 preenchidos, três instâncias da interface (autônoma,
embarcada e sem admissão) e um **hospedeiro de bancada** que fala o `ghd.*` e responde
`POST /auth/introspect`; percorre as jornadas; grava as imagens em
[`capturas/`](capturas/); e escreve [`capturas/manifesto.json`](capturas/manifesto.json)
com o tamanho e o resumo criptográfico de cada uma, mais as medidas colhidas na corrida.

Saída da corrida de 2026-09-06, últimas linhas, copiadas:

```text
33 captura(s), 5144889 bytes, 0 falha(s), 44.3s
```

Se uma captura não sair, o script **sai diferente de zero** e a falha entra no manifesto.
Não existe imagem de outro dia costurada num documento de hoje.

## O portão que guarda esta pasta

A Iron Law da skill é uma frase, e frase não reprova nada. O portão
[`../../scripts/check-jornadas.sh`](../../scripts/check-jornadas.sh) mede quatro
invariantes e sai diferente de zero quando qualquer uma cai:

| Invariante | O que exige |
|---|---|
| **J1** | toda captura em `capturas/` é citada por **exatamente uma** jornada — captura órfã é defeito, e captura citada duas vezes não tem dono que a regenere |
| **J2** | toda imagem citada por uma jornada existe em disco |
| **J3** | toda jornada traz `## Avaliação heurística — AAAA-MM-DD`, e a data **não é anterior** à das capturas (que o manifesto declara). É o passo que a skill chama de "o que todo mundo esquece" |
| **J4** | toda jornada declara o comando que regenera as capturas dela, e o gerador citado existe |

```text
$ scripts/check-jornadas.sh
── Jornadas vivas: captura, citação e heurística datada (P6) ──
  jornadas examinadas: 5 (001-chegada-e-embarque.md, 002-primeiro-projeto-e-ara.md, 003-nuvem-de-conflito.md, 007-a-travessia.md, 009-cinco-passos-de-focalizacao.md)
  capturas em disco: 52  ·  citações de imagem: 52  ·  data das capturas (manifesto): 2026-09-06
  invariantes: J1 órfã/duplicada · J2 citada e inexistente · J3 heurística datada e >= captura · J4 comando de regeneração
  verificações executadas: 114  ·  heurísticas datadas: 5/5  ·  comandos de regeneração: 5/5

✓ toda captura é citada por exatamente uma jornada, toda imagem citada existe,
  toda jornada traz heurística datada não anterior às capturas e o comando que as regenera.
```

**E o portão sabe reprovar**: cinco sabotagens em `scripts/tests/run-sabotagem.sh` mutam
uma cópia da fixture (`scripts/tests/sabotagem/jornadas/`) — captura órfã, imagem citada e
inexistente, heurística sem data, heurística mais velha que a captura e jornada sem comando
de regeneração — e cada uma tem de derrubá-lo **pelo motivo declarado**.

## As jornadas

| J | Jornada | Documento | Capturas | Estágio |
|---|---|---|---|---|
| J-01 | Chegada e embarque | [`001-chegada-e-embarque.md`](001-chegada-e-embarque.md) | 5 | 🟢 viva |
| J-02 | Primeiro projeto e ARA | [`002-primeiro-projeto-e-ara.md`](002-primeiro-projeto-e-ara.md) | 16 | 🟢 viva |
| J-03 | Nuvem de Conflito | [`003-nuvem-de-conflito.md`](003-nuvem-de-conflito.md) | 10 | 🟢 viva |
| J-04 | Da injeção ao plano (ARF → APR → AT) | — | — | 🟡 planejada (ciclo 008) |
| J-05 | Focalização | — | — | 🟡 planejada (ciclo 009) |
| J-06 | Estratégia & Táticas | — | — | 🟡 planejada (ciclo 010) |
| **J-07** | **A travessia — da ARA à Nuvem** | [`007-a-travessia.md`](007-a-travessia.md) | 5 | 🟢 viva |

### Por que J-04, J-05 e J-06 continuam sem documento

**Porque as ferramentas delas não existem no build**, e escrever a jornada assim mesmo
seria exatamente a ficção que a Iron Law proíbe. A evidência é uma listagem, não uma
lembrança:

```text
$ ls apps/api/src/toc_api/dominio/ | tr '\n' ' '
__init__.py __pycache__ analise.py ara.py criterios_ude.py erros.py eventos.py
federacao formulacao.py geracao.py grafo.py identidade.py lexico.py nuvem.py
portas.py projeto.py valores.py

$ ls apps/web/src/telas/ | tr '\n' ' '
TelaDaAra.test.tsx TelaDaAra.tsx TelaDaLixeira.tsx TelaDaNuvem.test.tsx
TelaDaNuvem.tsx TelaDeProjetos.test.tsx TelaDeProjetos.tsx registro.test.ts
registro.ts
```

Há domínio para grafo (M1), ARA (M2) e Nuvem (M3), e quatro telas. Não há módulo de ARF,
APR e AT (M4, ciclo 008), nem de focalização (M6, ciclo 009), nem de S&T (M5, ciclo 010).
As três jornadas nascem nos ciclos delas, com as capturas delas.

### Por que J-07 entrou na lista

A lista "cresce por decisão, não por acúmulo", e esta é a decisão: **o encadeamento entre
duas ferramentas não pertence a nenhuma das duas.** A escolha dos efeitos acontece na tela
da ARA, a rastreabilidade aparece na tela da Nuvem, e o que importa é justamente a costura
entre elas — o requisito INT-05, e a única coisa que nenhuma das quatro gerações da
linhagem TOC-Builder entregou. Documentá-la dentro da J-02 a esconderia no fim de uma
jornada longa; dentro da J-03, no começo de outra. Ela é a sua própria jornada.

## O que estas jornadas encontraram

Uma jornada viva que só elogia não está olhando. As quatro avaliações heurísticas de
2026-09-06 registraram **22 achados** e **20 itens conformes** — contados pelos portões
do próprio repositório:

```text
$ for f in docs/jornadas/00{1,2,3,7}-*.md; do echo -n "$f "; grep -cE '^\| A-[0-9]+ \|' "$f"; done
docs/jornadas/001-chegada-e-embarque.md 5
docs/jornadas/002-primeiro-projeto-e-ara.md 7
docs/jornadas/003-nuvem-de-conflito.md 7
docs/jornadas/007-a-travessia.md 3

$ grep -hcE '^\| ✅ \|' docs/jornadas/00{1,2,3,7}-*.md | paste -sd+ | bc
20
```

Dos 22, 4 achados são de severidade **Alta** — o quarto entrou com a travessia e ficou
fora desta tabela por uma corrida, que é exatamente o defeito que o portão
[`../../scripts/check-evidencia-colada.sh`](../../scripts/check-evidencia-colada.sh)
passou a reprovar:

| Achado | Onde | Severidade |
|---|---|---|
| A sessão nascida do embarque autentica `/aph/*` (`200`) mas não `/toc/*` (`401`): embarcada de verdade, a aplicação não carrega conteúdo | [J-01](001-chegada-e-embarque.md) A-01 | Alta |
| A ficha do UDE mostra o veredito antigo depois de "Reformular", até ser fechada e reaberta | [J-02](002-primeiro-projeto-e-ara.md) A-02 | Alta |
| "Ajustar à tela" enquadra a árvore abaixo da dobra: canvas visível vazio com 16 nós no projeto | [J-02](002-primeiro-projeto-e-ara.md) A-03 | Alta |
| A linha de origem da nuvem derivada identifica o projeto por identificador universal em vez do nome, e não diz quais efeitos foram promovidos | [J-07](007-a-travessia.md) A-01 | Alta |

Nenhum deles foi corrigido neste lote, e a razão está escrita em cada documento: são
mudanças em código de produção, e código de produção aqui nasce por ciclo, com spec e com
o teste que falha antes (P4). O que este lote entrega é o **diagnóstico com evidência por
`arquivo:linha`** — que é o insumo do ciclo que os corrigir.

## Limites declarados destas avaliações

- **Quem avaliou**: um agente, em contexto de construção, sobre as capturas geradas na
  mesma data. Não houve revisão independente em contexto fresco destas avaliações.
- **Não houve teste com pessoa usuária.** Nenhum achado vem de observação de uso real;
  todos vêm de inspeção heurística e de medição no navegador.
- **O hospedeiro da J-01 é uma bancada**, não a `ghdaru`. Ela prova o lado da aplicação da
  junta; não prova o lado do hospedeiro.
- **As capturas não regeneram byte-idênticas entre dias**: a lista de projetos mostra a
  data da última alteração, e os identificadores de projeto são novos a cada corrida. O que
  regenera é o percurso e o conjunto de arquivos — o manifesto guarda tamanho e resumo
  criptográfico de cada corrida para a comparação ser possível.
