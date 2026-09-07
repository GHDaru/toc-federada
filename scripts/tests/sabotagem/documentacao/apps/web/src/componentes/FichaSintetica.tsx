// Declara uma âncora de ajuda que EXISTE no verbete da ferramenta que ela nomeia.
import { BotaoDeAjuda } from "./documentacao/BotaoDeAjuda";

export function FichaSintetica({ abrir }: { abrir: (f: string, a: string) => void }) {
  return <BotaoDeAjuda ferramenta="nc" ancora="premissa-sustentada" aoAbrir={abrir} />;
}
