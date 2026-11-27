import { afterEach, describe, expect, it, vi } from "vitest";

import { ErroApi, listarVagas, urlDaApi, urlDeVagas } from "@/lib/api";
import type { PaginaVagas } from "@/types/vaga";

const PAGINA_VAZIA: PaginaVagas = { itens: [], total: 0, pagina: 1, por_pagina: 20, total_paginas: 0 };

function respostaJson(corpo: unknown, status = 200): Response {
  return new Response(JSON.stringify(corpo), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

afterEach(() => {
  vi.unstubAllEnvs();
});

describe("urlDaApi", () => {
  it("usa localhost:8000 sem a variável API_URL", () => {
    vi.stubEnv("API_URL", "");
    expect(urlDaApi()).toBe("http://localhost:8000");
  });

  it("usa a API_URL sem a barra final", () => {
    vi.stubEnv("API_URL", "http://api:8000/");
    expect(urlDaApi()).toBe("http://api:8000");
  });
});

describe("urlDeVagas", () => {
  it("monta a URL do GET /vagas com paginação", () => {
    expect(urlDeVagas({ q: "dados", remoto: true, pagina: 2 }, "http://api:8000")).toBe(
      "http://api:8000/vagas?q=dados&remoto=true&pagina=2&por_pagina=20",
    );
  });

  it("sempre manda a página, inclusive a 1", () => {
    expect(urlDeVagas({ pagina: 1 }, "http://x")).toBe("http://x/vagas?pagina=1&por_pagina=20");
  });
});

describe("listarVagas", () => {
  it("devolve a página da API", async () => {
    const fetchFalso = vi.fn().mockResolvedValue(respostaJson(PAGINA_VAZIA));

    const pagina = await listarVagas({ cidade: "Recife", pagina: 1 }, { baseUrl: "http://x", fetch: fetchFalso });

    expect(pagina).toEqual(PAGINA_VAZIA);
    expect(fetchFalso).toHaveBeenCalledWith("http://x/vagas?cidade=Recife&pagina=1&por_pagina=20", {
      cache: "no-store",
      headers: { Accept: "application/json" },
    });
  });

  it("transforma status de erro em ErroApi", async () => {
    const fetchFalso = vi.fn().mockResolvedValue(respostaJson({ detail: "x" }, 503));

    const promessa = listarVagas({ pagina: 1 }, { fetch: fetchFalso });

    await expect(promessa).rejects.toBeInstanceOf(ErroApi);
    await expect(listarVagas({ pagina: 1 }, { fetch: fetchFalso })).rejects.toMatchObject({
      status: 503,
      message: "A API respondeu com erro 503.",
    });
  });

  it("transforma falha de rede em ErroApi sem status", async () => {
    const fetchFalso = vi.fn().mockRejectedValue(new TypeError("fetch failed"));

    await expect(listarVagas({ pagina: 1 }, { fetch: fetchFalso })).rejects.toMatchObject({
      name: "ErroApi",
      status: undefined,
      message: "Não foi possível falar com a API. Ela está no ar?",
    });
  });
});
