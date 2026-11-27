import { paraParametros } from "@/lib/filtros";
import type { Filtros, PaginaVagas } from "@/types/vaga";

export const POR_PAGINA = 20;
const URL_PADRAO = "http://localhost:8000";

export class ErroApi extends Error {
  readonly status?: number;

  constructor(mensagem: string, status?: number) {
    super(mensagem);
    this.name = "ErroApi";
    this.status = status;
  }
}

type Opcoes = {
  baseUrl?: string;
  fetch?: typeof fetch;
};

export function urlDaApi(): string {
  return (process.env.API_URL || URL_PADRAO).replace(/\/+$/, "");
}

export function urlDeVagas(filtros: Filtros, baseUrl: string = urlDaApi()): string {
  const params = paraParametros(filtros);
  params.set("pagina", String(filtros.pagina));
  params.set("por_pagina", String(POR_PAGINA));
  return `${baseUrl}/vagas?${params.toString()}`;
}

export async function listarVagas(filtros: Filtros, opcoes: Opcoes = {}): Promise<PaginaVagas> {
  const buscar = opcoes.fetch ?? fetch;
  let resposta: Response;
  try {
    resposta = await buscar(urlDeVagas(filtros, opcoes.baseUrl), {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  } catch {
    throw new ErroApi("Não foi possível falar com a API. Ela está no ar?");
  }
  if (!resposta.ok) {
    throw new ErroApi(`A API respondeu com erro ${resposta.status}.`, resposta.status);
  }
  return (await resposta.json()) as PaginaVagas;
}
