# Rounds — em que ordem isto se constrói

> Siglas deste documento: **TOC** — Teoria das Restrições; **ARA** — Árvore da Realidade
> Atual; **UDE** — Efeito Indesejável; **NC** — Nuvem de Conflito; **ARF** — Árvore da
> Realidade Futura; **APR** — Árvore de Pré-Requisitos; **AT** — Árvore de Transição;
> **S&T** — Árvore de Estratégia & Táticas; **APH** — o padrão Aplicação ↔ Harness;
> **ADR** — Registro de Decisão Arquitetural; **IA** — inteligência artificial; **FSM** —
> máquina de estados finitos; **OTel** — OpenTelemetry; **SSE** — *Server-Sent Events*;
> **CI** — integração contínua; **i18n** — internacionalização; **eTLD+1** — o "site" no
> sentido do navegador; **SDK** — kit de desenvolvimento de software.

- **Decidido em**: 2026-09-03, ciclo 001 · **Fonte**: `specs/001-fundacao-e-planejamento/`
- **Formato herdado** da irmã (`gestaodeprioridades/docs/produto/rounds.md` 🟢): cada round
  carrega seis campos obrigatórios — Apetite · Entrega · Fora · Aptidão executável ·
  Depende de · Sai primeiro (com "Nunca sai") — mais a alocação dos defeitos D-NN da
  [`visao.md`](visao.md) §6 e, quando existe, o **Bloqueio externo declarado**.
- **Aptidão deste documento**: 🔴 dívida declarada — o verificador executável dos seis
  campos e da alocação exaustiva de D-01..D-11 ainda não existe; até ele entrar (candidato
  ao fechamento do ciclo 002), quem confere é a revisão independente do ciclo 001, item a
  item. Registrar a dívida aqui é o que impede o esquecimento silencioso (regra R2).

Cada round mapeia **um** ciclo do [`../roadmap.md`](../roadmap.md) — os nomes coincidem de
propósito: round 003 é o ciclo 003. O roadmap diz *quando* e com que portões; este
documento diz *o que entra, o que sai primeiro e o que nunca sai*.

## As quatro decisões que ordenam tudo

1. **O propósito é ser a segunda junta real da federação.** A aplicação TOC tem valor
   próprio — quatro gerações de demanda provada ([`visao.md`](visao.md) §3) — e é o
   pretexto honesto: duas aplicações independentes fechando contra o mesmo contrato é o
   teste que uma sozinha não faz. Por isso o critério de pronto do round 003 não é *"a
   tela funciona"*: é **"a junta fecha contra a `ghdaru` real"**.
2. **Apetite = um ciclo do método.** Round que não couber **perde escopo, não ganha
   ciclo**. É para isso que serve o campo `Sai primeiro`.
3. **Fundação antes de ferramenta.** A linhagem especificou o backend quatro vezes e
   construiu zero (D-03), e abandonou cinco repositórios (D-10). O antídoto é sequência:
   nenhum módulo de ferramenta nasce antes de o esqueleto (003) existir e provar a junta.
4. **Assistência só depois do catálogo.** Nenhuma ferramenta ganha IA antes de o round
   006 entregar o catálogo governado — a alternativa seria um SDK provisório, que é o
   D-01 com outro nome. O custo aceito: ARA (005) nasce sem assistência e a recebe no 006.

> **Primeiro corte**: o round **003**. É o menor pedaço que já prova o que o projeto
> existe para provar — antes dele há protótipo e papel; depois dele há uma aplicação
> federada de verdade, ainda que vazia de ferramentas.

---

## Round 002 — Protótipo de interfaces

- **Apetite**: um ciclo
- **Entrega**: protótipo **descartável** das telas de M1–M3 (canvas, vista tabular, ARA,
  NC) com base sintética, `ux-design.md` com papel semântico e `ai_visible` campo a campo
  **antes** de componente, e jornadas documentadas com captura gerada por script
  versionado + avaliação heurística datada (P6). Os requisitos de interface (RI) das
  specs de M1–M3 saem daqui validados por olho humano, não por suposição.
- **Fora**: qualquer código de produção (a definição é herdada da decisão análoga da
  irmã e fixada em ADR próprio se contestada); ARF/APR/AT/S&T/focalização — prototipar o
  que só entra nos rounds 008–010 seria estoque.
- **Aptidão executável**: rodar de novo o script de captura sobre o mesmo build regenera
  as imagens byte-idênticas; nenhuma captura órfã (toda imagem citada por exatamente uma
  jornada); `scripts/check-caminhos.sh` verde sobre as jornadas.
- **Depende de**: nenhum (após o gate humano do ciclo 001).
- **Sai primeiro**: a visão conflito+solução da NC (fica o diagrama do conflito).
  **Nunca sai**: a captura gerada por script — protótipo sem prova visual versionada é a
  linhagem de novo, que "funcionava" e nunca se soube exatamente o quê.
- **Defeitos**: nenhum — *declaração, não esquecimento*: protótipo descartável não
  corrige defeito de linhagem; ele reduz o risco de interface dos rounds que corrigem.

## Round 003 — Esqueleto federado (o primeiro corte)

- **Apetite**: um ciclo
- **Entrega**: uma pessoa entra na `ghdaru`, clica na aplicação TOC e vê a aplicação
  embarcada **sob a identidade dela** — ainda sem ferramenta alguma, listando projetos
  sintéticos de leitura. Por baixo: repositório publicado em eTLD+1 distinto do
  hospedeiro (E8.5), serviço FastAPI com banco Neon próprio e migração aplicada (E8.1),
  OTel do primeiro endpoint em diante (E8.2), admissão com os 4 parâmetros e falha rápida
  (E7.1), embarque com envelope `ghd.*`, tema por lista de permissões com *fallback*
  (E7.2), manifesto conforme ao Anexo B, e CI com as funções de aptidão do projeto.
- **Fora**: catálogo `toc.*`, ações, snapshot e wire (round 006); qualquer ferramenta
  TOC; qualquer escrita vinda do hospedeiro.
- **Aptidão executável**: **"a junta fecha contra a `ghdaru` real"** — não contra shell
  simulado: manifesto aceito pela rota de administração real, embed-token trocado por
  identidade em `POST /auth/introspect` servidor a servidor com o grant consumido,
  `ev.source` e `origin` verificados antes de qualquer payload, teste que prova recusa
  em falha fechada quando a fundação está indisponível, e o traço OTel da introspecção
  visível de ponta a ponta. Captura da jornada de embarque gerada do build embarcado.
- **Depende de**: 002 (o esqueleto embarca a casca de telas que o protótipo validou).
- **Sai primeiro**: o tema do inquilino (cai para tema próprio); o modo conteúdo do
  embarque. **Nunca sai**: a introspecção e a admissão com falha rápida — sem elas não
  há junta, e o round perde o propósito.
- **Defeitos**: **D-02** (login simulado morre: identidade só por introspecção),
  **D-03** (o backend deixa de ser especificação parada: nasce o serviço real),
  **D-07** (o dado sai do navegador: Neon próprio, isolado por inquilino).
- **Bloqueio externo declarado** — três, conhecidos pela experiência da irmã, nenhum
  nosso para resolver:
  1. **Os dois schemas de manifesto eram mutuamente exclusivos** quando a irmã mediu
     (golden da fundação exige `level` + `endpoints.validate_token`; o normativo do
     Anexo B exige `mode` + `endpoints.introspect`; ambos com
     `additionalProperties: false` — **4 erros** na validação cruzada):
     `gestaodeprioridades/mensagens/005-para-ghdaru-embarque-da-prioridades.md` §0 🟢.
     Re-medir na abertura do round; se persistir, o round entrega tudo menos o registro
     do manifesto, e a mensagem `mensagens/NNN` nossa referencia a da irmã.
  2. **A fatia de federação é desligada por padrão** (`FEDERATION_MANIFESTS_ENABLED`,
     tudo responde 404 sem ela — mensagens/005 §2.1 da irmã 🟢). Ligar é do operador da
     fundação, não nosso.
  3. **Os grants de embarque vivem em memória no hospedeiro**:
     `ghdaru/apps/api/src/ghdaru_api/identity/adapters/in_memory.py:60-65` 🟢 — o
     repositório é declaradamente protótipo (comentário na linha 61) e um reinício do
     host invalida embarques em voo. Aceitável para leitura; registrado para ninguém
     depurar como se fosse defeito nosso.

## Round 004 — Núcleo de diagramas (M1)

- **Apetite**: um ciclo
- **Entrega**: M1 completo com TDD — projetos com *soft delete* (E1.1), canvas com nós,
  arestas e desfazer de sessão (E1.2), vista tabular equivalente (E1.3), exportação e
  importação JSON não destrutiva (E1.4 básico). Primeira funcionalidade de verdade
  atravessando a junta do 003.
- **Fora**: qualquer semântica TOC (UDE, premissa, injeção — são de M2/M3); importação
  dos formatos da linhagem (E1.4 avançado, round 011).
- **Aptidão executável**: suíte de domínio verde e **sem rede** (o domínio não importa
  framework — contrato de `import-linter` que falha o build se importar); exportar e
  reimportar um projeto devolve JSON idêntico; importação de arquivo inválido **recusa
  com relato**, nunca substitui em silêncio.
- **Depende de**: 003.
- **Sai primeiro**: o desfazer de sessão (fica o modelo preparado para ele). **Nunca
  sai**: a vista tabular equivalente — na linhagem ela é o que tornava projetos grandes
  utilizáveis, e um canvas sozinho repetiria o corte errado.
- **Defeitos**: nenhum — *declaração, não esquecimento*: os defeitos de persistência e
  identidade já morreram no 003; os de semântica TOC morrem de 005 em diante.

## Round 005 — Árvore da Realidade Atual (M2)

- **Apetite**: um ciclo
- **Entrega**: ARA completa **sem assistência**: UDEs com validação formal como regra de
  domínio pura (E2.1), construção da árvore com relações causais e análise de
  suficiência (E2.2). A ferramenta mais madura da linhagem, agora testável.
- **Fora**: **E2.3** (assistência via catálogo) — decisão 4: entra no round 006, quando
  o catálogo existir. Qualquer outra ferramenta.
- **Aptidão executável**: os critérios decidíveis de UDE (estado e não ação, tempo
  presente, frase completa, sem culpar pessoa) avaliados por teste de domínio **sem
  rede e sem modelo** — o mesmo caso que o prompt do v3 tratava por chamada de IA passa
  agora por função pura; jornada viva da construção de uma ARA sintética com captura
  gerada do build.
- **Depende de**: 004.
- **Sai primeiro**: a análise de suficiência assistida por relatório (fica a marcação
  manual). **Nunca sai**: a validação formal de UDE como domínio puro — é a correção do
  D-08 e a razão de este round existir separado do 004.
- **Defeitos**: **D-08** (a regra de negócio sai do prompt e vira domínio testável).

## Round 006 — Ações governadas e snapshot (E7.3–E7.6)

- **Apetite**: um ciclo
- **Entrega**: o catálogo `toc.*` no manifesto, a FSM de proposta no servidor (todo
  verbo mutador vindo de modelo nasce `action_proposal`, com traço e lote), o registro
  de telas com snapshot sanitizado no servidor (tela é dado, nunca instrução), e o wire
  APH Nível 1 (SSE, `seq`, replay, cancelamento, códigos de erro). O primeiro
  consumidor: **E2.3** — sugerir UDEs, causas e relações e analisar a árvore, pela
  fundação.
- **Fora**: ações de NC/ARF/APR (entram com os módulos respectivos, sobre a mesma FSM);
  qualquer prompt ou chave no cliente.
- **Aptidão executável**: teste que prova que **sem a capability de escrita as ações
  mutadoras somem do catálogo** (a lição paga pela irmã); teste que prova que nenhuma
  mutação proposta por modelo aplica sem passar pela FSM; snapshot de tela gerado no
  servidor **sem nenhum campo marcado `ai_visible: false`**; replay por `seq` coberto
  por teste de wire.
- **Depende de**: 005 (as primeiras ações do catálogo operam sobre a ARA) e 003.
- **Sai primeiro**: o lote (fica proposta unitária). **Nunca sai**: a FSM única no
  servidor e o traço por ação — são o P2, INEGOCIÁVEL; um round que executa ação de
  modelo sem eles não pode ser aceito.
- **Defeitos**: **D-01** (o SDK no cliente morre: assistência exclusivamente pela
  fundação, chave nenhuma no navegador — ADR 0007).
- **Bloqueio externo declarado** — dois, e nenhum bloqueia a *nossa* entrega, apenas o
  alcance dela:
  1. **A chamada de ação federada do hospedeiro chega sem credencial**:
     `ghdaru/docs/adr/0023-acoes-federadas-por-adapter-remoto.md` 🟢 — a fatia F4 do
     host envia `POST {origin}/aph/actions/{action_id}` sem token (consequência
     declarada: *"Sem credencial nesta fatia"*), atrás de
     `FEDERATION_REMOTE_ACTIONS_ENABLED` desligada por padrão; a autenticação da borda
     é pré-requisito do **piloto F7, pendente do host**. Enquanto isso, a nossa borda
     de ações **recusa chamada não autenticada** (falha fechada) — o que significa que
     a execução disparada do harness só funciona de fato quando o F7 existir. A FSM, o
     catálogo e o consumo interno não dependem disso.
  2. **O escopo do grant não intersecta com o usuário**
     (`gestaodeprioridades/mensagens/005-para-ghdaru-embarque-da-prioridades.md` §4,
     item 2 🟢): o catálogo filtrado que publicamos é redução de superfície do modelo,
     **não** garantia de autorização — a fronteira real é a rota do hospedeiro. Por
     isso toda mutadora nasce recusável e a autorização se decide na nossa borda, por
     identidade introspectada, nunca por capability alegada.

## Round 007 — Nuvem de Conflito (M3)

- **Apetite**: um ciclo
- **Entrega**: NC completa — 5 entidades e arestas com edição direta (E3.1), premissas
  por aresta e injeções ligadas à premissa que invalidam (E3.2), geração assistida a
  partir de narrativa **pelo catálogo** (E3.3), visão conflito+solução (E3.4).
- **Fora**: semear ARF a partir de injeção (é o encadeamento, round 008).
- **Aptidão executável**: invariantes da nuvem como teste de domínio (exatamente 5
  entidades, 7 arestas, injeção sempre referencia premissa existente); a geração
  assistida entra como `action_proposal` recusável — teste prova que recusar deixa o
  projeto intacto; jornada viva do dilema sintético ("Instituição Horizonte") com
  captura do build.
- **Depende de**: 004 e 006.
- **Sai primeiro**: a visão conflito+solução (E3.4 — fica a lista de injeções sobre o
  diagrama do conflito). **Nunca sai**: premissas por aresta — nuvem sem premissa
  explícita é desenho de opinião, o problema do §1 da [`visao.md`](visao.md) de volta.
- **Defeitos**: nenhum — *declaração, não esquecimento*: a NC foi entregue pela 3ª/4ª
  gerações; o defeito dela era a assistência por SDK no cliente (D-01), que já morreu
  no 006.

## Round 008 — Árvores de futuro e implementação (M4)

- **Apetite**: um ciclo
- **Entrega**: o que quatro gerações nunca entregaram — ARF (E4.1), APR com obstáculos
  → objetivos intermediários sequenciados (E4.2), AT (E4.3) — e o **encadeamento**
  (E4.4): UDE da ARA alimenta NC, injeção da NC semeia ARF, ARF gera os obstáculos da
  APR.
- **Fora**: ramos negativos da ARF com tratamento assistido (fica a marcação manual);
  S&T (round 010).
- **Aptidão executável**: teste de domínio que percorre a cadeia inteira com dados
  sintéticos — cria UDE na ARA, promove à NC, injeta, semeia ARF, deriva obstáculo,
  sequencia OIs na APR — e prova que cada elo guarda a referência de origem (a
  contagem que na linhagem dava zero: D-11); as três árvores criáveis e exportáveis
  pelo E1.4.
- **Depende de**: 005 e 007.
- **Sai primeiro**: a AT (E4.3) — dos três diagramas é o de menor risco e o único sem
  entidade nova. **Nunca sai**: o encadeamento — sem ele este round entregaria mais
  três ilhas, que é exatamente o D-11.
- **Defeitos**: **D-04** (ARF/APR/AT saem do botão cinza), **D-11** (as ferramentas
  passam a se encadear).

## Round 009 — Focalização (M6)

- **Apetite**: um ciclo
- **Entrega**: registro da restrição e do passo atual por análise (E6.1) e a jornada
  guiada pelos cinco passos — identificar → explorar → subordinar → elevar → recomeçar
  — ligando as ferramentas construídas (E6.2).
- **Fora**: métricas de desempenho da restrição (DBR e contabilidade de ganho estão
  fora da v1 por ADR 0005, com a contagem zero colada na [`visao.md`](visao.md) §6).
- **Aptidão executável**: teste que percorre os cinco passos numa análise sintética e
  prova que cada passo referencia a ferramenta certa com o estado herdado do anterior;
  o passo "recomeçar" comprovadamente reabre o ciclo apontando a nova restrição, sem
  apagar a jornada anterior (histórico é apêndice, não sobrescrita).
- **Depende de**: 008.
- **Sai primeiro**: a sugestão assistida de qual ferramenta usar no passo (fica a
  jornada guiada estática). **Nunca sai**: o registro da restrição — é a entidade que
  dá nome à teoria, e o produto sem ela é um editor de diagramas.
- **Defeitos**: **D-09** (os cinco passos existem pela primeira vez na linhagem).

## Round 010 — Estratégia & Táticas (M5)

- **Apetite**: um ciclo
- **Entrega**: a ferramenta que regrediu, de volta — estrutura hierárquica (1, 1.1,
  1.1.2) com as três premissas por nó (E5.1) e status de acompanhamento (E5.2).
- **Fora**: qualquer vínculo automático com APR/AT (candidato a evolução, decisão
  nova).
- **Aptidão executável**: teste de domínio da numeração (inserir/remover nó renumera a
  subárvore corretamente); as três premissas persistidas e exibidas por nó; jornada
  viva com captura.
- **Depende de**: 004 (só do núcleo — a ordem tardia é escolha de valor, registrada no
  [`../roadmap.md`](../roadmap.md)).
- **Sai primeiro**: E5.2 (status — fica a estrutura). **Nunca sai**: as três premissas
  por nó — S&T sem premissa é organograma, e o modelo de dados da linhagem já as tinha
  (`tocbuilderv3/types.ts:293-295` 🟢); entregar menos que o protótipo seria regressão
  sobre regressão.
- **Defeitos**: **D-05** (a regressão da S&T é desfeita, com decisão registrada).

## Round 011 — Fundações da aplicação (M8 restante)

- **Apetite**: um ciclo
- **Entrega**: i18n pt/en consolidada em toda a superfície (E8.3), documentação
  embutida por ferramenta (E8.4), e E1.4 avançado — importação dos JSONs exportados
  pela 4ª geração, com validação e relato de recusa.
- **Fora**: idiomas além de pt/en; migração automática de dados da linhagem (quem quer,
  exporta e importa — decisão proposta na [`visao.md`](visao.md) §7, pergunta 2).
- **Aptidão executável**: verificação de que nenhuma string de interface vive fora do
  dicionário de i18n (grep executável em CI, com a contagem na saída — regra R2); cada
  ferramenta com rota de documentação embutida respondendo; importar um export real do
  `tocbuilderv3` sintético cria o projeto ou recusa com relato campo a campo.
- **Depende de**: 008 (a documentação embutida cobre as ferramentas que existem).
- **Sai primeiro**: E1.4 avançado (a importação da linhagem). **Nunca sai**: o portão
  de i18n — string órfã descoberta depois custa varredura completa, e a linhagem provou
  na 3ª geração que adiar i18n obriga a refazer telas.
- **Defeitos**: nenhum — *declaração, não esquecimento*: D-07 morreu no 003; o que
  sobra do M8 aqui é consolidação, não correção.

## Round 012 — Jornadas e autodeclaração

- **Apetite**: um ciclo
- **Entrega**: jornadas vivas consolidadas de ponta a ponta (da narrativa do dilema à
  APR, atravessando a focalização), matriz de aderência ao APH re-verificada item a
  item, **autodeclaração de Nível 2 (Operador) registrada em ADR** com evidência por
  requisito, e o site de produto atualizado pelo gerador versionado (ADR 0008).
- **Fora**: qualquer funcionalidade nova — round de fechamento não esconde feature.
- **Aptidão executável**: todas as capturas de todas as jornadas regeneram do build
  atual; a matriz de aderência tem um veredito por requisito APH com evidência por
  caminho (sem célula vazia); o site regenerado não diverge do commitado (diff vazio no
  CI).
- **Depende de**: 009, 010 e 011.
- **Sai primeiro**: nada — este round já é só o essencial de fechamento; se estourar,
  o que se corta é escopo dos rounds anteriores, nunca a autodeclaração com evidência.
  **Nunca sai**: a autodeclaração em ADR — é o "prove, não declare" aplicado ao projeto
  inteiro.
- **Defeitos**: nenhum — *declaração, não esquecimento*: fechamento verifica correções,
  não as faz.

## Defeitos não corrigidos em round próprio

- **D-06 · Zero testes** — não vira round: o princípio P4 obriga o teste a nascer
  **antes** do código em todos os rounds 004–011. Um round de "testar" seria o P4
  admitindo que foi violado oito vezes (o mesmo raciocínio da irmã para telemetria).
- **D-10 · Recomeço sem herança** — não vira round: é o defeito que o **ciclo 001
  inteiro** corrige, por escrito — visão medida, módulos, rounds, ADRs com alternativas
  numeradas. Se um round precisasse corrigi-lo, este documento teria falhado.

Conferência de exaustividade: D-01 (006) · D-02 (003) · D-03 (003) · D-04 (008) · D-05
(010) · D-06 (não corrigido em round, motivo acima) · D-07 (003) · D-08 (005) · D-09
(009) · D-10 (não corrigido em round, motivo acima) · D-11 (008). **Onze defeitos, onze
destinos, nenhum em dois lugares.**

## O que este documento não decide

- **Os portões de cada ciclo e suas pré-condições** — são do [`../roadmap.md`](../roadmap.md).
- **Requisitos, features e critérios de aceite** de cada módulo — são das specs
  (`specs/`), no formato do ADR 0004.
- **A resposta às perguntas do Product Steward** ([`visao.md`](visao.md) §7) — a
  pergunta 1 (colaboração por projeto) muda o E1.1 e precisa de resposta antes de a
  spec do round 004 congelar.
- **Quando os bloqueios externos caem** — são trabalho do hospedeiro e do padrão;
  nosso papel é medi-los de novo na abertura de cada round afetado e relatar por
  `mensagens/NNN` quando a medição mudar.
