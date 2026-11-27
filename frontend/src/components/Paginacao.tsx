import Link from "next/link";

import { montarBusca } from "@/lib/filtros";
import type { Filtros } from "@/types/vaga";

type Props = {
  filtros: Filtros;
  totalPaginas: number;
};

const ESTILO_LINK = "rounded-md border border-slate-300 bg-white px-3 py-1.5 hover:bg-slate-50";

export function Paginacao({ filtros, totalPaginas }: Props) {
  if (totalPaginas <= 1) return null;
  const { pagina } = filtros;

  return (
    <nav aria-label="Paginação" className="flex items-center justify-between text-sm">
      {pagina > 1 ? (
        <Link href={`/vagas${montarBusca({ ...filtros, pagina: pagina - 1 })}`} className={ESTILO_LINK}>
          Anterior
        </Link>
      ) : (
        <span />
      )}
      <span className="text-slate-600">
        Página {pagina} de {totalPaginas}
      </span>
      {pagina < totalPaginas ? (
        <Link href={`/vagas${montarBusca({ ...filtros, pagina: pagina + 1 })}`} className={ESTILO_LINK}>
          Próxima
        </Link>
      ) : (
        <span />
      )}
    </nav>
  );
}
