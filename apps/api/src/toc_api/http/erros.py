"""Tradução de recusa para HTTP — códigos ESTÁVEIS em caixa alta (Anexo A §A.7).

O corpo de erro é `{"error": {code, message, details?}}`, a forma que o Anexo A do Padrão
APH (Aplicação ↔ Harness) fixa na linha 42 ("Erros HTTP usam o corpo `{"error": <Erro
§A.7>}`") e que o `padrao/schemas/erro.schema.json` fecha com `additionalProperties:
false`. O `code` casa `^[A-Z][A-Z0-9_]*$` **porque o cliente discrimina por código e nunca
por mensagem** — a mensagem é para gente, o código é para máquina, e trocá-los é como se
perde a compatibilidade sem mudar uma linha de contrato.

**Dois códigos do registro mínimo do §A.7 são usados aqui com o significado que o registro
lhes dá**, e nenhum outro:

| Código | Situação, palavra por palavra do §A.7 |
|---|---|
| `UNAUTHORIZED` | "ação negada pela política de capabilities (APH-7.2)" |
| `INVALID_TRANSITION` | "confirmação ou transição fora da máquina de estados finitos" |

O §A.7 diz que uma implementação "PODE adicionar os seus", e os acrescentados estão
declarados em **um lugar só**: `dominio/federacao/wire.py`, que é o mesmo registro que o
fio usa. Havia aqui uma segunda tabela, e as duas divergiram — esta borda emitia
`INVALID_ARGUMENT` e a borda APH emitia `INVALID_ARGUMENTS` para a mesma situação, no
mesmo serviço. Como o cliente "discrimina por código e nunca por mensagem", quem tratasse
um dos dois por igualdade quebraria no outro. O §A.2 já dizia que os dois lados são o
mesmo objeto ("Erros HTTP usam o corpo `{"error": <Erro §A.7>}`"), logo o registro também
é um só, e `envelope()` abaixo **constrói pelo domínio**: código não declarado não sai
daqui, ele levanta na hora de montar a resposta. A varredura que impede a divergência de
voltar é `tests/contrato/test_registro_de_codigos_a7.py`.

**Por que `UNAUTHENTICATED` existe, e é acréscimo e não preguiça.** O próprio §A.7
registra, na linha do `UNAUTHORIZED`, uma "ressalva de lastro": o laboratório A "emite este
código literalmente, mas para **falha de autenticação e sessão de terceiro**, não para
negação por política". Usar o mesmo código para "você não se identificou" (401) e para
"você se identificou e não pode" (403) repetiria exatamente o defeito que o anexo
documenta — e apagaria, do lado do cliente, a diferença entre "renove a credencial" e
"peça a capacidade ao administrador".

Nenhuma mensagem daqui carrega texto do usuário, cadeia de conexão ou credencial (P7).
"""
from __future__ import annotations

from typing import Any

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as ErroHTTPStarlette

from ..aplicacao.governanca import AutorizacaoNegada, PoliticaAusente
from ..dominio.ara import ConectorInvalido, TransicaoDeStatusRecusada
from ..dominio.geracao import ResultadoDeGeracaoInvalido
from ..dominio.nuvem import (
    DerivacaoInvalida,
    InjecaoInvalida,
    PremissaInvalida,
    TopologiaImutavel,
    TransicaoDeInjecaoRecusada,
)
from ..dominio.federacao.wire import CODIGOS_PROPRIOS, ErroDoFio
from ..dominio.erros import (
    ArestaInvalida,
    DadoInvalido,
    ErroDeDominio,
    MutacaoForaDaRaiz,
    MutacaoRecusada,
    NaoEncontrado,
)

#: O registro é o do domínio — este nome existe para quem lê esta borda encontrar a
#: tabela sem sair do arquivo, e para o teste de varredura conferir que é a MESMA.
CODIGOS_ACRESCENTADOS: dict[str, str] = CODIGOS_PROPRIOS

#: A tradução de um `HTTPException` do Starlette em código do §A.7. Era um dicionário
#: dentro do tratador; subiu para cá porque um mapa de códigos escondido dentro de uma
#: função é invisível para quem varre o código-fonte — e o defeito que este módulo acabou
#: de pagar nasceu exatamente de um código que ninguém comparava com o registro.
CODIGO_POR_STATUS: dict[int, str] = {
    401: "UNAUTHENTICATED",
    403: "UNAUTHORIZED",
    404: "NOT_FOUND",
    405: "METHOD_NOT_ALLOWED",
}


class NaoAutenticado(Exception):
    """Não veio identidade utilizável. Sem detalhe do motivo — §B.6.5 do Anexo B.

    "Token inexistente", "expirado" e "já consumido" respondem igual: a diferença "é
    oráculo para quem testa tokens".
    """


def envelope(
    codigo: str, mensagem: str, *, detalhes: dict[str, Any] | None = None
) -> dict[str, Any]:
    """`{"error": {code, message, details?}}` — montado pelo domínio, nunca à mão.

    Montar o dicionário aqui foi o que permitiu a divergência: esta borda não passava por
    nenhuma validação de código, enquanto a borda APH passava por `ErroDoFio`. Agora é a
    mesma porta para as duas — código fora do registro levanta antes de virar resposta.

    A mensagem tem de existir (o schema normativo exige `minLength: 1`); quando a recusa
    de origem vem sem texto, o código vira a mensagem — que é pobre para gente e correto
    para máquina, e é melhor que um 500 no meio de um tratador de erro.
    """
    return ErroDoFio(code=codigo, message=mensagem or codigo, details=detalhes).como_corpo_http()


def _resposta(
    status: int,
    codigo: str,
    mensagem: str,
    *,
    detalhes: dict[str, Any] | None = None,
    cabecalhos: dict[str, str] | None = None,
) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=envelope(codigo, mensagem, detalhes=detalhes),
        headers=cabecalhos,
    )


def registrar_tradutores(app: FastAPI) -> None:
    """Liga cada recusa ao seu código. Ordem importa: a subclasse é registrada primeiro.

    O Starlette resolve o tratador percorrendo a ordem de resolução de método da exceção,
    então `ArestaInvalida` (que é `MutacaoRecusada`) precisa do seu próprio registro para
    não cair no genérico e perder o nome da regra violada.
    """

    @app.exception_handler(NaoAutenticado)
    async def _nao_autenticado(request: Request, erro: NaoAutenticado):
        return _resposta(
            401,
            "UNAUTHENTICATED",
            "identidade ausente ou não reconhecida",
            cabecalhos={"WWW-Authenticate": "Bearer"},
        )

    @app.exception_handler(AutorizacaoNegada)
    async def _sem_capacidade(request: Request, erro: AutorizacaoNegada):
        return _resposta(
            403,
            "UNAUTHORIZED",
            f"a operação {erro.operacao} exige a capability {erro.capability}",
            detalhes={"capacidade": erro.capability, "operacao": erro.operacao},
        )

    @app.exception_handler(PoliticaAusente)
    async def _sem_politica(request: Request, erro: PoliticaAusente):
        # Fail-closed: falta REGRA, não falta capacidade — e mesmo assim a resposta é
        # recusa. Um caso de uso sem política nunca chega aqui em produção porque o teste
        # de cobertura da política o pega antes; se chegar, ele não passa.
        return _resposta(
            403,
            "UNAUTHORIZED",
            "operação sem política de capacidade declarada — negada por omissão",
            detalhes={"operacao": getattr(erro.classe, "nome", erro.classe.__name__)},
        )

    @app.exception_handler(NaoEncontrado)
    async def _nao_encontrado(request: Request, erro: NaoEncontrado):
        return _resposta(404, "NOT_FOUND", "recurso não encontrado")

    @app.exception_handler(ArestaInvalida)
    async def _aresta_invalida(request: Request, erro: ArestaInvalida):
        return _resposta(
            409,
            "INVALID_EDGE",
            str(erro),
            detalhes={"regra": erro.regra},
        )

    @app.exception_handler(ConectorInvalido)
    async def _conector_invalido(request: Request, erro: ConectorInvalido):
        return _resposta(
            409, "INVALID_CONNECTOR", str(erro), detalhes={"regra": erro.regra}
        )

    @app.exception_handler(TransicaoDeStatusRecusada)
    async def _transicao(request: Request, erro: TransicaoDeStatusRecusada):
        return _resposta(
            409, "INVALID_TRANSITION", str(erro), detalhes={"motivo": erro.motivo}
        )

    @app.exception_handler(TopologiaImutavel)
    async def _topologia(request: Request, erro: TopologiaImutavel):
        return _resposta(409, "FIXED_TOPOLOGY", str(erro), detalhes={"regra": erro.regra})

    @app.exception_handler(PremissaInvalida)
    async def _premissa(request: Request, erro: PremissaInvalida):
        return _resposta(
            409, "INVALID_ASSUMPTION", str(erro), detalhes={"regra": erro.regra}
        )

    @app.exception_handler(InjecaoInvalida)
    async def _injecao(request: Request, erro: InjecaoInvalida):
        return _resposta(
            409, "INVALID_INJECTION", str(erro), detalhes={"regra": erro.regra}
        )

    @app.exception_handler(DerivacaoInvalida)
    async def _derivacao(request: Request, erro: DerivacaoInvalida):
        return _resposta(
            409, "INVALID_DERIVATION", str(erro), detalhes={"regra": erro.regra}
        )

    @app.exception_handler(TransicaoDeInjecaoRecusada)
    async def _transicao_de_injecao(request: Request, erro: TransicaoDeInjecaoRecusada):
        return _resposta(
            409, "INVALID_TRANSITION", str(erro), detalhes={"motivo": erro.motivo}
        )

    @app.exception_handler(ResultadoDeGeracaoInvalido)
    async def _geracao_invalida(request: Request, erro: ResultadoDeGeracaoInvalido):
        return _resposta(
            422, "INVALID_GENERATION_RESULT", str(erro), detalhes={"codigo": erro.codigo}
        )

    @app.exception_handler(MutacaoForaDaRaiz)
    async def _fora_da_raiz(request: Request, erro: MutacaoForaDaRaiz):
        """Operação só pela raiz do agregado — a regra mais antiga do DDD, agora imposta.

        Antes desta tradução, mutilar uma Nuvem de Conflito pela rota genérica do M1
        respondia `204 No Content` e a nuvem sumia da leitura logo depois: a aresta que
        faltava fazia a raiz não encontrar mais a topologia, e o cliente via `NOT_FOUND`
        sobre um projeto que ainda estava no banco.
        """
        return _resposta(
            409,
            "AGGREGATE_ROOT_REQUIRED",
            str(erro),
            detalhes={
                "operacao": erro.operacao,
                "ferramenta": erro.ferramenta,
                "raiz": erro.raiz,
            },
        )

    @app.exception_handler(MutacaoRecusada)
    async def _mutacao(request: Request, erro: MutacaoRecusada):
        return _resposta(409, "MUTATION_REFUSED", str(erro))

    @app.exception_handler(DadoInvalido)
    async def _dado_invalido(request: Request, erro: DadoInvalido):
        return _resposta(422, "INVALID_ARGUMENT", str(erro))

    @app.exception_handler(ErroDeDominio)
    async def _dominio(request: Request, erro: ErroDeDominio):
        # Rede de segurança: nenhuma recusa de domínio vira 500. Um 500 diria ao cliente
        # "o servidor quebrou" sobre uma regra de negócio que funcionou.
        return _resposta(409, "DOMAIN_REFUSED", str(erro))

    @app.exception_handler(RequestValidationError)
    async def _corpo_invalido(request: Request, erro: RequestValidationError):
        return _resposta(
            422,
            "INVALID_ARGUMENT",
            "corpo ou parâmetro fora do esquema declarado",
            detalhes={
                "campos": [
                    {
                        "onde": ".".join(str(p) for p in item.get("loc", ())),
                        "motivo": item.get("msg", ""),
                    }
                    for item in erro.errors()
                ]
            },
        )

    @app.exception_handler(ErroHTTPStarlette)
    async def _http(request: Request, erro: ErroHTTPStarlette):
        codigo = CODIGO_POR_STATUS.get(erro.status_code, "DOMAIN_REFUSED")
        return _resposta(
            erro.status_code,
            codigo,
            str(erro.detail),
            cabecalhos=getattr(erro, "headers", None),
        )
