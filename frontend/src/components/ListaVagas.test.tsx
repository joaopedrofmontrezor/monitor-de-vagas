import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { CarregandoVagas, EstadoErro } from "@/components/Estados";
import { ListaVagas } from "@/components/ListaVagas";
import { criarVaga } from "@/components/teste-vagas";
import { ErroApi } from "@/lib/api";
import type { Filtros, PaginaVagas } from "@/types/vaga";

function pagina(campos: Partial<PaginaVagas> = {}): PaginaVagas {
  return { itens: [], total: 0, pagina: 1, por_pagina: 20, total_paginas: 0, ...campos };
}

async function renderizar(filtros: Filtros, buscar: (f: Filtros) => Promise<PaginaVagas>) {
  render(await ListaVagas({ filtros, buscar }));
}

describe("ListaVagas", () => {
  it("lista as vagas com o total e a paginação", async () => {
    const itens = [criarVaga({ id: 1 }), criarVaga({ id: 2, titulo: "Estágio em Front-end" })];
    const buscar = vi.fn().mockResolvedValue(pagina({ itens, total: 41, total_paginas: 3 }));

    await renderizar({ q: "estagio", pagina: 1 }, buscar);

    expect(buscar).toHaveBeenCalledWith({ q: "estagio", pagina: 1 });
    expect(screen.getByText("41 vagas encontradas")).toBeInTheDocument();
    expect(screen.getAllByRole("article")).toHaveLength(2);
    expect(screen.getByRole("link", { name: "Próxima" })).toHaveAttribute("href", "/vagas?q=estagio&pagina=2");
  });

  it("mostra o estado vazio sugerindo limpar os filtros", async () => {
    await renderizar({ cidade: "Manaus", pagina: 1 }, vi.fn().mockResolvedValue(pagina()));

    expect(screen.getByText("Nenhuma vaga encontrada.")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "limpe os filtros" })).toHaveAttribute("href", "/vagas");
  });

  it("sem filtros, o estado vazio fala da coleta", async () => {
    await renderizar({ pagina: 1 }, vi.fn().mockResolvedValue(pagina()));

    expect(screen.getByText(/A coleta ainda não trouxe vagas/)).toBeInTheDocument();
  });

  it("mostra o erro da API", async () => {
    await renderizar({ pagina: 1 }, vi.fn().mockRejectedValue(new ErroApi("A API respondeu com erro 503.", 503)));

    expect(screen.getByRole("alert")).toHaveTextContent("A API respondeu com erro 503.");
  });

  it("erro desconhecido vira mensagem genérica", async () => {
    await renderizar({ pagina: 1 }, vi.fn().mockRejectedValue(new Error("boom")));

    expect(screen.getByRole("alert")).toHaveTextContent("Erro inesperado.");
  });
});

describe("Estados", () => {
  it("carregando avisa leitores de tela", () => {
    render(<CarregandoVagas />);

    expect(screen.getByRole("status")).toHaveTextContent("Carregando vagas...");
  });

  it("erro com botão de tentar de novo", async () => {
    const tentarDeNovo = vi.fn();
    render(<EstadoErro mensagem="falhou" tentarDeNovo={tentarDeNovo} />);

    await userEvent.setup().click(screen.getByRole("button", { name: "Tentar de novo" }));

    expect(tentarDeNovo).toHaveBeenCalledOnce();
  });
});
