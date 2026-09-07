# A unidade de restauração desta aplicação — procedimento e ensaio

> Siglas deste documento: **RPO** — *Recovery Point Objective* (objetivo de ponto de
> recuperação) · **RTO** — *Recovery Time Objective* (objetivo de tempo de recuperação) ·
> **PITR** — *Point-In-Time Recovery* (recuperação a um ponto no tempo) · **ADR** —
> *Architecture Decision Record* (Registro de Decisão Arquitetural) · **S3** — o protocolo
> de armazenamento de objetos · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
> Conflito · **HTTP** — *HyperText Transfer Protocol*.
>
> Requisitos que este documento fecha: **RF-01, RF-02, RF-03 e RN-07** da
> [`../../specs/011-fundacoes-da-aplicacao/spec.md`](../../specs/011-fundacoes-da-aplicacao/spec.md).

## A frase que governa este documento

> **"Backup é o que já foi restaurado com sucesso em outro lugar; cópia no mesmo
> armazenamento e na mesma conta é conveniência, não apólice."**

É o Princípio XII da constituição da fundação
(`ghdaru/.specify/memory/constitution.md:253-261`), e é a razão de este documento existir com um
**script executável ao lado**: uma cópia que ninguém restaurou é uma hipótese.

O ciclo 003 entregou o banco próprio e ensaiou o *rollback* de implantação — o que **não**
é restauração de banco. A medição está na spec 011 (fonte F-10):
`grep -rniE "backup|restaura|point-in-time" specs/003-esqueleto-federado/` devolve duas
linhas, uma de implantação e uma de "branch Neon criado antes de aplicar". Nenhuma das
duas é uma restauração ensaiada. Este é o delta.

## A unidade de restauração

Esta aplicação tem **banco próprio** (ADR 0002,
[`../adr/0002-stack-herdada-da-irma.md`](../adr/0002-stack-herdada-da-irma.md)): projeto
PostgreSQL Neon dedicado em produção, cluster local em desenvolvimento. Isso não é
preferência de organização — é o que faz a frase seguinte ser verdadeira:

> **Restaurar a `toc-federada` não rebobina nenhum outro produto da plataforma.**

Se esta aplicação dividisse banco com outro produto, restaurá-la a um ponto no tempo
levaria o outro junto — e a decisão de restaurar deixaria de ser desta equipe. O ensaio
prova a propriedade na prática: ele restaura num **banco novo** e sobe a aplicação contra
**ele**, nunca sobre a origem.

## O procedimento

```bash
export DATABASE_URL='postgresql+psycopg://…'      # a origem
scripts/ensaio-de-restauracao.sh                  # ensaio completo, limpa no fim
scripts/ensaio-de-restauracao.sh --manter         # deixa o destino de pé para inspeção
PROJETOS=50 scripts/ensaio-de-restauracao.sh      # com base maior
```

O script ([`../../scripts/ensaio-de-restauracao.sh`](../../scripts/ensaio-de-restauracao.sh))
faz sete passos, nesta ordem:

| # | Passo | Por que ele está aí |
|---|---|---|
| 1 | Migra e **semeia** a base sintética num esquema próprio, pela API | RF-05: semeadura é **comando explícito**, jamais efeito colateral de tabela vazia. Escrever pelos casos de uso (e não por `INSERT`) é o que faz o ensaio provar que a **aplicação** volta, não que o PostgreSQL copia linhas |
| 2 | Marca o **instante alvo** | É o ponto no tempo a que a restauração devolve — o número que a RF-03 exige no relatório |
| 3 | `pg_dump -Fc` do banco de origem | O despejo é o artefato; em produção o equivalente é a cópia gerenciada do provedor |
| 4 | `createdb` + `pg_restore` num **banco novo** | O "outro lugar" da frase. Restaurar por cima da origem provaria nada e destruiria tudo |
| 5 | Compara **tabela a tabela** e por **resumo `md5`** de projetos + nós | Contagem igual com conteúdo trocado passaria despercebida; o resumo compara o texto |
| 6 | Sobe a aplicação de verdade (`uvicorn --factory`, admissão do §B.4 completa) contra o destino e pede `GET /toc/projetos` | US-01: "a lista de projetos sintéticos aparece íntegra". Banco restaurado que a aplicação não consegue abrir não é restauração |
| 7 | Imprime o **relatório**: instante alvo, durações, tamanho e o que **não** volta | RF-03 |

Nenhuma credencial entra na saída (P7, RNF-10): a cadeia de conexão que o `/saude`
devolve já sai redigida (`postgresql+psycopg://***@/…`), e a credencial de admissão do
ensaio é sintética, vive dentro do processo e não é impressa.

## O que a restauração devolve — e o que ela não devolve

**Devolve** (medido no ensaio, não suposto): todo o conteúdo relacional da aplicação —
projetos, nós, arestas, fichas de Efeito Indesejável, pareceres, exames de elo,
conectores, premissas, injeções, ramos negativos, pares obstáculo↔objetivo intermediário,
fichas de passo, análises de focalização, árvores de Estratégia & Táticas, referências
cruzadas, propostas de ação e traço.

**Não devolve** — e cada linha é uma decisão, não um esquecimento:

- **arquivos em armazenamento compatível com S3** (anexos, capturas). Eles vivem fora do
  banco, atrás de porta própria, e têm apólice própria. Restaurar o banco e apontar para
  arquivos que já não existem é a forma mais comum de uma restauração "bem-sucedida"
  entregar uma aplicação quebrada;
- **o que foi escrito depois do instante alvo.** É o objetivo de ponto de recuperação em
  pessoa: nenhuma restauração inventa o que não estava no despejo;
- **índices e estatísticas** são **reconstruídos** pelo `pg_restore`, não copiados: o
  primeiro acesso depois da restauração é mais lento até o `ANALYZE`;
- **sessões de embarque em curso.** O grant do hospedeiro é de uso único e de vida curta
  (§B.6 do Anexo B): quem estava dentro refaz o *handshake*. Isto é correto, e não um
  defeito da restauração.

## Objetivos declarados

| Objetivo | Valor proposto | O que ele significa |
|---|---|---|
| **RPO** (ponto de recuperação) | 5 minutos | O intervalo máximo de trabalho que se aceita perder. Em produção, é a granularidade da recuperação a um ponto no tempo do provedor |
| **RTO** (tempo de recuperação) | 60 minutos | Da decisão de restaurar até a aplicação de pé. O ensaio local mede o **piso** desse número — não o número |

> **Os dois valores são proposta desta spec e dependem de decisão do Product Steward**, e
> o RPO depende ainda do plano contratado no provedor (lacuna L-01 da spec 011: "o plano
> contratado não está declarado em lugar nenhum deste repositório"). Enquanto não houver
> decisão registrada, eles são intenção — e este parágrafo existe para que ninguém os leia
> como compromisso.

## A periodicidade

A spec 011 exige **um ensaio dentro do ciclo**, e ele está feito (saída colada no
[`../../specs/011-fundacoes-da-aplicacao/qa-report.md`](../../specs/011-fundacoes-da-aplicacao/qa-report.md)).
A periodicidade seguinte é política operacional e precisa de dono — é uma das cinco
dúvidas em aberto da spec. Enquanto não houver dono, vale a regra mais simples que não
mente: **todo ciclo que toca migração roda o ensaio de novo**, porque é a migração que
muda o que a restauração tem de devolver.
