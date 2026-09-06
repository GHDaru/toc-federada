"""Esqueleto do duplo em memória — a mesma trava, em Python."""
from ...dominio.erros import ConflitoDeVersao


class RepositorioDeProjetosEmMemoria:
    def __init__(self) -> None:
        self._itens = {}
        self._aras = {}
        self._nuvens = {}

    def _exigir_versao_lida(self, projeto) -> None:
        guardado = self._itens.get(projeto.id)
        if guardado is None:
            return
        if projeto.versao_lida != guardado.versao:
            raise ConflitoDeVersao(
                f"projeto:{projeto.id}",
                versao_lida=projeto.versao_lida,
                versao_atual=guardado.versao,
            )

    def salvar(self, projeto) -> None:
        self._exigir_versao_lida(projeto)
        projeto.confirmar_gravacao()
        self._itens[projeto.id] = deepcopy(projeto)

    def salvar_ara(self, ara) -> None:
        self._exigir_versao_lida(ara.projeto)
        ara.projeto.confirmar_gravacao()
        self._aras[ara.projeto.id] = deepcopy(ara)

    def salvar_nuvem(self, nuvem) -> None:
        self._exigir_versao_lida(nuvem.projeto)
        nuvem.projeto.confirmar_gravacao()
        self._nuvens[nuvem.projeto.id] = deepcopy(nuvem)
