"use client";

import { EstadoErro } from "@/components/Estados";

type Props = {
  error: Error;
  reset: () => void;
};

export default function ErroVagas({ reset }: Props) {
  return <EstadoErro mensagem="Algo deu errado ao montar a página." tentarDeNovo={reset} />;
}
