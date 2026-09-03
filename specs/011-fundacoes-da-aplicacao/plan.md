# Plan 011 — Fundações da aplicação (ciclo planejado)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** — Definition
> of Done (Definição de Pronto) · **DoR** — Definition of Ready (Definição de Prontidão) ·
> **TDD** — Test-Driven Development (desenvolvimento guiado por teste) · **DDD** —
> Domain-Driven Design (Design Orientado a Domínio) · **i18n** — internacionalização ·
> **UI** — interface de usuário · **UX** — experiência de usuário · **IA** — inteligência
> artificial · **LLM** — modelo de linguagem de grande porte (*Large Language Model*) ·
> **OTel** — OpenTelemetry · **CI** — integração contínua · **REST** — Representational
> State Transfer · **JSON** — JavaScript Object Notation · **YAGNI** — *You Aren't Gonna
> Need It* (não vai precisar disso) · **DDL** — Data Definition Language (linguagem de
> definição de dados) · **RPO/RTO** — Recovery Point / Time Objective (objetivo de ponto /
> tempo de recuperação) · **UDE** — Undesirable Effect (Efeito Indesejável) · **ARA** —
> Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **S&T** — Árvore de Estratégia
> & Táticas

- **Spec**: [`spec.md`](spec.md) (Rascunho — aprovação no gate humano que abre o ciclo) ·
  **Raia**: plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e é reconferido na
  abertura, com o ciclo 008 promovido.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 011 existe antes deste plano e antes de qualquer código do ciclo. O escopo é o do round 011 ([`../../docs/produto/rounds.md`](../../docs/produto/rounds.md)) e nada além; os 5 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura, e nenhum deles se resolve em silêncio durante a execução. Mudança de escopo volta à spec — inclusive a resposta ao `[DÚVIDA]` do idioma padrão, que altera o RF-12. |
| II. Human-governed orchestration | ✅ O humano decide: as respostas do Clarify, o número do teto de pacote (L-04), a periodicidade do ensaio de restauração e o merge. Agentes implementam por fronteira (i18n no cliente · acervo de documentação · conversão do formato legado · operação de restauração), e a revisão independente em contexto fresco (`TAIL:review`) fica com quem não implementou. O ensaio de restauração é executado por agente e **conferido** pelo humano, porque é dele o risco. |
| III. Reversibility / risk gates | ✅ Este é o ciclo em que a reversibilidade da fundação deixa de ser promessa: a restauração é **ensaiada** (RF-02) em destino separado, e o relatório declara o que não volta (RF-03). Migração com `downgrade` testado (RNF-06); estrutura e dado em revisões separadas, expandir → contrair (RNF-05); nenhuma DDL emitida por caminho de execução (RF-04). O irreversível deste ciclo — importar arquivo de fora — nasce não destrutivo por desenho: sempre projeto novo (RN-05). |
| IV. Test-first / verifiable DoD | ✅ TDD estrito nas duas peças de domínio novas: o serviço de conversão do formato legado (teste com o arquivo sintético legado antes do serviço) e a resolução de idioma efetivo (os três caminhos antes do resolvedor). DoD com 18 linhas executáveis, cada uma com comando; as duas funções de aptidão novas (literal órfão, paridade de dicionários) **imprimem o tamanho examinado** (R2), sem o que o verde não é evidência. `TAIL:mutation` remove um verbete e uma chave e vê os portões derrubarem. |
| V. Context economy / boundary | ✅ Quatro fronteiras independentes num ciclo, deliberadamente: i18n toca o cliente e uma tabela; documentação embutida é conteúdo + uma rota; conversão de formato é domínio puro; restauração é operação. Cada uma cabe num contexto próprio com a spec como integrador, e nenhuma depende do resultado da outra — é o que torna o corte de apetite (E1.4 sai primeiro) executável sem desmontar o resto. |
| VI. Living artifacts | ✅ Nenhum artefato novo sem função forçante: o dicionário é consumido pelo portão de literal órfão e pelo de paridade; o acervo de documentação, pelo portão de cobertura ferramenta × verbete e pelo `scripts/check-caminhos.sh` (procedência dos verbetes); o relato de importação, pelos testes de recusa; o relatório do ensaio, pela DoD 14. A matriz de aderência ao APH ([`../../docs/integracao/aderencia-aph.md`](../../docs/integracao/aderencia-aph.md)) é re-verificada no mesmo pull request (INT-04). |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI, com porta de volta declarada: idiomas além de pt/en (round 011, § Fora); migração automática de dados da linhagem (visão §7, pergunta 2 — quem quer, exporta e importa); interface de tradução colaborativa; documentação gerada em tempo de execução (proibida pelo ADR 0007, não só dispensada). O ciclo não cria processo novo: usa os portões que já existem e acrescenta dois. |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo da spec, deste plano, das tasks e do `qa-report.md`; os termos novos (língua-fonte, idioma efetivo, verbete, unidade de restauração, descarte declarado) são definidos onde nascem. A documentação embutida deste ciclo é ela própria um teste do princípio: verbete que estreia sigla sem expandir é achado de revisão. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. A linhagem (`/home/user/tocbuilderv3`) e a constituição da fundação (`/home/user/ghdaru/.specify/memory/constitution.md`) são leitura — os defeitos medidos nelas (spec F-03, F-04, F-09, F-12, F-16) são **fonte**, não conserto. Se o idioma do embarque não chegar pelo envelope (spec L-02), a rota é `mensagens/NNN-para-ghdaru-...`: relatar e parar, nunca editar o hospedeiro. |
| P2. Federação por contrato (APH) | ✅ O idioma do embarque entra como **dado, nunca instrução** (INT-01), e a aplicação funciona sem ele (RF-14) — o padrão de degradação da junta. Nenhuma ação de catálogo nasce aqui (INT-03): trocar idioma cabe no item 8 (alvo único nomeado pelo gesto, valor literal no controle, reversível na sessão) e importar arquivo segue a política por tipo de ação do ciclo 004. As telas novas entram no registro de telas do 006 com identificador estável (INT-02), sem inventar segundo mecanismo. |
| P3. Domínio puro (DDD + hexagonal) | ✅ As duas peças de domínio novas — `PlanoDeConversao` e a resolução de `IdiomaEfetivo` — são puras: sem rede, sem banco, sem relógio, testáveis offline (RNF-02). O mecanismo de i18n do cliente, o acervo de documentação e a rotina de restauração estão **declarados fora do domínio** na spec, para ninguém os promover a entidade por engano. `import-linter` continua falhando o build na violação. |
| P4. TDD | ✅ Teste vermelho antes do código nas duas peças de domínio (T-05, T-10) e nos dois portões novos, que nascem pela sabotagem: o portão de literal órfão nasce com um literal plantado que ele tem de pegar; o de cobertura, com um verbete removido. Cobertura mínima de 85% no domínio novo (RNF-12). |
| P5. Observabilidade de nascença | ✅ As mutações novas (preferência de idioma, importação) nascem com traço OTel correlacionado e log estruturado (RNF-01), sobre a fundação do ciclo 003. Duas quedas silenciosas passam a ser observáveis por desenho: a queda de idioma para o padrão (RF-14) e a chave ausente em produção (RF-10) — o oposto do `translation \|\| key` da linhagem. |
| P6. Jornada viva com prova visual | ✅ Jornada de documentação e idioma, com captura gerada por script versionado do build real **nos dois idiomas** e avaliação heurística datada, no mesmo pull request (T-13). Base 100% sintética (ADR 0006): o arquivo legado usado como fixture é gerado por script a partir da "Instituição Horizonte", nunca um export real (RNF-11). |
| P7. Segredo nunca no cliente | ✅ Nenhuma chave ou credencial no cliente (DoD 16). O ponto específico deste ciclo: as credenciais do ensaio de restauração vêm de variável de ambiente e **não** aparecem na saída colada no `qa-report.md` (RNF-10) — colar evidência não é desculpa para vazar segredo, e é o erro fácil de um ciclo que cola saída de infraestrutura. |

**Sem violações.** Nenhum "não aplicável".

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento. O mecanismo de i18n vem do que a linhagem provou e do que ela errou, medido por linha (spec F-01..F-04, F-12, F-15, F-16); a forma da documentação embutida vem do `DocsView` (F-05); o formato legado está lido no código que o escreve e o lê (F-08, F-09). A única incógnita técnica — o que o plano do provedor permite restaurar (L-01) — não se resolve com pesquisa e sim com o **ensaio**, que é entrega do ciclo (RF-02). |
| `data-model.md` | `ART:data-model=yes` | O ciclo persiste estrutura nova (preferência de idioma por inquilino/usuário) e formaliza objetos de valor novos (`IdiomaEfetivo`, `ChaveDeMensagem`, `RelatoDeImportacao`) mais o agregado `Verbete`. O documento nasce na abertura do ciclo (tarefa T-02) como extensão declarada do modelo do ciclo 004, em `../004-nucleo-de-diagramas/data-model.md`, e traz o plano de migração no formato expandir → contrair (RNF-05). Os testes de domínio são a forma final e prevalecem sobre o documento. |
| Contratos de fronteira | `ART:contracts=no` | Nenhum contrato de fronteira novo. A importação e a exportação usam os recursos REST já contratados no ciclo 004, em `../004-nucleo-de-diagramas/contracts/rest-api.md`, acrescentando formato de entrada — o que se documenta como extensão do contrato existente, no pull request, não como contrato paralelo. Documentação embutida é leitura de conteúdo versionado, sem catálogo (INT-03). Duplicar contrato aqui seria criar segunda fonte para a mesma junta. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (18 linhas com comando); lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=yes` | Duas superfícies **novas** que o protótipo do ciclo 002 não desenhou: o painel de documentação embutida com âncoras (tela 6.2) e a tela de relato de importação campo a campo (tela 6.3), mais o seletor de idioma e o estado de tradução pendente. Interface nova exige papel semântico antes do componente; o adendo nasce neste ciclo, referenciado ao `ux-design.md` do 002, antes de qualquer linha de UI (T-04). |

**Dívida declarada dos dois `yes`.** Os artefatos `data-model.md` e `ux-design.md` são
declarados `yes` e **ainda não existem** — nascem na abertura do ciclo (T-02 e T-04), porque
o modelo de dados precisa das respostas do Clarify (a preferência é por pessoa ou por
inquilino?) e o desenho precisa do gate de UX. Enquanto isso, `scripts/check-conformance.sh
011` os reporta como declarados e ausentes, e a saída é esta:

```
    · data-model: declared ART:data-model=yes but no data-model.md in the cycle
    · ux-design: declared ART:ux-design=yes but no ux-design.md in the cycle
```

Está colado aqui em vez de descrito porque é o próprio portão dizendo o que falta (R1); a
alternativa — declarar `no` para o portão calar — seria mentir sobre um ciclo que
persiste estrutura e desenha tela nova.

## Decisões de arquitetura do módulo

1. **Um dicionário, um portão, nenhuma exceção sem motivo.** Toda cadeia visível vive no
   dicionário; a lista de exceções da função de aptidão de literal órfão exige **motivo
   escrito por linha**, no mesmo desenho de `scripts/check-caminhos.sh`. Exceção sem motivo
   falha o portão — é assim que um portão deixa de mentir depois de seis meses (spec L-05).
2. **Idioma efetivo é valor derivado, preferência é o que se persiste.** A ordem
   (preferência → embarque → língua-fonte) é função pura com o **motivo** anexado ao
   resultado; a interface exibe o motivo (RI-01) e o log registra a queda ao padrão
   (RF-14). Guardar "idioma atual" como estado persistido é o desenho que produz tela mista.
3. **Chave ausente é erro, não texto.** Em desenvolvimento e teste, lança; em CI, a
   paridade falha; em produção, cai para a língua-fonte com log. A linhagem renderizava a
   chave (`I18nProvider.tsx:41`) — três comportamentos declarados substituem um silêncio.
4. **Documentação é conteúdo versionado servido sob demanda.** Um arquivo por verbete, por
   idioma, com âncoras nomeadas e procedência citada; nenhuma geração em tempo de execução
   (ADR 0007). A cobertura é derivada do **registro de ferramentas** — a mesma lista que a
   navegação usa —, para não haver duas verdades sobre "quais ferramentas existem".
5. **O formato legado é conhecido por um só lugar.** `PlanoDeConversao` é o único ponto que
   entende o formato antigo; o resto do caminho de importação já existe desde o ciclo 004.
   Aposentar o formato é apagar um serviço, não desmontar a importação (Clarify 2).
6. **Descarte declarado em vez de descarte silencioso.** O relato de importação lista o que
   entrou **e** o que ficou fora, com contagem — inclusive o histórico de conversa do
   formato legado (RF-29). A decisão certa tomada em silêncio ainda é um defeito de
   confiança.
7. **A restauração é uma entrega, não um procedimento escrito.** O ciclo produz a saída de
   um ensaio real em destino separado; o documento de operação nasce **do** ensaio, com o
   que não voltou nomeado (RF-03). Cópia gerenciada não ensaiada é conveniência (spec
   RN-07).

## Grafo de dependência das tarefas

```
T-01 (DoD fixada + pré-condição: ciclo 008 promovido)
  ├─► T-02 (data-model: preferência, verbete, relato · plano expandir→contrair)
  │     └─► T-03 (migração Alembic com downgrade testado)
  ├─► T-04 (adendo de ux-design: painel de docs, relato de importação, seletor)
  ├─► T-05 (TDD: resolução de idioma efetivo — três caminhos, teste antes)
  │     ├─► T-06 (portão de literal órfão, nasce por sabotagem)
  │     └─► T-07 (portão de paridade de dicionários)
  ├─► T-10 (TDD: PlanoDeConversao + RelatoDeImportacao — teste antes)
  │     └─► T-11 (adaptador de importação legada + exportação consolidada)
  └─► T-12 (ensaio de restauração — independente, cedo no ciclo)
T-03, T-04, T-06, T-07 ─► T-08 (UI: seletor, dicionários, localização de formato)
T-04, T-08 ────────────► T-09 (acervo de documentação + painel + portão de cobertura)
T-08, T-09, T-11 ──────► T-13 (jornada viva nos dois idiomas)
T-12, T-13 ────────────► T-14 (aptidões + qa-report) ─► cauda (TAIL:*)
```

O T-12 é deliberadamente independente e **cedo**: se o plano do provedor não permitir o que
a spec L-01 assume, o ciclo precisa saber na primeira semana, não na véspera do gate.

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: ciclo **008 promovido** (a documentação embutida só cobre
  ferramentas que existem — [`../../docs/roadmap.md`](../../docs/roadmap.md)); os 5
  `[DÚVIDA]` do Clarify respondidos, em particular o idioma padrão (muda o RF-12) e a
  retenção do formato legado (muda o alcance do T-09); o teto de pacote da RNF-09 com número
  decidido; confirmação de que o plano do projeto Neon permite restaurar para destino
  separado (spec L-01) — ou o ADR que decide a alternativa.
- **DoD — o ciclo não fecha sem**: as 18 linhas da tabela de aceite verdes, com a saída
  colada (R1) e o tamanho examinado (R2) no [`qa-report.md`](qa-report.md); a saída do ensaio
  de restauração colada; a matriz de aderência ao APH re-verificada no mesmo pull request; a
  cauda completa (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 011): estourou → **sai primeiro** o E1.4 avançado (T-11,
  importação legada e exportação consolidada); **nunca sai** o portão de i18n (T-06 e T-07),
  porque cadeia órfã descoberta depois custa varredura completa — a linhagem pagou duas
  specs para provar isso. Perde escopo, não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-apolice — descobrir no fim do ciclo que a restauração assumida não é possível no plano contratado | spec L-01 | T-12 é independente e roda **cedo**; sem a saída do ensaio (DoD 14) o ciclo não fecha, e a impossibilidade vira ADR com a alternativa, não um item pendente. |
| GATE-idioma-ausente — o hospedeiro não enviar idioma no envelope e a aplicação abrir imprevisível | spec L-02 | A ordem do RF-12 resolve sem erro e registra a queda (RF-14); a lacuna do hospedeiro vira `mensagens/NNN` (P1: relatar e parar). O `[DÚVIDA]` 1 fecha a política antes da implementação. |
| GATE-excecao-sem-motivo — a lista de exceções do portão de literal órfão crescer e o verde passar a mentir | spec L-05 | Exceção exige motivo escrito por linha; `TAIL:mutation` planta um literal e exige que o portão o pegue; a saída imprime o tamanho examinado (R2), de modo que uma varredura que encolheu fica visível. |
| GATE-cobertura-de-verbete — a documentação nascer cobrindo duas ferramentas de seis, como na linhagem | spec F-06 | Portão de cobertura derivado do registro de ferramentas (DoD 8) + sabotagem que remove um verbete e exige a queda; verbete com tradução pendente conta como pendência **declarada**, não como coberto. |
| GATE-legado-eterno — o adaptador do formato antigo virar dependência permanente da linhagem | Clarify 2 | Data de aposentadoria decidida no gate; o formato vive num só serviço (`PlanoDeConversao`), de modo que a aposentadoria seja a remoção de um arquivo e dos seus testes. |
| GATE-segredo-na-evidencia — colar a saída do ensaio de restauração e vazar credencial junto | spec RNF-10 | `TAIL:security` verifica a evidência colada como superfície de vazamento; as credenciais vêm de variável de ambiente e a rotina não as imprime. |
