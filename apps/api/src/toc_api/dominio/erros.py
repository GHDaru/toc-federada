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


class MutacaoForaDaRaiz(MutacaoRecusada):
    """O estado é de uma ferramenta e a mutação não veio pela RAIZ do agregado dela.

    A regra que este erro impõe é a mais antiga do Design Orientado a Domínio (DDD):
    **operação só pela raiz do agregado**. As ferramentas da Teoria das Restrições (TOC)
    são raízes por composição — `ProjetoARA` e `NuvemDeConflito` contêm um `Projeto` do
    núcleo e acrescentam invariantes próprias (a topologia fixa de 5 entidades e 7
    arestas, o exame que nasce com todo elo, o arquivamento da ficha quando um Efeito
    Indesejável some, o conector sem referência órfã). Enquanto o `Projeto` contido
    aceitava mutação de quem o carregasse cru, havia **duas portas para o mesmo estado** e
    as invariantes moravam numa só.

    `ferramenta` e `raiz` viajam no erro porque a borda tem de dizer QUAL é a porta certa
    sem reconstruir a frase por texto — o cliente discrimina por código e por dado, nunca
    por mensagem (Anexo A §A.7 do Padrão APH — Aplicação ↔ Harness).
    """

    def __init__(self, operacao: str, ferramenta: str, raiz: str) -> None:
        super().__init__(
            f"{operacao}: o grafo de um projeto da ferramenta {ferramenta!r} só muda "
            f"pela raiz do agregado ({raiz})"
        )
        self.operacao = operacao
        self.ferramenta = ferramenta
        self.raiz = raiz
