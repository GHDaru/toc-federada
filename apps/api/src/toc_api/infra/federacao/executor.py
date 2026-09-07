"""O executor do catálogo `toc.*` — onde a ação governada toca o domínio de verdade.

Siglas, uma vez: **APH** — Aplicação ↔ Harness · **ARA** — Árvore da Realidade Atual ·
**UDE** — Efeito Indesejável · **UUID** — *Universally Unique Identifier* · **JSON** —
*JavaScript Object Notation*.

Ele implementa a porta `ExecutorDeAcao` e é o **único** lugar onde `action_id` vira chamada
de caso de uso. A tabela `_DESPACHO` é a superfície executável inteira: um `action_id` que
não estiver nela não executa, e não há caminho alternativo — que é o APH-4.1 ("o catálogo é
a única superfície executável") em forma de código.

Mora em `infra/` e não em `aplicacao/` por um motivo de camada: ele **compõe** casos de uso
(que são da aplicação) e conhece repositórios concretos. A camada de aplicação, por sua vez,
só conhece a porta — e é o `import-linter` que garante que continue assim.

**Falha de alvo é dado, não exceção que sobe.** Cada alvo devolve `(status, mensagem)`; a
falha de um não derruba o lote, porque o desfecho por alvo (APH-5.9(b)) existe justamente
para dizer que sete executaram e um não.
"""
from __future__ import annotations

from typing import Any, Callable, Mapping
from uuid import UUID

from ...aplicacao.ara import (
    AdicionarEfeito,
    AnalisarArvore,
    LigarNaARA,
    MarcarUde,
    ReformularUde,
    ValidarTextoDeUde,
)
from ...aplicacao.arvores import (
    AdicionarNoDaAPR,
    AdicionarNoDaARF,
    LigarNaARF,
    ParearObstaculo,
    RegistrarPasso,
)
from ...aplicacao.focalizacao import RegistrarRestricao
from ...aplicacao.nuvem import (
    AplicarGeracaoDeNuvem,
    RegistrarInjecao,
    RegistrarPremissa,
)
from ...aplicacao.grafo import AdicionarNo, EditarNo, ExcluirNo, LigarNos
from ...aplicacao.projetos import ListarProjetos
from ...dominio.erros import ErroDeDominio
from ...dominio.eventos import ORIGEM_DE_GERACAO
from ...dominio.geracao import ResultadoDeGeracao
from ...dominio.federacao.catalogo import CATALOGO_TOC, Catalogo
from ...dominio.federacao.principal import Principal
from ...dominio.apr import PapelNaAPR
from ...dominio.focalizacao import ReferenciaDeOrigemDaRestricao
from ...dominio.arf import PapelNaARF
from ...dominio.nuvem import ChaveDaAresta, SeparacaoTRIZ
from ...dominio.portas import (
    MotorDeGeracaoDeNuvem,
    Rastreador,
    Relogio,
    RepositorioDeAPR,
    RepositorioDeARA,
    RepositorioDeARF,
    RepositorioDeAT,
    RepositorioDeFocalizacao,
    RepositorioDeNuvens,
    RepositorioDeProjetos,
)
from ...dominio.valores import PosicaoNoCanvas

# Passo do canvas para nós criados em lote. O canvas real é do ciclo de interface; aqui a
# posição existe para o nó nascer válido, e nascer em diagonal é melhor que nascer todo
# empilhado na origem.
PASSO_DO_CANVAS = 140.0


class ExecutorDoCatalogo:
    """Implementa `ExecutorDeAcao` ligando o catálogo aos casos de uso do M1 e do M2."""

    def __init__(
        self,
        *,
        rastreador: Rastreador,
        projetos: RepositorioDeProjetos,
        aras: RepositorioDeARA | None,
        relogio: Relogio,
        nuvens: RepositorioDeNuvens | None = None,
        motor_de_geracao: MotorDeGeracaoDeNuvem | None = None,
        arvores: RepositorioDeARF | RepositorioDeAPR | RepositorioDeAT | None = None,
        focalizacoes: RepositorioDeFocalizacao | None = None,
        catalogo: Catalogo = CATALOGO_TOC,
    ) -> None:
        # O catálogo entra por injeção com o padrão real porque o executor precisa saber
        # de QUAL ferramenta é cada `action_id` — é o que permite recusar cedo, com a
        # mensagem que diz onde está a ação certa, em vez de deixar a invariante do
        # domínio recusar com um texto que a fundação não sabe corrigir.
        self._catalogo = catalogo
        self._listar = ListarProjetos(rastreador=rastreador, repositorio=projetos, relogio=relogio)
        self._adicionar = AdicionarNo(rastreador=rastreador, repositorio=projetos, relogio=relogio)
        self._editar = EditarNo(rastreador=rastreador, repositorio=projetos, relogio=relogio)
        self._excluir = ExcluirNo(rastreador=rastreador, repositorio=projetos, relogio=relogio)
        self._ligar = LigarNos(rastreador=rastreador, repositorio=projetos, relogio=relogio)
        self._validar_ude = ValidarTextoDeUde(rastreador=rastreador)
        self._analisar = (
            AnalisarArvore(rastreador=rastreador, repositorio=aras, relogio=relogio)
            if aras is not None
            else None
        )
        # M2 — as quatro ações mutadoras da Árvore da Realidade Atual (spec 005,
        # RF-32..RF-34). Passam pelos casos de uso DA RAIZ (`ProjetoARA`), nunca pelos
        # genéricos do M1: é essa a diferença entre a assistência funcionar na ferramenta
        # e mutilá-la — ou, depois da guarda da raiz, falhar para sempre nela.
        da_ara = dict(rastreador=rastreador, repositorio=aras, relogio=relogio)
        self._adicionar_efeito = AdicionarEfeito(**da_ara) if aras is not None else None
        self._marcar_ude = MarcarUde(**da_ara) if aras is not None else None
        self._ligar_na_ara = LigarNaARA(**da_ara) if aras is not None else None
        self._reformular_ude = ReformularUde(**da_ara) if aras is not None else None
        # M3 — Nuvem de Conflito. Os três casos de uso são montados só quando há
        # repositório de nuvens composto; sem ele, o `action_id` cai no ramo que devolve
        # `failed` com o motivo, e não num `AttributeError` disfarçado de erro de sistema.
        self._aplicar_geracao = (
            AplicarGeracaoDeNuvem(rastreador=rastreador, repositorio=nuvens, relogio=relogio)
            if nuvens is not None
            else None
        )
        self._registrar_premissa = (
            RegistrarPremissa(rastreador=rastreador, repositorio=nuvens, relogio=relogio)
            if nuvens is not None
            else None
        )
        self._registrar_injecao = (
            RegistrarInjecao(rastreador=rastreador, repositorio=nuvens, relogio=relogio)
            if nuvens is not None
            else None
        )
        # M4 — as quatro ações do módulo (spec 008, INT-05..INT-08). Montadas só quando há
        # repositório das árvores composto; sem ele, o `action_id` cai no ramo que devolve
        # `failed` com o motivo, e não num `AttributeError` disfarçado de erro de sistema.
        self._efeito_futuro = (
            AdicionarNoDaARF(rastreador=rastreador, repositorio=arvores, relogio=relogio)
            if arvores is not None
            else None
        )
        self._ligar_na_arf = (
            LigarNaARF(rastreador=rastreador, repositorio=arvores, relogio=relogio)
            if arvores is not None
            else None
        )
        self._no_da_apr = (
            AdicionarNoDaAPR(rastreador=rastreador, repositorio=arvores, relogio=relogio)
            if arvores is not None
            else None
        )
        self._parear = (
            ParearObstaculo(rastreador=rastreador, repositorio=arvores, relogio=relogio)
            if arvores is not None
            else None
        )
        self._registrar_passo = (
            RegistrarPasso(rastreador=rastreador, repositorio=arvores, relogio=relogio)
            if arvores is not None
            else None
        )
        # M6 — a única ação assistida do módulo (spec 009, RF-19). Montada só quando há
        # repositório de focalização composto; sem ele, o `action_id` cai no ramo que
        # devolve `failed` com o motivo, e não num `AttributeError` disfarçado de erro de
        # sistema. É a RF-20 do lado do servidor: a jornada guiada funciona sem isto.
        self._registrar_restricao = (
            RegistrarRestricao(
                rastreador=rastreador, repositorio=focalizacoes, relogio=relogio
            )
            if focalizacoes is not None
            else None
        )
        self._motor_de_geracao = motor_de_geracao
        self._projetos = projetos
        self._despacho: dict[str, Callable[..., tuple[str, str]]] = {
            "toc.listar_projetos": self._acao_listar_projetos,
            "toc.sugerir_udes": self._acao_sugerir_udes,
            "toc.analisar_suficiencia": self._acao_analisar_suficiencia,
            "toc.exportar_projeto": self._acao_exportar_projeto,
            # M2 — a ARA, pela raiz dela (spec 005, RF-32..RF-34).
            "toc.suggest_udes": self._acao_registrar_ude,
            "toc.suggest_causes": self._acao_sugerir_causa,
            "toc.suggest_relations": self._acao_sugerir_relacao,
            "toc.suggest_reformulation": self._acao_reformular_ude,
            # M1 — o projeto GENÉRICO, onde o próprio `Projeto` é a raiz do agregado.
            "toc.criar_nos": self._acao_criar_no,
            "toc.criar_arestas": self._acao_criar_aresta,
            "toc.atualizar_no": self._acao_atualizar_no,
            "toc.excluir_nos": self._acao_excluir_no,
            "toc.generate_conflict_cloud": self._acao_gerar_nuvem,
            "toc.suggest_assumptions": self._acao_sugerir_premissa,
            "toc.suggest_injections": self._acao_sugerir_injecao,
            # M4 — spec 008. Uma ação por elemento: aceitar duas e recusar uma sem
            # regenerar o que o grupo já validou (RF-43).
            "toc.suggest_future_effects": self._acao_sugerir_efeito_futuro,
            "toc.suggest_obstacles": self._acao_sugerir_obstaculo,
            "toc.suggest_intermediate_objectives": self._acao_sugerir_objetivo_intermediario,
            "toc.suggest_transition_steps": self._acao_sugerir_passo,
            # M6 — spec 009. Uma proposta por candidata: aceitar uma restrição e recusar
            # outra sem regenerar o que o grupo já olhou (RF-19).
            "toc.suggest_constraint": self._acao_sugerir_restricao,
        }
        self.saidas: list[Any] = []

    # -- porta ---------------------------------------------------------------------
    def executar(
        self, *, action_id: str, args: Mapping[str, Any], principal: Principal
    ) -> tuple[str, str]:
        acao = self._despacho.get(action_id)
        if acao is None:
            # Não há caminho alternativo: um `action_id` fora da tabela não executa.
            return ("failed", f"ação {action_id!r} sem execução declarada no despacho")
        try:
            desencontro = self._ferramenta_errada(action_id, args, principal)
            if desencontro is not None:
                return ("failed", desencontro)
            return acao(dict(args), principal)
        except ErroDeDominio as erro:
            # A invariante do domínio recusou. É desfecho do alvo, não exceção de sistema:
            # o `outcomes` existe para carregar exatamente isto.
            return ("failed", str(erro))
        except (ValueError, TypeError, KeyError) as erro:
            return ("failed", f"argumento inválido para {action_id}: {erro}")

    def _ferramenta_errada(
        self, action_id: str, args: Mapping[str, Any], principal: Principal
    ) -> str | None:
        """A ação é de outra ferramenta? Então recuse AQUI, dizendo onde está a certa.

        **Isto não é o que protege o agregado.** Quem protege é `Projeto._exigir_raiz`,
        no domínio, e o `scripts/check-raiz-do-agregado.sh` é o portão dele: mesmo que
        esta função fosse apagada, `toc.criar_nos` continuaria recusado numa ARA. O que
        ela acrescenta é a **mensagem acionável** — sem ela, a fundação recebia "o grafo
        de um projeto da ferramenta 'ara' só muda pela raiz" e não tinha como saber que a
        ação certa era `toc.suggest_udes`. Recusa que não ensina a acertar transforma
        assistência governada em beco sem saída, que foi exatamente o achado.

        Só age quando há o que comparar: ação com `ferramenta` declarada, `projeto_id`
        nos argumentos e projeto encontrado para este inquilino. Projeto inexistente
        segue para o caso de uso, que já sabe recusar (`NaoEncontrado`) — duplicar a
        recusa aqui só mudaria a mensagem de um erro que já é correto.
        """
        try:
            esperada = self._catalogo.acao(action_id).ferramenta
        except ErroDeDominio:  # pragma: no cover - o despacho já garantiu que existe
            return None
        if esperada is None or "projeto_id" not in args:
            return None
        try:
            projeto = self._projetos.obter(
                principal.dono().inquilino_id, UUID(str(args["projeto_id"]))
            )
        except (ValueError, TypeError):
            return None
        if projeto is None or projeto.ferramenta == esperada:
            return None
        alternativas = sorted(
            a.action_id
            for a in self._catalogo.compor(principal)
            if a.ferramenta == projeto.ferramenta and a.risk == "confirm"
        )
        onde = (
            f"as ações desta ferramenta são: {', '.join(alternativas)}"
            if alternativas
            else "esta ferramenta não tem ação mutadora no catálogo"
        )
        return (
            f"ação {action_id!r} é da ferramenta {esperada!r}; o projeto "
            f"{args['projeto_id']} é da ferramenta {projeto.ferramenta!r} — {onde}"
        )

    # -- ações de leitura ----------------------------------------------------------
    def _acao_listar_projetos(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        projetos = self._listar.rodar(dono=principal.dono())
        ferramenta = args.get("ferramenta")
        if ferramenta:
            projetos = [p for p in projetos if p.ferramenta == ferramenta]
        self.saidas.append([{"id": str(p.id), "nome": p.nome} for p in projetos])
        return ("executed", f"{len(projetos)} projeto(s)")

    def _acao_sugerir_udes(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """Sugestão é **rascunho**: não grava nada (RN-03).

        A separação em frases é deliberadamente ingênua e determinística — quem julga o
        texto é `validar_formalmente`, que é regra de domínio pura. Nenhum provedor de
        modelo é chamado aqui (ADR 0007): quem fala com modelo é a fundação.
        """
        narrativa = str(args.get("narrativa") or "")
        candidatos = [t.strip() for t in narrativa.replace("\n", ".").split(".") if t.strip()]
        dono = principal.dono()
        sugestoes = []
        for frase in candidatos[:20]:
            validacao = self._validar_ude.rodar(dono=dono, texto=frase)
            sugestoes.append(
                {
                    "texto": frase,
                    "aprovado": not validacao.reprovacoes,
                    "reprovacoes": [r.criterio for r in validacao.reprovacoes],
                }
            )
        self.saidas.append(sugestoes)
        aprovados = sum(1 for s in sugestoes if s["aprovado"])
        return ("executed", f"{aprovados} candidato(s) de {len(sugestoes)} frase(s)")

    def _acao_analisar_suficiencia(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        if self._analisar is None:
            return ("failed", "análise indisponível: repositório de ARA não composto")
        relatorio = self._analisar.rodar(
            dono=principal.dono(), projeto_id=UUID(str(args["projeto_id"]))
        )
        self.saidas.append(relatorio)
        return ("executed", "análise estrutural concluída")

    def _acao_exportar_projeto(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        projeto = self._projetos.obter(principal.dono().inquilino_id, UUID(str(args["projeto_id"])))
        if projeto is None:
            return ("failed", "projeto inexistente para este inquilino")
        self.saidas.append(
            {
                "projeto_id": str(projeto.id),
                "nome": projeto.nome,
                "nos": len(projeto.nos),
                "arestas": len(projeto.arestas),
            }
        )
        return ("executed", f"{len(projeto.nos)} nó(s) e {len(projeto.arestas)} aresta(s)")

    # -- M2: as quatro ações da ARA, PELA RAIZ (spec 005, RF-32..RF-34) ------------
    #
    # Nenhuma delas toca `AdicionarNo`, `LigarNos`, `EditarNo` ou `ExcluirNo` — os casos
    # de uso genéricos do M1. Elas chamam `AdicionarEfeito`, `MarcarUde`, `LigarNaARA` e
    # `ReformularUde`, que entram pelo `ProjetoARA`. É por isso que a ficha do Efeito
    # Indesejável nasce, a validação formal roda e o exame do elo nasce `nao_examinado`:
    # as invariantes da ferramenta moram na raiz, e quem passa por fora dela não as tem.
    #
    # O `proposta_id` viaja até o caso de uso e entra no span (RF-32): a mutação vinda de
    # modelo continua distinguível de edição humana um mês depois.

    def _acao_registrar_ude(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """RF-32/INT-02: o Efeito Indesejável nasce nó **e** ficha, num ato só."""
        if self._adicionar_efeito is None or self._marcar_ude is None:
            return ("failed", "registro indisponível: repositório de ARA não composto")
        indice = int(args.get("__indice__", 0))
        item = args["udes"][indice]
        proposta = self._proposta_de(args)
        projeto_id = UUID(str(args["projeto_id"]))
        no = self._adicionar_efeito.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            titulo=str(item["texto"]),
            descricao=str(item.get("descricao") or ""),
            posicao=PosicaoNoCanvas(PASSO_DO_CANVAS * indice, PASSO_DO_CANVAS * (indice % 3)),
            proposta_id=proposta,
        )
        # Marcar dispara a validação formal dos critérios — função pura de domínio. É o
        # ponto do RF-32: o modelo sugere o texto, quem dá o veredito decidível é a regra.
        self._marcar_ude.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            no_id=no.id,
            proposta_id=proposta,
        )
        return ("executed", str(no.id))

    def _acao_sugerir_causa(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """INT-03: a causa nasce nó **e** elo — a sugestão nunca fica solta."""
        if self._adicionar_efeito is None or self._ligar_na_ara is None:
            return ("failed", "sugestão indisponível: repositório de ARA não composto")
        indice = int(args.get("__indice__", 0))
        item = args["causas"][indice]
        proposta = self._proposta_de(args)
        projeto_id = UUID(str(args["projeto_id"]))
        # O nó alvo é conferido ANTES de criar a causa. Sem isto, um `no_id` inexistente
        # deixaria a causa gravada e o elo não — meia mutação, com um nó solto na árvore
        # e um desfecho `failed` que não diz que algo ficou. A conferência é de borda; a
        # invariante que recusa o elo continua sendo a do domínio.
        alvo = UUID(str(args["no_id"]))
        projeto = self._projetos.obter(principal.dono().inquilino_id, projeto_id)
        if projeto is not None and not projeto.tem_no(alvo):
            return ("failed", f"nó alvo {alvo} não existe neste projeto — nada foi criado")
        no = self._adicionar_efeito.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            titulo=str(item["texto"]),
            posicao=PosicaoNoCanvas(PASSO_DO_CANVAS * indice, -PASSO_DO_CANVAS),
            proposta_id=proposta,
        )
        self._ligar_na_ara.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            origem_id=no.id,
            destino_id=alvo,
            rotulo=str(item.get("rotulo") or ""),
            proposta_id=proposta,
        )
        return ("executed", str(no.id))

    def _acao_sugerir_relacao(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """INT-04: o elo entre nós que já existem. Nasce `nao_examinado` (RF-22)."""
        if self._ligar_na_ara is None:
            return ("failed", "sugestão indisponível: repositório de ARA não composto")
        indice = int(args.get("__indice__", 0))
        item = args["relacoes"][indice]
        aresta = self._ligar_na_ara.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            origem_id=UUID(str(item["origem_id"])),
            destino_id=UUID(str(item["destino_id"])),
            rotulo=str(item.get("rotulo") or ""),
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(aresta.id))

    def _acao_reformular_ude(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """RF-34: aplicar a reformulação REEXECUTA a validação formal (RF-10)."""
        if self._reformular_ude is None:
            return ("failed", "reformulação indisponível: repositório de ARA não composto")
        no = self._reformular_ude.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            no_id=UUID(str(args["no_id"])),
            texto=str(args["texto"]),
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(no.id))

    # -- ações mutadoras do projeto GENÉRICO (M1) ----------------------------------
    #
    # Elas servem o `Projeto` sem ferramenta acima, onde ele **é** a raiz do agregado.
    # Apontá-las para um projeto de ferramenta é o defeito que o ADR 0015 nomeia: antes
    # da guarda da raiz, mutilava; depois dela, falha para sempre. O `ferramenta` do
    # catálogo diz `generico` e `_ferramenta_errada` recusa cedo, com a ação certa no
    # texto — mas quem impede a escrita continua sendo a invariante do domínio.
    def _acao_criar_no(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        indice = int(args.get("__indice__", 0))
        item = args["nos"][indice]
        no = self._adicionar.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            titulo=item["titulo"],
            tipo=item.get("tipo", "generico"),
            posicao=PosicaoNoCanvas(PASSO_DO_CANVAS * indice, PASSO_DO_CANVAS * (indice % 3)),
        )
        return ("executed", str(no.id))

    def _acao_criar_aresta(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        indice = int(args.get("__indice__", 0))
        item = args["arestas"][indice]
        aresta = self._ligar.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            origem_id=UUID(str(item["origem_id"])),
            destino_id=UUID(str(item["destino_id"])),
        )
        return ("executed", str(aresta.id))

    def _acao_atualizar_no(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        no = self._editar.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            no_id=UUID(str(args["no_id"])),
            titulo=args.get("titulo"),
        )
        return ("executed", str(no.id))

    def _acao_excluir_no(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        indice = int(args.get("__indice__", 0))
        no_id = args["no_ids"][indice]
        removidas = self._excluir.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            no_id=UUID(str(no_id)),
        )
        return ("executed", f"{len(removidas)} aresta(s) removida(s) junto")

    # -- M3: as três ações da Nuvem de Conflito (só chegam aqui depois do gate) --------
    #
    # `__proposta__` é o identificador da proposta que autorizou a escrita, colocado nos
    # `args` pela camada de governança. Ele não é decoração: a RF-25 da spec 007 exige que
    # os eventos resultantes declarem a origem `geracao` **com a proposta**, e sem ele a
    # mutação seria indistinguível de edição humana um mês depois.

    def _proposta_de(self, args: dict[str, Any]) -> str:
        proposta = str(args.get("__proposta__") or "").strip()
        if not proposta:
            # Falha fechada: escrever conteúdo de modelo sem saber qual proposta o
            # autorizou é exatamente o que a RN-05 fecha.
            raise ValueError(
                "aplicação de conteúdo assistido sem identificador de proposta"
            )
        return proposta

    def _acao_gerar_nuvem(self, args: dict[str, Any], principal: Principal) -> tuple[str, str]:
        """RF-23/RF-25: aplica o resultado JÁ validado pelo `input_schema` da ação.

        A validação acontece duas vezes de propósito — no `input_schema`, antes de a
        proposta nascer (RF-22), e aqui, ao tipar o resultado. Uma engana-se por descuido;
        duas exigem intenção.
        """
        if self._aplicar_geracao is None:
            return ("failed", "geração indisponível: repositório de nuvens não composto")
        resultado = ResultadoDeGeracao.de_dicionario(args["resultado"])
        evento = self._aplicar_geracao.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            resultado=resultado,
            proposta_id=self._proposta_de(args),
        )
        return (
            "executed",
            f"{evento.entidades} entidade(s), {evento.premissas} premissa(s) e "
            f"{evento.injecoes} injeção(ões) aplicadas",
        )

    def _acao_sugerir_premissa(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        if self._registrar_premissa is None:
            return ("failed", "sugestão indisponível: repositório de nuvens não composto")
        premissa = self._registrar_premissa.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            chave=ChaveDaAresta(str(args["aresta"])),
            texto=str(args["texto"]),
            origem=ORIGEM_DE_GERACAO,
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(premissa.id))

    def _acao_sugerir_injecao(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        if self._registrar_injecao is None:
            return ("failed", "sugestão indisponível: repositório de nuvens não composto")
        separacao = args.get("separacao")
        injecao = self._registrar_injecao.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            premissa_id=UUID(str(args["premissa_id"])),
            texto=str(args["texto"]),
            separacao=SeparacaoTRIZ(separacao) if separacao else None,
            origem=ORIGEM_DE_GERACAO,
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(injecao.id))

    # -- M4: as quatro ações das árvores de futuro e implementação --------------------
    #
    # As quatro só chegam aqui **depois do gate humano** — são `confirm` no catálogo, e a
    # máquina de estados do ciclo 006 é a única porta. O `__proposta__` viaja até o caso de
    # uso e entra no span (RNF-03): é o que torna a mutação vinda de modelo distinguível de
    # edição humana um mês depois, e é a mesma disciplina que o M3 aplicou aos eventos.
    #
    # O que **não** existe aqui é decisão de round: nenhuma ação de ramo negativo (RF-10).

    def _acao_sugerir_efeito_futuro(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        """INT-05: um efeito futuro, ligado à injeção indicada — a sugestão nunca fica solta."""
        if self._efeito_futuro is None or self._ligar_na_arf is None:
            return ("failed", "sugestão indisponível: repositório de árvores não composto")
        proposta = self._proposta_de(args)
        projeto_id = UUID(str(args["projeto_id"]))
        no = self._efeito_futuro.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            papel=PapelNaARF.EFEITO_FUTURO,
            titulo=str(args["texto"]),
            posicao=PosicaoNoCanvas(PASSO_DO_CANVAS, PASSO_DO_CANVAS),
            proposta_id=proposta,
        )
        self._ligar_na_arf.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            origem_id=UUID(str(args["injecao_id"])),
            destino_id=no.id,
        )
        return ("executed", str(no.id))

    def _acao_sugerir_obstaculo(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        """INT-06: um obstáculo. A verbalização avaliada AVISA depois — nunca veta aqui."""
        if self._no_da_apr is None:
            return ("failed", "sugestão indisponível: repositório de árvores não composto")
        no = self._no_da_apr.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            papel=PapelNaAPR.OBSTACULO,
            titulo=str(args["texto"]),
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(no.id))

    def _acao_sugerir_objetivo_intermediario(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        """INT-07: o objetivo intermediário JÁ pareado — e o julgamento continua humano."""
        if self._no_da_apr is None or self._parear is None:
            return ("failed", "sugestão indisponível: repositório de árvores não composto")
        proposta = self._proposta_de(args)
        projeto_id = UUID(str(args["projeto_id"]))
        no = self._no_da_apr.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            papel=PapelNaAPR.OBJETIVO_INTERMEDIARIO,
            titulo=str(args["texto"]),
            proposta_id=proposta,
        )
        # O par vem pré-preenchido (INT-07); o **julgamento** do teste de validade não vem,
        # e não vem por regra: ele é humano (RN-07), e uma ação que o preenchesse trocaria
        # o método por uma caixa marcada.
        self._parear.rodar(
            dono=principal.dono(),
            projeto_id=projeto_id,
            obstaculo_id=UUID(str(args["obstaculo_id"])),
            oi_id=no.id,
            proposta_id=proposta,
        )
        return ("executed", str(no.id))

    def _acao_sugerir_passo(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        """INT-08: a tripla inteira. Sem os três campos a proposta nem nasce (input_schema)."""
        if self._registrar_passo is None:
            return ("failed", "sugestão indisponível: repositório de árvores não composto")
        no = self._registrar_passo.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            acao=str(args["acao"]),
            necessidade=str(args["necessidade"]),
            resultado_esperado=str(args["resultado_esperado"]),
            proposta_id=self._proposta_de(args),
        )
        return ("executed", str(no.id))

    def _acao_sugerir_restricao(
        self, args: dict[str, Any], principal: Principal
    ) -> tuple[str, str]:
        """RF-19/INT-02: aceitar registra a restrição COM a referência de origem.

        A origem não é opcional aqui, e a assimetria com a rota manual é o requisito: uma
        restrição registrada à mão pode não ter de onde ter vindo (RF-06), mas uma que
        nasceu de uma sugestão sobre a Árvore da Realidade Atual tem — e a referência é
        justamente a evidência que sustenta a conclusão (US-04). O `input_schema` exige os
        dois identificadores, então uma proposta sem eles nem chega aqui.
        """
        if self._registrar_restricao is None:
            return ("failed", "sugestão indisponível: repositório de focalização não composto")
        restricao = self._registrar_restricao.rodar(
            dono=principal.dono(),
            projeto_id=UUID(str(args["projeto_id"])),
            descricao=str(args["descricao"]),
            tipo=str(args["tipo"]),
            justificativa=str(args["justificativa"]),
            autor=str(args.get("autor") or principal.usuario_id),
            origem=ReferenciaDeOrigemDaRestricao(
                ferramenta="ara",
                projeto_id=UUID(str(args["ara_projeto_id"])),
                no_id=UUID(str(args["no_id"])),
            ),
        )
        return ("executed", str(restricao.id))
