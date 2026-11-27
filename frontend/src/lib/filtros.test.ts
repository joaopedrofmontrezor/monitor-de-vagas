import { describe, expect, it } from "vitest";

import { lerFiltros, montarBusca, temFiltro } from "@/lib/filtros";

describe("lerFiltros", () => {
  it("lê os filtros da URL", () => {
    expect(lerFiltros({ q: "dados", cidade: "São Paulo", remoto: "true", pagina: "3" })).toEqual({
      q: "dados",
      cidade: "São Paulo",
      remoto: true,
      pagina: 3,
    });
  });

  it("usa os padrões quando a URL não tem filtros", () => {
    expect(lerFiltros({})).toEqual({
      q: undefined,
      cidade: undefined,
      remoto: undefined,
      pagina: 1,
    });
  });

  it("ignora valores inválidos e espaços", () => {
    expect(lerFiltros({ q: "   ", remoto: "talvez", pagina: "-2" })).toEqual({
      q: undefined,
      cidade: undefined,
      remoto: undefined,
      pagina: 1,
    });
    expect(lerFiltros({ pagina: "1.5" }).pagina).toBe(1);
    expect(lerFiltros({ pagina: "abc" }).pagina).toBe(1);
  });

  it("entende remoto=false", () => {
    expect(lerFiltros({ remoto: "false" }).remoto).toBe(false);
  });

  it("usa o primeiro valor quando o parâmetro se repete", () => {
    expect(lerFiltros({ q: ["dados", "web"] }).q).toBe("dados");
  });

  it("corta textos maiores que o limite da API", () => {
    expect(lerFiltros({ q: "a".repeat(150) }).q).toHaveLength(100);
    expect(lerFiltros({ cidade: "b".repeat(150) }).cidade).toHaveLength(120);
  });
});

describe("montarBusca", () => {
  it("gera a URL só com os filtros preenchidos", () => {
    expect(montarBusca({ q: "dados", remoto: true, pagina: 1 })).toBe("?q=dados&remoto=true");
  });

  it("omite a página 1 e inclui as outras", () => {
    expect(montarBusca({ pagina: 1 })).toBe("");
    expect(montarBusca({ q: "web", pagina: 2 })).toBe("?q=web&pagina=2");
  });

  it("codifica acentos e espaços", () => {
    expect(montarBusca({ cidade: " São Paulo " })).toBe("?cidade=S%C3%A3o+Paulo");
  });

  it("volta ao mesmo filtro depois de ler", () => {
    const busca = "?q=dados&cidade=Campinas&remoto=false&pagina=4";
    const params = Object.fromEntries(new URLSearchParams(busca));

    expect(montarBusca(lerFiltros(params))).toBe(busca);
  });
});

describe("temFiltro", () => {
  it("é falso sem filtros, mesmo em outra página", () => {
    expect(temFiltro({ pagina: 3 })).toBe(false);
  });

  it("conta remoto=false como filtro", () => {
    expect(temFiltro({ remoto: false, pagina: 1 })).toBe(true);
  });
});
