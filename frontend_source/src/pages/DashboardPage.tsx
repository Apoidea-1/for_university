import { useMemo } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import {
  Area,
  AreaChart,
  CartesianGrid,
  Cell,
  Line,
  LineChart,
  Pie,
  PieChart,
  ResponsiveContainer,
  Tooltip,
  type TooltipProps,
  XAxis,
  YAxis,
} from "recharts";
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
          <div className="mt-6 h-[280px]">
            <ResponsiveContainer width="100%" height="100%">
              <AreaChart data={overviewQuery.data?.activity_timeline ?? []} margin={{ top: 4, right: 4, left: -16, bottom: 0 }}>
                <defs>
                  <linearGradient id="dash-grad-teal" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%"  stopColor="#14b8a6" stopOpacity={0.28} />
                    <stop offset="95%" stopColor="#14b8a6" stopOpacity={0} />
                  </linearGradient>
                  <linearGradient id="dash-grad-amber" x1="0" y1="0" x2="0" y2="1">
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
                  fill="url(#dash-grad-teal)"
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
                  fill="url(#dash-grad-amber)"
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
          {(categoriesAnalyticsQuery.data ?? []).length === 0 ? (
            <div className="mt-6 flex h-[220px] flex-col items-center justify-center gap-3 rounded-2xl border border-dashed border-white/10 text-center">
              <svg xmlns="http://www.w3.org/2000/svg" width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" className="text-slate-500">
                <circle cx="12" cy="12" r="10" /><path d="M12 8v4M12 16h.01" />
              </svg>
              <p className="text-sm font-medium text-slate-400">Категории не назначены</p>
              <p className="max-w-[240px] text-xs text-slate-500">Назначьте категории контактам, чтобы увидеть распределение сети.</p>
            </div>
          ) : (
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
          )}
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
