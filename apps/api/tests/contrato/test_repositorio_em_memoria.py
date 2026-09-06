"""O adaptador em memória tem de se comportar como o de banco — senão é um duplo que mente.

Ele é backend de verdade (é o que roda quando `DATABASE_URL` não existe), e é por isso que
merece teste próprio: um adaptador em memória mais permissivo que o SQL deixa a suíte verde
sobre um isolamento que não existe. Os mesmos comportamentos são medidos contra o
PostgreSQL real em `tests/integracao/test_grafo_e_ara_no_postgres.py`.
"""
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from toc_api.dominio.ara import EstadoDoExame, FichaDeUde, novo_projeto_ara
from toc_api.dominio.erros import MutacaoForaDaRaiz
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.projeto import Projeto
from toc_api.infra.persistencia.memoria import RepositorioDeProjetosEmMemoria

HORIZONTE = DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-facilitadora")
ALVORADA = DonoDoProjeto(inquilino_id="inq-alvorada", usuario_id="usr-consultor")
T0 = datetime(2026, 9, 5, 12, 0, tzinfo=timezone.utc)
BOM = "A taxa de conclusão dos cursos técnicos é de 54%."


def projeto_de(dono: DonoDoProjeto, nome: str = "Horizonte") -> Projeto:
    return Projeto(id=uuid4(), dono=dono, nome=nome, criado_em=T0, alterado_em=T0)


def test_a_leitura_cruzada_de_inquilino_volta_vazia():
    repositorio = RepositorioDeProjetosEmMemoria()
    projeto = projeto_de(HORIZONTE)
    repositorio.salvar(projeto)
    assert repositorio.obter(ALVORADA.inquilino_id, projeto.id) is None
    assert repositorio.listar(ALVORADA.inquilino_id) == []
    assert [p.id for p in repositorio.listar(HORIZONTE.inquilino_id)] == [projeto.id]


def test_mutar_o_agregado_devolvido_nao_muta_o_que_esta_guardado():
    """A cópia na fronteira: sem ela, um teste de exclusão reversível passa por acidente."""
    repositorio = RepositorioDeProjetosEmMemoria()
    projeto = projeto_de(HORIZONTE)
    repositorio.salvar(projeto)
    devolvido = repositorio.obter(HORIZONTE.inquilino_id, projeto.id)
    devolvido.renomear("nome trocado por fora", em=T0)
    assert repositorio.obter(HORIZONTE.inquilino_id, projeto.id).nome == "Horizonte"


def test_a_listagem_esconde_o_excluido_e_o_obter_continua_achando():
    repositorio = RepositorioDeProjetosEmMemoria()
    projeto = projeto_de(HORIZONTE)
    projeto.excluir(em=T0)
    repositorio.salvar(projeto)
    assert repositorio.listar(HORIZONTE.inquilino_id) == []
    assert len(repositorio.listar(HORIZONTE.inquilino_id, incluir_excluidos=True)) == 1
    assert repositorio.obter(HORIZONTE.inquilino_id, projeto.id) is not None


def test_a_listagem_filtra_por_usuario_e_ordena_pela_ultima_alteracao():
    repositorio = RepositorioDeProjetosEmMemoria()
    antigo = projeto_de(HORIZONTE, "antigo")
    novo = projeto_de(HORIZONTE, "novo")
    novo.renomear("novo", em=datetime(2026, 9, 6, 12, 0, tzinfo=timezone.utc))
    outro_usuario = projeto_de(
        DonoDoProjeto(inquilino_id="inq-horizonte", usuario_id="usr-participante"),
        "de outra pessoa",
    )
    for p in (antigo, novo, outro_usuario):
        repositorio.salvar(p)

    assert [p.nome for p in repositorio.listar("inq-horizonte")][0] == "novo"
    somente_dela = repositorio.listar("inq-horizonte", usuario_id="usr-facilitadora")
    assert {p.nome for p in somente_dela} == {"antigo", "novo"}


def test_a_ara_vai_e_volta_com_ficha_status_e_exame():
    repositorio = RepositorioDeProjetosEmMemoria()
    ara = novo_projeto_ara(id=uuid4(), dono=HORIZONTE, nome="Horizonte — ARA", em=T0)
    causa = ara.adicionar_efeito(titulo="Os formulários chegam incompletos.", em=T0)
    efeito = ara.adicionar_efeito(titulo=BOM, em=T0)
    elo = ara.ligar(causa.id, efeito.id, em=T0)
    ara.marcar_ude(efeito.id, ficha=FichaDeUde(area_impactada="Secretaria"), em=T0)
    ara.examinar_elo(elo.id, EstadoDoExame.SUFICIENTE, em=T0)
    repositorio.salvar_ara(ara)

    reaberta = repositorio.obter_ara(HORIZONTE.inquilino_id, ara.projeto.id)
    assert reaberta.ficha(efeito.id).area_impactada == "Secretaria"
    assert reaberta.exame(elo.id).estado is EstadoDoExame.SUFICIENTE
    assert reaberta.validacao(efeito.id).aprovado_nos_decidiveis is True
    assert repositorio.obter_ara(ALVORADA.inquilino_id, ara.projeto.id) is None


def test_gravar_pela_raiz_e_ler_pelo_m1_devolve_o_mesmo_agregado():
    """As duas portas de LEITURA veem o mesmo estado — e só uma delas escreve o grafo.

    Este teste media, antes, o contrário: gravava um nó pelo `Projeto` cru devolvido por
    `obter()` e conferia que a ARA o via. A propriedade "as duas visões apontam para o
    mesmo agregado" continua e é o que se afirma aqui; o que mudou é que a ESCRITA do
    grafo entra pela raiz `ProjetoARA`, e o `Projeto` cru recusa — que é a correção da
    porta dos fundos.
    """
    repositorio = RepositorioDeProjetosEmMemoria()
    ara = novo_projeto_ara(id=uuid4(), dono=HORIZONTE, nome="Horizonte — ARA", em=T0)
    ara.adicionar_efeito(titulo=BOM, em=T0)
    repositorio.salvar_ara(ara)

    guardado = repositorio.obter(HORIZONTE.inquilino_id, ara.projeto.id)

    assert [n.titulo for n in guardado.nos] == [BOM]
    assert [n.tipo for n in guardado.nos] == ["efeito"]


def test_o_projeto_cru_de_uma_ara_recusa_mutacao_de_grafo():
    """A porta dos fundos do agregado, medida no adaptador que a servia.

    `obter()` continua devolvendo o `Projeto` — leitura, lixeira e restauração dependem
    dele. O que ele não faz mais é aceitar mutação de grafo: quem quiser mexer nos nós de
    uma Árvore da Realidade Atual passa por `obter_ara()`.
    """
    repositorio = RepositorioDeProjetosEmMemoria()
    ara = novo_projeto_ara(id=uuid4(), dono=HORIZONTE, nome="Horizonte — ARA", em=T0)
    repositorio.salvar_ara(ara)

    guardado = repositorio.obter(HORIZONTE.inquilino_id, ara.projeto.id)

    with pytest.raises(MutacaoForaDaRaiz) as recusa:
        guardado.adicionar_no(titulo=BOM, em=T0)
    assert (recusa.value.ferramenta, recusa.value.raiz) == ("ara", "ProjetoARA")
    assert repositorio.obter_ara(HORIZONTE.inquilino_id, ara.projeto.id).nos == ()
