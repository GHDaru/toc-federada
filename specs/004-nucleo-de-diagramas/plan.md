# Plan 004 — Núcleo de diagramas (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of Done
> (Definição de Pronto) · DoR — Definition of Ready (Definição de Prontidão) · TDD —
> Test-Driven Development (desenvolvimento guiado por teste) · DDD — Domain-Driven
> Design (Design Orientado a Domínio) · UI — interface de usuário · IA — inteligência
> artificial · OTel — OpenTelemetry · CI — integração contínua · REST —
> Representational State Transfer · JSON — JavaScript Object Notation · YAGNI — You
> Aren't Gonna Need It · FSM — máquina de estados finitos

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes de o
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido na
  abertura, com a junta do ciclo 003 fechada.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 004 existe antes deste plano, e ambos antes de qualquer linha de código do módulo — o primeiro ciclo de implementação nasce com a ordem que a linhagem inverteu quatro vezes. Mudança de escopo volta à spec antes de virar código; os 4 `[DÚVIDA]` do Clarify vão ao Product Steward no gate de abertura. |
| II. Human-governed orchestration | ✅ O humano decide no gate: aprovação da spec, respostas do Clarify (retenção, concorrência, papéis, teto), corte de apetite se estourar. Agentes implementam por fronteira (domínio, adaptadores, UI); a revisão independente em contexto fresco fica com quem não implementou (`TAIL:review`). |
| III. Reversibility / risk gates | ✅ A reversibilidade é o **conteúdo** do ciclo, não só o método: exclusão suave (RF-06), desfazer de sessão (RF-22), reverter com evento compensatório (RF-25), migração com downgrade testado (RNF-09), importação que nunca substitui (RF-35). O irreversível (exclusão definitiva) sobe de classe e exige confirmação nomeada — o item 8 aplicado, não citado. |
| IV. Test-first / verifiable DoD | ✅ TDD estrito: cada invariante do `data-model.md` nasce como teste de domínio que falha primeiro; o teste do filtro invertido da linhagem (spec F-06 — a linha está colada na spec) é o T-04, escrito antes do agregado. DoD com 14 linhas executáveis; `TAIL:mutation` sabota a suíte de importação e o import-linter e os vê recusar. |
| V. Context economy / boundary | ✅ Corte por fronteira dentro do ciclo: domínio puro → casos de uso/portas → adaptadores → UI → jornada, cada um implementável em contexto separado com a spec como integrador. Semântica TOC fica inteira fora (RN-04) — é o corte que mantém M2–M5 paralelizáveis depois. |
| VI. Living artifacts | ✅ `data-model.md` é consumido pelos testes de domínio (divergência se resolve a favor do teste e volta ao documento); `contracts/rest-api.md` é consumido pelos testes de contrato e vira OpenAPI gerado; a jornada viva consome o build real; os eventos de domínio alimentam histórico, reverter e o traço — nenhum artefato sem função forçante. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI neste ciclo: colaboração em tempo real (Clarify 2 — bloqueio otimista basta até prova contrária), refazer/*redo* (mesma conclusão da irmã no ADR 0013 dela), versionamento de diagrama navegável (o objeto histórico basta), importação dos formatos da linhagem (ciclo 011). Cada descarte tem porta de volta declarada. |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo da spec, deste plano, das tasks e do qa-report; termos de domínio novos (exclusão suave, episódio, evento compensatório) definidos onde nascem. Conferência por amostragem do revisor da cauda, não por grep. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes externas da spec (linhagem, ADR 0013 da irmã) foram lidas com `arquivo:linha`; defeito encontrado na linhagem (o filtro invertido, F-06) é **fonte**, não conserto — ninguém commita no `tocbuilderv3`. Lacuna externa achada durante o ciclo vira `mensagens/NNN-...`. |
| P2. Federação por contrato (APH) | ✅ Identidade só pela introspecção da junta 003 (INT-01); autorização por capacidades, fail-closed (RNF-04); **item 8 operacionalizado**: política por tipo de ação declarada no servidor (RF-21), traço incondicional (RF-26), FSM uma só — as três formas executáveis que a irmã deixou como condição da Leitura A entram aqui como tarefas com aptidão (T-07, T-08). Nenhuma ação de IA neste ciclo (INT-02: catálogo é do 006). |
| P3. Domínio puro (DDD + hexagonal) | ✅ Agregado Projeto sem framework, relógio por porta, repositório por porta; `import-linter` no CI falhando o build na violação (RNF-02, DoD linha 1). O `data-model.md` declara explicitamente o que NÃO é domínio (pilha de desfazer, FSM, esquema físico). |
| P4. TDD | ✅ É o ciclo que estreia o P4 com código de produção: teste de domínio antes do agregado, teste de contrato antes do adaptador, o teste-testemunha do defeito da linhagem antes de tudo (T-04). Zero commit de domínio sem teste correspondente. |
| P5. Observabilidade de nascença | ✅ Toda mutação com traço OTel correlacionado e log estruturado (RNF-01), sobre a fundação de OTel do ciclo 003; o teste de integração falha se qualquer mutação não emitir traço (DoD linha 8) — traço por teste, não por promessa. |
| P6. Jornada viva com prova visual | ✅ Jornada da construção de um diagrama sintético, captura gerada do build real por script versionado, avaliação heurística datada, no mesmo pull request (T-14). Base 100% sintética (ADR 0006). |
| P7. Segredo nunca no cliente | ✅ Nenhum provedor de modelo, chave ou credencial no cliente (DoD linha 10); segredos do serviço só por variável de ambiente. O contraexemplo da linhagem (D-01) está medido na visão. |

**Sem violações.** Nenhum "não aplicável": este é o primeiro ciclo em que os sete
princípios operam ao mesmo tempo sobre código de produção.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: a forma do canvas e da tabela vem da linhagem medida (spec F-01–F-08) e do protótipo do ciclo 002; a persistência e a identidade vêm da junta do 003. A única incógnita real (desempenho com 200 nós) tem teste próprio na DoD, não pesquisa. |
| `data-model.md` | `ART:data-model=yes` | Primeiro ciclo com modelo de domínio persistido. Esboço em [`data-model.md`](data-model.md) — agregado, entidades, objetos de valor, eventos, invariantes — consolidado na abertura; os testes de domínio são a forma final e prevalecem sobre o documento. |
| `contracts/` | `ART:contracts=yes` | Primeiro ciclo que define interface própria: [`contracts/rest-api.md`](contracts/rest-api.md) esboça os recursos REST (`/api/toc/projects` e sub-recursos), a semântica de exclusão suave, a ausência deliberada do `PUT` de estado inteiro, e o contrato de importação. Vira OpenAPI gerado + testes de contrato no ciclo. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (14 linhas com comando); uma lista adicional duplicaria função (Princípio VI). |
| `ux-design.md` | `ART:ux-design=no` | O desenho das telas do M1 é entrega do ciclo 002 (`../002-prototipo-de-interfaces/`), que este ciclo **consome** — refazê-lo aqui duplicaria o artefato. Ajustes que a implementação exigir voltam ao `ux-design.md` de lá, no mesmo pull request. |

## Decisões de arquitetura do módulo

1. **Comandos nomeados, não "salvar estado".** A linhagem persistia por
   `saveProjectState` — o projeto inteiro por cima (`mockApiService.ts:286-301`). Aqui
   cada mutação é um comando do agregado com evento próprio; não existe rota de
   substituição cega (ver `contracts/rest-api.md`). É o que torna traço, desfazer,
   reverter e política por tipo de ação possíveis.
2. **Eventos de domínio somente-acréscimo** como espinha do histórico, do reverter e do
   traço — o desfazer gera `MutacaoCompensada` correlacionada, nunca apaga (padrão do
   ADR 0013 da irmã, spec F-13).
3. **Pilha de desfazer na sessão da interface**, disparando comandos inversos — o
   servidor mantém uma FSM só (item 8). Episódio ≠ clique; recarregar mata a pilha por
   desenho.
4. **Núcleo sem semântica TOC** (RN-04): tipo de nó e de projeto extensíveis por módulo.
   M2–M5 acrescentam entidades e regras por composição, nunca por `if` no núcleo.
5. **Política por tipo de ação declarada em dados** (tabela versionada no servidor), com
   o vocabulário de classes de risco que o catálogo `toc.*` (ciclo 006) reutiliza
   (INT-03).
6. **Exportação canônica** (ordenação estável de chaves e coleções) para que
   determinismo seja testável por `diff` — e a importação é uma função pura de validação
   antes de qualquer efeito.

## Grafo de dependência das tarefas

```
T-01 (DoD fixada)
  └─► T-02 (portas da junta 003 verificadas)
        └─► T-03 (contrato import-linter) ─► T-04 (teste-testemunha F-06)
              └─► T-05 (domínio: agregado+invariantes+eventos, TDD)
                    ├─► T-06 (casos de uso + portas)
                    │     ├─► T-07 (política por tipo de ação + traço incondicional)
                    │     ├─► T-08 (adaptadores REST + Alembic + isolamento)
                    │     └─► T-09 (export/import não destrutivo)
                    └─► T-10 (UI: lista+lixeira) ─► T-11 (UI: canvas+painel)
                                                      └─► T-12 (desfazer/reverter na UI)
T-08, T-09, T-12 ─► T-13 (i18n + tema + telas registráveis)
T-11..T-13 ─► T-14 (jornada viva) ─► T-15 (aptidões + qa-report) ─► cauda (T-16..T-19)
```

## Gates (DoR / DoD)

- **DoR — o ciclo não abre sem**: gate humano do 001 fechado; aptidão do ciclo 003
  verde ("a junta fecha contra a ghdaru real" — introspecção, banco, OTel, CI); os 4
  `[DÚVIDA]` do Clarify respondidos; `ux-design.md` do 002 cobrindo as telas 6.1–6.6 da
  spec.
- **DoD — o ciclo não fecha sem**: as 14 linhas da tabela de aceite da spec verdes com
  saída colada no `qa-report.md` (R1) e o tamanho do que cada portão examinou (R2);
  cauda completa (`TAIL:review`, `TAIL:security`, `TAIL:mutation`, `TAIL:gate`).
- **Corte de apetite** (round 004, spec F-14): estourou → sai primeiro o desfazer de
  sessão (modelo fica preparado: eventos e comandos inversos existem); **nunca sai** a
  vista tabular equivalente. Perde escopo, não ganha ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-junta — implementar contra uma junta 003 que não fechou de verdade | L-01 | DoR bloqueante: a aptidão do 003 é pré-condição de abertura; nenhum mock da introspecção em código de produção. |
| GATE-apetite — 4 épicos com TDD estourarem o ciclo | L-02 | Corte declarado antes de abrir (desfazer sai primeiro, tabela nunca); reavaliação no meio do ciclo contra o grafo de tarefas. |
| GATE-tela-id — o identificador de tela (INT-02) divergir do contrato do ciclo 006 | L-03 | Custo de migração declarado baixo; a spec 006 herda o formato daqui ou o troca com busca-e-substituição mecânica. |
| GATE-desempenho — a meta de 200 nós (RNF-05/06) não vir de medição própria | L-04 | Teste de carga na DoD (linha da RNF-05) + medição real na jornada viva; meta revista por ADR se a realidade discordar. |
| GATE-politica-por-origem — o item 8 degradar para `if origem == humano` na implementação | spec RF-21 | A tarefa T-07 tem aptidão própria: teste que envia a mesma mutação por dois caminhos e verifica que a decisão saiu da tabela de tipos de ação, nunca de origem alegada. |
