import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

import { FormularioFiltros } from "@/components/FormularioFiltros";

const push = vi.fn();

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push }),
}));

beforeEach(() => {
  push.mockClear();
});

describe("FormularioFiltros", () => {
  it("começa com os filtros da URL", () => {
    render(<FormularioFiltros filtros={{ q: "dados", cidade: "Recife", remoto: false, pagina: 2 }} />);

    expect(screen.getByLabelText("Buscar no título")).toHaveValue("dados");
    expect(screen.getByLabelText("Cidade")).toHaveValue("Recife");
    expect(screen.getByLabelText("Modalidade")).toHaveValue("false");
  });

  it("leva para a URL com os filtros e volta para a página 1", async () => {
    const usuario = userEvent.setup();
    render(<FormularioFiltros filtros={{ pagina: 3 }} />);

    await usuario.type(screen.getByLabelText("Buscar no título"), "dados");
    await usuario.selectOptions(screen.getByLabelText("Modalidade"), "Só remotas");
    await usuario.click(screen.getByRole("button", { name: "Buscar" }));

    expect(push).toHaveBeenCalledWith("/vagas?q=dados&remoto=true");
  });

  it("sem filtros leva para /vagas", async () => {
    const usuario = userEvent.setup();
    render(<FormularioFiltros filtros={{ q: "web", pagina: 1 }} />);

    await usuario.clear(screen.getByLabelText("Buscar no título"));
    await usuario.click(screen.getByRole("button", { name: "Buscar" }));

    expect(push).toHaveBeenCalledWith("/vagas");
  });

  it("tem link para limpar os filtros", () => {
    render(<FormularioFiltros filtros={{ q: "web", pagina: 1 }} />);

    expect(screen.getByRole("link", { name: "Limpar" })).toHaveAttribute("href", "/vagas");
  });
});
