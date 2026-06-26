import { Link } from "react-router-dom";
import { formatStage, formatTime } from "../lib/format";
import type { Match } from "../types";
import { TeamMark } from "./TeamMark";

const liveStatuses = new Set(["IN_PLAY", "PAUSED", "LIVE"]);
const finishedStatuses = new Set(["FINISHED"]);

export const isMatchLive = (match: Match) => liveStatuses.has(match.status);

export const getMatchStatusLabel = (match: Match) => {
  if (isMatchLive(match)) return "Em andamento";
  if (finishedStatuses.has(match.status)) return "Encerrado";
  return match.is_locked ? "Fechado" : `Ate ${formatTime(match.lock_at)}`;
};

export const isExactHit = (match: Match) =>
  match.scoring_home !== null &&
  match.scoring_away !== null &&
  match.my_prediction?.home_score === match.scoring_home &&
  match.my_prediction.away_score === match.scoring_away;

export function MatchCard({ match }: { match: Match }) {
  const hasResult = match.scoring_home !== null;
  const live = isMatchLive(match);
  const exactHit = isExactHit(match);

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
          className={`inline-flex items-center gap-2 rounded-full px-3 py-1 text-xs font-bold ${
            live ? "bg-mint text-field" : match.is_locked ? "bg-black/5 text-black/50" : "bg-mint text-field"
          }`}
        >
          {live && <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />}
          {getMatchStatusLabel(match)}
        </span>
      </div>

      <div className="grid grid-cols-[1fr_auto] items-center gap-x-5 gap-y-4">
        <TeamMark team={match.home_team} />
        <strong className="text-xl">
          {hasResult ? match.scoring_home : match.my_prediction?.home_score ?? "-"}
        </strong>
        <TeamMark team={match.away_team} />
        <strong className="text-xl">
          {hasResult ? match.scoring_away : match.my_prediction?.away_score ?? "-"}
        </strong>
      </div>

      <div className="mt-5 border-t border-black/8 pt-4 text-sm text-black/55">
        {hasResult ? (
          <span className="flex flex-wrap items-center gap-2">
            <span>
              Seu palpite:{" "}
              {match.my_prediction
                ? `${match.my_prediction.home_score} x ${match.my_prediction.away_score} · ${match.my_prediction.points} pts`
                : "nao enviado"}
            </span>
            {exactHit && (
              <span className="rounded-full bg-lime px-2.5 py-1 text-xs font-black text-ink">
                ✓ LT
              </span>
            )}
          </span>
        ) : match.my_prediction ? (
          "Palpite enviado. Voce ainda pode editar."
        ) : (
          "Toque para enviar seu palpite."
        )}
      </div>
    </Link>
  );
}
