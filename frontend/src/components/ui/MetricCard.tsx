import { Card } from "@/components/ui/Card";

export function MetricCard({
  label,
  value,
  detail,
}: {
  label: string;
  value: string | number;
  detail?: string;
}) {
  return (
    <Card className="space-y-2">
      <p className="text-sm text-slate-400">{label}</p>
      <p className="text-3xl font-extrabold tracking-tight text-white">{value}</p>
      {detail ? <p className="text-sm text-slate-500">{detail}</p> : null}
    </Card>
  );
}
