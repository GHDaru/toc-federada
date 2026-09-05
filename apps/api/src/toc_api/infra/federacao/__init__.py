"""Adaptadores da federação — a borda onde o efeito acontece.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **HTTP** — *HyperText Transfer Protocol* ·
**SSE** — *Server-Sent Events* · **SQL** — *Structured Query Language*.

O domínio e a aplicação não conhecem nada daqui: falam com `typing.Protocol`. O que mora
neste pacote é o que fala com o mundo — a introspecção por HTTP, os repositórios (memória e
PostgreSQL), o motor de conversa determinístico e o executor que liga o catálogo `toc.*`
aos casos de uso do M1 e do M2.
"""
