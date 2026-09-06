/**
 * A trilha dos cinco passos — a superfície de navegação do módulo (RI-01).
 *
 * Siglas, uma vez: **TOC** — Teoria das Restrições · **RI/RN/RF** — requisito de interface
 * / regra de negócio / requisito funcional · **ARIA** — *Accessible Rich Internet
 * Applications*.
 *
 * Três coisas que a RI-01 exige e que estão aqui de forma verificável:
 *
 * 1. **Estado distinguível por forma e rótulo, nunca só por cor.** Cada passo carrega um
 *    marcador textual (`✓`, `▶`, `·`) **e** o nome do estado por extenso em `aria-label`.
 *    Uma tela em preto e branco, um leitor de tela e um teste automatizado leem a mesma
 *    coisa — e é isso que "nunca só por cor" quer dizer na prática.
 * 2. **O passo atual é o foco visual**: `aria-current="step"`, que é o atributo que
 *    descreve exatamente esta situação, e não um `className` inventado.
 * 3. **A ordem é fixa** (RN-01). Este componente não ordena nada: ele desenha o que o
 *    servidor mandou, na ordem em que mandou. Uma trilha que reordenasse por conta
 *    própria seria uma segunda fonte de verdade sobre a coisa mais estável do método.
 *
 * A contagem de pendências por passo vem do mapa computado pelo domínio (RF-12); esta
 * tela **não** a recalcula.
 */
import type { PassoNaJornada, TipoDePasso } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

const MARCADOR: Record<string, string> = {
  concluido: "✓",
  em_andamento: "▶",
  pendente: "·",
};

export interface TrilhaDosPassosProps {
  passos: readonly PassoNaJornada[];
  passoAtual: TipoDePasso;
  selecionado: TipoDePasso;
  aoSelecionar(passo: TipoDePasso): void;
}

export function TrilhaDosPassos({
  passos,
  passoAtual,
  selecionado,
  aoSelecionar,
}: TrilhaDosPassosProps) {
  const { t } = useI18n();

  return (
    <nav className="trilha-dos-passos" aria-label={t("foco.titulo")}>
      <ol>
        {passos.map((passo, indice) => {
          const estado = t(`foco.estado.${passo.estado}`);
          const nome = t(`foco.passo_curto.${passo.tipo}`);
          return (
            <li key={passo.tipo}>
              <button
                type="button"
                className="passo-da-trilha"
                data-estado={passo.estado}
                data-atual={passo.tipo === passoAtual}
                data-selecionado={passo.tipo === selecionado}
                aria-current={passo.tipo === passoAtual ? "step" : undefined}
                aria-pressed={passo.tipo === selecionado}
                aria-label={`${indice + 1}. ${nome} — ${estado}`}
                onClick={() => aoSelecionar(passo.tipo)}
              >
                {/* Forma antes de cor: o marcador e o número sobrevivem ao monocromático. */}
                <span className="passo-marcador" aria-hidden="true">
                  {MARCADOR[passo.estado] ?? "·"}
                </span>
                <span className="passo-ordem" aria-hidden="true">
                  {indice + 1}
                </span>
                <span className="passo-nome">{nome}</span>
                <span className="passo-estado">{estado}</span>
                {passo.pendencias.length > 0 ? (
                  <span
                    className="passo-pendencias"
                    title={passo.pendencias.map((p) => p.detalhe).join(" · ")}
                  >
                    {passo.pendencias.length}
                  </span>
                ) : null}
              </button>
            </li>
          );
        })}
      </ol>
    </nav>
  );
}
