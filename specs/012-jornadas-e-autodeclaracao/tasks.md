# Tasks 012 — Jornadas e autodeclaração (ciclo planejado)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** — Definition of
> Done (Definição de Pronto) · **P6** — princípio "Jornada viva" da constituição do projeto
> · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **ARF** — Árvore da
> Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
> **S&T** — Árvore de Estratégia & Táticas · **UI** — interface de usuário · **UX** —
> experiência de usuário · **IA** — inteligência artificial · **CI** — integração contínua ·
> **HTTP** — HyperText Transfer Protocol · **i18n** — internacionalização.
>
> **Ciclo planejado no 001, não executado.** Nenhuma caixa se marca antes do fato: as
> marcações abaixo estão vazias de propósito. Este ciclo **não entrega funcionalidade** —
> quem encontrar uma correção de produto a leva à spec do módulo dono, e não a resolve de
> passagem aqui. Toda evidência vai para o [`qa-report.md`](qa-report.md) com a saída colada
> (regra R1) e o tamanho examinado (regra R2).

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 17 linhas da spec § Critérios de aceite) e
  conferir as pré-condições do roadmap: **ciclos 009, 010 e 011 promovidos**; as seis
  jornadas com script de captura versionado; aplicação publicada e alcançável num ambiente
  com base sintética. · Dep: — · Ref: [`spec.md`](spec.md) § Critérios de aceite;
  [`plan.md`](plan.md) § Gates (DoR); spec L-03 · Aceite: cada linha tem comando; as
  promoções verificadas por registro, não por memória.

## Frente 1 — Jornadas vivas consolidadas

- [ ] T-02 — Regerar as capturas das seis jornadas (J-01 a J-06) a partir do build atual,
  pelos scripts versionados, e comparar com as commitadas: diferença vazia, **ou** achado
  nomeado (jornada, captura, o que mudou). · Dep: T-01 · Ref: RF-01, RF-02; spec F-08, F-10
  · Aceite: DoD 1 e 2 — duas execuções seguidas produzem imagens idênticas; nenhuma
  atualização silenciosa de captura.
- [ ] T-03 — **Jornada de travessia**: a análise sintética da "Instituição Horizonte"
  atravessando ARA → NC → ARF → APR → AT com a focalização costurando, uma persona só do
  primeiro ao último elo, cada captura declarando o ciclo em que a tela nasceu. · Dep: T-02
  · Ref: RF-03, RF-04; RI-02 · Aceite: DoD 4 — o UDE que abre a análise é o mesmo que fecha;
  nenhum nome fora da base sintética (ADR 0006).
- [ ] T-04 — Função de aptidão de **captura órfã nos dois sentidos**: nenhuma captura sem
  jornada que a cite, nenhuma jornada citando captura inexistente; e o índice de jornadas
  com ciclo de nascimento, estágio e número de capturas. · Dep: T-02 · Ref: RF-06, RF-07;
  RI-01 · Aceite: DoD 3 — código 0 e as duas contagens impressas (R2); apagar uma captura
  citada derruba o portão (`TAIL:mutation`).

## Frente 2 — Conformidade executável do Nível 1

- [ ] T-05 — Executar a suíte de conformidade do Nível 1 do `GHDaru/protocolos` **de fora**,
  contra a URL publicada da aplicação, com perfil de adaptação versionado neste repositório
  se a nossa superfície divergir do canônico em endereço ou vocabulário. · Dep: T-01 · Ref:
  RF-13, RF-15, RF-16, RNF-03, RNF-07; spec F-05, F-09; INT-01 · Aceite: DoD 8 e 9 —
  relatório integral; cada tradução do perfil listada; nenhuma operação declarada ausente
  para escapar de check; nenhuma credencial em arquivo ou na saída.
- [ ] T-06 — Registrar a execução como **registro datado e imutável**: data, versão da
  norma, alvo, revisão do nosso código, perfil aplicado, veredito **como saiu** — e a lista
  dos itens que a caixa-preta não alcança, um a um, com a evidência interna de cada
  (caminho + teste próprio). · Dep: T-05 · Ref: RF-14, RF-17, RF-18, RNF-02; spec F-06,
  F-07 · Aceite: DoD 10 — nenhum item declarado contado como verificado; se o veredito for
  "não apto", cada falha sai com a decisão associada.

## Frente 3 — Matriz de aderência preenchida

- [ ] T-07 — Preencher
  [`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md) linha a
  linha: evidência com caminho e teste nas atendidas, **o que falta** nas parciais,
  **condição de reentrada** nas fora do alvo, delegação com ADR e a metade que continua
  nossa nas delegadas; e gravar a revisão datada no registro do próprio documento. · Dep:
  T-01 (evidência definitiva depois de T-06) · Ref: RF-08..RF-12; spec F-01, F-12, F-15 ·
  Aceite: DoD 6 e 7 — nenhuma célula de evidência vazia em linha atendida ou parcial;
  contagem por status impressa; `scripts/check-caminhos.sh` código 0 sobre as evidências.

## Frente 4 — Avaliação, autodeclaração e site

- [ ] T-08 — **Avaliação heurística datada do conjunto**: quem avaliou, quando, em que
  contexto, o que **não** foi avaliado; cada achado com severidade e destino (corrigido
  aqui, ou dívida com dono no módulo correspondente — nunca conserto de passagem). · Dep:
  T-02, T-03 · Ref: RF-05; RI-03; plan § Decisões 6 · Aceite: DoD 5 — limite declarado antes
  da tabela de achados; nenhum achado sem destino.
- [ ] T-09 — **ADR de autodeclaração**: Nível 2 (Operador), **lado aplicação** do Anexo B,
  com a cláusula que obriga a declaração por lado citada, a maturidade dos itens
  experimentais declarada, os limites nomeados (não há suíte executável para o Nível 2 nem
  para o lado aplicação — e por quê), e uma linha por requisito derivada da matriz. · Dep:
  T-06, T-07 · Ref: RF-19..RF-22; spec F-02, F-03, F-04, F-14 · Aceite: DoD 11 e 12 — todo
  veredito da declaração aparece na matriz com a mesma evidência; campo "Princípios tocados"
  preenchido (P2, e o que mais tocar) e alternativas descartadas com número real (R1).
- [ ] T-10 — Registrar o ADR: entrada no índice de ADRs e linha no índice de decisões por
  `scripts/record-decision.sh` — nunca editando `docs/records/decisoes.jsonl` à mão. · Dep:
  T-09 · Ref: RF-19; regra R5 · Aceite: DoD 13 — `scripts/check-adr.sh` código 0.
- [ ] T-11 — Regerar o **site de produto** pelo gerador versionado (ADR 0008), com
  navegação por módulo, ciclo e requisito, rastreabilidade nos dois sentidos e a nota de
  honestidade; provar que o commitado não diverge do gerado. · Dep: T-04, T-08, T-09 · Ref:
  RF-23, RF-24; RI-04..RI-06; RNF-04 · Aceite: DoD 14 e 15 — diferença vazia na CI;
  sabotagem (acrescentar um requisito a uma spec) muda a contagem exibida sem edição manual.

## Fechamento

- [ ] T-12 — Rodar TODAS as aptidões (as 17 linhas da DoD + os portões do método), colar
  saída, código de saída e tamanho examinado no [`qa-report.md`](qa-report.md); busca
  negativa de dado real de pessoa em capturas, relatórios e páginas do site; atualizar
  `CHANGELOG.md`; escrever a **retrospectiva do fechamento da versão 1** (o que virou regra
  versionada). · Dep: T-10, T-11 · Ref: DoD 16 e 17; RNF-06 · Aceite:
  `scripts/check-conformance.sh 012` código 0; nenhuma célula preenchida sem comando
  executado (R1).

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem preencheu a matriz não a
  revisa): conferir **linha a linha** que todo veredito da autodeclaração aparece na matriz
  com a mesma evidência; ler o perfil de adaptação contra a superfície real (adaptação ou
  lavagem?); conferir que nenhuma cláusula que depende do hospedeiro foi declarada como
  nossa (spec L-02); e a seção Fontes da spec por amostragem. · Dep: T-01..T-12

- [ ] TAIL:security — Passagem de segurança em contexto fresco: credencial em perfil, em
  variável de ambiente ou **na saída colada** do relatório; dado real de pessoa em captura,
  relatório ou página do site; e o que a autodeclaração revela sobre a superfície ao
  circular fora do repositório (endereços internos, códigos de erro, nomes de rota). · Dep:
  T-05, T-06, T-11

- [ ] TAIL:mutation — Sabotar e ver recusar: apagar uma captura citada por uma jornada
  (portão do T-04), esvaziar uma célula de evidência de linha atendida (portão do T-07),
  acrescentar um requisito a uma spec e conferir que a contagem do site muda sozinha (T-11),
  e declarar uma operação ausente no perfil para confirmar que o check **falha** em vez de
  ser pulado (T-05). Cada sabotagem com o comando e a recusa que imprimiu. · Dep: T-04,
  T-05, T-07, T-11

- [ ] TAIL:gate — Portão humano: o Product Steward lê a matriz e o relatório da suíte,
  **assina a autodeclaração** (é ela que circula para fora), decide sobre a publicação
  externa ([DÚVIDA] 2) e registra a decisão de merge em `docs/records/decisoes.jsonl` via
  `scripts/record-decision.sh`. Fecha a versão 1. · Dep: tudo
