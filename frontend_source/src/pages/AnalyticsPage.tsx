import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  Bar,
  BarChart,
  CartesianGrid,
  Cell,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
  XAxis,
  YAxis,
} from "recharts";

import { getAnalyticsOverview, getCategoryAnalytics, getStaleContacts } from "@/api/analytics";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { MetricCard } from "@/components/ui/MetricCard";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate } from "@/shared/lib/format";

function formatTick(dateStr: string) {
  const parts = dateStr.split("-");
  if (parts.length !== 3) return dateStr;
  const months = ["янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"];
  const m = parseInt(parts[1], 10) - 1;
  return `${parseInt(parts[2], 10)} ${months[m] ?? ""}`;
}

function ActivityTooltip({ active, payload, label }: TooltipProps<number, string>) {
  if (!active || !payload?.length) return null;
  return (
    <div className="rounded-xl border border-white/10 bg-[#0a1628] px-4 py-3 shadow-2xl">
      <p className="mb-2 text-[11px] font-semibold uppercase tracking-widest text-slate-500">{label}</p>
      {payload.map((entry) => (
        <div key={entry.dataKey} className="flex items-center gap-2 py-0.5">
          <span className="h-2 w-2 shrink-0 rounded-full" style={{ backgroundColor: entry.color }} />
          <span className="text-sm text-slate-400">
            {entry.dataKey === "contacts_added" ? "Контакты" : "Взаимодействия"}
          </span>
          <span className="ml-auto pl-4 text-sm font-bold text-white">{entry.value}</span>
        </div>
      ))}
    </div>
  );
}

export function AnalyticsPage() {
  const [days, setDays] = useState(21);
  const overviewQuery = useQuery({ queryKey: ["analytics-overview"], queryFn: getAnalyticsOverview });
  const categoriesQuery = useQuery({ queryKey: ["analytics-categories"], queryFn: getCategoryAnalytics });
  const staleQuery = useQuery({ queryKey: ["stale-contacts", days], queryFn: () => getStaleContacts(days) });

  if (overviewQuery.isLoading || categoriesQuery.isLoading || staleQuery.isLoading) {
    return <Spinner />;
  }
  if (overviewQuery.error || categoriesQuery.error || staleQuery.error) {
    return <Alert>Не удалось загрузить аналитику.</Alert>;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Контакты за 7 дней" value={overviewQuery.data?.new_contacts_7d ?? 0} />
        <MetricCard label="Контакты за 30 дней" value={overviewQuery.data?.new_contacts_30d ?? 0} />
        <MetricCard label="Взаимодействия за 7 дней" value={overviewQuery.data?.interactions_7d ?? 0} />
        <MetricCard label="Контакты без общения" value={overviewQuery.data?.stale_contacts_count ?? 0} />
      </section>

      <section className="grid gap-6 xl:grid-cols-2">
        <Card>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Динамика</p>
          <h3 className="mt-2 text-2xl font-bold text-white">Добавленные контакты и взаимодействия</h3>
          <div className="mt-6 h-[300px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overviewQuery.data?.activity_timeline ?? []} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="an-grad-teal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="an-grad-amber" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#f59e0b" stopOpacity={0.22} />
                    <stop offset="95%" stopColor="#f59e0b" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid stroke="rgba(255,255,255,0.04)" vertical={false} />
                <XAxis
                  dataKey="date"
                  stroke="#475569"
                  tickLine={false}
                  axisLine={false}
                  tickFormatter={formatTick}
                  tick={{ fontSize: 11, fill: "#475569" }}
                  interval="preserveStartEnd"
                />
                <YAxis
                  stroke="#475569"
                  tickLine={false}
                  axisLine={false}
                  tick={{ fontSize: 11, fill: "#475569" }}
                  allowDecimals={false}
                />
                <Tooltip content={<ActivityTooltip />} cursor={{ stroke: "rgba(255,255,255,0.08)", strokeWidth: 1 }} />
                <Area
                  type="monotone"
                  dataKey="contacts_added"
                  stroke="#14b8a6"
                  strokeWidth={2.5}
                  fill="url(#an-grad-teal)"
                  dot={false}
                  activeDot={{ r: 5, fill: "#14b8a6", stroke: "#0a1628", strokeWidth: 2.5 }}
                  animationDuration={1100}
                  animationEasing="ease-out"
                />
                <Area
                  type="monotone"
                  dataKey="interactions_logged"
                  stroke="#f59e0b"
                  strokeWidth={2.5}
                  fill="url(#an-grad-amber)"
                  dot={false}
                  activeDot={{ r: 5, fill: "#f59e0b", stroke: "#0a1628", strokeWidth: 2.5 }}
                  animationDuration={1400}
                  animationEasing="ease-out"
                />
              </AreaChart>
            </ResponsiveContainer>
          </div>
          <div className="mt-4 flex flex-wrap gap-5">
            <div className="flex items-center gap-2">
              <span className="h-px w-5 rounded-full bg-[#14b8a6]" />
              <span className="text-xs text-slate-400">Новые контакты</span>
            </div>
            <div className="flex items-center gap-2">
              <span className="h-px w-5 rounded-full bg-[#f59e0b]" />
              <span className="text-xs text-slate-400">Взаимодействия</span>
            </div>
          </div>
        </Card>

        <Card>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Категории</p>
          <h3 className="mt-2 text-2xl font-bold text-white">Состав сети контактов</h3>
          {(categoriesQuery.data ?? []).length === 0 ? (
            <div className="mt-6 flex h-[260px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/10 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500">
                <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
              </svg>
              <p className="text-sm font-medium text-slate-400">Категории не назначены</p>
              <p className="max-w-[260px] text-xs text-slate-500">Откройте карточку контакта и выберите категорию — тогда здесь появится диаграмма.</p>
            </div>
          ) : (
            <div className="mt-6 grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
              <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <PieChart>
                    <Pie data={categoriesQuery.data ?? []} dataKey="count" nameKey="category_name" outerRadius={92}>
                      {(categoriesQuery.data ?? []).map((item) => (
                        <Cell key={item.category_name} fill={item.color} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
              <div className="h-[260px]">
                <ResponsiveContainer width="100%" height="100%">
                  <BarChart data={categoriesQuery.data ?? []} layout="vertical" margin={{ left: 20 }}>
                    <XAxis type="number" stroke="#64748b" tickLine={false} axisLine={false} allowDecimals={false} />
                    <YAxis type="category" dataKey="category_name" stroke="#64748b" tickLine={false} axisLine={false} width={100} />
                    <Tooltip />
                    <Bar dataKey="count" radius={[0, 10, 10, 0]}>
                      {(categoriesQuery.data ?? []).map((item) => (
                        <Cell key={item.category_name} fill={item.color} />
                      ))}
                    </Bar>
                  </BarChart>
                </ResponsiveContainer>
              </div>
            </div>
          )}
        </Card>
      </section>

      <section className="space-y-4">
        <Card className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Контакты без общения</p>
            <h3 className="mt-2 text-2xl font-bold text-white">Люди, с которыми пора связаться</h3>
          </div>
          <div className="w-full max-w-[180px]">
            <label className="field-label">Дней без взаимодействия</label>
            <Input
              type="number"
              min={1}
              max={365}
              value={days}
              onChange={(event) => setDays(Number(event.target.value))}
            />
          </div>
        </Card>

        <Card className="overflow-hidden p-0">
          <div className="overflow-x-auto">
            <table className="min-w-full text-sm">
              <thead className="bg-white/5 text-left text-slate-400">
                <tr>
                  <th className="px-5 py-4 font-medium">Контакт</th>
                  <th className="px-5 py-4 font-medium">Компания</th>
                  <th className="px-5 py-4 font-medium">Последнее взаимодействие</th>
                  <th className="px-5 py-4 font-medium">Дней без активности</th>
                </tr>
              </thead>
              <tbody>
                {(staleQuery.data ?? []).map((contact) => (
                  <tr key={contact.id} className="border-t border-white/5">
                    <td className="px-5 py-4 text-white">
                      {contact.first_name} {contact.last_name ?? ""}
                    </td>
                    <td className="px-5 py-4 text-slate-300">{contact.company || "Без компании"}</td>
                    <td className="px-5 py-4 text-slate-300">{formatDate(contact.last_interaction_date)}</td>
                    <td className="px-5 py-4 text-slate-300">{contact.days_since_last_interaction ?? "Никогда"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      </section>
    </div>
  );
}
