import { FileImage, FileText, Inbox, RefreshCw } from "lucide-react";

import type { DocumentRecord } from "../lib/api";

type DocumentListProps = {
  items: DocumentRecord[];
  total: number;
  loading: boolean;
  error: Error | null;
  onRefresh: () => void;
};

const dateFormatter = new Intl.DateTimeFormat("ru-RU", {
  day: "2-digit",
  month: "short",
  hour: "2-digit",
  minute: "2-digit",
});

function formatBytes(bytes: number) {
  if (bytes < 1024 * 1024) return `${Math.max(1, Math.round(bytes / 1024))} КБ`;
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`;
}

function statusLabel(status: string) {
  if (status === "uploaded") return "Загружен";
  if (status === "duplicate_file") return "Точный дубль";
  return status.replaceAll("_", " ");
}

export function DocumentList({ items, total, loading, error, onRefresh }: DocumentListProps) {
  return (
    <section className="panel documents-card">
      <div className="card-header documents-heading">
        <div>
          <span className="section-label">Реестр</span>
          <h2>
            Последние документы <em>{total}</em>
          </h2>
        </div>
        <button className="icon-button" type="button" aria-label="Обновить" onClick={onRefresh}>
          <RefreshCw size={17} />
        </button>
      </div>

      {loading && (
        <div className="document-state">
          <RefreshCw className="spin" size={22} />
          <span>Получаем документы…</span>
        </div>
      )}

      {error && !loading && (
        <div className="document-state document-state--error">
          <span>Не удалось получить список: {error.message}</span>
        </div>
      )}

      {!loading && !error && items.length === 0 && (
        <div className="document-state document-state--empty">
          <Inbox size={28} />
          <strong>Здесь появятся документы</strong>
          <span>Загрузите первый файл — он сохранится локально.</span>
        </div>
      )}

      {items.length > 0 && (
        <div className="document-list">
          {items.map((document) => {
            const ImageIcon = document.mime_type.startsWith("image/") ? FileImage : FileText;
            return (
              <article className="document-row" key={document.id}>
                <span className="document-icon">
                  <ImageIcon size={19} />
                </span>
                <div className="document-name">
                  <strong>{document.original_filename}</strong>
                  <span>
                    {formatBytes(document.size_bytes)} · {dateFormatter.format(new Date(document.created_at))}
                  </span>
                </div>
                <span className={`status-badge status-badge--${document.status}`}>
                  {statusLabel(document.status)}
                </span>
              </article>
            );
          })}
        </div>
      )}
    </section>
  );
}
