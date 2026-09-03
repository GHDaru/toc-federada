# ADR 0002 — Stack herdada da irmã: React + TypeScript/Vite, FastAPI/Python, PostgreSQL Neon próprio, S3 atrás de porta, OpenTelemetry, Vercel + Railway

- **Status**: Aceita
- **Data**: 2026-09-03 · **Ciclo**: 001
- **Decisor**: agente construtor do ciclo 001, sob a regra R3 (decisão registrada;
  confirmação no gate humano do ciclo 001)
- **Sucede**: nenhum
- **Princípios tocados**: **P3** (a porta de armazenamento é a forma hexagonal da
  decisão), **P5** (OpenTelemetry entra como parte da stack, não como acessório), **P7**
  (deploy separa cliente e servidor — segredo só no segundo). Nenhum é emendado; os três
  são implementados.

## Contexto

Este ADR (Architecture Decision Record, registro de decisão arquitetural) fixa a stack da
aplicação de Teoria das Restrições (TOC). A irmã `gestaodeprioridades` já decidiu a dela
por ADR próprio e já pagou as decisões de deploy:

- `/home/user/gestaodeprioridades/docs/adr/0002-stack-e-arquitetura.md` 🟢 — React,
  FastAPI, Postgres Neon, storage compatível com S3;
- `/home/user/gestaodeprioridades/docs/adr/0018-onde-a-aplicacao-e-publicada.md` 🟢 —
  Vercel para a interface, Railway para o serviço;
- `gestaodeprioridades/CLAUDE.md:94` 🟢 — *"PostgreSQL Neon (banco, **esquema próprio**)"*.

A fundação `ghdaru` publica exemplos de adaptador para **ler, nunca copiar por atalho**.
Medidos:

```text
$ wc -l /home/user/ghdaru/apps/api/src/ghdaru_api/documents/ports/storage.py \
        /home/user/ghdaru/apps/api/src/ghdaru_api/documents/adapters/s3_compat.py
  16 /home/user/ghdaru/apps/api/src/ghdaru_api/documents/ports/storage.py
  89 /home/user/ghdaru/apps/api/src/ghdaru_api/documents/adapters/s3_compat.py
 105 total
```

## Decisão

1. **Interface**: React + TypeScript com Vite.
2. **Serviço**: FastAPI/Python — domínio e aplicação puros, efeito só por porta (P3),
   `import-linter` como função de aptidão.
3. **Banco**: PostgreSQL no Neon, em **projeto Neon próprio** — um passo além da irmã,
   que usa esquema próprio num banco compartilhado (`gestaodeprioridades/CLAUDE.md:94` 🟢).
   Projeto próprio isola credencial, ciclo de migração (Alembic) e raio de desastre por
   aplicação, que é o que "repositório, serviço e banco próprios" (ADR 0003) exige.
4. **Armazenamento de arquivos**: compatível com S3, **atrás de porta** — a porta de
   referência da fundação tem 16 linhas (medição acima); a nossa nasce no mesmo espírito,
   escrita aqui.
5. **Observabilidade**: OpenTelemetry desde a primeira funcionalidade (P5).
6. **Deploy**: Vercel (interface) + Railway (serviço), em eTLD+1 (domínio registrável)
   **distinto** do hospedeiro — a exigência de site distinto é do ADR 0003, que governa a
   federação; aqui entra só a escolha dos provedores, herdada do ADR 0018 da irmã.

Mudar qualquer item exige ADR novo que suceda este.

## Alternativas consideradas — descartadas com número

- **Stack nova (ex.: Node/Next.js no serviço).** Descartada: jogaria fora **105 linhas**
  de adaptador de referência legível na fundação (medição acima), **2 ADRs** de stack e
  deploy já decididos e operados pela irmã (0002 e 0018 de lá), e a simetria que permite
  ao mesmo Product Steward operar as duas aplicações com um só vocabulário técnico.
- **Compartilhar o serviço da irmã (um backend para dois produtos).** Descartada: a
  admissão federada é **por aplicação** — o manifesto exige `app_id` próprio e as ações
  levam o namespace no identificador (`<ns>.<id>`,
  `protocolos/padrao/anexo-b-federacao.md:111` 🟢; *"`app_id` | sua identidade no
  manifesto e prefixo das suas ações | **recuse subir**"*,
  `ghdaru/docs/integration/guia-desenvolvedor-app-federada.md:162` 🟢). Dois produtos num
  processo acoplariam dois ciclos de release numa fronteira que o contrato trata como duas.
- **Armazenamento direto, sem porta.** Descartada: o custo da porta, medido na referência,
  é **16 linhas** (`ghdaru/.../ports/storage.py`, `wc -l` acima). Violar o P3 para
  economizar 16 linhas não é economia.

## Consequências

- (+) Vocabulário técnico único entre as duas aplicações federadas; exemplos de adaptador
  prontos para ler na fundação.
- (+) Projeto Neon próprio: revogar, migrar ou apagar esta aplicação não toca dado de
  nenhuma outra.
- (−) **Projeto Neon próprio custa uma conta/projeto a mais para operar** (credencial,
  billing, monitoramento separados) — o preço do isolamento, pago pelo Product Steward.
- (−) Herdar a stack herda também os limites dela: fila, tempo real e busca textual não
  têm componente decidido; quando um módulo precisar, será ADR novo, não improviso.

## O que este ADR NÃO decide

- A arquitetura interna dos módulos (bounded contexts) — é matéria de
  `docs/produto/modulos.md` e das specs de cada ciclo.
- O desenho da fronteira federada (iframe, introspecção, manifesto) — ADR 0003.
- Versões exatas de framework e biblioteca — ficam no lockfile, e congelá-las em ADR
  seria duplicar função já servida (princípio VI do método).
- O provedor de armazenamento concreto (a porta permite decidir por ambiente).

## Registro

- `docs/governance/constitution.md` — P3, P5, P7, que esta stack implementa
- `/home/user/gestaodeprioridades/docs/adr/0002-stack-e-arquitetura.md` e
  `/home/user/gestaodeprioridades/docs/adr/0018-onde-a-aplicacao-e-publicada.md` — a herança
- `ghdaru/apps/api/src/ghdaru_api/documents/ports/storage.py` e
  `ghdaru/apps/api/src/ghdaru_api/documents/adapters/s3_compat.py` — as referências medidas
