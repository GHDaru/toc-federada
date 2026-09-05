"""Adaptador em memória da mesma porta — o backend de `DATABASE_URL` ausente.

Existe pelo motivo que a fundação registrou em
`apps/api/src/ghdaru_api/persistence/factory.py` (leitura apenas): dev e demonstração sem
banco. Duas diferenças conscientes em relação ao que lemos lá:

1. **Não semeia nada.** A spec 056 da fundação nasceu de um seed incondicional que
   publicava contas do repositório; aqui a fixture é responsabilidade de quem testa.
2. **Filtra por inquilino igual ao SQL.** Um duplo mais permissivo que o adaptador real
   faz a suíte ficar verde sobre um isolamento que não existe.
"""
from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from ...dominio.projeto import Projeto


class RepositorioDeProjetosEmMemoria:
    def __init__(self) -> None:
        self._itens: dict[UUID, Projeto] = {}
        self._aras: dict[UUID, object] = {}

    def salvar(self, projeto: Projeto) -> None:
        # Cópia na fronteira: sem isso, mutar o agregado devolvido mutaria o "banco" sem
        # passar por `salvar` — e o teste de exclusão reversível passaria por acidente.
        self._itens[projeto.id] = deepcopy(projeto)
        ara = self._aras.get(projeto.id)
        if ara is not None:
            ara.projeto = self._itens[projeto.id]

    def obter(self, inquilino_id: str, projeto_id: UUID) -> Projeto | None:
        achado = self._itens.get(projeto_id)
        if achado is None or achado.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    def listar(
        self,
        inquilino_id: str,
        *,
        usuario_id: str | None = None,
        incluir_excluidos: bool = False,
    ) -> list[Projeto]:
        achados = [
            p for p in self._itens.values() if p.dono.inquilino_id == inquilino_id
        ]
        if usuario_id is not None:
            achados = [p for p in achados if p.dono.usuario_id == usuario_id]
        if not incluir_excluidos:
            achados = [p for p in achados if p.excluido_em is None]
        achados.sort(key=lambda p: p.alterado_em, reverse=True)
        return [deepcopy(p) for p in achados]

    # -- Árvore da Realidade Atual (M2) --------------------------------------------
    # O duplo em memória também conforma à porta `RepositorioDeARA`: um backend que só
    # atende metade das portas faria a composição falhar em produção e passar em dev.

    def salvar_ara(self, ara) -> None:
        self._aras[ara.projeto.id] = deepcopy(ara)
        self._itens[ara.projeto.id] = self._aras[ara.projeto.id].projeto

    def obter_ara(self, inquilino_id: str, projeto_id: UUID):
        achado = self._aras.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)
