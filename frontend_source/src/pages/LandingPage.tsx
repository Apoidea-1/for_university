import { Link, useNavigate } from "react-router-dom";

import { useAuth } from "@/hooks/useAuth";
import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

const features = [
  "Добавляйте новые знакомства за несколько секунд после встреч и мероприятий.",
  "Храните историю общения, напоминания и важные договоренности в одном месте.",
  "Получайте подсказки ИИ по категориям, тегам, заметкам и следующему шагу.",
];

export function LandingPage() {
  const navigate = useNavigate();
  const { user, logout } = useAuth();

  const handleDemoClick = async () => {
    try {
      await fetch("/web/session/destroy", { method: "POST" });
    } catch (e) {
      console.error(e);
    }
    localStorage.removeItem("session_id");
    localStorage.removeItem("user_id");

    navigate("/register", {
      state: {
        demo: true,
        email: "demo@demo.com",
        password: "demopass",
      },
    });
  };

  return (
    <div className="page-shell flex min-h-screen flex-col justify-center">
      <div className="grid items-center gap-8 lg:grid-cols-[1.1fr_0.9fr]">
        <section className="space-y-8">
          <div className="inline-flex rounded-full border border-white/10 bg-white/5 px-4 py-2 text-sm font-semibold text-sand">
            Учебный сервис для личного нетворкинга
          </div>
          <div className="space-y-5">
            <h1 className="max-w-3xl text-5xl font-extrabold tracking-tight text-white sm:text-6xl">
              Превратите случайные знакомства в понятную систему.
            </h1>
            <p className="max-w-2xl text-lg leading-8 text-slate-300">
              NetWorkPilot помогает студентам и молодым специалистам не терять полезные контакты, вовремя
              возвращаться к общению и развивать профессиональные связи осознанно.
            </p>
          </div>
          <div className="flex flex-wrap gap-4">
            <Button className="px-6 py-3 text-base" onClick={handleDemoClick}>
              Попробовать демо
            </Button>
            <Link to="/login">
              <Button variant="secondary" className="px-6 py-3 text-base">
                Войти
              </Button>
            </Link>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            {features.map((feature) => (
              <Card key={feature} className="min-h-[160px]">
                <p className="text-sm leading-6 text-slate-300">{feature}</p>
              </Card>
            ))}
          </div>
        </section>

        <Card className="overflow-hidden p-0">
          <div className="bg-mesh p-6">
            <p className="text-xs uppercase tracking-[0.24em] text-accent">Внутри платформы</p>
            <h2 className="mt-3 text-3xl font-bold text-white">Одна система для всех ваших деловых контактов.</h2>
          </div>
          <div className="grid gap-3 p-6">
            <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
              <p className="text-sm text-slate-400">Контакты</p>
              <p className="mt-1 text-3xl font-bold text-white">128</p>
              <p className="mt-2 text-sm text-slate-500">Разложены по категориям, важности и контексту знакомства.</p>
            </div>
            <div className="grid gap-3 sm:grid-cols-2">
              <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                <p className="text-sm text-slate-400">Напоминания на подходе</p>
                <p className="mt-1 text-2xl font-bold text-white">7</p>
              </div>
              <div className="rounded-2xl border border-white/10 bg-panelSoft p-4">
                <p className="text-sm text-slate-400">Новые за месяц</p>
                <p className="mt-1 text-2xl font-bold text-white">24</p>
              </div>
            </div>
            <div className="rounded-2xl border border-accent/20 bg-accent/10 p-4 text-sm text-slate-200">
              ИИ подсказывает категорию, теги, краткий вывод и следующий шаг по заметкам после встречи.
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
