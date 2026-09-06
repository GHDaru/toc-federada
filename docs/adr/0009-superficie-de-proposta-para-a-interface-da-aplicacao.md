# ADR 0009 — A interface da aplicação decide proposta por `/toc/propostas`: mesma máquina de estados, mesmo traço, projeção estruturada

- **Status**: Aceita
- **Data**: 2026-09-06 · **Ciclo**: 007 (correção de defeito de produto achado por revisão independente)
- **Decisor**: agente construtor sob a regra R3 (ação reversível de baixo raio), com a
  quarta condição acionada — **toca princípio INEGOCIÁVEL**, e por isso a decisão está
  escrita aqui, argumentada contra o texto do princípio, em vez de apenas executada.
- **Sucede**: nenhum
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — "nada de segundo protocolo […] verbo
  mutador nasce `action_proposal`". Este ADR (Architecture Decision Record, registro de
  decisão arquitetural) **não emenda o P2 e não abre exceção a ele**: ele acrescenta uma
  **projeção** da mesma proposta de ação para o consumidor que faltava (a interface da
  própria aplicação), mantendo um único caminho de escrita. O argumento de por que isto
  não é um segundo protocolo está na seção "Decisão", item 2.

## Contexto

A revisão independente da interface achou um defeito de produto, e tinha razão: **o laço
da assistência não fechava na tela**.

A pré-visualização da geração assistida (`apps/web/src/componentes/nuvem/PreviaDaGeracao.tsx`)
mostrava o diff completo do que a geração propunha e oferecia **um** botão: "Recusar". A
ausência do "Aceitar" estava documentada no próprio componente — *"a escrita é da proposta
que atravessa a máquina de estados no servidor, com gate humano"* — e a documentação
descrevia o buraco em vez de fechá-lo: não existia, em lugar nenhum da aplicação, caminho
para a pessoa aceitar a proposta e ver a nuvem mudar. A funcionalidade mais vistosa do
produto não concluía.

A avaliação heurística datada da jornada J-03 já tinha registrado o mesmo achado, e ele
seguia aberto:

```text
$ grep -c 'A-03' docs/jornadas/003-nuvem-de-conflito.md
1
$ grep -o 'o único botão de decisão é \*\*Recusar\*\* — não há "Aceitar" nenhum' docs/jornadas/003-nuvem-de-conflito.md
o único botão de decisão é **Recusar** — não há "Aceitar" nenhum
```

**O servidor já tinha tudo o que faltava.** A ação governada existe
(`toc.generate_conflict_cloud`, `apps/api/src/toc_api/dominio/federacao/catalogo.py`), a
máquina de estados existe e é testada pela tabela e pelo complemento dela
(`apps/api/src/toc_api/dominio/federacao/proposta.py`), os casos de uso `ProporAcao` e
`DecidirProposta` existem com política, validação de `input_schema` e traço obrigatório
(`apps/api/src/toc_api/aplicacao/federacao/acoes.py`), e o executor sabe aplicar o
resultado na nuvem (`apps/api/src/toc_api/infra/federacao/executor.py`). O que **não**
existia era uma porta por onde a interface levasse a proposta ao gate e a decidisse.

As duas portas de proposta que existiam servem o **hospedeiro**, e nenhuma serve a tela:

| Porta | Consumidor | O que devolve |
|---|---|---|
| `POST /aph/sessions/{s}/proposals/{p}` (§A.6 do Anexo A) | hospedeiro, dentro de uma sessão de conversa | evento do fio |
| `POST /aph/actions/{action_id}` | hospedeiro, borda de execução (ADR 0023 de lá) | `{"result": "proposta <id> criada e aguardando confirmação humana (N alvo(s))"}` |

A segunda **tem** o identificador da proposta — dentro de uma frase em português. Lido, não
lembrado, de `apps/api/src/toc_api/http/aph.py`:

```text
$ grep -n 'aguardando confirmação' apps/api/src/toc_api/http/aph.py
394:                        f"proposta {proposta.proposal_id} criada e aguardando confirmação "
```

Extrair o `proposal_id` de dentro dessa frase seria a interface **discriminando por
mensagem**, que é exatamente o que o §A.7 proíbe ao fixar o `code` estável "porque o
cliente discrimina por código e nunca por mensagem" — e quebraria na primeira revisão de
texto, sem uma linha de contrato mudar.

## Decisão

1. **A aceitação da geração assistida é a confirmação de uma proposta de ação**, e nada
   mais. A tela não escreve no estado: ela cria a proposta no servidor (que nasce
   `proposed` e vai a `awaiting_approval`, porque a ação é `confirm`) e depois a confirma
   (`confirmed → executing → executed`). Quem escreve na Nuvem de Conflito é o executor do
   catálogo, depois da decisão, com traço correlacionado ao `proposal_id`.

2. **A porta da interface é `/toc/propostas`** —
   `POST /toc/propostas` (a proposta nasce) e `POST /toc/propostas/{proposal_id}/decisao`
   (o gate humano) —, montada sobre os **mesmos** `ProporAcao` e `DecidirProposta` da
   composição da federação.

   **Por que isto não é um segundo protocolo** (o teste que o P2 impõe, respondido item a
   item):

   - **não há segunda máquina de estados**: a FSM (máquina de estados finitos) é a mesma
     instância de domínio, e uma transição inválida pedida por aqui responde
     `409 INVALID_TRANSITION`, com o código que o próprio domínio nomeou;
   - **não há segunda política**: a autorização continua acontecendo dentro do caso de
     uso (§B.7.2), e a varredura `test_a_camada_http_nao_decide_acesso_em_lugar_nenhum`
     conta **zero** decisões de acesso na camada HTTP, este roteador incluído;
   - **não há segundo caminho de escrita**: a rota não toca repositório nenhum; sem
     confirmação, nada acontece — provado por leitura byte a byte do projeto antes e
     depois de propor;
   - **não há segundo registro de erros**: os códigos saem do registro único de
     `apps/api/src/toc_api/dominio/federacao/wire.py`, pela mesma função `envelope()`;
   - **não há segundo vocabulário**: `origem`, `risk`, `estado`, `status` e `outcomes` são
     os campos do §A.3/§A.6, com os mesmos significados.

   O que existe é uma **projeção a mais da mesma proposta**, para o terceiro consumidor —
   e ter três projeções de uma fonte é o próprio APH-4.4 ("uma fonte, três projeções"),
   que este projeto já aplica no catálogo.

3. **`origem` é dado declarado pelo cliente, e continua sem virar desvio de fluxo.** Só o
   cliente sabe a procedência do conteúdo (o servidor não tem como distinguir uma frase
   digitada de uma produzida pela assistência), então ele a declara; o padrão é `ia`,
   porque esta superfície nasce para conteúdo assistido. Ela muda **uma palavra na tela**
   e mais nada — nenhum `if` sobre origem decide fluxo, estado ou conteúdo (RI-02 da spec
   006, ADR 0009 da irmã, APH-5.9).

4. **A superfície de confirmação é uma só** (`proposta-de-acao`, RI-01 da spec 006):
   `apps/web/src/componentes/federacao/SuperficieDeConfirmacao.tsx` recebe uma proposta e
   não sabe nada da Nuvem de Conflito — geração, sugestão de premissa ou lote de nós usam
   a mesma tela. Confirmar e recusar têm a **mesma classe** de botão, porque peso visual
   igual é requisito (RI-06 da spec 007), não estética.

## Alternativas consideradas — descartadas com o motivo

- **Fazer a tela aplicar o resultado com os comandos REST da nuvem** (`PUT …/entidades/A`
  e amigos, em laço). Descartada, e é a que o defeito quase provocou: seria a interface
  escrevendo conteúdo de modelo direto no estado — o P2 pelo avesso, sem proposta, sem
  gate e sem traço; e a origem `geracao` dos eventos (RF-25 da spec 007) desapareceria,
  tornando a mutação assistida indistinguível de edição humana um mês depois. É
  literalmente o que a 4ª geração da linhagem fazia
  (`tocbuilderv3/components/ConflictCloudView.tsx`, leitura apenas).
- **Reaproveitar `POST /aph/actions/{action_id}` e extrair o identificador da frase.**
  Descartada: cliente discriminando por mensagem (§A.7), quebra em revisão de texto, e
  ainda faltaria a rota de decisão fora de sessão de conversa.
- **Fazer a interface abrir uma sessão do fio (`POST /aph/sessions`) só para decidir pelo
  §A.6.** Descartada por honestidade de modelo: a tela **não está conversando**. Criar
  uma sessão de conversa vazia para carregar uma decisão que já tem superfície própria
  encheria o log de sessões sem turno e faria a decisão parecer um turno de diálogo que
  nunca houve. O §A.6 continua servindo quem conversa — o hospedeiro.
- **Criar a proposta já no `POST …/geracoes`, junto da pré-visualização.** Descartada por
  causa da RF-28 (a NC funciona por inteiro com o catálogo ausente ou desligado): a
  pré-visualização passaria a depender de o principal ter `toc:write` e de o catálogo
  responder, e quem só lê perderia a leitura da geração. Também encheria o repositório de
  propostas que ninguém pediu, a cada clique em "Gerar", esperando o TTL (*Time To Live*,
  tempo de vida) vencer.

## Consequências

- (+) O laço fecha **pelo caminho certo**: a nuvem muda porque o servidor escreveu, e a
  tela mostra o que releu dele. A prova é de integração, com PostgreSQL real e três
  aplicações diferentes — propor numa, confirmar noutra, ler numa terceira
  (`apps/api/tests/integracao/test_propostas_no_postgres.py`).
- (+) Recusar deixou de ser silêncio: a recusa no gate é uma transição registrada, com
  traço `denied` (RI-04 da spec 006), enquanto recusar **a pré-visualização** continua de
  graça — ali não houve proposta, logo não há o que registrar.
- (+) A superfície de confirmação nasce reutilizável: as outras duas ações mutadoras do
  M3 (`toc.suggest_assumptions`, `toc.suggest_injections`) passam a ter para onde ir.
- (−) São **dois passos** para aplicar uma geração (aceitar leva ao gate; confirmar
  aplica). É o custo do desenho, e é deliberado: o primeiro passo é sobre o conteúdo (o
  diff), o segundo é sobre a autorização (o que o servidor registrou — proposta, alvos,
  vencimento). Colapsá-los num clique só faria a superfície de confirmação virar
  formalidade.
- (−) Uma proposta criada e abandonada fica `awaiting_approval` até o TTL de dez minutos
  vencer. Não há varredura de expiração em segundo plano; a expiração é decidida na
  tentativa de confirmar (`PROPOSAL_EXPIRED`). Dívida nomeada, não escondida.

## O que este ADR NÃO decide

- **A bandeja de propostas pendentes** (RI-07 da spec 007, RI-08 da 006: as aprovações
  pendentes reaparecem depois da recarga). O repositório já sabe respondê-la
  (`listar_pendentes`, implementado nos dois adaptadores e ainda sem chamador); a rota de
  listagem e a tela ficam para o ciclo que as especificar — YAGNI, e a decisão de hoje
  não as impede.
- O `context_hash` das telas do M3: a Nuvem de Conflito ainda não está no manifesto
  publicado, logo não é superfície de snapshot; os campos existem no contrato e a
  interface não os envia.
- Qualquer coisa sobre o fio do Anexo A, que fica exatamente como estava.

## Registro

- `docs/governance/constitution.md` — P2, cujo alcance esta decisão respeita
- `specs/006-acoes-governadas-e-snapshot/spec.md` — RF-16, RI-01 a RI-05
- `specs/007-nuvem-de-conflito/spec.md` — RF-21 a RF-28, RI-06
- `apps/api/src/toc_api/http/roteadores/propostas.py` — a porta decidida aqui
- `apps/web/src/componentes/federacao/SuperficieDeConfirmacao.tsx` — a superfície única
- `apps/api/tests/contrato/test_http_propostas.py` e
  `apps/api/tests/integracao/test_propostas_no_postgres.py` — a prova
