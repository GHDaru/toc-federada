# 003 — para `GHDaru/ghdaru`: o que falta para a `toc-federada` embarcar de verdade

> Siglas deste documento: **TOC** — Teoria das Restrições; **APH** — Aplicação ↔ Harness (o
> padrão da fronteira, em `GHDaru/protocolos`); **ADR** — *Architecture Decision Record*
> (Registro de Decisão Arquitetural); **eTLD+1** — *effective Top-Level Domain plus one*, o
> "site" no sentido do navegador; **TTL** — *Time To Live* (tempo de vida). Da constituição
> deste projeto: **P1** — fronteira de escrita única; **P2** — federação por contrato;
> **P7** — segredo nunca no cliente; **R1** — verifique antes de afirmar.

- **Destino**: `GHDaru/ghdaru` — lado **hospedeiro** da junta de federação
- **Commit lido**: `b205975732616000492429e494a633e059c9bdfb` (2026-09-02, *merge: integra a
  spec 059 … épico G/G2*). `main` e a ponta lida são **o mesmo commit** — conferido com
  `git log -1 --format=%H main`. Clone lido em `/home/user/ghdaru`, **somente leitura**
- **Norma conferida contra**: `GHDaru/protocolos@04eca6d4a267358be2e2a583f8ceef22deb137f5`
  (Padrão APH v0.8, Anexo A v0.5, **Anexo B — Federação v0.4**)
- **Somas de verificação dos arquivos citados** (`md5sum`, executado em 2026-09-05):

  ```text
  0a631f94d20255c976d2c803e385d7e2  apps/api/src/ghdaru_api/http/federated_actions.py
  2b00f9e535c96d0859bf7e5871ced83d  apps/api/src/ghdaru_api/http/manifest_loader.py
  8b9ac3bb53fbbe8d1e13341afc29d38d  apps/api/src/ghdaru_api/http/federation_router.py
  c5841bb9edc1196d89e1b8da09a0bb2c  apps/api/src/ghdaru_api/http/deps.py
  4bfad810b8a6c67eecb7fcc6df38598f  apps/api/src/ghdaru_api/identity/domain/capabilities.py
  7316335a90f9dd844cc753939be3a2ee  docs/integration/README.md
  9a0f9df25c1829e828453149b32d254d  docs/integration/instrucoes-construcao.md
  5386929ba678a7c241a73f108b1b4f4d  docs/integration/guia-desenvolvedor-app-federada.md
  ```

- **Origem do achado**: preparação do ciclo 003 da `toc-federada` (esqueleto federado,
  `mode: embedded`), auditoria do lado hospedeiro contra o §4.9 do padrão e o Anexo B
- **Data**: 2026-09-05 · **Estado**: **aberta**
- **Para quem executa**: esta mensagem é auto-suficiente. Não é preciso ler o nosso
  repositório para agir sobre nenhum item.

---

## 0 · Por que esta mensagem existe, e o que ela **não** repete

O princípio **P1** da nossa constituição proíbe escrever fora de `GHDaru/toc-federada`:
lacuna encontrada em repositório de leitura vira artefato de mensagem, com evidência por
`arquivo:linha`, nunca correção silenciosa nem aviso em conversa. Somos a **segunda**
aplicação candidata à federação; a primeira (`GHDaru/gestaodeprioridades`) já lhes escreveu
a mensagem 005 dela, em 2026-08-13, lendo `ghdaru@a105a03`.

Herdar os achados da irmã **de ouvido** seria o pior uso possível deste mecanismo: mensagem
que repete achado obsoleto ensina o destinatário a não lê-la. Então tudo que ela nos passou
foi **re-medido no código de hoje**, e o placar é este:

| O que a irmã relatou | Estado em `b205975` | Onde |
|---|---|---|
| schemas de manifesto mutuamente exclusivos | **resolvido** | §1 |
| credencial `ghd_` emitida e nunca verificada | **resolvido na introspecção**, aberto na chamada de ação | §1 e **A1** |
| ação federada sem credencial ("F7 pendente") | **confirmado** | **A1** |
| grants em memória (réplica única) | **confirmado**, e o registro de admissão também | **A5** |
| `ai_actions` das telas descartado na composição | **confirmado** | **A3** |
| APH-9.4b sem interseção com o usuário | **confirmado**, com reprodução executada | **A4** |

Sete achados ao todo — os quatro herdados que sobreviveram, mais três que apareceram na
auditoria (**A2**, **A6**, **A7**).

---

## 1 · Retirado: o bloqueio nº 0 da irmã não existe mais

A mensagem 005 da `gestaodeprioridades` abria dizendo que os dois schemas de manifesto —
o golden de vocês e o normativo do Anexo B — eram **mutuamente exclusivos**, e que o
manifesto conforme ao anexo saía **REJEITADO com 4 erros** na validação de vocês. Aquilo
bloqueava o registro de qualquer aplicação conforme.

Está fechado. O golden é hoje cópia do normativo, e a única diferença é de identificação:

```text
$ diff apps/api/contracts/aph/application-manifest.schema.json \
       /home/user/protocolos/padrao/schemas/federacao-manifesto.schema.json
3,4c3
<   "$id": "https://ghdaru.tecnologia/schemas/application-manifest.schema.json",
<   "x-procedencia": "Cópia verbatim de padrao/schemas/federacao-manifesto.schema.json em GHDaru/protocolos@7bbbbfe (Anexo B — Federação v0.2). NÃO editar aqui: divergir do normativo foi o que produziu a rejeição mútua de manifestos (spec 046). Mudança de contrato entra pelo repositório da especificação.",
---
>   "$id": "federacao-manifesto.schema.json",
```

As quatro divergências quebradoras que produziram os 4 erros — `level` contra **`mode`** e
`endpoints.validate_token` contra **`endpoints.introspect`** — desapareceram junto com o
schema antigo. E o manifesto conforme ao Anexo B agora **passa**: rodamos o **validador de
vocês** (`apps/api/src/ghdaru_api/conversation/domain/manifest.py:55`) contra o manifesto
que a irmã publicou no mesmo dia da mensagem 005
(`gestaodeprioridades@d2c8451`, 2026-08-13 — `mode: embedded`, `endpoints.introspect`, as
nove ações do §3 daquela mensagem).

O roteiro é curto o bastante para caber aqui — quem quiser refazer não depende de nós:

```python
# aph-remede-l01.py — roda sem servidor, só lê o disco dos dois repositórios
import json, sys
sys.path.insert(0, "/home/user/ghdaru/apps/api/src")
from ghdaru_api.conversation.domain.manifest import validate_manifest

alvo = "/home/user/gestaodeprioridades/specs/003-roadmap-e-rounds/contracts/manifesto.json"
erros = validate_manifest(json.load(open(alvo)))
print("erros:", len(erros), "| veredito:", "ACEITO" if not erros else "REJEITADO")
```

```text
$ python aph-remede-l01.py
erros: 0 | veredito: ACEITO
```

Registramos isto em primeiro lugar de propósito: vocês pagaram uma spec (046) para fechar
esse buraco, e a nossa spec 003 carregava o bloqueio **L-01** de risco *alto* por causa
dele. Ele saiu da nossa lista.

**E a credencial da aplicação passou a ser verificada** — pela metade, e a metade que falta
é o A1. A irmã relatou que a `ghd_` era "emitida e nunca verificada". Hoje
`POST /auth/introspect` autentica o chamador
(`apps/api/src/ghdaru_api/http/auth_router.py:74-91` emite o 401 uniforme; `:157-158`
confere que o grant pertence ao par `(tenant_id, app_id)` **antes** do consumo, para que uma
app não queime o grant da concorrente). Isso é o **APH-9.5**, que a norma ainda lista como
🧪 sem nenhum laboratório — vocês são o laboratório.

A distinção que importa: isso resolve a direção **aplicação → fundação**, em que a app se
identifica para introspectar. A direção **fundação → aplicação**, em que vocês chamam a
nossa ação, continua sem credencial nenhuma — é o achado A1, e não é o mesmo item.

---

## 2 · O que já está certo, e é bastante

Conferido em `b205975`, para que ninguém refaça o que existe:

| O que | Onde | Contra o quê |
|---|---|---|
| Envelope canônico e "a app fala primeiro" | `apps/web/src/features/federation/domain/handshake.ts:47-51` (descarta o que não vier do `contentWindow` **e** da origem admitida) e `:52-57` (só `ghd.ready` dispara handshake) | §B.2.1–§B.2.3 |
| `targetOrigin` dirigido, nunca `"*"` | `apps/web/src/features/federation/ui/FederatedFrame.tsx:98` e `:120` | §B.2.4 |
| `sandbox` correto para app genuinamente cross-origin | `FederatedFrame.tsx:171` (`allow-scripts allow-same-origin allow-forms` só com canal) e `:172` (`referrerPolicy="no-referrer"`) | APH-9.2 corrigido |
| Recusa de embarque same-origin e não-https | `apps/web/src/features/federation/domain/frame.ts:71,73` | §B.1.2/§B.1.3 (espelho no cliente) |
| Recusa de origem **same-site**, com "não sei" fechando | `apps/api/src/ghdaru_api/http/manifest_loader.py:99-135` — sem `FEDERATION_HOST_SITE` **nenhuma** origem é admitida | §B.1.2 |
| Grant próprio do embarque: prefixo `ghdg_`, TTL curto, uso único **atômico** | `apps/api/src/ghdaru_api/identity/application/use_cases.py:100-109` e `:164-167` (`pop`); repositório em `apps/api/src/ghdaru_api/identity/adapters/in_memory.py:76-80` | APH-9.4a |
| Grant sem `role`, e `{active:false}` que não distingue os casos | `apps/api/src/ghdaru_api/http/auth_router.py:175-185` | §B.6.3–§B.6.5 |
| Contrato de admissão publicado, com os quatro parâmetros do §B.4 | `apps/api/src/ghdaru_api/http/admission.py:75-89`, servido em `GET /admin/federated/{id}/admission-contract` | §B.4.4 |
| Mudança de parâmetro do contrato = mudança de admissão (fail-closed) | `apps/api/src/ghdaru_api/http/manifest_loader.py:149,157-170` (`admission_fingerprint`) | §B.4.2 |
| Rota canônica, reservada e ocupada recusadas **na admissão**, nomeando a rota | `apps/api/src/ghdaru_api/http/admin_router.py:184-234` | §B.10.1/§B.10.2 |
| Rede de runtime para a colisão que a admissão não alcança | `apps/api/src/ghdaru_api/http/manifest_loader.py:247-248` | §B.10.3 |

Nada disso é pouco: é a metade do Anexo B que só o hospedeiro pode entregar, e ela está
entregue. O que segue é o que falta.

---

## 3 · Auditoria do lado hospedeiro — placar por requisito

Nível alvo: **Nível 3 (Federado)** do §4.9, para uma aplicação `mode: embedded`. Auditoria
**por leitura**, com o alcance declarado no fim da seção.

| Req. | O que exige | Status | Evidência / lacuna |
|---|---|---|---|
| APH-9.1 | manifesto declarativo validável | ✅ | `apps/api/src/ghdaru_api/conversation/domain/manifest.py:55-58` valida contra o golden; `apps/api/src/ghdaru_api/http/admin_router.py:334-340` exige `origin` idêntico ao admitido (anti-spoof) e nunca grava parcial |
| §B.5.4 (1) | `url` de embarque pertence à `origin` declarada | ✅ | `apps/api/src/ghdaru_api/http/manifest_loader.py:185-195` (`_valid_embed`) |
| §B.5.4 (2) | origem de **site distinto** do hospedeiro | ✅ | `apps/api/src/ghdaru_api/http/manifest_loader.py:121-134` |
| §B.5.4 (3) | namespace de `screen.id`/`action_id` exclusivo da aplicação | ❌ | `_conflito_de_app_id` (`admin_router.py:239-248`) confere só o `app_id`. Busca por `namespace` em `admin_router.py`, `manifest_loader.py` e `apps/api/src/ghdaru_api/conversation/domain/manifest.py`: nenhuma verificação de prefixo. Achado **A6** |
| APH-9.2 | iframe + envelope tipado + origem dos dois lados + token por introspecção | ✅ (lado hospedeiro) | linhas da tabela do §2 |
| APH-9.3 | projeção MCP stateless | ⏳ | existe (`apps/api/src/ghdaru_api/http/mcp_projection.py`, ADR 0024); não exercitada por nós — `mode: embedded` não a usa |
| APH-9.4a | credencial própria do embarque, vida curta, uso único, nunca a sessão | ✅ | `use_cases.py:100-109`, `:164-167` |
| **APH-9.4b** | autoridade efetiva = `capabilities(usuário) ∩ concessão(app, tenant)`, aplicada fail-closed por rota, com a app atuante no traço | ❌ | `apps/api/src/ghdaru_api/http/federation_router.py:62` chama `granted_capabilities(app)`; `manifest_loader.py:206-212` documenta que o cálculo é `capabilities_required ∩ escopos`, "**NUNCA** as capabilities de fundação do usuário". Reproduzido no achado **A4** |
| APH-9.5 | introspecção autentica o chamador | ✅ | `apps/api/src/ghdaru_api/http/auth_router.py:74-91`, `:157-158` |
| §B.4.4 | quatro parâmetros de admissão por configuração | ✅ | `apps/api/src/ghdaru_api/http/admission.py:75-89` |
| §B.4 (5ª linha) | ambiente de teste oferecido (a tabela do §B.4 escreve **DEVE**; o §B.4.4 escreve **DEVERIA** — em qualquer leitura, não impede subir) | ⏳ | `admission.py:87` publica `FEDERATION_TEST_BASE_URL` ou `null`; se a variável está definida em algum ambiente de vocês é fato de operação, não de código — vira pergunta no §5 |
| §B.5.3 | tela com `ai_actions: []` marca item sensível e não entra no snapshot | ❌ | `ai_actions` é **campo obrigatório** do schema (`application-manifest.schema.json:127-131`) e não tem **nenhum** leitor em produção. Achado **A3** |
| §B.6.6 | introspecção autentica o chamador | ✅ | idem APH-9.5 |
| §B.6.7 | interseção com o usuário | ❌ | idem APH-9.4b |
| §B.9.1/§B.9.2 | `ghd.action_result` é palpite de interface, com escopo derivado do contexto admitido | ✅ | `handshake.ts:36-39,58-62` — o escopo sai do `context` admitido, não do `payload` |

**Placar do lado hospedeiro, Nível 3**: 15 obrigações examinadas — **9 ✅ · 4 ❌ · 2 ⏳**.
Os quatro ❌ viram os achados **A3**, **A4** e **A6** abaixo (o §B.6.7 e o APH-9.4b são a
mesma obrigação, contada nos dois lugares porque é assim que a norma a numera). O Nível 3
inteiro é 🧪 na norma, e o §B.11.3 obriga a declarar a maturidade junto com a conformidade.

Os achados **A1**, **A2**, **A5** e **A7** não aparecem na tabela, e o motivo importa:
nenhum deles é cláusula do Anexo B. O anexo especifica a junta do **embarque** — o canal,
o manifesto, o grant, a introspecção — e não diz nada sobre a chamada que o hospedeiro faz
**para dentro** da aplicação, sobre onde a convenção dessa chamada é publicada, sobre a
durabilidade do registro de admissão, nem sobre a documentação de entrada. São quatro
obrigações sem dono na norma, e as quatro nos bloqueiam.

**O que esta auditoria não alcança** — e a frase da skill que a produziu é boa: *auditoria
por leitura estima; execução calibra*. Nada aqui foi medido contra um servidor de pé. O que
só a execução resolve é a suíte do lado hospedeiro (`protocolos/conformidade/suite-federacao.mjs`),
que roda de fora contra uma URL. Quando vocês tiverem um ambiente de ensaio (§5), ela é o
juiz — e o que ela observar ganha do que esta tabela lê.

---

## 4 · Os achados

Ordenados pelo que nos bloqueia primeiro. Cada um traz **evidência**, **consequência para
quem embarca** e **sugestão separada** — para que vocês possam aceitar o diagnóstico e
recusar o remédio.

### A1 · A ação federada chega à aplicação sem credencial, sem inquilino e sem usuário — e isso, para nós, é o bloqueio central

Este é o item que a irmã chamou de "F7 pendente". Confirmado no código de hoje, e ele é
**pior do que a formulação de ouvido sugere**: não falta só a credencial.

**Evidência.** `apps/api/src/ghdaru_api/http/federated_actions.py:57-62`, o miolo do adaptador remoto:

```python
    def execute(self, action_id: str, params: dict) -> str:
        client = None
        try:
            client = self._client_factory()
            response = client.post(f"{self._origin}/aph/actions/{action_id}",
                                   json={"params": params}, timeout=self._timeout)
```

O `Protocol` do cliente (`:37-38`) **admite** `headers`, e nenhum chamador o preenche. O
corpo é `{"params": …}` e nada mais. O próprio módulo diz, na docstring (`:11`): *"Sem
credencial nesta fatia (registrado no ADR 0023; autenticação da borda federada é F7/F1)"* —
e o ADR 0023 diz o mesmo na decisão 1 (*"a chamada vai sem credencial"*) e na primeira
consequência negativa. Não estamos descobrindo nada que vocês não tenham escrito; estamos
dizendo **o que isso faz do outro lado**.

**Consequência para quem embarca.** O que chega ao nosso `POST /aph/actions/{action_id}` é
um pedido anônimo com parâmetros escolhidos por um modelo de linguagem. Dele não se extrai:
o **inquilino** (logo não há como filtrar dado por `tenant_id`), o **usuário** (logo não há
como auditar quem agiu, e o APH-9.4 exige a aplicação atuante no traço), nem **prova de que
o chamador é a fundação** (a rota é pública; qualquer um na internet a alcança).

A nossa constituição fecha o cerco: o **P2** manda identidade vir por
`POST /auth/introspect` e autorização ficar fora do modelo. Uma ação sem token não tem o que
introspectar. Portanto a única implementação **conforme** que podemos entregar hoje é
recusar toda chamada — o que significa que a metade conversacional do embarque simplesmente
não existe. Fica de pé o iframe, o handshake, o tema e a leitura; a IA da fundação não
consegue **operar** a aplicação, que é justamente o que o ADR 0007 deste projeto escolheu
como única fonte de assistência.

Vale registrar que vocês já mitigaram o que dava para mitigar de dentro:
`federated_actions.py:110-113` força `permission="ask"` e `read_only=False` em **toda** ação
federada, inclusive `risk: read`, exatamente porque a chamada vai sem credencial. É a
decisão certa, e ela também é a prova de que a lacuna é conhecida.

> **Sugestão** — separada do achado, e é de vocês decidir. A máquina já existe: o mesmo
> grant de uso único do embarque resolve a chamada de ação. Emitir um `ghdg_` por execução,
> com audiência na app e TTL de segundos, mandá-lo no `Authorization` (o `headers` do
> `Protocol` já está lá), e deixar que a aplicação o troque em `POST /auth/introspect` —
> resposta que já devolve `tenant_id`, `user`, `capabilities` e `app_id` — resolve
> credencial, identidade, inquilino e traço **de uma vez**, sem contrato novo e sem segundo
> protocolo. É o §B.6.2 aplicado à borda de ações em vez de só à de embarque.

### A2 · O endpoint que a fundação chama não está em documento nenhum que o guia aponte

**Evidência.** A convenção `POST {origin}/aph/actions/{action_id}` está no código
(`federated_actions.py:61`) e no ADR 0023 §5. Fora daí:

```text
$ grep -c "actions" docs/integration/guia-desenvolvedor-app-federada.md
0
```

Zero ocorrências da palavra no guia do desenvolvedor — o documento que o §0 dele manda pedir
antes de começar. O manifesto também não a carrega: o schema tem
`endpoints: {introspect, openapi, mcp_card}` com `additionalProperties: false`, então nem
declarar um endpoint de ações é possível. O próprio ADR 0023 §5 registra isso como proposta
pendente ao `protocolos` ("gap PROT"), e a mensagem 001 de vocês para o `protocolos` a lista
na linha `a` da tabela.

**Consequência para quem embarca.** Uma aplicação construída estritamente pelo guia **não
tem essa rota**. O resultado não é um erro legível: `federated_actions.py:63-64` devolve
`DEGRADED_MESSAGE`, e o operador vê uma aplicação admitida, aprovada, com telas compondo, e
todas as ações respondendo *"erro: app federada indisponível agora."* — uma falha que parece
de rede e é de contrato. Nós só sabemos que a rota existe porque lemos o adaptador de vocês;
quem receber apenas o guia não saberá.

> **Sugestão.** Enquanto o `endpoints.actions` não existe no normativo, uma seção de cinco
> linhas no `guia-desenvolvedor-app-federada.md` — método, caminho, corpo `{"params": …}`,
> contrato de resposta `{"result": <string>}` e o teto de 2 000 caracteres — custa quase
> nada e fecha o buraco para o próximo. O caminho longo (levar `endpoints.actions` ao Anexo
> B) já está aberto por vocês.

### A3 · `ai_actions` é obrigatório no manifesto e não tem leitor: a tela federada não entra em contexto nenhum

**Evidência.** O schema exige o campo em **toda** tela
(`apps/api/contracts/aph/application-manifest.schema.json:127-131`) e descreve a semântica
normativa em `:156` — *"[] marca item sensivel: NAO DEVE entrar no snapshot (B.5.3)"*. Em
produção, ninguém o lê:

```text
$ grep -rn "ai_actions" apps/api/src apps/web/src
apps/web/src/features/admin/adapters/fake-admin.ts:11:  screens: [{ id: "avalia.home", route: "/avalia", ai_actions: ["READ"] }],
```

Uma ocorrência, num **adaptador falso** de teste do painel. Zero em `apps/api/src`. A
composição descarta o campo por construção — `apps/api/src/ghdaru_api/http/manifest_loader.py:36-40` monta cada
`ScreenDefinition` com `fields=(), actions=()` fixos. E o caminho de contexto nem chega lá:
`apps/api/src/ghdaru_api/http/chat_router.py:238` entrega ao motor `screen_registry.scoped(modules)`, o registro
**só-fundação**, de modo que `_validated_interface`
(`apps/api/src/ghdaru_api/conversation/application/agent_turn.py:141-147`) devolve `(None, {})` para qualquer
`screen_id` federado. Vocês declararam exatamente isto no ADR 0022, última consequência
negativa; está lá, e continua verdade neste commit.

**Consequência para quem embarca.** Duas, e a segunda é a que dói.

1. O schema **obriga** a declarar, tela a tela, o que a IA pode fazer nela — e a declaração
   não produz efeito nenhum. Declaração sem mecanismo é o que a régua do próprio padrão
   proíbe contar como conformidade: hoje o `ai_actions: []` não protege nada; o que protege
   é o caminho inteiro estar ausente. Quando o snapshot alcançar telas federadas, a proteção
   precisa **nascer junto**, ou o marcador vira uma promessa que a norma fez e o código não
   cumpre.
2. "Tela é dado" não acontece para a aplicação federada. O copiloto da fundação nunca sabe
   em **qual** das nossas telas a pessoa está. Isso muda o que podemos prometer: a Árvore da
   Realidade Atual aberta na tela não é contexto da conversa, e uma ação proposta pelo
   modelo não pode se referir ao que o usuário está vendo. É uma limitação legítima de fatia
   — só precisa ser dita **no guia**, porque o §3.2 dele descreve o snapshot de três níveis
   como se valesse para todos.

> **Sugestão.** O lugar barato de honrar o §B.5.3 é a **composição**, não o snapshot: uma
> tela com `ai_actions: []` pode ser composta para navegação e marcada como fora de
> contexto, de modo que o dia em que o snapshot alcançar telas federadas o marcador já
> esteja sendo lido. E, enquanto isso não existe, uma linha no guia dizendo "hoje a sua tela
> não entra em contexto algum" evita que alguém desenhe a aplicação contando com o
> contrário.

### A4 · APH-9.4b: o grant não intersecta com o usuário — reproduzido

**Evidência.** `apps/api/src/ghdaru_api/http/federation_router.py:62` emite o grant com `granted_capabilities(app)`;
o `user` da requisição serve só para inquilino e identidade. E `granted_capabilities`
(`apps/api/src/ghdaru_api/http/manifest_loader.py:206-212`) diz por escrito o que calcula:

```python
def granted_capabilities(app: FederatedApp) -> list[str]:
    """Escopo efetivo da app (D1/D3): `capabilities_required` do manifesto ∩ escopos
    concedidos pelo admin — NUNCA as capabilities de fundação do usuário. …"""
```

Reproduzido com as funções de vocês, sem rede e sem servidor
(`sys.path` apontado para `apps/api/src`, uma app aprovada com `scopes` e manifesto de
`toc:read`/`toc:write`, e uma usuária de papel `member` num inquilino com o módulo `kb`
habilitado e **nenhum** módulo `toc`):

```python
# aph94b.py — funções do próprio hospedeiro, sem rede e sem banco
import sys; sys.path.insert(0, "/home/user/ghdaru/apps/api/src")
from ghdaru_api.http.admin_state import FederatedApp
from ghdaru_api.http.manifest_loader import granted_capabilities
from ghdaru_api.identity.domain.capabilities import derive_capabilities

manifesto = {"app_id": "toc", "capabilities_required": ["toc:read", "toc:write"],
             "mount": "iframe", "url": "https://toc-federada.example/embed"}
app = FederatedApp(id="1", tenant_id="t1", name="TOC", origin="https://toc-federada.example",
                   scopes=["toc:read", "toc:write"], status="approved", manifest=manifesto)

usuaria = derive_capabilities("member", ["kb"])          # nenhum módulo `toc` habilitado
print("capabilities da usuaria (papel member, modulo kb habilitado):", sorted(usuaria))
print("granted_capabilities(app) -> o que a app recebe no grant:", granted_capabilities(app))
print("intersecao que o APH-9.4b exigiria:", sorted(set(granted_capabilities(app)) & usuaria))
print()
print("capabilities de uma usuaria com o modulo toc habilitado (papel member):",
      sorted(derive_capabilities("member", ["toc"])))
```

```text
$ python aph94b.py
capabilities da usuaria (papel member, modulo kb habilitado): ['chat:use', 'kb:read', 'kb:write']
granted_capabilities(app) -> o que a app recebe no grant: ['toc:read', 'toc:write']
intersecao que o APH-9.4b exigiria: []

capabilities de uma usuaria com o modulo toc habilitado (papel member): ['chat:use', 'toc:read', 'toc:write']
```

A primeira metade confirma o relato da irmã no código de hoje: quem não tem capability
`toc:*` nenhuma abre um embarque e a aplicação recebe as duas. A segunda metade é o aviso
que o §B.6.7 do Anexo B dá a quem for fechar a cláusula, e que também se confirma aqui:
`apps/api/src/ghdaru_api/identity/domain/capabilities.py:29-31` concede `read` **e** `write` de cada módulo
habilitado a **qualquer** papel, então intersectar com o usuário fecharia o caso acima e
**não produziria atenuação nenhuma** para quem tem o módulo. A conta que falta é interseção;
o que falta de verdade é política de capability por papel.

**Consequência para quem embarca.** As `capabilities` que recebemos da introspecção **não
são a autoridade do usuário** — são o teto da aplicação. Nós vamos usá-las como fonte de
autorização, porque o P2 manda usá-las e não há outra; e isso significa que, hoje, a
`toc-federada` ofereceria escrita a uma pessoa cujo perfil na fundação não a autoriza. Como
o defeito não é nosso e não temos como detectá-lo de fora, a nossa defesa é a que o P2 já
prescreve: **todo verbo mutador nasce `action_proposal`**, recusável do lado do hospedeiro.
O que o A1 mostra é que hoje o hospedeiro não tem onde recusar uma chamada que ele mesmo
originou — os dois achados se somam.

> **Sugestão.** Fechar o §B.6.7 em duas partes explícitas, na ordem: primeiro
> `derive_capabilities` discriminar papel (senão a interseção é decoração), depois a
> interseção no mint (`federation_router.py:62`) e a cobrança fail-closed por rota. Quem
> fizer isso promove o requisito de 🧪 para ✅ no padrão — e hoje, pelo §B.6.7, **nenhum
> laboratório o implementa**.

### A5 · Registro federado e grants vivem em memória: um reinício da fundação **desadmite** a aplicação

A irmã relatou como "grants em memória (réplica única)". A metade dos grants vocês já
declararam no ADR 0025; a metade que ninguém tinha dito em voz alta é a do **registro**, e é
a que nos custa mais.

**Evidência.** `apps/api/src/ghdaru_api/http/deps.py:108-117` — os dois singletons, com o
comentário que cada um traz:

```python
# e a composição do registry (chat_router, F3). Protótipo in-memory; trocar o backing não
# muda as rotas.
federated_apps = FederatedAppRegistry()
…
# Grants de embed (spec 041 / D3): uso único, TTL de segundos — in-memory por decisão
# (como o registro federado), mesmo com DATABASE_URL; sobreviver a restart não é requisito.
embed_grants = InMemoryEmbedGrantRepository()
```

*(o `…` elide as linhas 111-114, que instanciam o registro de credenciais de consumidor
Nível 3 e não são o assunto aqui. `federated_apps` está na linha 110 e `embed_grants` na 117.)*

O registro guarda tudo num dicionário de processo (`apps/api/src/ghdaru_api/http/admin_state.py:48`), e o próprio
cabeçalho do módulo se declara *"Registros de N2 (apps federadas) e N3 (credenciais
headless) — protótipo in-memory"* (`admin_state.py:1`). Não há tabela para nenhum dos dois:

```text
$ grep -c "__tablename__" apps/api/src/ghdaru_api/persistence/orm.py
17
$ grep -n "federated\|embed_grant" apps/api/src/ghdaru_api/persistence/orm.py
$ echo $?
1
$ ls apps/api/alembic/versions/
0001_baseline.py
0002_backfill_kind.py
$ grep -c "federated\|embed_grant" apps/api/alembic/versions/*.py
apps/api/alembic/versions/0001_baseline.py:0
apps/api/alembic/versions/0002_backfill_kind.py:0
```

Dezessete tabelas mapeadas, **nenhuma** federada, e duas migrações — nenhuma delas cria
tabela de aplicação federada ou de grant.

**Consequência para quem embarca.** Um reinício do serviço da fundação — deploy, escala a
zero, queda — apaga **manifesto, aprovação e hash da credencial**. A partir daí:

- as nossas telas somem do shell sem nenhum evento que a aplicação possa observar;
- a nossa `TOC_APP_CREDENTIAL`, que é variável de ambiente do nosso servidor, passa a
  receber `401` — e o `401` é **uniforme por desenho** (o guia, §4.1, diz que ele é o mesmo
  para ausente, desconhecida, revogada e não aprovada). Não temos como distinguir "fui
  revogada" de "a fundação reiniciou";
- reconstituir exige `POST /admin/federated`, que em `admin_state.py:61-67` **emite uma
  credencial nova**. Ou seja: a recuperação não é um ato de administração do lado de vocês,
  é uma **mudança de configuração do nosso servidor** — na prática, um deploy nosso a cada
  reinício de vocês.

Some-se o que o ADR 0025 já declara: com mais de uma réplica o uso único quebra, porque o
grant emitido numa não é consumido na outra; e a resposta que a aplicação recebe é
`{active:false}`, indistinguível de expirado ou inexistente (§B.6.5, que está certo em não
distinguir — o problema é a causa, não a resposta).

> **Sugestão.** Separar as duas coisas, porque elas têm preços diferentes. **O registro
> federado precisa de persistência** antes de qualquer piloto: é estado de admissão, com
> gesto humano por trás e um segredo que só existe uma vez. **Os grants podem continuar
> efêmeros**, desde que fique declarado no contrato de admissão que o serviço roda em réplica
> única — o TTL é de segundos, e o §B.3.1 já manda a aplicação seguir em modo anônimo quando
> a credencial não vem. O que não funciona é o meio-termo silencioso de hoje: multi-réplica
> quebra sem sintoma legível.

### A6 · O namespace do manifesto não é verificado, e a colisão é silenciosa

**Evidência.** O §B.5.4 lista três obrigações que o schema não expressa e que quem admite
**DEVE** verificar fora dele. Duas estão feitas (linhas 2 e 3 da tabela do §3 desta
mensagem). A terceira não: `_conflito_de_app_id` (`apps/api/src/ghdaru_api/http/admin_router.py:239-248`) confere a
exclusividade do `app_id`, e nada confere que o `<ns>` de `screen.id` e `action_id` pertença
à aplicação. Busca feita em `admin_router.py`, `manifest_loader.py` e
`apps/api/src/ghdaru_api/conversation/domain/manifest.py`.

Quando a colisão acontece, ela é muda dos dois lados: telas colidentes caem num `continue`
(`manifest_loader.py:247-248`), e ações colidentes caem noutro
(`federated_actions.py:98-99`) — e o ADR 0023 registra, sobre este segundo, *"sem log do
skip: limitação registrada"*.

**Consequência para quem embarca.** O nosso prefixo é `toc.` (ADR 0003 deste projeto), e o
`app_id` é `toc`. Uma segunda aplicação aprovada no mesmo inquilino com `app_id` diferente
— `toc-builder`, por exemplo, que é o nome que a linhagem usa e que aparece no manifesto de
referência do próprio Anexo B — pode declarar `toc.arvore` legitimamente pelo schema. A
partir daí, quem foi admitido primeiro vence (`eligible_federated_apps` ordena por
`sequencia`, `manifest_loader.py:172`), e o perdedor perde telas e ações **sem erro, sem
log e sem aviso ao administrador**. É a mesma classe de defeito que a spec 048 fechou para
rotas, um nível acima.

> **Sugestão.** Cobrar no `approve`, junto da exclusividade do `app_id` que já está lá: ou o
> `<ns>` é o `app_id`, ou o prefixo declarado é exclusivo daquela aplicação no inquilino —
> que é literalmente o que o §B.5.2 pede. E, enquanto isso, um log no `continue` de
> `federated_actions.py:98` custa uma linha e transforma um sumiço em um sintoma.

### A7 · A porta de entrada da documentação manda o desenvolvedor para o documento errado

Este achado é de documento, não de código, e mesmo assim é o que mais provavelmente faria a
próxima aplicação implementar a junta errada.

**Evidência.** O índice da pasta de integração diz, em `docs/integration/README.md:42-44`:

```text
- **Vou construir uma app** → [`instrucoes-construcao.md`](instrucoes-construcao.md)
  (Parte A comum + Parte B Nível 3 + Parte C Nível 2), validando o manifesto contra
  [`manifest.schema.json`](manifest.schema.json).
```

E o guia correto não é citado nem uma vez:

```text
$ grep -c "guia-desenvolvedor" docs/integration/README.md
0
```

O documento para onde o índice aponta prescreve a junta **invertida**
(`docs/integration/instrucoes-construcao.md:192-199`):

```text
192:    S->>I: ghd.handshake { token, tenant, capabilities }
194:    Note over I: valida token via GET /me
195:    I->>S: ghd.ready { protocol:"ghd", v:1, payload:{ app_id } }
196:    S->>I: ghd.theme { tokens }
197:    I->>S: ghd.snapshot { snapshot }
198:    S->>I: ghd.ui_command { navigate | form.patch | … }
199:    I->>S: ghd.action_result { trace }
```

São quatro problemas num diagrama só, e os quatro contrariam a norma vigente. **Um**: o
shell fala primeiro (o §B.2.2 diz o contrário, e é um "NÃO DEVE" do hospedeiro). **Dois**: o
token é validado por `GET /me` como *bearer* (o §B.6.2 proíbe o grant como bearer em rota
nenhuma, e o código de vocês o rejeita por construção). **Três**: `ghd.theme`,
`ghd.snapshot` e `ghd.ui_command` **não existem** no vocabulário do §B.3, que o §B.11.1
declara fechado ("nenhum é válido para emitir enquanto o anexo não os admitir"). **Quatro**:
`ghd.action_result` aparece carregando `{ trace }`, quando o §B.9.1 diz que ele é sinal de
interface — *"nunca prova de execução"*, e **não deve** entrar em auditoria. A tabela logo abaixo
(`:206-211`) repete os seis. Que o arquivo foi tocado depois da spec 046 é visível na linha
`:207`, que já corrigiu `appId` para `app_id`: a correção passou pela linha ao lado da
inversão e não a viu. O ADR 0025 registrou esta deriva na última consequência — *"Deriva de
doc registrada, não corrigida"* — e ela continua aqui.

Some-se a isso que o guia correto está **datado**: cita "Padrão APH v0.5" e "Anexo A v0.3"
(`guia-desenvolvedor-app-federada.md:5,50`) quando a norma está em v0.8 e A v0.5; diz, no
fecho (`:253-256`), que a junta *"está desenhada … ainda não implementada"*, quando F3, F4,
D3 e D4 estão no ar; e manda não enviar `ghd.action_result` (`:205-206`) quando
`handshake.ts:58-62` o trata desde a spec 042.

**Consequência para quem embarca.** Um autor que comece pelo índice — que é o que um índice
existe para provocar — implementa o handshake invertido, usa o grant como bearer, espera
mensagens que ninguém emite e devolve traço num campo que o hospedeiro não deve auditar.
Nada disso falha na admissão: falha em silêncio, no
navegador, depois do deploy. Nós escapamos porque lemos o código antes do documento; isso
não escala, e não deveria ser a estratégia recomendada de integração.

> **Sugestão.** Duas linhas de edição resolvem a maior parte: o `README.md` da pasta apontar
> "Vou construir uma app" para o `guia-desenvolvedor-app-federada.md`, e o
> `instrucoes-construcao.md` ganhar, no topo, o mesmo aviso de superação que o
> `manifesto-aplicacao.md:3-8` já carrega — ele é o modelo, e funciona.

---

## 5 · O que precisamos de volta, e nada disso é segredo

Para o primeiro embarque de verdade:

1. **As duas variáveis ligadas, e em qual ambiente**: `FEDERATION_MANIFESTS_ENABLED`
   (`manifest_loader.py:26-29` — sem ela **tudo** responde 404, inclusive o mint do grant) e
   `FEDERATION_REMOTE_ACTIONS_ENABLED` (`federated_actions.py:28-31`, também `off` por
   padrão). As duas são `off` por omissão por decisão registrada, e é bom que sejam; só
   precisamos saber quando ligam.
2. **`FEDERATION_HOST_SITE` declarada** — sem ela, `validate_federated_origin` recusa
   **qualquer** origem (`manifest_loader.py:125-131`), e a recusa é 422 na nossa admissão.
3. **A aplicação registrada e aprovada**, com os escopos cobrindo `toc:read` e (a partir do
   nosso ciclo 006) `toc:write` — abaixo disso ela some de tudo com o mesmo 404.
4. **A credencial `ghd_`** emitida na admissão, entregue por canal de segredo. Ela nunca vai
   para o nosso navegador (P7 daqui; §4.1 do guia de vocês).
5. **O bloco "Contrato de admissão"** (`GET /admin/federated/{id}/admission-contract`) com os
   quatro parâmetros do §B.4 preenchidos — é ele que a nossa aplicação exige na partida, e a
   ausência de qualquer um faz o serviço **recusar-se a subir**, por desenho (§B.4.1).
6. **Existe ambiente de teste?** É a quinta linha da tabela do §B.4, que não impede subir. No código ela é publicada como `FEDERATION_TEST_BASE_URL` ou `null`
   (`admission.py:87`) — se está definida em algum ambiente, é fato que só vocês têm.
7. **Quantas réplicas** o serviço roda hoje. É a pergunta que o A5 transforma em decisão: com
   uma, os grants efêmeros são aceitáveis e nós tratamos o reinício como
   `GRANT_INATIVO`; com mais de uma, o uso único quebra de forma que nenhum dos dois lados
   observa.

---

## 6 · O que é nosso, e ainda não existe

Honestidade sobre o outro lado da ponte, para ninguém esperar por nós sem saber.

A `toc-federada` está em construção: o corpus de planejamento (doze specs) existe, o ciclo
001 fechou, e o **endereço público** da aplicação ainda é portão humano em aberto — logo o
`origin` e a `url` do nosso manifesto ainda não são definitivos. O que já está decidido e
não muda: `mode: embedded`, `app_id: toc`, prefixo `toc.` nas telas e ações, eTLD+1 distinto
do de vocês (§B.1.2), assistência de inteligência artificial **exclusivamente** pela
fundação — sem cliente de provedor no nosso produto —, e base de dados **sintética** desde o
primeiro dia, o que nos permite manter o repositório aberto.

O nosso ciclo 003 entrega o esqueleto federado somente leitura: recusa de subir sem os
quatro parâmetros nomeando o que faltou, `ghd.ready` primeiro, `event.source` **e**
`event.origin` verificados, `targetOrigin` dirigido, e o grant trocado por identidade na
introspecção antes de qualquer dado renderizar. Nada disso depende dos achados desta
mensagem. O que depende: o **A1**, que é o que separa "a aplicação aparece" de "a aplicação
é operável pela IA da fundação".

---

## 7 · Como isto chega ao destino — e não é por cópia

Pelo caminho da convenção ([`README.md`](README.md)): esta mensagem **não é copiada** para
`ghdaru`. O artefato vive aqui, versionado e datado; o que atravessa a fronteira é o
**aviso** de que ele existe, aberto pelo Product Steward, caso a caso (P1). Nenhuma linha
foi escrita, nem será, no repositório de vocês.
