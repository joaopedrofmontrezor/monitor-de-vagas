"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import type { FormEvent } from "react";

import { MAX_BUSCA, MAX_CIDADE, montarBusca } from "@/lib/filtros";
import type { Filtros } from "@/types/vaga";

type Props = {
  filtros: Filtros;
};

function lerRemoto(valor: FormDataEntryValue | null): boolean | undefined {
  if (valor === "true") return true;
  if (valor === "false") return false;
  return undefined;
}

export function FormularioFiltros({ filtros }: Props) {
  const router = useRouter();

  function buscar(evento: FormEvent<HTMLFormElement>) {
    evento.preventDefault();
    const dados = new FormData(evento.currentTarget);
    const busca = montarBusca({
      q: String(dados.get("q") ?? ""),
      cidade: String(dados.get("cidade") ?? ""),
      remoto: lerRemoto(dados.get("remoto")),
      pagina: 1,
    });
    router.push(`/vagas${busca}`);
  }

  const remoto = filtros.remoto === undefined ? "" : String(filtros.remoto);

  return (
    <form
      role="search"
      onSubmit={buscar}
      className="grid gap-3 rounded-lg border border-slate-200 bg-white p-4 sm:grid-cols-[2fr_1.5fr_1fr_auto]"
    >
      <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
        Buscar no título
        <input
          name="q"
          type="search"
          defaultValue={filtros.q ?? ""}
          maxLength={MAX_BUSCA}
          placeholder="dados, front-end, marketing..."
          className="rounded-md border border-slate-300 px-3 py-2 font-normal"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
        Cidade
        <input
          name="cidade"
          type="text"
          defaultValue={filtros.cidade ?? ""}
          maxLength={MAX_CIDADE}
          placeholder="São Paulo"
          className="rounded-md border border-slate-300 px-3 py-2 font-normal"
        />
      </label>
      <label className="flex flex-col gap-1 text-sm font-medium text-slate-700">
        Modalidade
        <select
          name="remoto"
          defaultValue={remoto}
          className="rounded-md border border-slate-300 px-3 py-2 font-normal"
        >
          <option value="">Todas</option>
          <option value="true">Só remotas</option>
          <option value="false">Presencial ou híbrida</option>
        </select>
      </label>
      <div className="flex items-end gap-2">
        <button
          type="submit"
          className="rounded-md bg-emerald-700 px-4 py-2 text-sm font-semibold text-white hover:bg-emerald-800"
        >
          Buscar
        </button>
        <Link href="/vagas" className="px-2 py-2 text-sm text-slate-600 hover:underline">
          Limpar
        </Link>
      </div>
    </form>
  );
}
