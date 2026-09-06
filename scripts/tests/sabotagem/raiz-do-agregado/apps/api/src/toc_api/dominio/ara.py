"""Esqueleto da raiz do M2 — Árvore da Realidade Atual."""
from .projeto import Projeto, registrar_raiz_de_ferramenta

FERRAMENTA_ARA = "ara"
registrar_raiz_de_ferramenta(FERRAMENTA_ARA, "ProjetoARA")


class ProjetoARA:
    projeto: Projeto

    def adicionar_efeito(self, **kw):
        with self.projeto.sob_a_raiz() as nucleo:
            return nucleo.adicionar_no(**kw)
