"""Admissão (§B.4 do Anexo B, spec 003 RF-01..RF-05) — a aplicação recusa subir.

Um teste por parâmetro ausente, como manda a DoD 1 da spec 003 ("um teste por parâmetro
ausente, asserta código e exit ≠ 0"). O contrato dos códigos é
`specs/003-esqueleto-federado/contracts/parametros-de-admissao.md`; aqui ele vira regra
executável, e a tabela do contrato é lida deste módulo — não copiada para cá à mão, para
não haver duas listas que divergem.
"""
from __future__ import annotations

import pytest

from toc_api.dominio.federacao.admissao import (
    OBRIGATORIOS,
    Admissao,
    AdmissaoRecusada,
    exigir_admissao,
)

AMBIENTE_COMPLETO = {
    "HOST_ORIGIN": "https://plataforma.exemplo",
    "HOST_BASE_URL": "https://api.plataforma.exemplo",
    "APP_ID": "toc",
    "EMBED_URL": "https://toc-federada.exemplo/toc/embarcado",
    "TOC_APP_CREDENTIAL": "ghd_credencial_sintetica",
    "DATABASE_URL": "postgresql+psycopg://toc@/toc_federada",
}


def test_ambiente_completo_admite() -> None:
    admissao = exigir_admissao(AMBIENTE_COMPLETO)

    assert isinstance(admissao, Admissao)
    assert admissao.host_origin == "https://plataforma.exemplo"
    assert admissao.app_id == "toc"


@pytest.mark.parametrize(
    ("variavel", "codigo"),
    [
        ("HOST_ORIGIN", "ADMISSAO_HOST_ORIGIN_AUSENTE"),
        ("HOST_BASE_URL", "ADMISSAO_HOST_BASE_URL_AUSENTE"),
        ("APP_ID", "ADMISSAO_APP_ID_AUSENTE"),
        ("EMBED_URL", "ADMISSAO_EMBED_URL_AUSENTE"),
        ("TOC_APP_CREDENTIAL", "ADMISSAO_CREDENCIAL_AUSENTE"),
        ("DATABASE_URL", "ADMISSAO_DATABASE_URL_AUSENTE"),
    ],
)
def test_cada_ausencia_recusa_nomeando_qual_faltou(variavel: str, codigo: str) -> None:
    ambiente = {k: v for k, v in AMBIENTE_COMPLETO.items() if k != variavel}

    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao(ambiente)

    assert recusa.value.codigo == codigo
    assert recusa.value.parametro == variavel
    # A mensagem NOMEIA o parâmetro: "recuse subir com erro categorizado que diga qual
    # faltou" (§B.4.1). Uma mensagem genérica cumpriria a letra e traía o motivo.
    assert variavel in str(recusa.value)


def test_valor_em_branco_conta_como_ausente() -> None:
    """`HOST_ORIGIN=""` é o defeito de configuração mais comum, e não é presença."""
    ambiente = {**AMBIENTE_COMPLETO, "HOST_ORIGIN": "   "}

    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao(ambiente)

    assert recusa.value.codigo == "ADMISSAO_HOST_ORIGIN_AUSENTE"


def test_a_recusa_nomeia_o_primeiro_ausente_na_ordem_declarada() -> None:
    """Faltando tudo, a recusa é determinística — diagnóstico não pode depender de sorte."""
    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao({})

    assert recusa.value.parametro == OBRIGATORIOS[0].variavel


def test_a_origem_do_hospedeiro_nunca_vem_de_payload() -> None:
    """RF-02: origem descoberta em runtime é origem *dita* (§B.2.3).

    O contraexemplo registrado na norma é ler a origem esperada de `payload.host_origin`.
    A assinatura de `exigir_admissao` é a defesa: ela recebe **um mapa de ambiente**, e a
    única forma de enfiar uma origem de payload aqui seria escrevê-la no ambiente do
    processo — o que já é reconfiguração (§B.4.2), não descoberta.
    """
    ambiente = {**AMBIENTE_COMPLETO}
    del ambiente["HOST_ORIGIN"]
    payload_hostil = {"host_origin": "https://atacante.exemplo"}

    with pytest.raises(AdmissaoRecusada):
        exigir_admissao(ambiente)

    assert "host_origin" not in {k.lower() for k in ambiente}
    assert payload_hostil["host_origin"] not in str(ambiente)


def test_a_credencial_nunca_aparece_na_representacao_da_admissao() -> None:
    """P7/RNF-01: credencial em `repr` cai em log de exceção sem ninguém decidir isso."""
    admissao = exigir_admissao(AMBIENTE_COMPLETO)

    texto = repr(admissao)
    assert "ghd_credencial_sintetica" not in texto
    assert "***" in texto
    # e continua acessível para quem precisa dela (o adaptador de introspecção)
    assert admissao.credencial_da_aplicacao == "ghd_credencial_sintetica"


def test_url_de_introspeccao_e_derivada_da_base_sem_barra_dupla() -> None:
    admissao = exigir_admissao(
        {**AMBIENTE_COMPLETO, "HOST_BASE_URL": "https://api.plataforma.exemplo/"}
    )

    assert admissao.url_de_introspeccao == "https://api.plataforma.exemplo/auth/introspect"


def test_a_url_de_embarque_deve_pertencer_a_origem_declarada() -> None:
    """§B.1.3: divergência entre `EMBED_URL` e a origem publicada é recusa.

    A origem publicada da aplicação é a da própria `EMBED_URL`; o que este teste fixa é
    que uma `EMBED_URL` que não seja `https` — ou que seja de outro esquema — não sobe.
    """
    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao({**AMBIENTE_COMPLETO, "EMBED_URL": "http://toc.exemplo/toc"})

    assert recusa.value.codigo == "ADMISSAO_EMBED_URL_INVALIDA"


def test_a_origem_do_hospedeiro_tem_de_ser_uma_origem_e_nao_uma_url_com_caminho() -> None:
    """Origem é `esquema://host[:porta]`. Comparar `event.origin` com uma URL que tenha
    caminho nunca casa — e o defeito só aparece no embarque real, tarde demais."""
    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao({**AMBIENTE_COMPLETO, "HOST_ORIGIN": "https://plataforma.exemplo/app"})

    assert recusa.value.codigo == "ADMISSAO_HOST_ORIGIN_INVALIDA"


def test_origem_nula_nunca_e_admitida() -> None:
    """RF-21: `"null"` é a origem de qualquer documento opaco (§B.2.3)."""
    with pytest.raises(AdmissaoRecusada) as recusa:
        exigir_admissao({**AMBIENTE_COMPLETO, "HOST_ORIGIN": "null"})

    assert recusa.value.codigo == "ADMISSAO_HOST_ORIGIN_INVALIDA"


def test_o_contrato_versionado_declara_exatamente_os_codigos_do_modulo() -> None:
    """R4/R5: o documento de contrato e o código não podem divergir em silêncio.

    O contrato `specs/003-esqueleto-federado/contracts/parametros-de-admissao.md` é lido
    aqui e cada código obrigatório do módulo tem de aparecer nele. Sem este teste, mudar
    um código deixaria o contrato mentindo — e contrato que mente é pior que contrato
    ausente.
    """
    from pathlib import Path

    raiz = Path(__file__).resolve().parents[4]
    contrato = (
        raiz / "specs/003-esqueleto-federado/contracts/parametros-de-admissao.md"
    ).read_text(encoding="utf-8")

    ausentes = [p.codigo for p in OBRIGATORIOS if p.codigo not in contrato]
    assert ausentes == [], f"códigos fora do contrato versionado: {ausentes}"
