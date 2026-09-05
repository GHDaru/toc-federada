"""As dependências da borda: quem é o pedido, e com que executor ele fala.

**O que este módulo faz**: lê o cabeçalho `Authorization`, troca o token por identidade
**na porta** `ProvedorDeIdentidade` e monta o `Executor` da camada de aplicação.

**O que este módulo NÃO faz, e a ausência é o ponto**: decidir acesso. Nenhuma linha aqui
pergunta se o principal pode alguma coisa. O §B.7.2 do Anexo B do Padrão APH (Aplicação ↔
Harness) manda que a verificação aconteça nos casos de uso, e registra que auditar
autorização por `Depends(...)` na rota "produz falso positivo sistemático". O teste
`tests/aplicacao/test_governanca_de_capacidades.py::test_a_camada_http_nao_decide_acesso_em_lugar_nenhum`
conta as chamadas que decidem acesso nesta camada por árvore sintática e exige zero.

Autenticar não é autorizar: dizer "não sei quem é você" é `401` e mora aqui; dizer "sei
quem é você e você não pode" é `403` e mora no caso de uso.
"""
from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Request

from ..aplicacao.governanca import Executor
from ..dominio.federacao.principal import Principal
from .erros import NaoAutenticado

ESQUEMA_BEARER = "bearer"


def token_do_cabecalho(cabecalho: str | None) -> str | None:
    """`Authorization: Bearer <token>` → o token. Qualquer outra coisa → `None`.

    Função pura, testável sem requisição. O esquema é comparado sem caixa porque o
    RFC 7235 o define assim, e um cliente que mande `bearer` minúsculo está certo.
    """
    if not cabecalho:
        return None
    partes = cabecalho.split(None, 1)
    if len(partes) != 2 or partes[0].lower() != ESQUEMA_BEARER:
        return None
    token = partes[1].strip()
    return token or None


def obter_principal(request: Request) -> Principal:
    """Troca o token pela identidade. Sem token válido, `401` — sem dizer por quê.

    O §B.6.5 proíbe distinguir "inexistente" de "expirado" de "já consumido", e é por isso
    que ausência de cabeçalho e token desconhecido terminam na MESMA exceção: manter a
    distinção aqui devolveria pelo status o oráculo que o corpo não devolve.
    """
    composicao = request.app.state.composicao
    token = token_do_cabecalho(request.headers.get("authorization"))
    if token is None:
        raise NaoAutenticado()
    principal = composicao.identidade.identificar(token)
    if principal is None:
        raise NaoAutenticado()
    return principal


def obter_executor(request: Request, principal: Annotated[Principal, Depends(obter_principal)]) -> Executor:
    """Monta o único caminho por onde um caso de uso roda.

    A rota recebe o `Executor` e **não** recebe o repositório, o relógio nem o rastreador:
    sem as portas na mão, ela não consegue montar um caso de uso por fora do ponto de
    verificação. A impossibilidade é estrutural, não disciplinar.
    """
    composicao = request.app.state.composicao
    return Executor(
        principal=principal,
        rastreador=composicao.rastreador,
        repositorio=composicao.projetos,
        relogio=composicao.relogio,
        # A porta da assistência (M3) viaja junto e é injetada **só** nos casos de uso que
        # a pedem no construtor. A rota continua sem poder montar caso de uso por fora: o
        # que ela recebe é o `Executor`, e é ele quem verifica a capacidade antes.
        motor=composicao.motor_de_geracao,
    )


ExecutorDependente = Annotated[Executor, Depends(obter_executor)]
