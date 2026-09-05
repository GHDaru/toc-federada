"""Casos de uso da federação — orquestração pura sobre as portas do Anexo A e B.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **FSM** — máquina de estados finitos.

Camada pura: zero import de SQLAlchemy, FastAPI, Pydantic, httpx ou OpenTelemetry — o
contrato P3-2 do `import-linter` reprova quem mudar isso. O span é aberto pela classe-base
`CasoDeUso`, inclusive quando o caso de uso recusa: recusa também é traço.
"""
