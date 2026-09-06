"""A superfície HTTP do encadeamento (E4.4) — `/toc/cadeia`, spec 008.

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **HTTP** — *HyperText Transfer Protocol* · **RF/RN** — requisito funcional
/ regra de negócio.

**Quatro rotas de escrita e uma de leitura**, e o desenho delas é a decisão:

- promover, semear e derivar são **`POST` com o alvo nomeado pelo gesto** (INT-04): o
  cliente diz de onde parte e como se chama o que nasce; o inquilino e o dono vêm do
  agregado de origem, **nunca** do corpo do pedido;
- as três aplicam **na hora** — manipulação direta do titular sob o item 8 da constituição
  do projeto, reversível por exclusão suave (RF-35), com traço obrigatório (RNF-03). Não
  há tela de confirmação e não há máquina de estados de proposta nesta superfície;
- a vista da cadeia é `GET`: leitura pura sobre as referências, com o elo pendente
  **visível** em vez de omitido (RF-35, US-18).

O que **não** está aqui: as quatro ações `toc.suggest_*`. Elas são inferência de modelo e
nascem `action_proposal` na máquina de estados do ciclo 006 — outro caminho, outro regime.
"""
from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, status

from ...aplicacao.cadeia import (
    AbrirCadeia,
    DerivarAprDeArf,
    DerivarAtDeOi,
    ListarReferenciasDoProjeto,
    PromoverUdesParaNC,
    SemearArfDeInjecao,
)
from ..dependencias import ExecutorDependente
from ..esquemas import (
    AprOut,
    ArfOut,
    AtOut,
    CadeiaOut,
    DerivacaoDeAprIn,
    DerivacaoDeAtIn,
    NuvemOut,
    PromocaoIn,
    ReferenciaOut,
    SemeaduraIn,
)

roteador = APIRouter(prefix="/toc/cadeia", tags=["cadeia"])


@roteador.post(
    "/promocoes", status_code=status.HTTP_201_CREATED, response_model=NuvemOut
)
def promover(corpo: PromocaoIn, executor: ExecutorDependente) -> NuvemOut:
    """RF-36 — o INT-05 da spec 007, executado: UDEs `Validado` viram o dilema de uma NC.

    A recusa da RN-13 (UDE fora de `Validado`) chega ao cliente como código estável com a
    regra nomeada em `details` — o cliente discrimina por código, nunca por mensagem.
    """
    nuvem = executor.rodar(
        PromoverUdesParaNC,
        projeto_id=corpo.ara_projeto_id,
        no_ids=tuple(corpo.no_ids),
        nome=corpo.nome,
    )
    return NuvemOut.de(nuvem)


@roteador.post(
    "/semeaduras", status_code=status.HTTP_201_CREATED, response_model=ArfOut
)
def semear(corpo: SemeaduraIn, executor: ExecutorDependente) -> ArfOut:
    """RF-38 — o INT-06 da spec 007, executado: a injeção escolhida vira o nó semente."""
    arf = executor.rodar(
        SemearArfDeInjecao,
        projeto_id=corpo.nc_projeto_id,
        injecao_id=corpo.injecao_id,
        nome=corpo.nome,
    )
    return ArfOut.de(arf)


@roteador.post(
    "/derivacoes/apr", status_code=status.HTTP_201_CREATED, response_model=AprOut
)
def derivar_apr(corpo: DerivacaoDeAprIn, executor: ExecutorDependente) -> AprOut:
    """RF-39: o objetivo é PROPOSTO do texto escolhido e continua editável."""
    apr = executor.rodar(
        DerivarAprDeArf,
        projeto_id=corpo.arf_projeto_id,
        no_id=corpo.no_id,
        nome=corpo.nome,
        objetivo=corpo.objetivo,
    )
    return AprOut.de(apr)


@roteador.post(
    "/derivacoes/at", status_code=status.HTTP_201_CREATED, response_model=AtOut
)
def derivar_at(corpo: DerivacaoDeAtIn, executor: ExecutorDependente) -> AtOut:
    """RF-40: o objetivo intermediário vira o alvo navegável da Árvore de Transição."""
    at = executor.rodar(
        DerivarAtDeOi,
        projeto_id=corpo.apr_projeto_id,
        no_id=corpo.no_id,
        nome=corpo.nome,
    )
    return AtOut.de(at)


@roteador.get("/{projeto_id}", response_model=CadeiaOut)
def vista_da_cadeia(projeto_id: UUID, executor: ExecutorDependente) -> CadeiaOut:
    """RF-41/RF-42: a travessia inteira a partir de qualquer elemento encadeado."""
    return CadeiaOut.de(executor.rodar(AbrirCadeia, projeto_id=projeto_id))


@roteador.get("/{projeto_id}/referencias", response_model=list[ReferenciaOut])
def referencias_do_projeto(
    projeto_id: UUID, executor: ExecutorDependente
) -> list[ReferenciaOut]:
    """RF-34: as referências de origem e destino de um projeto, para a ficha do elemento."""
    return [
        ReferenciaOut.de(r)
        for r in executor.rodar(ListarReferenciasDoProjeto, projeto_id=projeto_id)
    ]
