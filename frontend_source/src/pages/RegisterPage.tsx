import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { register } from "@/api/auth";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";

const schema = z.object({
  full_name: z
    .string({ required_error: "Введите имя и фамилию" })
    .min(2, "Введите имя и фамилию"),
  email: z
    .string({ required_error: "Введите почту" })
    .min(1, "Введите почту")
    .email("Введите корректную почту"),
  password: z
    .string({ required_error: "Введите пароль" })
    .min(8, "Пароль должен быть не короче 8 символов"),
});

type FormValues = z.infer<typeof schema>;

export function RegisterPage() {
  const navigate = useNavigate();
  const { setSession, user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
  });

  useEffect(() => {
    if (user) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate, user]);

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const response = await register(values);
      setSession(response.user);
      navigate("/dashboard", { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось зарегистрироваться");
    }
  });

  return (
    <div className="page-shell flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-xl">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Новый аккаунт</p>
        <h1 className="mt-3 text-3xl font-bold text-white">Создайте систему для своих деловых контактов</h1>
        <p className="mt-2 text-sm text-slate-400">После регистрации сразу будут доступны базовые категории, теги и интеграции.</p>

        <form className="mt-8 space-y-5" onSubmit={onSubmit}>
          <div>
            <label className="field-label">Имя и фамилия</label>
            <Input {...form.register("full_name")} placeholder="Алексей Смирнов" />
            {form.formState.errors.full_name ? (
              <p className="field-hint text-rose-300">{form.formState.errors.full_name.message}</p>
            ) : null}
          </div>
          <div>
            <label className="field-label">Почта</label>
            <Input {...form.register("email")} placeholder="you@example.com" />
            {form.formState.errors.email ? <p className="field-hint text-rose-300">{form.formState.errors.email.message}</p> : null}
          </div>
          <div>
            <label className="field-label">Пароль</label>
            <Input {...form.register("password")} type="password" placeholder="Минимум 8 символов" />
            {form.formState.errors.password ? (
              <p className="field-hint text-rose-300">{form.formState.errors.password.message}</p>
            ) : null}
          </div>

          {error ? <Alert>{error}</Alert> : null}

          <Button className="w-full" type="submit" loading={form.formState.isSubmitting}>
            Создать аккаунт
          </Button>
        </form>

        <div className="mt-6 flex items-center justify-between text-sm text-slate-400">
          <Link to="/" className="hover:text-white">
            На главную
          </Link>
          <Link to="/login" className="hover:text-white">
            У меня уже есть аккаунт
          </Link>
        </div>
      </Card>
    </div>
  );
}
