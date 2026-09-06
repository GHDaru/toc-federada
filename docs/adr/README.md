# Registros de Decisão Arquitetural (ADR)

Um ADR (do inglês *Architecture Decision Record*) é **imutável**: seu mérito nunca é
editado. Mudou de ideia? Um ADR novo **sucede** o anterior, e o anterior ganha
"Superseded by". O registro é a memória do projeto — editá-lo apaga a memória.

Todo ADR deste projeto declara o campo **"Princípios tocados"** — com `nenhum` escrito
por extenso quando for o caso (regra R3, quarta condição; a lição do ADR 0011→0016 da
irmã `gestaodeprioridades`) — e entra no índice consultável via
`scripts/record-decision.sh`. A coerência entre este índice, os arquivos e os status é
verificada por `scripts/check-adr.sh`.

| ADR | Título | Status | Princípios tocados | Data |
|---|---|---|---|---|
| 0001 | [Constituição própria do projeto (P1–P7) e herança das regras R1–R5 da irmã](0001-constituicao-propria-e-heranca-das-regras.md) | Aceita | todos (constitutivo) | 2026-09-03 |
| 0002 | [Stack herdada da irmã: React + TypeScript/Vite, FastAPI/Python, Neon próprio, S3 atrás de porta, OpenTelemetry, Vercel + Railway](0002-stack-herdada-da-irma.md) | Aceita | P3, P5, P7 | 2026-09-03 |
| 0003 | [Federação pelo Padrão APH: Nível 2 (Operador), `mode: embedded`, `app_id: toc`, identidade por introspecção, site distinto](0003-federacao-aph-nivel-2-embedded.md) | Aceita | P2 (INEGOCIÁVEL), P1 | 2026-09-03 |
| 0004 | [Taxonomia de planejamento (Módulo ⊃ Épico ⊃ Feature ⊃ Story) e absorção da reversa sem instalar o framework](0004-taxonomia-de-planejamento-e-absorcao-da-reversa.md) | Aceita | P1 | 2026-09-03 |
| 0005 | [Escopo do domínio v1: processos de pensamento completos + focalização; DBR e contabilidade de ganho fora](0005-escopo-do-dominio-v1.md) | Aceita | nenhum | 2026-09-03 |
| 0006 | [Base sintética desde o dia 1: nenhum dado real de pessoa em fixture, captura, spec ou exemplo](0006-base-sintetica-desde-o-dia-1.md) | Aceita | P7 | 2026-09-03 |
| 0007 | [Inteligência artificial somente pela fundação: sem SDK de provedor, chave nunca no cliente, prompts no servidor](0007-ia-somente-pela-fundacao.md) | Aceita | P2, P7 (INEGOCIÁVEIS) | 2026-09-03 |
| 0008 | [Site de produto gerado por script versionado, nunca escrito à mão](0008-site-de-produto-gerado-por-script.md) | Aceita | P6 | 2026-09-03 |
| 0009 | [A interface decide proposta por `/toc/propostas`: mesma máquina de estados, mesmo traço, projeção estruturada](0009-superficie-de-proposta-para-a-interface-da-aplicacao.md) | Aceita | P2 (INEGOCIÁVEL) | 2026-09-06 |
| 0010 | [Trava otimista por versão lida: a escrita do agregado condiciona-se à versão que leu, e o perdedor recebe `409 VERSION_CONFLICT`](0010-trava-otimista-por-versao-lida.md) | Aceita | P2 (INEGOCIÁVEL), P3, P4 | 2026-09-06 |
| 0011 | [A confirmação de proposta é uma transição atômica no banco, e a `idempotency_key` deduplica de verdade](0011-trava-da-proposta-e-dedup-real-da-chave.md) | Aceita | P2 (INEGOCIÁVEL), Maestro III (INEGOCIÁVEL), P3, P4, P5 | 2026-09-06 |
| 0012 | [O M4 nasce com o pacote de suficiência **extraído** e a referência cruzada como **agregado próprio**](0012-modulo-m4-suficiencia-compartilhada-e-referencia-como-agregado.md) | Aceita | P2 (INEGOCIÁVEL), P3, P4, P5 | 2026-09-06 |
| 0013 | [A restrição tem taxonomia **fechada**, e uma decisão herdada "mantida" **volta à mesa** a cada recomeço](0013-taxonomia-fechada-da-restricao-e-heranca-que-volta-a-mesa.md) | Aceita | P3, P4, P2 (INEGOCIÁVEL, alcance estreito declarado no ADR) | 2026-09-06 |
