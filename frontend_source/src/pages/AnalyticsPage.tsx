import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Bar, BarChart, Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { getAnalyticsOverview, getCategoryAnalytics, getStaleContacts } from "@/api/analytics";
import { Alert } from "@/components/ui/Alert";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { MetricCard } from "@/components/ui/MetricCard";
import { Spinner } from "@/components/ui/Spinner";
import { formatDate } from "@/shared/lib/format";

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
          <div className="mt-6 h-[320px]">
            <ResponsiveContainer width="100%" height="100%">
              <LineChart data={overviewQuery.data?.activity_timeline ?? []}>
                <XAxis dataKey="date" stroke="#64748b" tickLine={false} axisLine={false} />
                <YAxis stroke="#64748b" tickLine={false} axisLine={false} />
                <Tooltip />
                <Line type="monotone" dataKey="contacts_added" stroke="#14b8a6" strokeWidth={3} dot={false} />
                <Line type="monotone" dataKey="interactions_logged" stroke="#f59e0b" strokeWidth={3} dot={false} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        </Card>

        <Card>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Категории</p>
          <h3 className="mt-2 text-2xl font-bold text-white">Состав сети контактов</h3>
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
                  <XAxis type="number" stroke="#64748b" tickLine={false} axisLine={false} />
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
