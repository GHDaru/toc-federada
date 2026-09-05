"""O adaptador de introspecção — `POST {HOST_BASE_URL}/auth/introspect`, servidor a servidor.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol* ·
**TTL** — *Time To Live* (tempo de vida) · **JSON** — *JavaScript Object Notation*.

O que este arquivo garante, e cada item tem número na norma:

- **A troca é servidor a servidor** (§B.6.2, RF-06). O navegador nunca vê a credencial da
  aplicação, e o grant nunca é validado no cliente. P7 em uma linha.
- **O grant não é bearer** (§B.6.2). Ele viaja no **corpo**, em `{"token": …}`; quem
  autentica a chamada é a credencial da aplicação, no cabeçalho.
- **401 não vira retry** (RF-11). O 401 do hospedeiro é uniforme por desenho e não diz qual
  é o caso; tentar de novo é gastar tentativa contra uma resposta que não muda. O que se
  faz é registrar e sinalizar rotação da credencial.
- **Falha de rede ou 5xx é falha fechada** (RF-10). Nunca "presume válido", nunca cache de
  identidade para "não incomodar a fundação".
- **O grant nunca é registrado** (RNF-01): não entra em log, span, exceção nem `repr`. O
  `__repr__` do adaptador redige a credencial pelo mesmo motivo.

`httpx` mora **aqui** e em nenhum outro lugar do serviço — é o que o contrato P3-2 do
`import-linter` impõe, e a razão é a de sempre: efeito só por porta.
"""
from __future__ import annotations

from typing import Any, Mapping

import httpx

from ...dominio.federacao.principal import Principal, principal_de_introspeccao
from ...dominio.erros import ErroDeDominio

TEMPO_LIMITE_PADRAO = 5.0


class FundacaoIndisponivel(ErroDeDominio):
    """Rede caiu, tempo esgotou ou o hospedeiro respondeu 5xx. Falha **fechada**."""

    codigo = "FUNDACAO_INDISPONIVEL"


class CredencialRecusada(ErroDeDominio):
    """O hospedeiro respondeu 401 à **nossa** credencial — rotação, não retry (RF-11)."""

    codigo = "CREDENCIAL_RECUSADA"


class IntrospeccaoHttp:
    """Implementa `PortaDeIntrospeccao` com `httpx`. Cliente injetável, como no `ghdaru`."""

    def __init__(
        self,
        *,
        url: str,
        credencial: str,
        cliente: httpx.Client | None = None,
        tempo_limite: float = TEMPO_LIMITE_PADRAO,
    ) -> None:
        self._url = url
        self._credencial = credencial
        self._cliente = cliente
        self._tempo_limite = tempo_limite

    def __repr__(self) -> str:
        return f"IntrospeccaoHttp(url={self._url!r}, credencial='***')"

    def _executar(self, grant: str) -> tuple[int, Mapping[str, Any] | None]:
        cabecalhos = {
            # §B.6.6/spec 047 da fundação: o endpoint autentica o chamador, e quem se
            # autentica é a APLICAÇÃO. O grant do usuário vai no corpo, nunca aqui.
            "Authorization": f"Bearer {self._credencial}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        corpo = {"token": grant}
        try:
            if self._cliente is not None:
                resposta = self._cliente.post(self._url, json=corpo, headers=cabecalhos)
            else:
                with httpx.Client(timeout=self._tempo_limite) as cliente:
                    resposta = cliente.post(self._url, json=corpo, headers=cabecalhos)
        except httpx.HTTPError as erro:
            # A mensagem carrega o TIPO da falha, nunca o grant: `str(erro)` de httpx pode
            # trazer a URL, e a URL não tem segredo — o corpo é que teria.
            raise FundacaoIndisponivel(
                f"introspecção inalcançável ({type(erro).__name__}); a aplicação nega tudo"
            ) from None
        try:
            dados = resposta.json()
        except ValueError:
            dados = None
        return resposta.status_code, dados if isinstance(dados, Mapping) else None

    def trocar_grant(self, grant: str) -> Principal:
        status, dados = self._executar(grant)

        if status == 401:
            raise CredencialRecusada(
                "o hospedeiro recusou a credencial da aplicação — rotacione a credencial; "
                "sem retry automático, porque o 401 é uniforme por desenho (§B.6, RF-11)"
            )
        if status >= 500:
            raise FundacaoIndisponivel(f"introspecção respondeu HTTP {status}; a aplicação nega tudo")
        if status >= 400 or dados is None:
            # §B.6.3: as três respostas são de SUCESSO — o status não discrimina entre
            # elas. Um 4xx aqui é o hospedeiro fora do contrato, e a resposta é fechar.
            raise FundacaoIndisponivel(
                f"introspecção respondeu HTTP {status} fora do contrato do §B.6.3"
            )

        # A tradução resposta → identidade acontece **uma vez**, aqui. É o que impede que
        # cada chamador invente a sua (§B.6.2).
        return principal_de_introspeccao(dados)
