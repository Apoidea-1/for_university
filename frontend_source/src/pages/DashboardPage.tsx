import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Cell, Line, LineChart, Pie, PieChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import { Link } from "react-router-dom";

import { getAnalyticsOverview, getCategoryAnalytics } from "@/api/analytics";
import { listContacts, quickAddContact } from "@/api/contacts";
import { listCategories } from "@/api/lookups";
import { listReminders } from "@/api/reminders";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { ContactTable } from "@/features/contacts/ContactTable";
import { QuickContactForm } from "@/features/contacts/QuickContactForm";
import { MetricCard } from "@/components/ui/MetricCard";
import { Spinner } from "@/components/ui/Spinner";
import { formatDateTime } from "@/shared/lib/format";
import { getReminderTypeLabel } from "@/shared/lib/labels";

export function DashboardPage() {
  const queryClient = useQueryClient();
  const overviewQuery = useQuery({ queryKey: ["analytics-overview"], queryFn: getAnalyticsOverview });
  const categoriesAnalyticsQuery = useQuery({ queryKey: ["analytics-categories"], queryFn: getCategoryAnalytics });
  const categoriesQuery = useQuery({ queryKey: ["categories"], queryFn: listCategories });
  const recentContactsQuery = useQuery({
    queryKey: ["contacts", "recent-dashboard"],
    queryFn: () => listContacts({ sort_by: "created_at", sort_order: "desc" }),
  });
  const activeRemindersQuery = useQuery({
    queryKey: ["reminders", "active-dashboard"],
    queryFn: () => listReminders("active"),
  });

  const quickAddMutation = useMutation({
    mutationFn: quickAddContact,
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["contacts"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-overview"] }),
        queryClient.invalidateQueries({ queryKey: ["analytics-categories"] }),
      ]);
    },
  });

  const recentContacts = useMemo(() => recentContactsQuery.data?.items.slice(0, 5) ?? [], [recentContactsQuery.data]);

  if (overviewQuery.isLoading || categoriesQuery.isLoading) {
    return <Spinner />;
  }
  if (overviewQuery.error || categoriesQuery.error || categoriesAnalyticsQuery.error || recentContactsQuery.error || activeRemindersQuery.error) {
    return <Alert>Не удалось загрузить данные панели.</Alert>;
  }

  return (
    <div className="space-y-6">
      <section className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
        <MetricCard label="Новые контакты за 7 дней" value={overviewQuery.data?.new_contacts_7d ?? 0} detail="Свежие знакомства за последнюю неделю." />
        <MetricCard label="Взаимодействия за 30 дней" value={overviewQuery.data?.interactions_30d ?? 0} detail="Все зафиксированные касания." />
        <MetricCard label="Активные напоминания" value={overviewQuery.data?.active_reminders ?? 0} detail="Задачи, срок которых ещё не истёк." />
        <MetricCard label="Просроченные напоминания" value={overviewQuery.data?.overdue_reminders ?? 0} detail="Требуют внимания прямо сейчас." />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.2fr)_380px]">
        <Card>
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Динамика активности</p>
              <h3 className="mt-2 text-2xl font-bold text-white">Нетворкинг за последние 14 дней</h3>
            </div>
            <Badge>{overviewQuery.data?.stale_contacts_count ?? 0} без общения</Badge>
          </div>
          <div className="mt-6 h-[300px]">
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

        <QuickContactForm
          categories={categoriesQuery.data ?? []}
          onSubmit={async (payload) => {
            await quickAddMutation.mutateAsync(payload);
          }}
        />
      </section>

      <section className="grid gap-6 xl:grid-cols-[minmax(0,1.1fr)_minmax(0,0.9fr)]">
        <Card>
          <div className="flex items-center justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Распределение по категориям</p>
              <h3 className="mt-2 text-2xl font-bold text-white">Где сосредоточена сеть контактов</h3>
            </div>
            <Link to="/analytics" className="text-sm font-semibold text-slate-300 hover:text-white">
              Открыть аналитику
            </Link>
          </div>
          <div className="mt-6 grid gap-4 lg:grid-cols-[260px_minmax(0,1fr)]">
            <div className="h-[220px]">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie data={categoriesAnalyticsQuery.data ?? []} dataKey="count" nameKey="category_name" innerRadius={60} outerRadius={90}>
                    {(categoriesAnalyticsQuery.data ?? []).map((item) => (
                      <Cell key={item.category_name} fill={item.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="space-y-3">
              {(categoriesAnalyticsQuery.data ?? []).map((item) => (
                <div key={item.category_name} className="flex items-center justify-between rounded-2xl border border-white/10 bg-white/5 px-4 py-3">
                  <div className="flex items-center gap-3">
                    <span className="h-3 w-3 rounded-full" style={{ backgroundColor: item.color }} />
                    <p className="font-medium text-slate-200">{item.category_name}</p>
                  </div>
                  <p className="text-sm text-slate-400">{item.count}</p>
                </div>
              ))}
            </div>
          </div>
        </Card>

        <Card>
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Ближайшие задачи</p>
          <h3 className="mt-2 text-2xl font-bold text-white">Напоминания на ближайшее время</h3>
          <div className="mt-6 space-y-3">
            {(activeRemindersQuery.data ?? []).slice(0, 5).map((reminder) => (
              <div key={reminder.id} className="rounded-2xl border border-white/10 bg-white/5 p-4">
                <div className="flex items-start justify-between gap-3">
                  <div>
                    <p className="font-semibold text-white">{reminder.title}</p>
                    <p className="mt-1 text-sm text-slate-400">
                      {reminder.contact ? `${reminder.contact.first_name} ${reminder.contact.last_name ?? ""}` : "Общее напоминание"}
                    </p>
                  </div>
                  <Badge>{getReminderTypeLabel(reminder.reminder_type)}</Badge>
                </div>
                <p className="mt-3 text-sm text-slate-300">{reminder.description || "Без описания."}</p>
                <p className="mt-3 text-xs uppercase tracking-[0.18em] text-slate-500">{formatDateTime(reminder.due_date)}</p>
              </div>
            ))}
          </div>
        </Card>
      </section>

      <section>
        <div className="mb-4 flex items-center justify-between gap-4">
          <div>
            <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Последние контакты</p>
            <h3 className="mt-2 text-2xl font-bold text-white">Недавно добавленные люди</h3>
          </div>
          <Link to="/contacts" className="text-sm font-semibold text-slate-300 hover:text-white">
            Все контакты
          </Link>
        </div>
        <ContactTable contacts={recentContacts} />
      </section>
    </div>
  );
}
