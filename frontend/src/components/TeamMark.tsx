import type { Team } from "../types";

export function TeamMark({ team }: { team: Team }) {
  return (
    <div className="flex min-w-0 items-center gap-3">
      {team.crest_url ? (
        <img src={team.crest_url} alt="" className="h-9 w-9 object-contain" />
      ) : (
        <span className="grid h-9 w-9 place-items-center rounded-full bg-field text-xs font-black text-white">
          {team.code || team.name.slice(0, 3).toUpperCase()}
        </span>
      )}
      <span className="truncate font-bold">{team.short_name || team.name}</span>
    </div>
  );
}

