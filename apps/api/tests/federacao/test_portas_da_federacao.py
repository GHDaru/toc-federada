"""As portas da federação e os portões que as guardam — conformidade e execução.

Siglas: **APH** — Aplicação ↔ Harness · **JSON** — *JavaScript Object Notation*.

Duas coisas aqui, e as duas são "o portão olha para o que promete olhar" (regra R2):

1. **Conformidade estrutural das portas**: cada duplo de teste e cada adaptador de produção
   satisfazem o `typing.Protocol` correspondente. Sem isto, a porta mudaria de forma e só o
   adaptador quebraria — o duplo continuaria verde, e a suíte inteira mediria uma forma que
   já não existe.
2. **O portão do manifesto roda dentro da suíte**, e não só na integração contínua: a
   DoD 11 da spec 006 pede o script; tê-lo também aqui é o que impede o manifesto de
   divergir do schema entre duas execuções da CI.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

from toc_api.dominio.federacao.portas import (
    ExecutorDeAcao,
    GeradorDeIdentificadores,
    MotorDeConversa,
    PortaDeIntrospeccao,
    RepositorioDePropostas,
    RepositorioDeSessoes,
    RepositorioDeTraco,
)
from toc_api.infra.federacao.executor import ExecutorDoCatalogo
from toc_api.infra.federacao.introspeccao import IntrospeccaoHttp
from toc_api.infra.federacao.memoria import (
    IdentificadoresUuid,
    RepositorioDePropostasEmMemoria,
    RepositorioDeSessoesEmMemoria,
    RepositorioDeTracoEmMemoria,
)
from toc_api.infra.federacao.motor_local import MotorDeConversaLocal
from toc_api.infra.federacao.repositorio_sql import (
    RepositorioDePropostasSQL,
    RepositorioDeTracoSQL,
)

from .fakes import (
    ExecutorFalso,
    IdentificadoresFalsos,
    IntrospeccaoFalsa,
    MotorFalso,
    RepositorioDePropostasFalso,
    RepositorioDeSessoesFalso,
    RepositorioDeTracoFalso,
)

RAIZ_DO_REPO = Path(__file__).resolve().parents[4]

CONFORMIDADES = [
    (PortaDeIntrospeccao, IntrospeccaoFalsa()),
    (PortaDeIntrospeccao, IntrospeccaoHttp(url="https://x.exemplo/auth/introspect", credencial="ghd_x")),
    (RepositorioDeSessoes, RepositorioDeSessoesFalso()),
    (RepositorioDeSessoes, RepositorioDeSessoesEmMemoria()),
    (RepositorioDePropostas, RepositorioDePropostasFalso()),
    (RepositorioDePropostas, RepositorioDePropostasEmMemoria()),
    (RepositorioDePropostas, RepositorioDePropostasSQL(fabrica_de_sessao=lambda: None)),
    (RepositorioDeTraco, RepositorioDeTracoFalso()),
    (RepositorioDeTraco, RepositorioDeTracoEmMemoria()),
    (RepositorioDeTraco, RepositorioDeTracoSQL(fabrica_de_sessao=lambda: None)),
    (ExecutorDeAcao, ExecutorFalso()),
    (MotorDeConversa, MotorFalso()),
    (MotorDeConversa, MotorDeConversaLocal()),
    (GeradorDeIdentificadores, IdentificadoresFalsos()),
    (GeradorDeIdentificadores, IdentificadoresUuid()),
]


@pytest.mark.parametrize(("porta", "objeto"), CONFORMIDADES, ids=lambda v: getattr(v, "__name__", type(v).__name__))
def test_o_objeto_conforma_a_porta(porta, objeto) -> None:
    assert isinstance(objeto, porta), f"{type(objeto).__name__} não satisfaz {porta.__name__}"


def test_o_executor_do_catalogo_conforma_a_porta() -> None:
    """Construído à parte porque precisa de repositórios — e é o que a porta esconde."""
    from toc_api.infra.federacao.memoria import IdentificadoresUuid  # noqa: F401
    from toc_api.infra.persistencia.memoria import RepositorioDeProjetosEmMemoria
    from toc_api.infra.relogio import RelogioDoSistema
    from toc_api.infra.observabilidade.otel import RastreadorNulo

    repositorio = RepositorioDeProjetosEmMemoria()
    executor = ExecutorDoCatalogo(
        rastreador=RastreadorNulo(),
        projetos=repositorio,
        aras=repositorio,
        relogio=RelogioDoSistema(),
    )

    assert isinstance(executor, ExecutorDeAcao)


def test_toda_porta_da_federacao_tem_ao_menos_dois_conformantes() -> None:
    """Uma porta com um só implementador é uma interface que ninguém precisou de fato.

    O `ExecutorDeAcao` é a exceção declarada: o duplo está na lista e o real tem teste
    próprio logo acima, porque construí-lo exige repositórios.
    """
    contagem: dict[str, int] = {}
    for porta, _ in CONFORMIDADES:
        contagem[porta.__name__] = contagem.get(porta.__name__, 0) + 1
    contagem["ExecutorDeAcao"] += 1  # o real, verificado no teste acima

    medida = f"portas da federação conferidas: {len(contagem)}; conformantes: {contagem}"
    print(medida)
    magras = [nome for nome, quantos in contagem.items() if quantos < 2]
    assert magras == [], medida


def test_o_portao_do_manifesto_roda_e_repele_as_sabotagens() -> None:
    """DoD 11 da spec 006, dentro da suíte — e com a saída do portão colada na falha."""
    executado = subprocess.run(
        [str(RAIZ_DO_REPO / "scripts/check-manifesto.sh")],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert executado.returncode == 0, executado.stdout + executado.stderr
    assert "manifesto aceito pelo schema normativo — 0 erro" in executado.stdout
    assert "sabotagens aplicadas: 7; repelidas: 7" in executado.stdout


def test_o_portao_da_politica_recusa_a_sabotagem_no_codigo_de_producao() -> None:
    executado = subprocess.run(
        [str(RAIZ_DO_REPO / "scripts/check-politica.sh")],
        capture_output=True,
        text=True,
        timeout=120,
    )

    assert executado.returncode == 0, executado.stdout + executado.stderr


def test_o_portao_do_canal_roda_os_testes_do_ghd() -> None:
    """O canal é JavaScript e não entra no pytest — mas o portão dele, sim."""
    executado = subprocess.run(
        [str(RAIZ_DO_REPO / "scripts/check-canal.sh")],
        capture_output=True,
        text=True,
        timeout=180,
    )

    assert executado.returncode == 0, executado.stdout + executado.stderr
    assert "# fail 0" in executado.stdout
