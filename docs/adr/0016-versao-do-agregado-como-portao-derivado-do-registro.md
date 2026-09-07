# ADR 0016 — A versão do agregado é a metade de domínio da trava, e o portão que a mede tira o denominador do registro de raízes

- **Status**: Aceita
- **Data**: 2026-09-07 · **Ciclo**: correção de defeito grave achado por crítico hostil
- **Decisor**: agente construtor sob a regra R3 (ação reversível de baixo raio), com a
  quarta condição acionada — a decisão **muda o comportamento observável da fronteira**
  (operações da Árvore da Realidade Atual que antes nunca conflitavam passam a poder
  devolver `409 VERSION_CONFLICT`), e por isso está escrita aqui em vez de apenas
  executada.
- **Sucede**: nenhum — este registro de decisão arquitetural (ADR, do inglês *Architecture
  Decision Record*) **completa** o ADR 0010, não o contradiz. O 0010 continua "Aceita" e
  continua certo em tudo o que decidiu; o que ele não disse é que a trava tem uma segunda
  metade, no domínio, e é essa metade que este ADR nomeia e mede.
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — a mudança faz operações da ferramenta
  passarem a poder devolver `409 VERSION_CONFLICT`, um código que já está no **registro
  único** do §A.7 do Anexo A do Padrão APH (Aplicação ↔ Harness), acrescentado pelo ADR
  0010 com motivo declarado. **Nenhum código novo nasce aqui e nenhum segundo registro é
  criado**: o que muda é quantas operações podem emiti-lo. Também **P4** (o conserto
  começou pelos dois testes que reproduzem, contra o PostgreSQL real) e **P3** (a regra é
  do domínio; o adaptador continua sendo quem condiciona a escrita).

## Contexto

A trava otimista do ADR 0010 tem **duas metades**, e só uma estava medida:

1. **A metade do adaptador** — `UPDATE … WHERE versao = :versao_lida`, o `rowcount`
   conferido, o `ConflitoDeVersao` levantado, o `409` com os dois números. O portão
   `scripts/check-trava-otimista.sh` mede essa metade, e mede bem.
2. **A metade do domínio** — **a versão só protege o que ela acompanha**. Um agregado que
   muda estado persistido sem chamar `Projeto._avancar` faz as duas escritas que leram a
   mesma versão casarem as duas no `WHERE`; as duas são aceitas, e a reconciliação apaga
   do banco o retrato de quem gravou primeiro. Essa metade **não era medida por nada**.

O ADR 0010 podia tomar a primeira metade como dada porque, para o núcleo do Módulo 1 (M1 —
Núcleo de Diagramas Lógicos), ela era verdade: as oito mutações de grafo do `Projeto`
chamam `_avancar`, e o teste `test_toda_mutacao_avanca_a_versao_e_o_instante` cobria as
oito. O que ninguém verificou é se as **raízes de ferramenta** — que têm estado próprio
persistido, fora do grafo — faziam o mesmo.

### A medida do crítico, e a nossa reprodução (R1)

```text
$ for f in ara nuvem arf apr at snt focalizacao; do grep -c '_avancar' src/toc_api/dominio/$f.py; done
ara 0 · nuvem 11 · arf 10 · apr 6 · at 2 · snt 5 · focalizacao 10
```

A Árvore da Realidade Atual (ARA) era **o único agregado de ferramenta fora da trava**.
Marcar Efeito Indesejável (UDE, do inglês *undesirable effect*), editar a ficha, registrar
parecer, mudar o status para `validado`, examinar elo e formar conector E não avançavam
versão nenhuma. A reprodução, contra o PostgreSQL real, com o que voltou colado:

```text
$ pytest tests/integracao/test_concorrencia_no_postgres.py -k "parecer or validado"
concorrência M2 (parecer da ARA): 20 escritas · aceitas 20 · recusadas 0 · pareceres no banco 1
E       AssertionError: 20 escrita(s) aceita(s) e 1 parecer(es) no banco: julgamento humano
        aceito e perdido em silêncio
E       Failed: DID NOT RAISE ConflitoDeVersao
```

É o pior lugar possível para o buraco: a ARA é a porta de entrada do produto e o módulo em
que mais gente trabalha junto, e o que sumia era justamente o **trabalho de julgamento
humano** — o parecer e o status `validado`, os dois estados que a spec 005 (RN-10) protege
com guarda de máquina de estados para que "validado" signifique alguma coisa.

### O diagnóstico (skill `diagnostico-antes-do-fix`)

A pergunta era se a ARA ficou de fora por **ordem histórica** ou se havia algo **na
estrutura dela** que resistiu. A resposta medida é: as duas coisas, e a estrutural é a que
importa — porque é ela que explica por que várias ondas passaram por cima sem ver.

A ordem histórica sozinha não explica. A Nuvem de Conflito (NC) também é anterior à trava
(spec 007, contra a spec 005 da ARA) e **tem** o `_avancar` nas mutações próprias. O que
separa as duas é topologia:

```text
$ python3 (leitura por árvore sintática abstrata dos sete agregados de ferramenta)
ProjetoARA             delega ao núcleo: [adicionar_efeito, editar_aresta, editar_no,
                       excluir_aresta, excluir_no, ligar, mover_no, recolher_no, reformular]
                         das quais CRIAM nó/aresta: ['adicionar_efeito', 'ligar']
NuvemDeConflito        delega ao núcleo: ['editar_entidade']
                         das quais CRIAM nó/aresta: NENHUMA
```

A NC tem topologia **fixa** — a RN-01 da spec 007 diz que as 5 entidades e as 7 arestas
nascem juntas e não se destroem —, então ela não tem nenhuma delegação ao núcleo que crie
linha. Quem escreveu o teste de concorrência da NC no ciclo 008 **não tinha** o que
disputar a não ser uma mutação própria (`registrar_premissa`), e o `_avancar` entrou junto
com o teste.

A ARA tinha `adicionar_efeito`. O teste escrito no mesmo ciclo para provar que "a ARA tem a
mesma trava que o M1" disputou `adicionar_efeito`, foi verde **pelo `_avancar` do núcleo**,
e não tocou em uma linha de semântica da ferramenta. Foi por isso que a retrofit não a
alcançou: **a ARA é o único agregado de ferramenta anterior à trava que tinha onde se
esconder.**

A conclusão de método é a que decide o conserto: acrescentar as chamadas fecharia o caso.
A trava foi aplicada **agregado a agregado, à mão**, e o único que ficou de fora passou
despercebido por várias ondas — logo o que tem de mudar é o modo de aplicar, não só o
resultado.

## Decisão

**1. Toda mutação de estado próprio de raiz de ferramenta avança a versão.** As oito
mutações próprias da ARA (`marcar_ude`, `desmarcar_ude`, `editar_ficha`,
`registrar_parecer`, `mudar_status`, `examinar_elo`, `formar_conector_e`,
`desfazer_conector_e`) chamam `self.projeto._avancar(em)`, como as das outras seis raízes.

**2. Um portão cujo DENOMINADOR vem do registro, não de uma lista.**
`scripts/check-versao-do-agregado.sh` lê as raízes de ferramenta de
`registrar_raiz_de_ferramenta` — a mesma lista que `Projeto._exigir_raiz` já obriga toda
ferramenta a preencher para o grafo dela funcionar (*fail-closed*: ferramenta que não se
registra fica bloqueada, nunca liberada) — e compara com a lista das que avançam versão.
A diferença reprova.

Esta é a diferença deste portão para o `check-trava-otimista.sh`, que declara as portas de
escrita **à mão** e diz, no próprio comentário, que a lista escrita à mão é de propósito:
lá o alvo é o adaptador, um arquivo só, e derivar a lista dele faria o portão concordar com
quem esquecesse a trava. Aqui o alvo são sete agregados em sete arquivos, e foi exatamente
a lista mantida à mão que deixou um de fora. **O denominador certo depende do que se
mede**, e é por isso que os dois portões coexistem em vez de um substituir o outro.

**3. O portão mede as DUAS direções**, porque o inverso é o mesmo defeito com os papéis
trocados:

| Direção | O que reprova |
|---|---|
| domínio → adaptador | raiz registrada cujo método escreve estado próprio e não avança a versão |
| adaptador → domínio | `salvar_*` que grava sem passar por `_gravar_*` (escrita não condicionada) |
| registro → escrita | raiz registrada sem nenhum caminho de escrita que a receba |
| escrita → registro | `salvar_*` novo para um agregado que não entrou no registro |

Medida do inverso, executada: **7 de 7 raízes casadas com caminho de escrita
condicionado** — nenhuma raiz de ferramenta avança versão com escrita incondicional hoje.

Os **outros dois agregados persistidos** foram medidos à parte, porque não são raízes de
ferramenta e por isso ficam fora do denominador deste portão:

- `ReferenciaCruzada` (spec 008, RF-33) — as duas mutações reais (`suspender`, `reativar`)
  avançam, e a escrita é condicionada por `_gravar_referencia`, que o
  `check-trava-otimista.sh` já confere. Nada a fazer.
- `PropostaDeAcao` (federação) — **não tem versão numérica**: a trava dela é a transição
  de estado (`estado_lido`), decidida no ADR 0011 e medida pelo
  `scripts/check-trava-da-proposta.sh`. Exigir `_avancar` aqui seria confundir duas travas
  diferentes, e é por isso que ela não entra no registro de raízes de ferramenta.

**4. O que o portão NÃO exige, e por quê.** Não exige versão de método que só lê
(`analisar`, `gerar_verificacao`, `gerar_sequenciamento` produzem relatório e emitem evento,
sem tocar estado persistido); não exige de `__post_init__` e demais *dunder*, que rodam na
**construção** — inclusive na reidratação, que é leitura, e um agregado que saísse do banco
já com a versão adiantada teria a primeira gravação recusada sem ninguém ter concorrido; e
aceita como avanço a chamada a uma mutação **pública** do núcleo que avança por dentro
(`self.projeto.descrever_problema(...)`), lendo de `projeto.py` quais são — exigir uma
segunda chamada faria a versão pular de dois em dois.

**5. Sabotagem própria.** Cinco mutações declaradas em `scripts/tests/run-sabotagem.sh`,
quatro delas uma por direção da tabela acima — mais uma que cobra o preço da única
indulgência do portão (auxiliar privado só é perdoado se TODOS os chamadores dele
avançarem) —, sobre a base `scripts/tests/sabotagem/versao-do-agregado/`.
Um portão que nada derruba não é portão.

## Alternativas consideradas

| Alternativa | Por que não |
|---|---|
| **Só acrescentar os oito `_avancar` na ARA** | Fecha o caso e deixa a classe aberta — que é literalmente o defeito de que este ADR trata. O oitavo agregado nasceria fora da trava do mesmo jeito |
| **`_avancar` dentro do `_emitir` de cada raiz** | Amarra versão a EVENTO, e há evento de relatório que não muda estado persistido (`analisar`, `gerar_verificacao`). A versão passaria a subir em operação de leitura, e toda leitura sujaria o agregado |
| **Acrescentar o item ao `check-trava-otimista.sh`** | Aquele portão tem lista escrita à mão por um motivo declarado no próprio arquivo, e misturar as duas disciplinas de denominador num script só torna as duas ilegíveis. Portões separados, sobreposição declarada |
| **Teste de domínio "toda mutação avança a versão", agregado a agregado** | É o que já existia para o `Projeto` do M1, e passava verde enquanto a ARA estava fora: um teste por agregado tem o mesmo problema de denominador que a lista à mão |
| **Trava pessimista ou `serializable`** | Recusadas no ADR 0010, pelos motivos registrados lá. Nada aqui muda essa análise |

## Consequências

- Operações da ARA que **nunca** conflitavam passam a poder devolver `409
  VERSION_CONFLICT`: marcar Efeito Indesejável, editar ficha, registrar parecer, mudar
  status, examinar elo e formar conector. É mudança visível de comportamento, e é a
  desejada — antes elas não conflitavam porque apagavam o trabalho alheio em silêncio.
- A interface continua **sem** recarregar e refazer sozinha: ela discrimina o código
  (`apps/web/src/api/erros.ts`), e fechar o laço na tela segue sendo trabalho declarado
  como pendência, agora com mais operações que podem cair nele.
- Fica declarado como **pendência medida, não resolvida**: a ARA é também a única raiz de
  ferramenta cujas mutações próprias não chamam `Projeto._exigir_ativo` (`ara 0` contra
  `nuvem 12 · arf 4 · apr 2 · at 2 · snt 6 · focalizacao 11`), então marcar UDE e registrar
  parecer num projeto **excluído** ainda são aceitos. É a mesma família — guarda aplicada
  agregado a agregado, à mão — e merece o mesmo tratamento (teste que reproduz, correção e
  portão), num ciclo próprio.

## Fontes

- Reprodução e testes: `apps/api/tests/integracao/test_concorrencia_no_postgres.py`
- Correção: `apps/api/src/toc_api/dominio/ara.py`
- Portão e sabotagem: `scripts/check-versao-do-agregado.sh`,
  `scripts/tests/run-sabotagem.sh`, `scripts/tests/sabotagem/versao-do-agregado/`
- Decisão que este ADR completa: `docs/adr/0010-trava-otimista-por-versao-lida.md`
- Norma: `/home/user/protocolos/padrao/anexo-a-wire-format.md` (§A.7)
