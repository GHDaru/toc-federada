"""Esqueleto do agregado Projeto — só a forma que o portão inspeciona."""
from contextlib import contextmanager

FERRAMENTA_GENERICA = "generico"
RAIZ_POR_FERRAMENTA: dict[str, str] = {}


def registrar_raiz_de_ferramenta(ferramenta: str, raiz: str) -> None:
    RAIZ_POR_FERRAMENTA[ferramenta] = raiz


class Projeto:
    ferramenta = FERRAMENTA_GENERICA
    _profundidade_da_raiz = 0

    @contextmanager
    def sob_a_raiz(self):
        self._profundidade_da_raiz += 1
        try:
            yield self
        finally:
            self._profundidade_da_raiz -= 1

    def _exigir_raiz(self, operacao: str) -> None:
        ...

    def adicionar_no(self, **kw):
        self._exigir_raiz("adicionar_no")

    def editar_no(self, **kw):
        self._exigir_raiz("editar_no")

    def mover_no(self, **kw):
        self._exigir_raiz("mover_no")

    def recolher_no(self, **kw):
        self._exigir_raiz("recolher_no")

    def excluir_no(self, **kw):
        self._exigir_raiz("excluir_no")

    def ligar(self, **kw):
        self._exigir_raiz("ligar")

    def editar_aresta(self, **kw):
        self._exigir_raiz("editar_aresta")

    def excluir_aresta(self, **kw):
        self._exigir_raiz("excluir_aresta")
