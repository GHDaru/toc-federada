# Tasks 011 — Fundações da aplicação (ciclo planejado)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** — Definition
> of Done (Definição de Pronto) · **TDD** — Test-Driven Development (desenvolvimento
> guiado por teste) · **i18n** — internacionalização · **UI** — interface de usuário ·
> **UX** — experiência de usuário · **OTel** — OpenTelemetry · **CI** — integração
> contínua · **JSON** — JavaScript Object Notation · **REST** — Representational State
> Transfer · **DDL** — Data Definition Language (linguagem de definição de dados) ·
> **RPO/RTO** — Recovery Point / Time Objective (objetivo de ponto / tempo de
> recuperação) · **IA** — inteligência artificial.
>
> **Ciclo planejado no 001, não executado.** Nenhuma caixa se marca antes do fato: as
> marcações abaixo estão vazias de propósito. Ordem TDD em toda tarefa de código — o teste
> vermelho antes da implementação —, e a evidência de cada aceite vai para o
> [`qa-report.md`](qa-report.md) com a saída colada (regra R1) e o tamanho examinado
> (regra R2).

## Verificação primeiro

- [ ] T-01 — Fixar a DoD executável do ciclo (as 18 linhas da spec § Critérios de aceite)
  nos caminhos reais do repositório e conferir a pré-condição do roadmap: **ciclo 008
  promovido** (as seis ferramentas existem, logo há o que documentar). · Dep: — · Ref:
  [`spec.md`](spec.md) § Critérios de aceite; [`plan.md`](plan.md) § Gates (DoR) ·
  Aceite: cada linha tem comando que roda localmente e na CI; nenhum critério subjetivo; a
  promoção do 008 verificada por registro, não por memória.

## Fundação de dados e de desenho

- [ ] T-02 — `data-model.md` do ciclo: preferência de idioma por (inquilino, usuário),
  agregado `Verbete`, objetos de valor `IdiomaEfetivo`, `ChaveDeMensagem` e
  `RelatoDeImportacao`, **com o plano de migração no formato expandir → preencher →
  alternar → parar de escrever → contrair**. · Dep: T-01 · Ref: spec § Entidades; RNF-05 ·
  Aceite: o documento declara o que **não** é domínio (mecanismo de i18n, acervo, rotina de
  restauração) e nenhuma revisão planejada muda estrutura e linhas ao mesmo tempo.
- [ ] T-03 — Migração Alembic da preferência de idioma, com `downgrade` testado em banco
  limpo, sem resíduo; nenhum caminho de execução emite DDL. · Dep: T-02 · Ref: RF-04,
  RNF-05, RNF-06 · Aceite: DoD 15 — `alembic upgrade head && alembic downgrade base` com a
  saída colada; teste que sobe a aplicação contra esquema incompatível e vê o arranque
  falhar **imprimindo a diferença**.
- [ ] T-04 — Adendo de `ux-design` das superfícies novas — painel de documentação com
  âncoras, relato de importação campo a campo, seletor de idioma, estado de tradução
  pendente —, referenciado ao desenho do ciclo 002
  ([`../002-prototipo-de-interfaces/spec.md`](../002-prototipo-de-interfaces/spec.md)):
  papel semântico antes do componente. · Dep: T-01 · Ref: RI-01, RI-04..RI-09; plan §
  Artefatos (`ART:ux-design=yes`) · Aceite: cada tela nova tem papel semântico declarado e
  estado vazio/erro desenhado antes de qualquer linha de UI.

## Internacionalização (E8.3) — TDD e portões

- [ ] T-05 — Resolução do **idioma efetivo** como função pura: preferência da pessoa →
  idioma do embarque → língua-fonte, com o motivo anexado ao resultado. Teste dos três
  caminhos escrito **antes** do resolvedor, visto falhar. · Dep: T-01 · Ref: RF-12, RF-14 ·
  Aceite: DoD 5 — os três caminhos verdes com o motivo verificado; queda ao padrão aparece
  em log estruturado.
- [ ] T-06 — Função de aptidão de **literal órfão**, nascida por sabotagem: planta-se
  `"Salvar"` num componente, o portão tem de pegá-lo nomeando arquivo e linha; a lista de
  exceções exige **motivo escrito por linha**. · Dep: T-05 · Ref: RF-07; spec L-05; plan
  risco GATE-excecao-sem-motivo · Aceite: DoD 2 — código 0 no repositório limpo, código ≠ 0
  com o literal plantado, e a saída imprime "N arquivos, M cadeias examinadas" (R2).
- [ ] T-07 — Função de aptidão de **paridade de dicionários** `pt` × `en`: chave só na
  língua-fonte é pendência listada; chave só na tradução é erro. · Dep: T-05 · Ref: RF-08 ·
  Aceite: DoD 3 — as duas contagens impressas; remover uma chave da tradução aparece como
  pendência, acrescentar uma chave órfã derruba o portão.
- [ ] T-08 — Interface: seletor de idioma com origem da escolha, aplicação do idioma
  efetivo a **toda** a superfície, persistência da preferência no servidor, formatação e
  colação localizadas, e chave ausente falhando alto em desenvolvimento. · Dep: T-03, T-04,
  T-06, T-07 · Ref: RF-06, RF-09..RF-11, RF-13, RF-15..RF-17; RI-01..RI-03, RI-11 ·
  Aceite: DoD 4, 6 e 7 — trocar idioma sem recarregar e sem perder o diagrama aberto;
  limpar o navegador e reabrir mantém o idioma; conteúdo escrito por pessoa e identificador
  inalterados nos dois idiomas.

## Documentação embutida (E8.4)

- [ ] T-09 — Acervo de verbetes (um por ferramenta registrada + o da focalização),
  bilíngue, com âncoras nomeadas e procedência citada; painel lateral com índice, foco
  devolvido ao fechar e carregamento sob demanda; portão de cobertura ferramenta ×
  verbete derivado do **registro de ferramentas**. · Dep: T-04, T-08 · Ref:
  RF-18..RF-24; RI-04..RI-06, RNF-09 · Aceite: DoD 8 e 9 — as duas contagens impressas;
  `scripts/check-caminhos.sh` código 0 sobre as procedências; remover um verbete derruba o
  portão (`TAIL:mutation`); nenhum texto gerado em tempo de execução por modelo (ADR 0007).

## Exportação e importação consolidadas (E1.4)

- [ ] T-10 — `PlanoDeConversao` e `RelatoDeImportacao` como domínio puro, TDD estrito: o
  teste com o arquivo sintético no formato da quarta geração — incluindo `chatHistory`
  preenchido e uma aresta órfã — é escrito **antes** do serviço e visto falhar. · Dep: T-01
  · Ref: RF-26, RF-27, RF-29; spec F-08, F-09 · Aceite: DoD 10, 11 e 12 — conversão correta;
  dois problemas geram dois itens no relato e nada é criado; histórico de conversa não
  persistido e contagem declarada no relato.
- [ ] T-11 — Adaptador de importação legada no caminho do M1 (reconhecimento por assinatura
  de conteúdo, teto de tamanho, projeto novo com relato) e **exportação consolidada** de
  projeto multi-ferramenta com os vínculos de encadeamento. · Dep: T-10 · Ref: RF-25,
  RF-28, RF-30..RF-32; RI-07..RI-09 · Aceite: DoD 13 — ida e volta com vínculos recriados e
  contados; medição da RNF-08 (200 nós, 300 arestas, percentil 95) colada. **Primeira
  tarefa a sair se o apetite estourar** (round 011).

## Unidade de restauração (F8.1.3)

- [ ] T-12 — **Ensaio de restauração**, cedo e independente: restaurar a cópia do provedor
  para um destino separado, subir a aplicação contra o destino, verificar a base sintética
  íntegra e escrever o relatório com instante alvo, duração, objetivo de ponto e de tempo de
  recuperação, e **o que não voltou** (arquivos fora do banco, índices reconstruídos). ·
  Dep: T-01 · Ref: RF-01..RF-03, RNF-04, RNF-10; plan risco GATE-apolice · Aceite: DoD 14 —
  saída do ensaio colada no `qa-report.md`, **sem credencial na saída**; se o plano do
  provedor não permitir, o resultado é um ADR com a alternativa, nunca um item pendente.

## Jornada e fechamento

- [ ] T-13 — Jornada viva do ciclo: uma pessoa da "Instituição Horizonte" troca de idioma,
  abre a documentação de uma ferramenta pela âncora e importa um arquivo da geração
  anterior (um caso aceito e um recusado) — capturas geradas por script versionado do build
  real **nos dois idiomas**, com avaliação heurística datada, no mesmo pull request. · Dep:
  T-08, T-09, T-11 · Ref: P6; DoD 17; RNF-11 · Aceite: capturas regeneram determinísticas;
  base 100% sintética (ADR 0006); busca negativa de nome real com saída colada.
- [ ] T-14 — Rodar TODAS as aptidões (as 18 linhas da DoD + os portões do método), colar
  saída, código de saída e tamanho examinado no [`qa-report.md`](qa-report.md); re-verificar
  a matriz de aderência ao APH
  ([`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)) no
  mesmo pull request; cobertura de requisitos linha a linha (RF/RI/RNF/RN/INT); atualizar
  `CHANGELOG.md`. · Dep: T-13, T-12 · Ref: DoD 18; INT-04 · Aceite:
  `scripts/check-conformance.sh 011` código 0; nenhuma célula preenchida sem comando
  executado (R1).

## Cauda (fechamento — nenhuma marcada antes da evidência no qa-report)

- [ ] TAIL:review — Revisão independente em contexto fresco (quem executou não revisa):
  spec × código × DoD, com atenção explícita aos dois portões novos (a lista de exceções do
  literal órfão tem motivo por linha? o portão de cobertura deriva do registro de
  ferramentas ou de uma segunda lista?) e à seção Fontes da spec por amostragem. · Dep:
  T-01..T-14

- [ ] TAIL:security — Passagem de segurança em contexto fresco: segredo no cliente e
  **segredo na evidência colada** (o risco próprio deste ciclo), teto e caminho da
  importação de arquivo, isolamento por inquilino na tabela nova de preferência, ausência de
  SDK ou chave de provedor, e dado real de pessoa em fixture, verbete ou captura. · Dep:
  T-11, T-09, T-12

- [ ] TAIL:mutation — Sabotar e ver recusar: literal plantado num componente (portão do
  T-06), chave removida da tradução e chave órfã acrescentada (T-07), verbete removido do
  acervo (T-09), arquivo legado com aresta órfã e com `chatHistory` (T-10), e uma migração
  que muda estrutura e linhas na mesma revisão (RNF-05). Cada sabotagem com o comando e a
  recusa que imprimiu. · Dep: T-06, T-07, T-10, T-09

- [ ] TAIL:gate — Portão humano de merge: DoD verde apresentada, saída do ensaio de
  restauração lida pelo Product Steward, jornada revista nos dois idiomas, respostas dos 5
  `[DÚVIDA]` registradas, decisão de merge gravada em `docs/records/decisoes.jsonl` via
  `scripts/record-decision.sh`. · Dep: tudo
