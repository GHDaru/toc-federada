# ADR 0012 — O M4 nasce com o pacote de suficiência **extraído** e a referência cruzada como **agregado próprio**

> Siglas, uma vez neste documento: **ADR** — *Architecture Decision Record* (Registro de
> Decisão Arquitetural) · **TOC** — Teoria das Restrições · **M1** — Núcleo de Diagramas
> Lógicos · **M2** — Árvore da Realidade Atual (ARA) · **M3** — Nuvem de Conflito (NC) ·
> **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da Realidade Futura ·
> **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **UDE** — Efeito
> Indesejável · **ED** — Efeito Desejável · **OI** — Objetivo Intermediário · **APH** —
> Aplicação ↔ Harness · **DDD** — *Domain-Driven Design* (Design Orientado a Domínio) ·
> **RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional ·
> **HTTP** — *HyperText Transfer Protocol* · **SQL** — *Structured Query Language*.

- **Status**: Aceita
- **Data**: 2026-09-06
- **Ciclo**: 008 — Árvores de Futuro e Implementação ([`../../specs/008-arvores-de-futuro-e-implementacao/spec.md`](../../specs/008-arvores-de-futuro-e-implementacao/spec.md))
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — as quatro ações `toc.*` do módulo nascem
  `action_proposal` e nenhuma delas executa fora da máquina de estados do servidor;
  promover, semear e derivar são manipulação direta do titular sob o item 8 da
  constituição, e o ADR declara isso em vez de reinterpretá-lo · **P3** (o pacote extraído
  e as funções puras) · **P4** (o teste da cadeia nasceu vermelho antes da promoção
  existir) · **P5** (o identificador da referência criada viaja no traço).
- **Sucede**: nenhum ADR. Este acrescenta; não contradiz nenhuma decisão anterior.

## Contexto

O M4 é o módulo que faz esta aplicação **suceder a linhagem de fato**. Nas quatro gerações
do TOC-Builder, ARF, APR e AT foram item de menu desabilitado —
`tocbuilderv3/components/Sidebar.tsx:55-57` e o tipo de navegação em `types.ts:249-258`,
com zero componentes, zero prompts e zero linhas de domínio. E a referência entre projetos
nunca existiu: a contagem colada na spec 008 (F-08) é
`grep -c "araProjectId|sourceUdeId|linkedProject|crossTool" tocbuilderv3/types.ts` → `0`.

Ao implementar o módulo, três escolhas eram reais — cada uma com uma alternativa que
funcionaria e cobraria depois.

## Decisão

**1. O pacote de suficiência causal é EXTRAÍDO, nunca copiado.** O exame de elo, o
conector E e as duas leituras saíram de `apps/api/src/toc_api/dominio/ara.py` para `apps/api/src/toc_api/dominio/suficiencia.py`, e
a ARA e a ARF importam **o mesmo objeto**. A alternativa era duplicar as classes na ARF
— mais rápido de escrever e indistinguível por um teste de comportamento no primeiro dia.
Por isso a prova é de **identidade**: `apps/api/tests/dominio/test_suficiencia_compartilhada.py`
exige `ara.EstadoDoExame is suficiencia.EstadoDoExame`. Duas cópias que ainda não
divergiram passam num teste de comportamento e reprovam num de identidade.

No banco, a contrapartida física: a ARF **reusa** `elo_exame` e `conector_e` (as tabelas
do M2) em vez de ganhar tabelas gêmeas, e a reconciliação dos dois é um método só
(`_reconciliar_suficiencia`), usado pelas duas ferramentas.

**2. A lógica de NECESSIDADE da APR não mora nesse pacote — e a APR não oferece a
operação.** A ARA e a ARF encadeiam por suficiência ("Se A, então B"); a APR encadeia por
condição necessária ("A precisa existir antes de B"). A RN-05 da spec 008 diz que as duas
não se misturam no mesmo projeto, e a garantia entregue é **estrutural**, não visual:
`apps/api/src/toc_api/dominio/apr.py` não importa o pacote de suficiência, e `ProjetoAPR` não tem `examinar_elo`,
`exame`, `leitura_do_elo` nem `formar_conector_e`. A elipse de simultaneidade é classe
própria (`ElipseDeSimultaneidade`) e **não** o `ConectorE` reaproveitado, pelo mesmo
motivo: mesma notação visual, lógica diferente.

**3. A `ReferenciaCruzada` é agregado próprio, com trava otimista própria.** Um vínculo
entre dois projetos não pertence a nenhum dos dois; guardá-lo dentro de um faria a
consistência atravessar duas raízes e deixaria a ponta de fora sem responsável. Ela tem
identidade, estado (`ativa | pendente`), evento, e `versao`/`versao_lida` como o
`Projeto` — porque duas pessoas suspendem e reativam o mesmo vínculo, e quem partiu da
versão velha tem de ser **recusado com os dois números**, nunca sobrescrever em silêncio.

Consequência para o portão: `scripts/check-trava-otimista.sh` passou a conhecer **dois
gravadores** (`_gravar_projeto` e `_gravar_referencia`) e **sete** caminhos de escrita —
`salvar`, `salvar_ara`, `salvar_nuvem`, `salvar_arf`, `salvar_apr`, `salvar_at` e
`salvar_referencia`. Ele confere os dois gravadores pelos mesmos três itens (o `WHERE
versao =`, o `rowcount` conferido, o `ConflitoDeVersao` levantado), e
`scripts/tests/run-sabotagem.sh` ganhou 11 mutações que provam que ele reprova quando
qualquer peça sai:

```text
$ grep -c '"scripts/check-trava-otimista.sh" "trava-otimista"' scripts/tests/run-sabotagem.sh
11
```

**4. Nove códigos próprios novos no registro do §A.7.** Cada um nomeia uma recusa cuja
**correção do lado do cliente é diferente** das outras — que é o critério do §A.7 do Anexo
A para código próprio. `INVALID_PROMOTION` manda validar o Efeito Indesejável antes de
promover; `INVALID_SEEDING` manda escolher a injeção antes de semear; `INVALID_MIRROR`
manda escolher outro Efeito Indesejável. Um `MUTATION_REFUSED` genérico diria "não neste
estado" e deixaria o cliente adivinhando qual das três coisas fazer.

```text
$ grep -cE '^    "[A-Z][A-Z0-9_]*": ' apps/api/src/toc_api/dominio/federacao/wire.py
34
$ W=apps/api/src/toc_api/dominio/federacao/wire.py; echo $(( $(grep -cE '^    "[A-Z][A-Z0-9_]*",$' $W) + $(grep -cE '^    "[A-Z][A-Z0-9_]*": ' $W) ))
41
```

O `CODIGOS_PROPRIOS` tem 34 linhas com esta forma, e o registro §A.7 inteiro (mínimo
normativo mais os próprios) tem 41 códigos.

**5. As quatro ações `toc.suggest_*` do módulo EXECUTAM neste ciclo, e nada mais executa
sem gate.** É a virada que a spec 008 anuncia: no M2 e no M3 o P2 era prova negativa
("nada muta"); aqui é prova positiva — mutação direta é recusada, e o aceite cria o
elemento com o identificador da proposta no traço. Promover, semear e derivar seguem o
outro regime, o do item 8: manipulação direta do titular, aplicada na hora, reversível por
exclusão suave, com traço obrigatório.

**6. Não existe ação, rota nem prompt de ramo negativo assistido.** Decisão de round
(RF-10), e a prova é **negativa**: o catálogo não tem ação com `negative`/`ramo` no
identificador, e o OpenAPI publicado não tem rota assistida de ramo. A poda assistida é
decisão nova, com o seu próprio contrato de ação.

## Consequências

- **Boas**: a regra de suficiência tem uma implementação só, e o teste de identidade
  impede que ganhe duas; a cadeia UDE → NC → injeção → ARF → obstáculo → OI → passo é
  percorrível nos dois sentidos por função pura; a referência sobrevive à exclusão suave
  como `pendente` em vez de sumir; a trava otimista cobre a classe inteira, e não o caso.
- **Custo**: `apps/api/src/toc_api/dominio/ara.py` deixou de ser o dono das classes de suficiência (elas
  continuam importáveis de lá, e o teste de identidade é o que garante que continuem
  sendo as mesmas); o portão da trava ficou maior e precisa da lista de escrita atualizada
  a cada caminho novo — o que é o ponto dele.
- **Aberto**: o ramo negativo assistido e a poda automática ficam para um ciclo futuro,
  com ADR próprio. A vista da cadeia é calculada em memória, sem cache — a porta de volta
  está declarada na decisão 7 do plano do ciclo 008 se a medição da jornada discordar.
