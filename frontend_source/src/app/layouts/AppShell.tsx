import { useDeferredValue, useEffect, useRef, useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Link, NavLink, Outlet } from "react-router-dom";

import { listContacts } from "@/api/contacts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { useAuth } from "@/hooks/useAuth";
import { cn } from "@/shared/lib/cn";

const navItems = [
  { label: "Панель", to: "/dashboard" },
  { label: "Контакты", to: "/contacts" },
  { label: "Сеть", to: "/network" },
  { label: "Напоминания", to: "/reminders" },
  { label: "Аналитика", to: "/analytics" },
  { label: "Интеграции", to: "/integrations" },
];

export function AppShell() {
  const { logout, user } = useAuth();
  const [search, setSearch] = useState("");
  const [isSearchOpen, setIsSearchOpen] = useState(false);
  const deferredSearch = useDeferredValue(search.trim());
  const searchRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!searchRef.current?.contains(event.target as Node)) {
        setIsSearchOpen(false);
      }
    }
    document.addEventListener("mousedown", handlePointerDown);
    return () => {
      document.removeEventListener("mousedown", handlePointerDown);
    };
  }, []);

  const searchQuery = useQuery({
    queryKey: ["header-contact-search", deferredSearch],
    queryFn: () => listContacts({ search: deferredSearch, per_page: 8 }),
    enabled: deferredSearch.length >= 2,
  });

  const searchResults = searchQuery.data?.items ?? [];

  return (
    <div className="min-h-screen">
      <div className="workspace-shell">
        <div className="grid gap-5 xl:grid-cols-[280px_minmax(0,1fr)]">
          <aside className="glass-panel sticky top-6 h-fit p-4">
            <Link to="/dashboard" className="block rounded-3xl bg-mesh p-5">
              <p className="text-xs font-semibold uppercase tracking-[0.24em] text-accent">NetWorkPilot</p>
              <h1 className="mt-3 text-2xl font-extrabold text-white">Управляйте сетью контактов как рабочим активом.</h1>
              <p className="mt-2 text-sm text-slate-300">
                Контакты, связи, чаты, напоминания и AI-подсказки живут в одном защищённом рабочем пространстве.
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
              <Button className="mt-4 w-full" variant="secondary" onClick={() => void logout()}>
                Выйти
              </Button>
            </div>
          </aside>

          <main className="space-y-6">
            <header className="glass-panel flex flex-col gap-4 p-5">
              <div className="flex flex-col justify-between gap-4 lg:flex-row lg:items-start">
                <div>
                  <p className="text-sm font-semibold uppercase tracking-[0.24em] text-slate-500">Рабочее пространство</p>
                  <h2 className="mt-1 text-2xl font-bold text-white">Фокус на реальных связях, их качестве и следующем шаге.</h2>
                </div>
                <div className="flex flex-wrap gap-3">
                  <Link to="/contacts/new">
                    <Button>Добавить контакт</Button>
                  </Link>
                  <Link to="/network">
                    <Button variant="secondary">Открыть граф</Button>
                  </Link>
                </div>
              </div>

              <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
                <div ref={searchRef} className="relative w-full max-w-2xl">
                  <input
                    className="w-full rounded-2xl border border-borderSoft bg-panelSoft px-4 py-3 text-sm text-white outline-none transition focus:border-accent"
                    value={search}
                    onChange={(event) => {
                      setSearch(event.target.value);
                      setIsSearchOpen(true);
                    }}
                    onFocus={() => setIsSearchOpen(true)}
                    placeholder="Поиск по имени, компании, роли, заметкам, тегам, Telegram, телефону"
                  />

                  {isSearchOpen && deferredSearch.length >= 2 ? (
                    <div className="absolute left-0 right-0 top-[calc(100%+10px)] z-20 rounded-3xl border border-borderSoft bg-panel p-3 shadow-panel">
                      {searchQuery.isLoading ? (
                        <p className="px-3 py-2 text-sm text-slate-400">Ищу контакты…</p>
                      ) : searchResults.length ? (
                        <div className="space-y-2">
                          {searchResults.map((contact) => (
                            <Link
                              key={contact.id}
                              to={`/contacts/${contact.id}`}
                              className="block rounded-2xl px-3 py-3 transition hover:bg-white/5"
                              onClick={() => {
                                setIsSearchOpen(false);
                                setSearch("");
                              }}
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className="font-semibold text-white">
                                    {contact.first_name} {contact.last_name ?? ""}
                                  </p>
                                  <p className="mt-1 text-sm text-slate-400">
                                    {contact.role || "Без роли"} {contact.company ? `• ${contact.company}` : ""}
                                  </p>
                                </div>
                                <div className="flex flex-wrap gap-2">
                                  {contact.category ? <Badge>{contact.category.name}</Badge> : null}
                                  <Badge>{contact.importance_level}</Badge>
                                </div>
                              </div>
                            </Link>
                          ))}
                        </div>
                      ) : (
                        <p className="px-3 py-2 text-sm text-slate-400">Совпадений пока нет.</p>
                      )}
                    </div>
                  ) : null}
                </div>

                <div className="flex flex-wrap gap-2">
                  <Badge>SPA @ /app</Badge>
                  <Badge>Cookie session</Badge>
                  <Badge>Same-origin API</Badge>
                </div>
              </div>
            </header>

            <Outlet />
          </main>
        </div>
      </div>
    </div>
  );
}
