"""Serviço da aplicação toc-federada.

Camadas (brief §3 e P3): `dominio` e `aplicacao` são puros; `infra` e `http` são a borda.
O `import-linter` (contratos P3-1..P3-3 do `pyproject.toml`) é a função de aptidão, e
`scripts/check-arquitetura.sh` é o portão que a roda.
"""

__version__ = "0.1.0"
