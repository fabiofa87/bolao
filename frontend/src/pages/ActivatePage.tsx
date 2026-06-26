import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useForm } from "react-hook-form";
import { Navigate, useSearchParams } from "react-router-dom";
import { z } from "zod";
import { useSession } from "../hooks/useSession";
import { api } from "../lib/api";

const schema = z
  .object({
    email: z.string().email("Informe um e-mail valido.").optional().or(z.literal("")),
    display_name: z.string().min(2, "Informe seu nome."),
    password: z.string().min(8, "Use pelo menos 8 caracteres."),
    confirm: z.string()
  })
  .refine((data) => data.password === data.confirm, {
    message: "As senhas nao coincidem.",
    path: ["confirm"]
  });
type FormData = z.infer<typeof schema>;

type InviteInfo = {
  kind: "INDIVIDUAL" | "SHARED";
  is_shared: boolean;
  email: string;
  display_name: string;
  pool_group: string;
  remaining_uses: number | null;
  expires_at: string;
};

export function ActivatePage() {
  useSession();
  const [params] = useSearchParams();
  const token = params.get("token") ?? "";
  const queryClient = useQueryClient();
  const form = useForm<FormData>({ resolver: zodResolver(schema) });
  const invite = useQuery({
    queryKey: ["invite", token],
    queryFn: () => api<InviteInfo>(`/auth/invite/?token=${encodeURIComponent(token)}`),
    enabled: Boolean(token),
    retry: false
  });
  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      api("/auth/activate/", {
        method: "POST",
        body: JSON.stringify({
          token,
          email: invite.data?.is_shared ? data.email : undefined,
          display_name: data.display_name,
          password: data.password
        })
      }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ["session"] })
  });

  if (mutation.isSuccess) return <Navigate to="/" replace />;
  const isShared = Boolean(invite.data?.is_shared);

  return (
    <div className="grid min-h-screen place-items-center bg-ink p-5">
      <form
        onSubmit={form.handleSubmit((data) => mutation.mutate(data))}
        className="w-full max-w-lg rounded-[2rem] bg-paper p-7 md:p-10"
      >
        <span className="text-xs font-black uppercase tracking-[0.25em] text-field/60">
          Convite
        </span>
        <h1 className="mt-2 text-4xl font-black">Prepare seu palpite</h1>
        {!token && <p className="mt-5 text-red-700">O link de convite esta incompleto.</p>}
        {invite.isLoading && <p className="mt-5 text-black/55">Carregando convite...</p>}
        {invite.error && <p className="mt-5 text-red-700">{invite.error.message}</p>}
        {invite.data?.pool_group && (
          <p className="mt-5 rounded-2xl bg-white/70 p-4 text-sm font-bold text-field">
            Grupo: {invite.data.pool_group}
            {invite.data.remaining_uses !== null && ` · ${invite.data.remaining_uses} usos restantes`}
          </p>
        )}
        {isShared && (
          <>
            <label className="mt-7 block font-bold">
              Seu e-mail
              <input
                type="email"
                {...form.register("email")}
                className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3"
              />
            </label>
            <p className="text-sm text-red-700">{form.formState.errors.email?.message}</p>
          </>
        )}
        <label className="mt-7 block font-bold">
          Como quer aparecer no ranking?
          <input
            {...form.register("display_name")}
            placeholder={invite.data?.display_name}
            className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3"
          />
        </label>
        <p className="text-sm text-red-700">{form.formState.errors.display_name?.message}</p>
        <label className="mt-4 block font-bold">
          Crie uma senha
          <input
            type="password"
            {...form.register("password")}
            className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3"
          />
        </label>
        <p className="text-sm text-red-700">{form.formState.errors.password?.message}</p>
        <label className="mt-4 block font-bold">
          Confirme a senha
          <input
            type="password"
            {...form.register("confirm")}
            className="mt-2 w-full rounded-2xl border border-black/15 bg-white px-4 py-3"
          />
        </label>
        <p className="text-sm text-red-700">{form.formState.errors.confirm?.message}</p>
        {mutation.error && <p className="mt-4 text-red-700">{mutation.error.message}</p>}
        <button
          disabled={!token || invite.isError || mutation.isPending}
          className="mt-7 w-full rounded-2xl bg-lime px-5 py-4 font-black text-ink disabled:opacity-40"
        >
          Ativar minha conta
        </button>
      </form>
    </div>
  );
}
