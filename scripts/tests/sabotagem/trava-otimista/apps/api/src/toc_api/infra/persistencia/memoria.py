"""Esqueleto do duplo em memória — a mesma trava, em Python."""
from ...dominio.erros import ConflitoDeVersao


class RepositorioDeProjetosEmMemoria:
    def __init__(self) -> None:
        self._itens = {}
        self._aras = {}
        self._nuvens = {}
        self._arfs = {}
        self._aprs = {}
        self._ats = {}
        self._referencias = {}

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

    def salvar_arf(self, arf) -> None:
        self._exigir_versao_lida(arf.projeto)
        arf.projeto.confirmar_gravacao()
        self._arfs[arf.projeto.id] = deepcopy(arf)

    def salvar_apr(self, apr) -> None:
        self._exigir_versao_lida(apr.projeto)
        apr.projeto.confirmar_gravacao()
        self._aprs[apr.projeto.id] = deepcopy(apr)

    def salvar_at(self, at) -> None:
        self._exigir_versao_lida(at.projeto)
        at.projeto.confirmar_gravacao()
        self._ats[at.projeto.id] = deepcopy(at)

    def salvar_focalizacao(self, analise) -> None:
        self._exigir_versao_lida(analise.projeto)
        analise.projeto.confirmar_gravacao()
        self._focalizacoes[analise.projeto.id] = deepcopy(analise)

    def _exigir_versao_lida_da_referencia(self, referencia) -> None:
        guardada = self._referencias.get(referencia.id)
        if guardada is None:
            return
        if referencia.versao_lida != guardada.versao:
            raise ConflitoDeVersao(
                f"referencia:{referencia.id}",
                versao_lida=referencia.versao_lida,
                versao_atual=guardada.versao,
            )

    def salvar_referencia(self, referencia) -> None:
        self._exigir_versao_lida_da_referencia(referencia)
        referencia.confirmar_gravacao()
        self._referencias[referencia.id] = deepcopy(referencia)
