# Parâmetros de admissão — o que a aplicação exige para subir

> Siglas: **APH** — Aplicação ↔ Harness (o padrão da fronteira) · **TOC** — Teoria das
> Restrições · **ADR** — Architecture Decision Record (Registro de Decisão Arquitetural)
> · **TTL** — Time To Live (tempo de vida) · **URL** — Uniform Resource Locator ·
> **OTel** — OpenTelemetry.
>
> Contrato do lado **aplicação** do §B.4 do Anexo B (`GHDaru/protocolos`,
> `padrao/anexo-b-federacao.md:85-99`). Modelado no contrato da irmã
> (`gestaodeprioridades/specs/002-prototipo-de-interfaces/contracts/parametros-de-admissao.md`),
> com duas diferenças deliberadas: os **nomes seguem o §B.4** (a irmã escreveu o dela
> antes de o §B.4 existir — `GHDARU_BASE_URL` lá é `HOST_BASE_URL` aqui) e a **credencial
> de introspecção entrou** (a fundação passou a autenticar o chamador na spec 047 dela,
> depois do contrato da irmã). Os códigos de recusa são nossos.

## Regra

A aplicação **não pergunta**. Ela **exige na partida** e **recusa-se a subir** se faltar
qualquer parâmetro obrigatório, com erro categorizado que diz **qual** faltou (§B.4.1).
Falha de admissão é falha de configuração, e falha de configuração precisa ser
barulhenta: código de saída diferente de zero, código de recusa na última linha do log,
nenhuma porta aberta.

O que **nunca** acontece: subir pela metade, funcionar até alguém clicar, descobrir a
origem do hospedeiro em runtime (origem descoberta é origem *dita* — §B.2.3), ou
perguntar ao usuário o que a operadora deveria ter configurado.

## Os parâmetros

Os quatro primeiros são os do §B.4 do Anexo B — a Administradora do tenant os copia do
bloco "Contrato de admissão" no painel da fundação (Administração → Aplicações
federadas). Os dois últimos são exigência **nossa**, além do §B.4, e estão marcados.

| Parâmetro | Origem | Obrigatório | Para quê | Erro na ausência |
|---|---|---|---|---|
| `HOST_ORIGIN` | ambiente | sim (§B.4) | Origem do shell: conferida em **todo** `postMessage` recebido e usada como `targetOrigin` em todo emitido | `ADMISSAO_HOST_ORIGIN_AUSENTE` |
| `HOST_BASE_URL` | ambiente | sim (§B.4) | Introspecção (`POST /auth/introspect`), perfil, auditoria | `ADMISSAO_HOST_BASE_URL_AUSENTE` |
| `APP_ID` | ambiente | sim (§B.4) | Identidade no manifesto e prefixo das ações (`toc.*` — ADR 0003); esperado `toc` | `ADMISSAO_APP_ID_AUSENTE` |
| `EMBED_URL` | ambiente | sim (§B.4) | Ponto de montagem declarado no manifesto; a URL servida tem de pertencer à `origin` declarada (§B.1.3) | `ADMISSAO_EMBED_URL_AUSENTE` |
| `TOC_APP_CREDENTIAL` | ambiente | sim (**nossa**) | Credencial `ghd_…` emitida na admissão; autentica a aplicação no introspect (spec 047 da fundação). Segredo de servidor: **nunca** no bundle | `ADMISSAO_CREDENCIAL_AUSENTE` |
| `DATABASE_URL` | ambiente | sim (**nossa**) | Banco Neon próprio (E8.1); também seleciona o backend da factory de persistência | `ADMISSAO_DATABASE_URL_AUSENTE` |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | ambiente | não | Exportação de traço/métrica; ausente ⇒ exportador nulo e **registro** de que está nulo | — |
| ambiente de teste da fundação | operadora | não (§B.4: "DEVE ser oferecido") | Exercitar a junta sem produção | — não impede subir; ausência vai à [DÚVIDA] 4 da spec |
| `token` (grant `ghdg_…`) | `ghd.handshake` | sim | Trocado **imediatamente** por identidade na introspecção; uso único, TTL ≤ 120 s; **nunca confiado, nunca bearer** | `HANDSHAKE_SEM_TOKEN` |
| `tenant` | `ghd.handshake` | sim | Exibição enquanto a introspecção corre; a fronteira de isolamento real é o `tenant_id` **da resposta de introspecção** | `HANDSHAKE_SEM_TENANT` |
| `capabilities` | introspecção | sim | A única fonte de autorização, **fora** do modelo de linguagem (P2) | `INTROSPECCAO_SEM_CAPABILITIES` |
| `theme.tokens` | `ghd.handshake` | não | Marca do inquilino como variáveis CSS, por lista de permissão | — usa o tema próprio e **registra** que usou |

## Erros de fronteira, além da admissão

| Situação | Código | Comportamento |
|---|---|---|
| `ev.source !== window.parent` | `FONTE_NAO_ADMITIDA` | Descarta **sem processar**, registra (sem payload), conta em métrica, não responde |
| `ev.origin` ≠ `HOST_ORIGIN` (inclui `"null"`) | `ORIGEM_NAO_ADMITIDA` | Idem — e a origem esperada vem **daqui**, nunca de campo de payload (contraexemplo registrado na norma: `payload.host_origin`) |
| Envelope fora de `{protocol:"ghd", v:1, type, payload}` | `ENVELOPE_INVALIDO` | Ignora sem resposta (responder confirma presença — §B.2.1); registra |
| Introspecção devolve `{active: false}` | `GRANT_INATIVO` | Nenhum dado renderizado; estado com ação "recarregar pelo shell". Sem distinguir expirado × consumido × inexistente — a resposta não distingue (§B.6.5) |
| Introspecção indisponível (rede, 5xx) | `FUNDACAO_INDISPONIVEL` | Falha **fechada** e explícita, com "tentar de novo" — nunca silenciosa, nunca presumindo válido |
| Fundação responde 401 à nossa credencial | `CREDENCIAL_RECUSADA` | Registra, sinaliza rotação à Administradora do tenant, **sem retry automático** (o 401 é uniforme por desenho e não diz o caso) |
| `expires_at` do principal vencido | `SESSAO_EXPIRADA` | Encerra a sessão embarcada; novo embarque, nunca renovação por conta própria |
| Capability faltando para a operação | `CAPABILITY_INSUFICIENTE` | A operação não é oferecida (ausência é melhor fronteira que recusa — §B.7.3); no ciclo 006, a ação **não entra no catálogo** que a IA vê |

## O que verificamos, e o que não podemos verificar

**Verificável por teste neste ciclo** (DoD 1–7 da spec): cada ausência produz o código
certo e exit ≠ 0; fonte errada, origem errada e envelope divergente são descartados sem
resposta; token inativo não renderiza; falha fechada com a fundação fora do ar.

**Verificável só contra a fundação real** (DoD 12): que o bloco "Contrato de admissão"
do painel entrega estes nomes nesta forma, e que a nossa credencial é aceita. Diferente
da irmã — cujo contrato era proposta unilateral sob a lacuna L5 de então — o §B.4 já
existe como norma bilateral; o que resta em aberto aqui são os bloqueios L-01/L-02 da
spec (schemas de manifesto e fatia desligada), não a forma dos parâmetros.
