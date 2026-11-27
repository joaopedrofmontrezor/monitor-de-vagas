import { EstadoErro, EstadoVazio } from "@/components/Estados";
import { Paginacao } from "@/components/Paginacao";
import { VagaCard } from "@/components/VagaCard";
import { ErroApi, listarVagas } from "@/lib/api";
import { temFiltro } from "@/lib/filtros";
import { formatarTotal } from "@/lib/formatar";
import type { Filtros, PaginaVagas } from "@/types/vaga";

type Props = {
  filtros: Filtros;
  buscar?: (filtros: Filtros) => Promise<PaginaVagas>;
};

export async function ListaVagas({ filtros, buscar = listarVagas }: Props) {
  let pagina: PaginaVagas;
  try {
    pagina = await buscar(filtros);
  } catch (erro) {
    const mensagem = erro instanceof ErroApi ? erro.message : "Erro inesperado.";
    return <EstadoErro mensagem={mensagem} />;
  }

  if (pagina.itens.length === 0) {
    return <EstadoVazio comFiltro={temFiltro(filtros) || filtros.pagina > 1} />;
  }

  return (
    <div className="space-y-4">
      <p className="text-sm text-slate-600">{formatarTotal(pagina.total)}</p>
      <ul className="space-y-3">
        {pagina.itens.map((vaga) => (
          <li key={vaga.id}>
            <VagaCard vaga={vaga} />
          </li>
        ))}
      </ul>
      <Paginacao filtros={filtros} totalPaginas={pagina.total_paginas} />
    </div>
  );
}
