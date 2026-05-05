export const importanceLabels = {
  low: "Низкая",
  medium: "Средняя",
  high: "Высокая",
  strategic: "Стратегическая",
} as const;

export const interactionTypeLabels = {
  meeting: "Встреча",
  message: "Сообщение",
  call: "Звонок",
  project: "Совместный проект",
  other: "Другое",
} as const;

export const reminderTypeLabels = {
  follow_up: "Связаться повторно",
  congratulation: "Поздравление",
  reconnect: "Возобновить общение",
  custom: "Своя задача",
} as const;

export const reminderStatusLabels = {
  active: "Активные",
  overdue: "Просроченные",
  completed: "Выполненные",
} as const;

export const integrationStatusLabels = {
  connected: "Подключено",
  not_connected: "Не подключено",
  coming_soon: "Скоро",
} as const;

export function getImportanceLabel(value?: string | null) {
  if (!value) {
    return "Не указано";
  }
  return importanceLabels[value as keyof typeof importanceLabels] ?? value;
}

export function getInteractionTypeLabel(value?: string | null) {
  if (!value) {
    return "Другое";
  }
  return interactionTypeLabels[value as keyof typeof interactionTypeLabels] ?? value;
}

export function getReminderTypeLabel(value?: string | null) {
  if (!value) {
    return "Своя задача";
  }
  return reminderTypeLabels[value as keyof typeof reminderTypeLabels] ?? value;
}

export function getReminderStatusLabel(value?: string | null) {
  if (!value) {
    return "Активные";
  }
  return reminderStatusLabels[value as keyof typeof reminderStatusLabels] ?? value;
}

export function getIntegrationStatusLabel(value?: string | null) {
  if (!value) {
    return "Неизвестно";
  }
  return integrationStatusLabels[value as keyof typeof integrationStatusLabels] ?? value;
}
