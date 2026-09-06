"""O catálogo `toc.*` — a **única** superfície executável (APH-4.1).

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **JSON** — *JavaScript Object Notation* ·
**MCP** — *Model Context Protocol* · **UDE** — Efeito Indesejável · **UI** — interface de
usuário.

Uma fonte, três projeções (APH-4.4, RF-07). A fonte é a `AcaoDoCatalogo` deste módulo; as
projeções são:

| Projeção | Método | Consumidor |
|---|---|---|
| validação de argumentos | `validar_args` | a proposta, no servidor |
| ferramenta do modelo | `como_ferramenta` | a fundação, que fala com o modelo (ADR 0007) |
| entrada do manifesto | `como_manifesto` | a admissão do hospedeiro |
| ferramenta MCP (futura) | `como_ferramenta_mcp` | Nível 3, fora do alvo (ADR 0003) |

A quarta linha existe de propósito: o Nível 3 está **fora de escopo**, e é justamente por
isso que a projeção é uma função pura de dez linhas em vez de um servidor. O dia em que
alguém decidir o Nível 3, o que muda é o transporte, não a fonte — que é o argumento do
APH-4.4 escrito em código.

**Derivado de permissão** (APH-4.3, §B.7.3): `compor(principal)` devolve só o que aquele
principal pode fazer. Ação cuja capability ele não tem **não existe** para ele — ausência,
nunca recusa visível, porque a recusa revela o inventário.

**Uma nota sobre o `batch_atomicity`.** Ele é servido no catálogo (§A.5) e **não** entra no
manifesto: o schema normativo do manifesto não tem o campo (L-02 da spec 006, verificado em
`tests/federacao/test_catalogo.py`). A decisão está declarada, e o teste impede que ela
vire esquecimento.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Mapping

from ..erros import ErroDeDominio
from ..geracao import ESQUEMA_DO_RESULTADO
from ..nuvem import ChaveDaAresta, SeparacaoTRIZ
from .esquema import exigir_esquema_suportado, validar_contra_esquema
from .principal import Principal

# RN-01 da spec 006: a taxonomia mínima comprovada da norma (§B.5.3). Classe nova exige
# ADR — e o teste de domínio recusa qualquer coisa fora daqui.
RISCOS = frozenset({"read", "confirm"})

PREFIXO_DO_APP = "toc"


class AcaoDesconhecida(ErroDeDominio):
    """A ação não existe **para este principal**.

    O mesmo erro cobre "não existe" e "existe e você não pode", de propósito: distinguir
    os dois vazaria o inventário de quem tem mais permissão (§B.7.3).
    """


@dataclass(frozen=True, slots=True)
class AcaoDoCatalogo:
    """O `ActionSpec` do §4.4 do padrão — quatro declarações obrigatórias (APH-4.2)."""

    action_id: str
    title: str
    risk: str
    input_schema: Mapping[str, Any]
    description: str = ""
    ui_route: str | None = None
    intent_keywords: tuple[str, ...] = ()
    reversible: bool | None = None
    batch_atomicity: str | None = None
    # Qual campo dos `args` carrega os N alvos de um lote. Existe porque o desfecho por
    # alvo (APH-5.9(b)) precisa saber o que é um alvo **nesta** ação, e adivinhar por
    # "o primeiro array que eu achar" é a heurística que quebra na ação seguinte.
    campo_de_alvos: str | None = None

    def __post_init__(self) -> None:
        if not self.action_id or not self.action_id.startswith(f"{PREFIXO_DO_APP}."):
            raise ValueError(
                f"action_id {self.action_id!r} fora da forma <ns>.<id> com ns={PREFIXO_DO_APP!r} (§B.5.2)"
            )
        if not self.title:
            raise ValueError(f"{self.action_id}: ação sem título não entra no catálogo (APH-4.2)")
        if self.risk not in RISCOS:
            raise ValueError(
                f"{self.action_id}: risco {self.risk!r} fora da taxonomia {sorted(RISCOS)} (RN-01)"
            )
        if not self.input_schema:
            raise ValueError(f"{self.action_id}: ação sem input_schema não entra (APH-4.2)")
        if self.batch_atomicity is not None:
            if self.batch_atomicity not in {"all_or_nothing", "per_item"}:
                raise ValueError(f"{self.action_id}: batch_atomicity inválida")
            if not self.campo_de_alvos:
                raise ValueError(
                    f"{self.action_id}: ação de lote sem `campo_de_alvos` — o desfecho por "
                    "alvo (APH-5.9(b)) não teria como nomear os alvos"
                )
        elif self.campo_de_alvos:
            raise ValueError(
                f"{self.action_id}: `campo_de_alvos` sem `batch_atomicity` — ausente "
                "significa 'não desenhada para lote' (§A.5), nunca per_item por omissão"
            )

    # -- permissão -----------------------------------------------------------------
    @property
    def capability_exigida(self) -> str:
        """`read` → `toc:read`; `confirm` → `toc:write`.

        A derivação é uma linha porque a taxonomia é de duas classes (RN-01). Se um dia
        houver uma terceira, ela vem com ADR e esta função vira tabela — não `if` solto
        espalhado por rota, que é a armadilha do §B.7.2.
        """
        return f"{PREFIXO_DO_APP}:write" if self.risk == "confirm" else f"{PREFIXO_DO_APP}:read"

    @property
    def requires_confirmation(self) -> bool:
        """APH-5.2: a classe de risco decide, no servidor e antes da conversa."""
        return self.risk == "confirm"

    def visivel_para(self, principal: Principal) -> bool:
        return principal.pode(self.capability_exigida)

    # -- projeção 1: validação de argumentos ----------------------------------------
    def validar_args(self, args: Mapping[str, Any]) -> None:
        validar_contra_esquema(dict(args), self.input_schema)

    def alvos(self, args: Mapping[str, Any]) -> tuple[str, ...]:
        """Os identificadores dos alvos de um lote, no vocabulário da própria ação."""
        if not self.campo_de_alvos:
            return ()
        brutos = args.get(self.campo_de_alvos) or []
        nomes: list[str] = []
        for i, alvo in enumerate(brutos):
            if isinstance(alvo, str):
                nomes.append(alvo)
            elif isinstance(alvo, Mapping):
                # nome legível quando existe; posição quando não — o alvo precisa de um
                # identificador para o `outcomes`, e "sem nome" não é opção
                nomes.append(str(alvo.get("titulo") or alvo.get("origem_id") or f"#{i + 1}"))
            else:  # pragma: no cover - o esquema já recusou antes de chegar aqui
                nomes.append(f"#{i + 1}")
        return tuple(nomes)

    # -- projeção 2: ferramenta entregue ao modelo (pela fundação, ADR 0007) --------
    def como_ferramenta(self) -> dict[str, Any]:
        return {
            "name": self.action_id,
            "description": self.description or self.title,
            "input_schema": self.input_schema,
            "risk": self.risk,
            "requires_confirmation": self.requires_confirmation,
        }

    # -- projeção 3 (futura, Nível 3): ferramenta do Model Context Protocol ---------
    def como_ferramenta_mcp(self) -> dict[str, Any]:
        return {
            "name": self.action_id,
            "description": self.description or self.title,
            "inputSchema": self.input_schema,
            "annotations": {
                "readOnlyHint": self.risk == "read",
                "destructiveHint": self.risk == "confirm" and self.reversible is not True,
            },
        }

    # -- projeção 4: entrada do manifesto (schema normativo do Anexo B) ------------
    def como_manifesto(self) -> dict[str, Any]:
        entrada: dict[str, Any] = {
            "action_id": self.action_id,
            "title": self.title,
            "description": self.description,
            "risk": self.risk,
        }
        if self.reversible is not None:
            entrada["reversible"] = self.reversible
        entrada["input_schema"] = dict(self.input_schema)
        if self.ui_route:
            entrada["ui_route"] = self.ui_route
        if self.intent_keywords:
            entrada["intent_keywords"] = list(self.intent_keywords)
        return entrada

    # -- o catálogo servido em `GET /aph/catalog` (§A.5) ---------------------------
    def como_catalogo_servido(self) -> dict[str, Any]:
        entrada = self.como_manifesto()
        if self.batch_atomicity:
            entrada["batch_atomicity"] = self.batch_atomicity
        return entrada


@dataclass(frozen=True)
class Catalogo:
    """O conjunto de ações, validado na construção — nada entra torto."""

    acoes: tuple[AcaoDoCatalogo, ...]
    _por_id: dict[str, AcaoDoCatalogo] = field(init=False, repr=False, compare=False)

    def __post_init__(self) -> None:
        vistos: dict[str, AcaoDoCatalogo] = {}
        for acao in self.acoes:
            if acao.action_id in vistos:
                raise ValueError(f"action_id repetido no catálogo: {acao.action_id}")
            # O schema entra no catálogo só se este projeto souber validá-lo. Um schema
            # que o validador não entende produziria proposta aceita sem verificação —
            # e é a classe de defeito que a regra R2 nomeia.
            exigir_esquema_suportado(acao.input_schema)
            vistos[acao.action_id] = acao
        object.__setattr__(self, "_por_id", vistos)

    def acao(self, action_id: str) -> AcaoDoCatalogo:
        try:
            return self._por_id[action_id]
        except KeyError:
            raise AcaoDesconhecida(action_id) from None

    def compor(self, principal: Principal) -> tuple[AcaoDoCatalogo, ...]:
        """APH-4.3: o inventário que **este** principal vê."""
        return tuple(a for a in self.acoes if a.visivel_para(principal))

    def exigir_visivel(self, action_id: str, principal: Principal) -> AcaoDoCatalogo:
        """RF-09: citar `action_id` fora do composto é recusa, sem executar nada."""
        acao = self._por_id.get(action_id)
        if acao is None or not acao.visivel_para(principal):
            raise AcaoDesconhecida(action_id)
        return acao

    def como_manifesto(self) -> list[dict[str, Any]]:
        return [a.como_manifesto() for a in self.acoes]

    def como_catalogo_servido(self, principal: Principal) -> list[dict[str, Any]]:
        return [a.como_catalogo_servido() for a in self.compor(principal)]

    def como_ferramentas(self, principal: Principal) -> list[dict[str, Any]]:
        return [a.como_ferramenta() for a in self.compor(principal)]

    def rotear(self, texto: str, principal: Principal) -> AcaoDoCatalogo | None:
        """Roteamento **determinístico** por `intent_keywords` — o estágio inicial do APH-8.2.

        Não é classificação por modelo, e a diferença é o ADR 0007: nenhum provedor de
        inteligência artificial é chamado dentro deste produto. O que existe aqui é uma
        busca por palavra declarada no catálogo, sobre o inventário **já filtrado por
        permissão** — o que o principal não pode nem entra no conjunto de candidatos.

        Empate resolvido por número de palavras casadas e, depois, pela ordem do catálogo:
        roteamento tem de ser reprodutível, senão o mesmo pedido responde diferente em dias
        diferentes e ninguém consegue depurar.
        """
        limpo = texto.lower()
        melhor: tuple[int, int, AcaoDoCatalogo] | None = None
        for posicao, acao in enumerate(self.compor(principal)):
            casadas = sum(1 for palavra in acao.intent_keywords if palavra.lower() in limpo)
            if casadas and (melhor is None or casadas > melhor[0]):
                melhor = (casadas, -posicao, acao)
        return melhor[2] if melhor else None


ACOES_TOC: tuple[AcaoDoCatalogo, ...] = (
    AcaoDoCatalogo(
        action_id='toc.listar_projetos',
        title='Listar projetos',
        description='Lista os projetos TOC do tenant do principal, com ferramenta e ultima atualizacao.',
        risk='read',
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'properties': {   'ferramenta': {   'type': 'string',
                                                'description': 'Filtro opcional por '
                                                               'ferramenta (ex.: ara)'}}},
        ui_route='/toc/projetos',
        intent_keywords=('projetos', 'listar', 'arvores'),
    ),
    AcaoDoCatalogo(
        action_id='toc.sugerir_udes',
        title='Sugerir Efeitos Indesejaveis',
        description='A partir de uma narrativa, sugere candidatos a Efeito Indesejavel (UDE) para a Arvore da Realidade Atual. Nao grava nada: o resultado e rascunho ate a Facilitadora registrar.',
        risk='read',
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id', 'narrativa'],
            'properties': {   'projeto_id': {'type': 'string'},
                              'narrativa': {'type': 'string', 'maxLength': 8000}}},
        ui_route='/toc/ara',
        intent_keywords=('ude', 'efeito indesejavel', 'sugerir'),
    ),
    AcaoDoCatalogo(
        action_id='toc.analisar_suficiencia',
        title='Analisar suficiencia causal',
        description='Analisa a arvore atual e aponta relacoes causais com suficiencia fragil. Somente leitura.',
        risk='read',
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id'],
            'properties': {'projeto_id': {'type': 'string'}}},
        ui_route='/toc/ara',
        intent_keywords=('suficiencia', 'analisar', 'causa'),
    ),
    AcaoDoCatalogo(
        action_id='toc.criar_nos',
        title='Criar nos na arvore',
        description='Cria um ou N nos (lote: uma proposta com N alvos, APH-5.9) no projeto indicado. Mutadora: nasce proposta e atravessa a FSM.',
        risk='confirm',
        reversible=True,
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id', 'nos'],
            'properties': {   'projeto_id': {'type': 'string'},
                              'nos': {   'type': 'array',
                                         'minItems': 1,
                                         'maxItems': 50,
                                         'items': {   'type': 'object',
                                                      'additionalProperties': False,
                                                      'required': ['titulo', 'tipo'],
                                                      'properties': {   'titulo': {   'type': 'string',
                                                                                      'maxLength': 300},
                                                                        'tipo': {   'type': 'string',
                                                                                    'enum': [   'ude',
                                                                                                'causa',
                                                                                                'causa_raiz']}}}}}},
        ui_route='/toc/ara',
        intent_keywords=('criar', 'adicionar', 'no', 'ude'),
        batch_atomicity='per_item',
        campo_de_alvos='nos',
    ),
    AcaoDoCatalogo(
        action_id='toc.criar_arestas',
        title='Ligar causas e efeitos',
        description='Cria uma ou N arestas causais (lote: uma proposta com N alvos) entre nos existentes. Mutadora: nasce proposta.',
        risk='confirm',
        reversible=True,
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id', 'arestas'],
            'properties': {   'projeto_id': {'type': 'string'},
                              'arestas': {   'type': 'array',
                                             'minItems': 1,
                                             'maxItems': 50,
                                             'items': {   'type': 'object',
                                                          'additionalProperties': False,
                                                          'required': [   'origem_id',
                                                                          'destino_id'],
                                                          'properties': {   'origem_id': {   'type': 'string'},
                                                                            'destino_id': {   'type': 'string'}}}}}},
        ui_route='/toc/ara',
        intent_keywords=('ligar', 'aresta', 'causa', 'efeito'),
        batch_atomicity='per_item',
        campo_de_alvos='arestas',
    ),
    AcaoDoCatalogo(
        action_id='toc.atualizar_no',
        title='Atualizar um no',
        description='Altera titulo ou tipo de um no existente. Mutadora: nasce proposta.',
        risk='confirm',
        reversible=True,
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id', 'no_id'],
            'properties': {   'projeto_id': {'type': 'string'},
                              'no_id': {'type': 'string'},
                              'titulo': {'type': 'string', 'maxLength': 300},
                              'tipo': {   'type': 'string',
                                          'enum': ['ude', 'causa', 'causa_raiz']}}},
        ui_route='/toc/ara',
        intent_keywords=('atualizar', 'renomear', 'editar'),
    ),
    AcaoDoCatalogo(
        action_id='toc.excluir_nos',
        title='Excluir nos (exclusao suave)',
        description='Move um ou N nos (lote) e suas arestas incidentes para a lixeira. Reversivel pela restauracao; a exclusao definitiva nao esta no catalogo.',
        risk='confirm',
        reversible=True,
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id', 'no_ids'],
            'properties': {   'projeto_id': {'type': 'string'},
                              'no_ids': {   'type': 'array',
                                            'minItems': 1,
                                            'maxItems': 50,
                                            'items': {'type': 'string'}}}},
        ui_route='/toc/ara',
        intent_keywords=('excluir', 'remover', 'lixeira'),
        batch_atomicity='per_item',
        campo_de_alvos='no_ids',
    ),
    AcaoDoCatalogo(
        action_id='toc.exportar_projeto',
        title='Exportar projeto',
        description='Gera a exportacao canonica (JSON versionado e deterministico) do projeto. Somente leitura.',
        risk='read',
        input_schema={   'type': 'object',
            'additionalProperties': False,
            'required': ['projeto_id'],
            'properties': {'projeto_id': {'type': 'string'}}},
        ui_route='/toc/projetos',
        intent_keywords=('exportar', 'backup', 'json'),
    ),
    # -- M3 · Nuvem de Conflito (spec 007, INT-02..INT-04) ------------------------------
    #
    # As três são `confirm` porque as três **escrevem** na nuvem depois do gate. O que o
    # `input_schema` da primeira carrega merece ser lido: ele embute o esquema versionado
    # do ResultadoDeGeracao, e é isso que faz a validação do RF-22 acontecer **antes de a
    # proposta existir** — não há caminho em que conteúdo de modelo entre sem passar por
    # ele. A narrativa viaja junto, opcional, só para a auditoria saber de onde a proposta
    # veio; a nuvem é preenchida a partir do `resultado`, nunca do texto.
    AcaoDoCatalogo(
        action_id="toc.generate_conflict_cloud",
        title="Preencher a nuvem a partir de uma narrativa",
        description=(
            "Aplica na Nuvem de Conflito um resultado de geracao estruturado e validado "
            "por esquema versionado: 5 entidades, racional, premissas por aresta e "
            "injecoes por premissa. Mutadora: nasce proposta e espera o gate humano; "
            "recusar deixa o projeto intacto."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "resultado"],
            "properties": {
                "projeto_id": {"type": "string"},
                "narrativa": {"type": "string", "maxLength": 8000},
                "resultado": ESQUEMA_DO_RESULTADO,
            },
        },
        ui_route="/toc/nc",
        intent_keywords=("nuvem", "conflito", "dilema", "gerar"),
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_assumptions",
        title="Sugerir uma premissa para uma aresta",
        description=(
            "Registra UMA premissa sugerida numa das 7 arestas da nuvem. Granular de "
            "proposito: cada sugestao e uma proposta individual, para aceitar duas e "
            "recusar uma sem regenerar o que o grupo ja validou."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "aresta", "texto"],
            "properties": {
                "projeto_id": {"type": "string"},
                "aresta": {"type": "string", "enum": [c.value for c in ChaveDaAresta]},
                "texto": {"type": "string", "minLength": 1, "maxLength": 1000},
            },
        },
        ui_route="/toc/nc/aresta",
        intent_keywords=("premissa", "sugerir", "aresta"),
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_injections",
        title="Sugerir uma injecao para uma premissa",
        description=(
            "Registra UMA injecao ligada a premissa nomeada, com separacao TRIZ quando "
            "couber. Injecao sem premissa nao existe: a premissa e campo obrigatorio do "
            "contrato, nao convencao."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "premissa_id", "texto"],
            "properties": {
                "projeto_id": {"type": "string"},
                "premissa_id": {"type": "string"},
                "texto": {"type": "string", "minLength": 1, "maxLength": 1000},
                "separacao": {
                    "type": "string",
                    "enum": [s.value for s in SeparacaoTRIZ],
                },
            },
        },
        ui_route="/toc/nc/aresta",
        intent_keywords=("injecao", "solucao", "triz", "sugerir"),
    ),
    # -- M4 · Árvores de Futuro e Implementação (spec 008, INT-05..INT-08) --------------
    #
    # As quatro são `confirm` porque as quatro **escrevem** depois do gate. Cada uma
    # registra UM elemento de propósito (RF-43: "cada sugestão mutadora nascendo
    # `action_proposal` individual"), para aceitar duas e recusar uma sem regenerar o que o
    # grupo já validou — a mesma granularidade que o M3 escolheu para as premissas.
    #
    # E o que **não** existe aqui é decisão de round: **não há ação de ramo negativo**
    # (RF-10). A marcação do efeito colateral é manual nesta v1, e a prova é negativa: o
    # `grep` da DoD 8 (spec 008) procura os dois identificadores que uma ação assim teria
    # e devolve zero — inclusive aqui, e por isso este comentário não os escreve.
    AcaoDoCatalogo(
        action_id="toc.suggest_future_effects",
        title="Sugerir um efeito futuro para a Arvore da Realidade Futura",
        description=(
            "Registra UM efeito futuro ligado a uma injecao da Arvore da Realidade "
            "Futura. O contexto de dominio ja computado (verificacao estrutural) "
            "acompanha a entrada; o modelo nunca decide o que a funcao pura ja decidiu."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "injecao_id", "texto"],
            "properties": {
                "projeto_id": {"type": "string"},
                "injecao_id": {"type": "string"},
                "texto": {"type": "string", "minLength": 1, "maxLength": 300},
            },
        },
        ui_route="/toc/arf",
        intent_keywords=("efeito futuro", "realidade futura", "sugerir", "arf"),
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_obstacles",
        title="Sugerir um obstaculo para a Arvore de Pre-Requisitos",
        description=(
            "Registra UM obstaculo na Arvore de Pre-Requisitos. Obstaculo e condicao que "
            "existe hoje, nunca tarefa nem previsao: a verbalizacao avaliada avisa quem "
            "escrever diferente, e o aviso nao veta."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "texto"],
            "properties": {
                "projeto_id": {"type": "string"},
                "texto": {"type": "string", "minLength": 1, "maxLength": 300},
            },
        },
        ui_route="/toc/apr",
        intent_keywords=("obstaculo", "impedimento", "sugerir", "apr"),
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_intermediate_objectives",
        title="Sugerir um objetivo intermediario que supera um obstaculo",
        description=(
            "Registra UM objetivo intermediario e o pareia com o obstaculo indicado. O "
            "julgamento do teste de validade permanece humano (RN-07) e NAO vem "
            "preenchido por esta acao."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "obstaculo_id", "texto"],
            "properties": {
                "projeto_id": {"type": "string"},
                "obstaculo_id": {"type": "string"},
                "texto": {"type": "string", "minLength": 1, "maxLength": 300},
            },
        },
        ui_route="/toc/apr",
        intent_keywords=("objetivo intermediario", "superar", "sugerir"),
    ),
    AcaoDoCatalogo(
        action_id="toc.suggest_transition_steps",
        title="Sugerir um passo para a Arvore de Transicao",
        description=(
            "Registra UM passo com a tripla acao, necessidade e resultado esperado. "
            "Proposta sem os tres campos e recusada pelo input_schema ANTES de virar "
            "action_proposal: passo sem necessidade explicita degrada a arvore a lista de "
            "tarefas, e o contrato nao deixa isso acontecer."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": ["projeto_id", "acao", "necessidade", "resultado_esperado"],
            "properties": {
                "projeto_id": {"type": "string"},
                "acao": {"type": "string", "minLength": 1, "maxLength": 300},
                "necessidade": {"type": "string", "minLength": 1, "maxLength": 4000},
                "resultado_esperado": {"type": "string", "minLength": 1, "maxLength": 4000},
            },
        },
        ui_route="/toc/at",
        intent_keywords=("passo", "transicao", "sugerir", "at"),
    ),
    # -- M6 · Focalização (spec 009, INT-05) --------------------------------------------
    #
    # UMA ação, e ela é a única assistência do módulo (RF-19). Granular por candidata,
    # como as do M3 e do M4: aceitar uma restrição e recusar outra sem regenerar nada.
    #
    # `confirm` porque ela **escreve** depois do gate: aceitar registra a restrição do
    # ciclo aberto com a referência de origem (INT-02). E é exatamente esta ação que o
    # corte de apetite do round 009 solta primeiro — a jornada guiada é completa por
    # construção sem ela (RF-20), e o `input_schema` abaixo é o contrato que ela cumpre
    # quando existe.
    AcaoDoCatalogo(
        action_id="toc.suggest_constraint",
        title="Sugerir a restricao a partir da Arvore da Realidade Atual",
        description=(
            "Registra a restricao do ciclo aberto de uma analise de focalizacao, com a "
            "referencia de origem apontando para o no de causa raiz da Arvore da "
            "Realidade Atual vinculada ao passo identificar. Mutadora: nasce proposta e "
            "espera o gate humano; recusar deixa a analise byte a byte intacta."
        ),
        risk="confirm",
        reversible=True,
        input_schema={
            "type": "object",
            "additionalProperties": False,
            "required": [
                "projeto_id",
                "ara_projeto_id",
                "no_id",
                "descricao",
                "tipo",
                "justificativa",
            ],
            "properties": {
                "projeto_id": {"type": "string"},
                "ara_projeto_id": {"type": "string"},
                "no_id": {"type": "string"},
                "descricao": {"type": "string", "minLength": 1, "maxLength": 300},
                # O enum fechado da L-01, aqui como contrato: uma restricao de tipo
                # inventado e recusada pelo `input_schema` ANTES de virar action_proposal.
                "tipo": {
                    "type": "string",
                    "enum": ["fisica", "politica", "de_mercado"],
                },
                "justificativa": {"type": "string", "minLength": 1, "maxLength": 4000},
                "autor": {"type": "string", "maxLength": 200},
            },
        },
        ui_route="/toc/focalizacao",
        intent_keywords=("restricao", "gargalo", "focalizacao", "sugerir"),
    ),
)

# A instância que o serviço usa. É construída no import: um catálogo torto derruba o
# arranque, e não a primeira proposta.
CATALOGO_TOC = Catalogo(ACOES_TOC)
