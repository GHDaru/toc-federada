"""Esqueleto da raiz do M3 — Nuvem de Conflito."""
from .projeto import Projeto, registrar_raiz_de_ferramenta

FERRAMENTA_NC = "nc"
registrar_raiz_de_ferramenta(FERRAMENTA_NC, "NuvemDeConflito")


class NuvemDeConflito:
    projeto: Projeto

    def editar_entidade(self, **kw):
        with self.projeto.sob_a_raiz() as nucleo:
            return nucleo.editar_no(**kw)
