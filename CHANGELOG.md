# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

### Corrigido — a Árvore da Realidade Atual era o único agregado de ferramenta fora da trava otimista (2026-09-07)

Achado por crítico hostil, com medida que não deixa dúvida:
`apps/api/src/toc_api/dominio/ara.py` nunca chamava
`Projeto._avancar`, onde a versão incrementa.

```text
$ for f in ara nuvem arf apr at snt focalizacao; do grep -c '_avancar' src/toc_api/dominio/$f.py; done
ara 0 · nuvem 11 · arf 10 · apr 6 · at 2 · snt 5 · focalizacao 10
```

A trava do ADR 0010 tem **duas metades** e só uma estava medida: a do adaptador (`UPDATE …
WHERE versao = :versao_lida`, com portão próprio) e a do domínio — **a versão só protege o
que ela acompanha**. Marcar Efeito Indesejável (UDE), editar a ficha, registrar parecer,
mudar o status para `validado`, examinar elo e formar conector E não avançavam versão
nenhuma, então duas gravações que leram a mesma versão casavam as duas no `WHERE`, e a
reconciliação apagava do banco o retrato de quem gravou primeiro — `delete(tabela_ude …
no_id.notin_(marcados))`, com `ude_parecer.no_id` em `ON DELETE CASCADE`. Reproduzido
primeiro, contra o PostgreSQL real:

```text
concorrência M2 (parecer da ARA): 20 escritas · aceitas 20 · recusadas 0 · pareceres no banco 1
AssertionError: 20 escrita(s) aceita(s) e 1 parecer(es) no banco: julgamento humano aceito e perdido em silêncio
Failed: DID NOT RAISE ConflitoDeVersao
```

- **Diagnóstico antes do conserto.** Não foi só ordem histórica. A Nuvem de Conflito também
  é anterior à trava e **tem** o `_avancar`: a topologia dela é fixa (RN-01 da spec 007),
  logo nenhuma delegação ao núcleo cria linha, e o teste de concorrência dela **teve** de
  disputar uma mutação própria. A ARA tinha `adicionar_efeito`, e o teste escrito no ciclo
  008 para provar que "a ARA tem a mesma trava que o M1" foi verde **pelo `_avancar` do
  núcleo**, sem tocar em uma linha de semântica da ferramenta. A ARA é o único agregado de
  ferramenta anterior à trava que tinha onde se esconder.
- **Correção.** As oito mutações próprias da ARA passam a chamar `self.projeto._avancar(em)`.
- **Portão que fecha a CLASSE**, não o caso: `scripts/check-versao-do-agregado.sh` tira o
  **denominador do registro de raízes de ferramenta** (`registrar_raiz_de_ferramenta`) — a
  lista que toda ferramenta é obrigada a preencher para o grafo dela funcionar — e reprova
  a diferença entre "registrada" e "avança versão". Mede as duas direções: também reprova
  `salvar_*` que grava sem `_gravar_*`, raiz registrada sem caminho de escrita, e caminho
  de escrita novo para agregado fora do registro. Medida do inverso, executada: **7 de 7
  raízes casadas com caminho de escrita condicionado**. Com 5 sabotagens próprias.
- Decisão: `docs/adr/0016-versao-do-agregado-como-portao-derivado-do-registro.md`.
- **Pendência declarada, medida e não resolvida**: a ARA é também a única raiz cujas
  mutações próprias não chamam `Projeto._exigir_ativo` (`ara 0 · nuvem 12 · arf 4 · apr 2 ·
  at 2 · snt 6 · focalizacao 11`) — marcar UDE num projeto **excluído** ainda é aceito.
  Mesma família, ciclo próprio.


### Corrigido — caminhos que ninguém percorria inteiros: o embarque não alcançava o produto, e a cadeia exportada não voltava (2026-09-07)

Varredura da MESMA classe de problema da regressão anterior: caminho que existe, em que
todo mundo confia, e que nenhum teste percorre de ponta a ponta. Dois defeitos duros
saíram dela, os dois achados por teste novo que falhou antes do conserto.

- **A sessão emitida por `POST /toc/embarque` era recusada por toda rota de produto.** A
  borda tinha DOIS resolvedores de identidade: `http/aph.py::principal_de` consultava as
  sessões do embarque **e** o `ProvedorDeIdentidade`; `http/dependencias.py::obter_principal`
  — que autentica `/toc/projetos`, `/toc/ara`, `/toc/nc`, `/toc/arf`, `/toc/apr`, `/toc/at`,
  `/toc/snt`, `/toc/focalizacao`, `/toc/portabilidade`, `/toc/cadeia` e `/toc/propostas` —
  consultava só o segundo. Medido: o token do embarque abria `/aph/catalog` com `200` e
  recebia `401 UNAUTHENTICATED` em `POST /toc/projetos`. Como a interface manda esse mesmo
  token em toda chamada (`apps/web/src/api/cliente.ts:119`), a aplicação embarcada não
  alcançava rota nenhuma do produto fora da fronteira conversacional. Conserto na causa e
  não no sintoma: **um** resolvedor (`dependencias.resolver_principal`), usado pelos dois
  lados, com a verificação de validade da identidade dentro dele.
- **Exportar e reimportar uma cadeia de cinco ferramentas quebrava no banco.** A Nuvem
  guarda, em cada injeção escolhida, o projeto que ela semeou, e a coluna tem chave
  estrangeira para `projeto`; a importação gravava na ordem do arquivo (`ara → nc → arf …`),
  logo a Nuvem chegava apontando para uma Árvore da Realidade Futura que ainda não existia.
  Saída colada: `ForeignKeyViolation … fk_nc_injecao_semeadura_projeto_id_projeto`. Nenhum
  teste pegava porque a ida e volta só era exercitada sobre uma cadeia de DUAS ferramentas,
  e o duplo em memória não tem chave estrangeira para violar. `aplicacao.portabilidade.
  ordem_de_gravacao` põe quem é apontado antes de quem aponta; o **relato** continua na
  ordem do arquivo, para um detalhe de chave estrangeira não vazar para o contrato.

### Acrescentado — cinco suítes de caminho inteiro, e duas funções de aptidão que impedem o buraco de voltar (2026-09-07)

- `apps/api/tests/integracao/test_catalogo_ponta_a_ponta_no_postgres.py` — **toda** ação do catálogo
  `toc.*` do pedido ao estado relido por aplicação nova, mais a recusa deixando o estado
  byte a byte intacto. Carrega a **forcing function**: ação nova sem cenário derruba a
  suíte.
- `apps/api/tests/integracao/test_borda_federada_no_postgres.py` — o caminho do hospedeiro até
  `executed` sobre estado real, pelas duas formas (borda `POST /aph/actions/{id}` e fio
  conversacional com evento `action_proposal`). Antes, **todas** as propostas do lado
  federado apontavam para `UUID_INEXISTENTE`: o `executed` nunca acontecia.
- `apps/api/tests/integracao/test_embarque_com_fundacao_no_postgres.py` — o embarque inteiro contra
  uma fundação de mentira de pé em `127.0.0.1`, exercitando `IntrospeccaoHttp` de verdade
  (grant no corpo, credencial no cabeçalho) e as três falhas fechadas do §B.6.
- `apps/api/tests/integracao/test_cadeia_completa_no_postgres.py` — a travessia das cinco
  ferramentas pelo HTTP e pelo banco, do Efeito Indesejável ao passo de transição, com
  aplicação nova a cada elo; simetria a partir dos cinco pontos de partida; e a ida e volta
  do arquivo sobre a cadeia toda.
- `apps/api/tests/contrato/test_http_porta_dos_fundos_por_ferramenta.py` — as oito mutações de grafo
  × as sete ferramentas × as duas portas (rota genérica e catálogo). A lista de ferramentas
  sai de `RAIZ_POR_FERRAMENTA`: **ferramenta nova entra na varredura no dia em que se
  registra**.

### Corrigido — a regressão que o nosso próprio conserto criou: o catálogo federado voltou a alcançar as ferramentas (ADR 0015, 2026-09-07)

Fechar a porta dos fundos do agregado foi certo. O que ficou errado foi o outro lado, e
ninguém voltou para olhar: as quatro ações mutadoras genéricas do catálogo —
`toc.criar_nos`, `toc.criar_arestas`, `toc.atualizar_no`, `toc.excluir_nos` — continuaram
anunciando `ui_route: /toc/ara` e ligadas aos casos de uso **genéricos** do M1 (Núcleo de
Diagramas Lógicos). Como `Projeto._exigir_raiz` recusa comando genérico em toda ferramenta
com raiz, elas passaram a **falhar para sempre** em `ara`, `nc`, `arf`, `apr`, `at` e
`focalizacao`. Reproduzido de ponta a ponta contra o PostgreSQL real: criar uma Árvore da
Realidade Atual (ARA), propor `toc.criar_nos` com dois alvos, aprovar no gate humano, e o
desfecho voltar `failed`. A assistência de inteligência artificial (IA) da fundação — o
motivo de a aplicação ser federada — não alcançava **nenhuma** ferramenta do produto.

- **Diagnóstico antes do conserto.** A lacuna era de **uma** ferramenta, não de seis: o M3
  (Nuvem de Conflito), o M4 (árvores de futuro e implementação) e o M6 (focalização) já
  despachavam pelas raízes deles. A ARA é que ficou de fora, porque a "ação da ARA" que
  existia era a genérica com `ui_route: /toc/ara` — e a spec 005 (RF-32..RF-35,
  INT-02..INT-06) já tinha declarado quais eram as ações certas dela, no ciclo anterior.
- **Toda ação do catálogo declara a ferramenta cuja raiz a governa** (campo `ferramenta` no
  `ActionSpec`). Invariante de domínio: ação `risk: confirm` sem ferramenta **não entra** no
  catálogo, e o valor aceito é a genérica ou uma ferramenta cuja raiz se registrou — quem
  esquecer de se registrar fica bloqueada, nunca liberada.
- **A ARA ganhou as quatro ações que a spec 005 lhe prometia**, pelos casos de uso da raiz:
  `toc.suggest_udes` (`AdicionarEfeito` + `MarcarUde` — o Efeito Indesejável nasce com ficha
  e a validação formal roda), `toc.suggest_causes` (`AdicionarEfeito` + `LigarNaARA` — a
  causa nasce ligada), `toc.suggest_relations` (`LigarNaARA` — o elo nasce
  `nao_examinado`) e `toc.suggest_reformulation` (`ReformularUde` — mudar o texto reexecuta
  a validação). Catálogo: **16 → 20 ações**; manifesto regerado da mesma fonte e ainda
  válido contra o schema normativo do Anexo B, com as **7 sabotagens repelidas**.
- **As quatro genéricas pararam de mentir**: `ui_route: /toc/projetos`, descrição que aponta
  a ação certa de cada ferramenta, e `intent_keywords` que não capturam mais intenção da
  ARA.
- **A guarda da raiz continua fechada, provada sem depender da borda.** O executor recusa o
  desencontro de ferramenta com uma mensagem que **lista as ações daquela ferramenta** — mas
  isso é conveniência, não proteção, e há teste que desarma essa guarda de borda (um
  catálogo que declara `toc.criar_nos` como sendo da nuvem) e mostra a invariante do domínio
  recusando do mesmo jeito.
- **Portão novo — `scripts/check-acao-de-catalogo.sh`**, leitura estática (árvore sintática
  abstrata) do par catálogo × executor, sem importar nem executar nada: ação mutadora sem
  ferramenta declarada, ferramenta com raiz acionando caso de uso genérico, ação genérica
  acionando caso de uso de ferramenta, ação sem entrada no despacho, e mão mutadora que não
  aciona caso de uso nenhum. **5 sabotagens novas** (13 portões, 81 sabotagens no total).
- **A sonda sem asserção virou teste.** `apps/api/tests/integracao/` (o arquivo `test_zz_probe.py`) imprimia e não
  reprovava nada; foi substituída por
  `apps/api/tests/integracao/test_catalogo_por_ferramenta_no_postgres.py`, que percorre proposta →
  gate humano → desfecho contra o PostgreSQL real, ferramenta por ferramenta, e checa a
  recusa da rota genérica nas sete.
- **Ausência declarada, não esquecimento**: a Estratégia & Táticas (S&T) continua sem ação
  `toc.*` (spec 010, INT-04), e um teste afirma isso para não virar dívida silenciosa.
- **De quebra, a suíte de integração deixou de ser aleatória.** Ao acrescentar cinco testes
  de integração, a suíte inteira começou a cair com `FATAL: sorry, too many clients
  already` — **111 ocorrências, 5 falhas e 51 erros numa execução**, e a execução
  imediatamente anterior, sobre o mesmo código, verde com **1593 testes**. A causa não era
  o conserto: cada `criar_app` monta um motor com *pool* próprio, e só **5 dos 20** arquivos
  de integração devolviam esse *pool* ao cluster (`liberar_conexoes`, à mão); os outros 15
  seguravam as conexões até a coleta de lixo. Com `max_connections = 100`, a ordem de
  execução decidia o resultado — e suíte que falha em ordem aleatória não é evidência de
  nada. Agora uma fixture `autouse` do `apps/api/tests/integracao/conftest.py` registra todo motor
  criado durante o teste e o libera no fim: **174 testes de integração verdes e 7 conexões
  residuais** no cluster ao fim da execução, contra as 100 de antes.


### Documentação — o corpo documental alcançou a aplicação: site regerado, matriz do APH preenchida, relatórios de ciclo fechados (lote de fechamento documental, 2026-09-06)

Este lote não escreveu código de produção. Ele fechou a distância entre o que o repositório
**é** e o que os documentos **diziam que ele era** — que é uma dívida de honestidade, e por
isso paga com evidência colada, não com adjetivo.

- **O site de produto voltou a descrever este repositório.** `docs/product-site/` tinha sido
  gerado quando não havia uma linha de código de produção, e afirmava isso em três lugares —
  o pior deles uma métrica `Linhas de código de produção: 0` que era **constante escrita no
  gerador**, não medição. O gerador vendorizado ganhou a **adaptação 17**
  (`tools/product-site/README.md`): ele agora varre `apps/api` e `apps/web` e **conta** —
  arquivos e linhas de produção por camada, casos de teste escritos por suíte, rotas
  publicadas com o prefixo do próprio `APIRouter`, migrações, tabelas, portões e sabotagens.
  O site ganhou uma página **Código**, os módulos M1–M8 passaram a mostrar o que existe de
  cada um, e a "nota de honestidade" do roadmap deixou de ser um parágrafo digitado para ser
  derivada dos números.
  - A contagem estática de rotas foi **conferida contra o serviço de verdade**: o gerador diz
    `rotas=144` e `app.openapi()` devolve `operações no OpenAPI: 144 caminhos: 128`.
  - O que o gerador **não** faz está escrito na página: ele conta o que está **escrito**, não
    o que passou. `it.each` conta como uma declaração e vira N casos na execução — por isso
    o número do site (`casos=1514`) e o do executor (`1485 passed` no serviço,
    `307 passed` na interface) não têm de bater, e o site diz isso em vez de esconder.
  - Nada foi digitado: a atribuição de arquivo a módulo é um **mapa declarado**
    (`_MAPA_DE_CODIGO`), e os 9 arquivos que não casam padrão nenhum aparecem ao pé da
    página em vez de sumirem no arredondamento.
  - De quebra, a **adaptação 18**: a página de artefatos anunciava "0 passos" em jornadas
    de até treze passos, porque contava `## Passo N` (a convenção da origem) e não
    `### N · título` (a daqui). Um número errado é pior que nenhum número.
- **A matriz de aderência ao Padrão APH (Aplicação ↔ Harness) foi preenchida linha a linha**
  — a tarefa T-07 do ciclo 012, que estava declarada como dívida **Dv-3** e agora está
  fechada. Das 60 linhas: **46 `● atendido`** com `arquivo:linha` e teste, 2 `◑ parcial`,
  4 `○ planejado / não emitido`, 4 `✦ delegado à fundação` (ADR 0007) e 4 `✗ fora do alvo
  v1`. Três linhas mudaram de natureza, não só de status: §B.3.1 (modo anônimo saiu de
  "decisão adiada" para implementado), APH-5.3 (a deduplicação deixou de ser por estado da
  máquina de estados e virou unicidade no banco, migração `0007`) e APH-3.4 (o
  `context_hash` passou a ser calculado no servidor e comparado na confirmação). O
  contador `scripts/contar-aderencia-aph.py` nasceu junto, porque contar as marcas com
  `grep -o` sobre o arquivo inteiro devolve **52** onde as tabelas têm 46 — a legenda e a
  prosa também têm as marcas.
- **O preenchimento encontrou um defeito, e ele não foi arredondado.** Interface, serviço e
  manifesto declaram **17, 16 e 12 telas**, e a tela da Nuvem de Conflito (`toc.nuvem`)
  **não existe no registro do serviço**. A consequência é silenciosa e foi reproduzida no
  domínio puro: o snapshot dessa tela é **aceito** e chega ao modelo com **zero campos**,
  porque a terceira camada da sanitização descarta o que não está declarado
  (`campos: ()` contra `campos: (('projeto_id', 'text', 1, ''),)` na Árvore da Realidade
  Atual). Por isso a linha APH-3.1 é `◑ parcial`, e não `● atendido`. **Relatado, não
  corrigido**: consertar toca o manifesto, que é contrato sob gate humano ação a ação, e
  exige teste que falhe antes (P4). Está no §11.2 do `qa-report.md` do ciclo 012, com dono.
- **Os relatórios dos ciclos 010 e 011 deixaram de ter célula ambígua.** No 011, seis
  pré-condições de abertura estavam com `—`, que tanto pode dizer "não verificado" quanto
  "não cumprido": preenchidas, **cinco não foram cumpridas** — inclusive "ciclo 008
  promovido" e as cinco `[DÚVIDA]` do `## Clarify` —, e o ciclo foi executado assim mesmo.
  As duas linhas de matriz APH que o ciclo declarava tocar foram resolvidas (uma avançou,
  a outra continua fora do alvo). Os dois relatórios ganharam **achados numerados** (sete
  no 010, quatro no 011) e **pendências com dono** (sete no 011), e os quatro `TAIL:gate`
  continuam **em branco**.
- **Um defeito de prosa que o portão não pega, corrigido onde nasceu.**
  `scripts/tests/sabotagem/README.md` explicava a diferença entre as 67 sabotagens que o
  `grep` do registro conta e as **76** que a suíte declara dizendo que as do `check-i18n.sh`
  e do `check-documentacao.sh` "são escritas em forma de várias linhas". As duas metades
  estavam erradas: as nove que ficam de fora são **todas** do `check-i18n.sh`, são de uma
  linha só, e o motivo é o padrão `check-[a-z-]+\.sh`, que não casa o dígito de `i18n`.
  O `check-evidencia-colada.sh` continuou verde nos dois momentos — ele confere que o
  número bate com o comando, **não** que a prosa ao lado esteja certa, e o achado é a
  demonstração desse limite.
- **`docs/roadmap.md` passou a declarar o estado de cada ciclo no próprio cabeçalho** —
  `construção concluída`, `execução parcial`, `não executado` —, e o gerador do site lê
  esse estado em vez de uma lista fixa. A tabela nova "Onde o roadmap está, medido em
  2026-09-06" traz o estado com a origem de cada número ao lado: **11 de 12 ciclos** com
  trabalho executado, **0 promovidos** (a promoção é gate humano), 8 de 8 módulos com
  código, `1485 passed` no serviço, `307 passed (307)` na interface, 19 portões verdes,
  76 sabotagens reprovando pelo motivo certo e 11/11 na suíte de conformidade do Nível 1.
  O ciclo **002 nunca foi executado**, e agora isso está escrito no lugar onde se procura:
  o protótipo descartável não existiu, as telas nasceram direto na aplicação com jornada
  viva, e o `ux-design.md` que ele produziria não existe — que é a razão de o ciclo 010
  carregar `ART:ux-design=no` como dívida.

### Adição — M8: internacionalização com portão, documentação embutida, portabilidade e a restauração ENSAIADA (spec 011, ciclo 011)

- **O que este lote fecha, e o preço que a linhagem pagou por não ter feito.** Duas das
  **cinco** especificações de funcionalidade da quarta geração foram retrofit de
  internacionalização (`tocbuilderv3/specs/feat_internationalization_full.md` e
  `feat_internationalization_final_steps.md`, ambas de 2024-08-02) — e mesmo assim ela
  ficou com literais em português vivos no código de produção
  (`tocbuilderv3/components/SnTView.tsx:182`, `SnTStepEditorModal.tsx:92,95`) e com a
  **chave crua indo para a tela** quando a tradução faltava
  (`tocbuilderv3/i18n/I18nProvider.tsx:41`: `let result = translation || key;`). O que
  faltava não era disciplina: era portão.
- **`scripts/check-i18n.sh` — o portão de internacionalização** (RF-07, RF-08, RF-09).
  Três medidas numa: nenhuma cadeia visível fora do dicionário (varrida com o **próprio
  compilador do TypeScript**, nó de texto JSX e atributo visível — zero falso positivo por
  *generic*, zero falso negativo por atributo), paridade entre `pt` e `en` (chave sem
  tradução é pendência que reprova; chave só na tradução é erro), e a conferência de que
  o mecanismo **falha alto** em chave ausente. A lista de exceções exige **motivo escrito
  por linha**, e exceção que não corresponde a literal nenhum também derruba — a lacuna
  L-05 da spec diz por quê: "uma lista de exceções sem motivo é exatamente como um portão
  passa a mentir". Nove sabotagens declaradas.
- **A chave ausente deixou de virar texto de tela** (RF-09, RF-10). Em desenvolvimento e
  em teste, `traduzirCom` **lança** `ChaveDeTraducaoAusente` nomeando a chave e a tela; em
  produção, cai para a cadeia da língua-fonte e registra em log estruturado. A tradução de
  **código do servidor** (`tc`) continua tolerante, e a diferença é declarada: chave de
  tela é vocabulário fechado e tipado, código de servidor é vocabulário aberto.
- **O idioma efetivo virou função pura** (RF-12, RF-14): `preferência da pessoa → idioma do
  embarque → língua-fonte`, com o **motivo** da escolha junto e a queda para o padrão
  registrada. Na linhagem a mesma decisão lia `localStorage` por dentro do provedor
  (`I18nProvider.tsx:15`), e por isso a escolha morria com o dispositivo.
- **Documentação embutida com portão de cobertura** (E8.4). Sete verbetes — um por
  ferramenta registrada mais a jornada de focalização —, bilíngues onde há tradução e com
  **pendência declarada** onde não há (nunca uma tela vazia). O painel é lateral e não
  modal, abre **na âncora** do campo que pediu ajuda, devolve o foco ao fechar e carrega o
  corpo sob demanda. `scripts/check-documentacao.sh` deriva a lista de ferramentas do
  **registro do serviço** (`registrar_raiz_de_ferramenta`), e não de uma segunda lista:
  ferramenta nova sem verbete derruba o portão sem ninguém precisar lembrar. O precedente
  é `tocbuilderv3/components/DocsView.tsx:21-26` — quatro tópicos para seis ferramentas, e
  a frase `"Esta ferramenta ainda não foi implementada."` para as outras quatro. Seis
  sabotagens declaradas.
- **Exportação consolidada e ida e volta provada** (E1.4, RF-31, RF-32). Um projeto que
  atravessou ARA → NC → ARF → APR → AT sai num **arquivo único**, com seção por ferramenta
  e os vínculos entre elas, e volta criando **projetos novos** — sem tocar no que já
  existe (RN-05). A garantia não é disciplina: **todo identificador do documento é
  reescrito** antes de qualquer construção, o que mantém as referências internas
  consistentes e torna a colisão impossível. A ida e volta é medida contra o PostgreSQL
  real, e foi ela que encontrou um defeito de ordenação: o adaptador devolve os nós por
  `(criado_em, id)` e os cinco nós de uma Nuvem de Conflito nascem no mesmo instante — logo
  o desempate era por identificador, que muda na importação. A exportação passou a ordenar
  por **conteúdo**, com refinamento iterativo das chaves.
- **Adaptador do formato da quarta geração** (RF-25..RF-30), reconhecido por **assinatura
  de conteúdo** e nunca pelo nome do arquivo. Ele fecha os três defeitos medidos em
  `tocbuilderv3/components/NodeZoneView.tsx`: validação de três campos (`:314`), `alert()`
  genérico (`:315`) e o `chatHistory: data.chatHistory || []` que reintroduzia o diálogo
  com o modelo dentro do projeto criado (`:317`). Aqui o relato é **campo a campo** (dois
  problemas → dois itens, nada criado) e todo descarte é **declarado com contagem** —
  histórico de conversa, saída de modelo guardada no nó, identidade de origem.
- **A restauração deixou de ser hipótese** (F8.1.3, RF-01..RF-03). `scripts/ensaio-de-restauracao.sh`
  semeia uma base sintética por comando explícito, despeja, restaura **num banco novo**,
  compara tabela a tabela e por resumo `md5` do conteúdo, e **sobe a aplicação de verdade**
  (com a admissão do §B.4 completa) contra o destino restaurado. O procedimento, os
  objetivos de ponto e de tempo de recuperação e **o que não volta com o banco** estão em
  `docs/integracao/restauracao.md`. É a frase do Princípio XII da fundação executada:
  "backup é o que já foi restaurado com sucesso em outro lugar".
- **Números deste lote** (colados de execução, regra R1): a suíte do serviço saiu de
  `1394 passed` para `1485 passed` contra o PostgreSQL real (+91 testes) e a da interface
  de `280 passed (280)` para `307 passed (307)` (+27); os portões locais foram de 10 para
  **12** e as sabotagens de 61 para **76**. Desempenho da RNF-08 (teto de 5 s): converter
  200 nós e 200 arestas tem mediana de **2,3 ms** e percentil 95 entre **3,1 e 11,2 ms**
  em duas execuções de vinte repetições — a variação é da máquina, e está dita aqui em vez
  de escondida num número só; importar 200 nós e 199 arestas fica em **96,4 ms** de
  percentil 95. Cobertura do domínio novo (RNF-12, pede ≥ 85%): **87%**
  (`exportacao.py` 87%, `legado.py` 87%, `serializacao.py` 85%).
- **Carregamento sob demanda medido, não prometido** (RNF-09): `vite build` produz um
  pedaço por verbete (`ara-*.js` 5,34 kB, `nc-*.js` 4,86 kB, os outros cinco entre 1,65 e
  2,30 kB) fora do pacote inicial de 348,49 kB — abrir a documentação não engorda o
  primeiro carregamento em byte nenhum.

### Adição — M5: a árvore de **Estratégia & Táticas** volta (spec 010, ciclo 010)

- **O que este lote desfaz.** A árvore de Estratégia & Táticas (S&T) é a **única ferramenta
  que regrediu** na linhagem TOC-Builder: habilitada na 1ª geração
  (`TOC-Builder/components/Sidebar.tsx:44`, sem `disabled`) e na 2ª
  (`TOC-Builder-APP/components/Sidebar.tsx:44`), foi desligada na 3ª
  (`TOC-Builder-V2/components/Sidebar.tsx:56`) e na 4ª
  (`tocbuilderv3/components/Sidebar.tsx:58`), as duas com `disabled: true` e **sem uma
  linha de decisão registrada**. O modelo de dados ficou parado no código o tempo todo
  (`tocbuilderv3/types.ts:270-311`). Este ciclo desfaz a regressão — com a decisão
  registrada, que é o que faltou lá ([ADR 0014](docs/adr/0014-categoria-portada-e-transicao-de-status-livre-na-snt.md)).
- **Numeração derivada, nunca digitada** (RN-01). O número `1`/`1.1`/`1.1.2` é função pura
  da posição na árvore: não existe campo em formulário nenhum, não existe parâmetro em
  operação nenhuma, não existe coluna no banco e a exportação não o carrega. Na quarta
  geração ele era `stepNumber: string` obrigatório, texto livre, com o comentário
  `// Optionally, add validation for stepNumber format or uniqueness` logo abaixo
  (`tocbuilderv3/components/SnTStepEditorModal.tsx:56-57`) — e nenhuma das dez funções de
  serviço o conferia. A ausência do campo é **medida** no OpenAPI publicado, não prometida.
- **Renumeração local, com a propriedade que a torna confiável.** Inserir, mover e excluir
  renumeram só a subárvore afetada; um teste baseado em propriedade compara o resultado
  local com o recálculo total sobre **200 árvores geradas com semente fixa** e exige
  igualdade. Sem essa propriedade, a otimização seria uma segunda fonte de verdade — o
  defeito de que o módulo nasceu para se livrar.
- **As três premissas lógicas ganham papel** (RN-02). Os três campos existem desde a 1ª
  geração (`TOC-Builder/types.ts:243-245`) e a 4ª os oferecia em três áreas de texto
  empilhadas, sem contexto (`SnTStepEditorModal.tsx:137-159`). Aqui cada uma tem posição de
  leitura e **frase montada no servidor**: "Para alcançar `<1>` …, é necessário `<1.1>` …
  porque …" e "`<1.1.1>` e `<1.1.2>` bastam para `<1.1>` … porque …". Ausência é
  **pendência**, nunca trava de gravação (RN-06).
- **Árvore estrita, sem entidade de aresta** (RN-04). Pai único e ordem ordinal substituem
  o `edges: AraEdge[] // Reusing AraEdge for simplicity` da linhagem: multi-pai e ciclo
  ficam irrepresentáveis, e a única recusa necessária é mover um passo para dentro da
  própria subárvore.
- **A exclusão avisa quantos passos caem — e não toca no resto** (RN-05). O contraexemplo é
  o defeito de uma linha da quarta geração
  (`tocbuilderv3/services/mockApiService.ts:521`: `filter(n => n.id === nodeId)` mantinha
  **só** o nó excluído e descartava a árvore inteira). Ele entrou na suíte como caso de
  teste, comparando os passos de fora campo a campo antes e depois.
- **Status com autor e data** (RN-03): os quatro valores da linhagem, com transição livre
  entre eles e três recusas nomeadas (`sem_mudanca`, `autor_obrigatorio`, valor fora do
  vocabulário). O autor vem do principal da introspecção — o caso de uso **não tem**
  parâmetro `autor`, e um teste confere a assinatura.
- **Superfície completa**: domínio puro (`apps/api/src/toc_api/dominio/snt.py`), casos de uso
  (`apps/api/src/toc_api/aplicacao/snt.py`), migração `0009` com `downgrade`, adaptador SQL
  com a mesma trava otimista dos outros seis agregados, 13 rotas sob `/toc/snt`, quatro
  telas no registro do lado do serviço e da interface, e a tela React
  (`apps/web/src/telas/TelaDaSnT.tsx`) com árvore, ficha, vista tabular e painel de
  acompanhamento, em português e inglês.
- **Nenhuma ação de catálogo `toc.*`** nasce neste módulo (INT-04 da spec 010) — e a
  ausência é **provada**, não afirmada: `test_nenhuma_acao_do_catalogo_pertence_a_snt`.
- **Jornada viva J-011** — [`docs/jornadas/011-estrategia-e-taticas.md`](docs/jornadas/011-estrategia-e-taticas.md),
  com 12 capturas geradas do build real por script versionado, avaliação heurística datada e
  o desempenho da RNF-04 **medido** contra o serviço (abrir 100 passos em 5 níveis: p95 de
  10,7 ms; mover subárvore de 20 passos: 176,0 ms). A corrida completa de 2026-09-06, medida
  pelo `manifesto.json` que ela própria escreveu, levou o repositório a
  **81 capturas, 13 311 234 bytes, 0 falhas** — conferido por
  `scripts/check-evidencia-colada.sh`, que é o portão que impede este parágrafo de
  envelhecer em silêncio. **O tempo de parede não entra aqui**: ele muda a cada execução, e
  o manifesto não o grava.
- **TAIL:mutation**: `scripts/tests/mutacao-m5.sh` aplica 8 mutações às quatro funções cuja
  falha silenciosa reintroduziria os defeitos da linhagem e exige que a suíte fique
  vermelha em todas. A primeira execução encontrou **uma sobrevivente** — `renumerar`
  mantinha no mapa o número de passos já excluídos —, e o teste que faltava entrou junto.

### Correção — dois defeitos que a construção do M5 desenterrou

- **Projeto `snt` abria como Árvore da Realidade Atual.** `abrirFerramenta`
  (`apps/web/src/App.tsx`) caía no ramo genérico para toda ferramenta desconhecida, e o
  resultado era a tela da ARA recusando o projeto com `MUTATION_REFUSED`. Medido na bancada
  da jornada J-011, no build real — não em teste de unidade.
- **O portão `check-trava-otimista.sh` não conhecia o sétimo caminho de escrita.** Ele
  declara a lista à mão de propósito ("caminho de escrita novo entra AQUI no mesmo commit
  em que nasce"); `salvar_snt` entrou na lista junto com o adaptador, e o portão passou a
  conferir 9 de 9 caminhos em vez de 8 de 8.


### Adição — M4 ganha tela: as três árvores de futuro e a **cadeia** (spec 008, lado interface)

- **O buraco que este lote fecha.** O ciclo 008 escreveu o domínio da Árvore da Realidade
  Futura (ARF), da Árvore de Pré-Requisitos (APR), da Árvore de Transição (AT) e do
  encadeamento entre elas — e **nenhuma delas tinha interface**. Domínio sem tela é metade
  do trabalho: era exatamente a crítica que fazemos às quatro gerações do TOC-Builder, onde
  a ARF era um botão cinza (`tocbuilderv3/components/Sidebar.tsx:55`, `disabled: true`) e
  APR e AT nem botão tinham.
- **Quatro telas novas** — `TelaDaArf`, `TelaDaApr`, `TelaDaAt` e `TelaDaCadeia` —, cada uma
  com teste de fluxo feliz **e** de fluxo de erro, e as cinco entradas correspondentes no
  registro de telas (`toc.arf_canvas`, `toc.apr_canvas`, `toc.apr_sequencia`,
  `toc.at_canvas`, `toc.cadeia`). O registro do lado da interface estava **atrás** do
  manifesto publicado desde o ciclo 006: o serviço já declarava as cinco telas
  (`apps/api/src/toc_api/dominio/federacao/telas.py`) e a interface não, e o teste de paridade
  `registro.test.ts` estava vermelho por isso.
- **O ramo negativo tem superfície própria**, e não é mais um nó da lista. Ele ganha selo
  ("Efeito indevido"), moldura tracejada com faixa lateral, região dedicada com estado por
  extenso e as duas saídas lado a lado: **podar** (com a injeção que corta — e o seletor só
  oferece injeção, RN-04) ou **aceitar** (com justificativa obrigatória; o autor vem do
  principal, nunca do corpo). É o que separa uma árvore de futuro séria de uma lista de
  desejos, e agora aparece na tela como tal.
- **A cadeia** (`/toc/cadeia`) mostra o percurso completo numa tela só — Efeito Indesejável
  → conflito → injeção → árvore de futuro → obstáculos → transição —, com cada costura
  nomeada por extenso, as duas pontas navegáveis e o **elo pendente à vista** (RF-35): o
  vínculo que perdeu uma ponta não é escondido, porque é ele que a pessoa precisa
  consertar.
- **Internacionalização de nascença**: português e inglês para os quatro espaços de nome
  novos (`arf`, `apr`, `at`, `cadeia`) e para os sete vocabulários fechados que o servidor
  publica (`papel_na_arf`, `estado_do_ramo`, `papel_na_apr`, `status_do_passo`,
  `tipo_de_referencia`, `estado_da_referencia`, `aviso_de_verbalizacao`). O teste de
  paridade das tabelas continua verde.
- **Jornada viva J-10** — [`docs/jornadas/010-as-tres-arvores-e-a-cadeia.md`](docs/jornadas/010-as-tres-arvores-e-a-cadeia.md),
  com capturas geradas do build real pelo script versionado e avaliação heurística datada.

### Correção — três defeitos que a construção da interface do M4 desenterrou

- **Não havia rota para mover um nó da ARF nem da APR.** Os casos de uso `MoverNoDaARF` e
  `MoverNoDaAPR` existiam desde o ciclo 008 e estavam **importados pelo roteador sem
  nenhuma rota que os chamasse**: o canvas oferecia o gesto de arrastar e o gesto não tinha
  onde gravar. `PATCH /toc/{arf,apr}/projetos/{id}/nos/{no}` passa a aceitar `posicao`,
  pela raiz do agregado (a rota genérica do M1 recusa com `AGGREGATE_ROOT_REQUIRED`), e o
  `PATCH` sem campo algum é **recusa** e não sucesso vazio.
- **Duas classes de esquema com o mesmo nome no mesmo módulo.** `PendenciaOut` foi definida
  para a pendência de um passo da jornada de focalização (M6) e **de novo** para a
  pendência do plano de Estratégia & Táticas (M5); a segunda apagava a primeira, e a
  jornada inteira do M6 caía em tempo de resposta com "6 validation errors for
  PendenciaOut". A do M5 passa a chamar-se `PendenciaDoPlanoOut`; a segunda `LigarIn`, que
  era cópia exata da primeira, deixou de existir.
- **Um nome importado duas vezes em `erros.py` escondia uma classe de exceção inteira.**
  `TransicaoDeStatusRecusada` era importada de `dominio.ara` **e** de `dominio.snt`, e
  `@app.exception_handler(...)` registrava a mesma classe duas vezes: a recusa da Árvore da
  Realidade Atual perdia o `details.motivo` e chegava ao cliente como `MUTATION_REFUSED`
  seco. Os dois nomes ganharam apelido (`TransicaoDeStatusDaAra`, `TransicaoDeStatusDaSnT`).
- **Duas funções de aptidão novas** (`apps/api/tests/contrato/test_portas.py`) impedem a volta das
  duas últimas: nenhum esquema HTTP com nome repetido, nenhum nome importado duas vezes em
  `erros.py`. As três correções somadas devolvem a suíte inteira ao verde.


### Adição — M6: a jornada dos cinco passos de focalização, e a primeira vez que a aplicação diz **qual é a restrição** (spec 009)

- **O buraco que este módulo fecha.** Até aqui a aplicação sabia desenhar as ferramentas
  da Teoria das Restrições (TOC) e não sabia nomear o gargalo que elas existem para
  atacar. A `Restricao` nasce neste ciclo como entidade de domínio, com tipo, justificativa
  obrigatória e referência tipada de origem (o nó de causa raiz de uma Árvore da Realidade
  Atual — ARA).
- **A jornada (E6.1 + E6.2)** — `AnaliseDeFocalizacao` é agregado próprio, **composto**
  sobre o `Projeto` do M1: herda dono por inquilino, exclusão suave e a trava otimista por
  versão lida, e não usa grafo (uma jornada não é um diagrama). Uma análise nasce com o
  ciclo 1 aberto e os **cinco passos instanciados** — `identificar` → `explorar` →
  `subordinar` → `elevar` → `recomecar` —, e não há rota para criar, excluir ou reordenar
  passo: a ausência é o contrato.
- **A anti-inércia de Goldratt, como regra executável.** Recomeçar fecha o ciclo (imutável
  a partir dali), abre o próximo em `identificar` e herda as decisões vigentes de
  `explorar` e `subordinar` com veredito `pendente`. Concluir `subordinar` com herança
  pendente é **recusado**. E uma decisão julgada `mantida` **volta à mesa no recomeço
  seguinte**: um passe vitalício concedido por um único "manter" é inércia com carimbo.
  Decisão registrada no
  [ADR 0013](docs/adr/0013-taxonomia-fechada-da-restricao-e-heranca-que-volta-a-mesa.md).
- **Reabrir não apaga.** As decisões de um passo são tupla somente-acréscimo e a reabertura
  é fato registrado ao lado, nunca no lugar. A prova não é contagem: `CicloDeFocalizacao.retrato()`
  produz o conteúdo que as pessoas escreveram, e o teste compara o retrato do ciclo fechado
  antes e depois do recomeço.
- **Vínculos combinados pela porta, não pela implementação.** O vínculo é referência tipada
  a um projeto de outro módulo (ARA, Nuvem de Conflito, Árvore da Realidade Futura, Árvore
  de Pré-Requisitos, Árvore de Transição) — **nunca cópia**. O domínio conhece só a tabela
  canônica (fora dela exige justificativa e avisa, não bloqueia); existência, inquilino,
  ferramenta real e estado do alvo são conferidos no servidor, contra a porta. É o que
  permite a suíte de domínio do M6 rodar offline. A navegação de volta
  (`GET /toc/focalizacao/ferramentas/{id}/analises`) resolve por consulta, **sem campo novo
  em M2, M3 ou M4**.
- **Superfície e governança** — 15 caminhos (18 pares verbo + caminho) sob `/toc/focalizacao`; cinco códigos estáveis
  novos no registro do §A.7 (`INVALID_FOCUSING_STEP`, `INVALID_CYCLE`,
  `INVALID_CONSTRAINT`, `INVALID_TOOL_LINK`, `INVALID_INHERITED_DECISION`), todos com a
  regra nomeada em `detalhes.regra`; a ação governada `toc.suggest_constraint` (risco
  `confirm`, nasce proposta — a rota de leitura que a precede **não escreve nada**); três
  telas no registro com `ai_visible` campo a campo; migração Alembic `0008` com
  `downgrade`, levando as invariantes ao banco (índice parcial único para "um ciclo
  aberto", chave primária no ciclo para "uma restrição", `CHECK` para justificativa
  obrigatória fora do canônico e para veredito com autor).
- **Interface e jornada viva** — mapa dos cinco passos com estado **nunca só por cor**,
  painel do passo em três camadas (herdado → trabalho → decisão), julgamento de herança com
  dois vereditos de peso visual **igual**, linha do tempo somente leitura e listagem com
  passo atual e restrição como colunas de primeira classe. Jornada
  [`docs/jornadas/009-cinco-passos-de-focalizacao.md`](docs/jornadas/009-cinco-passos-de-focalizacao.md),
  com captura por passo gerada pelo script versionado a partir do build real. A corrida de
  2026-09-06 que a produziu, medida pelo `manifesto.json` que ela própria escreveu, levou o
  repositório a **69 capturas,
  10 599 868 bytes, 0 falhas** (`find docs/jornadas/capturas -name '*.png' | wc -l` → `69`,
  conferido pelo portão `scripts/check-evidencia-colada.sh`; o número cresceu com a J-10,
  que entrou depois — o portão é justamente o que impede este parágrafo de envelhecer em
  silêncio). **O tempo de parede não entra
  aqui**: ele muda a cada execução, e o manifesto não o grava.
- **Portões** — `scripts/check-trava-otimista.sh` passou a conhecer **oito** caminhos de
  escrita e `scripts/check-trava-da-proposta.sh` **nove** métodos `salvar*` (entrou
  `salvar_focalizacao`, nas duas listas **e** nas duas fixtures de sabotagem);
  `scripts/check-raiz-do-agregado.sh` conta agora **seis** raízes de ferramenta registradas;
  o catálogo servido tem **16 ações** e **12 telas**. Fechamento: `scripts/evidencia.sh`
  saiu `0` com **17 portões, 17 verdes, 0 vermelhos**, e `scripts/tests/run-sabotagem.sh`
  saiu `0` com **10 portões cobertos, 61 sabotagens, 61 reprovadas pelo motivo certo**.

### Correção — o painel do passo guardava a ferramenta canônica do passo em que foi montado

- Navegar de `identificar` para `subordinar` deixava "vincular ferramenta" desabilitado sem
  motivo aparente: o `<select>` mantinha o valor canônico do passo anterior. **Nenhum teste
  de unidade pegou** — cada um monta o painel uma vez —, e quem pegou foi a captura da
  jornada viva contra o build real, que é literalmente o argumento do princípio P6.
  Corrigido com `key={passo.tipo}` no `PainelDoPasso`, o que também limpa os rascunhos de
  nota e de decisão ao trocar de passo.

### Adição — M4: as três árvores que a linhagem nunca entregou, e o encadeamento que faltava (spec 008)

- **O que a linhagem tinha, medido:** nas quatro gerações do TOC-Builder, a Árvore da
  Realidade Futura (ARF), a Árvore de Pré-Requisitos (APR) e a Árvore de Transição (AT)
  eram **item de menu desabilitado** — `tocbuilderv3/components/Sidebar.tsx:55-57`,
  `types.ts:249-258` — com zero componentes, zero prompts e zero linhas de domínio. E a
  referência entre projetos nunca existiu:

  ```text
  $ grep -c "araProjectId\|sourceUdeId\|linkedProject\|crossTool" /home/user/tocbuilderv3/types.ts
  0
  ```

- **ARF (E4.1)** — papéis tipados (injeção · efeito futuro), arestas de suficiência com
  exame e conector E, espelho Efeito Indesejável (UDE) → Efeito Desejável com no máximo um
  por UDE, **ramo negativo** com `aberto → tratado | aceito` (tratar exige a injeção que
  corta; aceitar exige justificativa e autor) e verificação estrutural por função pura.
- **APR (E4.2)** — objetivo único e indestrutível, obstáculos e objetivos intermediários,
  **lógica de condição necessária** ("A precisa existir antes de B") sem exame de elo,
  pareamento obstáculo ↔ objetivo com julgamento acumulável, elipse de simultaneidade,
  sequenciamento em camadas com ciclo como pendência **bloqueante**, tabela resumo, e a
  verbalização avaliada offline sobre corpus versionado — que **avisa e não veta**.
- **AT (E4.3)** — passo com a tripla obrigatória (ação · necessidade · resultado
  esperado), precedência, status com motivo de bloqueio e resultado real; a divergência
  entre esperado e real fica no evento e **não** sobrescreve o esperado.
- **Encadeamento (E4.4)** — promover UDE `Validado` → Nuvem de Conflito (NC), semear
  injeção `escolhida` → ARF, derivar ARF → APR e objetivo intermediário → AT, cada um
  criando uma `ReferenciaCruzada` tipada; a cadeia inteira é percorrível nos dois sentidos
  e o elo com ponta excluída aparece `pendente`, nunca some.
- **Superfície e governança** — `/toc/arf`, `/toc/apr`, `/toc/at` e `/toc/cadeia`; nove
  códigos próprios novos no registro do §A.7; quatro ações `toc.suggest_*` que **executam
  neste ciclo** pela máquina de estados do servidor, cinco telas no registro, migração
  Alembic `0006` com `downgrade`, e a decisão registrada no
  [ADR 0012](docs/adr/0012-modulo-m4-suficiencia-compartilhada-e-referencia-como-agregado.md).
- **Portões** — `scripts/check-trava-otimista.sh` passou a conhecer **sete** caminhos de
  escrita e **dois** gravadores (o projeto e a referência cruzada, que é agregado próprio
  com versão própria); `scripts/check-raiz-do-agregado.sh` conta **cinco** raízes de
  ferramenta registradas.

### Correção — o gate humano multiplicado por uma corrida: a proposta de ação era o único agregado sem trava (achado de crítico hostil que o reproduziu)

- **Uma aprovação humana executava N vezes.** A trava otimista do achado anterior fechou o
  agregado **Projeto** e deixou a **proposta de ação** de fora — quem a instalou declarou a
  lacuna como pendência, e o ataque confirmou que a pendência era real. Reproduzido aqui,
  contra o PostgreSQL real, **antes de qualquer linha de conserto**
  (`apps/api/tests/integracao/test_corrida_de_confirmacao_no_postgres.py`):

  ```text
  corrida de confirmação · chave única · códigos {200: 8} · nós no banco 50 para 30 pedidos
    · títulos repetidos 22 · linhas de traço 8 · linha no banco: estado=failed execucoes=1
  corrida de confirmação · sem chave · códigos {200: 8} · nós no banco 49 · linhas de traço 8
  corrida de recusa · códigos {200: 8} · nós no banco 0
    · linhas de traço ['denied', 'denied', 'denied', 'denied', 'denied']
  ```

- **Diagnóstico antes do conserto — por que a máquina de estados finitos (FSM) não
  impediu.** Ela guardava o **objeto**, não a linha: `obter` reidrata um `PropostaDeAcao`
  novo a cada chamada e `transicionar` consulta um atributo de memória, então oito
  confirmações atravessavam oito agregados e as oito transições eram legítimas. E a
  gravação era um `ON CONFLICT DO UPDATE` **incondicional** que rodava **depois** do
  efeito — a prova está na própria linha depois do ataque: `estado=failed execucoes=1`
  depois de oito execuções, porque o último a gravar escreveu o retrato dele por cima.
  A transição `confirmed → executing` **é** a serialização natural do APH-5.1 (Padrão APH
  — Aplicação ↔ Harness), mas só quando existe **no banco e antes do efeito**.

- **Conserto na causa.** `PropostaDeAcao.estado_lido` + `confirmar_gravacao()` (o mesmo
  desenho de `Projeto.versao_lida`); `UPDATE … WHERE estado = :estado_lido` no adaptador,
  com `rowcount == 0` levantando `CorridaDeDecisao`; e — a peça central — a **reserva
  acontece antes do efeito** (`_reservar`, entre a transição e a primeira chamada ao
  executor): quem não escreve, não executa. Recusar também reserva, porque recusar também
  é decidir. Medido depois: `códigos {200: 8} · nós no banco 30 para 30 pedidos · títulos
  repetidos 0 · linhas de traço 1 · estado=executed execucoes=1`, estável em três corridas.

- **A `idempotency_key` passou a deduplicar de verdade (APH-5.3).** Ela existia desde a
  migração 0004, era gravada em toda confirmação e **lida em lugar nenhum** — o único
  leitor era um teste de domínio. Agora há índice único parcial por
  `(tenant_id, idempotency_key)` (migração **0007**) e a aplicação consulta a chave: a
  segunda confirmação devolve o **mesmo** resultado da primeira, sem reexecutar e sem novo
  traço, esperando quem venceu se ainda estiver executando. Sem chave, o perdedor recebe
  `409 INVALID_TRANSITION` — a verdade da FSM, e o que faz a chave significar alguma coisa.
  Código próprio novo, documentado no registro único do §A.7: `IDEMPOTENCY_KEY_REUSED`.

- **A CLASSE, e não o caso.** Os seis caminhos de escrita persistente dos dois adaptadores
  foram classificados um a um (`retrato` · `acréscimo` · `identidade`); o duplo em memória
  ganhou a mesma trava **e passou a devolver cópia** — ele entregava o objeto guardado, o
  que tornava a corrida invisível para a suíte de contrato inteira —; e
  `RepositorioDePropostasFalso` dos testes passou a **herdar** o duplo de produção, para
  não haver uma terceira permissividade.

- **Achado de tabela: a metade cliente do conserto anterior faltava.** O teste de paridade
  novo (`apps/web/src/i18n/i18n.test.tsx`) nasceu vermelho sobre `VERSION_CONFLICT`: o
  código estava em `apps/web/src/api/erros.ts` desde o ADR 0010 e **não tinha texto em
  nenhum dos dois idiomas**, então quem perdia a corrida de escrita lia "o serviço recusou
  a operação" — o genérico. Era o "perder sem saber" que aquele ADR se propôs a acabar,
  vivo do lado da tela. Texto acrescentado em `pt` e `en`, e a paridade agora é aptidão:
  todo código de `CODIGOS` tem de ter texto nos dois dicionários.

- **Portão novo — `scripts/check-trava-da-proposta.sh`** (26 verificações em 7 arquivos, 10 caminhos de escrita persistente classificados),
  com **10 sabotagens** próprias. A mais importante não olha texto e sim **ordem de
  linhas**: mover a reserva para depois do efeito deixa a trava inteira no lugar e inútil,
  e nenhuma varredura de presença veria isso. Entrou no agregador `scripts/evidencia.sh`.
  Decisão em **ADR 0011**.


### Correção — saída colada que envelheceu, e o portão que passa a reprová-la (achados de revisão independente)

- **Três achados, os três de evidência e nenhum de código.** Num repositório cuja regra R1
  diz *"nunca transcreva um `✓`: copie a linha que o script imprimiu"*, evidência que
  envelheceu é defeito de primeira classe: o bloco tem cifrão, tem bloco de código, tem
  cara de prova — e afirma o que o comando já não devolve.

  1. `apps/api/README.md` colava `40 passed, 786 deselected, 2 warnings in 35.29s`; o mesmo
     comando devolveu `42 passed, 797 deselected` às 02:47Z e `48 passed, 806 deselected`
     às 02:59Z do mesmo dia, porque a suíte cresce enquanto o serviço é construído.
  2. O CHANGELOG anunciava **33 capturas** e existem **36**
     (`find docs/jornadas/capturas -name '*.png' | wc -l` → `36`). A mensagem de commit que
     disse "33 telas" é história e não se reescreve; este arquivo e as jornadas podem, e
     agora trazem o número certo com o comando ao lado.
  3. A cauda do ciclo 012 estava vazia enquanto o trabalho existia — corrigido em
     `specs/012-jornadas-e-autodeclaracao/qa-report.md`.

- **A varredura que o achado 1 obrigou encontrou 15 afirmações envelhecidas em 5 arquivos**,
  e a mais instrutiva não era um número errado: quatro buscas de `docs/produto/visao.md`
  colavam `0` e devolviam `122`, `212`, `33` e `53` porque as dependências de `tocbuilderv3`
  passaram a existir na máquina e as buscas não passavam `--exclude-dir=node_modules`. A
  **afirmação** continuava certa e o **comando** tinha deixado de ser a testemunha dela —
  o caso mais traiçoeiro, porque não parece defeito. Também recolados:
  `docs/jornadas/README.md` (contagens de captura, achados e conformes),
  `docs/jornadas/002-primeiro-projeto-e-ara.md` (medida do canvas, que era de outra
  corrida), `tools/product-site/README.md` (com o site regerado junto) e
  `scripts/tests/sabotagem/README.md` (`27` mutações quando a suíte tem 48).

- **Portão novo — `scripts/check-evidencia-colada.sh`**, com registro em
  `scripts/evidencia-colada.json`: cada afirmação declara o **comando** que a produz e o
  **molde** literal em que o valor está colado; o portão re-executa e reprova quando os dois
  divergem. Ele nasceu **vermelho** sobre as 15 afirmações do repositório e ficou verde só
  depois das correções — o teste que reproduz o defeito veio antes da correção (P4). Entrou
  no agregador `scripts/evidencia.sh` e ganhou **cinco sabotagens** que o derrubam pelo
  motivo declarado, inclusive as três formas de o desligar por dentro (registro sem
  documento de destino, molde que casaria com qualquer valor, documento citado inexistente).
  **Limite declarado no cabeçalho do portão**: ele confere o que o registro declara, e
  saída cara ou instável — uma suíte inteira, um tempo em segundos, um identificador
  sorteado a cada corrida — fica de fora de propósito, com a volatilidade **dita ao lado**
  da saída no documento.

- **`docs/integracao/aderencia-aph.md` ganhou ressalva datada**: o parágrafo "Estado
  honesto" de 2026-09-03 dizia *"nada foi implementado"* enquanto a suíte do Nível 1 do
  `GHDaru/protocolos` fecha **11/11 verificados** contra o serviço. A matriz **não** foi
  preenchida (é a tarefa T-07 do ciclo 012, declarada como dívida com dono no
  `qa-report.md`): encobrir o atraso trocaria um defeito de honestidade por outro.

### Correção — perda de atualização silenciosa entre duas pessoas na mesma análise (achado de revisão independente)

- **Vinte escritas concorrentes de nó respondiam vinte vezes `201 Created` e persistiam
  UM nó.** `RepositorioDeProjetosSQL` gravava o **retrato** do agregado que estava em
  memória, e a reconciliação apagava do banco toda linha fora desse retrato
  (`delete(… id.notin_(ids))`). Com dois retratos, o segundo apaga o trabalho do primeiro
  — sem exceção, sem código de erro, sem aviso. Numa ferramenta de facilitação em grupo,
  que é o que esta aplicação se propõe a ser, é o pior desfecho possível.

  **Causa raiz, em duas metades** (por isso "acrescentar um `WHERE`" não bastava): a
  escrita era incondicional (`WHERE id AND tenant_id` casa sempre) **e** o agregado não
  guardava de que versão tinha partido — `versao` é incrementada em memória a cada
  mutação, então na hora de gravar já não era mais o número contra o qual comparar. A
  coluna existia, era incrementada, e o teste de domínio que a cobria passava chamando-a
  de "bloqueio otimista": era um contador, não uma trava.

  **Medido antes do conserto**, contra o PostgreSQL real: `escritas aceitas: 20 · nós no
  banco depois: 1 · TRABALHO PERDIDO EM SILÊNCIO: 19 nó(s)`.

  **Conserto** (decisão em [ADR 0010](docs/adr/0010-trava-otimista-por-versao-lida.md)):
  - **domínio**: `Projeto.versao_lida` guarda a versão que veio do banco e
    `Projeto.confirmar_gravacao()` a sincroniza depois do commit
    (`apps/api/src/toc_api/dominio/projeto.py`); a recusa é o erro tipado
    `ConflitoDeVersao`, com os dois números (`apps/api/src/toc_api/dominio/erros.py`);
  - **adaptador**: `UPDATE … WHERE versao = :versao_lida`, `rowcount == 0` relê a versão
    atual e levanta a recusa, e a transação inteira volta atrás
    (`apps/api/src/toc_api/infra/persistencia/repositorio_projetos.py`). Fecha a
    **classe**: as três portas de escrita — `salvar` (M1, Núcleo de Diagramas Lógicos),
    `salvar_ara` (M2, Árvore da Realidade Atual) e `salvar_nuvem` (M3, Nuvem de Conflito)
    — gravam pelo mesmo `_gravar_projeto` e nenhuma alcança as reconciliações sem passar
    por ele. O duplo em memória recebeu a mesma trava, senão a suíte de contrato ficaria
    verde sobre o que o banco recusa;
  - **borda**: `409` com `VERSION_CONFLICT` e `details: {agregado, versao_lida,
    versao_atual}` — código próprio **declarado** no registro único do §A.7 do Anexo A do
    Padrão APH (Aplicação ↔ Harness), porque nenhum código do registro mínimo nomeia duas
    escritas concorrentes sobre o mesmo agregado. Quem perde a corrida agora **sabe** que
    perdeu, e recebe o número com que recarrega e refaz;
  - **interface**: `apps/web/src/api/erros.ts` passa a discriminar o código novo.

  **Portão novo, com sabotagem própria**: `scripts/check-trava-otimista.sh` (registrado em
  `scripts/evidencia.sh`) confere as seis peças da correção, e
  `scripts/tests/run-sabotagem.sh` ganhou 8 mutações que provam que ele reprova quando
  qualquer uma delas é removida.

  **Depois do conserto**: `concorrência M1: 20 escritas · aceitas 1 · recusadas 19 · nós
  no banco 1` — e as aceitas são exatamente as persistidas, que é o invariante que faltava.

### Correção — o laço da assistência não fechava na tela (achado de revisão independente)

- **A pré-visualização da geração assistida era um beco sem saída.** Ela mostrava o diff
  inteiro do que a geração propunha e oferecia **um** botão: "Recusar". Não existia, em
  lugar nenhum da aplicação, caminho para a pessoa **aceitar** a proposta e ver a Nuvem de
  Conflito (NC) mudar — a funcionalidade mais vistosa do produto não concluía. A ausência
  estava documentada no próprio componente (*"a escrita é da proposta que atravessa a
  máquina de estados no servidor"*) e a documentação da ausência **é a descrição do
  buraco**, não o conserto dele. A avaliação heurística datada da jornada J-03 já
  registrava o mesmo achado (A-03), aberto desde então.

  **Causa raiz**: o servidor tinha a ação governada, a máquina de estados, a política, o
  traço e o executor — e as duas portas de proposta que existiam servem o **hospedeiro**
  (o fio do §A.6, dentro de uma sessão de conversa, e a borda `POST /aph/actions/{id}`,
  que devolve `{"result": <frase>}` por contrato dele). Faltava a porta do **terceiro
  consumidor**: a interface da própria aplicação, que precisa do `proposal_id` em dado
  estruturado — extraí-lo da frase seria o cliente discriminando por mensagem, o que o
  §A.7 do Anexo A proíbe.

  **Conserto** (pelo caminho que a spec 006 e o Padrão APH — Aplicação ↔ Harness — mandam,
  decisão em [ADR 0009](docs/adr/0009-superficie-de-proposta-para-a-interface-da-aplicacao.md)):
  - **serviço**: `POST /toc/propostas` (a proposta nasce e **espera**) e
    `POST /toc/propostas/{proposal_id}/decisao` (o gate humano), em
    `apps/api/src/toc_api/http/roteadores/propostas.py`, montadas sobre os **mesmos**
    `ProporAcao` e `DecidirProposta` — mesma FSM (máquina de estados finitos), mesma
    política verificada no caso de uso, mesmo registro de erros, mesmo traço. Nenhum
    segundo caminho de escrita: a rota não toca repositório;
  - **interface**: "Aceitar" na prévia leva a proposta ao gate, e a superfície de
    confirmação `proposta-de-acao`
    (`apps/web/src/componentes/federacao/SuperficieDeConfirmacao.tsx`, RI-01 da spec 006)
    confirma ou recusa — com os dois botões de mesmo peso, foco no resumo ao abrir e
    desfecho anunciado por `aria-live`. Depois da decisão a nuvem é **relida do serviço**;
    a tela não escreve nada.

  **Evidência do build real** (`docs/jornadas/scripts/capturar-telas.mjs`, capturas 08 a 10
  da J-03):

  ```text
    · proposta criada e aguardando decisão · nuvem intacta enquanto espera: true · linhas de traço antes da decisão: 0
    · confirmada: 2 de 5 entidades reescritas · premissas 7 → 14 · traço da ação: ["executed"]
  ```

- **Prova de persistência, com PostgreSQL real e três aplicações diferentes**
  (`apps/api/tests/integracao/test_propostas_no_postgres.py`): propor numa, confirmar
  noutra, ler numa terceira. Se a proposta vivesse em memória, a segunda não a encontraria;
  se a escrita fosse estado de tela, a terceira não a veria.

- **Dois achados de interface fechados junto** (jornada J-03): a prévia e a superfície de
  confirmação passaram a `min(880px, 100%)` — as duas são leitura para decidir, não
  formulário lateral (A-02) —, e a superfície não anuncia mais "itens afetados: 0" numa
  ação que não é lote (0 alvos é ausência, não quantidade).

- **Dois defeitos do gerador de capturas, achados ao regenerar**: ele semeava as arestas da
  Árvore da Realidade Atual (ARA) pela rota genérica do M1, que passou a responder
  `409 AGGREGATE_ROOT_REQUIRED` desde a correção da porta dos fundos do agregado (a jornada
  J-02 não regenerava mais); e apagava **todas** as capturas mesmo com `--jornada`, o que
  levava junto as das jornadas que aquela corrida não geraria.

### Correção — o agregado com porta dos fundos (achado de revisão independente, reproduzido)

- **A raiz do agregado deixou de ser o único caminho para o estado dela, e voltou a ser.**
  As ferramentas M2 (Árvore da Realidade Atual — ARA) e M3 (Nuvem de Conflito — NC) são
  raízes por composição: `ProjetoARA` e `NuvemDeConflito` contêm um `Projeto` do M1 (Núcleo
  de Diagramas Lógicos) e acrescentam as invariantes da ferramenta. O `Projeto` contido é a
  **mesma linha de banco** que as rotas genéricas de `/toc/projetos` abrem, e essas rotas o
  carregavam cru: duas portas para o mesmo estado, invariantes numa só.

  **Reprodução, colada da execução antes do conserto** (`POST /toc/nc/projetos`, depois a
  rota genérica sobre a aresta D↯D′):

  ```text
  nasceu: 5 entidades, 7 arestas
  DELETE aresta D_D_PRIME pela rota generica -> 204
  GET /toc/nc/projetos/{id} depois -> 404 {"error":{"code":"NOT_FOUND","message":"recurso não encontrado"}}
  DELETE entidade A pela rota generica -> 200 {"no_id":"…","arestas_removidas":["…","…"]}
  ```

  A nuvem **sumia da leitura** — `404` sobre um projeto que continuava no banco — e a
  resposta da mutilação era `204 No Content`.

  **Causa raiz**: a fronteira do agregado estava escrita em prosa e numa classe
  invólucra, não no objeto que guarda o estado. `Projeto.ferramenta` era um rótulo de
  filtro, então qualquer um que obtivesse um `Projeto` mutava o grafo da ferramenta.

  **Conserto** (mata a classe, não o caso): `Projeto._exigir_raiz` recusa as **oito**
  mutações de grafo (`adicionar_no`, `editar_no`, `mover_no`, `recolher_no`, `excluir_no`,
  `ligar`, `editar_aresta`, `excluir_aresta`) quando a `ferramenta` não é a genérica, e a
  única destrava é `Projeto.sob_a_raiz()`, usada por dentro das raízes. **Fail-closed por
  construção**: ferramenta nova nasce bloqueada mesmo sem se registrar. Erro novo
  `MutacaoForaDaRaiz` → `409 AGGREGATE_ROOT_REQUIRED` com `details.ferramenta` e
  `details.raiz` (registro do §A.7 em `apps/api/src/toc_api/dominio/federacao/wire.py`; mensagem de tela em
  `apps/web/src/i18n/pt.ts` e `en.ts`).

- **A mesma exposição, nas outras invariantes — procuradas, achadas e testadas.** Não era
  só a RN-01 da nuvem:
  - a **terceira porta**, que fechar as rotas teria deixado aberta: o executor do catálogo
    federado (`apps/api/src/toc_api/infra/federacao/executor.py`) monta os mesmos casos de uso genéricos para
    `toc.criar_nos`, `toc.criar_arestas`, `toc.atualizar_no` e `toc.excluir_nos`. Uma ação
    governada, aprovada por gate humano, mutilaria a nuvem igual. Recusa medida em
    `apps/api/tests/federacao/test_porta_dos_fundos_do_catalogo.py`;
  - **elo da ARA sem exame de suficiência** (RF-22): `ProjetoARA.ligar` cria o `Exame`;
    `Projeto.ligar` não sabe que exame existe — e a ARA **não tinha rota de aresta**, então
    a própria tela do produto ligava pela rota genérica;
  - **UDE órfão** (RF-05): pela rota genérica o nó sumia e a ficha ficava pendurada num
    identificador que não existe mais, sem `UdeArquivado`;
  - **conector E com aresta fantasma** (RN-11): `_soltar_das_conjuncoes` só rodava dentro de
    `excluir_no`; **não havia** `ProjetoARA.excluir_aresta`, e o produto apagava pela rota
    genérica deixando o conector apontando para o vazio. A operação passou a existir;
  - **UDE reescrito sem revalidar** (RF-10): `PATCH` genérico trocava o texto e o veredito
    formal anterior ficava pendurado. `ProjetoARA.editar_no` agora revalida no mesmo ato.

- **Adicionado — o grafo da ARA pela raiz.** Oito casos de uso (`AdicionarEfeito`,
  `EditarNoDaARA`, `MoverNoDaARA`, `RecolherNoDaARA`, `ExcluirNoDaARA`, `LigarNaARA`,
  `EditarArestaDaARA`, `ExcluirArestaDaARA`), todos na `POLITICA` de capacidades, e as
  rotas `POST/PATCH/DELETE /toc/ara/projetos/{id}/nos|arestas`. A rota
  `POST /toc/ara/projetos/{id}/efeitos` deixou de rodar o `AdicionarNo` genérico: dava o
  mesmo nó e era a ferramenta indo ao núcleo por fora da própria raiz. O cliente web
  (`apps/web/src/api/cliente.ts`) e a tela da ARA passaram a usá-las.

- **Adicionado — portão `scripts/check-raiz-do-agregado.sh`**, no `scripts/evidencia.sh` e
  na suíte de sabotagem com três mutações (chave vazando para a aplicação, mutação sem
  guarda, ferramenta que não se registra). Existe porque o `import-linter` mede **direção**
  de import e `aplicacao → dominio` é o sentido permitido: ele não veria uma camada de fora
  pegar a chave do núcleo.

### Correção — três achados de revisão independente que executou

- **`done` depois de `error` no fio (§A.1 do Anexo A)** — `apps/api/src/toc_api/http/aph.py`.
  `_acrescentar_ao_log` emitia o terminador `done` **incondicionalmente** depois do evento.
  Quando o evento é `error`, que já é terminador, o turno tentava encerrar duas vezes; o
  domínio recusava a segunda (`SessaoEncerrada`) e a recusa subia até a borda. **Efeito
  medido**: quem confirmava uma proposta com a tela desatualizada recebia
  `409 DOMAIN_REFUSED` com a mensagem interna `"sessão …: o turno já terminou em 'error'"`
  em vez do `PROPOSAL_CONTEXT_STALE` que o §A.7 nomeia — defeito de protocolo e vazamento
  de mensagem interna no mesmo `done`. Agora o terminador é condicional, e os eventos de
  uma decisão entram num turno só (um `done`, não um por evento). Testes que reproduzem
  antes do conserto: `test_acrescentar_ao_log_nao_tenta_um_segundo_terminador`,
  `test_decisao_com_contexto_divergente_devolve_o_codigo_do_a7`,
  `test_o_error_da_recusa_encerra_o_turno_sozinho_sem_done_atras` e
  `test_a_decisao_acrescenta_um_terminador_so_ao_log`.
- **Duas grafias do mesmo código de erro no mesmo serviço** — a borda REST emitia
  `INVALID_ARGUMENT` (`apps/api/src/toc_api/http/erros.py`) e a borda APH emitia
  `INVALID_ARGUMENTS` (`apps/api/src/toc_api/http/aph.py`) para a mesma situação. O §A.7 diz que "o cliente discrimina por código e
  nunca por mensagem": quem comparasse por igualdade trataria um e ignoraria o outro — e o
  cliente web já discriminava só o singular (`apps/web/src/api/erros.ts`). **Causa raiz**:
  eram **dois registros declarados**, um por borda, e nada comparava os dois; além disso
  o tradutor REST montava o envelope à mão, sem passar pela validação de código que a borda APH
  fazia por `ErroDoFio`. Agora há **um registro só**
  (`apps/api/src/toc_api/dominio/federacao/wire.py`, `CODIGOS_PROPRIOS`), `envelope()` constrói pelo domínio (código não declarado levanta
  antes de virar resposta) e o mapa `status → código` do tratador do Starlette virou a
  constante `CODIGO_POR_STATUS`, visível para quem varre. A aptidão nova é
  `apps/api/tests/contrato/test_registro_de_codigos_a7.py`: uma varredura por árvore
  sintática (AST) sobre `src/toc_api/**/*.py` que exige todo código literalmente emitido no
  registro, recusa duas grafias do mesmo código, e confere o outro lado da igualdade (os
  códigos que a tela discrimina).
- **O portão de conformidade APH não dizia o que mediu (regra R2)** —
  `scripts/check-conformidade-aph.sh`. Ele herdava o ambiente do shell: sem `DATABASE_URL`
  exportada o serviço sobe em `persistencia: memoria` e a suíte, que é caixa-preta,
  devolve **11/11 do mesmo jeito**. Foi o que aconteceu na corrida da revisão independente
  — verde legítimo, alvo errado, e a saída não dizia nem uma coisa nem outra. Agora o
  portão: monta o alvo com **ambiente explícito**; **sonda o banco antes** de subir o
  serviço (motor do SQLAlchemy é preguiçoso: sem a sondagem, o `/saude` diria `postgres`
  com o cluster fora do ar); **declara campo a campo** o que mediu — persistência, cadeia e
  de onde ela veio, servidor, revisão da migração, identidade, admissão, ambiente — e
  declara a **natureza do turno**: enlatado e determinístico, sem provedor de modelo
  (ADR 0007), medido sem grant, logo com principal anônimo e catálogo vazio; e **RECUSA**
  (saída 3) medir contra alvo em memória, a não ser que quem chama peça
  `--permitir-memoria`, e aí o veredito sai carimbado e a saída é 1. Duas sabotagens novas
  em `scripts/tests/run-sabotagem.sh` (terceira metade: sabotagem por **ambiente**, para
  portão que não tem fixture de arquivo) provam as duas metades.


### Jornadas vivas — J-01, J-02, J-03 e J-07 (princípio P6, skill `living-journey`)

- **`docs/jornadas/scripts/capturar-telas.mjs`**: o gerador versionado das capturas. Sobe
  o `toc-api` com os seis parâmetros de admissão do §B.4 preenchidos, três instâncias da
  interface (autônoma, embarcada sem token e sem admissão) e um **hospedeiro de bancada**
  que fala o `ghd.*` do Anexo B e responde `POST /auth/introspect`; percorre a aplicação
  com Chromium de verdade; grava `docs/jornadas/capturas/` e um `manifesto.json` com
  tamanho, resumo SHA-256 e as medidas colhidas na corrida. Falha de captura derruba a
  corrida — não existe imagem de outro dia num documento de hoje.
- **Quatro jornadas vivas**, com avaliação heurística datada de 2026-09-06:
  `001-chegada-e-embarque.md`, `002-primeiro-projeto-e-ara.md`,
  `003-nuvem-de-conflito.md` e `007-a-travessia.md`. Corrida de 2026-09-06, medida pelo
  `manifesto.json` que a própria corrida escreveu: **36 capturas,
  5 771 779 bytes, 0 falhas**
  (`find docs/jornadas/capturas -name '*.png' | wc -l` → `36`, conferido pelo
  portão `scripts/check-evidencia-colada.sh`). **O tempo de parede não entra aqui**: ele
  muda a cada execução e fingi-lo estável seria o mesmo defeito com outra roupa. O
  `manifesto.json` não grava duração, então não há de onde copiá-la: inventá-la aqui seria
  a violação que esta própria entrada está corrigindo.

  > **Correção de honestidade (2026-09-06).** A primeira redação desta entrada dizia
  > **33 capturas, 5 153 510 bytes, 44,1 s** — números de uma corrida anterior, colados
  > depois que a corrida seguinte já tinha gravado 36 imagens. A mensagem de commit que
  > anunciou "33 telas" é história e não se reescreve; este arquivo e as jornadas podem, e
  > por isso trazem o número certo com o comando ao lado.
- **A travessia (J-07) é jornada própria**: a mesma pessoa monta a Árvore da Realidade
  Atual com Efeitos Indesejáveis validados por regra pura, promove dois deles a dilema em
  um clique, e a Nuvem que nasce declara a origem — conferida pelo script contra os nós
  escolhidos, sob pena de derrubar a corrida. É o encadeamento (INT-05) que nenhuma das
  quatro gerações da linhagem entregou.
- **J-04, J-05 e J-06 continuam sem documento, com a evidência da ausência**: não há
  módulo de domínio nem tela para Árvore da Realidade Futura, Pré-Requisitos, Transição,
  focalização ou Estratégia & Táticas. Jornada sem captura é ficção, e a Iron Law da skill
  proíbe.
- **`scripts/check-jornadas.sh`**: a Iron Law virada portão executável — toda captura
  citada por exatamente uma jornada (J1), toda imagem citada existindo (J2), heurística
  datada e **não anterior** às capturas (J3, o passo que a skill chama de "o que todo
  mundo esquece") e o comando de regeneração declarado (J4). Corrida: 4 jornadas, 33
  capturas, 33 citações, **74 verificações**. Registrado em `scripts/evidencia.sh`
  (agora **13 portões, 13 verdes**) e provado por **cinco sabotagens** em
  `scripts/tests/run-sabotagem.sh` sobre a fixture `scripts/tests/sabotagem/jornadas/`
  (a suíte passa a ser **6 portões e 32 sabotagens**, todas reprovando pelo motivo
  declarado).
- **20 achados registrados**, três de severidade Alta e nenhum corrigido neste lote (são
  código de produção, e código de produção nasce por ciclo com teste que falha antes —
  P4): a sessão do embarque autentica `/aph/*` (`200`) e não `/toc/*` (`401`); a ficha do
  Efeito Indesejável mostra o veredito antigo depois de "Reformular"; e "Ajustar à tela"
  enquadra a árvore abaixo da dobra porque a área de trabalho cresce com o painel
  (2 761 px numa janela de 900 px). Cada um com evidência por `arquivo:linha`.

### Ciclo 007 — Nuvem de Conflito (M3, spec 007 · serviço)

- **Agregado `NuvemDeConflito`** (`apps/api/src/toc_api/dominio/nuvem.py`): topologia
  fixa de 5 entidades (A, B, C, D, D′) e 7 arestas (`A_B`, `A_C`, `B_D`, `C_D_PRIME`,
  `D_C`, `D_PRIME_B`, `D_D_PRIME`), criadas na origem e **indestrutíveis** (RN-01,
  RF-03); a chave da aresta é derivada do par de papéis e a classe (necessidade,
  pré-requisito, perigo, conflito) da chave (RN-02); leitura por extenso montada dos
  textos atuais (RF-07). Sobre o núcleo do M1 **por composição**, como o M2.
- **Premissa como entidade de primeira classe** (RF-12..RF-15): várias por aresta,
  ordenadas, com estado `vigente`/`desafiada` (justificativa obrigatória) e
  arquivamento que leva as injeções junto **dizendo quantas**. Premissa vazia é erro no
  domínio e no banco.
- **Injeção ligada a premissa** (RN-04): não existe construtor de injeção sem premissa
  viva; máquina de estados `candidata → escolhida | descartada` com retorno justificado
  (RN-08); classificação por separação TRIZ e cobertura das 5 separações no conflito
  D↯D′ (RN-07); `ReferenciaDeSemeadura` vazia ao escolher (RF-20, INT-06).
- **Encadeamento M2 → M3** (`derivar_nuvem_de_udes`, INT-05): a nuvem nasce a partir de
  Efeitos Indesejáveis da Árvore da Realidade Atual, com `ReferenciaDeOrigem` **tipada**
  (ferramenta, projeto e nós), dono herdado do agregado de origem e a ARA lida, nunca
  escrita. É a costura que nenhuma das quatro gerações da linhagem tinha: lá, ARA e
  Nuvem eram dois bancos simulados sem referência entre si
  (`tocbuilderv3/services/mockApiService.ts:10-14`).
- **Geração assistida com contrato, não com parser**: `ResultadoDeGeracao` validado
  contra esquema JSON versionado (`apps/api/src/toc_api/dominio/geracao.py`), recusa em falha fechada
  com código estável (`VERSAO_DESCONHECIDA`, `FORA_DO_ESQUEMA`), porta
  `MotorDeGeracaoDeNuvem` e adaptador **local determinístico declarado como tal** —
  nenhum SDK de provedor no produto (ADR 0007). O contraexemplo medido é o parser por
  expressão regular do v3, que devolvia `null` inteiro a qualquer variação de formato.
- **Três ações governadas** no catálogo `toc.*` (`toc.generate_conflict_cloud`,
  `toc.suggest_assumptions`, `toc.suggest_injections`), todas `confirm`: nascem
  `action_proposal`, o `input_schema` da primeira embute o esquema do resultado (a
  validação acontece antes de a proposta existir), e **recusar deixa o projeto byte a
  byte intacto** — provado por comparação de bytes do estado serializado. Sem
  `toc:write` as três não existem para o principal (RF-27). O manifesto versionado
  (`specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json`) passou de 8 para 11
  ações, aceito pelo schema normativo com 0 erro.
- **Heurísticas de formulação** (`apps/api/src/toc_api/dominio/formulacao.py`, RF-09..RF-11): léxico
  versionado pt/en, aviso pedagógico com explicação e exemplo, nunca bloqueio, e
  `indeterminado` honesto quando a heurística não alcança o caso — com corpus sintético
  próprio (`apps/api/tests/dominio/corpus_formulacao.json`, 20 casos: 10 bem e 10 mal formulados).
- **Persistência**: migração Alembic **0005** com `upgrade` e `downgrade` (tabelas
  `nc_nuvem`, `nc_premissa`, `nc_injecao`), invariantes impostas também pelo banco
  (premissa vazia, desafio sem justificativa, injeção sem premissa, status e separação
  fora do vocabulário) e testes de integração contra o PostgreSQL real.
- **Superfície HTTP** sob `/toc/nc` (20 operações): nenhuma cria ou exclui entidade ou
  aresta — a ausência é medida no OpenAPI publicado —, visão de solução com as **sete**
  posições (o defeito do v3, que renderizava cinco, virou caso de teste), vista tabular,
  validação com completude e avisos, e a rota de geração que devolve pré-visualização
  sem aplicar nada.

### Ciclo 001 — Fundação e planejamento (entregue, aguardando gate humano)

- **Método Maestro instalado** pelo instalador oficial (`bin/maestro init` do canônico)
  antes de qualquer artefato: agentes, skills, scripts do ritual, comandos e a governança
  do método (`docs/governance/`), verificados por `scripts/check-install.sh`.
- **Visão do produto** (`docs/produto/visao.md`): o problema (dilemas e conflitos
  organizacionais analisados sem método), o que a Teoria das Restrições (TOC) oferece, e
  a **linhagem medida** — quatro gerações de TOC-Builder e cinco repositórios natimortos
  contados por `ls` com a saída colada, onze defeitos D-01..D-11 cada um com o comando
  executado (a chave do provedor no navegador nas quatro gerações; a especificação de API
  byte-idêntica quatro vezes e nunca implementada; zero testes; metade das ferramentas
  quatro gerações desabilitada; a Estratégia & Táticas que regrediu), e as cinco
  perguntas ao Product Steward mantidas abertas com resposta proposta.
- **Mapa de módulos** (`docs/produto/modulos.md`): M1–M8 como *bounded contexts*, épicos
  por módulo, dependências e o grafo de ordem de construção — cada módulo amarrado ao
  defeito de linhagem que corrige ou à lacuna que preenche.
- **Rounds** (`docs/produto/rounds.md`): onze rounds mapeando os ciclos 002–012, cada um
  com os seis campos obrigatórios (Apetite · Entrega · Fora · Aptidão executável ·
  Depende de · Sai primeiro/Nunca sai), a aptidão do 003 fixada em **"a junta fecha
  contra a `ghdaru` real"**, alocação exaustiva dos onze defeitos (nove em rounds, dois
  não-corrigidos com motivo declarado), e os **bloqueios externos declarados** com
  caminho — os schemas de manifesto mutuamente exclusivos e os grants em memória
  (medições da irmã `gestaodeprioridades`, mensagem 005), e a ação federada sem
  credencial com F7 pendente (ADR 0023 do `ghdaru`).
- **Roadmap de ciclos** (`docs/roadmap.md`): os doze ciclos com raia, portões em bullets
  e a pré-condição explícita de cada um ("o que o ciclo NNN não pode começar sem");
  nenhuma linha de código de produção antes do ciclo 003.
- **Decisões estruturais** em Registro de Decisão Arquitetural (ADR), 0001–0008
  (`docs/adr/`): constituição própria e herança das regras R1–R5 da irmã; stack; a
  federação APH (Aplicação ↔ Harness) Nível 2 `mode: embedded`; taxonomia de
  planejamento com selos de confiança; escopo v1 (tambor-pulmão-corda fora, com a
  contagem zero colada); base sintética desde o dia 1; inteligência artificial somente
  pela fundação; site de produto gerado por script.
- **12 specs** (`specs/001-fundacao-e-planejamento/` a
  `specs/012-jornadas-e-autodeclaracao/`): a do próprio ciclo e as onze de planejamento
  dos módulos e fatias, no formato do ADR 0004 — requisitos com fonte e selo, lacunas
  L-NN e `## Clarify` limitado a cinco dúvidas por spec.
- **Gerador do site de produto vendorizado** (`tools/product-site/`, ADR 0008): o
  `spec-to-code-docs` de `GHDaru/daruskills` copiado com atribuição e **adaptado** ao
  vocabulário deste corpus — requisitos de interface (RI-NN) como tipo próprio ao lado de
  RF, RNF, RN e INT; agrupamento pelos sub-cabeçalhos que o autor escreveu; fontes lidas da
  seção `## Fontes` (F-NN com `arquivo:linha`); vocabulário da Teoria das Restrições; as
  oito fases reais do Maestro com dono, métrica e aresta de falha; taxonomia de 15 termos em
  três categorias. O `tools/product-site/templates/styles.css` fica **byte a byte idêntico** à origem (mesma
  soma `md5`), porque a régua de design não se troca por gosto.
- **Site de produto gerado** (`docs/product-site/`): quatro páginas — visão geral com
  taxonomia, workflow, ADRs, princípios, artefatos e métricas; os módulos M1–M8 com épicos
  e as doze specs; a matriz de rastreabilidade com 359 RF, 114 RI e 105 RNF, cada um com
  selo e fonte; e o roadmap dos doze ciclos com os portões reais e a **nota de honestidade**
  (ciclo 001 em curso, zero linha de código de produção, nenhuma jornada viva). Todo número
  é contado na geração (regra R1), e regerar duas vezes produz bytes idênticos.
- **Primeira mensagem externa** (`mensagens/001-para-daruskills-defeitos-do-gerador-de-site.md`):
  sete achados no gerador de origem, reproduzidos rodando-o cru contra este repositório —
  entre eles, os princípios da constituição contados como requisito não funcional em todas
  as specs (189 contra 105 reais), a fronteira de feature dividida por média (cinco das sete
  features da spec 004 com intervalo errado) e os portões do roadmap descartados em favor de
  uma tira fixa. Relatada e parada, como manda o P1.

- **Base sintética da "Instituição Horizonte"** (`docs/produto/dados/`, ADR 0006): a
  primeira base de dados do projeto nasce **sintética e declarada como tal no próprio
  arquivo** (`sintetica: True`) — uma instituição de ensino técnico fictícia, três
  personas que são **papéis** e não pessoas ("Facilitadora TOC", "Participante",
  "Gestora"), uma Árvore da Realidade Atual (ARA) de 16 nós (12 Efeitos Indesejáveis —
  UDE — e 4 causas) com 16 arestas causais, e uma Nuvem de Conflito de 5 entidades, 7
  arestas com premissa e 2 injeções. O medidor `docs/produto/dados/medir-base.py` valida
  a estrutura e roda as checagens: `validação estrutural: 0 falha(s)`, código de saída 0.
  A dívida que obriga a irmã `gestaodeprioridades` a ser um repositório privado **não
  nasceu aqui**, e passou a ser verificável em vez de prometida.
- **Defeito D-12 — os critérios de UDE nunca foram medidos** (`docs/produto/visao.md:406`,
  alocado ao round 005 em `docs/produto/rounds.md:322`): as quatro gerações da linhagem
  TOC-Builder carregam onze características de UDE **apenas como texto de prompt**, sem
  nenhuma jamais ter sido executada. O ciclo mediu: das 11 características, **8 checagens
  cobrindo 7 são decidíveis por função pura** e **4 exigem julgamento** e ficam fora do
  alcance de qualquer função. Sobre os 12 UDEs autorais, 3 passam e 9 reprovam, cada
  reprovação nomeando a checagem (CD-1 a CD-8). D-12 vira critério de aceite do épico
  E2.1 no ciclo 005 — a regra de domínio pura que o P3 exige, testável sem rede e sem
  modelo.
- **A circularidade do D-12 foi atacada com um conjunto de controle externo** — a
  pendência declarada pelo construtor da visão e o achado que custou a única derrota do
  gauntlet: a base autoral foi escrita pelo mesmo autor das checagens e *para* trazer as
  patologias que elas procuram, logo "3 de 12" mede acordo do autor consigo mesmo. O
  retrabalho colheu **9 enunciados da própria linhagem**, escritos antes das checagens e
  por outra mão (`tocbuilderv3/constants.ts` e `components/CanvasWelcome.tsx`, os oito de
  `constants.ts` idênticos nas quatro gerações), e mediu: **0 falso positivo, 1 falso
  negativo (K-03)**. Um defeito real nas checagens, achado por um conjunto que não foi
  escrito para elas.
- **Suíte de sabotagem** (`scripts/tests/run-sabotagem.sh`): os cinco portões deste
  projeto provados **não lenientes** — `portões cobertos: 5 · bases válidas aceitas: 5/5`
  e `sabotagens declaradas: 27 · reprovadas pelo motivo certo: 27/27`, cada sabotagem
  sobre uma cópia em `/tmp`, sem tocar o repositório. Código de saída 0. As quatro últimas
  são as do `scripts/check-vazamento.sh`, o portão que substituiu a linha 11 da DoD.
- **Agregador de evidência** (`scripts/evidencia.sh`): roda a bateria e emite a tabela com
  comando, código de saída e **denominador** de cada portão (regra R2) —
  `Portões executados: 6 · verdes: 6 · vermelhos: 0`.
- **`qa-report.md` do ciclo 001 preenchido com evidência real**
  (`specs/001-fundacao-e-planejamento/qa-report.md`): **18 verificações distintas, 17
  verdes e 1 vermelha**, toda saída colada literalmente; o veredito do gauntlet (10 peças
  julgadas às cegas contra o corpus da irmã `gestaodeprioridades` e o PROJETO_ECS — 9
  vitórias na primeira rodada, a visão de produto derrotada, retrabalhada e vencedora no
  rejulgamento, fechando 10/10); e a cauda com `TAIL:review`, `TAIL:security` e
  `TAIL:mutation` escritos. `TAIL:gate` fica **em branco de propósito**: o gate humano é
  do Product Steward e é indelegável.
- **Critério 11 da DoD reescrito, e provado por sabotagem** (`scripts/check-vazamento.sh`):
  ele media a *string do caminho* da base da irmã `gestaodeprioridades` quando dizia medir
  **vazamento de dado real de pessoa**, e por isso reprovava a própria evidência do ADR
  0006 — um comando que imprime só contagens. O critério novo mede **conteúdo**, em três
  sinais: nome próprio em campo de pessoa, registro no formato do esquema da irmã (quatro
  ou mais chaves no mesmo registro) e base real lida por código que não é `*.md`. Ele varre
  `arquivos varridos: 195 · linhas varridas: 51485 · registros JSON inspecionados: 2557` e
  sai 0; e **reprova quatro sabotagens** que plantam vazamento fictício. A troca está
  declarada na `specs/001-fundacao-e-planejamento/spec.md`. Não é afrouxamento: o critério
  novo é **mais largo** que o antigo — pega três classes que o antigo não via.
- **Verificador executável dos rounds** (`scripts/check-rounds.sh`): os sete campos
  obrigatórios por round, o grafo de dependências e a alocação exaustiva dos defeitos
  D-NN passaram a ser conferidos por máquina — `rounds examinados: 11 · conferências de
  campo: 77 · arestas de dependência: 15 · ciclos encontrados: 0 · defeitos medidos: 12 ·
  alocados a round: 10 · declarados sem round: 2`, código de saída 0, e cinco sabotagens
  provando que ele reprova. Era a dívida declarada em "Conhecido" deste mesmo ciclo.
- **Procedimento de fechamento de ciclo** (`docs/governance/como-fechar-um-ciclo.md`): o
  que o Product Steward confere antes de assinar (os sete itens do §8 do `qa-report.md`),
  o estado real das branches deste repositório (a branch de trabalho **não** se chama
  `dev` e a `main` local **não existe** — as duas medidas com `git rev-parse`), o comando
  exato de promoção com `MAESTRO_DEV_BRANCH`, o que o `scripts/promote-main.sh` grava em
  `docs/records/decisoes.jsonl`, e como reverter. O comportamento do script foi **medido
  num clone temporário com repositório remoto falso**, não descrito de memória: ele aborta
  hoje no portão de conformidade, e a rota manual que o próprio script autoriza está
  escrita. Nenhum agente executou a promoção — aprovar merge é portão humano inegociável, e
  quem executou não aprova o que executou.

### Conhecido

- **O gate humano do ciclo 001 está aberto**: são sete itens, tabelados no §8 de
  `specs/001-fundacao-e-planejamento/qa-report.md` — ratificar a constituição e os oito
  ADRs; responder as cinco perguntas da visão §7 e as três dúvidas do `## Clarify`;
  ratificar o critério 11 reescrito; autorizar a entrega da mensagem 002 ao método;
  aceitar ou recusar as sete dívidas do §9; e autorizar a promoção. O procedimento está
  em `docs/governance/como-fechar-um-ciclo.md`. Nada abaixo do ciclo 002 começa antes
  disso, e **nenhum agente executou a promoção**.
- **A promoção não roda pelo caminho feliz hoje**: o `scripts/promote-main.sh` chama
  `scripts/check-conformance.sh` sem argumento no seu passo 3 e aborta, porque o portão do
  método sai 1 (`✗ no cycle in range (floor 42) — the gate checked nothing.`). O próprio
  script prevê o caso e autoriza a rota manual quando a dívida está decidida e registrada
  — ela está (Dv-3 do §9). Some-se a isso que a branch de trabalho não se chama `dev` e a
  `main` local não existe neste clone: as duas coisas exigem uma variável de ambiente e um
  `git branch` antes de promover. Tudo medido e escrito em
  `docs/governance/como-fechar-um-ciclo.md`.
- **Um portão vermelho, diagnosticado e não afrouxado** (detalhe em
  `specs/001-fundacao-e-planejamento/qa-report.md` §4):
  - `scripts/check-conformance.sh 001` sai **1** por causa **externa**: os pisos do script
    são números **absolutos** de ciclo da história do repositório canônico do método
    (`FLOOR=42` na linha 52, `CRIT_FLOOR=45` na 54, `ABSENCE_FLOOR=61` na 77,
    `MUT_FLOOR=55` na 91). Num repositório que começa no ciclo 001, o ciclo mais novo é
    `012` por construção, logo `55 > 12` e `61 > 12` são verdadeiros para sempre e os
    blocos de sanidade do fecho (linhas 468-475) reprovam independentemente do que este
    repositório escreva. O arquivo é a superfície instalável do método e `GHDaru/maestro`
    é **leitura** (P1): **relatado e parado**, pendente a mensagem externa. Apertando os
    pisos para 1 — o que o próprio script permite, porque seus knobs só admitem apertar —
    o veredito substantivo aparece e é sobre o conteúdo, não sobre o piso.
  - O **segundo vermelho deixou de existir**: a linha 11 da DoD contava `1` onde a spec
    esperava `0`, e a única ocorrência era o **caminho** citado no bloco de evidência do
    ADR 0006 — um comando que imprime só contagens (`tarefas: 114`) e nunca conteúdo.
    Corpo de ADR committado não se reescreve e portão não se afrouxa; sobrou a rota certa,
    que era reescrever o **critério** para medir o que ele dizia medir. Feito, declarado na
    spec e provado por quatro sabotagens. **O que aguarda o Product Steward é a
    ratificação da troca de critério, não a execução dela.**
- **Sete dívidas declaradas com dono e ciclo**, tabeladas no §9 de
  `specs/001-fundacao-e-planejamento/qa-report.md`. As que mudam o próximo ciclo:
  - **RNF-01 (português no projeto, inglês na superfície instalável) não tem portão
    executável** — hoje é verificado por leitura. Dono: construtor do ciclo 002.
  - **`docs/produto/rounds.md:18` ainda declara que o verificador executável dos rounds
    "ainda não existe"** — e ele existe, passou com 77 conferências de campo e foi
    sabotado cinco vezes. O arquivo ficou fora dos lotes do fechamento; corrigir é uma
    linha, na abertura do ciclo 002. (Esta entrada do `CHANGELOG.md`, que carregava a
    mesma afirmação vencida, **foi corrigida acima**.)
  - **A seção "Fora de escopo" é pontuada e não bloqueante** no `scripts/check-specs.sh`:
    perdê-la custa 8 dos 15 pontos de Escopo e a spec continua passando no corte ≥ 80.
    Apertar exige a sabotagem que veja o portão reprovar — trabalho de ciclo.
  - **A circularidade da base autoral está mitigada, não resolvida** (9 enunciados de
    controle externos, 4 das 11 características de UDE indecidíveis por função pura).
    Fecha só com corpus de oficina real, e isso esbarra no ADR 0006 — vai para o ciclo 005.
- **Três bloqueios externos** condicionam o ciclo 003 e dois o alcance do 006 — todos de
  fora deste repositório, todos com caminho citado em `docs/produto/rounds.md`; a regra
  é re-medir na abertura do ciclo afetado, não assumir que caíram.
