const FORMATO_DATA = new Intl.DateTimeFormat("pt-BR", {
  day: "2-digit",
  month: "2-digit",
  year: "numeric",
  timeZone: "America/Sao_Paulo",
});

export function formatarData(iso: string | null): string | null {
  if (!iso) return null;
  const data = new Date(iso);
  return Number.isNaN(data.getTime()) ? null : FORMATO_DATA.format(data);
}

export function formatarTotal(total: number): string {
  if (total === 1) return "1 vaga encontrada";
  return `${total.toLocaleString("pt-BR")} vagas encontradas`;
}
