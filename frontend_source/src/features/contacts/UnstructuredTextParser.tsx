import { useState } from "react";

import { parseUnstructuredContact } from "@/api/ai";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import { Textarea } from "@/components/ui/Textarea";
import type { BusinessCardScanResult } from "@/types/api";

export function UnstructuredTextParser({
  onApply,
}: {
  onApply: (result: BusinessCardScanResult) => void;
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [text, setText] = useState("");

  async function handleParse() {
    if (!text.trim()) {
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const scanResult = await parseUnstructuredContact({ text });
      onApply(scanResult);
      setText(""); // Clear on success
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Не удалось распознать текст.");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Текст</p>
        <h3 className="mt-2 text-xl font-bold text-white">Создать с помощью ИИ</h3>
        <p className="mt-2 text-sm text-slate-400">
          Вставьте любой неструктурированный текст (подпись из письма, сообщение). Агент сам распределит данные по полям.
        </p>
      </div>

      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder="Например: Иван Иванов, работает в Яндекс директором, телефон 89991234567"
        className="min-h-[100px]"
      />

      {isLoading ? <Alert variant="info">Анализирую текст…</Alert> : null}
      {error ? <Alert>{error}</Alert> : null}

      <Button
        className="w-full"
        variant="secondary"
        onClick={handleParse}
        disabled={!text.trim()}
        loading={isLoading}
      >
        Разобрать текст
      </Button>
    </div>
  );
}
