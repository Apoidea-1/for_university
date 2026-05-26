import { useMemo, useState } from "react";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";
import { useMutation } from "@tanstack/react-query";

import { suggestContactMetadata } from "@/api/ai";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { Select } from "@/components/ui/Select";
import { Textarea } from "@/components/ui/Textarea";
import { BusinessCardScanner } from "@/features/contacts/BusinessCardScanner";
import { UnstructuredTextParser } from "@/features/contacts/UnstructuredTextParser";
import { importanceLabels } from "@/shared/lib/labels";
import type {
  BusinessCardScanResult,
  Category,
  Contact,
  ContactMetadataSuggestion,
  ImportanceLevel,
} from "@/types/api";

const schema = z.object({
  first_name: z.string({ required_error: "Введите имя" }).min(1, "Введите имя"),
  last_name: z.string().optional(),
  company: z.string().optional(),
  role: z.string().optional(),
  source_where_met: z.string().optional(),
  email: z.string().optional(),
  phone: z.string().optional(),
  telegram: z.string().optional(),
  linkedin: z.string().optional(),
  other_social: z.string().optional(),
  category_id: z.string().optional(),
  importance_level: z.enum(["low", "medium", "high", "strategic"]),
  notes: z.string().optional(),
  tag_names_text: z.string().optional(),
});

type FormValues = z.infer<typeof schema>;

function parseTags(raw?: string) {
  if (!raw) {
    return [];
  }
  return raw
    .split(",")
    .map((item) => item.trim())
    .filter(Boolean);
}

export interface ContactFormPayload {
  first_name: string;
  last_name?: string;
  company?: string;
  role?: string;
  source_where_met?: string;
  email?: string;
  phone?: string;
  telegram?: string;
  linkedin?: string;
  other_social?: string;
  category_id?: number | null;
  importance_level: ImportanceLevel;
  notes?: string;
  tag_names: string[];
}

export function ContactForm({
  categories,
  defaultContact,
  submitLabel,
  onSubmit,
  submitting,
}: {
  categories: Category[];
  defaultContact?: Contact;
  submitLabel: string;
  onSubmit: (payload: ContactFormPayload) => Promise<unknown>;
  submitting?: boolean;
}) {
  const [error, setError] = useState<string | null>(null);
  const [suggestion, setSuggestion] = useState<ContactMetadataSuggestion | null>(null);

  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      first_name: defaultContact?.first_name ?? "",
      last_name: defaultContact?.last_name ?? "",
      company: defaultContact?.company ?? "",
      role: defaultContact?.role ?? "",
      source_where_met: defaultContact?.source_where_met ?? "",
      email: defaultContact?.email ?? "",
      phone: defaultContact?.phone ?? "",
      telegram: defaultContact?.telegram ?? "",
      linkedin: defaultContact?.linkedin ?? "",
      other_social: defaultContact?.other_social ?? "",
      category_id: defaultContact?.category_id ? String(defaultContact.category_id) : "",
      importance_level: defaultContact?.importance_level ?? "medium",
      notes: defaultContact?.notes ?? "",
      tag_names_text: (defaultContact?.tags ?? []).map((tag) => tag.name).join(", "),
    },
  });

  const aiMutation = useMutation({
    mutationFn: async () =>
      suggestContactMetadata({
        notes: form.getValues("notes") ?? "",
        first_name: form.getValues("first_name"),
        company: form.getValues("company"),
        role: form.getValues("role"),
        source_where_met: form.getValues("source_where_met"),
        contact_id: defaultContact?.id,
      }),
    onSuccess: setSuggestion,
    onError: (mutationError) => {
      setError(mutationError instanceof Error ? mutationError.message : "Не удалось получить AI-подсказку.");
    },
  });

  const categoryNameMap = useMemo(
    () => new Map(categories.map((category) => [category.name.toLowerCase(), category])),
    [categories],
  );

  const applySuggestion = () => {
    if (!suggestion) {
      return;
    }
    const category = categoryNameMap.get(suggestion.category.toLowerCase());
    if (category) {
      form.setValue("category_id", String(category.id));
    }
    const currentTags = parseTags(form.getValues("tag_names_text"));
    const merged = Array.from(new Set([...currentTags, ...suggestion.tags]));
    form.setValue("tag_names_text", merged.join(", "));
    if (!form.getValues("notes")) {
      form.setValue("notes", suggestion.note_summary);
    }
  };

  const applyBusinessCard = (result: BusinessCardScanResult) => {
    const fallbackParts = (result.full_name || "").split(" ").filter(Boolean);
    if (result.first_name || fallbackParts[0]) {
      form.setValue("first_name", result.first_name || fallbackParts[0] || "");
    }
    if (result.last_name || fallbackParts.slice(1).join(" ")) {
      form.setValue("last_name", result.last_name || fallbackParts.slice(1).join(" "));
    }
    if (result.company) {
      form.setValue("company", result.company);
    }
    if (result.role) {
      form.setValue("role", result.role);
    }
    if (result.email) {
      form.setValue("email", result.email);
    }
    if (result.phone) {
      form.setValue("phone", result.phone);
    }
    if (result.telegram) {
      form.setValue("telegram", result.telegram);
    }
    if (result.linkedin) {
      form.setValue("linkedin", result.linkedin);
    }
    if (result.tags && result.tags.length > 0) {
      const currentTags = parseTags(form.getValues("tag_names_text"));
      const merged = Array.from(new Set([...currentTags, ...result.tags]));
      form.setValue("tag_names_text", merged.join(", "));

      if (merged.includes("bridge_contact") || merged.includes("mentor")) {
        form.setValue("importance_level", "high");
      } else if (merged.includes("peer")) {
        form.setValue("importance_level", "medium");
      } else {
        form.setValue("importance_level", "low");
      }
    }
    if (result.notes && !form.getValues("notes")) {
      form.setValue("notes", result.notes);
    }
  };

  const handleSubmit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      await onSubmit({
        first_name: values.first_name,
        last_name: values.last_name || undefined,
        company: values.company || undefined,
        role: values.role || undefined,
        source_where_met: values.source_where_met || undefined,
        email: values.email || undefined,
        phone: values.phone || undefined,
        telegram: values.telegram || undefined,
        linkedin: values.linkedin || undefined,
        other_social: values.other_social || undefined,
        category_id: values.category_id ? Number(values.category_id) : null,
        importance_level: values.importance_level,
        notes: values.notes || undefined,
        tag_names: parseTags(values.tag_names_text),
      });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось сохранить контакт.");
    }
  });

  return (
    <div className="grid gap-6 xl:grid-cols-[minmax(0,1fr)_360px]">
      <Card>
        <form className="space-y-6" onSubmit={handleSubmit}>
          <div className="grid gap-4 md:grid-cols-2">
            <div>
              <label className="field-label">Имя</label>
              <Input {...form.register("first_name")} placeholder="Елена" />
            </div>
            <div>
              <label className="field-label">Фамилия</label>
              <Input {...form.register("last_name")} placeholder="Петрова" />
            </div>
            <div>
              <label className="field-label">Компания</label>
              <Input {...form.register("company")} placeholder="Future HR" />
            </div>
            <div>
              <label className="field-label">Роль</label>
              <Input {...form.register("role")} placeholder="Recruiter" />
            </div>
            <div>
              <label className="field-label">Где познакомились</label>
              <Input {...form.register("source_where_met")} placeholder="Карьерный форум" />
            </div>
            <div>
              <label className="field-label">Важность</label>
              <Select {...form.register("importance_level")}>
                <option value="low">{importanceLabels.low}</option>
                <option value="medium">{importanceLabels.medium}</option>
                <option value="high">{importanceLabels.high}</option>
                <option value="strategic">{importanceLabels.strategic}</option>
              </Select>
            </div>
            <div>
              <label className="field-label">Email</label>
              <Input {...form.register("email")} placeholder="elena@futurehr.io" />
            </div>
            <div>
              <label className="field-label">Телефон</label>
              <Input {...form.register("phone")} placeholder="+7 999 000 00 00" />
            </div>
            <div>
              <label className="field-label">Telegram</label>
              <Input {...form.register("telegram")} placeholder="@elenahr" />
            </div>
            <div>
              <label className="field-label">LinkedIn</label>
              <Input {...form.register("linkedin")} placeholder="linkedin.com/in/elena" />
            </div>
            <div>
              <label className="field-label">Другая соцсеть</label>
              <Input {...form.register("other_social")} placeholder="X, Behance, GitHub и т.д." />
            </div>
            <div>
              <label className="field-label">Категория</label>
              <Select {...form.register("category_id")}>
                <option value="">Без категории</option>
                {categories.map((category) => (
                  <option key={category.id} value={category.id}>
                    {category.name}
                  </option>
                ))}
              </Select>
            </div>
          </div>

          <div>
            <label className="field-label">Заметки</label>
            <Textarea
              {...form.register("notes")}
              placeholder="Контекст знакомства, сильные стороны, договорённости и точки возврата."
            />
          </div>

          <div>
            <label className="field-label">Теги</label>
            <Input {...form.register("tag_names_text")} placeholder="карьера, hr, internship" />
            <p className="field-hint">Список через запятую. Новые теги создадутся автоматически.</p>
          </div>

          {error ? <Alert>{error}</Alert> : null}

          <div className="flex flex-wrap gap-3">
            <Button type="submit" loading={Boolean(submitting || form.formState.isSubmitting)}>
              {submitLabel}
            </Button>
            <Button
              type="button"
              variant="secondary"
              loading={aiMutation.isPending}
              onClick={() => aiMutation.mutate()}
            >
              Получить AI-подсказки
            </Button>
          </div>
        </form>
      </Card>

      <div className="space-y-6">
        <Card className="h-fit">
          <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">AI helper</p>
          <h3 className="mt-3 text-xl font-bold text-white">Соберите карточку быстрее и чище.</h3>
          <p className="mt-2 text-sm text-slate-400">
            Агент даёт рекомендации по категории, тегам и следующему шагу на основе заметок и контекста контакта.
          </p>

          {suggestion ? (
            <div className="mt-6 space-y-4">
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Категория</p>
                <p className="mt-2 text-lg font-semibold text-white">{suggestion.category}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Теги</p>
                <div className="mt-3 flex flex-wrap gap-2">
                  {suggestion.tags.map((tag) => (
                    <Badge key={tag}>{tag}</Badge>
                  ))}
                </div>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Краткий вывод</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{suggestion.note_summary}</p>
              </div>
              <div>
                <p className="text-xs uppercase tracking-[0.24em] text-slate-500">Следующий шаг</p>
                <p className="mt-2 text-sm leading-6 text-slate-300">{suggestion.next_action}</p>
              </div>
              <Button className="w-full" variant="secondary" onClick={applySuggestion}>
                Подставить в форму
              </Button>
            </div>
          ) : (
            <div className="mt-8 rounded-2xl border border-dashed border-borderSoft p-4 text-sm text-slate-400">
              Добавьте заметку и нажмите <span className="font-semibold text-slate-200">«Получить AI-подсказки»</span>.
            </div>
          )}
        </Card>

        <Card className="h-fit">
          <UnstructuredTextParser onApply={applyBusinessCard} />
        </Card>

        <Card className="h-fit">
          <BusinessCardScanner onApply={applyBusinessCard} />
        </Card>
      </div>
    </div>
  );
}
