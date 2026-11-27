import type { Filtros, ParametrosDaUrl } from "@/types/vaga";

export const MAX_BUSCA = 100;
export const MAX_CIDADE = 120;

function primeiro(valor: string | string[] | undefined): string | undefined {
  return Array.isArray(valor) ? valor[0] : valor;
}

function texto(valor: string | string[] | undefined, limite: number): string | undefined {
  const limpo = primeiro(valor)?.trim().slice(0, limite).trim();
  return limpo ? limpo : undefined;
}

function booleano(valor: string | string[] | undefined): boolean | undefined {
  const bruto = primeiro(valor);
  if (bruto === "true") return true;
  if (bruto === "false") return false;
  return undefined;
}

function pagina(valor: string | string[] | undefined): number {
  const numero = Number(primeiro(valor));
  return Number.isInteger(numero) && numero >= 1 ? numero : 1;
}

export function lerFiltros(params: ParametrosDaUrl): Filtros {
  return {
    q: texto(params.q, MAX_BUSCA),
    cidade: texto(params.cidade, MAX_CIDADE),
    remoto: booleano(params.remoto),
    pagina: pagina(params.pagina),
  };
}

export function paraParametros(filtros: Partial<Filtros>): URLSearchParams {
  const params = new URLSearchParams();
  const q = filtros.q?.trim();
  const cidade = filtros.cidade?.trim();
  if (q) params.set("q", q);
  if (cidade) params.set("cidade", cidade);
  if (filtros.remoto !== undefined) params.set("remoto", String(filtros.remoto));
  if (filtros.pagina && filtros.pagina > 1) params.set("pagina", String(filtros.pagina));
  return params;
}

export function montarBusca(filtros: Partial<Filtros>): string {
  const busca = paraParametros(filtros).toString();
  return busca ? `?${busca}` : "";
}

export function temFiltro(filtros: Filtros): boolean {
  return Boolean(filtros.q || filtros.cidade || filtros.remoto !== undefined);
}
