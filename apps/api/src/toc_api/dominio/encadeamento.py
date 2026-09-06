"""M4 · E4.4 — o encadeamento: promover, semear e derivar (spec 008).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **OI** — Objetivo
Intermediário · **TOC** — Teoria das Restrições · **RF/RN** — requisito funcional / regra
de negócio.

**Este módulo é a razão de o M4 existir.** Sem ele, o módulo entregaria três ilhas novas —
exatamente o defeito D-11 com mais ferramentas. Com ele, a análise inteira fica
percorrível: o Efeito Indesejável validado alimenta a Nuvem de Conflito; a injeção
escolhida semeia a Árvore da Realidade Futura; o efeito futuro deriva a Árvore de
Pré-Requisitos; o objetivo intermediário vira a Árvore de Transição.

**Onde ele mora e por quê.** As quatro operações **leem** um agregado e **criam** outro,
mais a `ReferenciaCruzada`. Nenhuma delas cabe dentro de uma raiz só — e é por isso que
elas são funções de domínio deste módulo, e não métodos de `ProjetoARA` ou `NuvemDeConflito`:
um método que criasse o agregado vizinho faria uma raiz responder pelo estado da outra.
O módulo importa as cinco ferramentas; nenhuma delas o importa de volta.

**RN-13 — a cadeia só avança sobre material auditado.** Promover exige UDE `Validado`
(máquina de estados do M2); semear exige injeção `escolhida` (máquina de estados do M3).
As duas máquinas são consumidas, nunca reimplementadas nem afrouxadas — e a diferença
para o `derivar_nuvem_de_udes` do M3, que aceita "marcado e não rejeitado", é deliberada e
está escrita lá: *"Apertá-la é decisão do ciclo 008, que é quem executa a promoção"*.
É aqui, e é agora.

**Item 8 da constituição do projeto** (INT-04): promover, semear e derivar são
**manipulação direta do titular** — alvo nomeado pelo gesto, reversível por exclusão suave,
traço obrigatório. Aplicam na hora, sem tela de confirmação e sem máquina de estados de
proposta. Quem nasce proposta são as sugestões inferidas por modelo (`toc.suggest_*`).
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Iterable, Sequence
from uuid import UUID, uuid4

from .apr import (
    FERRAMENTA_APR,
    PapelNaAPR,
    ProjetoAPR,
    novo_projeto_apr,
)
from .ara import FERRAMENTA_ARA, ProjetoARA, StatusDeValidacao
from .arf import FERRAMENTA_ARF, PapelNaARF, ProjetoARF, novo_projeto_arf
from .at import FERRAMENTA_AT, ProjetoAT, novo_projeto_at
from .erros import MutacaoRecusada, NaoEncontrado
from .eventos import (
    ArfDerivouApr,
    InjecaoSemeouArf,
    OiDerivouAt,
    UdePromovidoParaNc,
)
from .nuvem import (
    FERRAMENTA_NC,
    NuvemDeConflito,
    ReferenciaDeOrigem,
    ReferenciaDeSemeadura,
    StatusDeInjecao,
    novo_projeto_nc,
)
from .referencia import (
    EstadoDaReferencia,
    Ponta,
    ReferenciaCruzada,
    TipoDeReferencia,
    # RN-12: mora em `referencia.py`, com o agregado que ela muda; é reexportada aqui
    # porque quem lê o encadeamento espera encontrar a contrapartida da criação.
    sincronizar_referencias,
)
from .valores import LIMITE_DESCRICAO, PosicaoNoCanvas, texto as texto_de_dominio

#: Os papéis que cada ponta declara. São vocabulário da cadeia, e é por eles que a ficha
#: de um elemento sabe dizer "origem: ARF <nome>, efeito <texto>" (RF-34).
PAPEL_UDE = "ude"
PAPEL_INJECAO = "injecao"
PAPEL_EFEITO_FUTURO = "efeito_futuro"
PAPEL_OBJETIVO_INTERMEDIARIO = "objetivo_intermediario"


class PromocaoInvalida(MutacaoRecusada):
    """RF-36/RF-37. `regra`: `sem_ude` · `no_nao_e_ude` · `ude_nao_validado` ·
    `origem_excluida`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class SemeaduraInvalida(MutacaoRecusada):
    """RF-38. `regra`: `injecao_nao_escolhida` · `injecao_ja_semeou` · `origem_excluida`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


class DerivacaoInvalidaDoM4(MutacaoRecusada):
    """RF-39/RF-40. `regra`: `origem_excluida` · `alvo_nao_e_efeito` · `alvo_nao_e_objetivo`."""

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra


@dataclass(frozen=True, slots=True)
class Promocao:
    """O que a promoção UDE → NC produz: a nuvem nova **e** a referência que a explica."""

    nuvem: NuvemDeConflito
    referencia: ReferenciaCruzada


@dataclass(frozen=True, slots=True)
class Semeadura:
    arf: ProjetoARF
    referencia: ReferenciaCruzada


@dataclass(frozen=True, slots=True)
class DerivacaoDeApr:
    apr: ProjetoAPR
    referencia: ReferenciaCruzada


@dataclass(frozen=True, slots=True)
class DerivacaoDeAt:
    at: ProjetoAT
    referencia: ReferenciaCruzada


def _exigir_origem_viva(projeto, erro: type[MutacaoRecusada], operacao: str) -> None:
    if projeto.excluido_em is not None:
        raise erro("origem_excluida", f"{operacao}: o projeto de origem está excluído")


# --------------------------------------------------------------------------------------
# RF-36/RF-37 — promoção UDE → NC (execução do INT-05 da spec 007)
# --------------------------------------------------------------------------------------


def promover_udes_para_nc(
    ara: ProjetoARA,
    *,
    no_ids: Sequence[UUID],
    id: UUID,
    nome: str,
    em: datetime,
    referencia_id: UUID | None = None,
) -> Promocao:
    """Promove UDEs **validados** de uma ARA para uma Nuvem de Conflito nova.

    Três recusas, cada uma com regra nomeada, e a terceira é a que o ciclo 008 aperta
    (RN-13): `sem_ude`, `no_nao_e_ude` e `ude_nao_validado`. A ARA é **lida, nunca
    escrita** — promover não emite evento nenhum do lado do M2, e o teste confere a versão
    do agregado de origem antes e depois.

    O dono da nuvem vem do **agregado de origem**, nunca do chamador: é o que faz o
    isolamento por inquilino ser consequência do tipo, e não disciplina de quem chama.
    """
    _exigir_origem_viva(ara.projeto, PromocaoInvalida, "promover_udes_para_nc")
    if not no_ids:
        raise PromocaoInvalida(
            "sem_ude", "a promoção parte de pelo menos um Efeito Indesejável validado"
        )

    enunciados: list[str] = []
    for no_id in no_ids:
        no = ara.projeto.no(no_id)  # NaoEncontrado quando o nó não é deste projeto
        if not ara.e_ude(no_id):
            raise PromocaoInvalida(
                "no_nao_e_ude",
                f"o nó {no_id} existe mas não está marcado como Efeito Indesejável",
            )
        if ara.status(no_id) is not StatusDeValidacao.VALIDADO:
            raise PromocaoInvalida(
                "ude_nao_validado",
                f"o Efeito Indesejável {no_id} está em {ara.status(no_id).value}; a cadeia "
                "nasce de sintoma auditado, não de rascunho (RN-13)",
            )
        enunciados.append(no.titulo)

    descricao = texto_de_dominio(
        "\n".join(
            ["Dilema por trás do(s) Efeito(s) Indesejável(is) validado(s):", *(f"- {e}" for e in enunciados)]
        ),
        campo="descricao_do_problema",
        minimo=0,
        maximo=LIMITE_DESCRICAO,
    )
    nuvem = novo_projeto_nc(
        id=id,
        dono=ara.projeto.dono,
        nome=nome,
        em=em,
        descricao_do_problema=descricao,
        # INT-02: a projeção local de leitura do lado da NC é preenchida na MESMA
        # operação que cria a referência — uma fonte, duas vistas.
        origem=ReferenciaDeOrigem(
            ferramenta=FERRAMENTA_ARA, projeto_id=ara.projeto.id, nos=tuple(no_ids)
        ),
    )
    referencia = ReferenciaCruzada.nomeada(
        id=referencia_id or uuid4(),
        tipo=TipoDeReferencia.PROMOCAO_UDE_NC,
        origem=Ponta(
            ferramenta=FERRAMENTA_ARA,
            projeto_id=ara.projeto.id,
            elementos=tuple(no_ids),
            papel=PAPEL_UDE,
        ),
        destino=Ponta(ferramenta=FERRAMENTA_NC, projeto_id=nuvem.projeto.id),
        dono=ara.projeto.dono,
        em=em,
    )
    nuvem._emitir(
        UdePromovidoParaNc,
        em,
        udes=tuple(no_ids),
        nc_projeto_id=nuvem.projeto.id,
        referencia_id=referencia.id,
    )
    return Promocao(nuvem=nuvem, referencia=referencia)


# --------------------------------------------------------------------------------------
# RF-38 — semeadura injeção → ARF (execução do INT-06 da spec 007)
# --------------------------------------------------------------------------------------


def semear_arf_de_injecao(
    nuvem: NuvemDeConflito,
    *,
    injecao_id: UUID,
    id: UUID,
    nome: str,
    em: datetime,
    referencia_id: UUID | None = None,
) -> Semeadura:
    """A injeção **escolhida** semeia uma ARF nova, com ela como primeiro nó (RF-06).

    Diferente da promoção, aqui a origem **é escrita**: a `ReferenciaDeSemeadura` da
    injeção passa a apontar o projeto criado (INT-03/INT-06). É a projeção local de
    leitura que o ciclo 007 deixou preparada e vazia, preenchida na mesma operação que
    cria a referência cruzada.

    Os UDEs da cadeia viajam junto: eles vêm da `ReferenciaDeOrigem` da nuvem, e é isso
    que dá à ARF o conjunto contra o qual o espelho UDE → ED é conferido (RN-03).
    """
    _exigir_origem_viva(nuvem.projeto, SemeaduraInvalida, "semear_arf_de_injecao")
    injecao = nuvem.injecao(injecao_id)  # NaoEncontrado quando não é desta nuvem
    if injecao.status is not StatusDeInjecao.ESCOLHIDA:
        raise SemeaduraInvalida(
            "injecao_nao_escolhida",
            f"a injeção {injecao_id} está em {injecao.status.value}; só a injeção "
            "escolhida semeia a Árvore da Realidade Futura (RN-13)",
        )
    if injecao.semeadura is not None and injecao.semeadura.projeto_destino_id is not None:
        raise SemeaduraInvalida(
            "injecao_ja_semeou",
            f"a injeção {injecao_id} já semeou a árvore "
            f"{injecao.semeadura.projeto_destino_id}",
        )

    udes = nuvem.origem.nos if nuvem.origem else ()
    arf = novo_projeto_arf(
        id=id,
        dono=nuvem.projeto.dono,
        nome=nome,
        em=em,
        descricao_do_problema=texto_de_dominio(
            f"Realidade futura semeada pela injeção escolhida: {injecao.texto}",
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        origem=Ponta(
            ferramenta=FERRAMENTA_NC,
            projeto_id=nuvem.projeto.id,
            elementos=(injecao_id,),
            papel=PAPEL_INJECAO,
        ),
        udes_da_cadeia=udes,
    )
    # RF-06: o nó semente nasce com o texto da injeção — editável dali em diante sem
    # quebrar a referência, porque quem guarda o vínculo é a `ReferenciaCruzada`, não o
    # texto do nó.
    arf.adicionar_injecao(titulo=injecao.texto, em=em, posicao=PosicaoNoCanvas(0.0, 0.0))

    referencia = ReferenciaCruzada.nomeada(
        id=referencia_id or uuid4(),
        tipo=TipoDeReferencia.SEMEADURA_INJECAO_ARF,
        origem=Ponta(
            ferramenta=FERRAMENTA_NC,
            projeto_id=nuvem.projeto.id,
            elementos=(injecao_id,),
            papel=PAPEL_INJECAO,
        ),
        destino=Ponta(ferramenta=FERRAMENTA_ARF, projeto_id=arf.projeto.id),
        dono=nuvem.projeto.dono,
        em=em,
    )
    injecao.semeadura = ReferenciaDeSemeadura(
        injecao_id=injecao_id, projeto_destino_id=arf.projeto.id
    )
    nuvem.projeto._avancar(em)
    nuvem._emitir(
        InjecaoSemeouArf,
        em,
        injecao_id=injecao_id,
        arf_projeto_id=arf.projeto.id,
        referencia_id=referencia.id,
    )
    return Semeadura(arf=arf, referencia=referencia)


# --------------------------------------------------------------------------------------
# RF-39 e RF-40 — as derivações do lado de baixo da cadeia
# --------------------------------------------------------------------------------------


def derivar_apr_de_arf(
    arf: ProjetoARF,
    *,
    no_id: UUID,
    id: UUID,
    nome: str,
    em: datetime,
    objetivo: str | None = None,
    referencia_id: UUID | None = None,
) -> DerivacaoDeApr:
    """Deriva a APR de implementação a partir de um efeito futuro (ou injeção) da ARF.

    O objetivo da APR é **proposto** do texto escolhido pelo gesto e continua editável
    (RF-39): a APR verbaliza o objetivo no presente, e quem o escreve é o grupo. A
    referência guarda o vínculo, então editar o texto não quebra nada.
    """
    _exigir_origem_viva(arf.projeto, DerivacaoInvalidaDoM4, "derivar_apr_de_arf")
    papel = arf.papel_do_no(no_id)  # NaoEncontrado quando o nó não é deste projeto
    texto = arf.projeto.no(no_id).titulo
    proposto = objetivo if objetivo is not None else _objetivo_proposto(papel, texto)

    apr = novo_projeto_apr(
        id=id,
        dono=arf.projeto.dono,
        nome=nome,
        objetivo=proposto,
        em=em,
        descricao_do_problema=texto_de_dominio(
            f"Implementação derivada da Árvore da Realidade Futura: {texto}",
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        origem=Ponta(
            ferramenta=FERRAMENTA_ARF,
            projeto_id=arf.projeto.id,
            elementos=(no_id,),
            papel=papel.value,
        ),
    )
    referencia = ReferenciaCruzada.nomeada(
        id=referencia_id or uuid4(),
        tipo=TipoDeReferencia.DERIVACAO_ARF_APR,
        origem=Ponta(
            ferramenta=FERRAMENTA_ARF,
            projeto_id=arf.projeto.id,
            elementos=(no_id,),
            papel=papel.value,
        ),
        destino=Ponta(ferramenta=FERRAMENTA_APR, projeto_id=apr.projeto.id),
        dono=arf.projeto.dono,
        em=em,
    )
    arf._emitir(
        ArfDerivouApr,
        em,
        origem_no_id=no_id,
        apr_projeto_id=apr.projeto.id,
        referencia_id=referencia.id,
    )
    return DerivacaoDeApr(apr=apr, referencia=referencia)


def _objetivo_proposto(papel: PapelNaARF, texto: str) -> str:
    """O texto que a APR recebe como objetivo — proposta, nunca imposição.

    A injeção descreve o que **passa a existir**; o efeito futuro descreve o que **passa a
    ser verdade**. Nos dois casos o objetivo da APR é a implantação daquilo, e é isso que
    o prefixo diz — em português, no presente, do jeito que a APR exige.
    """
    if papel is PapelNaARF.INJECAO:
        return f"A injeção está implantada: {texto}"
    return f"O efeito está alcançado: {texto}"


def derivar_at_de_oi(
    apr: ProjetoAPR,
    *,
    no_id: UUID,
    id: UUID,
    nome: str,
    em: datetime,
    referencia_id: UUID | None = None,
) -> DerivacaoDeAt:
    """Cria a AT de um objetivo intermediário (ou do objetivo) da APR — RF-40.

    Obstáculo **não** deriva AT: ele é a condição que existe hoje, e descer uma condição
    a passos seria planejar a execução do problema. A recusa tem regra nomeada.
    """
    _exigir_origem_viva(apr.projeto, DerivacaoInvalidaDoM4, "derivar_at_de_oi")
    papel = apr.papel_do_no(no_id)
    if papel is PapelNaAPR.OBSTACULO:
        raise DerivacaoInvalidaDoM4(
            "alvo_nao_e_objetivo",
            f"o nó {no_id} é um obstáculo; a Árvore de Transição desce um objetivo "
            "intermediário (ou o objetivo) a passos, nunca a condição que bloqueia",
        )
    texto = apr.projeto.no(no_id).titulo
    alvo = Ponta(
        ferramenta=FERRAMENTA_APR,
        projeto_id=apr.projeto.id,
        elementos=(no_id,),
        papel=papel.value,
    )
    at = novo_projeto_at(
        id=id,
        dono=apr.projeto.dono,
        nome=nome,
        em=em,
        descricao_do_problema=texto_de_dominio(
            f"Transição derivada do objetivo intermediário: {texto}",
            campo="descricao_do_problema",
            minimo=0,
            maximo=LIMITE_DESCRICAO,
        ),
        alvo=alvo,
    )
    referencia = ReferenciaCruzada.nomeada(
        id=referencia_id or uuid4(),
        tipo=TipoDeReferencia.DERIVACAO_OI_AT,
        origem=alvo,
        destino=Ponta(ferramenta=FERRAMENTA_AT, projeto_id=at.projeto.id),
        dono=apr.projeto.dono,
        em=em,
    )
    apr._emitir(
        OiDerivouAt,
        em,
        objetivo_intermediario_id=no_id,
        at_projeto_id=at.projeto.id,
        referencia_id=referencia.id,
    )
    return DerivacaoDeAt(at=at, referencia=referencia)


__all__ = [
    "PAPEL_EFEITO_FUTURO",
    "PAPEL_INJECAO",
    "PAPEL_OBJETIVO_INTERMEDIARIO",
    "PAPEL_UDE",
    "DerivacaoDeApr",
    "DerivacaoDeAt",
    "DerivacaoInvalidaDoM4",
    "Promocao",
    "PromocaoInvalida",
    "Semeadura",
    "SemeaduraInvalida",
    "derivar_apr_de_arf",
    "derivar_at_de_oi",
    "promover_udes_para_nc",
    "semear_arf_de_injecao",
    "sincronizar_referencias",
]
