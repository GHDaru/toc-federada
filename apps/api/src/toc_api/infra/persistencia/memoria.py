"""Adaptador em memória da mesma porta — o backend de `DATABASE_URL` ausente.

Existe pelo motivo que a fundação registrou em
`apps/api/src/ghdaru_api/persistence/factory.py` (leitura apenas): dev e demonstração sem
banco. Duas diferenças conscientes em relação ao que lemos lá:

1. **Não semeia nada.** A spec 056 da fundação nasceu de um seed incondicional que
   publicava contas do repositório; aqui a fixture é responsabilidade de quem testa.
2. **Filtra por inquilino igual ao SQL.** Um duplo mais permissivo que o adaptador real
   faz a suíte ficar verde sobre um isolamento que não existe.
3. **Tem a MESMA trava otimista do SQL.** Pelo mesmo motivo do item 2, e com um caso
   nomeado: enquanto o adaptador real passou a recusar a segunda escrita da mesma versão
   (`ConflitoDeVersao`) e este duplo continuasse aceitando, os testes de contrato — que
   rodam sobre ele — ficariam verdes sobre uma perda de atualização que o banco de
   verdade recusa. A trava aqui é a comparação em Python do que lá é
   `UPDATE … WHERE versao = :versao_lida`.
"""
from __future__ import annotations

from copy import deepcopy
from uuid import UUID

from ...dominio.erros import ConflitoDeVersao
from ...dominio.projeto import Projeto
from ...dominio.referencia import ReferenciaCruzada


class RepositorioDeProjetosEmMemoria:
    def __init__(self) -> None:
        self._itens: dict[UUID, Projeto] = {}
        self._aras: dict[UUID, object] = {}
        self._nuvens: dict[UUID, object] = {}
        # M4 — Árvores de Futuro e Implementação (spec 008). O duplo conforma às portas do
        # M4 pelo mesmo motivo das anteriores: um backend que só atende parte das portas
        # falharia em produção e passaria em desenvolvimento.
        self._arfs: dict[UUID, object] = {}
        self._aprs: dict[UUID, object] = {}
        self._ats: dict[UUID, object] = {}
        self._referencias: dict[UUID, ReferenciaCruzada] = {}
        # M6 — Focalização (spec 009). Mesmo motivo dos anteriores: um backend que só
        # atende parte das portas falharia em produção e passaria em desenvolvimento.
        self._focalizacoes: dict[UUID, object] = {}

    def _exigir_versao_lida(self, projeto: Projeto) -> None:
        """A trava otimista do duplo — a mesma regra do `WHERE versao =` do adaptador SQL."""
        guardado = self._itens.get(projeto.id)
        if guardado is None:
            # Nada guardado: é inserção. Não há caminho que apague neste duplo, então
            # "sumiu debaixo de quem leu" — o `NaoEncontrado` do adaptador SQL — não tem
            # como acontecer aqui.
            return
        if projeto.versao_lida != guardado.versao:
            raise ConflitoDeVersao(
                f"projeto:{projeto.id}",
                versao_lida=projeto.versao_lida,
                versao_atual=guardado.versao,
            )

    def salvar(self, projeto: Projeto) -> None:
        self._exigir_versao_lida(projeto)
        projeto.confirmar_gravacao()
        # Cópia na fronteira: sem isso, mutar o agregado devolvido mutaria o "banco" sem
        # passar por `salvar` — e o teste de exclusão reversível passaria por acidente.
        self._itens[projeto.id] = deepcopy(projeto)
        ara = self._aras.get(projeto.id)
        if ara is not None:
            ara.projeto = self._itens[projeto.id]
        for guardados in (self._nuvens, self._arfs, self._aprs, self._ats, self._focalizacoes):
            agregado = guardados.get(projeto.id)
            if agregado is not None:
                agregado.projeto = self._itens[projeto.id]

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
        self._exigir_versao_lida(ara.projeto)
        ara.projeto.confirmar_gravacao()
        self._aras[ara.projeto.id] = deepcopy(ara)
        self._itens[ara.projeto.id] = self._aras[ara.projeto.id].projeto

    def obter_ara(self, inquilino_id: str, projeto_id: UUID):
        achado = self._aras.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    # -- Nuvem de Conflito (M3) ------------------------------------------------------
    # O duplo em memória também conforma à porta `RepositorioDeNuvens`, pelo mesmo motivo
    # da ARA: um backend que só atende parte das portas falharia em produção e passaria em
    # desenvolvimento.

    def salvar_nuvem(self, nuvem) -> None:
        self._exigir_versao_lida(nuvem.projeto)
        nuvem.projeto.confirmar_gravacao()
        self._nuvens[nuvem.projeto.id] = deepcopy(nuvem)
        self._itens[nuvem.projeto.id] = self._nuvens[nuvem.projeto.id].projeto

    def obter_nuvem(self, inquilino_id: str, projeto_id: UUID):
        achado = self._nuvens.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    # -- M4 · Árvores de Futuro e Implementação (spec 008) ------------------------------
    #
    # A trava otimista é a MESMA dos três anteriores, e pelo mesmo motivo: verde aqui
    # sobre uma perda de atualização que o banco de verdade recusa é verde sobre defeito.

    def salvar_arf(self, arf) -> None:
        self._exigir_versao_lida(arf.projeto)
        arf.projeto.confirmar_gravacao()
        self._arfs[arf.projeto.id] = deepcopy(arf)
        self._itens[arf.projeto.id] = self._arfs[arf.projeto.id].projeto

    def obter_arf(self, inquilino_id: str, projeto_id: UUID):
        achado = self._arfs.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    def salvar_apr(self, apr) -> None:
        self._exigir_versao_lida(apr.projeto)
        apr.projeto.confirmar_gravacao()
        self._aprs[apr.projeto.id] = deepcopy(apr)
        self._itens[apr.projeto.id] = self._aprs[apr.projeto.id].projeto

    def obter_apr(self, inquilino_id: str, projeto_id: UUID):
        achado = self._aprs.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    def salvar_at(self, at) -> None:
        self._exigir_versao_lida(at.projeto)
        at.projeto.confirmar_gravacao()
        self._ats[at.projeto.id] = deepcopy(at)
        self._itens[at.projeto.id] = self._ats[at.projeto.id].projeto

    def obter_at(self, inquilino_id: str, projeto_id: UUID):
        achado = self._ats.get(projeto_id)
        if achado is None or achado.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achado)

    # -- M6 · Focalização (spec 009) ---------------------------------------------------
    #
    # A trava otimista é a MESMA dos anteriores, e aqui ela protege o caso mais próprio do
    # módulo: a jornada é estado compartilhado numa sessão de facilitação, e duas pessoas
    # concluindo o mesmo passo a partir da mesma versão é o cenário normal, não o raro.

    def salvar_focalizacao(self, analise) -> None:
        self._exigir_versao_lida(analise.projeto)
        analise.projeto.confirmar_gravacao()
        self._focalizacoes[analise.projeto.id] = deepcopy(analise)
        self._itens[analise.projeto.id] = self._focalizacoes[analise.projeto.id].projeto

    def obter_focalizacao(self, inquilino_id: str, projeto_id: UUID):
        achada = self._focalizacoes.get(projeto_id)
        if achada is None or achada.projeto.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achada)

    # -- referência cruzada: agregado próprio, e por isso trava própria -----------------

    def _exigir_versao_lida_da_referencia(self, referencia: ReferenciaCruzada) -> None:
        """A trava do agregado do encadeamento — a mesma regra, sobre a outra versão."""
        guardada = self._referencias.get(referencia.id)
        if guardada is None:
            return
        if referencia.versao_lida != guardada.versao:
            raise ConflitoDeVersao(
                f"referencia:{referencia.id}",
                versao_lida=referencia.versao_lida,
                versao_atual=guardada.versao,
            )

    def salvar_referencia(self, referencia: ReferenciaCruzada) -> None:
        self._exigir_versao_lida_da_referencia(referencia)
        referencia.confirmar_gravacao()
        self._referencias[referencia.id] = deepcopy(referencia)

    def obter_referencia(self, inquilino_id: str, referencia_id: UUID):
        achada = self._referencias.get(referencia_id)
        if achada is None or achada.dono.inquilino_id != inquilino_id:
            return None
        return deepcopy(achada)

    def listar_referencias(
        self, inquilino_id: str, *, projeto_id: UUID | None = None
    ) -> list[ReferenciaCruzada]:
        achadas = [
            r for r in self._referencias.values() if r.dono.inquilino_id == inquilino_id
        ]
        if projeto_id is not None:
            achadas = [r for r in achadas if r.toca(projeto_id)]
        achadas.sort(key=lambda r: (r.criada_em, str(r.id)))
        return [deepcopy(r) for r in achadas]
