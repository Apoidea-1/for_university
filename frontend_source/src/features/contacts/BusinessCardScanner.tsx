import { useState, type ChangeEvent } from "react";

import { scanBusinessCard } from "@/api/ai";
import { Alert } from "@/components/ui/Alert";
import { Button } from "@/components/ui/Button";
import type { BusinessCardScanResult } from "@/types/api";

async function readFileAsDataUrl(file: File) {
  return new Promise<string>((resolve, reject) => {
    const reader = new FileReader();
    reader.onload = () => resolve(String(reader.result ?? ""));
    reader.onerror = () => reject(new Error("Не удалось прочитать файл."));
    reader.readAsDataURL(file);
  });
}

export function BusinessCardScanner({
  onApply,
}: {
  onApply: (result: BusinessCardScanResult) => void;
}) {
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<BusinessCardScanResult | null>(null);

  async function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0];
    if (!file) {
      return;
    }
    setError(null);
    setIsLoading(true);
    try {
      const imageBase64 = await readFileAsDataUrl(file);
      const scanResult = await scanBusinessCard({ image_base64: imageBase64 });
      setResult(scanResult);
    } catch (scanError) {
      setError(scanError instanceof Error ? scanError.message : "Не удалось распознать визитку.");
    } finally {
      setIsLoading(false);
      event.target.value = "";
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <p className="text-sm font-semibold uppercase tracking-[0.24em] text-accent">Визитка</p>
        <h3 className="mt-2 text-xl font-bold text-white">Распознавание по фото</h3>
        <p className="mt-2 text-sm text-slate-400">
          Загрузите фото визитки, агент вытащит имя, компанию, роль и каналы связи в структурированный вид.
        </p>
      </div>

      <label className="block rounded-2xl border border-dashed border-borderSoft bg-white/5 px-4 py-5 text-sm text-slate-300 transition hover:border-accent">
        <span className="block font-medium">Выбрать изображение</span>
        <span className="mt-1 block text-xs text-slate-500">PNG, JPG, WEBP. OCR включится только при настроенном AI-provider.</span>
        <input className="hidden" type="file" accept="image/*" onChange={handleFileChange} />
      </label>

      {isLoading ? <Alert variant="info">Сканирую визитку…</Alert> : null}
      {error ? <Alert>{error}</Alert> : null}

      {result ? (
        <div className="space-y-4 rounded-2xl border border-white/10 bg-white/5 p-4">
          <div className="grid gap-3 sm:grid-cols-2">
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Имя</p>
              <p className="mt-1 text-sm text-white">{result.full_name || "Не найдено"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Компания</p>
              <p className="mt-1 text-sm text-white">{result.company || "Не найдено"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Роль</p>
              <p className="mt-1 text-sm text-white">{result.role || "Не найдено"}</p>
            </div>
            <div>
              <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Email / Phone</p>
              <p className="mt-1 text-sm text-white">{result.email || result.phone || "Не найдено"}</p>
            </div>
          </div>

          {result.notes ? <p className="text-sm text-slate-300">{result.notes}</p> : null}

          <Button className="w-full" variant="secondary" onClick={() => onApply(result)}>
            Подставить в форму
          </Button>
        </div>
      ) : null}
    </div>
  );
}
