export const statusLabels: Record<string, string> = {
  uploaded: "Загружен",
  preprocessing: "Предобработка",
  classifying: "Классификация",
  extracting: "Извлечение",
  validating: "Проверка правил",
  needs_review: "Ручная проверка",
  approved: "Утверждён",
  rejected: "Отклонён",
  failed: "Ошибка",
  duplicate_file: "Точный дубль",
};

export function statusLabel(status: string) {
  return statusLabels[status] ?? status.replaceAll("_", " ");
}

export function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

export function formatDate(value: string, includeTime = true) {
  return new Intl.DateTimeFormat("ru-RU", {
    day: "2-digit",
    month: "short",
    year: "numeric",
    ...(includeTime ? { hour: "2-digit", minute: "2-digit" } : {}),
  }).format(new Date(value));
}
