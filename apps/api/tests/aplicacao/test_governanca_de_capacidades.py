"""A política de capacidades — e **o teste que conta os pontos de verificação**.

O Anexo B do Padrão APH (Aplicação ↔ Harness), §B.7.2, registra uma armadilha nominal:

> auditar autorização olhando `Depends(...)`/middleware na camada de rota, num código que
> segue o APH-7.2, produz **falso positivo sistemático**. Três equipes independentes
> caíram nela na primeira rodada de federação, inclusive sobre o próprio código.

Um teste que abrisse o HyperText Transfer Protocol (HTTP) e conferisse um `403` por rota
teria a mesma cegueira ao contrário: ficaria verde sobre as rotas que existem hoje e não
diria nada sobre o fio conversacional, sobre o catálogo de ações ou sobre qualquer chamador
que apareça depois. Por isso a contagem aqui é feita de três formas independentes:

1. **por caso de uso** — para CADA caso de uso concreto da camada de aplicação, um
   principal sem a capacidade exigida é recusado. O denominador é descoberto por
   introspecção do pacote, nunca digitado: um caso de uso novo entra na conta sozinho;
2. **por cobertura da política** — nenhum caso de uso concreto fica de fora da política, e
   a política não registra classe que não existe;
3. **por localização** — a chamada que decide acesso acontece em UM lugar da camada de
   aplicação e em ZERO lugares da camada HTTP, contado por árvore sintática (Abstract
   Syntax Tree, AST) e não por leitura.

Regra R2 do `CLAUDE.md` (portão verde declara quanto examinou): cada teste imprime o
tamanho do que examinou, e os números aparecem na saída do `pytest -s`.
"""
from __future__ import annotations

import ast
import importlib
import inspect
import pkgutil
from pathlib import Path

import pytest

import toc_api
import toc_api.aplicacao
from toc_api.aplicacao.casos_de_uso import CasoDeUso
from toc_api.aplicacao.governanca import (
    POLITICA,
    TOC_ESCRITA,
    TOC_LEITURA,
    AutorizacaoNegada,
    Executor,
    PoliticaAusente,
    capacidade_de,
    exigir_capacidade,
)
from toc_api.aplicacao.politica import PoliticaPorCapability, PoliticaSempreVerdadeira
from toc_api.dominio.federacao.principal import Principal, principal_de_introspeccao

from .fakes import RastreadorFalso, RelogioFalso, RepositorioDeARAFalso

def principal_com(capabilities: list[str]) -> Principal:
    """Sempre pelo construtor de verdade: identidade só nasce de introspecção (RF-07)."""
    return principal_de_introspeccao(
        {
            "active": True,
            "user": {"id": "usr-facilitadora", "name": "Facilitadora TOC"},
            "tenant_id": "inq-horizonte",
            "capabilities": capabilities,
        }
    )


SEM_NADA = principal_com([])
SO_LE = principal_com([TOC_LEITURA])
SO_ESCREVE = principal_com([TOC_ESCRITA])
PLENA = principal_com([TOC_LEITURA, TOC_ESCRITA])

#: Os cinco casos de uso que só leem. Escrito à mão de propósito: se um caso de uso
#: MUTADOR for registrado como leitura por descuido, a lista aqui não muda e o teste cai.
SO_LEITURA = {
    "abrir_projeto",
    "abrir_projeto_ara",
    "abrir_projeto_nc",
    "listar_lixeira",
    "listar_projetos",
    "validar_nuvem",
    "validar_texto_de_ude",
}


#: Os módulos cujo governo é desta tabela: o núcleo M1 (projeto, nó, aresta), o M2
#: (ARA) e o M3 (Nuvem de Conflito, spec 007). A superfície federada tem os seus próprios casos de uso e a sua própria
#: verificação, no lote da federação — declarar o escopo é o que impede este teste de
#: ficar vermelho por trabalho alheio e, ao mesmo tempo, o que impede que ele finja
#: cobrir o que não cobre.
MODULOS_DO_NUCLEO = (
    "toc_api.aplicacao.projetos",
    "toc_api.aplicacao.grafo",
    "toc_api.aplicacao.ara",
    "toc_api.aplicacao.nuvem",
)


def casos_de_uso_concretos() -> list[type[CasoDeUso]]:
    """Descobre por introspecção, nunca por lista digitada.

    Concreto = subclasse de `CasoDeUso` definida num dos `MODULOS_DO_NUCLEO` e cujo nome
    não começa com `_`. Os intermediários (`_ComRepositorio`, `_SobreProjeto`,
    `_SobreARA`, …) são andaimes de composição e não são chamáveis por ninguém de fora.
    """
    achados: dict[str, type[CasoDeUso]] = {}
    pacote = toc_api.aplicacao
    for modulo in pkgutil.iter_modules(pacote.__path__):
        importlib.import_module(f"{pacote.__name__}.{modulo.name}")
    pilha = [CasoDeUso]
    while pilha:
        classe = pilha.pop()
        for filha in classe.__subclasses__():
            pilha.append(filha)
            if (
                not filha.__name__.startswith("_")
                and filha.__module__ in MODULOS_DO_NUCLEO
            ):
                achados[filha.__name__] = filha
    return sorted(achados.values(), key=lambda c: c.__name__)


def pecas():
    return dict(
        rastreador=RastreadorFalso(),
        repositorio=RepositorioDeARAFalso(),
        relogio=RelogioFalso(instante=__import__("datetime").datetime.now()),
    )


# -- 1. contagem por caso de uso ----------------------------------------------------


def test_todo_caso_de_uso_recusa_o_principal_que_nao_tem_a_capacidade():
    """N casos de uso descobertos → N recusas. O denominador vai para a saída (R2)."""
    classes = casos_de_uso_concretos()
    executor = Executor(principal=SEM_NADA, **pecas())

    recusados = []
    for classe in classes:
        with pytest.raises(AutorizacaoNegada):
            executor.rodar(classe)
        recusados.append(classe.nome)

    print(
        f"\npontos de verificação exercidos: {len(recusados)} de "
        f"{len(classes)} casos de uso concretos → {sorted(recusados)}"
    )
    assert len(recusados) == len(classes)
    assert len(classes) >= 27, "a camada de aplicação encolheu — reveja a descoberta"


def test_a_recusa_acontece_ANTES_de_executar_qualquer_coisa():
    """Sem argumento nenhum, o que aparece é `AutorizacaoNegada` e não `TypeError`.

    É a prova de que a verificação precede a execução: se ela viesse depois, faltaria
    argumento obrigatório e o erro seria outro.
    """
    executor = Executor(principal=SEM_NADA, **pecas())
    from toc_api.aplicacao.projetos import CriarProjeto

    with pytest.raises(AutorizacaoNegada):
        executor.rodar(CriarProjeto)


def test_quem_so_le_e_recusado_em_toda_mutacao_e_aceito_em_toda_leitura():
    classes = casos_de_uso_concretos()
    politica = PoliticaPorCapability()
    negadas, permitidas = [], []
    for classe in classes:
        try:
            exigir_capacidade(politica, SO_LE, classe)
            permitidas.append(classe.nome)
        except AutorizacaoNegada:
            negadas.append(classe.nome)
    print(f"\nleitura pura: {len(permitidas)} permitidas, {len(negadas)} negadas")
    assert set(permitidas) == SO_LEITURA
    assert set(negadas) == {c.nome for c in classes} - SO_LEITURA


def test_quem_escreve_nao_ganha_leitura_de_graca():
    """`toc:write` não implica `toc:read`: as capacidades não têm hierarquia (§B.7.1)."""
    from toc_api.aplicacao.projetos import AbrirProjeto

    with pytest.raises(AutorizacaoNegada):
        exigir_capacidade(PoliticaPorCapability(), SO_ESCREVE, AbrirProjeto)


# -- 2. cobertura da política -------------------------------------------------------


def test_todo_caso_de_uso_concreto_esta_na_politica():
    classes = casos_de_uso_concretos()
    faltando = [c.__name__ for c in classes if c not in POLITICA]
    print(f"\ncasos de uso examinados: {len(classes)}; sem política: {len(faltando)}")
    assert faltando == []


def test_a_politica_nao_registra_classe_que_nao_e_caso_de_uso_concreto():
    conhecidos = set(casos_de_uso_concretos())
    sobrando = [c.__name__ for c in POLITICA if c not in conhecidos]
    assert sobrando == []


def test_a_politica_so_usa_capacidades_da_forma_recurso_verbo():
    assert set(POLITICA.values()) == {"toc:read", "toc:write"}


def test_caso_de_uso_fora_da_politica_e_negado_e_nao_liberado():
    """Fail-closed de verdade: a ausência de regra NEGA, nunca permite (RNF-04)."""

    class CasoDeUsoNaoRegistrado(CasoDeUso):
        nome = "caso_de_uso_nao_registrado"

        def executar(self, **kwargs):  # pragma: no cover - nunca deve ser alcançado
            raise AssertionError("executou um caso de uso sem política")

    with pytest.raises(PoliticaAusente):
        exigir_capacidade(PoliticaPorCapability(), PLENA, CasoDeUsoNaoRegistrado)
    with pytest.raises(PoliticaAusente):
        capacidade_de(CasoDeUsoNaoRegistrado)
    with pytest.raises(PoliticaAusente):
        Executor(principal=PLENA, **pecas()).rodar(CasoDeUsoNaoRegistrado)


# -- 3. localização da decisão (AST) ------------------------------------------------

RAIZ = Path(toc_api.__file__).resolve().parent
#: As funções que decidem acesso, na corrente inteira: `exigir_capacidade` (governança)
#: → `PoliticaDeAutorizacao.permite` (política) → `Principal.pode` (o predicado).
NOMES_QUE_DECIDEM = {"exigir_capacidade", "permite", "pode"}

#: Os módulos do núcleo M1/M2 que **delegam** a decisão ao `Executor` e por isso não
#: podem ter nenhuma chamada dessas. Se um caso de uso passar a decidir por conta
#: própria, aparece um segundo lugar para esquecer de decidir — e o teste cai.
MODULOS_QUE_NAO_DECIDEM = (
    "aplicacao/projetos.py",
    "aplicacao/grafo.py",
    "aplicacao/ara.py",
    "aplicacao/casos_de_uso.py",
)


def chamadas_que_decidem(pasta: Path) -> dict[str, dict[str, int]]:
    """Conta, por arquivo e por função, as CHAMADAS que decidem acesso.

    Conta chamada e não import: a camada HTTP legitimamente **importa**
    `AutorizacaoNegada` para traduzi-la em `403`. Traduzir uma recusa não é decidi-la.

    Conta por função, e não um total por arquivo, porque a decisão é uma corrente de três
    elos por desenho, e um total agregado não distinguiria "a corrente tem três elos" de
    "há três lugares decidindo". A primeira é a arquitetura; a segunda é o defeito.
    """
    contagem: dict[str, dict[str, int]] = {}
    for arquivo in sorted(pasta.rglob("*.py")):
        arvore = ast.parse(arquivo.read_text(encoding="utf-8"), filename=str(arquivo))
        por_nome: dict[str, int] = {}
        for no in ast.walk(arvore):
            if not isinstance(no, ast.Call):
                continue
            alvo = no.func
            nome = alvo.attr if isinstance(alvo, ast.Attribute) else getattr(alvo, "id", "")
            if nome in NOMES_QUE_DECIDEM:
                por_nome[nome] = por_nome.get(nome, 0) + 1
        if por_nome:
            contagem[str(arquivo.relative_to(RAIZ))] = por_nome
    return contagem


def test_a_decisao_do_nucleo_acontece_num_ponto_so_e_os_casos_de_uso_nao_decidem():
    arquivos = sorted((RAIZ / "aplicacao").rglob("*.py"))
    contagem = chamadas_que_decidem(RAIZ / "aplicacao")
    print(
        f"\narquivos de aplicacao examinados: {len(arquivos)}; "
        f"chamadas que decidem acesso, por arquivo: {contagem}"
    )
    # Um elo de cada na governança, e nenhum a mais: `exigir_capacidade` é chamada só
    # pelo `Executor`, e `permite` só por `exigir_capacidade`.
    assert contagem.get("aplicacao/governanca.py") == {
        "exigir_capacidade": 1,
        "permite": 1,
    }
    for modulo in MODULOS_QUE_NAO_DECIDEM:
        assert modulo not in contagem, (
            f"{modulo} passou a decidir acesso por conta própria; a decisão do núcleo "
            f"M1/M2 é do `Executor`, e um segundo ponto é um segundo lugar para esquecer"
        )


def test_a_camada_http_nao_decide_acesso_em_lugar_nenhum():
    pasta = RAIZ / "http"
    arquivos = sorted(pasta.rglob("*.py"))
    contagem = chamadas_que_decidem(pasta)
    print(
        f"\narquivos de http examinados: {len(arquivos)}; "
        f"chamadas que decidem acesso: {contagem or 'nenhuma'}"
    )
    assert arquivos, "não há camada HTTP para examinar — o portão responderia verde sobre nada"
    assert contagem == {}, (
        "a camada de rota voltou a decidir acesso — é exatamente o falso positivo "
        "sistemático que o §B.7.2 do Anexo B nomeia"
    )


def test_a_sabotagem_da_politica_derruba_as_recusas_deste_nucleo_tambem():
    """RF-20 da spec 006: trocar a política por uma que aprova tudo TEM de quebrar.

    A `PoliticaSempreVerdadeira` é a não-conformidade declarada de `aplicacao/politica.py`.
    Se as recusas deste arquivo continuassem acontecendo com ela injetada, é porque não
    estariam olhando para a política — passariam por acaso.
    """
    honesta = Executor(principal=SEM_NADA, **pecas())
    with pytest.raises(AutorizacaoNegada):
        honesta.rodar(CriarProjeto := __import__(
            "toc_api.aplicacao.projetos", fromlist=["CriarProjeto"]
        ).CriarProjeto)

    sabotada = Executor(
        principal=SEM_NADA, politica=PoliticaSempreVerdadeira(), **pecas()
    )
    projeto = sabotada.rodar(CriarProjeto, nome="A sabotagem passa")
    assert projeto is not None, (
        "com a política sabotada a recusa deveria sumir; se não sumiu, a recusa não vem "
        "da política e o teste de recusa não prova o que diz provar"
    )

    # E a política ausente continua negando MESMO com a sabotagem: fail-closed não é
    # decisão da política, é ausência de regra.
    class SemPolitica(CasoDeUso):
        nome = "sem_politica"

        def executar(self, **kwargs):  # pragma: no cover - inalcançável
            raise AssertionError("executou sem política")

    with pytest.raises(PoliticaAusente):
        sabotada.rodar(SemPolitica)


def test_a_politica_e_pura_nao_importa_framework_nem_banco():
    fonte = (RAIZ / "aplicacao" / "governanca.py").read_text(encoding="utf-8")
    arvore = ast.parse(fonte)
    importados = set()
    for no in ast.walk(arvore):
        if isinstance(no, ast.Import):
            importados.update(a.name.split(".")[0] for a in no.names)
        elif isinstance(no, ast.ImportFrom) and no.module and no.level == 0:
            importados.add(no.module.split(".")[0])
    proibidos = {"fastapi", "starlette", "pydantic", "sqlalchemy", "httpx", "opentelemetry"}
    assert importados & proibidos == set()


def test_o_executor_entrega_a_identidade_da_introspeccao_e_nao_a_do_pedido():
    """O chamador nunca escolhe o dono: quem o define é o principal (P2, RNF-03)."""
    from toc_api.aplicacao.projetos import CriarProjeto

    executor = Executor(principal=SO_ESCREVE, **pecas())
    projeto = executor.rodar(CriarProjeto, nome="Horizonte — diagrama")
    assert projeto.dono == SO_ESCREVE.dono()

    assinatura = inspect.signature(Executor.rodar)
    assert "dono" not in assinatura.parameters
