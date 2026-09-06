# UX design 009 — Focalização (M6)

- **Spec**: [`spec.md`](spec.md) · **Data**: 2026-09-06 · **Agente**: `ux-semantics`
- **Por que este documento existe neste ciclo e não nos anteriores**: o M6 é o único módulo
  de superfície nova **sem protótipo do ciclo 002** (lacuna L-05). As telas da jornada não
  existiam em nenhuma das quatro gerações do TOC-Builder — a linhagem sabia desenhar as
  ferramentas e não sabia dizer qual é a restrição. Então o papel semântico nasce aqui,
  antes do componente (`ART:ux-design=yes`, tarefa T-09).

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **ARA** — Árvore da
> Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura ·
> **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **M1** — Núcleo de
> Diagramas Lógicos · **M6** — Focalização · **UI/UX** — interface / experiência de
> usuário · **RI/RF/RN** — requisito de interface / funcional / regra de negócio ·
> **i18n** — internacionalização · **IA** — inteligência artificial.

## Jornada servida

[`../../docs/jornadas/009-cinco-passos-de-focalizacao.md`](../../docs/jornadas/009-cinco-passos-de-focalizacao.md)
— a facilitadora precisa saber, a qualquer momento: **onde a análise está**, **qual é a
restrição vigente**, **o que falta para avançar** e **o que veio do ciclo anterior sem ter
sido julgado**. As quatro perguntas são o desenho inteiro.

## Papéis semânticos consumidos (já catalogados)

| Papel | Componente | Onde aparece |
|---|---|---|
| Estado de carregamento | `Carregando` ([`../../apps/web/src/componentes/Estados.tsx`](../../apps/web/src/componentes/Estados.tsx)) | listagem e tela da jornada |
| Estado de erro com recuperação | `EstadoDeErro` | listagem e tela da jornada |
| Estado vazio com próximo passo | `EstadoVazio` | listagem sem análises; herança sem decisões |
| Mensagem de erro traduzida por código | `mensagemDeErro` | falha ao criar, ao concluir, ao vincular |
| Recurso remoto com recarga | `useRecurso` | as duas telas |
| Tabela de listagem com ações | padrão do M1 (`tabela-de-projetos`) | `TelaDeAnalisesDeFocalizacao` |

## Papéis introduzidos (novos — entram no catálogo antes do uso)

| Papel | Anatomia obrigatória | Por que não deriva de um existente |
|---|---|---|
| **Trilha de progresso invariante** (`TrilhaDosPassos`) | os 5 passos sempre visíveis, na ordem; por passo: número, nome, marcador de estado **textual**, contagem de pendências, `aria-label` com estado por extenso | um *stepper* comum permite pular, criar e reordenar etapas. Aqui a fixidez é a regra de negócio (RN-01): a trilha **mostra os cinco mesmo quando quatro estão pendentes**, porque esconder é sugerir que o método é configurável |
| **Painel em três camadas** (`PainelDoPasso`) | topo somente leitura (herdado) → meio editável (trabalho) → rodapé de ato explícito (decisão) | a ordem é o argumento: pôr o produto do passo anterior **na frente** de quem vai decidir é o RF-13. Um formulário comum inverteria (campos primeiro, contexto num acordeão) |
| **Julgamento de peso igual** (`JulgamentoDeHeranca`) | dois `submit` idênticos, mesma classe, mesma justificativa obrigatória, contador de pendentes com `role="status"` | um par confirmar/cancelar tem hierarquia. Aqui `manter` e `revogar` **não podem** ter: se manter fosse mais barato, a interface empurraria a inércia de volta — exatamente o que o quinto passo existe para impedir (RN-05) |
| **Cartão de vínculo com estado do alvo** | ferramenta, nome, papel, selo canônico/não canônico, estado resolvido (`ativo`/`arquivado`/`ausente`) com legenda, navegação desabilitada quando ausente | é referência viva a outro agregado, não um link. O estado do alvo é resolvido no servidor a cada leitura, e a degradação legível é requisito (RNF-04) |
| **Linha do tempo de ciclos** (`LinhaDoTempo`) | um bloco por ciclo, em ordem, com restrição, nº de decisões e desfecho; ciclo fechado **somente leitura**, marcado como tal | um histórico comum é lista de eventos. Aqui cada item é um ciclo inteiro comparável com o seguinte — é o que torna visível "a restrição mudou" |

## Estados obrigatórios

- [x] **Vazio** — listagem sem análises usa `EstadoVazio` com o próximo passo (criar);
  herança sem decisões diz "nenhuma decisão herdada"; passo sem vínculos diz o que
  vincular ali seria canônico.
- [x] **Carregando** — `Carregando` sem salto de layout; a recarga depois de uma mutação
  mantém o dado anterior na tela (`dado` preservado enquanto `carregando`).
- [x] **Erro** — `mensagemDeErro` traduz o código estável do §A.7 (`INVALID_FOCUSING_STEP`,
  `INVALID_CYCLE`, `INVALID_CONSTRAINT`, `INVALID_TOOL_LINK`,
  `INVALID_INHERITED_DECISION`, `VERSION_CONFLICT`) para a frase que diz **como resolver**,
  não só o que quebrou.
- [x] **Sem permissão** — a mutadora `toc.suggest_constraint` **não aparece** quando a
  capability falta; a política é do servidor, a tela apenas projeta.
- [x] **Somente leitura** — ciclo fechado exibe aviso com `role="status"` e nenhum controle
  de escrita, em vez de controles desabilitados sem explicação.

## Decisões de desenho que o requisito obriga

1. **Estado nunca só por cor.** Cada passo carrega marcador textual (`✓`, `▶`, `·`) **e**
   o estado por extenso no `aria-label`; a tabela de listagem repete o passo atual em
   texto. Daltonismo e captura em tons de cinza continuam legíveis.
2. **A pendência é do mapa, não do botão.** O botão de concluir **não** some quando há
   pendência: apagá-lo esconderia a regra em vez de ensiná-la. A recusa vem do servidor
   com a regra nomeada, e a tela lista as pendências computadas ao lado.
3. **Vincular fora do canônico é possível — e exige motivo.** O `<select>` de ferramenta
   oferece as cinco; escolher fora do canônico do passo revela o campo de justificativa e
   desabilita o envio sem ele. O método educa; não bloqueia.
4. **Uma coluna de restrição na listagem.** RI-07 pede passo atual e restrição vigente como
   colunas de primeira classe — e é por isso que a focalização tem listagem própria em vez
   de uma linha a mais em `/toc/projetos`: nenhuma outra ferramenta tem essas duas colunas,
   e a tabela genérica ficaria cheia de células vazias.

## Acessibilidade (não é etapa final)

- [x] Rótulo acessível em todo controle sem texto visível: a trilha é `<nav>` rotulada, cada
  passo tem `aria-label` com posição, nome e estado; o grupo de vereditos é `role="group"`
  rotulado.
- [x] Foco de teclado visível e ordem previsível: a ordem do DOM é a ordem das três camadas
  (herdado → trabalho → decisão), que é a ordem em que se lê.
- [x] Contadores dinâmicos anunciados: pendências de herança, avisos de vínculo e o aviso de
  somente leitura usam `role="status"`.
- [x] Tabela com `<caption>` e `<th scope="col">`.
- [x] Nenhum literal solto: pt e en em [`../../apps/web/src/i18n/pt.ts`](../../apps/web/src/i18n/pt.ts)
  e [`../../apps/web/src/i18n/en.ts`](../../apps/web/src/i18n/en.ts).

## Achado que só a captura do build real pegou

O painel do passo mantinha o `<select>` de ferramenta com o valor canônico **do passo em que
foi montado**: ao navegar de `identificar` para `subordinar`, "vincular" ficava desabilitado
sem motivo aparente. Nenhum teste de unidade pegou, porque cada teste monta o painel uma vez.
A correção foi `key={passo.tipo}` no `PainelDoPasso` — que também limpa os rascunhos de nota
e de decisão ao trocar de passo, o que é o comportamento certo por outro motivo. Registrado
na jornada viva; é o argumento do P6 em uma linha.

<!-- GATE: o humano aprova o desenho antes da implementação (DoR, quando há interface). -->
