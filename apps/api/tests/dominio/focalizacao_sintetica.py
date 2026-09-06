"""A análise sintética "Fluxo de matrículas" da Instituição Horizonte — fixture do M6.

Siglas, uma vez neste arquivo: **M6** — Focalização · **TOC** — Teoria das Restrições ·
**ARA** — Árvore da Realidade Atual · **NC** — Nuvem de Conflito · **APR** — Árvore de
Pré-Requisitos · **AT** — Árvore de Transição · **ADR** — *Architecture Decision Record*
(Registro de Decisão Arquitetural).

Nenhum dado real de pessoa entra aqui (ADR 0006): a instituição é fictícia, as personas
são papéis ("Facilitadora TOC", "Gestora") e o sistema analisado é inventado para o
teste. É a regra do `CLAUDE.md` — "a base é sintética desde o dia 1" — e
`scripts/check-vazamento.sh` é quem a confere.

O conteúdo respeita o método dos cinco passos: a restrição é uma **capacidade** concreta
do sistema analisado, e as decisões de exploração e de subordinação são regras de
operação — que é exatamente a matéria que sobrevive por inércia e que o quinto passo
existe para confrontar.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from uuid import UUID

from toc_api.dominio.identidade import DonoDoProjeto

AGORA = datetime(2026, 9, 6, 9, 0, tzinfo=timezone.utc)


def depois(minutos: int) -> datetime:
    """Instantes distintos e determinísticos — o relógio é porta, nunca `now()`."""
    return AGORA + timedelta(minutes=minutos)


DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-horizonte-01")
OUTRO_DONO = DonoDoProjeto(inquilino_id="instituicao-aurora", usuario_id="u-aurora-01")

AUTORA = "Facilitadora TOC"
GESTORA = "Gestora"

ID_DA_ANALISE = UUID("66666666-6666-4666-8666-666666666661")

#: Projetos das outras ferramentas, referenciados por identificador OPACO no domínio.
#: O domínio do M6 não sabe o que há dentro deles — é a decisão 2 do plano do ciclo 009,
#: e é o que faz esta suíte rodar sem que M2, M3 e M4 existam.
ID_DA_ARA = UUID("55555555-5555-4555-8555-555555555551")
ID_DA_NC = UUID("55555555-5555-4555-8555-555555555552")
ID_DA_APR = UUID("55555555-5555-4555-8555-555555555553")
ID_DA_AT = UUID("55555555-5555-4555-8555-555555555554")
ID_DA_ARF = UUID("55555555-5555-4555-8555-555555555555")

#: O nó de causa raiz da ARA sintética de onde a restrição do primeiro ciclo nasce.
ID_DO_NO_DE_CAUSA_RAIZ = UUID("44444444-4444-4444-8444-444444444441")

NOME = "Fluxo de matrículas"
SISTEMA = "Da inscrição do candidato à primeira aula assistida"
DESCRICAO_DO_SISTEMA = (
    "O fluxo de matrículas da Instituição Horizonte vai da inscrição do candidato até a "
    "primeira aula assistida, passando por conferência documental, contrato e alocação "
    "de turma."
)

RESTRICAO = "Capacidade de conferência da secretaria acadêmica"
JUSTIFICATIVA_DA_RESTRICAO = (
    "A fila de matrículas aguardando conferência documental cresce em todo período de "
    "entrada, e nenhuma outra etapa acumula fila."
)

DECISAO_DE_EXPLORAR = (
    "Priorizar na fila de conferência as matrículas com documentação completa"
)
DECISAO_DE_SUBORDINAR = (
    "Nenhuma turma abre antes de a secretaria confirmar a conferência da turma inteira"
)
DECISAO_DE_ELEVAR = (
    "Contratar duas pessoas para a conferência e treinar a equipe de atendimento"
)

CONFLITO_DE_SUBORDINACAO = (
    "A coordenação de cursos contesta a regra de só abrir turma com a conferência "
    "concluída: para ela, a turma cheia é o que garante o semestre."
)
