import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import { Card } from "@/components/ui/Card";

export function NotFoundPage() {
  return (
    <div className="page-shell flex min-h-screen items-center justify-center">
      <Card className="w-full max-w-xl text-center">
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">404</p>
        <h1 className="mt-3 text-4xl font-bold text-white">Страница не найдена.</h1>
        <p className="mt-3 text-slate-400">Такого адреса нет или страница была перемещена.</p>
        <div className="mt-8 flex justify-center">
          <Link to="/">
            <Button>На главную</Button>
          </Link>
        </div>
      </Card>
    </div>
  );
}
