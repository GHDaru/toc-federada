"""A composição da federação — um lugar só monta a fronteira inteira.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **TTL** — *Time To Live* (tempo de vida) ·
**HTTP** — *HyperText Transfer Protocol* · **ARA** — Árvore da Realidade Atual.

Existe pelo mesmo motivo da `Composicao` do `http/app.py`: a borda é o único lugar
autorizado a conhecer as quatro camadas, e concentrar a montagem num objeto torna óbvio o
que a fronteira precisa para funcionar. Um caso de uso que passe a exigir uma porta nova
quebra **aqui**, na composição, e não numa rota em produção.

A escolha do adaptador de introspecção segue a regra da admissão: **com** os parâmetros do
§B.4, o adaptador é o de verdade (HTTP servidor a servidor); **sem** eles, o serviço está
em modo de desenvolvimento e não há introspecção nenhuma — toda sessão é anônima, e o
catálogo composto é vazio. Fail-closed também no modo de desenvolvimento: nunca existe um
"principal de mentira" com capabilities.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import timedelta
from typing import Any

from ...aplicacao.federacao.acoes import DecidirProposta, ProporAcao
from ...aplicacao.federacao.catalogo import ComporCatalogo
from ...aplicacao.federacao.identidade import EstabelecerIdentidade
from ...aplicacao.politica import PoliticaDeAutorizacao, PoliticaPorCapability
from ...dominio.federacao.admissao import Admissao
from ...dominio.federacao.catalogo import CATALOGO_TOC, Catalogo
from ...dominio.federacao.telas import REGISTRO_DE_TELAS, RegistroDeTelas
from ...dominio.portas import Rastreador, Relogio, RepositorioDeARA, RepositorioDeProjetos
from .executor import ExecutorDoCatalogo
from .introspeccao import IntrospeccaoHttp
from .limitador import LimitadorDeTaxa
from .memoria import (
    IdentificadoresUuid,
    RegistroDeSessoesDeAplicacao,
    RepositorioDePropostasEmMemoria,
    RepositorioDeSessoesEmMemoria,
    RepositorioDeTracoEmMemoria,
)
from .motor_local import MotorDeConversaLocal
from .repositorio_sql import RepositorioDePropostasSQL, RepositorioDeTracoSQL

# TTL da proposta em `awaiting_approval` (DÚVIDA 2 da spec 006, proposta a aprovar no gate):
# dez minutos — tempo de ler um lote de oito com calma sem deixar gate pendurado.
TTL_DA_PROPOSTA = timedelta(minutes=10)


class IntrospeccaoAusente:
    """Modo de desenvolvimento: não há fundação, logo não há identidade — e ponto.

    Ela levanta em vez de devolver um principal de mentira, porque um principal de mentira
    com capabilities seria exatamente a "janela de acesso sem dono" que a RF-10 fecha.
    """

    def trocar_grant(self, grant: str):  # noqa: ANN201
        from ...dominio.federacao.principal import IntrospeccaoInvalida

        raise IntrospeccaoInvalida(
            "FUNDACAO_INDISPONIVEL",
            "serviço em modo de desenvolvimento (sem parâmetros de admissão do §B.4): "
            "não há introspecção configurada, então não há identidade",
        )


@dataclass
class ComposicaoDaFederacao:
    """Tudo o que a superfície APH precisa, montado uma vez."""

    catalogo: Catalogo
    registro_de_telas: RegistroDeTelas
    sessoes: RepositorioDeSessoesEmMemoria
    propostas: Any
    tracos: Any
    identificadores: IdentificadoresUuid
    motor: MotorDeConversaLocal
    limitador: LimitadorDeTaxa
    estabelecer_identidade: EstabelecerIdentidade
    compor_catalogo: ComporCatalogo
    propor_acao: ProporAcao
    decidir_proposta: DecidirProposta
    sessoes_de_aplicacao: Any
    intervalo_do_turno: float
    turnos: dict[str, Any] = field(default_factory=dict)


def compor_federacao(
    *,
    rastreador: Rastreador,
    relogio: Relogio,
    projetos: RepositorioDeProjetos,
    aras: RepositorioDeARA | None,
    admissao: Admissao | None,
    nuvens: Any | None = None,
    motor_de_geracao: Any | None = None,
    intervalo_do_turno: float,
    motor_do_banco: Any | None = None,
    politica: PoliticaDeAutorizacao | None = None,
    propostas=None,
    tracos=None,
) -> ComposicaoDaFederacao:
    introspeccao = (
        IntrospeccaoHttp(
            url=admissao.url_de_introspeccao, credencial=admissao.credencial_da_aplicacao
        )
        if admissao is not None
        else IntrospeccaoAusente()
    )
    # A governança é persistida quando há banco — proposta e traço têm tabela e migração
    # (0004). Sem `DATABASE_URL` o serviço roda em memória, e o `/saude` já declara isso.
    if propostas is None or tracos is None:
        if motor_do_banco is not None:
            from ..persistencia.motor import criar_fabrica_de_sessao

            fabrica = criar_fabrica_de_sessao(motor_do_banco)
            propostas = propostas if propostas is not None else RepositorioDePropostasSQL(fabrica)
            tracos = tracos if tracos is not None else RepositorioDeTracoSQL(fabrica)
        else:
            propostas = propostas if propostas is not None else RepositorioDePropostasEmMemoria()
            tracos = tracos if tracos is not None else RepositorioDeTracoEmMemoria()
    identificadores = IdentificadoresUuid()
    executor = ExecutorDoCatalogo(
        rastreador=rastreador,
        projetos=projetos,
        aras=aras,
        # O mesmo adaptador atende as três portas (M1, M2 e M3); o domínio continua com
        # três, que é o que impede a assinatura do núcleo de mencionar premissa e injeção.
        nuvens=nuvens if nuvens is not None else aras,
        # E as três portas do M4 (ARF, APR e AT). O mesmo adaptador atende as seis; o
        # domínio continua com seis, que é o que impede a assinatura do núcleo de
        # mencionar ramo negativo, par obstáculo↔objetivo e ficha de passo.
        arvores=aras,
        # E a porta do M6 (spec 009). O mesmo adaptador atende as sete; o domínio continua
        # com sete, que é o que impede a assinatura do núcleo de mencionar ciclo de
        # focalização, restrição e decisão herdada.
        focalizacoes=aras,
        motor_de_geracao=motor_de_geracao,
        relogio=relogio,
    )
    comum = dict(
        rastreador=rastreador,
        catalogo=CATALOGO_TOC,
        propostas=propostas,
        tracos=tracos,
        executor=executor,
        relogio=relogio,
        identificadores=identificadores,
        politica=politica or PoliticaPorCapability(),
        ttl=TTL_DA_PROPOSTA,
    )
    return ComposicaoDaFederacao(
        catalogo=CATALOGO_TOC,
        registro_de_telas=REGISTRO_DE_TELAS,
        sessoes=RepositorioDeSessoesEmMemoria(),
        propostas=propostas,
        tracos=tracos,
        identificadores=identificadores,
        motor=MotorDeConversaLocal(),
        limitador=LimitadorDeTaxa(),
        estabelecer_identidade=EstabelecerIdentidade(
            rastreador=rastreador, introspeccao=introspeccao, relogio=relogio
        ),
        compor_catalogo=ComporCatalogo(rastreador=rastreador, catalogo=CATALOGO_TOC),
        propor_acao=ProporAcao(**comum),
        decidir_proposta=DecidirProposta(**comum),
        sessoes_de_aplicacao=RegistroDeSessoesDeAplicacao(),
        intervalo_do_turno=intervalo_do_turno,
    )
