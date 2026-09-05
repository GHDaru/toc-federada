"""Identidade no domínio — apenas o par que isola, nunca a credencial.

Não existe entidade `Usuario` persistida, e a ausência é decisão de spec, não esquecimento:
`specs/003-esqueleto-federado/data-model.md` diz "Usuário e senha: não existem. Identidade
é da fundação, por introspecção (ADR 0003); persistir credencial criaria o login próprio
que o P2 proíbe". O que atravessa a fronteira e chega aqui é este objeto de valor.
"""
from __future__ import annotations

from dataclasses import dataclass

from .erros import DadoInvalido


@dataclass(frozen=True, slots=True)
class DonoDoProjeto:
    """`(inquilino_id, usuario_id)`, ambos vindos da introspecção (spec 004, INT-01).

    Imutável e igual por valor. É a chave do isolamento (RNF-03): nenhuma consulta do
    repositório existe sem o `inquilino_id` que sai daqui.
    """

    inquilino_id: str
    usuario_id: str

    def __post_init__(self) -> None:
        # O defeito D-02 da linhagem foi um `'user_placeholder_001'`: sem usuário real não
        # há isolamento. Um identificador em branco é a mesma coisa com outro nome.
        if not self.inquilino_id or not self.inquilino_id.strip():
            raise DadoInvalido("inquilino_id vazio")
        if not self.usuario_id or not self.usuario_id.strip():
            raise DadoInvalido("usuario_id vazio")
