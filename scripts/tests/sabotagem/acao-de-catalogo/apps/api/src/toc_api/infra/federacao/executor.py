"""Executor mínimo — a forma que `check-acao-de-catalogo.sh` lê (fixture, não serviço)."""
from ...aplicacao.ara import AdicionarEfeito
from ...aplicacao.grafo import AdicionarNo
from ...aplicacao.projetos import ListarProjetos


class ExecutorDoCatalogo:
    def __init__(self, *, rastreador, projetos, aras, relogio) -> None:
        self._listar = ListarProjetos(rastreador=rastreador, repositorio=projetos)
        self._adicionar = AdicionarNo(rastreador=rastreador, repositorio=projetos)
        self._adicionar_efeito = (
            AdicionarEfeito(rastreador=rastreador, repositorio=aras) if aras is not None else None
        )
        self._despacho: dict = {
            "toc.listar_projetos": self._acao_listar_projetos,
            "toc.suggest_udes": self._acao_registrar_ude,
            "toc.criar_nos": self._acao_criar_no,
        }

    def _acao_listar_projetos(self, args, principal):
        return ("executed", str(len(self._listar.rodar(dono=principal))))

    def _acao_registrar_ude(self, args, principal):
        no = self._adicionar_efeito.rodar(dono=principal, titulo=args["texto"])
        return ("executed", str(no))

    def _acao_criar_no(self, args, principal):
        no = self._adicionar.rodar(dono=principal, titulo=args["titulo"])
        return ("executed", str(no))
