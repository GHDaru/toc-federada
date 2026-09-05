"""Catálogo `toc.*` — uma fonte, três projeções, derivado de permissão (APH-4.x).

Siglas: **APH** — Aplicação ↔ Harness · **JSON** — *JavaScript Object Notation* ·
**UDE** — Efeito Indesejável.

O que se prova aqui, na ordem dos requisitos da spec 006:

- RF-06: ação sem `action_id`, título, `input_schema` ou risco **não entra**.
- RF-05/RN-05: sem `toc:write`, nenhuma ação `confirm` aparece — **ausência**, não recusa
  (§B.7.3). O teste imprime a contagem antes e depois, que é o portão do roadmap.
- RF-07: o mesmo `input_schema` valida `args`, vira ferramenta do modelo e entra no
  manifesto — as três projeções saem da mesma fonte.
- RF-04: paridade com `contracts/manifesto.json` — um teste que falha se divergirem.
- RF-02: prefixo `toc` em toda ação e toda tela; rota de tela sob `/toc/`.
- RF-28: `batch_atomicity` declarado no catálogo servido; ação sem o campo não é de lote.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from toc_api.dominio.federacao.catalogo import (
    CATALOGO_TOC,
    AcaoDoCatalogo,
    AcaoDesconhecida,
    Catalogo,
    RISCOS,
)
from toc_api.dominio.federacao.principal import principal_anonimo, principal_de_introspeccao

RAIZ = Path(__file__).resolve().parents[4]
MANIFESTO = json.loads(
    (RAIZ / "specs/006-acoes-governadas-e-snapshot/contracts/manifesto.json").read_text("utf-8")
)


def _principal(capabilities: list[str]):
    return principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "u-01", "name": "Facilitadora TOC"},
            "tenant_id": "instituicao-horizonte",
            "capabilities": capabilities,
            "app_id": "toc",
        }
    )


def test_toda_acao_declara_os_quatro_campos_do_aph_4_2() -> None:
    for acao in CATALOGO_TOC.acoes:
        assert acao.action_id
        assert acao.title
        assert acao.risk in RISCOS
        assert isinstance(acao.input_schema, dict) and acao.input_schema


def test_acao_sem_um_dos_quatro_campos_nao_entra_no_catalogo() -> None:
    with pytest.raises(ValueError):
        AcaoDoCatalogo(action_id="toc.x", title="", risk="read", input_schema={"type": "object"})
    with pytest.raises(ValueError):
        AcaoDoCatalogo(action_id="toc.x", title="X", risk="talvez", input_schema={"type": "object"})
    with pytest.raises(ValueError):
        AcaoDoCatalogo(action_id="toc.x", title="X", risk="read", input_schema={})


def test_toda_acao_e_prefixada_pelo_app_id() -> None:
    """RF-02: forma `<ns>.<id>` do §B.5.2, com o prefixo igual ao `app_id`."""
    for acao in CATALOGO_TOC.acoes:
        assert acao.action_id.startswith("toc."), acao.action_id


def test_toda_rota_de_ui_vive_sob_barra_toc() -> None:
    for acao in CATALOGO_TOC.acoes:
        if acao.ui_route:
            assert acao.ui_route.startswith("/toc/"), acao.action_id
            assert acao.ui_route == acao.ui_route.lower()
            assert not acao.ui_route.endswith("/")


def test_catalogo_composto_sem_write_nao_tem_nenhuma_acao_confirm() -> None:
    """RF-05, o portão do roadmap: a contagem antes e depois sai impressa."""
    so_leitura = _principal(["toc:read"])
    completo = _principal(["toc:read", "toc:write"])

    visiveis_leitura = CATALOGO_TOC.compor(so_leitura)
    visiveis_completo = CATALOGO_TOC.compor(completo)

    medida = (
        f"catálogo: {len(CATALOGO_TOC.acoes)} ações declaradas; "
        f"com toc:read+toc:write → {len(visiveis_completo)}; "
        f"só com toc:read → {len(visiveis_leitura)}; "
        f"anônimo → {len(CATALOGO_TOC.compor(principal_anonimo()))}"
    )
    print(medida)
    assert [a.risk for a in visiveis_leitura].count("confirm") == 0
    assert len(visiveis_leitura) < len(visiveis_completo)
    assert "11 ações declaradas" in medida, medida


def test_principal_anonimo_ve_catalogo_vazio() -> None:
    """Ausência é a fronteira: sem capability, a superfície executável é vazia."""
    assert CATALOGO_TOC.compor(principal_anonimo()) == ()


def test_acao_fora_do_catalogo_composto_e_desconhecida_para_aquele_principal() -> None:
    """RF-09: proposta que cite `action_id` fora do composto é recusada.

    O erro é o mesmo de ação inexistente, de propósito: distinguir "não existe" de "existe
    e você não pode" vazaria o inventário do inquilino ao lado.
    """
    so_leitura = _principal(["toc:read"])

    with pytest.raises(AcaoDesconhecida):
        CATALOGO_TOC.exigir_visivel("toc.criar_nos", so_leitura)
    with pytest.raises(AcaoDesconhecida):
        CATALOGO_TOC.exigir_visivel("toc.inexistente", so_leitura)

    assert CATALOGO_TOC.exigir_visivel("toc.listar_projetos", so_leitura).risk == "read"


def test_a_projecao_de_ferramenta_carrega_o_mesmo_input_schema() -> None:
    """RF-07, projeção 2: a *tool* que a fundação entrega ao modelo."""
    acao = CATALOGO_TOC.acao("toc.criar_nos")

    ferramenta = acao.como_ferramenta()

    assert ferramenta["name"] == "toc.criar_nos"
    assert ferramenta["description"]
    assert ferramenta["input_schema"] is acao.input_schema
    # a ferramenta declara o risco: o modelo não decide a classe, mas precisa saber que
    # a chamada vira proposta e não execução (APH-5.2)
    assert ferramenta["risk"] == "confirm"
    assert ferramenta["requires_confirmation"] is True


def test_a_projecao_de_mcp_sai_da_mesma_fonte() -> None:
    """RF-07, projeção 3 (futura): a ferramenta do Model Context Protocol.

    O Nível 3 está **fora de escopo** (ADR 0003), e é justamente por isso que a projeção
    existe como função pura e não como servidor: o dia em que o Nível 3 for decidido, o
    que muda é o transporte, não a fonte.
    """
    acao = CATALOGO_TOC.acao("toc.listar_projetos")

    mcp = acao.como_ferramenta_mcp()

    assert mcp["name"] == "toc.listar_projetos"
    assert mcp["inputSchema"] is acao.input_schema
    assert mcp["annotations"]["readOnlyHint"] is True


def test_a_projecao_de_manifesto_bate_campo_a_campo_com_o_contrato_versionado() -> None:
    """RF-04: as ações do manifesto e as do catálogo servido vêm da MESMA fonte.

    Sem este teste, o manifesto submetido e o catálogo servido derivam em silêncio — que
    é o defeito que a RF-03 chama de "deriva silenciosa".
    """
    do_catalogo = {a["action_id"]: a for a in CATALOGO_TOC.como_manifesto()}
    do_contrato = {a["action_id"]: a for a in MANIFESTO["actions"]}

    assert set(do_catalogo) == set(do_contrato)
    for action_id, esperado in do_contrato.items():
        assert do_catalogo[action_id] == esperado, f"divergência em {action_id}"


def test_batch_atomicity_so_existe_nas_acoes_desenhadas_para_lote() -> None:
    """RF-28 e §A.5: ausente significa "não desenhada para lote", nunca `per_item`."""
    de_lote = {a.action_id for a in CATALOGO_TOC.acoes if a.batch_atomicity}
    assert de_lote == {"toc.criar_nos", "toc.criar_arestas", "toc.excluir_nos"}

    for acao in CATALOGO_TOC.acoes:
        if acao.batch_atomicity:
            assert acao.batch_atomicity in {"all_or_nothing", "per_item"}
            assert acao.campo_de_alvos, f"{acao.action_id} é de lote e não diz onde estão os alvos"
        else:
            assert acao.campo_de_alvos is None


def test_o_catalogo_servido_declara_batch_atomicity_mesmo_com_o_manifesto_sem_ele() -> None:
    """L-02 da spec 006, verificado aqui: o schema normativo do manifesto não tem o campo.

    A decisão declarada é servir a atomicidade no **catálogo** (§A.5) e omiti-la do
    manifesto. Este teste é o que impede a decisão de virar esquecimento.
    """
    schema = json.loads(
        (RAIZ.parent / "protocolos/padrao/schemas/federacao-manifesto.schema.json").read_text("utf-8")
    )
    assert "batch_atomicity" not in json.dumps(schema)

    servido = {a["action_id"]: a for a in CATALOGO_TOC.como_catalogo_servido(_principal(["toc:read", "toc:write"]))}
    assert servido["toc.criar_nos"]["batch_atomicity"] == "per_item"
    assert "batch_atomicity" not in {k for a in CATALOGO_TOC.como_manifesto() for k in a}


def test_toda_acao_de_mutacao_e_confirm_e_toda_leitura_e_read() -> None:
    """RN-01: `read` nunca muta; toda mutação é `confirm`. Classe nova exige ADR."""
    for acao in CATALOGO_TOC.acoes:
        assert acao.risk in {"read", "confirm"}
        assert acao.requires_confirmation == (acao.risk == "confirm")
        if acao.risk == "confirm":
            assert acao.capability_exigida == "toc:write"
        else:
            assert acao.capability_exigida == "toc:read"


def test_exclusao_definitiva_nao_esta_no_catalogo() -> None:
    """RN-02: exclusão definitiva não entra no catálogo da inteligência artificial."""
    ids = {a.action_id for a in CATALOGO_TOC.acoes}
    assert "toc.excluir_definitivamente" not in ids
    assert CATALOGO_TOC.acao("toc.excluir_nos").reversible is True


def test_catalogo_recusa_esquema_que_o_validador_nao_entende() -> None:
    """O catálogo é construído com `exigir_esquema_suportado`: schema que este projeto não
    sabe validar não vira ação — o defeito aparece na construção, não na primeira proposta."""
    from toc_api.dominio.federacao.esquema import EsquemaNaoSuportado

    with pytest.raises(EsquemaNaoSuportado):
        Catalogo(
            (
                AcaoDoCatalogo(
                    action_id="toc.x",
                    title="X",
                    risk="read",
                    input_schema={"type": "object", "properties": {"a": {"pattern": "^x"}}},
                ),
            )
        )


def test_o_catalogo_nao_tem_action_id_repetido() -> None:
    ids = [a.action_id for a in CATALOGO_TOC.acoes]
    assert len(ids) == len(set(ids))
