import { useEffect, useState } from "react";
import { Link, useNavigate } from "react-router-dom";
import { useForm } from "react-hook-form";
import { z } from "zod";
import { zodResolver } from "@hookform/resolvers/zod";

import { login } from "@/api/auth";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";
import { Input } from "@/components/ui/Input";
import { useAuth } from "@/hooks/useAuth";

const schema = z.object({
  email: z
    .string({ required_error: "Введите почту" })
    .min(1, "Введите почту")
    .email("Введите корректную почту"),
  password: z
    .string({ required_error: "Введите пароль" })
    .min(8, "Пароль должен быть не короче 8 символов"),
});

type FormValues = z.infer<typeof schema>;

export function LoginPage() {
  const navigate = useNavigate();
  const { setSession, user } = useAuth();
  const [error, setError] = useState<string | null>(null);
  const form = useForm<FormValues>({
    resolver: zodResolver(schema),
    defaultValues: {
      email: "demo@demo.com",
      password: "demopass",
    },
  });

  useEffect(() => {
    if (user) {
      navigate("/dashboard", { replace: true });
    }
  }, [navigate, user]);

  const onSubmit = form.handleSubmit(async (values) => {
    setError(null);
    try {
      const response = await login(values);
      setSession(response.user);
      navigate("/dashboard", { replace: true });
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "Не удалось войти");
    }
  });

  return (
    <div className="page-shell flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-lg">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">С возвращением</p>
        <h1 className="mt-3 text-3xl font-bold text-white">Войдите в рабочее пространство</h1>
        <p className="mt-2 text-sm text-slate-400">Используйте демо-доступ или создайте свой аккаунт.</p>

        <form className="mt-8 space-y-5" onSubmit={onSubmit}>
          <div>
            <label className="field-label">Почта</label>
            <Input {...form.register("email")} placeholder="you@example.com" />
            {form.formState.errors.email ? <p className="field-hint text-rose-300">{form.formState.errors.email.message}</p> : null}
          </div>
          <div>
            <label className="field-label">Пароль</label>
            <Input {...form.register("password")} type="password" placeholder="Введите пароль" />
            {form.formState.errors.password ? (
              <p className="field-hint text-rose-300">{form.formState.errors.password.message}</p>
            ) : null}
          </div>

          {error ? <Alert>{error}</Alert> : null}

          <Button className="w-full" type="submit" loading={form.formState.isSubmitting}>
            Войти
          </Button>
        </form>

        <div className="mt-6 flex items-center justify-between text-sm text-slate-400">
          <Link to="/" className="hover:text-white">
            На главную
          </Link>
          <Link to="/register" className="hover:text-white">
            Создать аккаунт
          </Link>
        </div>
      </Card>
    </div>
  );
}
