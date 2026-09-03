# Tasks 004 — Módulo sintético (fixture)

> Siglas: DoD — Definition of Done (Definição de Pronto); TAIL — a cauda de fechamento do
> ciclo (revisão · segurança · mutação · gate).

- [ ] T-01 — Manter este fixture mínimo. · Dep: nenhum · Ref: `spec.md` ·
  Aceite: `scripts/check-specs.sh scripts/tests/sabotagem/specs` sai 0.
- [ ] T-02 — `TAIL:review` — revisão independente em contexto fresco por quem não escreveu.
- [ ] T-03 — `TAIL:security` — passe de segurança: nenhum segredo e nenhum dado real de
  pessoa no fixture.
- [ ] T-04 — `TAIL:mutation` — sabotar e ver reprovar: `scripts/tests/run-sabotagem.sh`.
- [ ] T-05 — `TAIL:gate` — gate humano do ciclo que adotar o portão.
