import { useQuery } from "@tanstack/react-query";
import { CheckCircle2, Cpu, HardDrive, ScanText, Server, XCircle } from "lucide-react";

import { PageHeader } from "../components/PageHeader";
import { getCapabilities } from "../lib/api";

const documentTypeLabels: Record<string, string> = {
  invoice: "Счёт",
  service_act: "Акт выполненных работ",
};

export function SettingsPage() {
  const capabilities = useQuery({
    queryKey: ["system-capabilities"],
    queryFn: getCapabilities,
  });
  const data = capabilities.data;

  return (
    <>
      <PageHeader
        kicker="DF / Окружение"
        title="Конфигурация системы"
        description="Фактические возможности запущенного API, а не локальные настройки браузера."
        actions={
          <button
            className="secondary-button"
            type="button"
            onClick={() => void capabilities.refetch()}
          >
            Обновить состояние
          </button>
        }
      />

      <section className="settings-layout">
        <aside className="settings-aside panel">
          <Server size={22} />
          <span className="section-label">Runtime</span>
          <h2>{data ? `Профиль ${data.environment}` : "Проверка окружения"}</h2>
          <p>
            Рабочие параметры задаются через переменные DOCFLOW_* и применяются сервером при
            запуске.
          </p>
          <div className="settings-state">
            <span className={data ? "settings-dot--ok" : ""} />
            {capabilities.isLoading
              ? "Получаем конфигурацию"
              : data
                ? "API отвечает"
                : "API недоступен"}
          </div>
          {capabilities.error && <p className="run-error">{capabilities.error.message}</p>}
        </aside>

        <article className="settings-panel panel">
          <section className="settings-section">
            <div className="settings-section-heading">
              <span>01</span>
              <div>
                <h2>Распознавание</h2>
                <p>Состояние OCR для сканов и изображений без текстового слоя.</p>
              </div>
            </div>
            <RuntimeRow
              icon={<ScanText size={19} />}
              title="Tesseract OCR"
              description={data?.ocr_command ?? "Исполняемый файл не найден"}
              value={data?.ocr_available ? "Готов" : "Недоступен"}
              ready={data?.ocr_available}
            />
            <RuntimeRow
              icon={<Cpu size={19} />}
              title="Языковые пакеты"
              description={`Запрошено: ${data?.ocr_languages_requested ?? "rus+eng"}`}
              value={data?.ocr_languages_installed.join(", ") || "—"}
              ready={Boolean(data?.ocr_languages_installed.length)}
            />
          </section>

          <section className="settings-section">
            <div className="settings-section-heading">
              <span>02</span>
              <div>
                <h2>Извлечение данных</h2>
                <p>Активный AI-профиль и граница автоматического принятия.</p>
              </div>
            </div>
            <RuntimeRow
              icon={<Cpu size={19} />}
              title="Провайдер"
              description={
                data?.demo_mode
                  ? "Локальное извлечение из OCR-текста без внешнего API"
                  : "Внешний AI-провайдер"
              }
              value={data?.llm_model ?? data?.llm_provider ?? "—"}
              ready={Boolean(data)}
            />
            <RuntimeRow
              icon={<CheckCircle2 size={19} />}
              title="Порог автоприёмки"
              description="Ниже этого значения документ отправляется оператору"
              value={data ? `${Math.round(data.auto_accept_threshold * 100)}%` : "—"}
              ready={Boolean(data)}
            />
          </section>

          <section className="settings-section">
            <div className="settings-section-heading">
              <span>03</span>
              <div>
                <h2>Документы и хранение</h2>
                <p>Поддерживаемые схемы и ограничения входного потока.</p>
              </div>
            </div>
            <RuntimeRow
              icon={<HardDrive size={19} />}
              title="Хранилище"
              description={`Лимит одного файла: ${data?.max_upload_size_mb ?? "—"} МБ`}
              value={data?.storage_backend ?? "—"}
              ready={Boolean(data)}
            />
            <RuntimeRow
              icon={<CheckCircle2 size={19} />}
              title="Типы документов"
              description="Версионированные схемы извлечения и проверки"
              value={
                data?.document_types.map((item) => documentTypeLabels[item] ?? item).join(" · ") ??
                "—"
              }
              ready={Boolean(data?.document_types.length)}
            />
          </section>
        </article>
      </section>
    </>
  );
}

function RuntimeRow({
  icon,
  title,
  description,
  value,
  ready,
}: {
  icon: React.ReactNode;
  title: string;
  description: string;
  value: string;
  ready?: boolean;
}) {
  return (
    <div className="setting-row runtime-row">
      <span className="runtime-icon">{icon}</span>
      <div className="setting-copy">
        <strong>{title}</strong>
        <span>{description}</span>
      </div>
      <div className={ready ? "runtime-value runtime-value--ready" : "runtime-value"}>
        {ready ? <CheckCircle2 size={15} /> : <XCircle size={15} />}
        <span>{value}</span>
      </div>
    </div>
  );
}
