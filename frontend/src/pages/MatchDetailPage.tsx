import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect } from "react";
import { useForm } from "react-hook-form";
import { Link, useParams } from "react-router-dom";
import { z } from "zod";
import { TeamMark } from "../components/TeamMark";
import { api } from "../lib/api";
import { formatDate, formatStage, formatTime } from "../lib/format";
import type { Match, Prediction } from "../types";

const schema = z.object({
  home_score: z.coerce.number().int().min(0).max(99),
  away_score: z.coerce.number().int().min(0).max(99)
});
type FormData = z.infer<typeof schema>;

export function MatchDetailPage() {
  const { id } = useParams();
  const queryClient = useQueryClient();
  const match = useQuery({
    queryKey: ["match", id],
    queryFn: () => api<Match>(`/matches/${id}/`)
  });
  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  useEffect(() => {
    if (match.data?.my_prediction) {
      form.reset({
        home_score: match.data.my_prediction.home_score,
        away_score: match.data.my_prediction.away_score
      });
    }
  }, [match.data?.my_prediction, form]);
  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      api<Prediction>(`/matches/${id}/prediction/`, {
        method: "PUT",
        body: JSON.stringify(data)
      }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["match", id] });
      queryClient.invalidateQueries({ queryKey: ["matches"] });
    }
  });

  if (match.isLoading) return <p>Carregando partida...</p>;
  if (!match.data) return <p>Partida não encontrada.</p>;
  const data = match.data;
  const hasResult = data.scoring_home !== null;

  return (
    <div className="mx-auto max-w-3xl">
      <Link to="/" className="text-sm font-bold text-field/60">← Voltar aos jogos</Link>
      <article className="panel mt-5 overflow-hidden rounded-[2rem]">
        <header className="bg-field p-6 text-white md:p-9">
          <div className="flex justify-between gap-4 text-sm text-white/60">
            <span>{formatStage(data.stage)}</span>
            <span>{formatDate(data.kickoff_at)} · {formatTime(data.kickoff_at)}</span>
          </div>
          <div className="mt-8 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
            <div className="flex justify-end"><TeamMark team={data.home_team} /></div>
            <span className="text-sm font-black text-lime">X</span>
            <TeamMark team={data.away_team} />
          </div>
          {hasResult && (
            <div className="mt-7 text-center text-5xl font-black">
              {data.scoring_home} <span className="text-white/25">:</span> {data.scoring_away}
            </div>
          )}
        </header>

        <div className="p-6 md:p-9">
          {!data.is_locked ? (
            <form onSubmit={form.handleSubmit((values) => mutation.mutate(values))}>
              <h2 className="text-2xl font-black">Seu palpite</h2>
              <p className="mt-1 text-sm text-black/55">
                Você pode editar até {formatTime(data.lock_at)}.
              </p>
              <div className="mt-6 grid grid-cols-[1fr_auto_1fr] items-center gap-4">
                <input aria-label={`Gols de ${data.home_team.name}`} type="number" min="0" {...form.register("home_score")} className="w-full rounded-2xl border border-black/15 bg-white p-4 text-center text-3xl font-black" />
                <span className="font-black text-black/25">X</span>
                <input aria-label={`Gols de ${data.away_team.name}`} type="number" min="0" {...form.register("away_score")} className="w-full rounded-2xl border border-black/15 bg-white p-4 text-center text-3xl font-black" />
              </div>
              {mutation.error && <p className="mt-4 text-sm text-red-700">{mutation.error.message}</p>}
              {mutation.isSuccess && <p className="mt-4 text-sm font-bold text-field">Palpite salvo.</p>}
              <button className="mt-6 w-full rounded-2xl bg-lime px-5 py-4 font-black text-ink">
                {data.my_prediction ? "Atualizar palpite" : "Confirmar palpite"}
              </button>
            </form>
          ) : (
            <div>
              <h2 className="text-2xl font-black">Palpites da turma</h2>
              <p className="mt-1 text-sm text-black/55">O prazo encerrou e os palpites foram revelados.</p>
              <div className="mt-6 divide-y divide-black/8">
                {data.predictions.map((prediction) => (
                  <div key={prediction.id} className="flex items-center justify-between py-4">
                    <span className="font-bold">{prediction.user_name}</span>
                    <span className="rounded-full bg-black/5 px-4 py-2 font-black">
                      {prediction.home_score} x {prediction.away_score}
                      {hasResult && <small className="ml-2 text-field/55">{prediction.points} pts</small>}
                    </span>
                  </div>
                ))}
                {!data.predictions.length && <p className="py-5 text-black/50">Nenhum palpite enviado.</p>}
              </div>
            </div>
          )}
        </div>
      </article>
    </div>
  );
}

