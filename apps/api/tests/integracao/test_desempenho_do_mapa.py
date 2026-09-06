"""RNF-05: abrir o mapa da jornada de uma análise madura fica abaixo de 1 s no p95.

Siglas, uma vez neste arquivo: **M6** — Focalização · **ARA** — Árvore da Realidade Atual
· **NC** — Nuvem de Conflito · **APR** — Árvore de Pré-Requisitos · **AT** — Árvore de
Transição · **RNF** — requisito não funcional · **SQL** — *Structured Query Language* ·
**p95** — percentil 95.

**Por que este arquivo existe.** A spec 009 declara um alvo numérico (RNF-05: "abrir o
mapa da jornada de uma análise com 5 ciclos e 30 vínculos, p95 < 1 s") e um alvo numérico
sem medição é uma intenção. A medição vive aqui, contra o PostgreSQL real, e não num
caderno: o `qa-report.md` cola o que este teste imprimiu.

**O que ele NÃO mede** — limite declarado, não escondido: não mede latência de rede, nem
serialização HTTP, nem o navegador. Mede o caminho que o módulo controla — a leitura do
agregado pela porta e o mapa da jornada, que é função pura sobre ele. O alvo da spec é do
caminho inteiro; este é o piso dele, e o resto é do ciclo que instrumentar a borda.

**Por que o limite do teste é folgado.** A máquina de CI (integração contínua) não é a de
produção, e um teste de desempenho que reprova por ruído de vizinho ensina a desligá-lo.
O alvo da spec (1 s) é a barra do produto; a asserção aqui é 3 s, e o número medido —
não o limite — é o que vai para o relatório.
"""
from __future__ import annotations

import time
from statistics import median
from uuid import uuid4

import pytest

from toc_api.dominio.focalizacao import (
    SistemaAnalisado,
    TipoDeFerramentaVinculada,
    TipoDePasso,
    TipoDeRestricao,
    VereditoDeHeranca,
    mapa_da_jornada,
    nova_analise_de_focalizacao,
)
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.persistencia.fabrica import criar_persistencia

from ..dominio.focalizacao_sintetica import (
    AGORA,
    AUTORA,
    DESCRICAO_DO_SISTEMA,
    DONO,
    JUSTIFICATIVA_DA_RESTRICAO,
    NOME,
    SISTEMA,
    depois,
)

pytestmark = pytest.mark.integracao

#: 5 ciclos × 6 vínculos = 30, exatamente o cenário que a RNF-05 nomeia.
CICLOS = 5
VINCULOS_POR_CICLO = 6
LEITURAS = 40
#: Folga sobre o alvo de produto (1 s), pelo motivo escrito no cabeçalho.
TETO_DA_ASSERCAO_S = 3.0

#: Um vínculo por passo canônico, mais dois fora do canônico com justificativa (RN-06) —
#: a análise madura tem as duas espécies, e a não-canônica custa a justificativa.
VINCULOS = (
    (TipoDePasso.IDENTIFICAR, TipoDeFerramentaVinculada.ARA, ""),
    (TipoDePasso.EXPLORAR, TipoDeFerramentaVinculada.NC, ""),
    (TipoDePasso.SUBORDINAR, TipoDeFerramentaVinculada.NC, ""),
    (TipoDePasso.ELEVAR, TipoDeFerramentaVinculada.APR, ""),
    (TipoDePasso.ELEVAR, TipoDeFerramentaVinculada.AT, ""),
    (TipoDePasso.IDENTIFICAR, TipoDeFerramentaVinculada.ARF, "a ARF do ciclo anterior é o contexto"),
)


def test_o_mapa_de_uma_analise_com_cinco_ciclos_e_trinta_vinculos_abre_rapido(
    url_postgres, esquema_migrado
) -> None:
    persistencia = criar_persistencia(
        Configuracao.do_ambiente({"DATABASE_URL": url_postgres, "TOC_DB_SCHEMA": esquema_migrado})
    )
    repositorio = persistencia.projetos

    analise = nova_analise_de_focalizacao(
        id=uuid4(),
        dono=DONO,
        nome=NOME,
        sistema=SistemaAnalisado(nome=SISTEMA, descricao=DESCRICAO_DO_SISTEMA),
        em=AGORA,
    )

    vinculos_criados = 0
    for volta in range(CICLOS):
        base = volta * 100
        analise.registrar_restricao(
            descricao=f"a fila do posto {volta + 1}",
            tipo=TipoDeRestricao.FISICA,
            justificativa=JUSTIFICATIVA_DA_RESTRICAO,
            autor=AUTORA,
            em=depois(base + 5),
        )
        for passo, ferramenta, motivo in VINCULOS:
            analise.vincular_ferramenta(
                passo,
                vinculo_id=uuid4(),
                tipo=ferramenta,
                projeto_id=uuid4(),
                papel=f"volta {volta + 1}",
                justificativa=motivo,
                em=depois(base + 6),
            )
            vinculos_criados += 1
        analise.concluir_passo(
            TipoDePasso.IDENTIFICAR, decisao=f"a restrição da volta {volta + 1}",
            autor=AUTORA, em=depois(base + 10),
        )
        analise.julgar_todas_as_herancas(
            veredito=VereditoDeHeranca.MANTIDA,
            justificativa="revisada e ainda válida",
            autor=AUTORA,
            em=depois(base + 12),
        )
        analise.concluir_passo(
            TipoDePasso.EXPLORAR, decisao="explorar sem investir", autor=AUTORA,
            em=depois(base + 20),
        )
        analise.concluir_passo(
            TipoDePasso.SUBORDINAR, decisao="tudo o mais serve a ela", autor=AUTORA,
            em=depois(base + 30),
        )
        analise.concluir_passo(
            TipoDePasso.ELEVAR, decisao="elevada", autor=AUTORA, em=depois(base + 40)
        )
        if volta < CICLOS - 1:
            analise.recomecar(em=depois(base + 50))

    repositorio.salvar_focalizacao(analise)

    assert vinculos_criados == 30, "o cenário da RNF-05 é 30 vínculos"
    assert len(analise.ciclos) == CICLOS

    amostras: list[float] = []
    for _ in range(LEITURAS):
        inicio = time.perf_counter()
        lida = repositorio.obter_focalizacao(DONO.inquilino_id, analise.id)
        assert lida is not None
        mapa = mapa_da_jornada(lida)
        amostras.append(time.perf_counter() - inicio)

    amostras.sort()
    p95 = amostras[int(round(0.95 * (len(amostras) - 1)))]
    print(
        f"\nRNF-05 · {CICLOS} ciclos · {vinculos_criados} vínculos · {LEITURAS} leituras"
        f" · mediana {median(amostras) * 1000:.1f} ms"
        f" · p95 {p95 * 1000:.1f} ms"
        f" · máximo {amostras[-1] * 1000:.1f} ms"
        f" · passos no mapa {len(mapa.passos)}"
    )
    assert p95 < TETO_DA_ASSERCAO_S, f"p95 = {p95:.3f}s"
