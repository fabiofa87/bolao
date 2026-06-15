import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useNavigate } from "react-router-dom";
import { useSession } from "../hooks/useSession";
import { api } from "../lib/api";

export function ProfilePage() {
  const session = useSession();
  const queryClient = useQueryClient();
  const navigate = useNavigate();
  const logout = useMutation({
    mutationFn: () => api("/auth/logout/", { method: "POST" }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["session"] });
      navigate("/entrar");
    }
  });
  return (
    <div className="mx-auto max-w-xl">
      <h2 className="text-4xl font-black">Seu perfil</h2>
      <div className="panel mt-7 rounded-[2rem] p-7">
        <span className="text-sm text-black/45">Nome no ranking</span>
        <strong className="mt-1 block text-2xl">{session.data?.user?.display_name}</strong>
        <span className="mt-6 block text-sm text-black/45">E-mail</span>
        <strong className="mt-1 block">{session.data?.user?.email}</strong>
        <button onClick={() => logout.mutate()} className="mt-8 w-full rounded-2xl border border-red-700/20 px-5 py-3 font-bold text-red-700">
          Sair da conta
        </button>
      </div>
    </div>
  );
}

