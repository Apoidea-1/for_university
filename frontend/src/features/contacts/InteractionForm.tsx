import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { interactionTypeLabels } from "@/shared/lib/labels";

const schema = z.object({
  type: z.enum(["meeting", "message", "call", "project", "other"]),
  title: z.string({ required_error: "Введите заголовок" }).min(2, "Введите короткий заголовок"),
  description: z.string().optional(),
  interaction_date: z.string({ required_error: "Укажите дату и время" }).min(1, "Укажите дату и время"),
});

type FormValues = z.infer<typeof schema>;

export function InteractionForm({
  onSubmit,
}: {
  onSubmit: (payload: FormValues) => Promise<unknown>;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      type: "message",
      title: "",
      description: "",
      interaction_date: new Date().toISOString().slice(0, 16),
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit({
      ...values,
      interaction_date: new Date(values.interaction_date).toISOString(),
    });
    form.reset({
      type: "message",
      title: "",
      description: "",
      interaction_date: new Date().toISOString().slice(0, 16),
    });
  });

  return (
    <Card className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Взаимодействие</p>
        <h3 className="mt-2 text-xl font-bold text-white">Зафиксируйте новое касание</h3>
      </div>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Select {...form.register("type")}>
          <option value="meeting">{interactionTypeLabels.meeting}</option>
          <option value="message">{interactionTypeLabels.message}</option>
          <option value="call">{interactionTypeLabels.call}</option>
          <option value="project">{interactionTypeLabels.project}</option>
          <option value="other">{interactionTypeLabels.other}</option>
        </Select>
        <Input {...form.register("title")} placeholder="Короткий заголовок" />
        <Input {...form.register("interaction_date")} type="datetime-local" />
        <Textarea {...form.register("description")} placeholder="Что произошло и к чему стоит вернуться дальше?" className="min-h-[110px]" />
        <Button className="w-full" type="submit" loading={form.formState.isSubmitting}>
          Сохранить взаимодействие
        </Button>
      </form>
    </Card>
  );
}
