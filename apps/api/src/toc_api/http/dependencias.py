"""As dependências da borda: quem é o pedido, e com que executor ele fala.

**O que este módulo faz**: lê o cabeçalho `Authorization`, troca o token por identidade
**na porta** `ProvedorDeIdentidade` e monta o `Executor` da camada de aplicação.

**O que este módulo NÃO faz, e a ausência é o ponto**: decidir acesso. Nenhuma linha aqui
pergunta se o principal pode alguma coisa. O §B.7.2 do Anexo B do Padrão APH (Aplicação ↔
Harness) manda que a verificação aconteça nos casos de uso, e registra que auditar
autorização por `Depends(...)` na rota "produz falso positivo sistemático". O teste
`apps/api/tests/aplicacao/test_governanca_de_capacidades.py::test_a_camada_http_nao_decide_acesso_em_lugar_nenhum`
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


def resolver_principal(composicao, token: str) -> Principal | None:
    """O ÚNICO resolvedor de portador → identidade da borda. Duas origens legítimas, uma função.

    As duas origens são:

    1. as **sessões abertas por `POST /toc/embarque`** — o grant da fundação já trocado por
       identidade (§B.6 do Anexo B do Padrão APH — Aplicação ↔ Harness);
    2. o **`ProvedorDeIdentidade`** da composição — o adaptador de desenvolvimento, que
       fora de desenvolvimento nega tudo.

    As duas desembocam no MESMO `Principal`, construído pela mesma
    `principal_de_introspeccao`: não há segundo caminho de nascimento de identidade, que é
    o que o P2 e o RF-07 proíbem.

    **Por que esta função existe, e não um trecho repetido em cada lugar.** Havia dois
    resolvedores: este e o `principal_de` de `http/aph.py`. O de `aph.py` consultava as
    duas origens; este consultava só a segunda. O efeito era que o token devolvido pelo
    embarque abria `/aph/catalog` e era recusado por toda rota de produto com `401` — e a
    interface manda exatamente esse token em toda chamada
    (`apps/web/src/api/cliente.ts:119`). Duas cópias de uma regra divergem; a defesa é não
    ter duas. Reprodução colada em
    `apps/api/tests/integracao/test_embarque_com_fundacao_no_postgres.py::
    test_a_sessao_do_embarque_autentica_a_SUPERFICIE_INTEIRA_e_nao_so_o_aph`.

    Identidade **vencida não autentica**, e a sessão é encerrada aqui: deixar a verificação
    de validade só num dos consumidores é a mesma divergência com outro nome.
    """
    federacao = getattr(composicao, "federacao", None)
    sessoes = getattr(federacao, "sessoes_de_aplicacao", None) if federacao else None
    principal = sessoes.principal(token) if sessoes is not None else None
    if principal is None:
        principal = composicao.identidade.identificar(token)
    if principal is None:
        return None
    if principal.expirado_em(composicao.relogio.agora()):
        if sessoes is not None:
            sessoes.encerrar(token)
        return None
    return principal


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
    principal = resolver_principal(composicao, token)
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
