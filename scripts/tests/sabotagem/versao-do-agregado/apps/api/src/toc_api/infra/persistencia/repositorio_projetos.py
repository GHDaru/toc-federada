"""Adaptador sintético — cada raiz registrada tem caminho de escrita, e ele é condicionado.

O `WHERE versao = :versao_lida` de verdade mora no serviço; aqui basta a FORMA que o
portão lê: todo `salvar_*` anota o agregado que recebe e passa por `_gravar_projeto`.
"""
from __future__ import annotations

from toc_api.dominio.ferramenta import ProjetoSintetico
from toc_api.dominio.projeto import Projeto
from toc_api.dominio.segunda import ProjetoSegundo


class RepositorioDeProjetosSQL:
    def __init__(self, sessao) -> None:
        self._sessao = sessao

    def salvar(self, projeto: Projeto) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, projeto)
        projeto.confirmar_gravacao()

    def salvar_sintetico(self, agregado: ProjetoSintetico) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, agregado.projeto)
        agregado.projeto.confirmar_gravacao()

    def salvar_segundo(self, agregado: ProjetoSegundo) -> None:
        with self._sessao.begin() as s:
            self._gravar_projeto(s, agregado.projeto)
        agregado.projeto.confirmar_gravacao()

    def _gravar_projeto(self, s, projeto: Projeto) -> None:
        """A trava: a escrita casa contra a versão LIDA, e quem não casa é recusado."""
        s.execute(
            "update projeto set versao = :nova where id = :id and versao = :lida",
            {"nova": projeto.versao, "id": id(projeto), "lida": projeto.versao_lida},
        )
