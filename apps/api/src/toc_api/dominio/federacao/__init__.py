"""Federação APH (Aplicação ↔ Harness) — a fronteira, como regra de domínio pura.

Siglas, uma vez: **APH** — Aplicação ↔ Harness, o padrão da fronteira · **FSM** — máquina
de estados finitos · **SSE** — *Server-Sent Events* · **TTL** — *Time To Live* (tempo de
vida) · **UDE** — Efeito Indesejável · **JSON** — *JavaScript Object Notation*.

Por que a federação inteira mora no **domínio** e não na borda: o P2 do projeto declara a
federação por contrato como INEGOCIÁVEL, e contrato que vive no adaptador é contrato que
cada rota nova reimplementa pela metade. Aqui estão, puras e testáveis sem rede:

- `admissao`   — os parâmetros do §B.4 e a recusa de subir que nomeia o que faltou.
- `principal`  — a identidade que só existe depois da introspecção (§B.6.2).
- `esquema`    — o validador do subconjunto de JSON Schema que os `input_schema` usam.
- `catalogo`   — a fonte única `AcaoDoCatalogo` e as suas três projeções (APH-4.4).
- `proposta`   — a FSM de proposta de ação (APH-5.1) e o lote com desfecho por alvo.
- `telas`      — o registro de telas compartilhado (APH-3.1).
- `snapshot`   — a sanitização em três camadas, no servidor (APH-3.3/3.5).
- `wire`       — o envelope de evento, os códigos de erro e a sessão de conversa.
- `traco`      — o traço de execução, que existe para 100% das ações (APH-5.5).
- `canal`      — as regras do envelope `ghd.*` do Anexo B, §B.2.

Nada aqui importa framework: o contrato P3-1 do `import-linter` reprova quem tentar.
"""
