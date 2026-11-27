import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { criarVaga } from "@/components/teste-vagas";
import { VagaCard } from "@/components/VagaCard";

describe("VagaCard", () => {
  it("mostra título com link externo, empresa, cidade e data", () => {
    render(<VagaCard vaga={criarVaga()} />);

    const link = screen.getByRole("link", { name: "Estágio em Engenharia de Dados" });
    expect(link).toHaveAttribute("href", "https://job-boards.greenhouse.io/btgpactual/jobs/1");
    expect(link).toHaveAttribute("target", "_blank");
    expect(link).toHaveAttribute("rel", "noopener noreferrer");
    expect(screen.getByText("BTG Pactual")).toBeInTheDocument();
    expect(screen.getByText("São Paulo - SP")).toBeInTheDocument();
    expect(screen.getByText("Publicada em 10/11/2026")).toBeInTheDocument();
    expect(screen.queryByText("Remoto")).not.toBeInTheDocument();
  });

  it("mostra o selo de remoto e cai para a data da coleta", () => {
    render(<VagaCard vaga={criarVaga({ remoto: true, cidade: null, empresa: null, publicada_em: null })} />);

    expect(screen.getByText("Remoto")).toBeInTheDocument();
    expect(screen.getByText("Empresa não informada")).toBeInTheDocument();
    expect(screen.getByText("Coletada em 27/11/2026")).toBeInTheDocument();
  });
});
