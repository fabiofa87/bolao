import { NavLink, Outlet } from "react-router-dom";
import { useSession } from "../hooks/useSession";

const links = [
  { to: "/", label: "Jogos" },
  { to: "/ranking", label: "Ranking" },
  { to: "/perfil", label: "Perfil" }
];

export function AppLayout() {
  const { data } = useSession();
  return (
    <div className="min-h-screen pb-24 md:pb-0">
      <header className="bg-ink text-white">
        <div className="mx-auto flex max-w-6xl items-center justify-between px-5 py-5">
          <div>
            <span className="text-xs font-bold uppercase tracking-[0.25em] text-lime">
              Copa do Mundo
            </span>
            <h1 className="text-xl font-black tracking-tight">Bolão 2026</h1>
          </div>
          <span className="hidden text-sm text-white/70 md:block">
            Olá, {data?.user?.display_name}
          </span>
        </div>
        <nav className="mx-auto hidden max-w-6xl gap-2 px-5 pb-4 md:flex">
          {links.map((link) => (
            <NavLink
              key={link.to}
              to={link.to}
              className={({ isActive }) =>
                `rounded-full px-4 py-2 text-sm font-bold ${
                  isActive ? "bg-lime text-ink" : "text-white/70 hover:bg-white/10"
                }`
              }
            >
              {link.label}
            </NavLink>
          ))}
        </nav>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-7 md:px-5 md:py-10">
        <Outlet />
      </main>

      <nav className="fixed inset-x-0 bottom-0 z-20 grid grid-cols-3 border-t border-black/10 bg-white/95 px-3 py-2 backdrop-blur md:hidden">
        {links.map((link) => (
          <NavLink
            key={link.to}
            to={link.to}
            className={({ isActive }) =>
              `rounded-xl py-3 text-center text-sm font-bold ${
                isActive ? "bg-field text-white" : "text-ink/60"
              }`
            }
          >
            {link.label}
          </NavLink>
        ))}
      </nav>
    </div>
  );
}
