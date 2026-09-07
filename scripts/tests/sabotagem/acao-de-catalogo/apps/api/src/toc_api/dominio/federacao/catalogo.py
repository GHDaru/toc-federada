"""Catálogo mínimo — a forma que `check-acao-de-catalogo.sh` lê (fixture, não serviço)."""
from ..ara import FERRAMENTA_ARA
from ..valores import FERRAMENTA_GENERICA


class AcaoDoCatalogo:
    pass


ACOES_TOC = (
    AcaoDoCatalogo(
        action_id="toc.listar_projetos",
        title="Listar projetos",
        risk="read",
        input_schema={"type": "object"},
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_udes",
        ferramenta=FERRAMENTA_ARA,
        title="Registrar Efeitos Indesejaveis",
        risk="confirm",
        input_schema={"type": "object"},
    ),
    AcaoDoCatalogo(
        action_id="toc.criar_nos",
        ferramenta=FERRAMENTA_GENERICA,
        title="Criar nos no projeto generico",
        risk="confirm",
        input_schema={"type": "object"},
    ),
)
