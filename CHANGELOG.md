# Changelog

Formato: [Keep a Changelog](https://keepachangelog.com/pt-BR/1.1.0/).
Versionamento: [SemVer](https://semver.org/lang/pt-BR/).

## [Não publicado]

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
  repositório a **52 capturas,
  8 481 359 bytes, 0 falhas** (`find docs/jornadas/capturas -name '*.png' | wc -l` → `52`,
  conferido pelo portão `scripts/check-evidencia-colada.sh`). **O tempo de parede não entra
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
