import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { MatchCard } from "../components/MatchCard";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";
import type { Match } from "../types";

export function MatchesPage() {
  const [showAll, setShowAll] = useState(false);
  const matches = useQuery({
    queryKey: ["matches"],
    queryFn: () => api<Match[]>("/matches/")
  });
  const groups = useMemo(() => {
    const source = (matches.data ?? []).filter(
      (match) => showAll || new Date(match.kickoff_at) >= new Date(Date.now() - 4 * 60 * 60 * 1000)
    );
    return source.reduce<Record<string, Match[]>>((result, match) => {
      const date = match.kickoff_at.slice(0, 10);
      result[date] = [...(result[date] ?? []), match];
      return result;
    }, {});
  }, [matches.data, showAll]);

  return (
    <>
      <div className="flex flex-col justify-between gap-5 md:flex-row md:items-end">
        <div>
          <span className="text-xs font-black uppercase tracking-[0.24em] text-field/55">Seus jogos</span>
          <h2 className="mt-2 text-4xl font-black tracking-tight md:text-5xl">
            Cada placar conta.
          </h2>
        </div>
        <div className="flex rounded-full bg-black/5 p-1">
          <button onClick={() => setShowAll(false)} className={`rounded-full px-4 py-2 text-sm font-bold ${!showAll ? "bg-white shadow" : ""}`}>Próximos</button>
          <button onClick={() => setShowAll(true)} className={`rounded-full px-4 py-2 text-sm font-bold ${showAll ? "bg-white shadow" : ""}`}>Todos</button>
        </div>
      </div>

      <section className="panel mt-7 rounded-[2rem] p-5 md:p-6">
        <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
          <div>
            <span className="text-xs font-black uppercase tracking-[0.24em] text-field/55">Regras de pontuação</span>
            <h3 className="mt-1 text-2xl font-black">Como os pontos são calculados</h3>
          </div>
          <div className="grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
            <div className="rounded-2xl bg-lime/60 p-4">
              <strong className="block text-xl">PE</strong>
              <span className="block text-sm font-bold">Placar Exato</span>
              <span className="mt-1 block text-sm">5 pontos</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4">
              <strong className="block text-xl">RC</strong>
              <span className="block text-sm font-bold">Placar Errado e Resultado Certo</span>
              <span className="mt-1 block text-sm">2 pontos</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4">
              <strong className="block text-xl">EE</strong>
              <span className="block text-sm font-bold">Empate com Placar Errado</span>
              <span className="mt-1 block text-sm">+1 ponto</span>
            </div>
            <div className="rounded-2xl bg-white/70 p-4">
              <strong className="block text-xl">GV</strong>
              <span className="block text-sm font-bold">Acertou o Gol do Vencedor</span>
              <span className="mt-1 block text-sm">+1 ponto</span>
            </div>
          </div>
        </div>
      </section>

      {matches.isLoading && <p className="mt-10">Carregando partidas...</p>}
      {matches.error && <p className="mt-10 text-red-700">{matches.error.message}</p>}
      <div className="mt-9 space-y-10">
        {Object.entries(groups).map(([date, dateMatches]) => (
          <section key={date}>
            <h3 className="mb-4 text-sm font-black uppercase tracking-wider text-black/45">
              {formatDate(`${date}T12:00:00Z`)}
            </h3>
            <div className="grid gap-4 lg:grid-cols-2">
              {dateMatches?.map((match) => <MatchCard key={match.id} match={match} />)}
            </div>
          </section>
        ))}
      </div>
    </>
  );
}
