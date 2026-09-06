"""A proposta de ação vista pela própria aplicação — a superfície do gate humano.

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness (o padrão da fronteira) ·
**FSM** — máquina de estados finitos · **HTTP** — *HyperText Transfer Protocol* · **NC** —
Nuvem de Conflito · **TTL** — *Time To Live* (tempo de vida) · **RF/RI** — requisito
funcional / de interface.

## Por que este roteador existe

A assistência do produto termina numa pré-visualização em diff: a pessoa vê o que a
geração propõe **antes** de qualquer escrita. Faltava o outro lado do laço — o caminho por
onde ela **aceita**. Sem ele, a funcionalidade mais vistosa do produto não concluía, e a
ausência estava documentada em vez de fechada.

O caminho certo é um só, e não é a tela escrever no estado: aceitar é **confirmar uma
proposta de ação** que atravessa a máquina de estados no servidor —
`proposed → awaiting_approval → confirmed → executing → executed` — com traço em todo
desfecho (P2, APH-5.1 e 5.5, RF-23/RF-25 da spec 007). Estas duas rotas são a porta dessa
travessia para a interface da própria aplicação.

## Por que não reaproveitar as rotas do fio

Três consumidores, o mesmo motor, três portas — e a diferença é de contrato, não de regra:

| Consumidor | Porta | Corpo |
|---|---|---|
| hospedeiro, na conversa | `POST /aph/sessions/{s}/proposals/{p}` (§A.6) | evento do fio |
| hospedeiro, borda de execução | `POST /aph/actions/{action_id}` | `{"result": <texto>}` |
| **a interface desta aplicação** | **`/toc/propostas`** | proposta estruturada |

A interface não conversa para aceitar um diff que ela já mostrou inteiro: ela precisa do
`proposal_id` em **dado**. A borda federada devolve uma frase, por contrato do hospedeiro
(ADR 0023 de lá); ler o identificador de dentro dela seria o cliente discriminando por
mensagem, que é o que o §A.7 proíbe com todas as letras. O que muda aqui é a projeção; a
FSM, a política, o `input_schema` e o sumidouro de traço são os MESMOS objetos —
`ProporAcao` e `DecidirProposta`, montados uma vez na composição da federação.

## O que este módulo NÃO faz

Não decide acesso (§B.7.2: a verificação mora nos casos de uso, e a varredura
`test_a_camada_http_nao_decide_acesso_em_lugar_nenhum` conta zero aqui), não constrói caso
de uso, não toca repositório e não interpreta o conteúdo da proposta. Ele traduz recusa em
código do §A.7 e projeta o agregado — nada mais.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import JSONResponse

from ...dominio.federacao.catalogo import AcaoDesconhecida
from ...dominio.federacao.esquema import ArgumentosInvalidos, EsquemaNaoSuportado
from ...dominio.federacao.principal import Principal
from ...dominio.federacao.proposta import Origem, PropostaDeAcao, TransicaoInvalida
from ...dominio.federacao.traco import AcaoSemTraco
from ..dependencias import obter_principal
from ..erros import envelope
from ..esquemas import DecisaoIn, PropostaIn, PropostaOut

roteador = APIRouter(prefix="/toc/propostas", tags=["propostas-de-acao"])

PrincipalDependente = Annotated[Principal, Depends(obter_principal)]


def _recusa(status_http: int, codigo: str, mensagem: str) -> JSONResponse:
    """O envelope `{"error": …}` do §A.7, montado pelo domínio (nunca à mão)."""
    return JSONResponse(status_code=status_http, content=envelope(codigo, mensagem))


def _federacao(request: Request):
    return request.app.state.composicao.federacao


def _titulo(request: Request, action_id: str) -> str:
    """O título vem do CATÁLOGO, não do cliente: a tela mostra o que o servidor declara."""
    try:
        return _federacao(request).catalogo.acao(action_id).title
    except AcaoDesconhecida:  # pragma: no cover - a proposta só existe se a ação existia
        return action_id


def _projetar(request: Request, proposta: PropostaDeAcao) -> PropostaOut:
    return PropostaOut.de(proposta, titulo=_titulo(request, proposta.action_id))


@roteador.post("", status_code=status.HTTP_201_CREATED, response_model=PropostaOut)
def propor(corpo: PropostaIn, request: Request, principal: PrincipalDependente):
    """A proposta nasce — e **espera**, quando a ação é mutadora (P2, APH-5.2).

    Nada é escrito aqui. Uma ação de risco `read` executa direto (é o que o APH-5.2
    permite, e o desfecho já volta na resposta); uma de risco `confirm` para em
    `awaiting_approval` e só a decisão a move.
    """
    try:
        resultado = _federacao(request).propor_acao.rodar(
            principal=principal,
            action_id=corpo.action_id,
            args=corpo.args,
            origem=Origem(corpo.origem),
            contexto_hash=corpo.contexto_hash,
        )
    except AcaoDesconhecida:
        # §B.7.3: "não existe" e "existe e você não pode" respondem IGUAL — distinguir os
        # dois entregaria o inventário de quem tem mais permissão.
        return _recusa(404, "ACTION_NOT_FOUND", "ação indisponível para este principal")
    except (ArgumentosInvalidos, EsquemaNaoSuportado) as erro:
        return _recusa(400, "INVALID_ARGUMENT", str(erro))
    except AcaoSemTraco as erro:
        # APH-5.5: sem sumidouro de traço não há execução — e a recusa é antes do efeito.
        return _recusa(503, "UNAUTHORIZED", str(erro))
    return _projetar(request, resultado.proposta)


@roteador.post("/{proposal_id}/decisao", response_model=PropostaOut)
def decidir(proposal_id: str, corpo: DecisaoIn, request: Request, principal: PrincipalDependente):
    """O gate humano. Confirmar executa; recusar encerra — e as duas deixam traço.

    Recusa silenciosa é defeito (RI-04 da spec 006): a resposta traz o desfecho nos dois
    casos, e é ele que a tela mostra.
    """
    try:
        resultado = _federacao(request).decidir_proposta.rodar(
            principal=principal,
            proposal_id=proposal_id,
            aprovado=corpo.aprovado,
            contexto_hash=corpo.context_hash,
            idempotency_key=corpo.idempotency_key,
        )
    except AcaoDesconhecida:
        # Proposta de outro inquilino é indistinguível de inexistente — a mesma fronteira
        # do M1, e pelo motivo mais forte: uma proposta alheia é uma mutação alheia à
        # espera de confirmação.
        return _recusa(404, "PROPOSAL_NOT_FOUND", "proposta inexistente para este principal")
    except TransicaoInvalida as erro:
        # `INVALID_TRANSITION`, `PROPOSAL_EXPIRED` e `PROPOSAL_CONTEXT_STALE` saem daqui
        # com o código que o próprio domínio nomeou: a borda traduz, nunca adivinha.
        return _recusa(erro.http, erro.codigo, erro.detalhe)
    except AcaoSemTraco as erro:
        return _recusa(503, "UNAUTHORIZED", str(erro))
    return _projetar(request, resultado.proposta)
