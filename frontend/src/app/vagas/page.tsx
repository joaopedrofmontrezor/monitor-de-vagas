import type { Metadata } from "next";
import { Suspense } from "react";

import { CarregandoVagas } from "@/components/Estados";
import { FormularioFiltros } from "@/components/FormularioFiltros";
import { ListaVagas } from "@/components/ListaVagas";
import { lerFiltros, montarBusca } from "@/lib/filtros";
import type { ParametrosDaUrl } from "@/types/vaga";

export const metadata: Metadata = {
  title: "Vagas | Monitor de Vagas",
};

type Props = {
  searchParams: Promise<ParametrosDaUrl>;
};

export default async function PaginaVagas({ searchParams }: Props) {
  const filtros = lerFiltros(await searchParams);
  const chave = montarBusca(filtros);

  return (
    <section className="space-y-5">
      <h1 className="text-2xl font-bold">Vagas de estágio</h1>
      <FormularioFiltros key={`filtros${chave}`} filtros={filtros} />
      <Suspense key={`lista${chave}`} fallback={<CarregandoVagas />}>
        <ListaVagas filtros={filtros} />
      </Suspense>
    </section>
  );
}
