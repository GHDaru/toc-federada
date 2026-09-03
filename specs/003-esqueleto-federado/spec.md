# Spec 003 — Esqueleto federado (M7/M8 — recorte E7.1, E7.2, E8.1, E8.2, E8.5)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · RF/RI/RNF/RN/INT — requisito
> funcional / de interface / não funcional / regra de negócio / integração · US — User
> Story · DoD — Definition of Done (Definição de Pronto) · OTel — OpenTelemetry ·
> CI — integração contínua · TTL — Time To Live (tempo de vida) · eTLD+1 — *effective
> Top-Level Domain plus one* (o "site" no sentido do navegador) · CSS — Cascading Style
> Sheets · URL — Uniform Resource Locator · SSE — *Server-Sent Events* · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · IA — inteligência
> artificial · i18n — internacionalização · FSM — máquina de estados finitos ·
> UDE — Efeito Indesejável

- **Status**: Rascunho — ciclo **planejado, não executado** (abre após os ciclos 001 e
  002; gate humano do ciclo 001)
- **Raia**: **infra** (plena + reversibilidade — a única do roadmap)
- **Data**: 2026-09-03
- **Origem**: [`../../docs/roadmap.md`](../../docs/roadmap.md) ciclo 003 ·
  [`../../docs/produto/rounds.md`](../../docs/produto/rounds.md) round 003 ·
  [`../../docs/produto/modulos.md`](../../docs/produto/modulos.md) (M7, M8) ·
  ADR 0002 (stack) e ADR 0003 (federação), que este ciclo executa

## O quê e por quê

O primeiro corte de código de produção: a aplicação **existe, embarcada na `ghdaru` real,
sob a identidade de quem a abriu, com banco e traço próprios** — ainda sem nenhuma
ferramenta TOC. A aptidão central, e a mais importante do roadmap, é executável e binária:
**"a junta fecha contra a `ghdaru` real"** — manifesto aceito pela rota de administração
real, grant trocado por identidade em `POST /auth/introspect` servidor a servidor,
`ev.source` e `ev.origin` verificados antes de qualquer conteúdo, falha fechada com a
fundação indisponível, e traço OTel de ponta a ponta. Nada disso contra shell simulado.

O motivo da ordem — junta antes de ferramenta — está medido na linhagem e na irmã. A
linhagem TOC-Builder produziu quatro gerações standalone que nunca encontraram a
plataforma (defeito D-10 da [`../../docs/produto/visao.md`](../../docs/produto/visao.md));
e a primeira aplicação federada, a irmã `gestaodeprioridades`, provou no protótipo dela
que **cada metade da junta escrita sem contrato diverge**: envelope incompatível
([F-02]), `postMessage` com `targetOrigin` `"*"` ([F-04]), `ev.source` nunca verificado
([F-05]). Os três defeitos estão hoje **registrados na própria norma como
contraexemplos** — e cada um vira, nesta spec, um requisito com teste que o reproduz e o
recusa. Errar igual à irmã, depois de a norma ter pago para documentar o erro, seria
pagar duas vezes.

**Recorte declarado.** Esta spec cobre **só a junta e o chão**: épicos E7.1 (identidade e
admissão) e E7.2 (embarque) do módulo M7, e E8.1 (persistência própria), E8.2 (OTel) e
E8.5 (deploy) do módulo M8. O restante do M7 — catálogo `toc.*`, ações governadas,
registro de telas, snapshot e wire (E7.3–E7.6) — vive em
[`../006-acoes-governadas-e-snapshot/spec.md`](../006-acoes-governadas-e-snapshot/spec.md);
o restante do M8 — i18n consolidada e documentação embutida (E8.3, E8.4) — vive em
[`../011-fundacoes-da-aplicacao/spec.md`](../011-fundacoes-da-aplicacao/spec.md). Nenhum
requisito daqueles épicos se repete aqui.

## O que entra como dado

- **ADR 0003** ([`../../docs/adr/0003-federacao-aph-nivel-2-embedded.md`](../../docs/adr/0003-federacao-aph-nivel-2-embedded.md)):
  Padrão APH Nível 2 (Operador), `mode: embedded`, `app_id: toc`, namespace `toc.*`,
  identidade por `POST /auth/introspect`, site em eTLD+1 distinto do hospedeiro. Esta
  spec não rediscute nada disso: ela o executa.
- **ADR 0002** ([`../../docs/adr/0002-stack-herdada-da-irma.md`](../../docs/adr/0002-stack-herdada-da-irma.md)):
  React + TypeScript/Vite · FastAPI/Python · PostgreSQL Neon em **projeto próprio** ·
  OTel · deploy Vercel (interface) + Railway (serviço).
- **ADR 0006** (base sintética): os projetos listados no embarque são da "Instituição
  Horizonte" e afins — nenhum dado real de pessoa, nunca.
- **ADR 0007** (IA somente pela fundação): este ciclo não fala com provedor de modelo
  nenhum; a assistência entra no ciclo 006, pelo catálogo.
- **O lado normativo da junta**: Anexo B do padrão APH (envelope §B.2, admissão §B.4,
  grant e introspecção §B.6, modo embarcado §B.8) e o guia do desenvolvedor de aplicação
  federada da fundação — fontes [F-01]…[F-13], todas lidas e citadas por linha.
- **A casca de telas validada no ciclo 002**: o esqueleto embarca o que o protótipo
  descartável provou por olho humano; nenhuma tela nova é desenhada aqui além dos
  estados de fronteira (§ Telas e fluxos).
- **Os três bloqueios externos do round 003** (re-medidos na abertura do ciclo — L-01 a
  L-03): schemas de manifesto mutuamente exclusivos, fatia de federação desligada por
  padrão, grants em memória no hospedeiro.

## Épicos, features e user stories

### E7.1 — Identidade e admissão

**F7.1.1 — Admissão com falha rápida** — a aplicação exige os parâmetros de admissão na
partida e recusa-se a subir nomeando o que faltou; o contrato completo, com códigos de
recusa, vive em [`contracts/parametros-de-admissao.md`](contracts/parametros-de-admissao.md).

- US-01 — Como **Administradora do tenant**, quero que a aplicação recuse subir dizendo
  exatamente qual parâmetro de admissão faltou, para corrigir a configuração em minutos
  em vez de depurar um erro que só aparece quando alguém clica.
  - Dado um ambiente sem `HOST_ORIGIN`, Quando o serviço inicia, Então ele termina com
    código de saída diferente de zero e a última linha do log traz
    `ADMISSAO_HOST_ORIGIN_AUSENTE` — e nenhuma porta fica aberta.

**F7.1.2 — Introspecção** — o grant recebido no handshake é trocado **imediatamente** por
identidade em `POST /auth/introspect`, servidor a servidor; a aplicação nunca confia no
que o handshake diz.

- US-02 — Como **Gestora**, quero abrir a aplicação TOC dentro da plataforma e vê-la sob
  a minha identidade e o meu tenant, para não existir um segundo login nem um segundo
  cadastro.
  - Dado um embarque com grant válido, Quando a aplicação troca o grant na introspecção,
    Então a resposta `active: true` traz usuário, `tenant_id` e `capabilities`, e é
    **essa resposta** — nunca o payload do handshake — que define o que eu vejo.
- US-03 — Como **Agente de IA da fundação** (persona de contrato), quero que a autorização
  da aplicação venha só das `capabilities` da introspecção, para nenhum texto meu — nem
  de tela, nem de payload — conseguir ampliá-la.
  - Dado um principal sem `toc:read`, Quando a aplicação monta a resposta do embarque,
    Então nenhum projeto é listado, qualquer que seja o conteúdo do handshake.

**F7.1.3 — Falha fechada** — indisponibilidade ou recusa da fundação nunca vira acesso.

- US-04 — Como **Administradora do tenant**, quero que a aplicação negue tudo quando não
  conseguir validar a identidade, para uma queda da fundação nunca virar uma janela de
  acesso sem dono.
  - Dado o endpoint de introspecção fora do ar, Quando um embarque chega, Então a
    aplicação responde o estado `FUNDACAO_INDISPONIVEL`, não renderiza dado algum e
    **não** presume o grant válido.

### E7.2 — Embarque

**F7.2.1 — Envelope e handshake `ghd.*`** — o canal fala exatamente o envelope canônico
do §B.2.1; a aplicação fala primeiro.

- US-05 — Como **Gestora**, quero que a aplicação apareça embarcada em poucos segundos ou
  declare honestamente que não conseguiu, para nunca encarar um retângulo branco sem
  explicação.
  - Dado o iframe montado pelo hospedeiro, Quando a aplicação carrega, Então ela emite
    `ghd.ready` com `{app_id: "toc"}` antes de qualquer outra mensagem — e, sem
    `ghd.handshake` dentro da janela, mostra o estado "sem canal" (§ Telas e fluxos).

**F7.2.2 — Verificação de fonte e origem** — os três defeitos que a norma registrou do
protótipo da irmã, cada um recusado por teste.

- US-06 — Como **Administradora do tenant**, quero que a aplicação descarte qualquer
  mensagem que não venha comprovadamente do shell admitido, para um site malicioso que a
  embarque não conseguir nem saber que ela existe.
  - Dado um `postMessage` cuja origem difere de `HOST_ORIGIN` **ou** cujo `ev.source`
    não é `window.parent`, Quando a mensagem chega, Então ela é descartada sem resposta
    e sem efeito, e o descarte é contado em métrica.

**F7.2.3 — Modo conteúdo e tema** — embarcada, a aplicação é só conteúdo, vestida com o
tema do inquilino e com *fallback* completo.

- US-07 — Como **Participante**, quero a aplicação com a cara da plataforma em que estou,
  para não sentir que cliquei para fora do sistema.
  - Dado `theme.tokens` parciais no handshake, Quando a tela renderiza, Então cada token
    recebido vira variável CSS e cada token ausente cai no tema próprio — nenhum
    elemento fica sem cor definida.

### E8.1 — Persistência própria

**F8.1.1 — Banco e migrações próprios** — PostgreSQL Neon em projeto próprio, migrações
Alembic com `upgrade` **e** `downgrade`, nada compartilhado com a fundação.

- US-08 — Como **Administradora do tenant**, quero o dado da aplicação num banco dela,
  isolado por tenant, para o ciclo de vida do meu dado não depender do banco de um
  produto que não é este.
  - Dado um banco Neon limpo, Quando `alembic upgrade head` e depois
    `alembic downgrade base` rodam, Então o esquema volta ao estado vazio **sem
    resíduo** — nenhuma tabela, nenhum tipo, nenhum índice sobrando.

**F8.1.2 — Isolamento por tenant** — toda leitura é filtrada pelo `tenant_id` da
introspecção; não existe consulta sem tenant.

- US-09 — Como **Gestora**, quero ver só os projetos do meu tenant, para a lista de outra
  organização nunca vazar na minha — nem por defeito.
  - Dado dois tenants com projetos sintéticos distintos, Quando um principal do tenant A
    lista projetos, Então nenhum projeto do tenant B aparece — e o teste que o prova
    consulta com os dois principais.

### E8.2 — Observabilidade OTel

**F8.2.1 — Traço de nascença** — todo endpoint nasce com span; a introspecção é visível
de ponta a ponta no traço do embarque (P5: sem traço, não está pronta).

- US-10 — Como **Administradora do tenant**, quero seguir um embarque do `ghd.ready` até
  a lista renderizada num único traço, para uma falha de junta ser diagnosticável em
  minutos, não em suposições.
  - Dado um embarque completo, Quando consulto o traço, Então vejo a requisição de
    embarque, o span da chamada de introspecção e a consulta de projetos correlacionados
    pelo mesmo `trace_id` — e os logs estruturados carregam esse `trace_id`.

### E8.5 — Deploy e CI

**F8.5.1 — Site próprio e integração contínua** — interface e serviço publicados em
eTLD+1 distinto do hospedeiro; CI com as funções de aptidão do projeto; rollback
documentado e ensaiado (raia infra).

- US-11 — Como **Administradora do tenant**, quero a aplicação servida de um site que não
  é o da plataforma, para a fronteira de origem em que toda a segurança do embarque se
  apoia existir de fato — não só no manifesto.
  - Dado o endereço publicado, Quando comparo o eTLD+1 dele com o do hospedeiro, Então
    são distintos — e é isso que o portão humano do endereço aprova antes de ele entrar
    no manifesto.

## Entidades e modelo de domínio

Modelo mínimo deste ciclo — detalhado em [`data-model.md`](data-model.md); o domínio TOC
(nó, aresta causal, UDE) só nasce no ciclo 004:

- **Principal** (objeto de valor, nunca persistido como credencial): resultado da
  introspecção — `usuario {id, nome, email}`, `tenant_id`, `capabilities[]`,
  `expires_at`. Invariante: só existe construído a partir de uma resposta
  `active: true`; não há construtor a partir de payload de handshake.
- **Tenant** (referência): o `tenant_id` do hospedeiro é chave estrangeira lógica de todo
  agregado local. Invariante: nenhuma consulta de repositório aceita ausência de
  `tenant_id`.
- **Projeto** (agregado próprio, mínimo neste ciclo): `id`, `tenant_id`, `nome`,
  `ferramenta` (enum futuro), `atualizado_em`, `apagado_em` (soft delete nasce no 004 —
  aqui a coluna existe e fica nula). Invariante: pertence a exatamente um tenant desde a
  criação.
- **Evento de domínio**: nenhum neste ciclo — o primeiro (`ProjetoCriado`) nasce no 004
  com a primeira escrita. Registrar isso aqui evita inventá-lo sem consumidor
  (Princípio VI do método).

## Requisitos funcionais

### F7.1.1 — Admissão com falha rápida

RF-01: QUANDO iniciar sem qualquer um dos quatro parâmetros de admissão do §B.4
(`HOST_ORIGIN`, `HOST_BASE_URL`, `APP_ID`, `EMBED_URL`), O SISTEMA DEVE recusar-se a
subir com erro categorizado que nomeia **qual** faltou (códigos no
[`contracts/parametros-de-admissao.md`](contracts/parametros-de-admissao.md)). [F-07][F-09] 🟡

RF-02: O SISTEMA DEVE ler os parâmetros de admissão exclusivamente de configuração
(variável de ambiente), nunca de mensagem do canal nem de payload — origem descoberta em
runtime é origem *dita*, e o §B.2.3 proíbe conferir contra o que o remetente escolheu.
[F-07][F-06] 🟡

RF-03: QUANDO iniciar sem `DATABASE_URL` ou sem a credencial de introspecção
(`TOC_APP_CREDENTIAL`), O SISTEMA DEVE recusar-se a subir com os códigos próprios do
contrato — estes dois são exigência **nossa**, além dos quatro do §B.4, e o contrato os
declara como tal. 🟡

RF-04: QUANDO recusar-se a subir, O SISTEMA DEVE terminar com código de saída diferente
de zero, com o código de recusa na última linha do log estruturado, sem abrir porta nem
responder requisição — subir pela metade é não-conformidade nomeada (§B.4.1). [F-07] 🟡

RF-05: O SISTEMA DEVE tratar mudança de qualquer parâmetro de admissão como
reconfiguração (novo deploy), nunca como descoberta em runtime (§B.4.2). 🟡

### F7.1.2 — Introspecção

RF-06: QUANDO receber o grant no `ghd.handshake`, O SISTEMA DEVE trocá-lo imediatamente
por identidade em `POST {HOST_BASE_URL}/auth/introspect`, servidor a servidor, com a
credencial da aplicação no cabeçalho `Authorization: Bearer` — o grant nunca é validado
no navegador. [F-08][F-11][F-12] 🟡

RF-07: O SISTEMA NÃO DEVE construir identidade a partir do payload do handshake: o
payload é dado, e a identidade só existe depois de uma resposta `active: true` da
introspecção (§B.6.2, §B.9.5). [F-08] 🟡

RF-08: O SISTEMA DEVE guardar o Principal (usuário, `tenant_id`, `capabilities`,
`expires_at`) e descartar o grant após a troca — o grant é de uso único com TTL ≤ 120 s,
e a segunda introspecção do mesmo token responde `active: false` por desenho.
[F-10][F-13] 🟡

RF-09: QUANDO a introspecção responder `{active: false}`, O SISTEMA NÃO DEVE renderizar
dado algum e DEVE apresentar o estado `GRANT_INATIVO` com a ação "recarregar pelo shell"
— sem distinguir expirado de consumido de inexistente, porque a resposta não distingue
(§B.6.5). [F-08] 🟡

RF-10: QUANDO a introspecção estiver indisponível (falha de rede ou resposta 5xx), O
SISTEMA DEVE falhar fechado: estado `FUNDACAO_INDISPONIVEL`, nenhum dado renderizado,
nunca presumir o grant válido. 🟡

RF-11: QUANDO o hospedeiro responder 401 à credencial da aplicação, O SISTEMA DEVE
registrar o evento e sinalizar necessidade de rotação da credencial — sem retry
automático, porque o 401 é uniforme por desenho e não diz qual é o caso. [F-11] 🟡

RF-12: O SISTEMA DEVE derivar toda autorização exclusivamente das `capabilities` da
resposta de introspecção — nunca de texto de modelo, de tela ou de payload do canal
(P2, autorização fora do modelo de linguagem). 🟡

RF-13: QUANDO `expires_at` do Principal passar, O SISTEMA DEVE encerrar a sessão
embarcada e exigir novo embarque — sem renovar credencial por conta própria, porque não
há rota para isso e inventá-la seria segundo protocolo (P2). 🟡

### F7.2.1 — Envelope e handshake

RF-14: Toda mensagem emitida no canal DEVE ser um objeto com exatamente os quatro campos
`{protocol: "ghd", v: 1, type, payload}` — o contraexemplo é o envelope
`{tipo, versao, payload}` do protótipo da irmã, com o qual "a junta não fecharia"
(palavras da norma). [F-01][F-02] 🟡

RF-15: QUANDO montar embarcada, O SISTEMA DEVE emitir `ghd.ready` com payload
`{app_id: "toc"}` antes de qualquer outra mensagem — a aplicação fala primeiro (§B.2.2).
[F-01] 🟡

RF-16: QUANDO receber mensagem cujo `protocol` não seja `"ghd"` **ou** cujo `v` não seja
`1`, O SISTEMA DEVE ignorá-la sem efeito e sem resposta — responder já confirma presença
(§B.2.1). [F-01] 🟡

RF-17: QUANDO receber `type` desconhecido em envelope válido, O SISTEMA DEVE ignorá-lo
sem efeito — evolução aditiva (§B.2.5); quebrar por mensagem nova é defeito. 🟡

RF-18: QUANDO não receber `ghd.handshake` dentro da janela declarada (6 s, a mesma do
laboratório — §B.3.2), O SISTEMA DEVE apresentar o estado "sem canal" — honesto, não
fatal ([DÚVIDA] 2 do Clarify decide se há modo anônimo além dele). 🟡

RF-19: QUANDO receber `ghd.resource_changed`, O SISTEMA DEVE recarregar apenas os seus
próprios dados (a lista de projetos, neste ciclo) — o sinal não carrega escopo e não se
deriva escopo de payload (§B.9.2, lido pelo espelho da aplicação). 🟡

### F7.2.2 — Verificação de fonte e origem

RF-20: QUANDO receber qualquer mensagem do canal, O SISTEMA DEVE verificar **nesta
ordem**: (1) `ev.source === window.parent`; (2) `ev.origin` igual a `HOST_ORIGIN` da
configuração; (3) só então olhar o conteúdo — a trava dupla do §B.2.3, que no protótipo
da irmã existia pela metade (`ev.source === parent` **não existe** lá, registro da
própria norma). [F-03][F-05] 🟡

RF-21: O SISTEMA NÃO DEVE aceitar `ev.origin === "null"` em caso algum, e NÃO DEVE ler a
origem esperada de campo de payload — o contraexemplo `payload.host_origin` é circular e
está registrado na norma. [F-06] 🟡

RF-22: Todo `postMessage` emitido DEVE usar `HOST_ORIGIN` como `targetOrigin`; `"*"` é
proibido **inclusive** para o `ghd.ready` — o contraexemplo é o protótipo da irmã
postando `ghd.ready` com `"*"` tendo `HOST_ORIGIN` em mãos. [F-04] 🟡

RF-23: QUANDO descartar mensagem (fonte ou origem não admitida), O SISTEMA DEVE
registrar o descarte em log estruturado (origem ofensora truncada, sem payload) e
contá-lo em métrica — e NÃO DEVE responder. 🟡

### F7.2.3 — Modo conteúdo e tema

RF-24: O SISTEMA DEVE saber que está embarcado por sinal explícito na URL de embarque
(parâmetro declarado no manifesto), nunca por heurística de
`window.parent !== window` (§B.8.2). [F-17] 🟡

RF-25: Embarcado, O SISTEMA DEVE renderizar apenas conteúdo: sem cabeçalho de navegação
próprio, menu global, rodapé ou seletor de inquilino — quem navega é o hospedeiro
(§B.8.1). [F-17] 🟡

RF-26: QUANDO o handshake trouxer `theme.tokens`, O SISTEMA DEVE aplicá-los como
variáveis CSS por lista de permissão (só os tokens que o manifesto declara consumir) e
DEVE cobrir todo token ausente com o tema próprio — tokens são parciais por desenho
(§B.4.3). [F-18] 🟡

RF-27: Embarcado e identificado, O SISTEMA DEVE listar os projetos sintéticos do tenant
do Principal — a entrega visível do round 003: leitura, sob identidade real, sem
ferramenta ainda. 🟡

### F8.1.1 — Banco e migrações próprios

RF-28: O SISTEMA DEVE usar PostgreSQL Neon em **projeto próprio**, conectado por
`DATABASE_URL` — nenhuma tabela, esquema ou `Base.metadata` compartilhado com a
fundação. [F-19] 🟡

RF-29: Toda mudança de esquema DEVE nascer como migração Alembic com `upgrade` **e**
`downgrade`; o `downgrade` DEVE ser testado — aplicado e revertido num banco limpo sem
resíduo (portão da raia infra). 🟡

RF-30: O SISTEMA DEVE escolher o backend de persistência por configuração
(`DATABASE_URL`: Postgres × in-memory para teste), atrás de porta — o padrão comprovado
da fundação, lido e não copiado. [F-19] 🟡

### F8.1.2 — Isolamento por tenant

RF-31: Toda consulta de repositório DEVE ser filtrada pelo `tenant_id` do Principal; não
DEVE existir método de leitura sem parâmetro de tenant — e o teste de isolamento
consulta com dois principais de tenants distintos e prova a não-interseção. 🟡

### F8.2.1 — Observabilidade de nascença

RF-32: Todo endpoint do serviço DEVE nascer com span OTel; requisição sem traço é
defeito, não pendência (P5). 🟡

RF-33: A chamada de introspecção DEVE ter span próprio, correlacionado ao traço da
requisição de embarque — o traço de ponta a ponta é parte da aptidão "a junta fecha". 🟡

RF-34: Todo log DEVE ser estruturado e carregar o `trace_id` da requisição; falha de
admissão (RF-04) e descarte de mensagem (RF-23) DEVEM aparecer em log e métrica. 🟡

RF-35: QUANDO não houver coletor OTel configurado, O SISTEMA DEVE operar com exportador
nulo — observabilidade ausente degrada o diagnóstico, nunca o serviço. 🟡

### F8.5.1 — Deploy e CI

RF-36: A interface e o serviço DEVEM ser publicados em site cujo eTLD+1 é **distinto**
do hospedeiro (§B.1.2) — Vercel e Railway conforme o ADR 0002; o endereço passa pelo
portão humano antes de entrar no manifesto. [F-16] 🟡

RF-37: O manifesto DEVE declarar `mode: embedded`, `app_id: toc`, `url` e `origin` em
`https` na mesma origem do deploy, e ser submetido à rota real de administração da
fundação — sujeito ao bloqueio externo L-01 (schemas mutuamente exclusivos quando a irmã
mediu). [F-14] 🟡

RF-38: A CI DEVE rodar, em todo pull request: a suíte de testes, as funções de aptidão
do projeto (`check-caminhos.sh`, `check-adrs-sucessao.sh`, `check-specs.sh`,
`check-links.sh`) e o lint de arquitetura (`import-linter`) — vermelho bloqueia merge. 🟡

RF-39: O procedimento de rollback de deploy (interface e serviço) DEVE estar documentado
e **ensaiado uma vez** dentro do ciclo, com a saída do ensaio colada no
`qa-report.md` (raia infra: reversibilidade é entrega, não intenção). 🟡

## Requisitos de interface

RI-01: Cada estado de fronteira — "aguardando handshake", "sem canal", `GRANT_INATIVO`,
`FUNDACAO_INDISPONIVEL` — DEVE ter tela própria com nome do estado, explicação de uma
frase e ação disponível; nunca um frame em branco. 🟡

RI-02: As telas de erro NÃO DEVEM expor detalhe interno (URL de introspecção, stack,
conteúdo de payload): código categorizado + ação, e o resto vai para o traço. 🟡

RI-03: Embarcada, a única tela de conteúdo deste ciclo é a lista de projetos: nome,
ferramenta e última atualização, sob o tema do inquilino. 🟡

RI-04: O tema próprio (fallback) DEVE cobrir claro e escuro; token do inquilino ausente
nunca deixa elemento sem cor definida (mesma régua do ciclo 002). 🟡

RI-05: O foco de teclado NÃO DEVE ficar preso dentro do frame; a troca para estado de
erro DEVE ser anunciada a leitor de tela (`aria-live`). 🟡

RI-06: Toda string visível DEVE viver em arquivo de mensagens (português como
língua-fonte) — preparação para o E8.3, que consolida i18n no ciclo 011. 🟡

RI-07: A jornada de embarque (feliz + três estados de falha) DEVE ter captura gerada por
script versionado a partir do build embarcado real, com avaliação heurística datada
(P6). 🟡

RI-08: Modo autônomo (fora de iframe, para desenvolvimento) DEVE existir e ser
visivelmente distinto do embarcado — com aviso "modo de desenvolvimento, sem identidade
da fundação" — para ninguém confundir a casca local com a junta real. 🟡

## Requisitos não funcionais

RNF-01: O grant NUNCA aparece em log, traço, URL ou armazenamento — redigido em toda
saída; a verificação é um grep negativo sobre os logs do teste de embarque. 🟡

RNF-02: A credencial da aplicação (`TOC_APP_CREDENTIAL`) vive só no servidor, por
variável de ambiente — nunca no bundle, nunca no navegador (P7; a violação canônica da
linhagem está medida em [F-20]). 🟡

RNF-03: Fail-closed em todo caminho de erro da fronteira: exceção não tratada na
admissão, na introspecção ou no canal resulta em negação, nunca em acesso. 🟡

RNF-04: Nenhum dado real de pessoa em fixture, log de exemplo ou captura (ADR 0006) —
o portão é grep das personas proibidas sobre `fixtures/` e `docs/jornadas/`. 🟡

RNF-05: Adaptadores de fronteira (canal, introspecção) com teste de fluxo feliz **e** de
cada fluxo de erro — a cobertura dos caminhos de recusa é a que importa aqui. 🟡

RNF-06: Tempo do `ghd.ready` à lista renderizada: **medido e registrado** pelo traço
OTel em todo embarque; alvo proposto ≤ 3 s em rede de referência, a fixar no gate
(L-06 — não há baseline antes da primeira medição real). 🟡

RNF-07: Reinício do hospedeiro invalida embarques em voo (grants em memória lá — L-03):
O SISTEMA DEVE tratar o caso como `GRANT_INATIVO` comum, sem tratamento especial e sem
abrir chamado como se fosse defeito nosso. 🟡

RNF-08: A aplicação DEVE funcionar sob o sandbox mínimo do hospedeiro
(`allow-scripts allow-same-origin`) sem pedir permissão adicional neste ciclo. 🟡

RNF-09: Segredos ausentes do repositório: nenhum valor de `TOC_APP_CREDENTIAL` ou
`DATABASE_URL` em arquivo versionado — o portão é grep por prefixo (`ghd_`,
`postgres://`) sobre a árvore. 🟡

RNF-10: O pipeline de CI DEVE terminar em menos de 10 minutos — acima disso o portão
deixa de ser rodado antes do push, e portão que não roda não protege. 🟡

## Regras de negócio

Nenhuma regra de negócio TOC entra neste ciclo — a junta é infraestrutura, e os
critérios de UDE, suficiência causal e afins nascem com o M2 (ciclo 005). A única regra
de negócio própria do ciclo:

RN-01: Projeto sintético é **somente leitura** neste ciclo: nenhuma escrita vinda do
hospedeiro, nenhuma ação de mutação exposta — escrita e catálogo nascem juntos no ciclo
006, com a FSM de proposta (round 003, "Fora"). 🟡

## Integrações

INT-01: `POST /auth/introspect` da fundação — a fronteira de identidade. Contrato: corpo
`{token}`, credencial da aplicação em `Authorization: Bearer`, três respostas possíveis
(sessão ativa · grant ativo sem `role` · `{active:false}` e só), todas com status de
sucesso. Rota real medida: [F-12] 🟢. Consumo: RF-06..RF-11.

INT-02: Canal `postMessage` `ghd.*` — vocabulário consumido neste ciclo: emite
`ghd.ready`; recebe `ghd.handshake` e `ghd.resource_changed`. `ghd.action_result` só
nasce quando houver ação (ciclo 006). Envelope e travas: RF-14..RF-23.

INT-03: Admissão — os quatro parâmetros do §B.4 + credencial, entregues pela
Administradora do tenant a partir do bloco "Contrato de admissão" do painel da fundação;
manifesto submetido a `POST /admin/federated` (sujeito a L-01/L-02). Contrato nosso:
[`contracts/parametros-de-admissao.md`](contracts/parametros-de-admissao.md).

INT-04: Exportação OTel — OTLP por variável de ambiente; sem coletor, exportador nulo
(RF-35).

INT-05: **O que este ciclo NÃO integra** (declarado para ninguém procurar): catálogo
`toc.*`, snapshot, registro de telas e wire SSE — tudo no ciclo 006
([`../006-acoes-governadas-e-snapshot/spec.md`](../006-acoes-governadas-e-snapshot/spec.md)).

## Telas e fluxos

### 6.1 Lista de projetos (embarcada) — Job: provar a identidade na prática · Campos:
nome do projeto, ferramenta, última atualização · Ações: nenhuma mutadora (RN-01);
recarregar via `ghd.resource_changed`.

### 6.2 Estados de fronteira — Job: falha honesta, nunca frame branco · Estados:
"aguardando handshake" (com janela de 6 s), "sem canal", `GRANT_INATIVO` (ação:
recarregar pelo shell), `FUNDACAO_INDISPONIVEL` (ação: tentar de novo) · Campos: nome do
estado + uma frase + ação (RI-01, RI-02).

### 6.3 Fluxo de embarque (o feliz)
1. Hospedeiro monta o iframe com a URL de embarque (+ sinal explícito de modo embarcado).
2. Aplicação carrega, emite `ghd.ready {app_id: "toc"}` com `targetOrigin = HOST_ORIGIN`.
3. Hospedeiro responde `ghd.handshake {token, tenant, capabilities, theme}`.
4. Aplicação verifica `ev.source` e `ev.origin`, aceita, aplica tema com fallback.
5. Servidor da aplicação troca o grant em `POST /auth/introspect` (credencial própria).
6. Resposta `active: true` vira Principal; lista de projetos do tenant renderiza.
7. Traço OTel único cobre 2→6; grant descartado.

## Entregáveis

- Serviço FastAPI mínimo: admissão fail-fast, porta de identidade + adaptador de
  introspecção, repositório de projetos (Postgres + in-memory), rota de leitura.
- Interface: casca embarcável (modo conteúdo), adaptador do canal `ghd.*`, telas 6.1/6.2,
  tema com fallback.
- Migração Alembic `0001` (tenant/projeto) com downgrade testado.
- Manifesto da aplicação (`mode: embedded`, `app_id: toc`) + submissão real (ou a
  mensagem `mensagens/NNN` se L-01 persistir).
- [`contracts/parametros-de-admissao.md`](contracts/parametros-de-admissao.md) (neste
  ciclo vira código; o documento já existe como contrato) e
  [`data-model.md`](data-model.md).
- CI (testes + aptidões + import-linter), deploy Vercel + Railway, rollback documentado
  e ensaiado.
- Jornada viva do embarque (captura por script + heurística datada) e entrada no
  `CHANGELOG.md`.

## Critérios de aceite (DoD)

| # | Critério | Verificação executável |
|---|---|---|
| 1 | Admissão recusa nomeando o que faltou | `pytest tests/admissao -q` — um teste por parâmetro ausente, asserta código e exit ≠ 0 |
| 2 | Handshake nunca confiado | `pytest tests/identidade -q` — payload forjado sem introspecção não produz Principal |
| 3 | Grant trocado e descartado | `pytest tests/identidade -q -k grant` — introspecção chamada 1×; grep negativo do grant nos logs |
| 4 | Falha fechada | `pytest tests/identidade -q -k indisponivel` — 5xx/timeout ⇒ negação, zero dado |
| 5 | Trava dupla do canal | `pytest tests/canal -q` — `ev.source` errado descarta; origem errada descarta; `"null"` descarta; nunca responde |
| 6 | `targetOrigin` dirigido | `grep -rn 'postMessage' app/web/src/federacao/ \| grep -v HOST_ORIGIN` ⇒ vazio |
| 7 | Envelope canônico | `pytest tests/canal -q -k envelope` — `{tipo, versao}` (o da irmã) é ignorado sem resposta |
| 8 | Migração reversível sem resíduo | `alembic upgrade head && alembic downgrade base` num Neon limpo; `\dt` vazio ao final, saída colada |
| 9 | Isolamento por tenant | `pytest tests/persistencia -q -k isolamento` — dois tenants, interseção vazia |
| 10 | Traço de ponta a ponta | teste de integração asserta spans embarque→introspecção→consulta sob o mesmo `trace_id` |
| 11 | eTLD+1 distinto | comparação dos domínios registráveis publicados, colada no `qa-report.md` (portão humano) |
| 12 | Junta fecha contra a `ghdaru` real | roteiro do `qa-report.md`: manifesto aceito (ou L-01 re-medido + mensagem), introspecção servidor a servidor com resposta colada |
| 13 | Sem segredo versionado | `grep -rEn 'ghd_[A-Za-z0-9]\|postgres://' --include='*' . \| grep -v exemplo` ⇒ vazio |
| 14 | Rollback ensaiado | saída do ensaio (deploy anterior restaurado) colada no `qa-report.md` |

## Fontes

F-01: `/home/user/protocolos/padrao/anexo-b-federacao.md:44-50` — §B.2.1: envelope de
exatamente quatro campos `{protocol:"ghd", v:1, type, payload}`; mensagem que não case
`protocol` e `v` é ignorada sem resposta — uso: RF-14..RF-16 🟢

F-02: `/home/user/protocolos/padrao/anexo-b-federacao.md:52` — o contraexemplo do
envelope: a irmã implementou `{tipo, versao, payload}` (`prototipo/adaptadores.js:129`)
e "hoje a junta não fecharia" — uso: RF-14, DoD 7 🟢

F-03: `/home/user/protocolos/padrao/anexo-b-federacao.md:56` — §B.2.3: ordem de
verificação (1) `event.source`, (2) `event.origin` por igualdade com origem de
configuração, (3) conteúdo — uso: RF-20 🟢

F-04: `/home/user/protocolos/padrao/anexo-b-federacao.md:62` — defeito real registrado:
`prototipo/adaptadores.js` posta `ghd.ready` com `parent.postMessage(pronto, "*")` tendo
`HOST_ORIGIN` em mãos — uso: RF-22 🟢

F-05: `/home/user/protocolos/padrao/anexo-b-federacao.md:23` — tabela de proveniência:
o protótipo da irmã verifica só `ev.origin`; "`ev.source === parent` **não existe**" —
uso: RF-20 🟢

F-06: `/home/user/protocolos/padrao/anexo-b-federacao.md:58` — caso real da origem lida
de `payload.host_origin` (circular) e `event.origin === "null"` nunca aceitável — uso:
RF-02, RF-21 🟢

F-07: `/home/user/protocolos/padrao/anexo-b-federacao.md:85-93` — §B.4: tabela dos
parâmetros de admissão (4 linhas com "recusa de subir" — contado por
`grep -c 'recusa de subir'` = `4`) e §B.4.1: recusar subir nomeando qual faltou — uso:
RF-01..RF-04 🟢

F-08: `/home/user/protocolos/padrao/anexo-b-federacao.md:123-139` — §B.6: grant de uso
único e vida curta; a aplicação não confia na credencial (§B.6.2); as três respostas da
introspecção (§B.6.3, linhas 129-133); `{active:false}` sem distinção (§B.6.5) — uso:
RF-06..RF-09 🟢

F-09: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:152-167` —
§4.3 do guia: os quatro parâmetros por configuração, nunca por mensagem; "recuse subir
com erro categorizado que diga qual faltou" — uso: RF-01, RF-02 🟢

F-10: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:196-199` —
"O token é um grant de USO ÚNICO (`ghdg_…`, TTL 120 s) — troque-o IMEDIATAMENTE por
identidade via `POST /auth/introspect` (…) guarde o principal, não o token" — uso:
RF-06, RF-08 🟢

F-11: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:116-147` —
contrato do introspect com `Authorization: Bearer ghd_<credencial>` (spec 047 da
fundação), 401 uniforme e seu tratamento sem retry cego — uso: RF-06, RF-11 🟢

F-12: `/home/user/ghdaru/apps/api/src/ghdaru_api/http/auth_router.py:139` —
`@router.post("/auth/introspect")`: a rota existe na fundação real, com autenticação de
chamador (`_calling_app`, 401 uniforme) — uso: INT-01 🟢

F-13: `/home/user/ghdaru/apps/api/tests/identity/test_embed_grant.py:44` —
`assert EMBED_GRANT_TTL <= timedelta(seconds=120)` ("vida curta é requisito, não
acaso") — uso: RF-08 🟢

F-14: `/home/user/gestaodeprioridades/mensagens/005-para-ghdaru-embarque-da-prioridades.md:14-23`
— "Os dois schemas de manifesto são mutuamente exclusivos" · "REJEITADO · 4 erros" — a
medição da irmã que fundamenta L-01 — uso: RF-37, L-01 🟢

F-15: `/home/user/gestaodeprioridades/specs/002-prototipo-de-interfaces/contracts/parametros-de-admissao.md`
— o contrato de admissão da irmã, modelo do nosso (códigos de recusa por parâmetro,
erros de fronteira) — uso: contracts/ 🟢

F-16: `/home/user/protocolos/padrao/anexo-b-federacao.md:38` — §B.1.2: servida de site
distinto (eTLD+1) do hospedeiro; recusa como estado honesto — uso: RF-36 🟢

F-17: `/home/user/protocolos/padrao/anexo-b-federacao.md:159-161` — §B.8.1 (só
conteúdo) e §B.8.2 (sinal explícito, nunca heurística de `window.parent`) — uso:
RF-24, RF-25 🟢

F-18: `/home/user/protocolos/padrao/anexo-b-federacao.md:97` — §B.4.3: tokens de tema
parciais por desenho; tema padrão obrigatório para o que não vier — uso: RF-26 🟢

F-19: `/home/user/ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:39-41` —
"seu banco e migrações são seus (não compartilhe `Base.metadata`)"; factory por
`DATABASE_URL` (`persistence/factory.py` como referência) — uso: RF-28, RF-30 🟢

F-20: `/home/user/ghdaru/apps/api/src/ghdaru_api/identity/adapters/in_memory.py:58-60`
— grants de embed em repositório in-memory declaradamente protótipo ("sobreviver a
restart não é requisito") — uso: RNF-07, L-03 🟢

## Lacunas e assunções

L-01: **Os dois schemas de manifesto eram mutuamente exclusivos quando a irmã mediu**
(golden da fundação × normativo do Anexo B, 4 erros na validação cruzada — [F-14]) —
assunção: re-medição na abertura do ciclo; se persistir, o ciclo entrega tudo menos o
registro do manifesto, com mensagem nossa referenciando a da irmã — risco **alto** (é o
único item da aptidão central que não depende só de nós).

L-02: **A fatia de federação da fundação é desligada por padrão**
(`FEDERATION_MANIFESTS_ENABLED` — `ghdaru/apps/api/src/ghdaru_api/http/manifest_loader.py:28`
🟢; sem ela, tudo responde 404) — assunção: ligar é do operador da fundação e será
pedido na abertura do ciclo — risco **médio**.

L-03: **Grants de embarque vivem em memória no hospedeiro** ([F-20]) — assunção:
reinício do host invalida embarques em voo e a aplicação trata como `GRANT_INATIVO`
comum (RNF-07); aceitável para leitura — risco **baixo**.

L-04: **A autenticação do chamador da introspecção é 🧪 na norma** (§B.6.6), mas a
fundação já a implementa (spec 047 — [F-11], [F-12]) — assunção: seguimos a
implementação real da fundação; se a norma fechar a cláusula com forma diferente, o
adaptador de introspecção absorve a mudança — risco **baixo**.

L-05: **Ambiente de teste da fundação não confirmado** (quinta linha da tabela do §B.4:
"DEVE ser oferecido", mas não impede subir) — assunção: sem ele, o ensaio da junta
acontece direto no ambiente real com tenant de teste — risco **médio** (vai ao Clarify).

L-06: **Não há baseline de desempenho do embarque** — assunção: o alvo ≤ 3 s do RNF-06 é
proposto, não medido; a primeira medição real o calibra no gate — risco **baixo**.

## Clarify

- [DÚVIDA] 1 — Qual é o endereço publicado (eTLD+1) da aplicação? A escolha é
  irreversível na prática (entra no manifesto que circula) e o roadmap a declara portão
  humano deste ciclo. Proposta a aprovar antes do RF-36.
- [DÚVIDA] 2 — Sem `ghd.handshake` na janela, seguimos só com o estado "sem canal"
  (RF-18) ou implementamos o modo anônimo que o §B.3.1 recomenda (DEVERIA), com conteúdo
  público sem dado de usuário? O ciclo 003 não tem conteúdo público óbvio; a proposta é
  "sem canal" agora e modo anônimo como decisão do ciclo 011.
- [DÚVIDA] 3 — O manifesto v1 declara `capabilities_required: ["toc:read"]` apenas (este
  ciclo é somente leitura — RN-01), com `toc:write` entrando no ciclo 006? Ou já declara
  as duas para evitar re-admissão?
- [DÚVIDA] 4 — Existe ambiente de teste da fundação para exercitar a junta (L-05)? Quem
  emite a credencial e o tenant de ensaio?
- [DÚVIDA] 5 — Se L-01 persistir na re-medição, confirmar que a entrega "tudo menos o
  registro do manifesto" fecha o ciclo com gate aprovado — ou se o ciclo fica aberto até
  os schemas convergirem.
