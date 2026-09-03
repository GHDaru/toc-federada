# Plan 002 — Protótipo de interfaces (ciclo planejado)

> Siglas: TOC — Teoria das Restrições · APH — Aplicação ↔ Harness · ADR — Architecture
> Decision Record (Registro de Decisão Arquitetural) · DoD — Definition of Done
> (Definição de Pronto) · TDD — Test-Driven Development · DDD — Domain-Driven Design ·
> UDE — Undesirable Effect (Efeito Indesejável) · ARA — Árvore da Realidade Atual · NC —
> Nuvem de Conflito · IA — inteligência artificial · YAGNI — You Aren't Gonna Need It ·
> RI — requisito de interface

- **Spec**: `spec.md` (Rascunho — aprovação no gate humano que abre o ciclo) · **Raia**:
  plena · **Data**: 2026-09-03
- **Estado**: **planejado no ciclo 001, não executado.** Este plano é escrito antes do
  ciclo abrir; o Constitution Check abaixo avalia o plano como está e será reconferido na
  abertura, com as precondições do roadmap fechadas.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec 002 existe antes deste plano e ambos antes de qualquer componente; o `## Clarify` (3 dúvidas) vai ao Product Steward no gate que abre o ciclo — a ordem que a irmã só conseguiu no segundo ciclo dela nasce aqui de primeira. |
| II. Human-governed orchestration | ✅ Decisões de produto (pergunta 1 da visão §7, apetite da visão conflito+solução) são do humano, no gate. O corte visual em iframe estreito é criação reversível — decisão de agente registrada em ADR se material (regra R3, paga pela irmã). Revisão independente em contexto fresco na cauda. |
| III. Reversibility / risk gates | ✅ Classe **escrita** em código descartável por contrato: sem implantação, sem dado real, sem rede, sem fundação. A reversibilidade é a natureza do artefato (quatro condições, F-01 da spec), não uma mitigação acrescentada. |
| IV. Test-first / verifiable DoD | ⚠️ **Parcial, e declarado.** O protótipo descartável não está sob TDD (F-01 da spec; mesma fronteira da irmã). O que é verificável por máquina está na DoD da spec (11 linhas com comando): condições do descartável, proveniência e determinismo das capturas, ausência de provedor no cliente. O juízo "esta tela está boa" fica com o humano — é o que a avaliação heurística datada registra. |
| V. Context economy / boundary | ✅ Corte por fronteira: o 002 decide **forma** (RIs de M1–M3), o 003 fecha a junta, o 004+ implementa. Nenhuma linha de domínio, nenhum requisito de módulo antecipado — as specs de módulo consomem o resultado, não o contrário. |
| VI. Living artifacts | ✅ Cada artefato tem consumidor com função forçante: o `ux-design.md` alimenta os componentes; a fixture alimenta o protótipo e as capturas; as capturas alimentam as jornadas; as jornadas alimentam as specs de M1–M3 e o `docs/jornadas/README.md` diz o estágio de cada J-NN. |
| VII. Light governance / YAGNI | ✅ Descartados por YAGNI: sistema de design próprio (tokens bastam), infraestrutura de captura em nuvem (script local), painel de conversa (a IA é da fundação — ADR 0007), e prototipar M4–M6 (estoque). Três artefatos condicionais declarados `no` com motivo, abaixo. |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo da spec, deste plano, das tasks e do qa-report; conferência por leitura de cada documento (não por memória), amostrada pelo revisor da cauda. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório. As fontes externas (irmã, linhagem, norma, guia) foram lidas com `arquivo:linha` nas Fontes da spec; lacuna externa encontrada durante o ciclo vira `mensagens/NNN-...`, nunca commit lá fora. |
| P2. Federação por contrato (APH) | ✅ Sem integração real, o P2 opera aqui como **forma**: o adaptador falso reproduz o envelope do guia (F-05 da spec), o modo só-conteúdo segue o B.8.1 (F-09), o tema segue a regra de interseção+fallback (F-04) — para que o ciclo 003 troque adaptador, não desenho. Nenhum verbo mutador de IA existe neste ciclo (INT-02). |
| P3. Domínio puro (DDD + hexagonal) | ⚠️ **Não aplicável por decisão herdada** (F-01 da spec): protótipo descartável não tem domínio. A forma da porta, porém, já nasce: identidade/tema/handshake isolados atrás do adaptador falso. Volta obrigatório no 003/004. |
| P4. TDD | ⚠️ **Não aplicável por decisão herdada** (F-01 da spec). A tranca contra a porta estreita virar larga é a condição 4: apagado ou reescrito, nunca promovido — mais a aptidão de importação (DoD linha 2). Volta obrigatório no 004. |
| P5. Observabilidade de nascença | ⚠️ **Não aplicável**: sem serviço, sem requisição, sem traço a emitir. Sobe com o esqueleto no 003. |
| P6. Jornada viva com prova visual | ✅ É a entrega central: captura gerada do build do protótipo por script versionado, determinística (regenera byte-idêntica), avaliação heurística datada, tudo no mesmo pull request. A promoção a jornada viva definitiva (build de produção) fica para o ciclo de implementação de cada ferramenta — declarado no `docs/jornadas/README.md`. |
| P7. Segredo nunca no cliente | ✅ Nenhum segredo existe no ciclo; nenhuma chamada a provedor de modelo do navegador (DoD linha 9) — o contraexemplo da linhagem está medido na spec (F-08). |

**Sem violações.** Três "não aplicável" (P3, P4, P5), todos consequência da fronteira
herdada do protótipo descartável e todos com data de volta: ciclos 003 e 004.

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita a resolver por experimento: a forma do canvas/tabela está na linhagem (F-02 da spec), a norma de tema e embarque no guia e no Anexo B (F-04, F-09) — tudo lido, com linha citada. O que é incógnita de verdade (densidade em 420px) se responde **vendo o protótipo**, que é o ciclo inteiro. |
| `data-model.md` | `ART:data-model=no` | Protótipo descartável não tem modelo de domínio (condição 2, F-01 da spec). Os modelos nascem nas specs de módulo, seção "Entidades e modelo de domínio". |
| `contracts/` | `ART:contracts=no` | Diferença deliberada em relação à irmã, que declarou `yes` no ciclo análogo: o catálogo dela nascia junto do protótipo; o nosso catálogo `toc.*` tem ciclo próprio (006) e os parâmetros de admissão são do esqueleto (003). Declarar contrato aqui duplicaria função que o roadmap já deu a outro ciclo (Princípio VI) — o custo aceito está em L-03 da spec. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável (11 linhas com comando e valor esperado); o mínimo de acessibilidade está no RI-14. Uma lista adicional seria a mesma função duas vezes. |
| `ux-design.md` | `ART:ux-design=yes` | O ciclo é inteiro sobre tela: **papel semântico antes de componente** é regra do modelo operacional, não preferência. É onde cada objeto declara `ai_visible` com padrão **não visível** — decisão de segurança tomada antes de existir pixel, para o snapshot do ciclo 006 nascer por lista de permissão. |

## Como

### Fase 1 — Semântica antes de pixel (bloqueia a fase 2)

1. **`ux-design.md`**: papel semântico, estados obrigatórios e `ai_visible` de cada
   objeto de tela da spec (§ Entidades) — cada `sim` com justificativa escrita.
2. **Fixture sintética** em `prototipo/dados/`: o dilema e a ARA da "Instituição
   Horizonte", com os estados de validação de UDE **já resolvidos no dado** (nenhum
   cálculo no protótipo).

### Fase 2 — O protótipo descartável

3. Esqueleto em `prototipo/`, satisfazendo as quatro condições (F-01 da spec); tokens dos
   dois temas; adaptador falso do handshake devolvendo o envelope do guia (F-05).
4. Canvas + vista tabular com alternância sem perda (RI-01..RI-05).
5. Telas de ARA e NC com a forma canônica (RI-11..RI-13 — a visão conflito+solução é o
   "sai primeiro" se o apetite estourar).
6. Casca de hospedeiro local com iframe: modo só-conteúdo, tema do inquilino por cima com
   fallback, duas larguras (RI-06..RI-10).

### Fase 3 — A prova

7. Script versionado de captura; capturas determinísticas (mesma fixture, relógio
   congelado), regeneráveis byte-idênticas.
8. Documentos de jornada em versão de protótipo com avaliação heurística datada;
   `docs/jornadas/README.md` atualizado com o estágio de cada J-NN.
9. DoD completa executada, saídas coladas no `qa-report.md` (R1/R2), cauda de fechamento.

### Ordem e paralelismo

A fase 1 é sequencial e **bloqueia** a 2 — papel semântico antes de componente. Dentro da
fase 2, os passos 4–6 paralelizam por tela. A lição R3 da irmã vale por inteiro: escolhas
visuais do descartável são do agente (decidir, registrar, seguir); o que para no humano é
o que o roadmap já marcou — o corte de telas no gate do ciclo.

## Riscos e portões

| Risco | Ligado a | Mitigação |
|---|---|---|
| GATE-promocao — o descartável ser promovido a produção por conveniência | RF-02 | Condição 4 (apagado ou reescrito) + DoD linha 2 (`apps/` não importa de `prototipo/`; zero declarado como vácuo enquanto `apps/` não existir — R2). |
| GATE-captura-manual — captura colada à mão sob pressão de prazo | RF-03 | DoD linha 5: rodar o script duas vezes e comparar; imagem que não regenera é defeito, não evidência. |
| GATE-largura-herdada — 420px da irmã não valer para o nosso embarque | L-01 | Capturas estreitas são de protótipo e regeneram; a medição real é aptidão do ciclo 003 ("a junta fecha"). |
| GATE-proposta-tardia — a interface de propor→confirmar→executar só ser vista no 006 | L-03 | Aceito e declarado (INT-02): o custo é uma rodada de ajuste sobre build real no 006 — menor que inventar um catálogo sem spec agora. |
| GATE-dado-real — dado de pessoa escorregar para fixture ou captura | RNF-01 | DoD linha 4 + TAIL:security com esta instrução explícita; a regra é constitutiva (ADR 0006) e está no `CLAUDE.md` que todo agente lê primeiro. |

## Verificação (DoD)

A tabela executável completa está na spec (§ Critérios de aceite, 11 linhas). Resumo do
que fecha o ciclo quando ele rodar:

| Comando | Saída esperada |
|---|---|
| `test -f specs/002-prototipo-de-interfaces/ux-design.md` | código 0 |
| script de captura, duas execuções sobre o mesmo build + `diff -r` | diferença vazia (byte-idênticas) |
| conferência de capturas órfãs | toda imagem citada por exatamente uma jornada, contagem na saída (R2) |
| `grep -rniE "GoogleGenAI\|api_key\|apiKey" prototipo/ \| wc -l` | `0` |
| `scripts/check-caminhos.sh` | código 0, dizendo quantos caminhos conferiu (R2) |
| `scripts/check-conformance.sh 002` | código 0 |
