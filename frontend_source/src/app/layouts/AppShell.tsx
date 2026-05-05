import { Link, NavLink, Outlet } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/shared/lib/cn";

const navItems = [
  { label: "Панель", to: "/dashboard" },
  { label: "Контакты", to: "/contacts" },
  { label: "Напоминания", to: "/reminders" },
  { label: "Аналитика", to: "/analytics" },
  { label: "Интеграции", to: "/integrations" },
];

export function AppShell() {
  const { logout, user } = useAuth();

  return (
    <div className="min-h-screen">
      <div className="workspace-shell">
        <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="glass-panel sticky top-6 h-fit p-4">
            <Link to="/dashboard" className="block rounded-3xl bg-mesh p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">NetWorkPilot</p>
              <h1 className="mt-3 text-2xl font-extrabold text-white">Держите сеть контактов под контролем.</h1>
              <p className="mt-2 text-sm text-slate-300">
                Личная система для знакомств, карьерных контактов, встреч и повторных касаний.
              </p>
            </Link>

            <nav className="mt-6 flex gap-2 overflow-x-auto lg:flex-col">
              {navItems.map((item) => (
                <NavLink
                  key={item.to}
                  to={item.to}
                  className={({ isActive }) =>
                    cn(
                      "rounded-2xl px-4 py-3 text-sm font-semibold text-slate-300 transition hover:bg-white/5 hover:text-white",
                      isActive && "bg-accent text-slate-950 hover:bg-accent",
                    )
                  }
                >
                  {item.label}
                </NavLink>
              ))}
            </nav>

            <div className="mt-6 rounded-2xl border border-borderSoft bg-panelSoft p-4">
              <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Профиль</p>
              <p className="mt-3 text-base font-semibold text-white">{user?.full_name}</p>
              <p className="mt-1 text-sm text-slate-400">{user?.email}</p>
              <Button className="mt-4 w-full" variant="secondary" onClick={logout}>
                Выйти
              </Button>
            </div>
          </aside>

          <main className="space-y-6">
            <header className="glass-panel flex flex-col justify-between gap-4 p-5 sm:flex-row sm:items-center">
              <div>
                <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Рабочее пространство</p>
                <h2 className="mt-1 text-2xl font-bold text-white">Развивайте профессиональные связи системно.</h2>
              </div>
              <div className="flex flex-wrap gap-3">
                <Link to="/contacts/new">
                  <Button>Добавить контакт</Button>
                </Link>
                <Link to="/reminders">
                  <Button variant="secondary">Создать напоминание</Button>
                </Link>
              </div>
            </header>

            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
