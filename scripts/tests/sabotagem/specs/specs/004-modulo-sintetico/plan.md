# Plan 004 — Módulo sintético (fixture)

> Siglas: ADR — Architecture Decision Record (Registro de Decisão Arquitetural) · DoR —
> Definition of Ready (definição de pronto para começar) · DoD — Definition of Done
> (Definição de Pronto) · TDD — Test-Driven Development (desenvolvimento guiado por teste).

Plano sintético: existe para o portão `check-specs.sh` ter uma entrada válida com as
**duas** tabelas de Constitution Check e os cinco artefatos condicionais declarados.

## Constitution Check (governance/principles.md)

| Princípio | Conformidade |
|---|---|
| I. Spec-driven | ✅ A spec sintética existe antes deste plano, na ordem que o método exige. |
| II. Human-governed orchestration | ✅ O fixture não decide nada; a decisão fica com o gate humano do ciclo real. |
| III. Reversibility / risk gates | ✅ Tudo aqui é arquivo de teste, reversível com um `git revert`. |
| IV. Test-first / verifiable DoD | ✅ Este fixture **é** o teste: sem ele o portão não prova que aceita o certo. |
| V. Context economy / boundary | ✅ Fixture mínimo de propósito — o menor que ainda exercita todas as invariantes. |
| VI. Living artifacts | ✅ Consumido por `scripts/tests/run-sabotagem.sh` a cada execução; sem consumidor seria lixo. |
| VII. Light governance / YAGNI | ✅ Nenhuma seção além das que o portão confere; nada de spec de mentira "realista". |
| VIII. Intelligible communication | ✅ Bloco de siglas no topo de cada artefato do fixture, como nos artefatos reais. |

### Project Constitution Check (governance/constitution.md — ADR 0001)

| Princípio | Conformidade |
|---|---|
| P1. Fronteira de escrita | ✅ Só este repositório; o fixture não toca em repositório algum de fora. |
| P2. Federação por contrato | ✅ Não aplicável por conteúdo, e dito por extenso: fixture não atravessa fronteira. |
| P3. Domínio puro (DDD + hexagonal) | ✅ Nenhum código de produção nasce aqui; nada a violar. |
| P4. TDD | ✅ É a forma pura do P4: o fixture existe antes de o portão poder ser declarado pronto. |
| P5. Observabilidade de nascença | ✅ A observabilidade do portão é a saída que ele imprime, com denominador (regra R2). |
| P6. Jornada viva | ✅ Não aplicável: fixture não tem tela, e isso está escrito em vez de omitido. |
| P7. Segredo nunca no cliente | ✅ Nenhuma credencial, chave ou dado real de pessoa neste fixture (ADR 0006). |

**Sem violações.**

## Artefatos deste ciclo (declare todos os cinco — silêncio não é decisão)

| Artefato | Declaração | Por quê |
|---|---|---|
| `research.md` | `ART:research=no` | Não há incógnita: o formato é o que o portão confere. |
| `data-model.md` | `ART:data-model=no` | Fixture não tem modelo de domínio persistido. |
| `contracts/` | `ART:contracts=no` | Fixture não define interface para ninguém. |
| `checklist.md` | `ART:checklist=no` | A DoD da spec já é executável; lista adicional duplicaria função. |
| `ux-design.md` | `ART:ux-design=no` | Fixture não tem tela. |

## Decisões de arquitetura do módulo

1. O fixture é base **válida**, e a sabotagem é aplicada sobre uma cópia — assim o mesmo
   arquivo prova o verde e o vermelho.

## Gates (DoR / DoD)

- **DoR**: as quatro invariantes de `check-specs.sh` cobertas por pelo menos uma sabotagem.
- **DoD**: `scripts/tests/run-sabotagem.sh` verde.
