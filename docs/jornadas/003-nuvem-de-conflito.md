# J-03 · A Nuvem de Conflito

> **Siglas deste documento**, na primeira ocorrência: **TOC** — Teoria das Restrições ·
> **NC** — Nuvem de Conflito · **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
> Indesejável (*Undesirable Effect*) · **TRIZ** — Teoria da Resolução Inventiva de
> Problemas · **API** — interface de programação de aplicações · **IA** — inteligência
> artificial · **ADR** — Registro de Decisão Arquitetural · **P6** — o princípio "Jornada
> viva" · **RF/RI/RN** — requisito funcional / de interface / regra de negócio.

- **Estágio**: 🟢 viva — capturas do build real
- **Nasce no ciclo**: 007 · **Spec**:
  [`../../specs/007-nuvem-de-conflito/spec.md`](../../specs/007-nuvem-de-conflito/spec.md)
- **Capturas geradas em**: 2026-09-06 · **Avaliação heurística revisitada em**: 2026-09-06
- **Como regenerar** (a nuvem desta jornada é a que a travessia derivou, e por isso a
  corrente J-02 → J-07 → J-03 corre junta):

  ```bash
  PLAYWRIGHT_BROWSERS_PATH=/opt/pw-browsers node docs/jornadas/scripts/capturar-telas.mjs --jornada J-03
  ```

- **Base**: sintética, `docs/produto/dados/analise-horizonte.json` v1.0.0 — cinco
  entidades, sete arestas com premissa escrita, duas injeções. Instituição e personas
  **fictícias** (ADR 0006).

## Quem, e o que quer

A **Facilitadora TOC** entra na nuvem que acabou de derivar da árvore (jornada
[J-07](007-a-travessia.md)). O dilema da Instituição Horizonte é conhecido pelo grupo, e
ninguém consegue resolvê-lo discutindo: **abrir toda turma que atinja o mínimo de
matrículas** garante a receita do semestre, e **abrir só quando houver docente titular
alocado** garante a qualidade — as duas ações não cabem juntas.

O que ela quer da ferramenta não é uma resposta. É **escrever as premissas**: a frase que
cada seta está assumindo, para o grupo poder atacar a mais frágil em vez de negociar um
meio-termo entre as duas ações. É esse o método, e é isso que a nuvem tem de tornar
visível.

## O percurso

### 1 · O diagrama canônico, preenchido

As cinco entidades ganham o texto do grupo e cada uma das sete arestas recebe a sua
premissa. O cabeçalho passa de `0 de 7` para **`7 de 7 arestas com premissa`**, e o botão
"Arestas pendentes" fica desabilitado em `(0)`:

![O diagrama do conflito, completo](capturas/003-nuvem-de-conflito/01-diagrama-do-conflito.png)

Contagem medida, não estimada:

```text
  · arestas desenhadas no diagrama: 7
  · completude: 7 de 7 arestas com premissa · injeções criadas: 2
```

A leitura do diagrama, da esquerda para a direita:

| Posição | Texto |
|---|---|
| **A** — objetivo comum | A Instituição Horizonte forma turmas completas com alta taxa de conclusão. |
| **B** — necessidade | A instituição precisa de receita previsível a cada semestre. |
| **C** — necessidade | A instituição precisa de qualidade pedagógica em cada turma aberta. |
| **D** — ação | Abrir toda turma que atinja o mínimo de matrículas. |
| **D′** — ação oposta | Abrir turma somente quando houver docente titular alocado. |

E as sete arestas, com a classe que o domínio dá a cada uma: duas de **Necessidade**
(A↔B, A↔C), duas de **Pré-requisito** (B↔D, C↔D′), duas de **Perigo** (as diagonais
tracejadas em vermelho, D↔C e D′↔B) e uma de **Conflito** (D↔D′).

> **Não existe arrastar neste diagrama, e a ausência é decisão.** A topologia é fixa
> (RN-01): quem usa edita **texto**, não arruma caixas. As posições vêm do servidor.

### 2 · A ficha de uma aresta: a premissa que a sustenta

Clicar na aresta de conflito abre a ficha, com a leitura do elo no cabeçalho e a premissa
em estado **Vigente**:

![Ficha da aresta com premissa](capturas/003-nuvem-de-conflito/02-ficha-da-aresta-com-premissa.png)

> Esperar a alocação do docente titular faz a turma perder a janela de matrícula.

Dois botões guardam o método: **Desafiar premissa** (que exige justificativa escrita) e
**Arquivar premissa** (que responde quantas injeções foram junto — nunca em silêncio).

### 3 · A injeção nasce ligada à premissa que invalida

![Injeção ligada à premissa](capturas/003-nuvem-de-conflito/03-injecao-ligada-a-premissa.png)

> A alocação do docente titular acontece na abertura do calendário, antes da matrícula.
> Separação no tempo · Candidata

A injeção **não flutua**: ela mora dentro da premissa que ataca, carrega a classificação
TRIZ ("Separação no tempo") e um status próprio (Candidata / Escolhida / Descartada). É a
diferença entre "uma ideia que alguém teve" e "a coisa que derruba esta frase".

### 4 · A visão de solução: as sete posições espelhadas

![Visão de solução](capturas/003-nuvem-de-conflito/04-visao-de-solucao.png)

Cada uma das sete arestas vira uma posição lida por extenso — *"Para ter A Instituição
Horizonte forma turmas completas com alta taxa de conclusão., precisamos de A instituição
precisa de receita previsível a cada semestre."* — e as que ainda não têm injeção dizem
**"Sem injeção"** com a borda pontilhada. Nesta nuvem, duas das sete têm injeção e cinco
estão pendentes: a ferramenta mostra **o buraco**, não esconde.

### 5 · Conflito e solução, lado a lado

![Lado a lado](capturas/003-nuvem-de-conflito/05-lado-a-lado.png)

### 6 · A vista tabular

![Vista tabular](capturas/003-nuvem-de-conflito/06-vista-tabular.png)

Aresta × premissas × injeções, no mesmo dado. A escolha de visão **persiste na sessão**
(RI-08): quem está conduzindo um grupo não quer reescolher a visão a cada recarga.

### 7 · Gerar não aplica — a assistência entra como proposta

A Facilitadora cola a narrativa do dilema e pede **"Gerar a partir da narrativa"**. O que
volta é uma **pré-visualização**, e a tela diz isso com todas as letras antes de qualquer
conteúdo:

![Pré-visualização da geração](capturas/003-nuvem-de-conflito/07-previa-da-geracao.png)

> Nada foi aplicado: a escrita é da ação governada, com gate humano.

Abaixo do aviso vem o identificador da ação do catálogo — `toc.generate_conflict_cloud` —,
o racional, e um diff **Posição × Hoje × Proposto** para as cinco entidades, seguido das
sugestões de premissa por aresta (`A_B`, `A_C`, `B_D`, `C_D_PRIME`, `D_C`, `D_PRIME_B`,
`D_D_PRIME`) e da separação TRIZ sugerida para o conflito. O único botão de decisão visível
é **Recusar** — e recusar deixa o projeto exatamente como estava.

**É aqui que esta aplicação difere da linhagem que ela sucede.** Na 4ª geração, a mesma
operação era uma chamada de rede a um provedor de modelo de linguagem feita **do
navegador**, com a chave no cliente (`tocbuilderv3/services/geminiService.ts:16`), e o que
o modelo devolvia era gravado. Aqui não há cliente de provedor na interface: a geração é do
servidor, é ação nomeada do catálogo, e a escrita passa por proposta com portão humano
(ADR 0007 e P7).

## O que esta jornada prova

| Afirmação | Evidência |
|---|---|
| O diagrama desenha as **sete** arestas da topologia canônica | `arestas desenhadas no diagrama: 7` |
| Toda aresta pode carregar premissa escrita, e a completude é visível | `completude: 7 de 7 arestas com premissa`; cabeçalho na captura 01 |
| A injeção nasce presa à premissa que ataca, com classificação TRIZ e status | captura 03 |
| A visão de solução declara as posições **sem** injeção | captura 04 — cinco "Sem injeção" |
| O mesmo dado tem quatro projeções (conflito, solução, lado a lado, tabela) | capturas 01, 04, 05 e 06 |
| Gerar **não** escreve: devolve diff e o identificador da ação governada | captura 07 — "Nada foi aplicado…" + `toc.generate_conflict_cloud` |
| Nenhum segredo de provedor na interface | não há cliente de provedor em `apps/web`; a geração é rota do serviço |

## Avaliação heurística — 2026-09-06

Avaliada por um agente, em contexto de construção, sobre as capturas geradas nesta mesma
data. **Não houve teste com pessoa usuária.**

| # | Achado | Heurística | Severidade | Destino |
|---|---|---|---|---|
| A-01 | A leitura das arestas concatena as frases das entidades sem tratar a pontuação: *"…alta taxa de conclusão., precisamos de A instituição precisa…"* e *"…docente titular alocado. não podem coexistir"*. A visão de solução inteira é feita dessas leituras, então o defeito aparece sete vezes na mesma tela | Correspondência com o mundo real / estética | Média | 📝 registrado |
| A-02 | A pré-visualização da geração abre numa coluna estreita à esquerda enquanto a metade direita da janela fica vazia; o diff Hoje × Proposto fica com três a quatro palavras por linha | Estética e design minimalista | Média | 📝 registrado |
| A-03 | Na pré-visualização, o único botão de decisão é **Recusar** — não há "Aceitar" nenhum, e a tela não explica por onde a proposta seria aplicada. Está **coerente** com a regra (quem escreve é a ação governada com portão humano), mas quem lê a tela fica sem o próximo passo | Ajuda e documentação | Média | 📝 registrado |
| A-04 | O texto da injeção e a sua classificação aparecem grudados na visão de solução (*"…antes da matrícula.Separação no tempo · Candidata"*), sem separador | Estética | Baixa | 📝 registrado |
| A-05 | A linha de origem repete o identificador universal do projeto de origem em todas as visões (ver achado A-01 da jornada [J-07](007-a-travessia.md)) | Correspondência com o mundo real | Média | 📝 registrado em J-07 |
| ✅ | A completude (`7 de 7`) fica no cabeçalho, com salto direto para as pendentes | Visibilidade do estado do sistema | — | conforme |
| ✅ | As posições sem injeção são declaradas em vez de omitidas | Visibilidade do estado do sistema | — | conforme |
| ✅ | Gerar não aplica, e a tela diz isso antes do conteúdo | Prevenção de erro / controle e liberdade | — | conforme |
| ✅ | A topologia é fixa e não há arrastar: quem usa edita texto | Prevenção de erro | — | conforme |
| ✅ | Desafiar premissa exige justificativa; arquivar responde quantas injeções foram junto | Prevenção de erro / visibilidade | — | conforme |

### Rastro do achado A-01, por `arquivo:linha`

A leitura de cada aresta é montada no **servidor**, em
[`apps/api/src/toc_api/dominio/nuvem.py`](../../apps/api/src/toc_api/dominio/nuvem.py)
(método `leitura`), concatenando o texto das entidades com conectivos fixos. Como o texto
das entidades vem do grupo e termina em ponto, a junção produz `".,"` e `". não"`. A
correção é de domínio (aparar a pontuação final antes de concatenar), não de interface — e
por isso vale um teste puro, que é onde ela deve nascer.
