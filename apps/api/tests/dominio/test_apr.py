"""M4 · E4.2 — a Árvore de Pré-Requisitos (APR): obstáculos, objetivos e sequenciamento.

Siglas, uma vez neste arquivo: **APR** — Árvore de Pré-Requisitos · **OI** — Objetivo
Intermediário · **ARF** — Árvore da Realidade Futura · **ARA** — Árvore da Realidade
Atual · **TOC** — Teoria das Restrições · **M1** — Núcleo de Diagramas Lógicos ·
**RF/RN/RNF** — requisito funcional / regra de negócio / requisito não funcional.

**A distinção que manda neste arquivo é lógica, não visual.** A ARA e a ARF usam
**suficiência** ("Se A, então B"); a APR usa **condição necessária** ("A precisa existir
antes de B") — a fonte técnica é a skill local `toc-prt`
(`references/prt-methodology.md`, "Lógica usada: Condição Necessária... Diferente das
árvores de Realidade Atual e Futura"). A RN-05 diz que as duas não se misturam no mesmo
projeto, e a prova aqui é **negativa**: a APR não oferece a operação de exame de elo. O
que a ferramenta não oferece é o que ninguém usa por engano.

Base sintética (ADR 0006): "Instituição Horizonte", personas fictícias.
"""
from __future__ import annotations

from datetime import datetime, timezone
from uuid import UUID, uuid4

import pytest

from toc_api.dominio.apr import (
    FERRAMENTA_APR,
    ElipseInvalida,
    PapelNaAPR,
    PapelNaAprInvalido,
    ParInvalido,
    ProjetoAPR,
    novo_projeto_apr,
    reidratar_apr,
)
from toc_api.dominio.erros import MutacaoForaDaRaiz, MutacaoRecusada, NaoEncontrado
from toc_api.dominio.eventos import (
    ElipseFormada,
    ObstaculoPareado,
    SequenciamentoGerado,
)
# Apelido local: o evento do domínio chama-se `TesteDeValidadeJulgado` (vocabulário da
# spec 008), e o pytest tentaria coletá-lo como classe de teste se o nome entrasse aqui.
from toc_api.dominio.eventos import TesteDeValidadeJulgado as JulgamentoDoParRegistrado
from toc_api.dominio.identidade import DonoDoProjeto
from toc_api.dominio.verbalizacao import CodigoDeVerbalizacao, Veredito

AGORA = datetime(2026, 9, 6, 10, 0, tzinfo=timezone.utc)
DONO = DonoDoProjeto(inquilino_id="instituicao-horizonte", usuario_id="u-facilitadora")
ID_DA_APR = UUID("33333333-3333-4333-8333-333333333301")

OBJETIVO = "O processo de matrícula responde em dois dias"
OBSTACULO = "Há apenas uma pessoa treinada no sistema de matrículas"
OI = "Existem três pessoas treinadas e escaladas"


def apr() -> ProjetoAPR:
    projeto = novo_projeto_apr(
        id=ID_DA_APR, dono=DONO, nome="Implementação da matrícula", objetivo=OBJETIVO, em=AGORA
    )
    projeto.drenar_eventos()
    return projeto


# --------------------------------------------------------------------------------------
# F4.2.1 — o projeto, o objetivo único, e a lógica de necessidade (RF-14..RF-16, RN-05)
# --------------------------------------------------------------------------------------


def test_a_apr_nasce_com_exatamente_um_objetivo_verbalizado_no_presente() -> None:
    arvore = novo_projeto_apr(
        id=ID_DA_APR, dono=DONO, nome="Implementação", objetivo=OBJETIVO, em=AGORA
    )
    print(f"ferramenta={arvore.projeto.ferramenta!r} objetivo={arvore.objetivo.titulo!r}")
    assert arvore.projeto.ferramenta == FERRAMENTA_APR
    assert arvore.objetivo.titulo == OBJETIVO
    assert arvore.papel_do_no(arvore.objetivo.id) is PapelNaAPR.OBJETIVO
    assert len(arvore.nos_do_papel(PapelNaAPR.OBJETIVO)) == 1


def test_o_projeto_da_apr_recusa_mutacao_que_nao_venha_pela_raiz() -> None:
    arvore = apr()
    with pytest.raises(MutacaoForaDaRaiz) as erro:
        arvore.projeto.adicionar_no(titulo="por fora", em=AGORA)
    print(f"recusa: ferramenta={erro.value.ferramenta!r} raiz={erro.value.raiz!r}")
    assert erro.value.raiz == "ProjetoAPR"


def test_o_objetivo_e_indestrutivel_e_o_papel_dele_nao_muda() -> None:
    """RF-14: "criado na origem e indestrutível enquanto o projeto viver — texto editável,
    papel não"."""
    arvore = apr()

    with pytest.raises(PapelNaAprInvalido) as no_papel:
        arvore.mudar_papel(arvore.objetivo.id, PapelNaAPR.OBJETIVO_INTERMEDIARIO, em=AGORA)
    with pytest.raises(PapelNaAprInvalido) as na_exclusao:
        arvore.excluir_no(arvore.objetivo.id, em=AGORA)

    print(f"papel: {no_papel.value.regra} · exclusão: {na_exclusao.value.regra}")
    assert no_papel.value.regra == "objetivo_imutavel"
    assert na_exclusao.value.regra == "objetivo_indestrutivel"

    arvore.editar_objetivo("O processo de matrícula responde em um dia", em=AGORA)
    assert arvore.objetivo.titulo == "O processo de matrícula responde em um dia"


def test_a_aresta_se_le_precisa_existir_antes_de_e_nunca_se_entao() -> None:
    """RF-16/RN-05: a APR usa condição necessária. A leitura é a prova positiva."""
    arvore = apr()
    primeiro = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    segundo = arvore.adicionar_objetivo_intermediario(
        titulo="A escala de plantão da matrícula está publicada", em=AGORA
    )

    dependencia = arvore.depender(primeiro.id, segundo.id, em=AGORA)

    leitura = arvore.leitura_da_dependencia(dependencia.id)
    print(f"leitura: {leitura}")
    assert leitura == f"{OI} precisa existir antes de A escala de plantão da matrícula está publicada"
    assert "então" not in leitura


def test_a_apr_nao_oferece_exame_de_elo_nem_conector_de_suficiencia() -> None:
    """RN-05, a prova NEGATIVA: as duas lógicas não se misturam no mesmo projeto.

    A garantia não é um aviso de interface: é a **ausência da operação**. O que a
    ferramenta não oferece é o que ninguém usa por engano.
    """
    arvore = apr()
    ausentes = [
        nome
        for nome in ("examinar_elo", "exame", "leitura_do_elo", "formar_conector_e")
        if not hasattr(arvore, nome)
    ]
    print(f"operações de suficiência ausentes da APR: {ausentes}")
    assert len(ausentes) == 4


def test_obstaculo_e_objetivo_intermediario_nascem_com_papeis_distintos() -> None:
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)

    print(f"tipos: obstáculo={obstaculo.tipo!r} objetivo intermediário={oi.tipo!r}")
    assert arvore.papel_do_no(obstaculo.id) is PapelNaAPR.OBSTACULO
    assert arvore.papel_do_no(oi.id) is PapelNaAPR.OBJETIVO_INTERMEDIARIO
    assert obstaculo.tipo != oi.tipo


def test_dependencia_so_liga_objetivo_intermediario_a_oi_ou_ao_objetivo() -> None:
    """A dependência é entre OIs (ou OI → objetivo). Obstáculo é anotação, não etapa."""
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)

    with pytest.raises(PapelNaAprInvalido) as erro:
        arvore.depender(obstaculo.id, oi.id, em=AGORA)

    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "dependencia_entre_objetivos"
    assert arvore.depender(oi.id, arvore.objetivo.id, em=AGORA)


# --------------------------------------------------------------------------------------
# F4.2.2 — pareamento obstáculo ↔ OI e o teste de validade (RF-17, RF-18, RN-07, RN-09)
# --------------------------------------------------------------------------------------


def test_parear_registra_o_obstaculo_com_o_oi_que_o_supera() -> None:
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)

    par = arvore.parear(obstaculo.id, oi.id, em=AGORA)

    print(f"par: obstáculo={str(par.obstaculo_id)[:8]} oi={str(par.objetivo_intermediario_id)[:8]}")
    assert par.obstaculo_id == obstaculo.id
    assert par.objetivo_intermediario_id == oi.id
    assert isinstance(arvore.projeto.eventos[-1], ObstaculoPareado)


def test_um_oi_supera_mais_de_um_obstaculo_e_o_obstaculo_tem_um_par_so() -> None:
    """RF-17: "um OI pode superar vários obstáculos" — a recíproca não vale."""
    arvore = apr()
    um = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    outro = arvore.adicionar_obstaculo(
        titulo="A escala do plantão de matrícula muda toda semana", em=AGORA
    )
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    arvore.parear(um.id, oi.id, em=AGORA)
    arvore.parear(outro.id, oi.id, em=AGORA)

    assert len(arvore.pares()) == 2

    outro_oi = arvore.adicionar_objetivo_intermediario(titulo="A escala está publicada", em=AGORA)
    with pytest.raises(ParInvalido) as erro:
        arvore.parear(um.id, outro_oi.id, em=AGORA)
    print(f"recusa: regra={erro.value.regra!r}")
    assert erro.value.regra == "obstaculo_ja_pareado"


def test_parear_exige_os_papeis_certos_nas_duas_pontas() -> None:
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    outro = arvore.adicionar_obstaculo(titulo="A fila tem trinta pessoas", em=AGORA)
    with pytest.raises(ParInvalido) as erro:
        arvore.parear(obstaculo.id, outro.id, em=AGORA)
    assert erro.value.regra == "papel_incompativel"


def test_o_teste_de_validade_e_julgamento_registrado_e_nunca_campo_calculado() -> None:
    """RN-07: parecer com autor e data, acumulável, **nunca sobrescrito**."""
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    par = arvore.parear(obstaculo.id, oi.id, em=AGORA)

    leitura = arvore.leitura_do_teste_de_validade(par.id)
    print(f"teste: {leitura}")
    assert leitura == f"Se {OI}, então {OBSTACULO} não impede mais {OBJETIVO}"

    arvore.julgar_par(
        par.id, autor="Facilitadora TOC", valido=True, justificativa="a escala cobre o pico", em=AGORA
    )
    arvore.julgar_par(
        par.id,
        autor="Gestora da Instituição Horizonte",
        valido=False,
        justificativa="o pico exige quatro pessoas, não três",
        em=AGORA,
    )

    julgamentos = arvore.par(par.id).julgamentos
    print(f"julgamentos acumulados: {[(j.autor, j.valido) for j in julgamentos]}")
    assert len(julgamentos) == 2
    assert julgamentos[0].valido is True and julgamentos[1].valido is False
    assert isinstance(arvore.projeto.eventos[-1], JulgamentoDoParRegistrado)


def test_julgar_exige_autor_e_justificativa() -> None:
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    par = arvore.parear(obstaculo.id, oi.id, em=AGORA)

    with pytest.raises(Exception):
        arvore.julgar_par(par.id, autor="", valido=True, justificativa="x", em=AGORA)
    with pytest.raises(Exception):
        arvore.julgar_par(par.id, autor="Facilitadora TOC", valido=True, justificativa=" ", em=AGORA)


def test_obstaculo_sem_oi_e_pendencia_e_nunca_proibicao_de_gravar() -> None:
    """RN-09: "o levantamento em grupo precisa registrar antes de parear"."""
    arvore = apr()
    solto = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi_orfao = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)

    pendencias = arvore.pendencias_de_pareamento()

    print(f"pendências: {pendencias}")
    assert pendencias["obstaculos_sem_oi"] == (solto.id,)
    assert pendencias["objetivos_sem_obstaculo"] == (oi_orfao.id,)


def test_excluir_uma_ponta_do_par_desfaz_o_par_sem_deixar_referencia_orfa() -> None:
    arvore = apr()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    oi = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    arvore.parear(obstaculo.id, oi.id, em=AGORA)

    arvore.excluir_no(oi.id, em=AGORA)

    assert arvore.pares() == ()
    assert arvore.pendencias_de_pareamento()["obstaculos_sem_oi"] == (obstaculo.id,)


# --------------------------------------------------------------------------------------
# F4.2.3 — a verbalização avaliada avisa, e NÃO veta (RF-21, RN-08)
# --------------------------------------------------------------------------------------


def test_o_obstaculo_verbalizado_como_tarefa_recebe_aviso_e_e_registrado_assim_mesmo() -> None:
    arvore = apr()

    torto = arvore.adicionar_obstaculo(titulo="Precisamos criar a conversão de dados", em=AGORA)
    avaliacao = arvore.avaliar_verbalizacao(torto.id)

    print(f"veredito={avaliacao.veredito.value} códigos={avaliacao.codigos}")
    assert avaliacao.veredito is Veredito.AVISO
    assert CodigoDeVerbalizacao.VERBO_DE_ACAO.value in avaliacao.codigos
    # RN-08: aviso, nunca veto — o nó está lá.
    assert arvore.projeto.no(torto.id).titulo == "Precisamos criar a conversão de dados"


def test_a_reavaliacao_e_automatica_na_edicao_do_texto() -> None:
    """RF-21: "a reavaliação é automática na edição" — o aviso não fica pendurado."""
    arvore = apr()
    torto = arvore.adicionar_obstaculo(titulo="Precisamos criar a conversão de dados", em=AGORA)
    assert arvore.avaliar_verbalizacao(torto.id).veredito is Veredito.AVISO

    arvore.editar_no(torto.id, titulo="Não existe conversão de dados entre os dois sistemas", em=AGORA)

    print(f"depois da edição: {arvore.avaliar_verbalizacao(torto.id).veredito.value}")
    assert arvore.avaliar_verbalizacao(torto.id).veredito is Veredito.ATENDE


def test_o_objetivo_nao_e_avaliado_pela_heuristica_dos_dois_papeis() -> None:
    arvore = apr()
    with pytest.raises(MutacaoRecusada):
        arvore.avaliar_verbalizacao(arvore.objetivo.id)


# --------------------------------------------------------------------------------------
# F4.2.4 — sequenciamento por dependência (RF-23..RF-27, RN-06)
# --------------------------------------------------------------------------------------


def apr_sequenciada() -> tuple[ProjetoAPR, dict[str, UUID]]:
    """Seis objetivos intermediários com dependências declaradas (a US-10 em fixture)."""
    arvore = apr()
    nomes = {
        "treinadas": "Existem três pessoas treinadas e escaladas",
        "escala": "A escala de plantão da matrícula está publicada",
        "conferencia": "A rotina de conferência está operacional e validada",
        "sistema": "O sistema de matrículas conversa com o financeiro",
        "painel": "O painel de fila está disponível para a Secretaria",
        "piloto": "O piloto da matrícula em dois dias está concluído",
    }
    ids = {
        chave: arvore.adicionar_objetivo_intermediario(titulo=titulo, em=AGORA).id
        for chave, titulo in nomes.items()
    }
    arvore.depender(ids["treinadas"], ids["escala"], em=AGORA)
    arvore.depender(ids["sistema"], ids["conferencia"], em=AGORA)
    arvore.depender(ids["escala"], ids["piloto"], em=AGORA)
    arvore.depender(ids["conferencia"], ids["piloto"], em=AGORA)
    arvore.depender(ids["piloto"], arvore.objetivo.id, em=AGORA)
    return arvore, ids


def test_o_sequenciamento_poe_em_camadas_quem_nao_depende_de_nada_primeiro() -> None:
    arvore, ids = apr_sequenciada()

    sequencia = arvore.sequenciar()

    camadas = [sorted(str(i)[:4] for i in camada) for camada in sequencia.camadas]
    print(f"camadas: {len(sequencia.camadas)} · resumo={sequencia.resumo()}")
    assert set(sequencia.camadas[0]) == {ids["treinadas"], ids["sistema"], ids["painel"]}
    assert set(sequencia.camadas[1]) == {ids["escala"], ids["conferencia"]}
    assert set(sequencia.camadas[2]) == {ids["piloto"]}
    assert camadas  # a saída acima nomeia o que foi examinado (R2)


def test_o_sequenciamento_identifica_ramos_paralelos() -> None:
    arvore, ids = apr_sequenciada()

    sequencia = arvore.sequenciar()

    tamanhos = sorted(len(r) for r in sequencia.ramos_paralelos)
    print(f"ramos paralelos: {len(sequencia.ramos_paralelos)} com tamanhos {tamanhos}")
    # O "painel" não depende de nada e nada depende dele: é um ramo próprio.
    assert any(ramo == (ids["painel"],) for ramo in sequencia.ramos_paralelos)
    assert len(sequencia.ramos_paralelos) == 2


def test_dependencia_circular_e_pendencia_bloqueante_com_o_ciclo_nomeado() -> None:
    """RN-06/RF-24: diferente da ARA, onde ciclo é legítimo — aqui ele BLOQUEIA."""
    arvore = apr()
    um = arvore.adicionar_objetivo_intermediario(titulo="A escala está publicada", em=AGORA)
    outro = arvore.adicionar_objetivo_intermediario(titulo=OI, em=AGORA)
    arvore.depender(um.id, outro.id, em=AGORA)
    arvore.depender(outro.id, um.id, em=AGORA)

    sequencia = arvore.sequenciar()

    print(f"ciclos={len(sequencia.ciclos)} bloqueado={sequencia.bloqueado}")
    assert sequencia.bloqueado is True
    assert len(sequencia.ciclos) == 1
    assert set(sequencia.ciclos[0]) == {um.id, outro.id}
    assert sequencia.camadas == ()


def test_a_elipse_de_simultaneidade_agrupa_duas_dependencias_do_mesmo_destino() -> None:
    """RF-19/RN-06: "A **e** B precisam existir antes de C" — a conjunção de necessidade."""
    arvore, ids = apr_sequenciada()
    para_o_piloto = tuple(
        a.id for a in arvore.arestas if a.destino_id == ids["piloto"]
    )

    elipse = arvore.formar_elipse(para_o_piloto, em=AGORA)

    leitura = arvore.leitura_da_elipse(elipse.id)
    print(f"elipse: {leitura}")
    assert "e" in leitura and "precisam existir antes de" in leitura
    assert isinstance(arvore.projeto.eventos[-1], ElipseFormada)
    assert arvore.sequenciar().elipses == (elipse.id,)


def test_a_elipse_exige_duas_dependencias_e_um_destino_unico() -> None:
    arvore, ids = apr_sequenciada()
    uma = next(a.id for a in arvore.arestas if a.destino_id == ids["piloto"])
    outra = next(a.id for a in arvore.arestas if a.destino_id == ids["escala"])

    with pytest.raises(ElipseInvalida) as sozinha:
        arvore.formar_elipse((uma,), em=AGORA)
    with pytest.raises(ElipseInvalida) as destinos:
        arvore.formar_elipse((uma, outra), em=AGORA)

    print(f"regras: {sozinha.value.regra} · {destinos.value.regra}")
    assert sozinha.value.regra == "minimo_duas_dependencias"
    assert destinos.value.regra == "destino_unico"


def test_excluir_a_dependencia_dissolve_a_elipse_em_vez_de_deixar_referencia_orfa() -> None:
    arvore, ids = apr_sequenciada()
    para_o_piloto = tuple(a.id for a in arvore.arestas if a.destino_id == ids["piloto"])
    elipse = arvore.formar_elipse(para_o_piloto, em=AGORA)

    arvore.excluir_dependencia(para_o_piloto[0], em=AGORA)

    print(f"elipses após excluir uma dependência: {arvore.elipses()}")
    assert arvore.elipses() == ()
    with pytest.raises(NaoEncontrado):
        arvore.elipse(elipse.id)


def test_a_tabela_resumo_traz_obstaculo_oi_e_dependencias_na_ordem_das_camadas() -> None:
    """RF-25/US-11: "levar o plano à reunião sem exigir leitura de diagrama"."""
    arvore, ids = apr_sequenciada()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    arvore.parear(obstaculo.id, ids["treinadas"], em=AGORA)
    orfao = arvore.adicionar_obstaculo(titulo="A fila tem trinta pessoas por dia", em=AGORA)

    linhas = arvore.tabela_resumo()

    for linha in linhas:
        print(
            f"camada={linha.camada} obstáculo={linha.obstaculo!r} "
            f"oi={linha.objetivo_intermediario!r} depende_de={linha.depende_de}"
        )
    # A ordem é a das CAMADAS (RF-25); dentro da camada é canônica por identificador,
    # para o mesmo plano sair igual duas vezes.
    assert [l.camada for l in linhas] == sorted(
        [l.camada for l in linhas if l.camada is not None]
    ) + [None]
    com_obstaculo = [l for l in linhas if l.obstaculo == OBSTACULO]
    assert len(com_obstaculo) == 1
    assert com_obstaculo[0].camada == 0
    assert com_obstaculo[0].objetivo_intermediario == "Existem três pessoas treinadas e escaladas"
    # O obstáculo sem par entra como pendência no fim, nunca sumindo da tabela.
    assert linhas[-1].obstaculo == "A fila tem trinta pessoas por dia"
    assert linhas[-1].objetivo_intermediario is None
    assert linhas[-1].camada is None


def test_gerar_o_sequenciamento_emite_o_resumo_quantitativo_e_nao_muta_o_grafo() -> None:
    """RF-26: `SequenciamentoGerado` com camadas, OIs por camada e pendências."""
    arvore, _ = apr_sequenciada()
    antes = (len(arvore.nos), len(arvore.arestas))
    arvore.drenar_eventos()

    sequencia = arvore.gerar_sequenciamento(em=AGORA)

    evento = arvore.projeto.eventos[-1]
    print(f"antes={antes} depois={(len(arvore.nos), len(arvore.arestas))} resumo={evento.resumo}")
    assert antes == (len(arvore.nos), len(arvore.arestas))
    assert isinstance(evento, SequenciamentoGerado)
    assert evento.resumo["camadas"] == len(sequencia.camadas)
    assert evento.resumo["objetivos_intermediarios"] == 6


def test_reidratar_a_apr_nao_emite_evento_nenhum() -> None:
    arvore, ids = apr_sequenciada()
    obstaculo = arvore.adicionar_obstaculo(titulo=OBSTACULO, em=AGORA)
    par = arvore.parear(obstaculo.id, ids["treinadas"], em=AGORA)

    de_volta = reidratar_apr(arvore.projeto, pares=(par,), elipses=())

    print(f"eventos após reidratar: {len(de_volta.projeto.eventos)}")
    assert de_volta.projeto.eventos == ()
    assert de_volta.pares()[0].id == par.id
    assert de_volta.objetivo.titulo == OBJETIVO
