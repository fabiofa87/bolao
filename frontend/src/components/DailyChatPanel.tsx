import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { api } from "../lib/api";
import { formatTime } from "../lib/format";
import type { ChatMessage, DailyChat } from "../types";

const schema = z.object({
  body: z.string().trim().min(1, "Escreva uma mensagem.").max(500, "Use ate 500 caracteres.")
});
type FormData = z.infer<typeof schema>;

export function DailyChatPanel() {
  const [groupId, setGroupId] = useState<number | undefined>();
  const bottomRef = useRef<HTMLDivElement>(null);
  const queryClient = useQueryClient();
  const form = useForm<FormData>({ resolver: zodResolver(schema) });

  const chat = useQuery({
    queryKey: ["chat", groupId],
    queryFn: () =>
      api<DailyChat>(`/chat/${groupId ? `?pool_group=${groupId}` : ""}`),
    refetchInterval: 5000
  });

  useEffect(() => {
    if (!groupId && chat.data?.selected_group) {
      setGroupId(chat.data.selected_group.id);
    }
  }, [chat.data?.selected_group, groupId]);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat.data?.messages.length]);

  const send = useMutation({
    mutationFn: (data: FormData) =>
      api<ChatMessage>("/chat/", {
        method: "POST",
        body: JSON.stringify({ body: data.body, pool_group: groupId })
      }),
    onSuccess: () => {
      form.reset({ body: "" });
      queryClient.invalidateQueries({ queryKey: ["chat"] });
    }
  });

  return (
    <section className="panel mt-7 overflow-hidden rounded-[2rem]">
      <div className="flex flex-col gap-3 border-b border-black/8 p-5 md:flex-row md:items-center md:justify-between">
        <div>
          <span className="text-xs font-black uppercase tracking-[0.24em] text-field/55">
            Chat diario
          </span>
          <strong className="mt-1 block text-2xl font-black">
            {chat.data?.selected_group?.name ?? "Seu grupo"}
          </strong>
          <small className="text-black/45">
            Mensagens de hoje: {chat.data?.chat_date ?? "..."}
          </small>
        </div>
        {chat.data && chat.data.groups.length > 1 && (
          <select
            value={groupId ?? chat.data.selected_group?.id ?? ""}
            onChange={(event) => setGroupId(Number(event.target.value))}
            className="rounded-2xl border border-black/15 bg-white px-4 py-3 font-bold"
          >
            {chat.data.groups.map((group) => (
              <option key={group.id} value={group.id}>
                {group.name}
              </option>
            ))}
          </select>
        )}
      </div>

      <div className="flex h-[58vh] flex-col gap-3 overflow-y-auto bg-white/45 p-4 md:p-6">
        {chat.isLoading && <p className="text-black/50">Carregando chat...</p>}
        {chat.error && <p className="text-red-700">{chat.error.message}</p>}
        {chat.data?.messages.map((message) => (
          <article key={message.id} className="rounded-3xl bg-white p-4 shadow-sm">
            <div className="mb-2 flex items-center justify-between gap-3">
              <strong>{message.user_name}</strong>
              <small className="text-black/40">{formatTime(message.created_at)}</small>
            </div>
            <p className="whitespace-pre-wrap break-words text-black/75">{message.body}</p>
          </article>
        ))}
        {chat.data && chat.data.messages.length === 0 && (
          <p className="rounded-3xl bg-white p-5 text-center text-black/50">
            Nenhuma mensagem hoje. Seja a primeira pessoa a provocar.
          </p>
        )}
        <div ref={bottomRef} />
      </div>

      <form
        onSubmit={form.handleSubmit((data) => send.mutate(data))}
        className="border-t border-black/8 bg-white p-4 md:p-5"
      >
        <label className="sr-only" htmlFor="chat-message">
          Mensagem
        </label>
        <textarea
          id="chat-message"
          rows={3}
          placeholder="Escreva uma mensagem para o grupo..."
          {...form.register("body")}
          className="w-full resize-none rounded-2xl border border-black/15 bg-paper px-4 py-3 outline-none focus:border-field"
        />
        <div className="mt-3 flex items-center justify-between gap-3">
          <p className="text-sm text-red-700">
            {form.formState.errors.body?.message ?? (send.error ? send.error.message : "")}
          </p>
          <button
            disabled={send.isPending || !chat.data?.selected_group}
            className="rounded-2xl bg-field px-5 py-3 font-black text-white disabled:opacity-40"
          >
            Enviar
          </button>
        </div>
      </form>
    </section>
  );
}
