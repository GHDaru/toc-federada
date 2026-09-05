"""A porta `ProvedorDeIdentidade` e o adaptador FALSO de desenvolvimento (P2).

Esta aplicação **não tem login** (P2, item 2): identidade é da fundação, trocada por
`POST /auth/introspect`. O adaptador real dessa troca é de outro lote desta onda; o que
está aqui é a **porta** pela qual os dois lados se combinam, mais um adaptador falso para
o desenvolvimento andar — combinar pela porta, nunca pela implementação.

O que estes testes travam, e cada um vem de uma cláusula escrita:

- **§B.6.5 do Anexo B do Padrão APH (Aplicação ↔ Harness)**: "`{active:false}` NÃO DEVE
  distinguir 'token inexistente' de 'expirado' de 'já consumido': a diferença é oráculo
  para quem testa tokens". A porta devolve `None` nos três casos, e é por isso que ela não
  levanta exceções diferentes por motivo;
- **§B.6.4**: resposta de grant não carrega `role` — a construção do `Principal` recusa a
  resposta que o traga (`principal_de_introspeccao`, do lote da federação);
- **§B.9.5**: "a aplicação também não confia: o `payload` do handshake é **dado**, e a
  identidade só existe depois da introspecção". O falso é um registro fechado, não um
  decodificador do que o cliente mandou;
- **P7**: nenhuma credencial no repositório. O falso lê o registro de variável de
  ambiente do servidor, e o padrão é uma persona **fictícia** (ADR 0006).

O falso monta o principal pela MESMA função que traduz a introspecção de verdade
(`principal_de_introspeccao`): um segundo construtor de identidade é o que o RF-07 da spec
006 proíbe, e um adaptador de mentira com caminho próprio seria exatamente isso.
"""
from __future__ import annotations

import pytest

from toc_api.aplicacao.governanca import TOC_ESCRITA, TOC_LEITURA
from toc_api.dominio import portas
from toc_api.dominio.federacao.principal import principal_de_introspeccao
from toc_api.infra.configuracao import Configuracao
from toc_api.infra.identidade.falso import (
    PERSONA_DE_DESENVOLVIMENTO,
    ProvedorDeIdentidadeFalso,
    ProvedorQueNegaTudo,
    criar_provedor_de_identidade,
)


def test_a_porta_e_um_protocolo_verificavel_em_execucao():
    assert getattr(portas.ProvedorDeIdentidade, "_is_runtime_protocol", False)


def test_os_dois_adaptadores_satisfazem_a_porta():
    assert isinstance(ProvedorDeIdentidadeFalso({}), portas.ProvedorDeIdentidade)
    assert isinstance(ProvedorQueNegaTudo(), portas.ProvedorDeIdentidade)


def test_o_falso_identifica_o_token_registrado():
    principal = principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "usr-facilitadora", "name": "Facilitadora TOC"},
            "tenant_id": "inq-horizonte",
            "capabilities": ["toc:read", "toc:write"],
        }
    )
    provedor = ProvedorDeIdentidadeFalso({"tok-valido": principal})
    assert provedor.identificar("tok-valido") is principal


@pytest.mark.parametrize("token", ["tok-inexistente", "", "   ", "tok-VALIDO"])
def test_o_falso_devolve_none_sem_dizer_por_que_b_6_5(token):
    provedor = ProvedorDeIdentidadeFalso({"tok-valido": PERSONA_DE_DESENVOLVIMENTO[1]})
    assert provedor.identificar(token) is None


def test_o_que_nega_tudo_nega_ate_o_token_que_pareceria_bom():
    assert ProvedorQueNegaTudo().identificar("tok-valido") is None


def test_em_desenvolvimento_a_fabrica_entrega_o_falso_com_persona_ficticia():
    provedor = criar_provedor_de_identidade(
        Configuracao.do_ambiente({"TOC_AMBIENTE": "desenvolvimento"})
    )
    assert isinstance(provedor, ProvedorDeIdentidadeFalso)
    token, persona = PERSONA_DE_DESENVOLVIMENTO
    achado = provedor.identificar(token)
    assert achado == persona
    assert achado.dono().inquilino_id == "inq-horizonte"
    assert achado.dono().usuario_id == "usr-facilitadora"
    assert [c.valor for c in achado.capabilities] == [TOC_LEITURA, TOC_ESCRITA]


@pytest.mark.parametrize("ambiente", ["producao", "homologacao", "PRODUCAO"])
def test_fora_de_desenvolvimento_a_fabrica_nega_tudo_nunca_cai_no_falso(ambiente):
    """Fail-closed: sem o adaptador real de introspecção, ninguém entra — nem por engano.

    O caminho errado seria "cai no falso quando o real não está montado": um adaptador de
    desenvolvimento em produção é um login próprio com outro nome, que é o que o P2 proíbe.
    """
    provedor = criar_provedor_de_identidade(
        Configuracao.do_ambiente({"TOC_AMBIENTE": ambiente})
    )
    assert isinstance(provedor, ProvedorQueNegaTudo)
    assert provedor.identificar(PERSONA_DE_DESENVOLVIMENTO[0]) is None


def test_o_registro_falso_vem_de_variavel_de_ambiente_do_servidor():
    config = Configuracao.do_ambiente(
        {
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": (
                '{"tok-so-leitura": {"inquilino_id": "inq-horizonte",'
                ' "usuario_id": "usr-observadora", "capabilities": ["toc:read"]}}'
            ),
        }
    )
    provedor = criar_provedor_de_identidade(config)
    principal = provedor.identificar("tok-so-leitura")
    assert principal is not None
    assert [c.valor for c in principal.capabilities] == [TOC_LEITURA]
    assert principal.pode(TOC_ESCRITA) is False
    assert provedor.identificar(PERSONA_DE_DESENVOLVIMENTO[0]) is None


def test_registro_falso_com_curinga_nao_concede_nada():
    """Curinga descartado, e não aceito — §B.7.1, mesmo num adaptador de brincadeira."""
    config = Configuracao.do_ambiente(
        {
            "TOC_AMBIENTE": "teste",
            "TOC_IDENTIDADES_FALSAS": (
                '{"tok-esperto": {"inquilino_id": "i", "usuario_id": "u",'
                ' "capabilities": ["*:*", "toc:*"]}}'
            ),
        }
    )
    principal = criar_provedor_de_identidade(config).identificar("tok-esperto")
    assert principal is not None
    assert principal.capabilities == ()
    assert principal.capabilities_recusadas == ("*:*", "toc:*")
    assert principal.pode(TOC_LEITURA) is False


def test_registro_falso_ilegivel_nega_tudo_em_vez_de_abrir():
    config = Configuracao.do_ambiente(
        {"TOC_AMBIENTE": "teste", "TOC_IDENTIDADES_FALSAS": "isto não é JSON"}
    )
    assert isinstance(criar_provedor_de_identidade(config), ProvedorQueNegaTudo)


def test_nenhum_token_de_verdade_mora_no_repositorio_p7():
    """O único token em código é sintético e declarado como tal (ADR 0006 e P7)."""
    token, _ = PERSONA_DE_DESENVOLVIMENTO
    assert token.startswith("tok-desenvolvimento")
