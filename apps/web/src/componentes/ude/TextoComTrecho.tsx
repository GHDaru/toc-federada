/**
 * O texto do Efeito Indesejável (UDE) com os trechos reprovados marcados **no lugar**.
 *
 * RI-03 da spec 005: "a reprovação de critério decidível aponta o trecho no próprio texto
 * do UDE (marcação inline), com a explicação ao lado — não em janela separada". Janela
 * separada obriga quem lê a segurar o texto na cabeça enquanto lê a crítica; a marcação
 * põe os dois no mesmo campo de visão.
 */
export interface TrechoMarcado {
  trecho: string;
  codigo: string;
}

interface Pedaco {
  texto: string;
  codigo?: string;
}

/** Corta o texto nos trechos apontados. Trecho ausente do texto é simplesmente ignorado. */
export function fatiar(texto: string, marcas: readonly TrechoMarcado[]): Pedaco[] {
  const posicoes = marcas
    .map((marca) => ({ ...marca, inicio: marca.trecho ? texto.indexOf(marca.trecho) : -1 }))
    .filter((marca) => marca.inicio >= 0)
    .sort((a, b) => a.inicio - b.inicio);

  const pedacos: Pedaco[] = [];
  let cursor = 0;
  for (const marca of posicoes) {
    if (marca.inicio < cursor) continue; // trechos sobrepostos: o primeiro manda
    if (marca.inicio > cursor) pedacos.push({ texto: texto.slice(cursor, marca.inicio) });
    pedacos.push({ texto: marca.trecho, codigo: marca.codigo });
    cursor = marca.inicio + marca.trecho.length;
  }
  if (cursor < texto.length) pedacos.push({ texto: texto.slice(cursor) });
  return pedacos;
}

export function TextoComTrecho({ texto, marcas }: { texto: string; marcas: readonly TrechoMarcado[] }) {
  return (
    <p className="texto-com-trecho">
      {fatiar(texto, marcas).map((pedaco, indice) =>
        pedaco.codigo ? (
          <mark key={indice} data-criterio={pedaco.codigo}>
            {pedaco.texto}
          </mark>
        ) : (
          <span key={indice}>{pedaco.texto}</span>
        ),
      )}
    </p>
  );
}
