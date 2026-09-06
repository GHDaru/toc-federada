# ADR 0013 — A restrição tem taxonomia **fechada**, e uma decisão herdada "mantida" **volta à mesa** a cada recomeço

> Siglas, uma vez neste documento: **ADR** — *Architecture Decision Record* (Registro de
> Decisão Arquitetural) · **TOC** — Teoria das Restrições · **M2** — Árvore da Realidade
> Atual (ARA) · **M6** — Focalização · **RF/RN** — requisito funcional / regra de negócio ·
> **SQL** — *Structured Query Language* · **UI** — interface de usuário · **APH** —
> Aplicação ↔ Harness.

- **Status**: Aceita
- **Data**: 2026-09-06
- **Ciclo**: 009 — Focalização ([`../../specs/009-focalizacao/spec.md`](../../specs/009-focalizacao/spec.md))
- **Princípios tocados**: **P3** (as duas decisões são regra de **domínio puro**, testáveis
  sem rede, e não configuração de borda) · **P4** (as duas nasceram como teste vermelho —
  `test_uma_decisao_mantida_volta_a_ser_julgada_no_recomeco_seguinte` existiu antes de
  `_herdar` saber somar a segunda fonte) · **P2 (INEGOCIÁVEL)** é tocado **apenas** pelo
  item 1, e no sentido estreito de que o `enum` fechado vira `enum` no `input_schema` da
  ação governada `toc.suggest_constraint`: nenhuma das duas decisões cria protocolo,
  identidade ou autorização, e o verbo mutador continua nascendo `action_proposal`.
  Declarado por extenso porque a regra R3 exige que um ADR diga qual princípio inegociável
  encosta na matéria — a omissão é o sintoma, não a discordância.
- **Sucede**: nenhum ADR. Este acrescenta ao [ADR 0005](0005-escopo-do-dominio-v1.md)
  (escopo do domínio v1), que declara a focalização dentro do escopo sem decidir a forma da
  restrição, e não contradiz nenhuma decisão anterior.

## Contexto

O M6 é o módulo em que a aplicação, pela primeira vez, **diz qual é a restrição**. Nas
quatro gerações do TOC-Builder ela nunca existiu como dado: a linhagem sabia desenhar as
ferramentas da TOC e não sabia nomear o gargalo que elas existem para atacar.

Ao modelar a jornada dos cinco passos de focalização, duas escolhas eram reais — cada uma
com uma alternativa defensável, e cada uma com um custo que só apareceria depois.

## Decisão

### 1. `TipoDeRestricao` é um `enum` **fechado** de três valores

`fisica` · `politica` · `de_mercado` — os três tipos clássicos da literatura da TOC.

A alternativa era texto livre, e ela é sedutora: nenhuma migração, nenhuma discussão de
vocabulário, cada instituição usa a palavra que usa. O custo aparece na **linha do tempo**,
que é a razão de ser do módulo: ela compara restrições **entre ciclos**, e com texto livre
"capacidade" e "física" viram duas coisas diferentes em análises vizinhas da mesma
instituição. Uma comparação que depende de a pessoa ter digitado a mesma palavra não é uma
comparação — é uma coincidência.

Fechado também é o que permite o `enum` no `input_schema` de `toc.suggest_constraint`: uma
proposta com tipo inventado é recusada pelo esquema, antes de chegar ao executor.

Ampliar a taxonomia é **migração aditiva pequena** (uma linha no `enum`, uma linha na
restrição `CHECK`, uma chave em cada idioma). Voltar de texto livre para `enum` depois de
mil análises escritas é um projeto de limpeza de dados. A assimetria decide.

### 2. Uma decisão herdada julgada `mantida` **volta a ser julgada** no recomeço seguinte

Ao recomeçar, `_herdar` produz duas fontes de decisões herdadas, todas nascendo
`pendente`:

1. as decisões vigentes de `explorar` e `subordinar` do ciclo que está fechando — as regras
   de operação que ele criou;
2. as decisões que **aquele mesmo ciclo** herdou e julgou **`mantida`**.

As `revogada` não voltam: revogar é justamente dizer que aquela regra deixou de valer.

**A spec não escreveu esta segunda fonte.** Ela pede o julgamento da herança (RF-16, RN-05)
e para no primeiro ciclo. Implementar só o que estava escrito produziria o seguinte: uma
regra mantida uma vez atravessaria todos os ciclos futuros **sem nunca mais ser olhada** —
que é a definição operacional exata da inércia que o quinto passo de Goldratt existe para
impedir. Um passe vitalício concedido por um único "manter" é pior do que não ter
julgamento nenhum, porque parece governança.

A regra é, portanto, uma **derivação do requisito**, não um requisito novo: o quinto passo
diz "não deixe a inércia virar a restrição", e uma decisão que nunca mais volta à mesa é
inércia com carimbo.

### 3. Um passo reaberto herda **só a decisão vigente**

Consequência da RN-04 (histórico é apêndice: reabrir e concluir de novo acrescenta, nunca
substitui). Um passo reaberto tem duas decisões no histórico, mas a regra de operação que
sobreviveu é **a última** — a anterior já foi substituída pelo próprio grupo. Herdar as
duas mandaria à mesa uma regra que ninguém segue mais, e ruído é como um aviso deixa de
funcionar: quem recebe pendência inútil aprende a despachar todas.

Este item foi encontrado **pelo teste de traço**, não pelo desenho: a contagem de decisões
herdadas voltou 3 onde a jornada esperava 2. Está aqui porque a correção mudou
comportamento, e comportamento mudado sem registro é memória perdida.

### 4. Os cinco erros do módulo entram no registro §A.7 como códigos próprios

`INVALID_FOCUSING_STEP` · `INVALID_CYCLE` · `INVALID_CONSTRAINT` · `INVALID_TOOL_LINK` ·
`INVALID_INHERITED_DECISION` — todos `409`, todos com a regra nomeada em `detalhes.regra`.
A alternativa era reusar um código genérico de conflito e diferenciar por texto em
português, o que obrigaria o cliente a interpretar prosa para saber o que corrigir.

O corpo de um ADR não se reescreve, então a **contagem corrente** do registro passa a ser
cobrada do ADR mais novo — este — e a do [ADR 0012](0012-modulo-m4-suficiencia-compartilhada-e-referencia-como-agregado.md)
fica sendo o número da data dele. Executado em 2026-09-06:

```text
$ grep -cE '^    "[A-Z][A-Z0-9_]*": ' apps/api/src/toc_api/dominio/federacao/wire.py
39
$ W=apps/api/src/toc_api/dominio/federacao/wire.py; echo $(( $(grep -cE '^    "[A-Z][A-Z0-9_]*",$' $W) + $(grep -cE '^    "[A-Z][A-Z0-9_]*": ' $W) ))
46
```

O `CODIGOS_PROPRIOS` tem 39 linhas com esta forma, e o registro §A.7 inteiro (mínimo
normativo mais os próprios) tem 46 códigos. O portão que mantém esta conta viva é
`scripts/check-evidencia-colada.sh`.

## Consequências

**Boas.** A linha do tempo compara ciclos de verdade — "a restrição era política, agora é
de mercado" é uma frase que o dado sustenta. A herança pendente bloqueia a conclusão de
`subordinar`, então a inércia não passa em silêncio: ela custa um veredito com
justificativa e autor, e custa **a cada volta**. A UI traduz isso em dois botões de peso
igual (`manter` e `revogar`), porque se manter fosse mais barato a interface estaria
empurrando de volta o que a regra bloqueia.

**Custos aceitos.** Uma instituição cujo vocabulário não caiba em três tipos precisa de uma
migração para ser atendida — pequena, mas migração. E uma análise longa acumula vereditos
repetidos: quem manteve dez regras julga dez de novo no ciclo seguinte. É atrito
**intencional**; a alternativa é o passe vitalício. Se a prática mostrar que o atrito
excede o valor, o remédio é um lote de julgamento com justificativa comum — nunca o
silêncio.

**Onde isto vive.** Domínio:
[`../../apps/api/src/toc_api/dominio/focalizacao.py`](../../apps/api/src/toc_api/dominio/focalizacao.py)
(`TipoDeRestricao`, `PASSOS_QUE_GERAM_INERCIA`, `_herdar`). Provas:
[`../../apps/api/tests/dominio/test_heranca.py`](../../apps/api/tests/dominio/test_heranca.py).
Guarda no banco: `ck_foco_restricao_tipo_da_restricao` e
`ck_foco_heranca_veredito_exige_justificativa_e_autor`, em
[`../../apps/api/src/toc_api/alembic/versions/0008_m6_focalizacao.py`](../../apps/api/src/toc_api/alembic/versions/0008_m6_focalizacao.py).
