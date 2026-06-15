import { useQuery } from "@tanstack/react-query";
import { api } from "../lib/api";
import type { User } from "../types";

type Session = { authenticated: boolean; user: User | null };

export const useSession = () =>
  useQuery({
    queryKey: ["session"],
    queryFn: () => api<Session>("/auth/session/"),
    staleTime: 60_000,
    retry: false
  });

