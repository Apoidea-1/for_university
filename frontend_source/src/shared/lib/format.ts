import { format, formatDistanceToNowStrict } from "date-fns";
import { ru } from "date-fns/locale";

export function formatDateTime(value?: string | null) {
  if (!value) {
    return "Дата не указана";
  }
  return format(new Date(value), "dd MMM yyyy, HH:mm", { locale: ru });
}

export function formatDate(value?: string | null) {
  if (!value) {
    return "Дата не указана";
  }
  return format(new Date(value), "dd MMM yyyy", { locale: ru });
}

export function relativeFromNow(value?: string | null) {
  if (!value) {
    return "Никогда";
  }
  return formatDistanceToNowStrict(new Date(value), { addSuffix: true, locale: ru });
}
