export type Vaga = {
  id: number;
  fonte: string;
  tipo: string;
  titulo: string;
  empresa: string | null;
  cidade: string | null;
  remoto: boolean;
  url: string;
  publicada_em: string | null;
  coletada_em: string;
};

export type PaginaVagas = {
  itens: Vaga[];
  total: number;
  pagina: number;
  por_pagina: number;
  total_paginas: number;
};

export type Filtros = {
  q?: string;
  cidade?: string;
  remoto?: boolean;
  pagina: number;
};

export type ParametrosDaUrl = Record<string, string | string[] | undefined>;
