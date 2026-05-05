import { useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import type { Category } from "@/types/api";

const schema = z.object({
  first_name: z.string({ required_error: "Введите имя" }).min(1, "Введите имя"),
  source_where_met: z.string().optional(),
  category_id: z.string().optional(),
  notes: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

export function QuickContactForm({
  categories,
  onSubmit,
}: {
  categories: Category[];
  onSubmit: (payload: { first_name: string; source_where_met?: string; category_id?: number | null; notes?: string }) => Promise<unknown>;
}) {
  const [status, setStatus] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      first_name: "",
      source_where_met: "",
      category_id: "",
      notes: "",
    },
  });

  const handleSubmit = form.handleSubmit(async (values) => {
    try {
      await onSubmit({
        first_name: values.first_name,
        source_where_met: values.source_where_met || undefined,
        category_id: values.category_id ? Number(values.category_id) : null,
        notes: values.notes || undefined,
      });
      setStatus("Контакт добавлен.");
      form.reset();
    } catch (submitError) {
      setStatus(submitError instanceof Error ? submitError.message : "Не удалось добавить контакт");
    }
  });

  return (
    <Card className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Быстрое добавление</p>
        <h3 className="mt-2 text-xl font-bold text-white">Добавьте контакт меньше чем за 20 секунд.</h3>
      </div>
      <form className="space-y-4" onSubmit={handleSubmit}>
        <Input {...form.register("first_name")} placeholder="Имя" />
        <Input {...form.register("source_where_met")} placeholder="Где познакомились" />
        <Select {...form.register("category_id")}>
          <option value="">Выберите категорию</option>
          {categories.map((category) => (
            <option key={category.id} value={category.id}>
              {category.name}
            </option>
          ))}
        </Select>
        <Textarea {...form.register("notes")} placeholder="Короткая заметка" className="min-h-[100px]" />
        {status ? <Alert variant={status === "Контакт добавлен." ? "success" : "error"}>{status}</Alert> : null}
        <Button className="w-full" type="submit" loading={form.formState.isSubmitting}>
          Добавить контакт
        </Button>
      </form>
    </Card>
  );
}
