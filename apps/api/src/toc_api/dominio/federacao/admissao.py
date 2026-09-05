"""Admissão — os parâmetros que a aplicação exige para subir (§B.4 do Anexo B).

Siglas, uma vez neste arquivo: **APH** — Aplicação ↔ Harness · **URL** — *Uniform Resource
Locator*.

A regra em uma frase: **a aplicação não pergunta, exige na partida, e recusa subir
nomeando qual parâmetro faltou** (§B.4.1). Subir pela metade e funcionar até alguém clicar
é não-conformidade com nome.

Três decisões que não são estilo:

1. **Função pura sobre um mapa**, não leitura de `os.environ`. Assim a regra é testável
   sem processo, e existe **um** lugar que sabe o nome de cada variável. É o mesmo motivo
   da `infra/configuracao.py` — aqui a mesma disciplina, mas no domínio, porque §B.4 é
   norma da fronteira e não detalhe de infraestrutura.
2. **Origem nunca vem de mensagem.** O §B.2.3 é explícito, e o contraexemplo registrado na
   norma é uma aplicação que lia a origem esperada de `payload.host_origin` — circular,
   porque quem envia escolheria contra o que ser conferido. A assinatura desta função é a
   defesa: ela só enxerga configuração.
3. **A validação de forma acontece aqui**, não no primeiro embarque. Uma `HOST_ORIGIN` com
   caminho (`https://host/app`) nunca casaria com `event.origin`, e o defeito só apareceria
   na junta real — tarde, e parecendo defeito do hospedeiro.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Mapping

from ..erros import ErroDeDominio

# Origem é `esquema://host[:porta]` — sem caminho, sem barra final, sem consulta.
# `event.origin` do navegador tem exatamente esta forma; comparar por igualdade com
# qualquer outra coisa é comparar com o que nunca chega.
FORMA_DE_ORIGEM = re.compile(r"^https?://[a-z0-9.-]+(:\d+)?$", re.IGNORECASE)

# `app_id` estável e único, na forma do §B.5.2 do Anexo B.
FORMA_DE_APP_ID = re.compile(r"^[a-z][a-z0-9-]{1,48}$")


class AdmissaoRecusada(ErroDeDominio):
    """A aplicação não sobe. Carrega o **código** e o **parâmetro** — não só um texto.

    O código é o que a operadora procura na documentação; o parâmetro é o que ela
    corrige. Uma exceção com só a frase obrigaria quem lê o log a inferir os dois.
    """

    def __init__(self, codigo: str, parametro: str, detalhe: str) -> None:
        super().__init__(f"{codigo}: {parametro} — {detalhe}")
        self.codigo = codigo
        self.parametro = parametro
        self.detalhe = detalhe


@dataclass(frozen=True, slots=True)
class ParametroDeAdmissao:
    """Uma linha da tabela do §B.4 (ou uma exigência nossa, declarada como tal)."""

    variavel: str
    codigo: str
    para_que: str
    do_anexo_b: bool
    segredo: bool = False


# A ordem é o roteiro de diagnóstico: faltando tudo, a recusa aponta a primeira linha, e
# a operadora corrige de cima para baixo. Determinismo aqui é usabilidade de operação.
OBRIGATORIOS: tuple[ParametroDeAdmissao, ...] = (
    ParametroDeAdmissao(
        "HOST_ORIGIN",
        "ADMISSAO_HOST_ORIGIN_AUSENTE",
        "origem do shell, conferida em todo postMessage recebido e usada como targetOrigin",
        do_anexo_b=True,
    ),
    ParametroDeAdmissao(
        "HOST_BASE_URL",
        "ADMISSAO_HOST_BASE_URL_AUSENTE",
        "base da introspecção (POST /auth/introspect), perfil e auditoria",
        do_anexo_b=True,
    ),
    ParametroDeAdmissao(
        "APP_ID",
        "ADMISSAO_APP_ID_AUSENTE",
        "identidade no manifesto e prefixo das ações (toc.*)",
        do_anexo_b=True,
    ),
    ParametroDeAdmissao(
        "EMBED_URL",
        "ADMISSAO_EMBED_URL_AUSENTE",
        "ponto de montagem declarado no manifesto",
        do_anexo_b=True,
    ),
    ParametroDeAdmissao(
        "TOC_APP_CREDENTIAL",
        "ADMISSAO_CREDENCIAL_AUSENTE",
        "credencial da aplicação no introspect; segredo de servidor, nunca no bundle",
        do_anexo_b=False,
        segredo=True,
    ),
    ParametroDeAdmissao(
        "DATABASE_URL",
        "ADMISSAO_DATABASE_URL_AUSENTE",
        "banco próprio da aplicação (E8.1); nada compartilhado com a fundação",
        do_anexo_b=False,
        segredo=True,
    ),
)

CAMINHO_DA_INTROSPECCAO = "/auth/introspect"


@dataclass(frozen=True, slots=True)
class Admissao:
    """Os parâmetros admitidos, já validados de forma. Imutável e sem segredo no `repr`."""

    host_origin: str
    host_base_url: str
    app_id: str
    embed_url: str
    credencial_da_aplicacao: str
    url_do_banco: str

    @property
    def url_de_introspeccao(self) -> str:
        return f"{self.host_base_url.rstrip('/')}{CAMINHO_DA_INTROSPECCAO}"

    def __repr__(self) -> str:
        # RNF-01/RNF-02: credencial e cadeia de conexão NUNCA aparecem. Um `repr` que
        # vaza segredo não vaza no dia em que se escreve — vaza no dia em que alguém
        # imprime a exceção.
        return (
            f"Admissao(host_origin={self.host_origin!r}, "
            f"host_base_url={self.host_base_url!r}, app_id={self.app_id!r}, "
            f"embed_url={self.embed_url!r}, credencial_da_aplicacao='***', "
            f"url_do_banco='***')"
        )


def _exigir(ambiente: Mapping[str, str], parametro: ParametroDeAdmissao) -> str:
    valor = (ambiente.get(parametro.variavel) or "").strip()
    if not valor:
        raise AdmissaoRecusada(
            parametro.codigo,
            parametro.variavel,
            f"exigido para {parametro.para_que}",
        )
    return valor


def exigir_admissao(ambiente: Mapping[str, str]) -> Admissao:
    """Lê o ambiente e devolve a admissão — ou recusa nomeando o que impede subir.

    Quem chama é o arranque do serviço (`http/app.py`), e a recusa termina o processo com
    código de saída diferente de zero, sem abrir porta (RF-04).
    """
    valores = {p.variavel: _exigir(ambiente, p) for p in OBRIGATORIOS}

    origem = valores["HOST_ORIGIN"]
    if origem.lower() == "null" or not FORMA_DE_ORIGEM.match(origem):
        raise AdmissaoRecusada(
            "ADMISSAO_HOST_ORIGIN_INVALIDA",
            "HOST_ORIGIN",
            f"esperado esquema://host[:porta] sem caminho, recebido {origem!r} "
            "(a origem 'null' de documento opaco nunca é admitida — §B.2.3)",
        )

    base = valores["HOST_BASE_URL"]
    if not base.lower().startswith(("http://", "https://")):
        raise AdmissaoRecusada(
            "ADMISSAO_HOST_BASE_URL_INVALIDA",
            "HOST_BASE_URL",
            f"esperada URL absoluta, recebido {base!r}",
        )

    app_id = valores["APP_ID"]
    if not FORMA_DE_APP_ID.match(app_id):
        raise AdmissaoRecusada(
            "ADMISSAO_APP_ID_INVALIDO",
            "APP_ID",
            f"esperada a forma ^[a-z][a-z0-9-]{{1,48}}$ (§B.5.2), recebido {app_id!r}",
        )

    embed = valores["EMBED_URL"]
    # `https` é exigência do schema normativo do manifesto para `url` e `origin`; uma
    # `EMBED_URL` em `http` produziria manifesto inválido só na hora de submeter.
    if not embed.lower().startswith("https://"):
        raise AdmissaoRecusada(
            "ADMISSAO_EMBED_URL_INVALIDA",
            "EMBED_URL",
            f"esperada URL https (§B.1.3 e schema do manifesto), recebido {embed!r}",
        )

    return Admissao(
        host_origin=origem,
        host_base_url=base,
        app_id=app_id,
        embed_url=embed,
        credencial_da_aplicacao=valores["TOC_APP_CREDENTIAL"],
        url_do_banco=valores["DATABASE_URL"],
    )
