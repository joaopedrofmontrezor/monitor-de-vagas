import { formatarData } from "@/lib/formatar";
import type { Vaga } from "@/types/vaga";

type Props = {
  vaga: Vaga;
};

export function VagaCard({ vaga }: Props) {
  const publicada = formatarData(vaga.publicada_em);
  const data = publicada ? `Publicada em ${publicada}` : `Coletada em ${formatarData(vaga.coletada_em)}`;

  return (
    <article className="rounded-lg border border-slate-200 bg-white p-4 shadow-sm transition hover:border-slate-300">
      <h2 className="text-lg font-semibold text-slate-900">
        <a
          href={vaga.url}
          target="_blank"
          rel="noopener noreferrer"
          className="hover:text-emerald-700 hover:underline"
        >
          {vaga.titulo}
        </a>
      </h2>
      <p className="mt-1 text-sm text-slate-700">{vaga.empresa ?? "Empresa não informada"}</p>
      <div className="mt-3 flex flex-wrap items-center gap-2 text-xs">
        {vaga.cidade && (
          <span className="rounded-full bg-slate-100 px-2 py-1 text-slate-700">{vaga.cidade}</span>
        )}
        {vaga.remoto && (
          <span className="rounded-full bg-emerald-100 px-2 py-1 font-medium text-emerald-800">
            Remoto
          </span>
        )}
        <span className="text-slate-500">{data}</span>
        <span className="text-slate-400">via {vaga.fonte}</span>
      </div>
    </article>
  );
}
