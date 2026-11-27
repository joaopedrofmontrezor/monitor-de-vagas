import { describe, expect, it } from "vitest";

import { formatarData, formatarTotal } from "@/lib/formatar";

describe("formatarData", () => {
  it("formata no fuso de São Paulo", () => {
    expect(formatarData("2026-11-27T01:30:00Z")).toBe("26/11/2026");
    expect(formatarData("2026-11-10T09:00:00-03:00")).toBe("10/11/2026");
  });

  it("devolve null para vazio ou inválido", () => {
    expect(formatarData(null)).toBeNull();
    expect(formatarData("ontem")).toBeNull();
  });
});

describe("formatarTotal", () => {
  it("usa singular e plural", () => {
    expect(formatarTotal(1)).toBe("1 vaga encontrada");
    expect(formatarTotal(0)).toBe("0 vagas encontradas");
    expect(formatarTotal(1437)).toBe("1.437 vagas encontradas");
  });
});
