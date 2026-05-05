import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { reminderTypeLabels } from "@/shared/lib/labels";
import type { Contact } from "@/types/api";

const schema = z.object({
  contact_id: z.string().optional(),
  title: z.string({ required_error: "Введите заголовок" }).min(2, "Введите заголовок"),
  description: z.string().optional(),
  due_date: z.string({ required_error: "Укажите дату и время" }).min(1, "Укажите дату и время"),
  reminder_type: z.enum(["follow_up", "congratulation", "reconnect", "custom"]),
});

type FormValues = z.infer<typeof schema>;

export function ReminderForm({
  contacts,
  defaultContactId,
  onSubmit,
}: {
  contacts: Contact[];
  defaultContactId?: number;
  onSubmit: (payload: {
    contact_id?: number | null;
    title: string;
    description?: string;
    due_date: string;
    reminder_type: string;
  }) => Promise<unknown>;
}) {
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      contact_id: defaultContactId ? String(defaultContactId) : "",
      title: "",
      description: "",
      due_date: new Date(Date.now() + 1000 * 60 * 60 * 24 * 5).toISOString().slice(0, 16),
      reminder_type: "follow_up",
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    await onSubmit({
      contact_id: values.contact_id ? Number(values.contact_id) : null,
      title: values.title,
      description: values.description || undefined,
      due_date: new Date(values.due_date).toISOString(),
      reminder_type: values.reminder_type,
    });
    form.reset({
      ...values,
      title: "",
      description: "",
    });
  });

  return (
    <Card className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Напоминание</p>
        <h3 className="mt-2 text-xl font-bold text-white">Запланируйте следующее действие</h3>
      </div>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Select {...form.register("contact_id")}>
          <option value="">Без привязки к контакту</option>
          {contacts.map((contact) => (
            <option key={contact.id} value={contact.id}>
              {contact.first_name} {contact.last_name ?? ""} {contact.company ? `• ${contact.company}` : ""}
            </option>
          ))}
        </Select>
        <Input {...form.register("title")} placeholder="Что нужно сделать" />
        <Textarea {...form.register("description")} placeholder="Контекст, шаблон сообщения или детали" className="min-h-[100px]" />
        <Input {...form.register("due_date")} type="datetime-local" />
        <Select {...form.register("reminder_type")}>
          <option value="follow_up">{reminderTypeLabels.follow_up}</option>
          <option value="congratulation">{reminderTypeLabels.congratulation}</option>
          <option value="reconnect">{reminderTypeLabels.reconnect}</option>
          <option value="custom">{reminderTypeLabels.custom}</option>
        </Select>
        <Button className="w-full" type="submit" loading={form.formState.isSubmitting}>
          Сохранить напоминание
        </Button>
      </form>
    </Card>
  );
}
