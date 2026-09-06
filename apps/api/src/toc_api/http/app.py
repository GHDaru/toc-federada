"""A casca HTTP — só o que o esqueleto precisa: composição e um endpoint de saúde.

As rotas de conteúdo (`/projetos`, `/aph/*`, o fio SSE) nascem nos ciclos 003, 004 e 006.
O que existe aqui é a **composição**: um lugar que lê a configuração, monta a persistência
e o traço, e os entrega. É o único lugar do serviço autorizado a conhecer as quatro
camadas — o contrato P3-3 do `import-linter` diz isso em forma de aptidão.

`/saude` não é enfeite: é o que responde "qual backend está de pé e em que migração", e
foi a ausência dessa resposta que deixou a fundação publicar `persistence: in-memory` com
contas de repositório abertas (spec 056 de lá, lida em
`apps/api/src/ghdaru_api/persistence/factory.py`).
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Any

from fastapi import FastAPI

from ..dominio.portas import Rastreador, RepositorioDeProjetos
from ..infra.configuracao import Configuracao
from ..infra.observabilidade.otel import configurar_traco
from ..dominio.federacao.admissao import Admissao, AdmissaoRecusada, exigir_admissao
from ..dominio.portas import ProvedorDeIdentidade
from ..infra.federacao.composicao import ComposicaoDaFederacao, compor_federacao
from ..infra.geracao.motor_local import MotorDeGeracaoLocal
from ..infra.identidade.falso import criar_provedor_de_identidade
from ..infra.persistencia.fabrica import Persistencia, criar_persistencia
from ..infra.relogio import RelogioDoSistema
from . import erros as tradutores
from .aph import INTERVALO_DO_TURNO_S, criar_router_aph
from .roteadores import arvores as roteadores_do_m4
from .roteadores import cadeia as roteador_da_cadeia
from .roteadores import focalizacao as roteador_da_focalizacao
from .roteadores import projetos as roteador_de_projetos
from .roteadores import ara as roteador_da_ara
from .roteadores import nuvem as roteador_da_nuvem
from .roteadores import propostas as roteador_de_propostas


@dataclass(frozen=True)
class Composicao:
    """Tudo o que a borda monta uma vez e injeta nos casos de uso."""

    config: Configuracao
    persistencia: Persistencia
    rastreador: Rastreador
    relogio: RelogioDoSistema
    identidade: ProvedorDeIdentidade
    #: Os parâmetros do §B.4 do Anexo B quando presentes; `None` = modo de desenvolvimento.
    admissao: Admissao | None = None
    #: A fronteira APH (Aplicação ↔ Harness) inteira: catálogo, propostas, traço e fio.
    federacao: ComposicaoDaFederacao | None = None
    #: A porta da assistência do M3 (`MotorDeGeracaoDeNuvem`). O adaptador desta fase é
    #: local e determinístico, e **declara-se** como tal no `/saude`: nenhum provedor de
    #: inteligência artificial é chamado de dentro deste produto (ADR 0007).
    motor_de_geracao: Any | None = None

    @property
    def projetos(self) -> RepositorioDeProjetos:
        return self.persistencia.projetos


def compor(ambiente: dict[str, str] | None = None) -> Composicao:
    # `is None`, e não `ambiente or os.environ`: um dicionário VAZIO é falso em Python, e
    # a versão com `or` fazia "compor sem nenhuma variável" cair silenciosamente no
    # ambiente do processo. O defeito só apareceu porque um `export DATABASE_URL` no shell
    # mudou o resultado de um teste que passava o ambiente explicitamente — que é
    # exatamente a classe de bug que some quando a máquina de quem testa é limpa.
    bruto = dict(os.environ if ambiente is None else ambiente)
    config = Configuracao.do_ambiente(bruto)
    persistencia = criar_persistencia(config)
    rastreador = configurar_traco(config)
    relogio = RelogioDoSistema()

    # A admissão do §B.4 é **opcional aqui e obrigatória no arranque** (`arranque.py`), e a
    # assimetria é deliberada: a recusa de subir é do processo (RF-04 da spec 003 — código
    # de saída diferente de zero, sem abrir porta), e esta função monta um objeto, que não
    # "sobe". Sem os parâmetros o serviço fica em **modo de desenvolvimento**: sem
    # introspecção, logo sem identidade da fundação, logo com catálogo composto vazio. É
    # fail-closed, não permissivo — e o `/saude` diz em qual dos dois estados ele está.
    try:
        admissao = exigir_admissao(bruto)
    except AdmissaoRecusada:
        admissao = None

    return Composicao(
        motor_de_geracao=MotorDeGeracaoLocal(),
        config=config,
        persistencia=persistencia,
        rastreador=rastreador,
        relogio=relogio,
        identidade=criar_provedor_de_identidade(config),
        admissao=admissao,
        federacao=compor_federacao(
            rastreador=rastreador,
            relogio=relogio,
            projetos=persistencia.projetos,
            aras=persistencia.projetos,
            admissao=admissao,
            intervalo_do_turno=_intervalo_do_turno(bruto),
            motor_do_banco=persistencia.motor,
        ),
    )


def _intervalo_do_turno(ambiente: dict[str, str]) -> float:
    """O passo entre eventos do turno do fio, em segundos.

    Não é ajuste de desempenho: é o que permite ao teste de contrato exercitar o fio com
    intervalo perto de zero enquanto o serviço real mantém um turno com duração suficiente
    para alguém conseguir cancelá-lo — cancelamento cooperativo (APH-1.4) só existe
    enquanto há o que cancelar.
    """
    bruto = (ambiente.get("TOC_INTERVALO_DO_TURNO_MS") or "").strip()
    if not bruto:
        return INTERVALO_DO_TURNO_S
    try:
        return max(0.0, float(bruto) / 1000.0)
    except ValueError:
        return INTERVALO_DO_TURNO_S


def criar_app(ambiente: dict[str, str] | None = None) -> FastAPI:
    composicao = compor(ambiente)
    app = FastAPI(
        title="toc-api",
        version="0.1.0",
        summary="Serviço da toc-federada — Processos de Pensamento da Teoria das Restrições",
    )
    app.state.composicao = composicao
    tradutores.registrar_tradutores(app)
    app.include_router(roteador_de_projetos.roteador)
    app.include_router(roteador_da_ara.roteador)
    app.include_router(roteador_da_nuvem.roteador)
    # M4 — as três árvores e o encadeamento (spec 008). Três roteadores e não um: ARF, APR
    # e AT têm lógicas distintas (suficiência × necessidade × precedência), e um prefixo
    # comum convidaria a rota compartilhada — onde as lógicas se misturariam (RN-05).
    app.include_router(roteadores_do_m4.arf)
    app.include_router(roteadores_do_m4.apr)
    app.include_router(roteadores_do_m4.at)
    app.include_router(roteador_da_cadeia.roteador)
    # M6 — a jornada dos cinco passos (spec 009). Roteador próprio e não uma rota do M1:
    # a análise de focalização não é diagrama, e as operações dela — registrar restrição,
    # concluir passo, julgar herança, recomeçar — não têm par no núcleo.
    app.include_router(roteador_da_focalizacao.roteador)
    # O gate humano visto pela própria interface: a proposta de ação nasce e é
    # decidida aqui, pelos MESMOS casos de uso que o fio usa (spec 006, RI-01).
    app.include_router(roteador_de_propostas.roteador)
    # A superfície APH: fio do Anexo A (sessões, SSE, replay, cancelamento), catálogo
    # `toc.*`, decisão de proposta, borda federada e traço auditável.
    app.include_router(criar_router_aph(composicao))

    @app.get("/saude")
    def saude() -> dict[str, Any]:
        # A cadeia de conexão NUNCA sai daqui: `url_redigida` já removeu a credencial (P7).
        return {
            "servico": composicao.config.nome_do_servico,
            "ambiente": composicao.config.ambiente,
            "persistencia": composicao.persistencia.backend,
            "banco": composicao.config.url_redigida,
            "traco": type(composicao.rastreador).__name__,
            # Qual adaptador de geração está montado. `local-deterministico` significa
            # "sem fundação repassando o modelo": a assistência do M3 é um duplo local e
            # declarado, e é melhor que isso apareça aqui do que seja suposto.
            "geracao": getattr(composicao.motor_de_geracao, "nome", None),
            # Qual adaptador de identidade está de pé. `ProvedorQueNegaTudo` significa
            # "sem introspecção montada: ninguém entra" — e é melhor que isso apareça no
            # `/saude` do que seja descoberto por uma tela em branco.
            "identidade": type(composicao.identidade).__name__,
            # Admitida (os quatro parâmetros do §B.4 mais os dois nossos estão presentes)
            # ou em modo de desenvolvimento (sem fundação, logo sem identidade dela).
            "admissao": "admitida" if composicao.admissao else "ausente (desenvolvimento)",
            "app_id": composicao.admissao.app_id if composicao.admissao else None,
        }

    return app
