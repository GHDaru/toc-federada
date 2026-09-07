// A língua-fonte (RN-01 da spec 011): toda chave existe primeiro aqui.
export const pt = {
  app: {
    titulo: "TOC Federada",
    salvar: "Salvar",
    cancelar: "Cancelar",
  },
  projetos: {
    titulo: "Projetos",
    contagem: "{{n}} projeto(s)",
  },
} as const;

export type Dicionario = typeof pt;
