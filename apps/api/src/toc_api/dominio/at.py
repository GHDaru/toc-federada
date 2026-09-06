"""M4 · E4.3 — a Árvore de Transição (AT) sobre o núcleo do M1 (spec 008).

Siglas, uma vez neste arquivo: **AT** — Árvore de Transição · **APR** — Árvore de
Pré-Requisitos · **OI** — Objetivo Intermediário · **TOC** — Teoria das Restrições ·
**M1** — Núcleo de Diagramas Lógicos · **RF/RN** — requisito funcional / regra de negócio.

**O menor delta possível** (decisão 8 do plano do ciclo 008): o passo é um nó do M1 com
uma `FichaDePasso` (objeto de valor) e a precedência é a aresta do M1. Não há entidade de
projeto nova. É coerente com o round — "dos três diagramas, o de menor risco" — e com o
corte: se a AT sair do ciclo, sai limpa.

**A regra que dá sentido à ferramenta é a RN-10**: a tripla ação · necessidade · resultado
esperado é **obrigatória na criação**. "Passo sem necessidade explícita é o que degrada a
AT a lista de tarefas" — e lista de tarefas não é Processo de Pensamento. Por isso os três
campos não têm valor padrão.

**A segunda regra é a do acompanhamento** (RF-30): ao concluir com resultado real
diferente do esperado, a divergência vai para o **evento** e o esperado **não** é
sobrescrito. Apagar o esperado apagaria a pergunta que a AT existe para responder.

O que a AT deliberadamente **não** é: gestor de projetos. Prazo, responsável, calendário e
percentual de conclusão estão fora de escopo por decisão declarada da spec — priorizar e
acompanhar o trabalho de pessoas é o produto da irmã `gestaodeprioridades`.
"""
from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass, field, replace
from datetime import datetime
from enum import Enum
from typing import Iterator, Mapping
from uuid import UUID

from .erros import DadoInvalido, MutacaoRecusada
from .eventos import AtCriada, FichaDePassoEditada, PassoMudouDeStatus, PassoRegistrado
from .grafo import ArestaCausal, No, alcanca, sucessores
from .identidade import DonoDoProjeto
from .projeto import Projeto, registrar_raiz_de_ferramenta
from .referencia import Ponta
from .valores import LIMITE_DESCRICAO, LIMITE_TITULO, PosicaoNoCanvas, texto as texto_de_dominio

#: O tipo de projeto do M4 · E4.3 (spec 008, RF-28).
FERRAMENTA_AT = "at"

#: A AT é a RAIZ do agregado: o grafo de um projeto `at` só muda por dentro dela. Sem
#: isto, `Projeto.adicionar_no` criaria passo **sem ficha** — que é exatamente a lista de
#: tarefas que a RN-10 existe para impedir.
registrar_raiz_de_ferramenta(FERRAMENTA_AT, "ProjetoAT")

#: Todo nó da AT é um passo. Não há segundo papel: a AT não tem obstáculo nem injeção.
TIPO_DE_NO_PASSO = "at_passo"

LIMITE_MOTIVO = 1000
LIMITE_RESULTADO = 1000


class StatusDoPasso(str, Enum):
    """RF-30: acompanhamento **leve** — quatro estados, nenhum campo de gestão de projeto."""

    PENDENTE = "pendente"
    EM_EXECUCAO = "em_execucao"
    CONCLUIDO = "concluido"
    BLOQUEADO = "bloqueado"


class PassoInvalido(MutacaoRecusada):
    """`regra`: `sem_ficha` · `precedencia_de_passo`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class TransicaoDePassoRecusada(MutacaoRecusada):
    """RF-30. `motivo`: `sem_mudanca` · `motivo_obrigatorio` · `resultado_real_obrigatorio`."""

    def __init__(self, motivo: str, detalhe: str = "") -> None:
        super().__init__(f"{motivo}: {detalhe}" if detalhe else motivo)
        self.motivo = motivo


@dataclass(frozen=True, slots=True)
class FichaDePasso:
    """A tripla obrigatória mais o acompanhamento (RN-10, RF-30).

    Objeto de valor: mudar um campo cria ficha nova. É isso que impede o resultado
    esperado de ser mutado por baixo do agregado, sem passar pelo evento.
    """

    acao: str
    necessidade: str
    resultado_esperado: str
    status: StatusDoPasso = StatusDoPasso.PENDENTE
    motivo_do_bloqueio: str = ""
    resultado_real: str = ""

    def __post_init__(self) -> None:
        # RN-10: os três, sempre. Sem valor padrão e sem "opcional por enquanto".
        object.__setattr__(
            self, "acao", texto_de_dominio(self.acao, campo="acao", minimo=1, maximo=LIMITE_TITULO)
        )
        object.__setattr__(
            self,
            "necessidade",
            texto_de_dominio(
                self.necessidade, campo="necessidade", minimo=1, maximo=LIMITE_DESCRICAO
            ),
        )
        object.__setattr__(
            self,
            "resultado_esperado",
            texto_de_dominio(
                self.resultado_esperado,
                campo="resultado_esperado",
                minimo=1,
                maximo=LIMITE_DESCRICAO,
            ),
        )
        object.__setattr__(self, "status", StatusDoPasso(self.status))
        object.__setattr__(self, "motivo_do_bloqueio", (self.motivo_do_bloqueio or "").strip())
        object.__setattr__(self, "resultado_real", (self.resultado_real or "").strip())

    def leitura(self) -> str:
        """RF-29: "Para <necessidade>, <ação>; espero <resultado>"."""
        return f"Para {self.necessidade}, {self.acao}; espero {self.resultado_esperado}"

    @property
    def divergente(self) -> bool:
        """O real difere do esperado? Comparação de texto normalizado — e nada apagado."""
        return bool(self.resultado_real) and (
            self.resultado_real.strip().casefold()
            != self.resultado_esperado.strip().casefold()
        )


@dataclass(slots=True)
class ProjetoAT:
    """A AT: um `Projeto` do M1, uma ficha por passo, e o alvo de onde ela nasceu."""

    projeto: Projeto
    #: RF-40: o OI (ou objetivo) que esta AT desce a passos, quando ela foi derivada.
    alvo: Ponta | None = None
    _fichas: dict[UUID, FichaDePasso] = field(default_factory=dict)

    def __post_init__(self) -> None:
        if self.projeto.ferramenta != FERRAMENTA_AT:
            raise MutacaoRecusada(
                f"ProjetoAT exige ferramenta {FERRAMENTA_AT!r}, "
                f"veio {self.projeto.ferramenta!r}"
            )

    # -- a única porta para o `Projeto` contido ----------------------------------

    @contextmanager
    def _nucleo(self) -> Iterator[Projeto]:
        with self.projeto.sob_a_raiz() as nucleo:
            yield nucleo

    # -- consultas ---------------------------------------------------------------

    @property
    def passos(self) -> tuple[No, ...]:
        return self.projeto.nos

    @property
    def precedencias(self) -> tuple[ArestaCausal, ...]:
        return self.projeto.arestas

    @property
    def eventos(self):
        return self.projeto.eventos

    def drenar_eventos(self):
        return self.projeto.drenar_eventos()

    def ficha(self, no_id: UUID) -> FichaDePasso:
        try:
            return self._fichas[no_id]
        except KeyError as ausente:
            raise PassoInvalido("sem_ficha", f"o nó {no_id} não é um passo desta AT") from ausente

    def fichas(self) -> tuple[tuple[UUID, FichaDePasso], ...]:
        return tuple(sorted(self._fichas.items(), key=lambda par: str(par[0])))

    def leitura_do_passo(self, no_id: UUID) -> str:
        return self.ficha(no_id).leitura()

    # -- passos, pela raiz -------------------------------------------------------

    def registrar_passo(
        self,
        *,
        acao: str,
        necessidade: str,
        resultado_esperado: str,
        em: datetime,
        posicao: PosicaoNoCanvas | None = None,
        no_id: UUID | None = None,
    ) -> No:
        """RN-10: a ficha é construída ANTES do nó — se a tripla falta, nada nasce."""
        ficha = FichaDePasso(
            acao=acao, necessidade=necessidade, resultado_esperado=resultado_esperado
        )
        with self._nucleo() as nucleo:
            no = nucleo.adicionar_no(
                titulo=ficha.acao,
                tipo=TIPO_DE_NO_PASSO,
                posicao=posicao,
                no_id=no_id,
                em=em,
            )
        self._fichas[no.id] = ficha
        self._emitir(PassoRegistrado, em, no_id=no.id)
        return no

    def editar_ficha(
        self,
        no_id: UUID,
        *,
        em: datetime,
        acao: str | None = None,
        necessidade: str | None = None,
        resultado_esperado: str | None = None,
    ) -> FichaDePasso:
        atual = self.ficha(no_id)
        campos: list[str] = []
        nova = atual
        if acao is not None:
            nova = replace(nova, acao=acao)
            campos.append("acao")
        if necessidade is not None:
            nova = replace(nova, necessidade=necessidade)
            campos.append("necessidade")
        if resultado_esperado is not None:
            nova = replace(nova, resultado_esperado=resultado_esperado)
            campos.append("resultado_esperado")
        if not campos:
            raise MutacaoRecusada("editar_ficha: nenhum campo informado")
        if "acao" in campos:
            # O título do nó do M1 É a ação: manter os dois em sincronia por dentro da raiz
            # evita a segunda fonte de verdade que envelheceria na primeira edição.
            with self._nucleo() as nucleo:
                nucleo.editar_no(no_id, titulo=nova.acao, em=em)
        else:
            self.projeto._exigir_ativo("editar_ficha")
            self.projeto._avancar(em)
        self._fichas[no_id] = nova
        self._emitir(FichaDePassoEditada, em, no_id=no_id, campos=tuple(campos))
        return nova

    def preceder(self, antes_id: UUID, depois_id: UUID, *, em: datetime, **kw) -> ArestaCausal:
        """A aresta da AT é **precedência**: o passo antes, o passo depois."""
        for identificador in (antes_id, depois_id):
            self.ficha(identificador)
        with self._nucleo() as nucleo:
            return nucleo.ligar(antes_id, depois_id, em=em, **kw)

    def excluir_precedencia(self, aresta_id: UUID, *, em: datetime) -> None:
        with self._nucleo() as nucleo:
            nucleo.excluir_aresta(aresta_id, em=em)

    def excluir_no(self, no_id: UUID, *, em: datetime) -> list[UUID]:
        self.ficha(no_id)
        with self._nucleo() as nucleo:
            removidas = nucleo.excluir_no(no_id, em=em)
        self._fichas.pop(no_id, None)
        return removidas

    def editar_no(self, no_id: UUID, *, em: datetime, **kw) -> No:
        """Editar o título é editar a AÇÃO — e a ficha acompanha, nunca diverge."""
        if "titulo" in kw and kw["titulo"] is not None and no_id in self._fichas:
            self.editar_ficha(no_id, acao=kw["titulo"], em=em)
            return self.projeto.no(no_id)
        with self._nucleo() as nucleo:
            return nucleo.editar_no(no_id, em=em, **kw)

    def mover_no(self, no_id: UUID, posicao: PosicaoNoCanvas, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.mover_no(no_id, posicao, em=em)

    def recolher_no(self, no_id: UUID, recolhido: bool, *, em: datetime) -> No:
        with self._nucleo() as nucleo:
            return nucleo.recolher_no(no_id, recolhido, em=em)

    # -- acompanhamento (RF-30, RF-31) -------------------------------------------

    def mudar_status(
        self,
        no_id: UUID,
        status: StatusDoPasso,
        *,
        em: datetime,
        motivo: str = "",
        resultado_real: str = "",
    ) -> FichaDePasso:
        """RF-30: bloquear exige motivo; concluir exige o resultado real.

        E o esperado **não** é sobrescrito: o real entra em campo próprio, e a divergência
        vai para o evento. Insumo para revisitar a árvore — nunca para apagar a promessa.
        """
        self.projeto._exigir_ativo("mudar_status")
        atual = self.ficha(no_id)
        novo = StatusDoPasso(status)
        if novo is atual.status:
            raise TransicaoDePassoRecusada("sem_mudanca", f"o passo já está {novo.value}")
        if novo is StatusDoPasso.BLOQUEADO and not (motivo or "").strip():
            raise TransicaoDePassoRecusada(
                "motivo_obrigatorio", "bloquear um passo exige dizer o que o bloqueia (RF-30)"
            )
        if novo is StatusDoPasso.CONCLUIDO and not (resultado_real or "").strip():
            raise TransicaoDePassoRecusada(
                "resultado_real_obrigatorio",
                "concluir um passo exige registrar o que ele produziu de fato (RF-30)",
            )
        ficha = replace(
            atual,
            status=novo,
            motivo_do_bloqueio=(motivo or "")[:LIMITE_MOTIVO]
            if novo is StatusDoPasso.BLOQUEADO
            else "",
            resultado_real=(resultado_real or "")[:LIMITE_RESULTADO]
            if novo is StatusDoPasso.CONCLUIDO
            else atual.resultado_real,
        )
        self._fichas[no_id] = ficha
        self.projeto._avancar(em)
        self._emitir(
            PassoMudouDeStatus,
            em,
            no_id=no_id,
            de=atual.status.value,
            para=novo.value,
            motivo_do_bloqueio=ficha.motivo_do_bloqueio,
            resultado_real=ficha.resultado_real if novo is StatusDoPasso.CONCLUIDO else "",
            divergente=ficha.divergente if novo is StatusDoPasso.CONCLUIDO else False,
        )
        return ficha

    def bloqueados(self) -> tuple[tuple[UUID, str], ...]:
        """RF-31: os passos bloqueados **com o motivo** — a lista que a Gestora abre."""
        return tuple(
            (no_id, ficha.motivo_do_bloqueio)
            for no_id, ficha in self.fichas()
            if ficha.status is StatusDoPasso.BLOQUEADO
        )

    def resumo_de_execucao(self) -> dict[str, int]:
        """RF-31: contagem por status no cabeçalho do projeto. Função pura."""
        contagem = {status.value: 0 for status in StatusDoPasso}
        for _, ficha in self.fichas():
            contagem[ficha.status.value] += 1
        contagem["passos"] = len(self._fichas)
        contagem["inalcancaveis"] = len(self.passos_inalcancaveis())
        return contagem

    # -- ordem e alcance (RF-32) -------------------------------------------------

    def _iniciais(self) -> tuple[UUID, ...]:
        """Os passos sem precedente — de onde a leitura começa."""
        com_precedente = {a.destino_id for a in self.projeto.arestas}
        return tuple(n.id for n in self.projeto.nos if n.id not in com_precedente)

    def ordem_de_leitura(self) -> tuple[UUID, ...]:
        """RF-32: a leitura segue a precedência declarada, e é reprodutível.

        Ordem canônica dentro de cada nível (por identificador): um plano que se lê em
        ordem diferente a cada abertura não se leva a lugar nenhum.
        """
        entrada = {n.id: 0 for n in self.projeto.nos}
        for aresta in self.projeto.arestas:
            if aresta.destino_id in entrada:
                entrada[aresta.destino_id] += 1
        saida = sucessores(self.projeto.arestas)
        restantes = set(entrada)
        ordem: list[UUID] = []
        while restantes:
            nivel = sorted((n for n in restantes if entrada[n] == 0), key=str)
            if not nivel:
                # Ciclo de precedência: o resto entra em ordem canônica, e os passos
                # inalcançáveis aparecem como pendência em `passos_inalcancaveis`.
                ordem.extend(sorted(restantes, key=str))
                break
            ordem.extend(nivel)
            for no in nivel:
                restantes.discard(no)
                for destino in saida.get(no, []):
                    if destino in entrada:
                        entrada[destino] -= 1
        return tuple(ordem)

    def passos_inalcancaveis(self) -> tuple[UUID, ...]:
        """RF-32: sem caminho desde os passos iniciais — pendência, nunca proibição."""
        saida = sucessores(self.projeto.arestas)
        alcancados: set[UUID] = set()
        for inicial in self._iniciais():
            alcancados.add(inicial)
            alcancados |= alcanca(inicial, saida)
        return tuple(
            sorted((n.id for n in self.projeto.nos if n.id not in alcancados), key=str)
        )

    # -- internos ------------------------------------------------------------------

    def _emitir(self, classe, em: datetime, **carga) -> None:
        self.projeto.eventos = self.projeto.eventos + (
            classe(
                projeto_id=self.projeto.id,
                dono=self.projeto.dono,
                instante=em,
                **carga,
            ),
        )


def novo_projeto_at(
    *,
    id: UUID,
    dono: DonoDoProjeto,
    nome: str,
    em: datetime,
    descricao_do_problema: str = "",
    alvo: Ponta | None = None,
) -> ProjetoAT:
    """Cria o `Projeto` do M1 com a ferramenta certa e o embrulha na raiz da AT."""
    projeto = Projeto(
        id=id,
        dono=dono,
        nome=nome,
        ferramenta=FERRAMENTA_AT,
        descricao_do_problema=texto_de_dominio(
            descricao_do_problema,
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        criado_em=em,
        alterado_em=em,
    )
    arvore = ProjetoAT(projeto=projeto, alvo=alvo)
    arvore._emitir(
        AtCriada,
        em,
        alvo_projeto_id=alvo.projeto_id if alvo else None,
        alvo_no_id=alvo.elementos[0] if alvo and alvo.elementos else None,
    )
    return arvore


def reidratar_at(
    projeto: Projeto,
    *,
    fichas: Mapping[UUID, FichaDePasso] | None = None,
    alvo: Ponta | None = None,
) -> ProjetoAT:
    """Monta a AT a partir do que estava GRAVADO — sem emitir evento nenhum."""
    arvore = ProjetoAT(projeto=projeto, alvo=alvo)
    arvore._fichas = dict(fichas or {})
    projeto.eventos = ()
    return arvore


__all__ = [
    "FERRAMENTA_AT",
    "TIPO_DE_NO_PASSO",
    "FichaDePasso",
    "PassoInvalido",
    "ProjetoAT",
    "StatusDoPasso",
    "TransicaoDePassoRecusada",
    "novo_projeto_at",
    "reidratar_at",
]
