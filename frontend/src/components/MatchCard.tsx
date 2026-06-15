import { Link } from "react-router-dom";
import { formatStage, formatTime } from "../lib/format";
import type { Match } from "../types";
import { TeamMark } from "./TeamMark";

export function MatchCard({ match }: { match: Match }) {
  const hasResult = match.scoring_home !== null;
  return (
    <Link
      to={`/jogos/${match.id}`}
      className="panel block rounded-3xl p-5 transition hover:-translate-y-0.5 hover:border-field/30"
    >
      <div className="mb-5 flex items-center justify-between gap-3">
        <span className="text-xs font-black uppercase tracking-wider text-field/60">
          {formatStage(match.stage)}
        </span>
        <span
          className={`rounded-full px-3 py-1 text-xs font-bold ${
            match.is_locked ? "bg-black/5 text-black/50" : "bg-mint text-field"
          }`}
        >
          {match.is_locked ? "Fechado" : `Até ${formatTime(match.lock_at)}`}
        </span>
      </div>

      <div className="grid grid-cols-[1fr_auto] items-center gap-x-5 gap-y-4">
        <TeamMark team={match.home_team} />
        <strong className="text-xl">{hasResult ? match.scoring_home : match.my_prediction?.home_score ?? "–"}</strong>
        <TeamMark team={match.away_team} />
        <strong className="text-xl">{hasResult ? match.scoring_away : match.my_prediction?.away_score ?? "–"}</strong>
      </div>

      <div className="mt-5 border-t border-black/8 pt-4 text-sm text-black/55">
        {hasResult
          ? `Seu palpite: ${match.my_prediction ? `${match.my_prediction.home_score} x ${match.my_prediction.away_score} · ${match.my_prediction.points} pts` : "não enviado"}`
          : match.my_prediction
            ? "Palpite enviado. Você ainda pode editar."
            : "Toque para enviar seu palpite."}
      </div>
    </Link>
  );
}

