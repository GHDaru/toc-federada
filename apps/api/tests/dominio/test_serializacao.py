"""O codec de domínio: dataclass ↔ documento JSON, sem framework e sem mágica.

Siglas, uma vez neste arquivo: **JSON** — *JavaScript Object Notation* · **UUID** —
identificador único universal · **UDE** — Efeito Indesejável · **TOC** — Teoria das
Restrições.

**Por que um codec e não `pydantic`.** O P3 proíbe o domínio de importar Pydantic,
SQLAlchemy, FastAPI ou httpx — e a exportação consolidada (RF-31 e RF-32 da spec 011) é
**domínio puro**: ela tem de rodar sem rede e sem banco, porque a ida e volta é uma
propriedade do modelo, não do transporte. O que este módulo faz é a parte mecânica —
`UUID` vira texto, `Enum` vira o valor, `datetime` vira ISO 8601, `dataclass` vira
objeto na **ordem de declaração dos campos** — para que os exportadores por ferramenta
digam só o que é decisão: quais seções existem e o que fica de fora.

A ordem importa e é testada: exportação que muda de forma entre duas execuções não serve
para comparar nem para versionar, e a primeira coisa que alguém faz com um export é
comparar dois (a mesma razão escrita em `exportar_analise`, do M6).
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.erros import DadoInvalido
from toc_api.dominio.serializacao import codificar, decodificar


class Cor(str, Enum):
    VERDE = "verde"
    VERMELHO = "vermelho"


@dataclass(frozen=True, slots=True)
class Folha:
    id: UUID
    texto: str = ""
    peso: int = 0


@dataclass(frozen=True, slots=True)
class Galho:
    id: UUID
    cor: Cor
    quando: datetime
    folhas: tuple[Folha, ...] = ()
    apelido: str | None = None
    medidas: dict[str, float] = field(default_factory=dict)


UM = UUID("11111111-1111-4111-8111-111111111111")
DOIS = UUID("22222222-2222-4222-8222-222222222222")
INSTANTE = datetime(2026, 9, 6, 12, 30, tzinfo=timezone.utc)


def test_codifica_uuid_enum_e_instante_como_texto():
    galho = Galho(id=UM, cor=Cor.VERDE, quando=INSTANTE)
    assert codificar(galho) == {
        "id": "11111111-1111-4111-8111-111111111111",
        "cor": "verde",
        "quando": "2026-09-06T12:30:00+00:00",
        "folhas": [],
        "apelido": None,
        "medidas": {},
    }


def test_a_ordem_dos_campos_e_a_da_declaracao_e_nao_muda_entre_execucoes():
    galho = Galho(id=UM, cor=Cor.VERMELHO, quando=INSTANTE, apelido="x")
    assert list(codificar(galho)) == ["id", "cor", "quando", "folhas", "apelido", "medidas"]
    assert list(codificar(galho)) == list(codificar(galho))


def test_ida_e_volta_devolve_o_valor_igual():
    galho = Galho(
        id=UM,
        cor=Cor.VERDE,
        quando=INSTANTE,
        folhas=(Folha(id=DOIS, texto="uma", peso=3),),
        apelido="ramo",
        medidas={"largura": 1.5},
    )
    assert decodificar(Galho, codificar(galho)) == galho


def test_tupla_volta_tupla_e_nao_lista():
    """`tuple` é o que o domínio guarda: uma cópia da coleção não é a coleção."""
    galho = decodificar(Galho, codificar(Galho(id=UM, cor=Cor.VERDE, quando=INSTANTE,
                                               folhas=(Folha(id=DOIS),))))
    assert isinstance(galho.folhas, tuple)


def test_dicionario_com_chave_uuid_volta_com_chave_uuid():
    dado = codificar({UM: Folha(id=DOIS, texto="a")})
    assert dado == {"11111111-1111-4111-8111-111111111111": {"id": str(DOIS), "texto": "a", "peso": 0}}
    assert decodificar(dict[UUID, Folha], dado) == {UM: Folha(id=DOIS, texto="a")}


def test_opcional_ausente_no_documento_cai_no_padrao_do_campo():
    assert decodificar(Folha, {"id": str(UM)}) == Folha(id=UM)


def test_campo_obrigatorio_ausente_e_recusado_dizendo_o_nome():
    with pytest.raises(DadoInvalido) as erro:
        decodificar(Folha, {"texto": "sem id"})
    assert "id" in str(erro.value)


def test_campo_desconhecido_no_documento_e_recusado_e_nao_ignorado():
    """Ignorar campo desconhecido é como a linhagem perdia dado em silêncio (F-09)."""
    with pytest.raises(DadoInvalido) as erro:
        decodificar(Folha, {"id": str(UM), "inventado": 1})
    assert "inventado" in str(erro.value)


def test_tipo_que_o_codec_nao_conhece_falha_alto_em_vez_de_virar_texto():
    with pytest.raises(DadoInvalido):
        codificar(object())


def test_valor_fora_do_vocabulario_do_enum_e_recusado():
    with pytest.raises(DadoInvalido) as erro:
        decodificar(Galho, {"id": str(UM), "cor": "azul", "quando": INSTANTE.isoformat()})
    assert "azul" in str(erro.value)


def test_uuid_mal_formado_e_recusado_com_o_campo_no_texto():
    with pytest.raises(DadoInvalido) as erro:
        decodificar(Folha, {"id": "isto-nao-e-uuid"})
    assert "id" in str(erro.value)


def test_uuids_gerados_de_verdade_atravessam_a_ida_e_volta():
    folha = Folha(id=uuid4(), texto="sintética", peso=7)
    assert decodificar(Folha, codificar(folha)) == folha
