"""Status do passo e acompanhamento — o E5.2 da spec 010.

Siglas, uma vez neste arquivo: **S&T** — Estratégia & Táticas (*Strategy & Tactics*) ·
**M5** — o módulo da S&T · **RN/RF** — regra de negócio / requisito funcional da spec 010
· **ADR** — *Architecture Decision Record* (Registro de Decisão Arquitetural).

Os quatro valores vêm verbatim da linhagem (`tocbuilderv3/types.ts:270-275`), onde já
eram portugueses: `'Nenhum'`, `'Validado'`, `'Não Validado'`, `'Em Execução'`. O que a
linhagem **não** tinha é o que este arquivo prova: **autor e data a cada mudança** (RN-03).

Sobre a política de transição: ela é **livre entre os quatro**, e isso foi decidido, não
esquecido — [DÚVIDA] 2 da spec 010, resolvida no ADR 0014. Impor "só executa depois de
validado" travaria a reunião real em que o plano já está em execução quando a validação
formal sai. O que **falha** são as transições que não querem dizer nada: mudar para o
valor que já está, mudar sem dizer quem mudou, e valor fora do vocabulário fechado.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.erros import MutacaoRecusada
from toc_api.dominio.eventos import StatusDoPassoMudou
from toc_api.dominio.snt import StatusDoPasso, TransicaoDeStatusRecusada

from .snt_sintetica import AGORA, STATUS_NA_REUNIAO
from .test_snt import plano_completo


def test_os_quatro_valores_sao_os_da_linhagem() -> None:
    valores = [s.value for s in StatusDoPasso]
    print(f"valores={valores}")
    assert valores == ["nenhum", "validado", "nao_validado", "em_execucao"]


def test_o_passo_nasce_no_status_nenhum() -> None:
    a, chaves = plano_completo()
    print(f"status inicial={a.ficha(chaves['1']).status.value!r}")
    assert a.ficha(chaves["1"]).status is StatusDoPasso.NENHUM


def test_mudar_status_registra_autor_e_data_no_evento() -> None:
    """RN-03: a linhagem mudava status sem registrar quem. Aqui o evento carrega os dois."""
    a, chaves = plano_completo()
    a.mudar_status(chaves["1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA)
    evento = [e for e in a.eventos if isinstance(e, StatusDoPassoMudou)][-1]
    print(
        f"evento: de={evento.de!r} para={evento.para!r} autor={evento.autor!r} "
        f"instante={evento.instante.isoformat()}"
    )
    assert (evento.de, evento.para, evento.autor) == ("nenhum", "validado", "u-gestora")
    assert evento.instante == AGORA


def test_as_doze_transicoes_entre_valores_distintos_sao_livres() -> None:
    """RN-03/[DÚVIDA] 2: 4×3 = 12 transições, todas aceitas — e a contagem é a evidência."""
    a, chaves = plano_completo()
    alvo = chaves["1.3"]
    aceitas = 0
    for de in StatusDoPasso:
        for para in StatusDoPasso:
            if de is para:
                continue
            # Coloca o passo em `de` sem passar pela regra de "sem mudança".
            if a.ficha(alvo).status is not de:
                a.mudar_status(alvo, de, autor="u-gestora", em=AGORA)
            a.mudar_status(alvo, para, autor="u-gestora", em=AGORA)
            aceitas += 1
    print(f"transições entre valores distintos examinadas: {aceitas} · recusadas: 0")
    assert aceitas == 12


def test_mudar_para_o_mesmo_status_e_recusado() -> None:
    a, chaves = plano_completo()
    a.mudar_status(chaves["1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA)
    with pytest.raises(TransicaoDeStatusRecusada) as erro:
        a.mudar_status(chaves["1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA)
    print(f"recusa: motivo={erro.value.motivo!r}")
    assert erro.value.motivo == "sem_mudanca"


def test_mudar_status_sem_autor_e_recusado() -> None:
    """RN-03: status sem autor é o que a linhagem tinha — e é o que não atravessa."""
    a, chaves = plano_completo()
    with pytest.raises(TransicaoDeStatusRecusada) as erro:
        a.mudar_status(chaves["1.1"], StatusDoPasso.VALIDADO, autor="   ", em=AGORA)
    print(f"recusa: motivo={erro.value.motivo!r}")
    assert erro.value.motivo == "autor_obrigatorio"


def test_status_fora_do_vocabulario_fechado_e_recusado() -> None:
    a, chaves = plano_completo()
    with pytest.raises(ValueError) as erro:
        a.mudar_status(chaves["1.1"], "concluido", autor="u-gestora", em=AGORA)
    print(f"recusa: {erro.value}")


def test_a_recusa_nao_muda_nada_no_agregado() -> None:
    a, chaves = plano_completo()
    antes = (a.ficha(chaves["1.1"]), a.projeto.versao)
    with pytest.raises(TransicaoDeStatusRecusada):
        a.mudar_status(chaves["1.1"], StatusDoPasso.NENHUM, autor="u-gestora", em=AGORA)
    depois = (a.ficha(chaves["1.1"]), a.projeto.versao)
    print(f"versão antes={antes[1]} depois={depois[1]} · ficha idêntica: {antes[0] == depois[0]}")
    assert antes == depois


# ---------------------------------------------------------------------------------------
# F5.2.2 · o painel de acompanhamento (RF-17, RF-18)
# ---------------------------------------------------------------------------------------


def test_a_reuniao_de_acompanhamento_conta_por_status_e_calcula_progresso() -> None:
    a, chaves = plano_completo()
    for chave, status in STATUS_NA_REUNIAO.items():
        a.mudar_status(chaves[chave], status, autor="u-gestora", em=AGORA)
    resumo = a.pendencias()
    print(
        f"passos examinados={resumo.passos_examinados} · por status={dict(resumo.por_status)} "
        f"· progresso={resumo.progresso:.3f}"
    )
    assert resumo.por_status == {
        "nenhum": 4, "validado": 1, "nao_validado": 1, "em_execucao": 1,
    }
    assert resumo.passos_examinados == 7
    assert resumo.progresso == pytest.approx(1 / 7)


def test_filtrar_por_status_mantem_os_ancestrais_visiveis() -> None:
    """RF-18: sem os ancestrais, o passo filtrado aparece sem o plano que o explica."""
    a, chaves = plano_completo()
    a.mudar_status(chaves["1.1.2"], StatusDoPasso.EM_EXECUCAO, autor="u-gestora", em=AGORA)
    filtrados = a.por_status(StatusDoPasso.EM_EXECUCAO)
    visiveis = a.com_ancestrais(filtrados)
    print(
        f"em execução: {[a.numero(x) for x in filtrados]} · "
        f"visíveis com contexto: {[a.numero(x) for x in visiveis]}"
    )
    assert [a.numero(x) for x in filtrados] == ["1.1.2"]
    assert [a.numero(x) for x in visiveis] == ["1", "1.1", "1.1.2"]


def test_o_projeto_excluido_recusa_mudanca_de_status() -> None:
    a, chaves = plano_completo()
    a.projeto.excluir(em=AGORA)
    with pytest.raises(MutacaoRecusada):
        a.mudar_status(chaves["1.1"], StatusDoPasso.VALIDADO, autor="u-gestora", em=AGORA)
    print("mudança de status recusada sobre projeto excluído")
