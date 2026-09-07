"""E1.4 — exportação consolidada e importação, como domínio puro (spec 011, RF-31, RF-32).

Siglas, uma vez neste arquivo: **ARA** — Árvore da Realidade Atual · **UDE** — Efeito
Indesejável · **NC** — Nuvem de Conflito · **ARF** — Árvore da Realidade Futura · **APR**
— Árvore de Pré-Requisitos · **AT** — Árvore de Transição · **S&T** — Estratégia &
Táticas · **OI** — Objetivo Intermediário · **TOC** — Teoria das Restrições · **JSON** —
*JavaScript Object Notation* · **UUID** — identificador único universal · **RF/RN** —
requisito funcional / regra de negócio.

**O problema que ele resolve.** A US-17 da spec 011 diz em uma linha: "quero exportar a
análise completa, e não seis arquivos soltos". Uma análise da TOC atravessa cinco
ferramentas e o que costura as cinco são os **vínculos** — e vínculo é justamente o que
não cabe dentro de nenhum dos arquivos separados. Daí o arquivo único, com uma seção por
ferramenta e os vínculos no mesmo documento.

**Onde ele mora e por quê.** Aqui, no domínio, pelo mesmo motivo de `encadeamento.py`: a
operação **lê vários agregados** e não cabe dentro de nenhuma raiz — um método de
`ProjetoARA` que exportasse a cadeia faria uma raiz responder pelo estado das outras. Este
módulo importa as ferramentas; nenhuma delas o importa de volta.

**Três regras que valem aqui, e cada uma é um teste:**

- **RN-05 — importar nunca muta projeto existente.** O resultado é sempre projeto NOVO. A
  garantia não é disciplina: **todo identificador do documento é reescrito** antes de
  qualquer construção, num mapa de uma passada só. Como a reescrita é total, as referências
  internas (o exame que aponta para a aresta, a injeção que aponta para a premissa, o
  vínculo que aponta para os dois projetos) continuam consistentes — e nenhuma delas pode
  colidir com o que já está no banco do destino.
- **RF-27 — validar o arquivo INTEIRO antes de qualquer efeito.** Sem relato não há
  escrita, e o relato é campo a campo (caminho do campo + motivo). O contraste medido é
  `tocbuilderv3/components/NodeZoneView.tsx:314-317`: três campos conferidos, `alert()`
  genérico, resto passando.
- **RN-06 — todo descarte é declarado.** Um export parcial (só a NC, sem a ARA) traz
  ponteiro para projeto que não veio junto; ele **não** é importado apontando para o vazio:
  é podado e **dito** no relato.

**O que NÃO viaja no documento, e a ausência é desenho:**

| Não viaja | Por quê |
|---|---|
| inquilino e usuário | identidade é da fundação; importar num destino é adotar a identidade de LÁ |
| `versao` do agregado | é estado de sincronia com o repositório (a trava otimista), não conteúdo |
| `excluido_em` | a importação nasce ativa; a lixeira é do destino |
| eventos | importar não é viver a análise de novo (mesma regra de `reidratar_*`) |

**Ferramenta com documento próprio.** A S&T (RF-21 da spec 010) e a jornada de focalização
(RF-18 da spec 009) já têm formato canônico versionado e importador próprio. Elas **não**
ganham um segundo formato aqui: a entrada delas declara `forma:
"documento_da_ferramenta"` e carrega o documento delas. Um segundo formato para o mesmo
conteúdo é a dívida que a linhagem pagava com `stepNumber` digitado e `edges` livres
contando histórias diferentes.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Callable, Iterable, Mapping, Sequence
from uuid import UUID, uuid4

from .apr import ElipseDeSimultaneidade, FERRAMENTA_APR, ParObstaculoOI, ProjetoAPR, reidratar_apr
from .ara import (
    FERRAMENTA_ARA,
    FichaDeUde,
    ParecerDeJulgamento,
    ProjetoARA,
    StatusDeValidacao,
    reidratar_ara,
)
from .arf import EspelhoDeUde, FERRAMENTA_ARF, ProjetoARF, RamoNegativo, reidratar_arf
from .at import FERRAMENTA_AT, FichaDePasso, ProjetoAT, reidratar_at
from .erros import ErroDeDominio
from .focalizacao import (
    FERRAMENTA_FOCALIZACAO,
    AnaliseDeFocalizacao,
    exportar_analise,
    importar_analise,
)
from .grafo import ArestaCausal, No
from .identidade import DonoDoProjeto
from .nuvem import (
    FERRAMENTA_NC,
    Injecao,
    NuvemDeConflito,
    Premissa,
    ReferenciaDeOrigem,
    reidratar_nuvem,
)
from .projeto import Projeto
from .referencia import Ponta, ReferenciaCruzada, TipoDeReferencia, reidratar_referencia
from .serializacao import codificar, decodificar
from .snt import ArvoreSnT, FERRAMENTA_SNT, exportar_arvore_snt, importar_arvore_snt
from .suficiencia import ConectorE, Exame
from .valores import FERRAMENTA_GENERICA

#: A versão do formato consolidado. Viaja no documento porque arquivo sem versão é arquivo
#: que ninguém migra depois — a mesma razão escrita em `toc.snt/1` e `toc.focalizacao/1`.
VERSAO_DO_CONSOLIDADO = "toc.consolidado/1"

#: A ordem em que as ferramentas saem no arquivo. É a ordem da cadeia da TOC — realidade
#: atual, conflito, futuro, pré-requisitos, transição —, e é fixa para o arquivo ser
#: comparável entre duas execuções (a mesma exigência do determinismo do M5 e do M6).
ORDEM_CANONICA = (
    FERRAMENTA_GENERICA,
    FERRAMENTA_ARA,
    FERRAMENTA_NC,
    FERRAMENTA_ARF,
    FERRAMENTA_APR,
    FERRAMENTA_AT,
    FERRAMENTA_SNT,
    FERRAMENTA_FOCALIZACAO,
)

FORMA_NUCLEO = "nucleo_e_secao"
FORMA_DOCUMENTO = "documento_da_ferramenta"


# ---------------------------------------------------------------------------------------
# O relato — objeto de valor puro (spec 011, § Entidades)
# ---------------------------------------------------------------------------------------


@dataclass(frozen=True, slots=True)
class ProblemaDeImportacao:
    """Um problema, com o CAMINHO do campo e o motivo — nunca uma caixa de alerta."""

    campo: str
    motivo: str


@dataclass(frozen=True, slots=True)
class DescarteDeclarado:
    """RN-06: o que a importação deixou de fora, dito por escrito e contado."""

    campo: str
    motivo: str
    quantidade: int = 1


@dataclass(frozen=True, slots=True)
class RelatoDeImportacao:
    """Resultado puro da validação: contagens, problemas e descartes declarados."""

    contagens: Mapping[str, int] = field(default_factory=dict)
    problemas: tuple[ProblemaDeImportacao, ...] = ()
    descartes: tuple[DescarteDeclarado, ...] = ()

    @property
    def aceito(self) -> bool:
        return not self.problemas


@dataclass(frozen=True, slots=True)
class ResultadoDaImportacao:
    """O que a importação devolve. `projetos` vazio quando o relato não foi aceito."""

    relato: RelatoDeImportacao
    projetos: tuple[Any, ...] = ()
    vinculos: tuple[ReferenciaCruzada, ...] = ()


# ---------------------------------------------------------------------------------------
# Exportação
# ---------------------------------------------------------------------------------------


def exportar_consolidado(
    projetos: Iterable[Any],
    *,
    vinculos: Iterable[ReferenciaCruzada] = (),
    exportado_em: datetime,
) -> dict:
    """O documento único da análise — determinístico, sem identidade e sem eventos.

    `projetos` são os agregados de raiz (`ProjetoARA`, `NuvemDeConflito`, `ProjetoARF`,
    `ProjetoAPR`, `ProjetoAT`, `ArvoreSnT`, `AnaliseDeFocalizacao`) ou um `Projeto`
    genérico do M1. O instante entra por argumento: relógio é porta, e o domínio não o lê.
    """
    entradas = [_exportar_projeto(agregado) for agregado in projetos]
    elos = [_exportar_vinculo(v) for v in vinculos]

    # A ordem canônica é calculada sobre o documento INTEIRO, e não projeto a projeto: a
    # Nuvem de Conflito guarda a lista dos Efeitos Indesejáveis de origem, que são nós da
    # Árvore da Realidade Atual — de OUTRA entrada. Uma tabela de chaves por projeto não
    # conheceria aqueles nós, e a lista sairia ordenada pelo identificador cru, que é
    # exatamente o que muda na importação.
    chaves = _chaves_de_conteudo({"projetos": entradas, "vinculos": elos})
    entradas = [_ordenar(entrada, chaves) for entrada in entradas]
    elos = [_ordenar(elo, chaves) for elo in elos]

    entradas.sort(key=_ordem_da_entrada)
    elos.sort(key=lambda elo: _ordem_do_vinculo(elo, chaves))
    return {
        "versao": VERSAO_DO_CONSOLIDADO,
        "exportado_em": exportado_em.isoformat(),
        "projetos": entradas,
        "vinculos": elos,
    }


def _ordem_da_entrada(entrada: Mapping[str, Any]) -> tuple[int, str, str]:
    ferramenta = str(entrada["ferramenta"])
    posicao = ORDEM_CANONICA.index(ferramenta) if ferramenta in ORDEM_CANONICA else len(ORDEM_CANONICA)
    return (posicao, str(entrada.get("nome", "")), str(entrada["id"]))


#: A ordem dos vínculos no arquivo: a da cadeia da TOC (promoção → semeadura → derivações),
#: depois o instante, depois o CONTEÚDO. O desempate por conteúdo e não por identificador é
#: a mesma razão da ordem canônica dos nós: identificador muda na importação.
_ORDEM_DO_TIPO = {tipo.value: i for i, tipo in enumerate(TipoDeReferencia)}


def _ordem_do_vinculo(elo: Mapping[str, Any], chaves: dict[str, str]) -> tuple:
    return (
        _ORDEM_DO_TIPO.get(str(elo.get("tipo")), len(_ORDEM_DO_TIPO)),
        str(elo.get("criada_em", "")),
        _assinatura(elo, chaves, sem_id=True),
    )


def _exportar_projeto(agregado: Any) -> dict:
    projeto = agregado.projeto if hasattr(agregado, "projeto") else agregado
    ferramenta = projeto.ferramenta
    if ferramenta in _DELEGADOS:
        return {
            "id": str(projeto.id),
            "ferramenta": ferramenta,
            "forma": FORMA_DOCUMENTO,
            "secao": _DELEGADOS[ferramenta][0](agregado),
        }
    return (
        {
            "id": str(projeto.id),
            "ferramenta": ferramenta,
            "forma": FORMA_NUCLEO,
            "nome": projeto.nome,
            "descricao_do_problema": projeto.descricao_do_problema,
            "criado_em": projeto.criado_em.isoformat(),
            "alterado_em": projeto.alterado_em.isoformat(),
            "nos": [codificar(no) for no in projeto.nos],
            "arestas": [codificar(aresta) for aresta in projeto.arestas],
            "secao": _SECAO_POR_FERRAMENTA.get(ferramenta, _secao_vazia)(agregado),
        }
    )


# ---------------------------------------------------------------------------------------
# Ordem canônica: o documento é ordenado pelo CONTEÚDO, nunca pelo identificador
# ---------------------------------------------------------------------------------------
#
# **O defeito que isto conserta, e como ele apareceu.** A ida e volta contra o PostgreSQL
# real ficou vermelha com o conteúdo inteiro e certo: só a ORDEM das linhas mudava. A
# causa está no adaptador, e é legítima — ele devolve os nós por `(criado_em, id)`
# (`infra/persistencia/repositorio_projetos.py:560`) e os cinco nós de uma Nuvem de
# Conflito nascem no MESMO instante, logo o desempate é por identificador. Como a
# importação dá identificadores novos, a segunda exportação saía em outra ordem.
#
# Ordenar por identificador não resolve (é ele que muda) e "confiar na ordem do banco"
# não resolve (é ela que varia). O que não varia é o **conteúdo**: a chave de ordenação de
# cada item é a serialização dele com o identificador PRÓPRIO removido e toda referência
# substituída pela chave do item referido. Como uma aresta referencia nós e uma injeção
# referencia uma premissa, as chaves se estabilizam em poucas passadas — daí o
# refinamento iterativo abaixo.
#
# **Limite declarado**: dois itens com conteúdo byte a byte idêntico (mesmo título, mesma
# descrição, mesma posição no canvas) são indistinguíveis para esta ordenação, como são
# para quem lê a tela. Eles atravessam a ida e volta como conjunto; qual dos dois recebe
# qual identificador novo não é decidido aqui.

#: Quantas passadas de refinamento. A cadeia de referência mais longa do modelo é
#: `injeção → premissa → aresta → nó` (quatro níveis); quatro passadas a percorrem
#: inteira, e uma quinta não mudaria nada.
PASSADAS_DE_REFINAMENTO = 4


def _chaves_de_conteudo(valor: Any) -> dict[str, str]:
    objetos: dict[str, Any] = {}
    _coletar(valor, objetos)
    chaves: dict[str, str] = {identificador: "" for identificador in objetos}
    for _ in range(PASSADAS_DE_REFINAMENTO):
        novas = {
            identificador: _assinatura(objeto, chaves, sem_id=True)
            for identificador, objeto in objetos.items()
        }
        if novas == chaves:
            break
        chaves = novas
    return chaves


def _coletar(valor: Any, objetos: dict[str, Any]) -> None:
    if isinstance(valor, dict):
        identificador = valor.get("id")
        if _e_uuid(identificador):
            objetos[str(UUID(str(identificador)))] = valor
        for item in valor.values():
            _coletar(item, objetos)
    elif isinstance(valor, list):
        for item in valor:
            _coletar(item, objetos)


def _assinatura(valor: Any, chaves: dict[str, str], *, sem_id: bool = False) -> str:
    """A serialização do valor com identificador trocado pela chave do que ele nomeia."""
    if isinstance(valor, dict):
        partes = [
            f"{k}={_assinatura(v, chaves)}"
            for k, v in sorted(valor.items())
            if not (sem_id and k == "id")
        ]
        return "{" + ";".join(partes) + "}"
    if isinstance(valor, list):
        return "[" + ";".join(_assinatura(item, chaves) for item in valor) + "]"
    if _e_uuid(valor):
        return chaves.get(str(UUID(str(valor))), "?")
    return repr(valor)


def _ordenar(valor: Any, chaves: dict[str, str]) -> Any:
    if isinstance(valor, dict):
        if valor and all(_e_uuid(k) for k in valor):
            # Dicionário indexado por identificador (fichas, exames, status): a ordem das
            # chaves é a do que elas nomeiam.
            return {
                k: _ordenar(v, chaves)
                for k, v in sorted(
                    valor.items(), key=lambda par: chaves.get(str(UUID(par[0])), par[0])
                )
            }
        return {k: _ordenar(v, chaves) for k, v in valor.items()}
    if isinstance(valor, list):
        itens = [_ordenar(item, chaves) for item in valor]
        if itens and all(_e_uuid(i) for i in itens):
            # Lista de referências (as arestas de um conector, os UDEs da cadeia): é
            # conjunto, e a ordem dela não carrega significado nenhum.
            return sorted(itens, key=lambda i: chaves.get(str(UUID(i)), i))
        if itens and all(isinstance(i, dict) and _e_uuid(i.get("id")) for i in itens):
            # Lista de entidades (nós, arestas, premissas, injeções, ramos, pares…).
            return sorted(itens, key=lambda i: _assinatura(i, chaves, sem_id=True))
        # Todo o resto — pareceres, julgamentos, decisões — fica NA ORDEM EM QUE VEIO.
        # São históricos: reordená-los por conteúdo trocaria cronologia por alfabeto.
        return itens
    return valor


def _exportar_vinculo(vinculo: ReferenciaCruzada) -> dict:
    return {
        "id": str(vinculo.id),
        "tipo": vinculo.tipo.value,
        "origem": codificar(vinculo.origem),
        "destino": codificar(vinculo.destino),
        "estado": vinculo.estado.value,
        "motivo": vinculo.motivo,
        "criada_em": vinculo.criada_em.isoformat(),
    }


def _secao_vazia(_agregado: Any) -> dict:
    return {}


def _secao_da_ara(ara: ProjetoARA) -> dict:
    return {
        "udes": codificar(ara._udes),
        "status": codificar(ara._status),
        "pareceres": codificar(ara._pareceres),
        "exames": codificar(ara._exames),
        "conectores": codificar(sorted(ara._conectores.values(), key=lambda c: str(c.id))),
    }


def _secao_da_nuvem(nuvem: NuvemDeConflito) -> dict:
    return {
        "racional": nuvem.racional,
        "origem": codificar(nuvem.origem),
        "premissas": codificar(sorted(nuvem._premissas.values(), key=lambda p: (p.aresta.value, p.ordem, str(p.id)))),
        "injecoes": codificar(sorted(nuvem._injecoes.values(), key=lambda i: str(i.id))),
    }


def _secao_da_arf(arf: ProjetoARF) -> dict:
    return {
        "origem": codificar(arf.origem),
        "udes_da_cadeia": codificar(list(arf.udes_da_cadeia)),
        "espelhos": codificar(arf._espelhos),
        "ramos": codificar(sorted(arf._ramos.values(), key=lambda r: str(r.id))),
        "exames": codificar(arf._exames),
        "conectores": codificar(sorted(arf._conectores.values(), key=lambda c: str(c.id))),
    }


def _secao_da_apr(apr: ProjetoAPR) -> dict:
    return {
        "origem": codificar(apr.origem),
        "pares": codificar(sorted(apr._pares.values(), key=lambda p: str(p.id))),
        "elipses": codificar(sorted(apr._elipses.values(), key=lambda e: str(e.id))),
    }


def _secao_da_at(at: ProjetoAT) -> dict:
    return {"alvo": codificar(at.alvo), "fichas": codificar(at._fichas)}


_SECAO_POR_FERRAMENTA: dict[str, Callable[[Any], dict]] = {
    FERRAMENTA_ARA: _secao_da_ara,
    FERRAMENTA_NC: _secao_da_nuvem,
    FERRAMENTA_ARF: _secao_da_arf,
    FERRAMENTA_APR: _secao_da_apr,
    FERRAMENTA_AT: _secao_da_at,
}

#: As ferramentas que já têm formato canônico próprio: aqui se DELEGA, não se reinventa.
_DELEGADOS: dict[str, tuple[Callable[[Any], dict], str]] = {
    FERRAMENTA_SNT: (exportar_arvore_snt, "toc.snt/1"),
    FERRAMENTA_FOCALIZACAO: (exportar_analise, "toc.focalizacao/1"),
}


# ---------------------------------------------------------------------------------------
# Esqueleto — a comparação da ida e volta (RF-32)
# ---------------------------------------------------------------------------------------


def esqueleto(documento: Mapping[str, Any]) -> dict:
    """O documento com identificador e carimbo de exportação normalizados.

    RF-32 pede arquivo "estruturalmente idêntico, **a menos de identificadores e carimbos
    de tempo**" — logo a comparação precisa de uma forma canônica. Cada UUID vira `#N` na
    ordem em que aparece (ordem que é determinística porque a exportação é), e o instante
    da exportação sai. **Só isso**: se esta função apagasse mais alguma coisa, a ida e
    volta passaria verde sobre conteúdo perdido, que é exatamente o que ela existe para
    pegar.
    """
    mapa: dict[str, str] = {}
    limpo = {chave: valor for chave, valor in documento.items() if chave != "exportado_em"}
    return _normalizar(limpo, mapa)


def _normalizar(valor: Any, mapa: dict[str, str]) -> Any:
    if isinstance(valor, dict):
        return {_normalizar_texto(k, mapa): _normalizar(v, mapa) for k, v in valor.items()}
    if isinstance(valor, list):
        return [_normalizar(item, mapa) for item in valor]
    if isinstance(valor, str):
        return _normalizar_texto(valor, mapa)
    return valor


def _normalizar_texto(valor: str, mapa: dict[str, str]) -> str:
    if not _e_uuid(valor):
        return valor
    canonico = str(UUID(valor))
    if canonico not in mapa:
        mapa[canonico] = f"#{len(mapa)}"
    return mapa[canonico]


def _e_uuid(valor: Any) -> bool:
    if not isinstance(valor, str) or len(valor) != 36:
        return False
    try:
        UUID(valor)
    except ValueError:
        return False
    return True


# ---------------------------------------------------------------------------------------
# Importação
# ---------------------------------------------------------------------------------------


def importar_consolidado(
    documento: Any,
    *,
    dono: DonoDoProjeto,
    novo_id: Callable[[], UUID] = uuid4,
) -> ResultadoDaImportacao:
    """Valida o arquivo inteiro, e só então constrói — projetos NOVOS, sempre (RN-05).

    Não levanta exceção por conteúdo: conteúdo errado vira **problema no relato**, com o
    caminho do campo. Levantar aqui daria à interface uma mensagem só para um arquivo com
    dez erros, que é o defeito da linhagem que o RF-27 corrige.
    """
    problemas: list[ProblemaDeImportacao] = []
    if not isinstance(documento, Mapping):
        return ResultadoDaImportacao(
            RelatoDeImportacao(
                problemas=(
                    ProblemaDeImportacao("documento", "esperava um objeto JSON no topo"),
                ),
            )
        )

    versao = documento.get("versao")
    if versao != VERSAO_DO_CONSOLIDADO:
        return ResultadoDaImportacao(
            RelatoDeImportacao(
                problemas=(
                    ProblemaDeImportacao(
                        "versao",
                        f"documento de versão {versao!r}; esta aplicação lê "
                        f"{VERSAO_DO_CONSOLIDADO!r}",
                    ),
                )
            )
        )

    entradas = documento.get("projetos")
    if not isinstance(entradas, Sequence) or isinstance(entradas, (str, bytes)):
        problemas.append(ProblemaDeImportacao("projetos", "esperava uma lista de projetos"))
        return ResultadoDaImportacao(RelatoDeImportacao(problemas=tuple(problemas)))
    brutos_de_vinculo = documento.get("vinculos") or []
    if not isinstance(brutos_de_vinculo, Sequence) or isinstance(brutos_de_vinculo, (str, bytes)):
        problemas.append(ProblemaDeImportacao("vinculos", "esperava uma lista de vínculos"))
        return ResultadoDaImportacao(RelatoDeImportacao(problemas=tuple(problemas)))

    # -- 1. validação, campo a campo, ANTES de qualquer construção ----------------------
    projetos_do_arquivo: set[str] = set()
    elementos_do_arquivo: set[str] = set()
    for posicao, entrada in enumerate(entradas):
        caminho = f"projetos[{posicao}]"
        if not isinstance(entrada, Mapping):
            problemas.append(ProblemaDeImportacao(caminho, "esperava um objeto de projeto"))
            continue
        _validar_entrada(entrada, caminho, problemas, projetos_do_arquivo, elementos_do_arquivo)

    for posicao, bruto in enumerate(brutos_de_vinculo):
        _validar_vinculo(bruto, f"vinculos[{posicao}]", problemas, projetos_do_arquivo)

    if problemas:
        return ResultadoDaImportacao(RelatoDeImportacao(problemas=tuple(problemas)))

    # -- 2. identidade nova para tudo, de uma passada só (RN-05) -----------------------
    mapa: dict[str, str] = {}
    renomeado = _renomear(dict(documento), mapa, novo_id)
    conhecidos = {_uuid(mapa[chave]) for chave in projetos_do_arquivo}

    # -- 3. construção -----------------------------------------------------------------
    descartes: list[DescarteDeclarado] = []
    projetos: list[Any] = []
    try:
        for entrada in renomeado["projetos"]:
            projetos.append(_construir(entrada, dono=dono, conhecidos=conhecidos, descartes=descartes))
        vinculos = tuple(
            _construir_vinculo(bruto, dono=dono) for bruto in renomeado.get("vinculos", [])
        )
    except ErroDeDominio as erro:
        # Rede de segurança: o que a validação não previu vira problema, nunca meia
        # importação. Um agregado construído pela metade seria pior que a recusa.
        return ResultadoDaImportacao(
            RelatoDeImportacao(
                problemas=(ProblemaDeImportacao("documento", f"conteúdo recusado: {erro}"),)
            )
        )

    contagens = {
        "projetos": len(projetos),
        "nos": sum(len(_projeto(p).nos) for p in projetos),
        "arestas": sum(len(_projeto(p).arestas) for p in projetos),
        "vinculos": len(vinculos),
    }
    return ResultadoDaImportacao(
        RelatoDeImportacao(contagens=contagens, descartes=tuple(descartes)),
        projetos=tuple(projetos),
        vinculos=vinculos,
    )


def _projeto(agregado: Any) -> Projeto:
    return agregado.projeto if hasattr(agregado, "projeto") else agregado


# -- validação --------------------------------------------------------------------------


def _validar_entrada(
    entrada: Mapping[str, Any],
    caminho: str,
    problemas: list[ProblemaDeImportacao],
    projetos: set[str],
    elementos: set[str],
) -> None:
    identificador = entrada.get("id")
    if not _e_uuid(identificador):
        problemas.append(ProblemaDeImportacao(f"{caminho}.id", "identificador ausente ou inválido"))
    else:
        projetos.add(str(UUID(str(identificador))))

    ferramenta = entrada.get("ferramenta")
    if ferramenta not in ORDEM_CANONICA:
        problemas.append(
            ProblemaDeImportacao(
                f"{caminho}.ferramenta",
                f"ferramenta {ferramenta!r} não é conhecida por esta aplicação",
            )
        )
        return

    forma = entrada.get("forma")
    if ferramenta in _DELEGADOS:
        if forma != FORMA_DOCUMENTO:
            problemas.append(
                ProblemaDeImportacao(
                    f"{caminho}.forma",
                    f"{ferramenta} exporta pelo documento próprio: esperava {FORMA_DOCUMENTO!r}",
                )
            )
            return
        secao = entrada.get("secao")
        esperada = _DELEGADOS[ferramenta][1]
        if not isinstance(secao, Mapping) or secao.get("versao") != esperada:
            problemas.append(
                ProblemaDeImportacao(
                    f"{caminho}.secao.versao",
                    f"esperava o documento {esperada!r} da ferramenta {ferramenta}",
                )
            )
        return

    if forma != FORMA_NUCLEO:
        problemas.append(
            ProblemaDeImportacao(f"{caminho}.forma", f"esperava {FORMA_NUCLEO!r}, veio {forma!r}")
        )
        return

    nome = entrada.get("nome")
    if not isinstance(nome, str) or not nome.strip():
        problemas.append(ProblemaDeImportacao(f"{caminho}.nome", "o nome do projeto é obrigatório"))

    for campo in ("criado_em", "alterado_em"):
        try:
            datetime.fromisoformat(str(entrada.get(campo)))
        except ValueError:
            problemas.append(
                ProblemaDeImportacao(f"{caminho}.{campo}", "instante ausente ou fora do ISO 8601")
            )

    nos = entrada.get("nos")
    arestas = entrada.get("arestas")
    if not isinstance(nos, list) or not isinstance(arestas, list):
        problemas.append(ProblemaDeImportacao(f"{caminho}.nos", "esperava listas de nós e arestas"))
        return

    ids_de_no: set[str] = set()
    for posicao, bruto in enumerate(nos):
        sub = f"{caminho}.nos[{posicao}]"
        erro = _decodifica(No, bruto, sub)
        if erro:
            problemas.append(erro)
            continue
        ids_de_no.add(str(UUID(str(bruto["id"]))))

    ids_de_aresta: set[str] = set()
    for posicao, bruto in enumerate(arestas):
        sub = f"{caminho}.arestas[{posicao}]"
        erro = _decodifica(ArestaCausal, bruto, sub)
        if erro:
            problemas.append(erro)
            continue
        ids_de_aresta.add(str(UUID(str(bruto["id"]))))
        for ponta in ("origem_id", "destino_id"):
            alvo = str(UUID(str(bruto[ponta])))
            if alvo not in ids_de_no:
                problemas.append(
                    ProblemaDeImportacao(
                        f"{sub}.{ponta}",
                        f"aponta para o nó {alvo}, que não existe neste projeto",
                    )
                )

    elementos.update(ids_de_no | ids_de_aresta)

    validador = _VALIDADOR_DE_SECAO.get(str(ferramenta))
    if validador is not None:
        validador(entrada.get("secao"), f"{caminho}.secao", problemas, ids_de_no, ids_de_aresta)


def _decodifica(tipo: type, bruto: Any, caminho: str) -> ProblemaDeImportacao | None:
    """Roda o codec só para VALIDAR — o valor construído aqui é descartado de propósito."""
    try:
        decodificar(tipo, bruto, caminho=caminho)
    except ErroDeDominio as erro:
        return ProblemaDeImportacao(caminho, str(erro))
    return None


def _validar_secao(
    esperado: Mapping[str, Any],
    secao: Any,
    caminho: str,
    problemas: list[ProblemaDeImportacao],
) -> bool:
    """Confere que a seção tem exatamente os campos declarados, e nada mais (RN-06)."""
    if not isinstance(secao, Mapping):
        problemas.append(ProblemaDeImportacao(caminho, "esperava o objeto da seção da ferramenta"))
        return False
    sobrando = sorted(set(secao) - set(esperado))
    if sobrando:
        problemas.append(
            ProblemaDeImportacao(
                caminho, f"campo(s) que esta seção não tem: {', '.join(sobrando)}"
            )
        )
        return False
    conforme = True
    for campo, tipo in esperado.items():
        if campo not in secao:
            continue
        if tipo is str:
            if not isinstance(secao[campo], str):
                problemas.append(ProblemaDeImportacao(f"{caminho}.{campo}", "esperava texto"))
                conforme = False
            continue
        erro = _decodifica(tipo, secao[campo], f"{caminho}.{campo}")
        if erro:
            problemas.append(erro)
            conforme = False
    return conforme


def _exigir_referencia(
    ids: Iterable[Any],
    universo: set[str],
    caminho: str,
    problemas: list[ProblemaDeImportacao],
    o_que: str,
) -> None:
    for identificador in ids:
        alvo = str(identificador)
        if alvo not in universo:
            problemas.append(
                ProblemaDeImportacao(caminho, f"aponta para {o_que} {alvo}, que não existe aqui")
            )


_CAMPOS_DA_ARA = {
    "udes": dict[UUID, FichaDeUde],
    "status": dict[UUID, StatusDeValidacao],
    "pareceres": dict[UUID, list[ParecerDeJulgamento]],
    "exames": dict[UUID, Exame],
    "conectores": list[ConectorE],
}
_CAMPOS_DA_NC = {
    "racional": str,
    "origem": ReferenciaDeOrigem | None,
    "premissas": list[Premissa],
    "injecoes": list[Injecao],
}
_CAMPOS_DA_ARF = {
    "origem": Ponta | None,
    "udes_da_cadeia": list[UUID],
    "espelhos": dict[UUID, EspelhoDeUde],
    "ramos": list[RamoNegativo],
    "exames": dict[UUID, Exame],
    "conectores": list[ConectorE],
}
_CAMPOS_DA_APR = {
    "origem": Ponta | None,
    "pares": list[ParObstaculoOI],
    "elipses": list[ElipseDeSimultaneidade],
}
_CAMPOS_DA_AT = {"alvo": Ponta | None, "fichas": dict[UUID, FichaDePasso]}


def _validar_secao_da_ara(secao, caminho, problemas, nos, arestas) -> None:
    if not _validar_secao(_CAMPOS_DA_ARA, secao, caminho, problemas):
        return
    for campo in ("udes", "status", "pareceres"):
        _exigir_referencia(secao.get(campo, {}), nos, f"{caminho}.{campo}", problemas, "o nó")
    _exigir_referencia(secao.get("exames", {}), arestas, f"{caminho}.exames", problemas, "a aresta")
    for posicao, conector in enumerate(secao.get("conectores", [])):
        sub = f"{caminho}.conectores[{posicao}]"
        _exigir_referencia([conector["destino_id"]], nos, f"{sub}.destino_id", problemas, "o nó")
        _exigir_referencia(conector["arestas"], arestas, f"{sub}.arestas", problemas, "a aresta")


def _validar_secao_da_nc(secao, caminho, problemas, nos, arestas) -> None:
    if not _validar_secao(_CAMPOS_DA_NC, secao, caminho, problemas):
        return
    premissas = {str(p["id"]) for p in secao.get("premissas", [])}
    for posicao, injecao in enumerate(secao.get("injecoes", [])):
        _exigir_referencia(
            [injecao["premissa_id"]],
            premissas,
            f"{caminho}.injecoes[{posicao}].premissa_id",
            problemas,
            "a premissa",
        )


def _validar_secao_da_arf(secao, caminho, problemas, nos, arestas) -> None:
    if not _validar_secao(_CAMPOS_DA_ARF, secao, caminho, problemas):
        return
    _exigir_referencia(secao.get("espelhos", {}), nos, f"{caminho}.espelhos", problemas, "o nó")
    _exigir_referencia(secao.get("exames", {}), arestas, f"{caminho}.exames", problemas, "a aresta")
    for posicao, ramo in enumerate(secao.get("ramos", [])):
        _exigir_referencia(
            [ramo["raiz_id"]], nos, f"{caminho}.ramos[{posicao}].raiz_id", problemas, "o nó"
        )


def _validar_secao_da_apr(secao, caminho, problemas, nos, arestas) -> None:
    if not _validar_secao(_CAMPOS_DA_APR, secao, caminho, problemas):
        return
    for posicao, par in enumerate(secao.get("pares", [])):
        sub = f"{caminho}.pares[{posicao}]"
        _exigir_referencia([par["obstaculo_id"]], nos, f"{sub}.obstaculo_id", problemas, "o nó")
        _exigir_referencia(
            [par["objetivo_intermediario_id"]], nos, f"{sub}.objetivo_intermediario_id",
            problemas, "o nó",
        )


def _validar_secao_da_at(secao, caminho, problemas, nos, arestas) -> None:
    if not _validar_secao(_CAMPOS_DA_AT, secao, caminho, problemas):
        return
    _exigir_referencia(secao.get("fichas", {}), nos, f"{caminho}.fichas", problemas, "o nó")


_VALIDADOR_DE_SECAO: dict[str, Callable[..., None]] = {
    FERRAMENTA_ARA: _validar_secao_da_ara,
    FERRAMENTA_NC: _validar_secao_da_nc,
    FERRAMENTA_ARF: _validar_secao_da_arf,
    FERRAMENTA_APR: _validar_secao_da_apr,
    FERRAMENTA_AT: _validar_secao_da_at,
    FERRAMENTA_GENERICA: lambda secao, caminho, problemas, nos, arestas: _validar_secao(
        {}, secao if secao is not None else {}, caminho, problemas
    ),
}


def _validar_vinculo(
    bruto: Any,
    caminho: str,
    problemas: list[ProblemaDeImportacao],
    projetos: set[str],
) -> None:
    if not isinstance(bruto, Mapping):
        problemas.append(ProblemaDeImportacao(caminho, "esperava um objeto de vínculo"))
        return
    try:
        TipoDeReferencia(bruto.get("tipo"))
    except ValueError:
        problemas.append(
            ProblemaDeImportacao(f"{caminho}.tipo", f"tipo de vínculo desconhecido: {bruto.get('tipo')!r}")
        )
    for lado in ("origem", "destino"):
        ponta = bruto.get(lado)
        if not isinstance(ponta, Mapping) or not _e_uuid(ponta.get("projeto_id")):
            problemas.append(
                ProblemaDeImportacao(f"{caminho}.{lado}.projeto_id", "ponta sem projeto válido")
            )
            continue
        alvo = str(UUID(str(ponta["projeto_id"])))
        if alvo not in projetos:
            problemas.append(
                ProblemaDeImportacao(
                    f"{caminho}.{lado}.projeto_id",
                    f"aponta para o projeto {alvo}, que não veio neste arquivo",
                )
            )


# -- renomeação de identidade -----------------------------------------------------------


def _renomear(valor: Any, mapa: dict[str, str], novo_id: Callable[[], UUID]) -> Any:
    """Reescreve TODO identificador do documento. É o que garante a RN-05 por construção."""
    if isinstance(valor, Mapping):
        return {
            _renomear_texto(str(chave), mapa, novo_id): _renomear(item, mapa, novo_id)
            for chave, item in valor.items()
        }
    if isinstance(valor, list):
        return [_renomear(item, mapa, novo_id) for item in valor]
    if isinstance(valor, str):
        return _renomear_texto(valor, mapa, novo_id)
    return valor


def _renomear_texto(valor: str, mapa: dict[str, str], novo_id: Callable[[], UUID]) -> str:
    if not _e_uuid(valor):
        return valor
    canonico = str(UUID(valor))
    if canonico not in mapa:
        mapa[canonico] = str(novo_id())
    return mapa[canonico]


def _uuid(valor: Any) -> UUID:
    return UUID(str(valor))


# -- construção -------------------------------------------------------------------------


def _construir(
    entrada: Mapping[str, Any],
    *,
    dono: DonoDoProjeto,
    conhecidos: set[UUID],
    descartes: list[DescarteDeclarado],
) -> Any:
    ferramenta = str(entrada["ferramenta"])
    if ferramenta in _DELEGADOS:
        return _construir_delegado(ferramenta, entrada, dono=dono, conhecidos=conhecidos)

    projeto = Projeto(
        id=_uuid(entrada["id"]),
        dono=dono,
        nome=str(entrada["nome"]),
        ferramenta=ferramenta,
        descricao_do_problema=str(entrada.get("descricao_do_problema", "")),
        criado_em=datetime.fromisoformat(str(entrada["criado_em"])),
        alterado_em=datetime.fromisoformat(str(entrada["alterado_em"])),
        nos=tuple(decodificar(No, bruto) for bruto in entrada["nos"]),
        arestas=tuple(decodificar(ArestaCausal, bruto) for bruto in entrada["arestas"]),
    )
    projeto.eventos = ()
    secao = dict(entrada.get("secao") or {})
    montador = _MONTADOR_POR_FERRAMENTA.get(ferramenta)
    if montador is None:
        return projeto
    return montador(projeto, secao, conhecidos, descartes)


def _construir_delegado(
    ferramenta: str,
    entrada: Mapping[str, Any],
    *,
    dono: DonoDoProjeto,
    conhecidos: set[UUID],
) -> Any:
    documento = dict(entrada["secao"])
    identificador = _uuid(entrada["id"])
    if ferramenta == FERRAMENTA_SNT:
        return importar_arvore_snt(documento, id=identificador, dono=dono)
    analise, _pendentes = importar_analise(
        documento, id=identificador, dono=dono, projetos_existentes=conhecidos
    )
    return analise


def _podar(
    ponta: Mapping[str, Any] | None,
    conhecidos: set[UUID],
    descartes: list[DescarteDeclarado],
    campo: str,
) -> Mapping[str, Any] | None:
    """RN-06: ponteiro para projeto que não veio no arquivo é podado E declarado."""
    if ponta is None:
        return None
    if _uuid(ponta["projeto_id"]) in conhecidos:
        return ponta
    descartes.append(
        DescarteDeclarado(campo, "aponta para projeto que não veio neste arquivo")
    )
    return None


def _montar_ara(projeto, secao, conhecidos, descartes) -> ProjetoARA:
    ara = reidratar_ara(
        projeto,
        udes=decodificar(dict[UUID, FichaDeUde], secao.get("udes", {})),
        status=decodificar(dict[UUID, StatusDeValidacao], secao.get("status", {})),
        pareceres=decodificar(dict[UUID, list[ParecerDeJulgamento]], secao.get("pareceres", {})),
        exames=decodificar(dict[UUID, Exame], secao.get("exames", {})),
        conectores=tuple(decodificar(list[ConectorE], secao.get("conectores", []))),
    )
    ara.projeto.eventos = ()
    return ara


def _montar_nuvem(projeto, secao, conhecidos, descartes) -> NuvemDeConflito:
    origem = _podar(secao.get("origem"), conhecidos, descartes, "nc.origem")
    return reidratar_nuvem(
        projeto,
        racional=str(secao.get("racional", "")),
        premissas=decodificar(list[Premissa], secao.get("premissas", [])),
        injecoes=decodificar(list[Injecao], secao.get("injecoes", [])),
        origem=decodificar(ReferenciaDeOrigem, origem) if origem else None,
    )


def _montar_arf(projeto, secao, conhecidos, descartes) -> ProjetoARF:
    origem = _podar(secao.get("origem"), conhecidos, descartes, "arf.origem")
    return reidratar_arf(
        projeto,
        espelhos=decodificar(dict[UUID, EspelhoDeUde], secao.get("espelhos", {})),
        ramos=decodificar(list[RamoNegativo], secao.get("ramos", [])),
        exames=decodificar(dict[UUID, Exame], secao.get("exames", {})),
        conectores=decodificar(list[ConectorE], secao.get("conectores", [])),
        origem=decodificar(Ponta, origem) if origem else None,
        udes_da_cadeia=decodificar(list[UUID], secao.get("udes_da_cadeia", [])),
    )


def _montar_apr(projeto, secao, conhecidos, descartes) -> ProjetoAPR:
    origem = _podar(secao.get("origem"), conhecidos, descartes, "apr.origem")
    return reidratar_apr(
        projeto,
        pares=decodificar(list[ParObstaculoOI], secao.get("pares", [])),
        elipses=decodificar(list[ElipseDeSimultaneidade], secao.get("elipses", [])),
        origem=decodificar(Ponta, origem) if origem else None,
    )


def _montar_at(projeto, secao, conhecidos, descartes) -> ProjetoAT:
    alvo = _podar(secao.get("alvo"), conhecidos, descartes, "at.alvo")
    return reidratar_at(
        projeto,
        fichas=decodificar(dict[UUID, FichaDePasso], secao.get("fichas", {})),
        alvo=decodificar(Ponta, alvo) if alvo else None,
    )


_MONTADOR_POR_FERRAMENTA: dict[str, Callable[..., Any]] = {
    FERRAMENTA_ARA: _montar_ara,
    FERRAMENTA_NC: _montar_nuvem,
    FERRAMENTA_ARF: _montar_arf,
    FERRAMENTA_APR: _montar_apr,
    FERRAMENTA_AT: _montar_at,
}


def _construir_vinculo(bruto: Mapping[str, Any], *, dono: DonoDoProjeto) -> ReferenciaCruzada:
    vinculo = reidratar_referencia(
        id=_uuid(bruto["id"]),
        tipo=TipoDeReferencia(bruto["tipo"]),
        origem=decodificar(Ponta, bruto["origem"]),
        destino=decodificar(Ponta, bruto["destino"]),
        dono=dono,
        criada_em=datetime.fromisoformat(str(bruto["criada_em"])),
        estado=bruto.get("estado", "ativa"),
        motivo=str(bruto.get("motivo", "")),
    )
    # `reidratar_referencia` sai com `versao_lida = versao` porque reidratar é carregar o
    # que JÁ está no banco. Importar é o contrário: este vínculo nunca foi gravado, e o
    # adaptador decide INSERT ou UPDATE exatamente por este número
    # (`repositorio_projetos.py`, "Agregado que nunca foi gravado"). Deixá-lo em 1 faria a
    # primeira gravação virar um `UPDATE` de linha inexistente — o import silenciosamente
    # perdido. Os agregados de projeto já nascem com 0 porque o `Projeto` deles é novo.
    vinculo.versao_lida = 0
    return vinculo


__all__ = [
    "FORMA_DOCUMENTO",
    "FORMA_NUCLEO",
    "ORDEM_CANONICA",
    "VERSAO_DO_CONSOLIDADO",
    "DescarteDeclarado",
    "ProblemaDeImportacao",
    "RelatoDeImportacao",
    "ResultadoDaImportacao",
    "esqueleto",
    "exportar_consolidado",
    "importar_consolidado",
]
