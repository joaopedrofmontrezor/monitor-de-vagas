import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { Paginacao } from "@/components/Paginacao";

describe("Paginacao", () => {
  it("não aparece com uma página só", () => {
    const { container } = render(<Paginacao filtros={{ pagina: 1 }} totalPaginas={1} />);

    expect(container).toBeEmptyDOMElement();
  });

  it("mantém os filtros nos links de anterior e próxima", () => {
    render(<Paginacao filtros={{ q: "dados", remoto: true, pagina: 2 }} totalPaginas={3} />);

    expect(screen.getByText("Página 2 de 3")).toBeInTheDocument();
    expect(screen.getByRole("link", { name: "Anterior" })).toHaveAttribute("href", "/vagas?q=dados&remoto=true");
    expect(screen.getByRole("link", { name: "Próxima" })).toHaveAttribute(
      "href",
      "/vagas?q=dados&remoto=true&pagina=3",
    );
  });

  it("esconde anterior na primeira e próxima na última", () => {
    const { rerender } = render(<Paginacao filtros={{ pagina: 1 }} totalPaginas={2} />);
    expect(screen.queryByRole("link", { name: "Anterior" })).not.toBeInTheDocument();

    rerender(<Paginacao filtros={{ pagina: 2 }} totalPaginas={2} />);
    expect(screen.queryByRole("link", { name: "Próxima" })).not.toBeInTheDocument();
  });
});
