import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { connectMockIntegration, listIntegrations } from "@/api/integrations";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Spinner } from "@/components/ui/Spinner";
import { getIntegrationStatusLabel } from "@/shared/lib/labels";

const providerLabels: Record<string, string> = {
  google_calendar: "Google Calendar",
  linkedin: "LinkedIn",
  telegram: "Telegram",
};

export function IntegrationsPage() {
  const queryClient = useQueryClient();
  const integrationsQuery = useQuery({ queryKey: ["integrations"], queryFn: listIntegrations });
  const connectMutation = useMutation({
    mutationFn: connectMockIntegration,
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: ["integrations"] });
    },
  });

  if (integrationsQuery.isLoading) {
    return <Spinner />;
  }
  if (integrationsQuery.error) {
    return <Alert>Не удалось загрузить интеграции.</Alert>;
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      {(integrationsQuery.data ?? []).map((integration) => (
        <Card key={integration.id} className="space-y-5">
          <div className="flex items-start justify-between gap-4">
            <div>
              <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Интеграция</p>
              <h3 className="mt-2 text-2xl font-bold text-white">{providerLabels[integration.provider]}</h3>
            </div>
            <Badge>{getIntegrationStatusLabel(integration.status)}</Badge>
          </div>
          <p className="text-sm leading-6 text-slate-400">
            {integration.provider === "google_calendar"
              ? "Тестовое подключение показывает, как позже будут синхронизироваться напоминания и события."
              : "Интеграция уже заложена в архитектуру backend и frontend, но полный сценарий появится позже."}
          </p>
          <Button
            className="w-full"
            variant="secondary"
            disabled
          >
            В разработке
          </Button>
        </Card>
      ))}
    </div>
  );
}
