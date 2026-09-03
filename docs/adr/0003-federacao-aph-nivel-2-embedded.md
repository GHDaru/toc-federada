# ADR 0003 — Federação pelo Padrão APH: Nível 2 (Operador), `mode: embedded`, `app_id: toc`, identidade por introspecção, site distinto do hospedeiro

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: Product Steward (toca princípio INEGOCIÁVEL — quarta condição da R3)
- **Sucede**: nenhum
- **Princípios tocados**: **P2 (INEGOCIÁVEL)** — este ADR (Architecture Decision Record,
  registro de decisão arquitetural) é a decisão que o P2 referencia; o alcance do P2 está
  declarado **no próprio texto do princípio** desde a versão 1.0.0 da constituição, lição
  paga pela irmã no ciclo ADR 0011→0016 de lá (decidir matéria de princípio inegociável
  sem citá-lo custou uma emenda constitucional). Toca também **P1** de lado: `mode:
  embedded` é o que mantém todo o código desta aplicação dentro desta fronteira de escrita.

## Contexto

Esta é a **segunda aplicação candidata à federação** da plataforma `GHDaru/ghdaru`. A
fronteira entre aplicação e hospedeiro é governada pelo padrão **APH — Aplicação ↔
Harness** (`GHDaru/protocolos`), que define três níveis 🟢:

```text
$ grep -n 'Nível' protocolos/padrao/padrao-aph.md | sed -n '2,4p'   # a tabela de níveis
52:| **Nível 1** | Observador | vê a tela e responde com contexto | ...
53:| **Nível 2** | Operador | age sobre a aplicação com governança | Nível 1 + §4.2 completo, §4.4, §4.5, §4.6, §4.7 completo, §4.8 |
54:| **Nível 3** 🧪 | Federado *(nível experimental)* | integra apps de terceiros no mesmo contrato | Nível 2 + §4.9 |
```

A norma diz que *"uma aplicação que 'conversa integralmente' no sentido deste padrão é
**Nível 2 (Operador)**. O Nível 3 é para plataformas"*
(`protocolos/padrao/padrao-aph.md:64` 🟢). O checklist de autodeclaração, medido:
**11** caixas no Nível 1 (linha 192), **19** na linha própria do Nível 2 — 10 obrigatórias
e 9 recomendadas (linha 194) —, **7** adicionais no Nível 3 (linha 196):

```text
$ for l in 192 194 196; do printf "linha %s: " $l; \
    sed -n "${l}p" protocolos/padrao/padrao-aph.md | grep -o '\[ \]' | wc -l; done
linha 192: 11
linha 194: 19
linha 196: 7
```

O manifesto de federação declara **modo**, não número — e `internal` fica explicitamente
fora do Anexo B: *"internal = aplicacao propria da plataforma, que compartilha runtime e
por isso esta FORA do Anexo B (sem fronteira de origem); embedded = app de terceiro no
shell"* (`protocolos/padrao/schemas/federacao-manifesto.schema.json:45` 🟢; o enum com
`embedded` está na linha 42). A rota de identidade chama-se introspecção — a norma
renomeou `endpoints.validate_token` → `endpoints.introspect` e apertou `screen.id` e
`action_id` para a forma `<ns>.<id>` (`protocolos/padrao/anexo-b-federacao.md:111` 🟢).
O guia da fundação exige os parâmetros de admissão *"por configuração (variável de
ambiente ou equivalente), **nunca** [no código]"*
(`ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:154` 🟢) e manda **recusar
subir** sem `app_id` (`:162` 🟢).

## Decisão

1. **Alvo de conformidade: Nível 2 (Operador)** do padrão APH, **lado aplicação** do
   Anexo B — e a declaração de conformidade dirá sempre **de qual lado** e com que
   maturidade, porque o lado aplicação não tem suíte executável (ver consequência
   negativa).
2. **`mode: embedded`**: a aplicação roda em repositório, serviço e banco próprios e é
   embutida no shell do `ghdaru` por iframe. Nunca `internal` — `internal` está fora do
   Anexo B e exigiria escrever dentro do `ghdaru`, violando o P1.
3. **Identidade**: `app_id: toc` no manifesto; **nenhum login próprio** — toda identidade
   chega por `POST /auth/introspect` contra a fundação, e token é **validado por
   introspecção, nunca confiado**. Os quatro parâmetros de admissão (origem da fundação,
   `app_id`, endpoint de introspecção, credencial de serviço) entram **por configuração**
   e a aplicação **recusa subir** sem eles (fail-fast), conforme o guia 🟢.
4. **Namespace**: telas e ações levam o prefixo `toc.` na forma `<ns>.<id>` exigida pelo
   schema (`anexo-b-federacao.md:111` 🟢) — ex.: `toc.projetos`, `toc.criar_no`.
5. **Origem**: a aplicação é servida de **site distinto (eTLD+1, domínio registrável)**
   do hospedeiro, com `targetOrigin` dirigido e verificação de `event.origin` **e**
   `event.source` — os requisitos de embarque da norma (`padrao-aph.md:196` 🟢). Os
   provedores concretos são o ADR 0002.
6. **Governança de mutação**: verbo mutador nasce `action_proposal`; a máquina de estados
   da proposta é uma só e do servidor; tela é dado e nunca instrução — o detalhamento por
   módulo é a spec do M7 (`specs/` do roadmap, ciclos 003 e 006).

## Alternativas consideradas — descartadas com número

- **Ficar no Nível 1 (Observador).** Descartada: o produto existe para assistência que
  **age** — sugerir Efeitos Indesejáveis (UDEs), criar nós, analisar árvores — e as
  famílias `action_proposal`/`action_result` e `ui_command` pertencem ao Nível 2
  (`padrao-aph.md:78` 🟢). As **11** caixas do Nível 1 (medição acima) não incluem
  catálogo, FSM (máquina de estados finitos) de proposta nem confirmação proporcional ao
  risco — exatamente o que a assistência da TOC (Teoria das Restrições) precisa.
- **Mirar o Nível 3 (Federado) já.** Descartada: o Nível 3 é **experimental** — *"nenhuma
  implementação o exercitou de ponta a ponta"* (`padrao-aph.md:56` 🟢) — e as suas **7**
  caixas adicionais são papel de **plataforma** (`:64` 🟢), que é o `ghdaru`, não desta
  aplicação. O lado hospedeiro é dele; o nosso lado já é coberto pelo embarque do Nível 2+
  Anexo B.
- **`mode: internal` (rodar dentro do ghdaru).** Descartada: o schema declara `internal`
  **fora do Anexo B** (`federacao-manifesto.schema.json:45` 🟢) — sem fronteira de origem
  não há contrato a cumprir — e todo o código viveria no repositório da fundação, que o
  P1 declara somente-leitura. A irmã tomou a mesma decisão pelo mesmo motivo (ADR 0003 de lá).

## Consequências

- (+) O contrato inteiro da fronteira já está escrito e versionado em `GHDaru/protocolos`;
  nada de segundo protocolo.
- (+) Repositório, serviço e banco próprios: o raio de qualquer defeito nosso para com o
  hospedeiro é o iframe, não o processo.
- (−) **O lado aplicação do Nível 2 não tem suíte de conformidade executável** — a suíte
  cobre o Nível 1 e o lado hospedeiro (`padrao-aph.md:17` 🟢; a lacuna declarada do
  normativo na `:200` 🟢). A nossa conformidade será **autodeclaração com evidência por
  requisito** (ciclo 012 do roadmap), que é estruturalmente mais fraca que um portão
  automático — e fica dito aqui, não descoberto depois.
- (−) Site distinto custa dois domínios e a matriz de CORS/origens para manter; e o
  embarque só é testável de ponta a ponta **contra a fundação real** — o critério do
  ciclo 003 ("a junta fecha contra a ghdaru real") existe por causa disto.

## O que este ADR NÃO decide

- O desenho do catálogo `toc.*` (quais ações, com que risco e `input_schema`) — spec do
  M7, ciclo 006.
- O conteúdo do manifesto além de `app_id` e `mode` — validado contra o schema na spec de
  fronteira do ciclo 003.
- A política de sandbox do iframe além do mínimo normativo — a irmã tem decisão própria
  (`allow-same-origin` + site distinto, ADR 0017 de lá) que será reavaliada, não herdada
  às cegas.
- A autodeclaração de conformidade em si — é entrega do ciclo 012, em ADR próprio.

## Registro

- `docs/governance/constitution.md` — P2, cujo alcance nasce declarado
- `protocolos/padrao/padrao-aph.md`, `protocolos/padrao/anexo-b-federacao.md`,
  `protocolos/padrao/schemas/federacao-manifesto.schema.json` — a norma citada por linha
- `ghdaru/docs/integration/guia-desenvolvedor-app-federada.md` — o guia do lado hospedeiro
- `docs/produto/modulos.md` — M7, o módulo que implementa esta decisão
