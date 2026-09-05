"""Erros de domínio — tipados, para a borda traduzir sem adivinhar.

Nenhum deles carrega texto de interface: o domínio diz O QUE foi recusado; quem traduz
para HTTP, para mensagem de tela ou para envelope APH é a borda.
"""
from __future__ import annotations


class ErroDeDominio(Exception):
    """Raiz de tudo que o domínio recusa."""


class DadoInvalido(ErroDeDominio):
    """Valor que nunca poderia entrar — nome vazio, identificador em branco."""


class MutacaoRecusada(ErroDeDominio):
    """A operação é válida em geral, mas não neste estado do agregado."""


class NaoEncontrado(ErroDeDominio):
    """O agregado não existe **para este inquilino**.

    Por que não existe `Proibido` ao lado: através da fronteira do inquilino, a resposta
    é sempre esta. Distinguir "não existe" de "existe e é de outro" vazaria a existência
    do projeto alheio — que é justamente o que o isolamento (RNF-03) protege.
    """


class ArestaInvalida(MutacaoRecusada):
    """Aresta que viola uma regra de grafo — e a regra tem NOME.

    A spec 004 (RF-18) exige "mensagem que diga a regra violada"; um erro genérico
    obrigaria a borda a adivinhar por texto. `regra` é uma das três:
    `pontas_no_projeto` (RF-20), `sem_auto_laco` (RN-02), `sem_duplicata` (RN-03) — e é
    a mesma palavra que a restrição do banco carrega em `infra/persistencia/tabelas.py`.
    """

    def __init__(self, regra: str, detalhe: str = "") -> None:
        super().__init__(f"{regra}: {detalhe}" if detalhe else regra)
        self.regra = regra
