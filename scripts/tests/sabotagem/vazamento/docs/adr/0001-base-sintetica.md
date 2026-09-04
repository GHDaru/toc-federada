# ADR 0001 — Base sintética desde o dia 1 (base válida de sabotagem)

- **Status**: Aceita
- **Data**: 2026-09-04 · **Ciclo**: 001
- **Sucede**: nenhum
- **Princípios tocados**: **P7** — o princípio fala de segredo técnico; este ADR
  (Architecture Decision Record, registro de decisão arquitetural) estende o espírito ao
  dado pessoal.

## Contexto

A base real da irmã foi **medida** para justificar esta decisão — contagens apenas, nenhum
dado copiado. É este bloco que o critério antigo confundia com vazamento, e é por isso que
ele existe aqui: a base válida tem de continuar verde com ele dentro.

```text
$ python3 - <<'EOF'
import json
d = json.load(open('/home/user/gestaodeprioridades/prototipo/dados/fixture.json'))
print('tarefas:', len(d['tarefas']))
print('valores distintos em responsavel:', len({t.get('responsavel') for t in d['tarefas']}))
EOF
tarefas: 114
valores distintos em responsavel: 6
```

## Decisão

Nenhum dado real de pessoa entra neste repositório: nem nome, nem enunciado de trabalho,
nem data de desempenho. Persona é papel fictício; organização é inventada.
