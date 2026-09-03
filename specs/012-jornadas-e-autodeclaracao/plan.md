# Plan 012 — Jornadas e autodeclaração (ciclo planejado)

> Siglas: **TOC** — Teoria das Restrições · **APH** — Aplicação ↔ Harness · **ADR** —
> Architecture Decision Record (Registro de Decisão Arquitetural) · **DoD** — Definition of
> Done (Definição de Pronto) · **DoR** — Definition of Ready (Definição de Prontidão) ·
> **TDD** — Test-Driven Development (desenvolvimento guiado por teste) · **DDD** —
> Domain-Driven Design (Design Orientado a Domínio) · **P6** — princípio "Jornada viva" da
> constituição do projeto · **ARA** — Árvore da Realidade Atual · **NC** — Nuvem de
> Conflito · **ARF** — Árvore da Realidade Futura · **APR** — Árvore de Pré-Requisitos ·
> **AT** — Árvore de Transição · **S&T** — Árvore de Estratégia & Táticas · **UI** —
> interface de usuário · **UX** — experiência de usuário · **IA** — inteligência artificial
> · **LLM** — modelo de linguagem de grande porte (*Large Language Model*) · **CI** —
> integração contínua · **OTel** — OpenTelemetry · **HTTP** — HyperText Transfer Protocol ·
> **YAGNI** — *You Aren't Gonna Need It* (não vai precisar disso) · **i18n** —
> internacionalização

- **Spec**: [`spec.md`](spec.md) (Rascunho — aprovação no gate humano que abre o ciclo) ·
  **Raia**: plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e é reconferido na
  abertura, com os ciclos 009, 010 e 011 promovidos.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 012 existe antes deste plano; o escopo é o do round 012 e a regra "nada de funcionalidade nova" é o próprio recorte — round de fechamento não esconde feature. Achado da avaliação heurística que exija mudança de produto **volta à spec do módulo dono**, não vira conserto de passagem aqui; é a diferença entre fechar e alargar. Os 5 `[DÚVIDA]` vão ao gate de abertura. |
| II. Human-governed orchestration | ✅ A decisão mais pesada do ciclo é humana e indelegável: o Product Steward **assina a autodeclaração**, porque é ela que circula para fora do repositório (portão humano do roadmap). Agentes executam a suíte, preenchem a matriz e regeram capturas; a revisão independente em contexto fresco confere linha a linha (`TAIL:review`) — e quem preencheu a matriz não é quem a revisa. |
| III. Reversibility / risk gates | ✅ O ciclo não muda produto: o raio é documental, e o único efeito externo é a **publicação da declaração** — irreversível na prática (uma declaração circula), por isso sobe de classe e vira portão humano explícito ([DÚVIDA] 2 decide se publica já). A execução da suíte roda contra ambiente de teste com base sintética (RNF-07), nunca contra dado de produção. Registro de execução e ADR corrigem-se por acréscimo, nunca por reescrita (RN-05). |
| IV. Test-first / verifiable DoD | ✅ Este ciclo é quase todo função de aptidão: 17 linhas de DoD, cada uma com comando. As duas verificações novas nascem por sabotagem — captura órfã e célula de evidência vazia —, e a DoD 15 sabota o gerador do site (acrescentar um requisito muda a contagem exibida sem edição manual). Onde a verificação não é possível — Nível 2, lado aplicação do Anexo B —, o limite é **declarado**, que é a forma honesta de "prove, não declare" quando a prova mecânica não existe. |
| V. Context economy / boundary | ✅ Quatro frentes independentes (jornadas · matriz · suíte · autodeclaração e site), cada uma em contexto próprio, com a spec como integrador. A dependência real é uma só e está no fim: a autodeclaração **deriva** da matriz e do relatório da suíte, e por isso é a última tarefa antes da cauda. |
| VI. Living artifacts | ✅ Nenhum artefato novo sem função forçante: a matriz é consumida pela autodeclaração (uma fonte, duas apresentações — RF-22); o relatório da suíte é consumido pela matriz; as jornadas, pelo portão de captura órfã; o site, pelo portão de divergência. É o ciclo em que a cadeia de rastreabilidade **spec ↔ pull request ↔ testes ↔ jornada** é percorrida inteira e verificada de ponta a ponta. |
| VII. Light governance / YAGNI | ✅ Descartados com porta de volta declarada: suíte própria para o Nível 2 (a norma diz por que não existe — [F-02] da spec; construir uma nossa seria inventar régua para nos medir); certificação externa; avaliação heurística por pessoa de fora (fica como dívida declarada, [DÚVIDA] 3). O ciclo não cria processo novo: usa os portões existentes e acrescenta dois. |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo dos quatro artefatos do ciclo. O cuidado específico aqui é o público: a autodeclaração é o documento que sai do repositório, e nela **toda** sigla de norma (APH, FSM, SSE) nasce por extenso — o leitor de fora não tem o nosso contexto, e é para ele que o princípio VIII existe. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ A suíte, os perfis de exemplo e a norma ficam no `GHDaru/protocolos`, que é **leitura**: rodamos a suíte de fora, contra a nossa URL, e o que fica aqui é o nosso perfil e o nosso registro de execução (INT-01). Lacuna encontrada na norma ou na fundação durante a medição vira `mensagens/NNN-para-<repo>-<assunto>.md` com evidência por `arquivo:linha` — relatar e parar (INT-03). |
| P2. Federação por contrato (APH) | ✅ É o ciclo que **presta contas** ao P2, princípio inegociável: a matriz recebe veredito e evidência por requisito, e a autodeclaração diz o lado (aplicação), a maturidade dos itens experimentais e os limites da prova, exatamente como o §B.12.1 e o §B.11.3 exigem (spec F-03, F-04). Nenhum atalho: requisito delegado à fundação é declarado delegação, nunca contado como conformidade nossa (RF-11). |
| P3. Domínio puro (DDD + hexagonal) | ✅ Nenhuma entidade de domínio nasce aqui, e a spec declara isso por escrito em vez de deixar a seção vazia. `import-linter` continua no CI; o ciclo não acrescenta dependência de produção. |
| P4. TDD | ✅ Não há código de produção novo, logo não há teste-primeiro de produção — e isto é **declaração, não isenção**: as duas funções de aptidão novas (captura órfã, célula vazia) nascem pela sabotagem que elas têm de pegar, que é o teste-primeiro na forma que este ciclo tem. |
| P5. Observabilidade de nascença | ✅ Sem funcionalidade nova, não há traço novo a nascer — declaração, não esquecimento. O que este ciclo verifica é o traço **já existente**: a linha APH-5.5 da matriz (traço em 100% das ações, inclusive recusadas) só fecha com a evidência do teste do ciclo 006. |
| P6. Jornada viva com prova visual | ✅ É o princípio que dá nome ao ciclo: seis jornadas regeradas do build atual, uma travessia de ponta a ponta com persona única, avaliação heurística datada com limite declarado, e o portão de captura órfã nos dois sentidos. Base 100% sintética (ADR 0006), verificada por busca negativa (DoD 16). |
| P7. Segredo nunca no cliente | ✅ A execução da suíte não grava credencial em arquivo: o perfil declara **nomes** de variáveis de ambiente e o token não é impresso nem versionado (RNF-03, spec F-09). O relatório colado é superfície de vazamento e entra no passe de segurança da cauda. |

**Sem violações.** Duas ausências são declaradas por extenso — nenhuma entidade de domínio
(P3) e nenhum traço novo (P5) —, porque um "não aplicável" mudo é o mesmo que uma caixa
marcada sem testemunha.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Nada a pesquisar: a norma está lida e citada por linha (spec F-02..F-07, F-09, F-14, F-15), a suíte tem instruções de uso executáveis e o formato de perfil tem exemplo comentado. O que falta é **medir**, e medir é entrega do ciclo (RF-13), não pesquisa. |
| `data-model.md` | `ART:data-model=no` | Nenhuma entidade de domínio nasce e nenhuma migração é escrita — a spec declara isso na seção de modelo em vez de omiti-la. Os objetos deste ciclo (jornada, linha de aderência, execução, autodeclaração) são artefatos versionados com invariantes verificadas por função de aptidão, não estruturas persistidas. |
| Contratos de fronteira | `ART:contracts=no` | Nenhum contrato novo. O manifesto e o catálogo já foram contratados no ciclo 006; este ciclo os **audita**, e auditar com um segundo contrato criaria a segunda verdade que a matriz existe para impedir. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (17 linhas com comando) e a matriz de aderência é ela própria a lista de conferência da fronteira, com função forçante (RF-08). Uma terceira lista duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | Nenhuma tela nova de produto. As superfícies deste ciclo são documentos e o site gerado — cujo desenho é decisão do ADR 0008 e do gerador vendorizado, não deste plano. Achado de usabilidade da avaliação heurística volta ao `ux-design.md` do módulo dono, no ciclo dele. |

## Decisões de arquitetura do ciclo

1. **Uma fonte, duas apresentações.** A matriz de aderência é a fonte; a autodeclaração é
   uma projeção dela (RF-22), e o site publica **a mesma** declaração, gerada do ADR
   (INT-04). Redigir a declaração à parte criaria duas verdades sobre a mesma fronteira —
   que é precisamente o defeito que a norma fecha com a matriz em dado, e não em prosa
   (spec F-15).
2. **O veredito entra como saiu.** O relatório da suíte é registro imutável, com data,
   alvo, versão da norma e revisão medida; medição nova é registro novo (RNF-02). O
   precedente é o registro da própria fundação: **não apta**, 8 de 11, publicado assim
   (spec F-07).
3. **Perfil de adaptação só se necessário, e sempre no nosso repositório.** Ele traduz
   endereço e vocabulário; declarar operação ausente **faz o check falhar** e é para isso
   que serve (RF-16). O perfil versionado junto do relatório é o que permite a uma terceira
   pessoa distinguir adaptação de lavagem.
4. **Limite declarado onde não há régua.** Nível 2 e lado aplicação do Anexo B não têm
   suíte; a autodeclaração diz isso **junto com a declaração**, não em nota de rodapé
   (RF-21). Uma declaração que esconde o próprio limite é pior que uma lacuna registrada.
5. **A travessia é a prova do encadeamento.** As seis jornadas provam seis ferramentas; a
   sétima prova que elas se ligam — que é o defeito D-11 da linhagem, ferramentas que não
   se encadeiam. Persona única do primeiro ao último elo, verificada na DoD 4.
6. **Achado de produto não vira conserto de passagem.** Toda severidade encontrada na
   avaliação heurística sai com destino declarado: corrigido aqui (se for texto, rótulo ou
   contraste) ou dívida com dono no módulo correspondente. Fechar um ciclo consertando
   silenciosamente o que outro ciclo entregou é como a rastreabilidade se rompe.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada + pré-condições: 009, 010 e 011 promovidos)
  ├─► T-02 (regenerar capturas das seis jornadas; divergência vira achado)
  │     ├─► T-03 (jornada de travessia, persona única)
  │     └─► T-04 (portão de captura órfã, nos dois sentidos)
  ├─► T-05 (executar a suíte do Nível 1 contra a URL publicada; perfil se preciso)
  │     └─► T-06 (registro datado e imutável da execução + itens declarados)
  └─► T-07 (preencher a matriz linha a linha: evidência, parciais, delegações, fora do alvo)
T-02, T-03 ─► T-08 (avaliação heurística datada do conjunto, com destino por achado)
T-06, T-07 ─► T-09 (ADR de autodeclaração — lado, maturidade, limites, evidência)
T-09 ──────► T-10 (índice de ADRs + registro de decisões)
T-04, T-08, T-09 ─► T-11 (regerar o site; portão de divergência; nota de honestidade)
T-10, T-11 ─► T-12 (aptidões + qa-report + retrospectiva da v1) ─► cauda (TAIL:*)
```

A ordem não é arbitrária: **a autodeclaração é a última coisa a ser escrita**, porque ela é
derivada. Escrevê-la antes da matriz e do relatório seria declarar e depois procurar
evidência — a inversão exata que este ciclo existe para não cometer.

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: ciclos **009, 010 e 011 promovidos**
  ([`../../docs/roadmap.md`](../../docs/roadmap.md) — "autodeclarar antes seria declarar sem
  provar"); as seis jornadas existentes com os seus scripts de captura versionados; a
  aplicação publicada e alcançável num ambiente com base sintética (spec L-03); os 5
  `[DÚVIDA]` respondidos, em especial o destino de um veredito "não apto" ([DÚVIDA] 1) e a
  publicação externa da declaração ([DÚVIDA] 2).
- **DoD — o ciclo não fecha sem**: as 17 linhas da tabela de aceite verdes, com saída colada
  (R1) e tamanho examinado (R2) no [`qa-report.md`](qa-report.md); o relatório integral da
  suíte registrado, com o veredito como saiu; a matriz sem célula de evidência vazia; o ADR
  de autodeclaração no índice e no registro de decisões; o site regenerado sem divergência;
  a cauda completa (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 012): **nada sai** — este round já é só o essencial de
  fechamento; se estourar, o que se corta é escopo dos rounds anteriores. **Nunca sai** a
  autodeclaração com evidência.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-declarar-sem-medir — a autodeclaração ser escrita antes da matriz e do relatório e a evidência ser procurada depois | spec RF-22 | Ordem do grafo: T-09 depende de T-06 e T-07. `TAIL:review` confere linha a linha que todo veredito da declaração aparece na matriz com a mesma evidência — divergência entre os dois é achado bloqueante. |
| GATE-nao-apto — a suíte devolver "não apto" no fechamento da versão 1 | spec L-01, [DÚVIDA] 1 | O veredito entra como saiu (RN-04) e cada falha sai com decisão associada (RF-18). A política — corrigir aqui ou declarar com dono e prazo — é decidida **no gate de abertura**, não sob pressão do resultado. |
| GATE-perfil-lavagem — o perfil de adaptação virar isenção disfarçada | spec RF-15, RF-16 | O perfil é versionado aqui, o relatório lista cada tradução aplicada, e a própria suíte recusa fusões de vocabulário na carga (spec F-09). `TAIL:review` lê o perfil contra a superfície real. |
| GATE-captura-envelhecida — capturas que não regeneram passarem como se fossem do build atual | spec RF-01, L-05 | DoD 1 e 2 com `diff`; divergência vira achado nomeado (RF-02). Se o determinismo não se sustentar, a tolerância é **declarada** no portão, nunca aplicada em silêncio. |
| GATE-metade-do-outro-lado — declarar como nossas cláusulas que dependem do hospedeiro | spec L-02 | As 16 cláusulas de "ambos" saem com a nossa metade provada e o estado da outra **observado**, não afirmado; divergência vira `mensagens/NNN` (INT-03). |
| GATE-sigla-nua-para-fora — a declaração circular fora do repositório com jargão que só nós entendemos | Princípio VIII | A autodeclaração é revisada com a régua editorial antes do gate: toda sigla de norma por extenso na primeira ocorrência, e um parágrafo de abertura que diga o que é o padrão e o que é o nosso lado. |
