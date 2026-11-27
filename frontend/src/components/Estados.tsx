import Link from "next/link";

export function CarregandoVagas() {
  return (
    <div role="status" aria-live="polite" className="space-y-3">
      <span className="sr-only">Carregando vagas...</span>
      {[0, 1, 2].map((i) => (
        <div key={i} className="h-24 animate-pulse rounded-lg bg-slate-200" />
      ))}
    </div>
  );
}

type PropsVazio = {
  comFiltro: boolean;
};

export function EstadoVazio({ comFiltro }: PropsVazio) {
  return (
    <div className="rounded-lg border border-dashed border-slate-300 bg-white p-8 text-center">
      <p className="font-medium text-slate-800">Nenhuma vaga encontrada.</p>
      {comFiltro ? (
        <p className="mt-2 text-sm text-slate-600">
          Tente outros termos ou{" "}
          <Link href="/vagas" className="text-emerald-700 hover:underline">
            limpe os filtros
          </Link>
          .
        </p>
      ) : (
        <p className="mt-2 text-sm text-slate-600">
          A coleta ainda não trouxe vagas. Rode <code>make coletar</code> ou espere o worker.
        </p>
      )}
    </div>
  );
}

type PropsErro = {
  mensagem: string;
  tentarDeNovo?: () => void;
};

export function EstadoErro({ mensagem, tentarDeNovo }: PropsErro) {
  return (
    <div role="alert" className="rounded-lg border border-red-200 bg-red-50 p-6 text-center">
      <p className="font-medium text-red-800">Não deu para carregar as vagas.</p>
      <p className="mt-1 text-sm text-red-700">{mensagem}</p>
      {tentarDeNovo && (
        <button
          type="button"
          onClick={tentarDeNovo}
          className="mt-3 rounded-md border border-red-300 bg-white px-3 py-1.5 text-sm text-red-800 hover:bg-red-100"
        >
          Tentar de novo
        </button>
      )}
    </div>
  );
}
