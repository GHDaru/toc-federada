"""O teste do domínio é a exceção declarada: ele exercita a chave de propósito."""
from toc_api.dominio.projeto import Projeto


def test_a_chave_da_raiz_destrava_o_nucleo():
    projeto = Projeto()
    with projeto.sob_a_raiz() as nucleo:
        nucleo.adicionar_no()
