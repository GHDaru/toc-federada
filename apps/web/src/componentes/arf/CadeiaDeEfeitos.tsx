/**
 * A leitura da Árvore da Realidade Futura (ARF): o ponto de partida e o que ele encadeia.
 *
 * Siglas, uma vez: **ARF** — Árvore da Realidade Futura · **UDE** — Efeito Indesejável ·
 * **ED** — Efeito Desejável · **RI/RF/RN** — requisito de interface / funcional / regra de
 * negócio.
 *
 * Por que uma leitura ao lado do canvas, e não só o canvas: a ARF tem uma direção. A
 * injeção é o que **ainda não existe** e é dela que tudo parte; o efeito futuro é
 * consequência. Um canvas mostra o grafo e não mostra a direção da leitura — e foi assim
 * que as quatro gerações da linhagem trataram a árvore de futuro (mal: como botão cinza,
 * `tocbuilderv3/components/Sidebar.tsx:55`).
 *
 * **Nada é recalculado aqui.** A leitura de suficiência de cada elo (`Se …, então …`) vem
 * montada do servidor, dos textos ATUAIS dos nós; o espelho UDE → ED vem do agregado; o
 * ramo negativo vem da lista de ramos. A única coisa que este componente faz com o grafo
 * é agrupar por nó o que já veio pronto.
 */
import type { EloDaArf, EspelhoDeUde, NoDaArvore, RamoNegativo } from "../../dominio/tipos";
import { useI18n } from "../../i18n";

export interface CadeiaDeEfeitosProps {
  nos: readonly NoDaArvore[];
  elos: readonly EloDaArf[];
  espelhos: readonly EspelhoDeUde[];
  ramos: readonly RamoNegativo[];
  selecionado: string | null;
  aoSelecionar(id: string): void;
}

export function CadeiaDeEfeitos({
  nos,
  elos,
  espelhos,
  ramos,
  selecionado,
  aoSelecionar,
}: CadeiaDeEfeitosProps) {
  const { t } = useI18n();
  const injecoes = nos.filter((no) => no.papel === "injecao");
  const efeitos = nos.filter((no) => no.papel === "efeito_futuro");
  const espelhados = new Set(espelhos.map((e) => e.no_id));
  const raizesDeRamo = new Set(ramos.map((r) => r.raiz_id));

  const saindo = (id: string) => elos.filter((e) => e.origem_id === id);
  const chegando = (id: string) => elos.filter((e) => e.destino_id === id);

  return (
    <div className="leitura-da-arf">
      <section className="ponto-de-partida" role="region" aria-label={t("arf.ponto_de_partida")}>
        <h3>{t("arf.ponto_de_partida")}</h3>
        <p className="explicacao">{t("arf.ponto_de_partida_explicacao")}</p>
        {injecoes.length === 0 ? (
          <p className="vazio">{t("arf.sem_injecao")}</p>
        ) : (
          <ol className="lista-de-injecoes">
            {injecoes.map((no) => {
              const causa = saindo(no.id);
              return (
                <li
                  key={no.id}
                  aria-label={no.titulo}
                  data-papel="injecao"
                  data-selecionado={selecionado === no.id ? "sim" : "nao"}
                >
                  <button type="button" className="texto-do-no" onClick={() => aoSelecionar(no.id)}>
                    {no.titulo}
                  </button>
                  <p className="grau">
                    {causa.length === 0
                      ? t("arf.sem_saida")
                      : t("arf.causa_de", { n: causa.length })}
                  </p>
                </li>
              );
            })}
          </ol>
        )}
      </section>

      <section className="efeitos-encadeados" role="region" aria-label={t("arf.efeitos")}>
        <h3>{t("arf.efeitos")}</h3>
        <p className="explicacao">{t("arf.efeitos_explicacao")}</p>
        {efeitos.length === 0 ? (
          <p className="vazio">{t("arf.sem_efeito")}</p>
        ) : (
          <ul className="lista-de-efeitos">
            {efeitos.map((no) => {
              const ehRamoNegativo = raizesDeRamo.has(no.id);
              return (
                <li
                  key={no.id}
                  aria-label={no.titulo}
                  data-papel="efeito_futuro"
                  // O ramo negativo NÃO é mais um efeito da lista: ele é a contramão da
                  // injeção, e o dado está no elemento para a folha de estilo poder
                  // diferenciá-lo sem depender de cor sozinha.
                  data-ramo-negativo={ehRamoNegativo ? "sim" : "nao"}
                  data-selecionado={selecionado === no.id ? "sim" : "nao"}
                >
                  <button type="button" className="texto-do-no" onClick={() => aoSelecionar(no.id)}>
                    {no.titulo}
                  </button>
                  {/* O Efeito Desejável é o efeito futuro que CONVERTE um Efeito
                      Indesejável da cadeia (RN-03). Um ramo negativo nunca o é. */}
                  {espelhados.has(no.id) && !ehRamoNegativo ? (
                    <p className="selo-ed" title={t("arf.espelha_ude")}>
                      {t("arf.efeito_desejavel")}
                    </p>
                  ) : null}
                  {ehRamoNegativo ? (
                    <p className="selo-ramo">{t("arf.ramo.raiz")}</p>
                  ) : null}
                  <ul className="leituras">
                    {chegando(no.id).map((elo) => (
                      <li key={elo.id} className="leitura-do-elo">
                        {elo.leitura}
                      </li>
                    ))}
                  </ul>
                </li>
              );
            })}
          </ul>
        )}
      </section>
    </div>
  );
}
