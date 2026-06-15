import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Navigate, Link } from "react-router-dom";
import { z } from "zod";
import { useSession } from "../hooks/useSession";
import { api } from "../lib/api";

const schema = z.object({
  email: z.string().email("Informe um e-mail válido."),
  password: z.string().min(1, "Informe sua senha.")
});
type FormData = z.infer<typeof schema>;

export function LoginPage() {
  const session = useSession();
  const queryClient = useQueryClient();
  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      api("/auth/login/", { method: "POST", body: JSON.stringify(data) }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["session"] })
  });

  if (session.data?.authenticated) return <Navigate to="/" replace />;

  return (
    <div className="grid min-h-screen bg-ink md:grid-cols-2">
      <section className="flex items-end bg-[radial-gradient(circle_at_top_left,_#256b50,_#071c17_65%)] p-8 text-white md:p-14">
        <div className="max-w-xl">
          <span className="font-black uppercase tracking-[0.28em] text-lime">Copa 2026</span>
          <h1 className="mt-5 text-5xl font-black leading-none md:text-7xl">
            Palpite sem demora. Ranking sem discussão.
          </h1>
          <p className="mt-6 max-w-md text-lg text-white/65">
            O bolão privado da turma, com prazo automático e cada ponto auditável.
          </p>
        </div>
      </section>
      <section className="flex items-center justify-center bg-paper p-6">
        <form
          className="panel w-full max-w-md rounded-[2rem] p-7 md:p-10"
          onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
        >
          <h2 className="text-3xl font-black">Entrar</h2>
          <p className="mt-2 text-black/55">Use o e-mail cadastrado no convite.</p>
          <label className="mt-7 block text-sm font-bold">
            E-mail
            <input
              {...form.register("email")}
              type="email"
              className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3 outline-none focus:border-field"
            />
          </label>
          <p className="mt-1 text-sm text-red-700">{form.formState.errors.email?.message}</p>
          <label className="mt-4 block text-sm font-bold">
            Senha
            <input
              {...form.register("password")}
              type="password"
              className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3 outline-none focus:border-field"
            />
          </label>
          <p className="mt-1 text-sm text-red-700">{form.formState.errors.password?.message}</p>
          {mutation.error && <p className="mt-4 text-sm text-red-700">{mutation.error.message}</p>}
          <button className="mt-7 w-full rounded-2xl bg-field px-5 py-4 font-black text-white hover:bg-ink">
            Entrar no bolão
          </button>
          <p className="mt-5 text-center text-sm text-black/50">
            Primeiro acesso? Abra o link de convite enviado pelo administrador.
          </p>
        </form>
      </section>
    </div>
  );
}

