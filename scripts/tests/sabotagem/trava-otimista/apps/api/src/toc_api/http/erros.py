"""Esqueleto da borda — o tradutor da recusa em 409 com os dois números."""


def registrar_tradutores(app):
    @app.exception_handler(ConflitoDeVersao)
    async def _conflito_de_versao(request, erro):
        return _resposta(
            409,
            "VERSION_CONFLICT",
            str(erro),
            detalhes={
                "agregado": erro.agregado,
                "versao_lida": erro.versao_lida,
                "versao_atual": erro.versao_atual,
            },
        )
