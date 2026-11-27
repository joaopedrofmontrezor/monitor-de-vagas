import type { Vaga } from "@/types/vaga";

export function criarVaga(campos: Partial<Vaga> = {}): Vaga {
  return {
    id: 1,
    fonte: "greenhouse",
    tipo: "estagio",
    titulo: "Estágio em Engenharia de Dados",
    empresa: "BTG Pactual",
    cidade: "São Paulo - SP",
    remoto: false,
    url: "https://job-boards.greenhouse.io/btgpactual/jobs/1",
    publicada_em: "2026-11-10T12:00:00Z",
    coletada_em: "2026-11-27T12:00:00Z",
    ...campos,
  };
}
