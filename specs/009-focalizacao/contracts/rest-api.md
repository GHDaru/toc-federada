# Contrato REST 009 — Focalização (M6)

> Siglas, uma vez neste documento: **TOC** — Teoria das Restrições · **M1** — Núcleo de
> Diagramas Lógicos · **M2** — Árvore da Realidade Atual (ARA) · **M3** — Nuvem de
> Conflito (NC) · **M4** — Árvores de Futuro e Implementação · **ARF** — Árvore da
> Realidade Futura · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de Transição ·
> **M6** — Focalização · **REST** — *Representational State Transfer* · **HTTP** —
> *HyperText Transfer Protocol* · **UUID** — *Universally Unique Identifier* · **JSON** —
> *JavaScript Object Notation* · **APH** — Aplicação ↔ Harness · **RF/RN/RNF/RI** —
> requisito funcional / regra de negócio / requisito não funcional / requisito de
> interface · **ADR** — *Architecture Decision Record*.

- **Prefixo**: `/toc/focalizacao` — 15 caminhos, 18 pares verbo + caminho · **implementação**:
  [`../../../apps/api/src/toc_api/http/roteadores/focalizacao.py`](../../../apps/api/src/toc_api/http/roteadores/focalizacao.py)
  · **esquemas**: [`../../../apps/api/src/toc_api/http/esquemas.py`](../../../apps/api/src/toc_api/http/esquemas.py)
- **Contrato executável**: [`../../../apps/api/tests/contrato/test_http_focalizacao.py`](../../../apps/api/tests/contrato/test_http_focalizacao.py)
  valida cada resposta contra o OpenAPI da própria aplicação. Divergência entre este
  documento e o teste se resolve a favor do teste.
- **Autorização**: `fail-closed`, fora do modelo de linguagem (P2). A política vive em
  [`../../../apps/api/src/toc_api/aplicacao/governanca.py`](../../../apps/api/src/toc_api/aplicacao/governanca.py):
  6 casos de uso de leitura sob `TOC_LEITURA`, 12 de escrita sob `TOC_ESCRITA`.
- **Isolamento**: todo recurso é filtrado pelo dono `(inquilino_id, usuario_id)` vindo da
  introspecção (INT-01). Projeto de outro inquilino responde `404`, nunca `403` — a
  existência não vaza.

## A jornada

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises` | RF-01, RF-02 | `201` `AnaliseOut` — a análise nasce com o **ciclo 1 aberto e os cinco passos instanciados**; não existe casca sem jornada |
| `GET` | `/analises` | RF-03, RI-07 | `200` `[AnaliseResumoOut]` — passo atual e restrição vigente como colunas de primeira classe |
| `GET` | `/analises/{projeto_id}` | RF-04 | `200` `AnaliseOut` |
| `DELETE` | `/analises/{projeto_id}` | RF-04 | `200` `AnaliseOut` — exclusão **suave**, herdada do M1 |
| `POST` | `/analises/{projeto_id}/restauracao` | RF-04 | `200` `AnaliseOut` |
| `GET` | `/analises/{projeto_id}/jornada` | RF-07, RI-01 | `200` `JornadaOut` — o mapa dos cinco passos com estado, pendências e avisos |
| `GET` | `/analises/{projeto_id}/linha-do-tempo` | RF-17, RI-06 | `200` `[CicloNaLinhaOut]` — os ciclos em ordem, com restrição e desfecho |

## A restrição

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises/{projeto_id}/restricao` | RF-05, RF-06 | `201` `RestricaoOut` — `origem` é **opcional**: a ARA ajuda, nunca condiciona |
| `PUT` | `/analises/{projeto_id}/restricao` | RF-08 | `200` `RestricaoOut` |

O corpo do `PUT` **não tem campo `tipo`** de propósito: trocar o tipo da restrição é trocar
de restrição, e o caminho para isso é registrar outra — o esquema `EditarRestricaoIn` recusa
o campo com `extra="forbid"` antes de o domínio precisar opinar.

## Os passos

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises/{projeto_id}/passos/{passo}/conclusao` | RF-09 | `200` `JornadaOut` — avançar é ato explícito, e a resposta já é o mapa depois dele |
| `POST` | `/analises/{projeto_id}/reaberturas` | RF-10 | `200` `JornadaOut` — reabre o passo **imediatamente anterior**, sem apagar a decisão dele |
| `POST` | `/analises/{projeto_id}/passos/{passo}/notas` | RF-11 | `201` `JornadaOut` — anotar **não** avança a jornada |

Não há `POST /passos`, `DELETE /passos/{passo}` nem rota de reordenação. A ausência é o
contrato: os cinco passos são invariante (RN-01), não coleção.

## Os vínculos de ferramenta

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises/{projeto_id}/passos/{passo}/vinculos` | RF-14, RNF-04 | `201` `VinculoOut` |
| `DELETE` | `/analises/{projeto_id}/passos/{passo}/vinculos/{vinculo_id}` | RF-14 | `200` `JornadaOut` |
| `GET` | `/ferramentas/{alvo_id}/analises` | L-03, INT-04 | `200` `[ReferenciaReversaOut]` — a navegação de volta, **sem campo novo em M2, M3 ou M4** |

**A combinação pela porta, não pela implementação.** O vínculo é opaco no domínio (só a
canonicidade da RN-06 é regra de domínio). Existência, inquilino, ferramenta declarada ×
ferramenta real e estado do alvo são conferidos **no servidor**, na camada de aplicação,
contra a porta `RepositorioDeProjetos` — nunca contra o agregado de outro módulo. É o que
permite a suíte de domínio do M6 rodar offline sem M2, M3 e M4 instalados.

O `VinculoOut` carrega o estado resolvido do alvo (`ativo`, `arquivado`, `inexistente`), com
legenda legível. Vínculo apontando para projeto arquivado **degrada**, não quebra: a
jornada continua e a tela avisa.

## A herança e o recomeço

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises/{projeto_id}/heranca/{decisao_id}/veredito` | RF-16, RN-05 | `200` `JornadaOut` |
| `POST` | `/analises/{projeto_id}/recomecos` | RF-15, RF-16 | `201` `AnaliseOut` — fecha o ciclo, abre o próximo em `identificar` e herda o que pode virar inércia |

`VeredictoIn.veredito` é `Literal["mantida", "revogada"]`: **`pendente` não é aceito**.
Voltar a pendente apagaria um julgamento, e histórico é apêndice (RN-04). A recusa acontece
na borda **e** no domínio; nenhuma das duas basta sozinha, porque o fio conversacional do
APH não passa pela borda REST.

## A assistência (RF-19)

| Verbo | Caminho | Requisito | Resposta |
|---|---|---|---|
| `POST` | `/analises/{projeto_id}/sugestoes-de-restricao?ara_projeto_id=` | RF-19, RF-20 | `200` `SugestaoDeRestricaoOut` |

**Esta rota não escreve nada.** Ela devolve as candidatas (nó de causa raiz da ARA
vinculada ao passo `identificar`, com racional e alcance sobre os efeitos indesejáveis), o
`action_id` da ação governada e o aviso de que aplicar exige proposta. Quem escreve é a
confirmação da proposta na máquina de estados do ciclo 006 — e é por isso que recusar é de
graça: nada foi tocado.

Sem ARA vinculada, a lista volta **vazia** e a jornada segue: a sugestão é aceleradora,
nunca dependência (RF-20).

## Erros (§A.7 do Anexo A do padrão APH)

Cinco códigos estáveis novos, todos `409`, todos com `detalhes.regra` — o cliente corrige
sem interpretar texto em português:

| Código | Erro de domínio | Exemplo de `regra` |
|---|---|---|
| `INVALID_FOCUSING_STEP` | `PassoInvalido` | `ordem_canonica` |
| `INVALID_CYCLE` | `CicloInvalido` | `sem_ciclo_aberto` |
| `INVALID_CONSTRAINT` | `RestricaoInvalida` | — |
| `INVALID_TOOL_LINK` | `VinculoInvalido` | — |
| `INVALID_INHERITED_DECISION` | `HerancaInvalida` | — |

A trava otimista responde `409 VERSION_CONFLICT` (ADR 0010) em toda rota mutadora acima —
o M6 não tem código próprio para conflito de versão, e a lacuna do registro mínimo do §A.7
está relatada em [`../../../mensagens/005-para-protocolos-codigo-de-conflito-de-versao-no-a7.md`](../../../mensagens/005-para-protocolos-codigo-de-conflito-de-versao-no-a7.md).

## Observabilidade (P5)

Toda mutação emite traço OpenTelemetry com o identificador do agregado; o teste
[`../../../apps/api/tests/integracao/test_traco_m6.py`](../../../apps/api/tests/integracao/test_traco_m6.py)
falha se `RestricaoRegistrada`, `PassoConcluido` ou `CicloFechado` não deixarem rastro.
