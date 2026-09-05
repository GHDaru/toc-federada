"""Os roteadores da aplicação, todos sob o prefixo próprio `/toc`.

**Por que prefixo próprio.** O guia do hospedeiro, ao descrever a classe de colisão que a
admissão não alcança — módulos de inquilino que nascem depois da aprovação —, diz que
"escolher um prefixo próprio (`/toc/…`) é a defesa prática"
(`ghdaru/docs/integration/guia-desenvolvedor-app-federada.md`, leitura apenas; §B.10.3 do
Anexo B do Padrão APH — Aplicação ↔ Harness, descreve a mesma classe). O esboço de
contrato do ciclo 001 (`specs/004-nucleo-de-diagramas/contracts/rest-api.md`) escrevia
`/api/toc` e declara, ele próprio, que "não fixa o formato binário/byte final dos corpos"
e que a paginação e o resto são "decisão do ciclo 004, registrada no próprio código".
`/api` acrescentaria um prefixo genérico a colidir e não defende de nada.
"""
