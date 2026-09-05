"""M2 — a validação formal do Efeito Indesejável (UDE) como REGRA DE DOMÍNIO PURA.

Contexto, porque este arquivo é a razão de o ciclo 005 existir: a 4ª geração da linhagem
escreveu as onze características de um UDE bem articulado **dentro de um texto de prompt**
(`tocbuilderv3/constants.ts:123-133`), interpolado numa chamada ao provedor a partir do
navegador. Validar um UDE custava rede, o resultado variava com o modelo, e nenhum teste
jamais cobriu a regra — é o defeito D-08 da visão. Aqui a mesma regra é função pura:
sem rede, sem modelo, sem estado.

Sete das onze características viram oito checagens decidíveis (a característica 2 vira
duas: frase completa e tempo presente); as outras quatro (1, 4, 5 e 7) dependem de
julgamento sobre o sistema analisado e são declaradas como julgamento — nunca como regra
que aprova ou reprova (spec 005, RF-08, RF-09 e RN-07..RN-09).

A paridade com `docs/produto/dados/medir-base.py`, que fez a tradução original, é medida
em `test_paridade_com_medir_base.py`.
"""
import pytest

from toc_api.dominio.criterios_ude import (
    CRITERIOS,
    CRITERIOS_DECIDIVEIS,
    CRITERIOS_DE_JULGAMENTO,
    ClasseDeCriterio,
    Veredito,
    validar_formalmente,
)


def codigos_reprovados(texto: str) -> set[str]:
    return {
        v.criterio.codigo
        for v in validar_formalmente(texto).vereditos
        if v.veredito is Veredito.NAO_ATENDE
    }


# -- o catálogo das onze características ------------------------------------------------


def test_as_onze_caracteristicas_da_linhagem_estao_declaradas_com_sua_classe():
    """RF-09: a classificação decidível × julgamento é DADO do domínio, não prompt."""
    caracteristicas = {c.caracteristica for c in CRITERIOS}
    assert caracteristicas == {str(n) for n in range(1, 12)}
    assert len(CRITERIOS_DECIDIVEIS) == 8
    assert len(CRITERIOS_DE_JULGAMENTO) == 4
    assert {c.caracteristica for c in CRITERIOS_DE_JULGAMENTO} == {"1", "4", "5", "7"}
    assert all(c.regra.startswith("RN-") for c in CRITERIOS)


def test_criterio_de_julgamento_nunca_reprova_sozinho():
    """RF-08 e RN-10: julgamento é pendência de parecer, não reprovação da máquina."""
    validacao = validar_formalmente("A taxa de conclusão dos cursos técnicos é de 54%.")
    julgamentos = [
        v for v in validacao.vereditos
        if v.criterio.classe is ClasseDeCriterio.JULGAMENTO
    ]
    assert len(julgamentos) == 4
    assert all(v.veredito is Veredito.INDETERMINADO for v in julgamentos)
    assert validacao.aprovado_nos_decidiveis is True
    assert len(validacao.pendencias_de_julgamento) == 4


# -- os casos canônicos da linhagem (RF-12, DoD 2) ---------------------------------------


@pytest.mark.parametrize(
    "texto, esperado, codigo",
    [
        # `tocbuilderv3/constants.ts:162` — 'Exemplo Ruim: "Falta de treinamento causa
        # erros." (UDE + Causa) -> Bom UDE: "A taxa de erros no processo X é de 15%."'
        ("Falta de treinamento causa erros.", False, "CD-7"),
        ("A taxa de erros no processo X é de 15%.", True, None),
        # `constants.ts:163` — 'Exemplo Ruim: "Precisamos de um novo software para
        # gerenciar tarefas." (Solução) -> Bom UDE: "Tarefas frequentemente ultrapassam
        # o prazo."'
        ("Precisamos de um novo software para gerenciar tarefas.", False, "CD-5"),
        ("Tarefas frequentemente ultrapassam o prazo.", True, None),
    ],
)
def test_canonicos_da_linhagem(texto, esperado, codigo):
    validacao = validar_formalmente(texto)
    assert validacao.aprovado_nos_decidiveis is esperado, validacao.motivos
    if codigo:
        assert codigo in codigos_reprovados(texto)


def test_falso_negativo_do_conjunto_de_controle_k03_esta_fechado():
    """O TESTE VERMELHO do lote — `docs/produto/visao.md` §6, defeito D-12.

    O conjunto de controle (nove enunciados colhidos da linhagem, rotulados PELA FONTE)
    encontrou exatamente um falso negativo: a fonte rotula
    "Falta de treinamento causa erros." (`tocbuilderv3/constants.ts:162`) como
    **Exemplo Ruim** porque o enunciado traz a própria causa (característica 10), e a
    checagem CD-7 de `medir-base.py` APROVAVA — porque procura conectivos ("porque",
    "devido a", "já que") e não o **verbo causal** ("causa", "leva a", "resulta em").

    A visão declara o destino em letras: "tem de fechar o falso negativo K-03 — que hoje
    falha e é o caso de teste que nasce vermelho (P4)". É este.
    """
    validacao = validar_formalmente("Falta de treinamento causa erros.")
    assert validacao.aprovado_nos_decidiveis is False
    reprovacao = validacao.veredito_de("CD-7")
    assert reprovacao.veredito is Veredito.NAO_ATENDE
    assert reprovacao.trecho == "causa"


@pytest.mark.parametrize(
    "texto",
    [
        "Falta de treinamento causa erros.",
        "O acúmulo de pendências leva a atrasos na secretaria.",
        "A conferência manual resulta em retrabalho na matrícula.",
        "O sistema desatualizado provoca lançamentos duplicados.",
        "A ausência de conferência acarreta divergência de matrícula.",
    ],
)
def test_verbo_causal_reprova_a_cd7_como_o_conectivo_reprova(texto):
    """A regra passa a cobrir a FAMÍLIA do defeito, não só o caso que o denunciou."""
    assert "CD-7" in codigos_reprovados(texto)


def test_causa_como_substantivo_nao_dispara_a_cd7():
    """Sem isto, fechar o falso negativo abriria um falso positivo.

    "A causa" é sujeito, não verbo. Um marcador cego trocaria um defeito por outro, e o
    conjunto de controle não teria como perceber — ele só tem nove enunciados.
    """
    assert "CD-7" not in codigos_reprovados(
        "A causa do atraso permanece desconhecida na secretaria."
    )


# -- as oito checagens decidíveis, uma a uma ---------------------------------------------


@pytest.mark.parametrize(
    "codigo, texto",
    [
        ("CD-1", "Alta evasão"),
        ("CD-2", "A evasão aumentará no próximo semestre."),
        ("CD-3", "Reduzir o tempo de resposta às solicitações dos alunos."),
        ("CD-4", "A equipe da secretaria é desleixada com os prazos."),
        ("CD-5", "Falta um sistema integrado de matrícula na secretaria."),
        ("CD-6", "Os professores chegam atrasados e as salas não têm projetor."),
        ("CD-7", "Os alunos abandonam o curso porque a coordenação não responde."),
        ("CD-8", "O atendimento ao aluno é péssimo."),
    ],
)
def test_cada_checagem_decidivel_reprova_a_sua_patologia(codigo, texto):
    assert codigo in codigos_reprovados(texto)


def test_veredito_aponta_o_trecho_que_o_motivou():
    """RI-03: a reprovação aponta o trecho no próprio texto, não uma frase genérica."""
    validacao = validar_formalmente("O atendimento ao aluno é péssimo.")
    veredito = validacao.veredito_de("CD-8")
    assert veredito.trecho and veredito.trecho.lower() in "o atendimento ao aluno é péssimo."


def test_validacao_e_deterministica():
    """RNF-01: mesmo texto, mesmo resultado — sem rede, sem modelo, sem estado."""
    texto = "Os alunos abandonam o curso porque a coordenação não responde."
    primeira = validar_formalmente(texto)
    segunda = validar_formalmente(texto)
    assert primeira == segunda


def test_texto_vazio_nao_e_um_ude_aprovado():
    assert validar_formalmente("   ").aprovado_nos_decidiveis is False
