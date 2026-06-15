import { Navigate } from "react-router-dom";
import { useSession } from "../hooks/useSession";

export function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const session = useSession();
  if (session.isLoading) {
    return <div className="grid min-h-screen place-items-center bg-paper font-bold">Carregando...</div>;
  }
  if (!session.data?.authenticated) return <Navigate to="/entrar" replace />;
  return children;
}

