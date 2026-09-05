"""Duplos das portas — a camada de aplicação testa sem banco e sem rede (brief §0.2).

Estes duplos implementam as portas de `toc_api.dominio.portas` estruturalmente
(`typing.Protocol`), sem herdar nada: se a porta mudar de forma, o teste de conformidade
em `tests/contrato/test_portas.py` acusa.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from typing import Iterator
from uuid import UUID

from toc_api.dominio.projeto import Projeto


@dataclass
class SpanFalso:
    nome: str
    atributos: dict[str, object] = field(default_factory=dict)
    encerrado: bool = False

    def atributo(self, chave: str, valor: str | int | float | bool) -> None:
        self.atributos[chave] = valor


@dataclass
class RastreadorFalso:
    """Guarda os spans abertos, na ordem, para o teste conferir nome e atributos."""

    spans: list[SpanFalso] = field(default_factory=list)

    @contextmanager
    def span(self, nome: str, **atributos: str | int | float | bool) -> Iterator[SpanFalso]:
        s = SpanFalso(nome=nome, atributos=dict(atributos))
        self.spans.append(s)
        try:
            yield s
        finally:
            s.encerrado = True

    @property
    def nomes(self) -> list[str]:
        return [s.nome for s in self.spans]


@dataclass
class RelogioFalso:
    instante: datetime

    def agora(self) -> datetime:
        return self.instante


@dataclass
class RepositorioDeProjetosFalso:
    """Repositório em memória que EXIGE inquilino em toda leitura — como a porta.

    O filtro por inquilino mora aqui de propósito: é assim que o adaptador SQL também
    tem de se comportar (invariante 1 do `data-model.md` do ciclo 003), e o teste de
    isolamento roda contra os dois.
    """

    itens: dict[UUID, Projeto] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        self.itens[projeto.id] = projeto

    def obter(self, inquilino_id: str, projeto_id: UUID) -> Projeto | None:
        p = self.itens.get(projeto_id)
        if p is None or p.dono.inquilino_id != inquilino_id:
            return None
        return p

    def listar(
        self,
        inquilino_id: str,
        *,
        usuario_id: str | None = None,
        incluir_excluidos: bool = False,
    ) -> list[Projeto]:
        achados = [p for p in self.itens.values() if p.dono.inquilino_id == inquilino_id]
        if usuario_id is not None:
            achados = [p for p in achados if p.dono.usuario_id == usuario_id]
        if not incluir_excluidos:
            achados = [p for p in achados if p.excluido_em is None]
        return sorted(achados, key=lambda p: p.alterado_em, reverse=True)


@dataclass
class RepositorioDeARAFalso(RepositorioDeProjetosFalso):
    """O mesmo duplo, também conforme à porta `RepositorioDeARA` (M2).

    Guarda o `ProjetoARA` inteiro — ficha, status, pareceres, exames e conectores — e
    mantém `itens` apontando para o MESMO `Projeto` que a ARA embrulha. Sem isso, um caso
    de uso do M1 (`AdicionarNo`) e um do M2 (`MarcarUde`) trabalhariam sobre duas cópias
    e a suíte ficaria verde sobre uma consistência que não existe.

    O duplo **não** prova persistência: quem prova é `tests/integracao/`, contra o
    PostgreSQL real.
    """

    aras: dict[UUID, object] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        super().salvar(projeto)
        ara = self.aras.get(projeto.id)
        if ara is not None and ara.projeto is not projeto:
            ara.projeto = projeto

    def salvar_ara(self, ara) -> None:
        self.aras[ara.projeto.id] = ara
        self.itens[ara.projeto.id] = ara.projeto

    def obter_ara(self, inquilino_id: str, projeto_id: UUID):
        ara = self.aras.get(projeto_id)
        if ara is None or ara.projeto.dono.inquilino_id != inquilino_id:
            return None
        return ara


@dataclass
class RepositorioDeNuvemFalso(RepositorioDeARAFalso):
    """O mesmo duplo, também conforme à porta `RepositorioDeNuvens` (M3).

    Guarda a `NuvemDeConflito` inteira — racional, premissas, injeções e a referência de
    origem — e mantém `itens` apontando para o MESMO `Projeto` que a nuvem embrulha. É a
    razão de ele herdar do duplo da ARA e não nascer sozinho: a derivação M2 → M3 lê uma
    Árvore da Realidade Atual (ARA) e grava uma Nuvem de Conflito (NC) **na mesma
    transação de leitura do caso de uso**, e um duplo que não soubesse os dois lados
    esconderia justamente o encadeamento que o ciclo 007 entrega.
    """

    nuvens: dict[UUID, object] = field(default_factory=dict)

    def salvar(self, projeto: Projeto) -> None:
        super().salvar(projeto)
        nuvem = self.nuvens.get(projeto.id)
        if nuvem is not None and nuvem.projeto is not projeto:
            nuvem.projeto = projeto

    def salvar_nuvem(self, nuvem) -> None:
        self.nuvens[nuvem.projeto.id] = nuvem
        self.itens[nuvem.projeto.id] = nuvem.projeto

    def obter_nuvem(self, inquilino_id: str, projeto_id: UUID):
        nuvem = self.nuvens.get(projeto_id)
        if nuvem is None or nuvem.projeto.dono.inquilino_id != inquilino_id:
            return None
        return nuvem


@dataclass
class MotorDeGeracaoFalso:
    """Duplo da porta `MotorDeGeracaoDeNuvem` — determinístico e sem provedor nenhum.

    O `resultado` é devolvido tal e qual: é assim que o teste exercita tanto o caminho
    feliz quanto a **falha fechada** (basta devolver estrutura torta e ver a recusa
    acontecer antes de qualquer escrita).
    """

    resultado: dict = field(default_factory=dict)
    premissas: tuple = ()
    injecoes: tuple = ()
    chamadas: list[tuple[str, str]] = field(default_factory=list)

    def gerar_nuvem(self, *, narrativa: str, contexto: dict) -> dict:
        self.chamadas.append(("gerar_nuvem", narrativa))
        return self.resultado

    def sugerir_premissas(self, *, aresta: str, narrativa: str, contexto: dict) -> tuple:
        self.chamadas.append(("sugerir_premissas", aresta))
        return self.premissas

    def sugerir_injecoes(self, *, premissa: str, contexto: dict) -> tuple:
        self.chamadas.append(("sugerir_injecoes", premissa))
        return self.injecoes
