import { useQuery } from "@tanstack/react-query";
import { useMemo, useState } from "react";
import { DailyChatPanel } from "../components/DailyChatPanel";
import { MatchCard } from "../components/MatchCard";
import { api } from "../lib/api";
import { formatDate } from "../lib/format";
import type { Match } from "../types";

type ResultsTab = "upcoming" | "all" | "rules" | "chat";

const baseRules = [
  ["PE", "Placar Exato", "5 pontos"],
  ["RC", "Resultado certo com placar errado", "2 pontos"],
  ["EE", "Empate certo com placar errado", "3 pontos"],
  ["GV", "Vitoria certa com gols exatos do vencedor", "3 pontos"]
];

const stageMultipliers = [
  ["Fase de grupos", "1x"],
  ["16 avos de final", "2x"],
  ["Oitavas de final", "3x"],
  ["Quartas de final", "4x"],
  ["Semifinal", "5x"],
  ["Disputa de terceiro lugar", "5x"],
  ["Final", "10x"]
];

export function MatchesPage() {
  const [activeTab, setActiveTab] = useState<ResultsTab>("upcoming");
  const matches = useQuery({
    queryKey: ["matches"],
    queryFn: () => api<Match[]>("/matches/"),
    refetchInterval: 60_000
  });
  const groups = useMemo(() => {
    const source = (matches.data ?? []).filter(
      (match) =>
        activeTab === "all" || new Date(match.kickoff_at) >= new Date(Date.now() - 4 * 60 * 60 * 1000)
    );
    return source.reduce<Record<string, Match[]>>((result, match) => {
      const date = match.kickoff_at.slice(0, 10);
      result[date] = [...(result[date] ?? []), match];
      return result;
    }, {});
  }, [matches.data, activeTab]);

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
          <button
            onClick={() => setActiveTab("upcoming")}
            className={`rounded-full px-4 py-2 text-sm font-bold ${activeTab === "upcoming" ? "bg-white shadow" : ""}`}
          >
            Proximos
          </button>
          <button
            onClick={() => setActiveTab("all")}
            className={`rounded-full px-4 py-2 text-sm font-bold ${activeTab === "all" ? "bg-white shadow" : ""}`}
          >
            Todos
          </button>
          <button
            onClick={() => setActiveTab("rules")}
            className={`rounded-full px-4 py-2 text-sm font-bold ${activeTab === "rules" ? "bg-white shadow" : ""}`}
          >
            Regras
          </button>
          <button
            onClick={() => setActiveTab("chat")}
            className={`rounded-full px-4 py-2 text-sm font-bold ${activeTab === "chat" ? "bg-white shadow" : ""}`}
          >
            Chat
          </button>
        </div>
      </div>

      {activeTab === "chat" ? (
        <DailyChatPanel />
      ) : activeTab === "rules" ? (
        <section className="panel mt-7 rounded-[2rem] p-5 md:p-7">
          <div>
            <span className="text-xs font-black uppercase tracking-[0.24em] text-field/55">
              Regras de pontuacao
            </span>
            <h3 className="mt-1 text-3xl font-black">Pontuacao sem conversa fiada</h3>
            <p className="mt-2 max-w-2xl text-sm text-black/55">
              Primeiro calculamos os pontos-base do palpite. Depois multiplicamos pela fase da partida.
            </p>
          </div>

          <div className="mt-7 grid gap-4 lg:grid-cols-2">
            <div className="rounded-3xl bg-white/70 p-5">
              <h4 className="text-xl font-black">Pontos-base</h4>
              <div className="mt-4 space-y-3">
                {baseRules.map(([code, label, points]) => (
                  <div key={code} className="flex items-center justify-between gap-4 rounded-2xl bg-paper p-4">
                    <div>
                      <strong className="mr-2 text-lg">{code}</strong>
                      <span className="font-bold">{label}</span>
                    </div>
                    <span className="text-sm font-black text-field">{points}</span>
                  </div>
                ))}
              </div>
            </div>

            <div className="rounded-3xl bg-white/70 p-5">
              <h4 className="text-xl font-black">Multiplicador por fase</h4>
              <div className="mt-4 space-y-3">
                {stageMultipliers.map(([stage, multiplier]) => (
                  <div key={stage} className="flex items-center justify-between gap-4 rounded-2xl bg-paper p-4">
                    <span className="font-bold">{stage}</span>
                    <span className="rounded-full bg-lime px-3 py-1 text-sm font-black text-ink">
                      {multiplier}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          </div>

          <div className="mt-5 rounded-3xl bg-field p-5 text-white">
            <strong className="block">Exemplo</strong>
            <p className="mt-1 text-sm text-white/75">
              Placar exato na final vale 5 x 10 = 50 pontos. Resultado certo nas quartas vale 2 x 4 = 8 pontos.
            </p>
          </div>
        </section>
      ) : (
        <>
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
      )}
    </>
  );
}
