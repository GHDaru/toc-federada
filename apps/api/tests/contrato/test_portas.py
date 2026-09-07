"""As portas são contrato: quem as implementa satisfaz a MESMA forma, fake ou adaptador.

Por que este teste existe: um duplo que diverge da porta faz a suíte de aplicação ficar
verde enquanto o adaptador real quebra em produção. Aqui os dois lados são medidos contra
a mesma `typing.Protocol`.
"""
from toc_api.dominio import portas
from toc_api.infra.observabilidade.otel import RastreadorNulo
from toc_api.infra.persistencia.memoria import RepositorioDeProjetosEmMemoria
from toc_api.infra.persistencia.repositorio_projetos import RepositorioDeProjetosSQL
from toc_api.infra.relogio import RelogioDoSistema

from tests.aplicacao.fakes import (
    RastreadorFalso,
    RelogioFalso,
    RepositorioDeARAFalso,
    RepositorioDeProjetosFalso,
)


def test_toda_porta_e_um_protocolo_verificavel_em_execucao():
    for porta in (
        portas.Relogio,
        portas.Rastreador,
        portas.RepositorioDeProjetos,
        portas.RepositorioDeARA,
        # M6 — Focalização (spec 009): a porta da jornada e a composta que a validação de
        # vínculo exige entram aqui no commit em que nascem.
        portas.RepositorioDeFocalizacao,
        portas.RepositorioDaJornada,
    ):
        assert getattr(porta, "_is_runtime_protocol", False), (
            f"{porta.__name__} precisa de @runtime_checkable para o contrato ser medível"
        )


def test_os_duplos_dos_testes_satisfazem_as_portas():
    assert isinstance(RastreadorFalso(), portas.Rastreador)
    assert isinstance(RepositorioDeProjetosFalso(), portas.RepositorioDeProjetos)
    assert isinstance(RepositorioDeARAFalso(), portas.RepositorioDeARA)
    assert isinstance(RelogioFalso.__new__(RelogioFalso), portas.Relogio)
    from tests.aplicacao.fakes_m6 import RepositorioDaJornadaFalso

    assert isinstance(RepositorioDaJornadaFalso(), portas.RepositorioDeFocalizacao)
    assert isinstance(RepositorioDaJornadaFalso(), portas.RepositorioDaJornada)


def test_os_adaptadores_de_infra_satisfazem_as_mesmas_portas():
    assert isinstance(RastreadorNulo(), portas.Rastreador)
    assert isinstance(RepositorioDeProjetosEmMemoria(), portas.RepositorioDeProjetos)
    assert isinstance(RelogioDoSistema(), portas.Relogio)
    # O adaptador SQL exige uma fábrica de sessão; a conformidade é medida na classe.
    assert isinstance(RepositorioDeProjetosEmMemoria(), portas.RepositorioDeARA)
    # O adaptador SQL exige uma fábrica de sessão; a conformidade é medida na classe.
    assert isinstance(RepositorioDeProjetosEmMemoria(), portas.RepositorioDaJornada)
    for porta in (
        portas.RepositorioDeProjetos,
        portas.RepositorioDeARA,
        portas.RepositorioDeFocalizacao,
        portas.RepositorioDaJornada,
    ):
        assert isinstance(
            RepositorioDeProjetosSQL.__new__(RepositorioDeProjetosSQL), porta
        ), f"o adaptador SQL não satisfaz {porta.__name__}"


# --------------------------------------------------------------------------------------
# Nome de esquema é CONTRATO: dois iguais no mesmo módulo é um defeito silencioso
#
# `esquemas.py` é um módulo só, e em Python a segunda definição de uma classe **apaga a
# primeira**. Quando isso acontece entre dois modelos de resposta, o código que instancia
# o primeiro passa a instanciar o segundo — e o erro não aparece na importação nem no
# `mypy`: aparece em produção, como `ValidationError` de campo que "não existe", na
# primeira vez que aquela rota devolve dado.
#
# Foi exatamente o que aconteceu: `PendenciaOut` foi definida para a pendência de um passo
# da jornada de focalização (M6 — passo, regra, detalhe) e **de novo** para a pendência do
# plano de Estratégia & Táticas (M5 — no_id, numero, tipo). A segunda venceu, e as cinco
# provas de traço do M6 caíram com "6 validation errors for PendenciaOut".
#
# Este teste é a função de aptidão da regra. Ele não julga nomes bonitos: julga colisão.
def test_nenhum_esquema_http_tem_nome_repetido():
    import ast
    import collections
    import pathlib

    caminho = pathlib.Path(__file__).resolve().parents[2] / "src/toc_api/http/esquemas.py"
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    nomes = [n.name for n in arvore.body if isinstance(n, ast.ClassDef)]
    repetidos = {n: q for n, q in collections.Counter(nomes).items() if q > 1}

    print(f"classes de esquema examinadas: {len(nomes)} · repetidas: {repetidos}")
    assert repetidos == {}, (
        "duas classes com o mesmo nome no mesmo módulo: a segunda apaga a primeira e o "
        f"defeito só aparece em tempo de resposta — {repetidos}"
    )


# O mesmo defeito, um andar acima: em `erros.py` o que colide não é a classe, é o NOME
# IMPORTADO. `from ..dominio.ara import TransicaoDeStatusRecusada` seguido de
# `from ..dominio.snt import TransicaoDeStatusRecusada` deixa o segundo no lugar do
# primeiro — e `@app.exception_handler(TransicaoDeStatusRecusada)` passa a registrar DUAS
# VEZES a mesma classe, deixando a outra sem tradutor. O efeito no cliente é silencioso e
# caro: a recusa da Árvore da Realidade Atual, que devia dizer
# `details.motivo = "reabertura_sem_justificativa"`, chegava como `MUTATION_REFUSED` seco.
def test_nenhum_nome_importado_em_erros_py_e_ligado_duas_vezes():
    import ast
    import collections
    import pathlib

    caminho = pathlib.Path(__file__).resolve().parents[2] / "src/toc_api/http/erros.py"
    arvore = ast.parse(caminho.read_text(encoding="utf-8"))
    ligados = [
        alias.asname or alias.name
        for no in ast.walk(arvore)
        if isinstance(no, (ast.Import, ast.ImportFrom))
        for alias in no.names
    ]
    repetidos = {n: q for n, q in collections.Counter(ligados).items() if q > 1}

    print(f"nomes importados em erros.py: {len(ligados)} · ligados duas vezes: {repetidos}")
    assert repetidos == {}, (
        "um nome importado duas vezes esconde uma classe de exceção inteira do registro "
        f"de tradutores — dê apelido (`as`) ao segundo: {repetidos}"
    )
