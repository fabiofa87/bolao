import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { RankingRow } from "../types";

export function RankingPage() {
  const ranking = useQuery({
    queryKey: ["ranking"],
    queryFn: () => api<RankingRow[]>("/ranking/")
  });
  return (
    <div className="mx-auto max-w-4xl">
      <span className="text-xs font-black uppercase tracking-[0.24em] text-field/55">Classificação</span>
      <h2 className="mt-2 text-4xl font-black md:text-5xl">Ranking da turma</h2>
      <div className="panel mt-8 overflow-hidden rounded-[2rem]">
        {ranking.data?.map((row) => (
          <div key={row.user_id} className="grid grid-cols-[3.5rem_1fr_auto_auto] items-center gap-3 border-b border-black/8 px-5 py-5 last:border-0 md:px-8">
            <span className={`text-2xl font-black ${row.rank <= 3 ? "text-field" : "text-black/30"}`}>{row.rank}º</span>
            <div>
              <strong className="block">{row.display_name}</strong>
              <small className="text-black/45">
                {row.prediction_points} nos jogos
                {row.adjustment_points !== 0 && ` · ${row.adjustment_points} de saldo`}
              </small>
            </div>
            <span className="rounded-full bg-white/80 px-3 py-2 text-sm font-black" title="LT: acertou o resultado correto">
              LT {row.correct_result_hits}
              {row.adjustment_exact_hits > 0 && (
                <small className="ml-1 text-black/45">+{row.adjustment_exact_hits}</small>
              )}
            </span>
            <span className="rounded-full bg-lime px-4 py-2 font-black">{row.total_points} pts</span>
          </div>
        ))}
        {!ranking.isLoading && !ranking.data?.length && <p className="p-8 text-black/50">O ranking ainda está vazio.</p>}
      </div>
    </div>
  );
}

