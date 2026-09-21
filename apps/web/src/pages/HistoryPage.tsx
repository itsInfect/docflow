import { FileClock, Search } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { useAuditEvents } from "../hooks/useAuditEvents";
import type { AuditEventRecord } from "../lib/api";
import { formatDate, statusLabel, statusLabels } from "../lib/documents";

const emptyEvents: AuditEventRecord[] = [];

const actorLabels: Record<string, string> = {
  system: "Система",
  operator: "Оператор",
};

export function HistoryPage() {
  const events = useAuditEvents();
  const items = events.data?.items ?? emptyEvents;
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("ru-RU");
    return items.filter((item) => {
      const haystack = `${item.original_filename} ${item.reason ?? ""}`.toLocaleLowerCase(
        "ru-RU",
      );
      const matchesQuery = !normalizedQuery || haystack.includes(normalizedQuery);
      return matchesQuery && (status === "all" || item.to_status === status);
    });
  }, [items, query, status]);

  return (
    <>
      <PageHeader
        kicker="DF / Аудит"
        title="История операций"
        description="Полная хронология этапов обработки, автоматических решений и действий оператора."
      />

      <section className="registry-toolbar panel history-toolbar">
        <label className="search-field">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Документ или причина события"
          />
        </label>
        <label className="filter-field">
          <span>Новый статус</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">Все статусы</option>
            {Object.entries(statusLabels).map(([value, label]) => (
              <option value={value} key={value}>
                {label}
              </option>
            ))}
          </select>
        </label>
      </section>

      <section className="history-layout">
        <article className="history-list panel">
          <div className="card-header">
            <div>
              <span className="section-label">События</span>
              <h2>Лента обработки</h2>
            </div>
            <span className="panel-counter">{filtered.length.toString().padStart(2, "0")}</span>
          </div>

          {events.isLoading && <div className="table-state">Загружаем историю…</div>}
          {events.error && (
            <div className="table-state table-state--error">
              Не удалось получить историю: {events.error.message}
            </div>
          )}
          {!events.isLoading && !events.error && filtered.length === 0 && (
            <div className="table-state">
              <FileClock size={29} />
              <strong>{items.length ? "События не найдены" : "История пока пуста"}</strong>
              <span>
                {items.length
                  ? "Измените фильтры поиска."
                  : "Первая запись появится после загрузки документа."}
              </span>
            </div>
          )}

          <div className="timeline">
            {filtered.map((event, index) => (
              <article className="history-entry" key={event.id}>
                <div className="history-axis">
                  <span className="history-marker">{String(index + 1).padStart(2, "0")}</span>
                </div>
                <div className="history-content">
                  <div className="history-title-row">
                    <strong>{event.original_filename}</strong>
                    <span className={`status-badge status-badge--${event.to_status}`}>
                      {statusLabel(event.to_status)}
                    </span>
                  </div>
                  <p>{event.reason ?? "Статус документа изменён."}</p>
                  <div className="history-meta">
                    <span>{formatDate(event.created_at)}</span>
                    <span>
                      {event.from_status
                        ? `${statusLabel(event.from_status)} → ${statusLabel(event.to_status)}`
                        : `Создан → ${statusLabel(event.to_status)}`}
                    </span>
                    <span className={`history-actor history-actor--${event.actor_type}`}>
                      {actorLabels[event.actor_type] ?? event.actor_type}
                    </span>
                    <span>ID {event.document_id.slice(0, 8)}</span>
                  </div>
                </div>
              </article>
            ))}
          </div>
        </article>

        <aside className="history-note panel">
          <span className="section-label">Аудит</span>
          <h2>Воспроизводимая цепочка решений</h2>
          <p>
            Каждый переход хранится отдельно: можно увидеть, когда и почему изменился статус и кем
            было принято решение.
          </p>
          <dl className="audit-list">
            <div>
              <dt>Событий</dt>
              <dd>{events.data?.total ?? 0}</dd>
            </div>
            <div>
              <dt>Автоматика</dt>
              <dd>Этапы пайплайна и проверки</dd>
            </div>
            <div>
              <dt>Оператор</dt>
              <dd>Исправления, одобрение и дубли</dd>
            </div>
          </dl>
        </aside>
      </section>
    </>
  );
}
