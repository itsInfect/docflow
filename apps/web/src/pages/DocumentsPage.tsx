import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Download, FileSearch, LoaderCircle, Play, ScanText, Search, Upload, X } from "lucide-react";
import { useMemo, useState } from "react";

import { PageHeader } from "../components/PageHeader";
import { UploadPanel } from "../components/UploadPanel";
import { useDocuments } from "../hooks/useDocuments";
import {
  listDocumentRuns,
  downloadRevisionExport,
  startDocumentProcessing,
  type DocumentRecord,
  type ProcessingRunRecord,
} from "../lib/api";
import { formatBytes, formatDate, statusLabel, statusLabels } from "../lib/documents";

const emptyDocuments: DocumentRecord[] = [];

export function DocumentsPage() {
  const documents = useDocuments();
  const items = documents.data?.items ?? emptyDocuments;
  const [query, setQuery] = useState("");
  const [status, setStatus] = useState("all");
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const exportRevisions = useMutation({
    mutationFn: (format: "csv" | "xlsx") => downloadRevisionExport(format),
    onSuccess: (blob, format) => {
      const url = URL.createObjectURL(blob);
      const link = window.document.createElement("a");
      link.href = url;
      link.download = `docflow-approved-revisions.${format}`;
      link.click();
      URL.revokeObjectURL(url);
    },
  });

  const filtered = useMemo(() => {
    const normalizedQuery = query.trim().toLocaleLowerCase("ru-RU");
    return items.filter((item) => {
      const matchesQuery =
        !normalizedQuery || item.original_filename.toLocaleLowerCase("ru-RU").includes(normalizedQuery);
      const matchesStatus = status === "all" || item.status === status;
      return matchesQuery && matchesStatus;
    });
  }, [items, query, status]);

  const selected = items.find((item) => item.id === selectedId) ?? null;

  return (
    <>
      <PageHeader
        kicker="DF / Реестр"
        title="Документы"
        description="Все поступившие файлы, их текущие состояния и технические реквизиты."
        actions={
          <>
            <button className="secondary-button export-button" type="button" disabled={exportRevisions.isPending} onClick={() => exportRevisions.mutate("csv")}>
              <Download size={14} /> CSV
            </button>
            <button className="secondary-button export-button" type="button" disabled={exportRevisions.isPending} onClick={() => exportRevisions.mutate("xlsx")}>
              {exportRevisions.isPending ? <LoaderCircle className="spin" size={14} /> : <Download size={14} />} XLSX
            </button>
            <a className="primary-button" href="#upload"><Upload size={16} />Новый документ</a>
          </>
        }
      />

      {exportRevisions.error && <p className="form-message form-message--error">Не удалось подготовить экспорт: {exportRevisions.error.message}</p>}

      <section className="registry-toolbar panel">
        <label className="search-field">
          <Search size={16} />
          <input
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Поиск по имени файла"
          />
        </label>
        <label className="filter-field">
          <span>Статус</span>
          <select value={status} onChange={(event) => setStatus(event.target.value)}>
            <option value="all">Все статусы</option>
            {Object.entries(statusLabels).map(([value, label]) => (
              <option value={value} key={value}>{label}</option>
            ))}
          </select>
        </label>
        <span className="registry-count">Показано: {filtered.length} из {items.length}</span>
      </section>

      <section className="registry-layout">
        <article className="registry-table-card panel">
          <div className="card-header registry-heading">
            <div><span className="section-label">Основной реестр</span><h2>Список документов</h2></div>
            <button className="icon-button" type="button" onClick={() => void documents.refetch()} aria-label="Обновить список">
              <FileSearch size={17} />
            </button>
          </div>

          {documents.isLoading && <div className="table-state">Загружаем реестр…</div>}
          {documents.error && <div className="table-state table-state--error">Не удалось получить документы: {documents.error.message}</div>}
          {!documents.isLoading && !documents.error && filtered.length === 0 && (
            <div className="table-state">
              <FileSearch size={27} />
              <strong>{items.length ? "Ничего не найдено" : "Реестр пока пуст"}</strong>
              <span>{items.length ? "Измените поисковый запрос или фильтр." : "Загрузите первый документ в панели справа."}</span>
            </div>
          )}

          {filtered.length > 0 && (
            <div className="table-scroll">
              <table className="data-table">
                <thead><tr><th>Документ</th><th>Статус</th><th>Формат</th><th>Размер</th><th>Добавлен</th></tr></thead>
                <tbody>
                  {filtered.map((document) => (
                    <tr className={selectedId === document.id ? "data-row data-row--selected" : "data-row"} key={document.id}>
                      <td>
                        <button className="document-link" type="button" onClick={() => setSelectedId(document.id)}>
                          <strong>{document.original_filename}</strong>
                          <span>{document.id.slice(0, 8)}</span>
                        </button>
                      </td>
                      <td><span className={`status-badge status-badge--${document.status}`}>{statusLabel(document.status)}</span></td>
                      <td>{document.mime_type.split("/").at(-1)?.toUpperCase()}</td>
                      <td>{formatBytes(document.size_bytes)}</td>
                      <td>{formatDate(document.created_at)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>

        <aside className="registry-side">
          {selected ? (
            <DocumentDetails document={selected} onClose={() => setSelectedId(null)} />
          ) : (
            <UploadPanel />
          )}
        </aside>
      </section>
    </>
  );
}

function DocumentDetails({ document, onClose }: { document: DocumentRecord; onClose: () => void }) {
  const queryClient = useQueryClient();
  const runs = useQuery({
    queryKey: ["document-runs", document.id],
    queryFn: () => listDocumentRuns(document.id),
  });
  const processDocument = useMutation({
    mutationFn: () => startDocumentProcessing(document.id),
    onSuccess: async () => {
      await Promise.all([
        queryClient.invalidateQueries({ queryKey: ["documents"] }),
        queryClient.invalidateQueries({ queryKey: ["document-runs", document.id] }),
        queryClient.invalidateQueries({ queryKey: ["audit-events"] }),
      ]);
    },
  });
  const latestRun = runs.data?.items[0];
  const cannotProcess = ["duplicate_file", "rejected"].includes(document.status);

  return (
    <article className="document-details panel">
      <div className="card-header">
        <div><span className="section-label">Карточка документа</span><h2>{document.original_filename}</h2></div>
        <button className="icon-button" type="button" onClick={onClose} aria-label="Закрыть карточку"><X size={16} /></button>
      </div>
      <dl className="details-list">
        <div><dt>Статус</dt><dd><span className={`status-badge status-badge--${document.status}`}>{statusLabel(document.status)}</span></dd></div>
        <div><dt>Тип файла</dt><dd>{document.mime_type}</dd></div>
        <div><dt>Размер</dt><dd>{formatBytes(document.size_bytes)}</dd></div>
        <div><dt>Страниц</dt><dd>{document.page_count ?? "Ещё не определено"}</dd></div>
        <div><dt>Дата загрузки</dt><dd>{formatDate(document.created_at)}</dd></div>
        <div><dt>Тип документа</dt><dd>{document.doc_type ?? "Ещё не определён"}</dd></div>
        <div><dt>Confidence</dt><dd>{document.confidence === null ? "—" : document.confidence.toFixed(2)}</dd></div>
        <div><dt>ID</dt><dd className="technical-value">{document.id}</dd></div>
      </dl>
      {document.is_duplicate_of && (
        <div className="detail-notice">Точный дубль документа <span>{document.is_duplicate_of.slice(0, 8)}</span></div>
      )}
      {!cannotProcess && (
        <button
          className="process-button"
          type="button"
          disabled={processDocument.isPending}
          onClick={() => processDocument.mutate()}
        >
          {processDocument.isPending ? <LoaderCircle className="spin" size={16} /> : <Play size={15} />}
          {latestRun ? "Запустить новую версию" : "Начать обработку"}
        </button>
      )}
      {processDocument.error && <p className="run-error">{processDocument.error.message}</p>}
      {runs.isLoading && <div className="run-loading">Загружаем историю запусков…</div>}
      {latestRun && <RunSummary run={latestRun} total={runs.data?.total ?? 1} />}
    </article>
  );
}

function RunSummary({ run, total }: { run: ProcessingRunRecord; total: number }) {
  const labels: Record<string, string> = {
    running: "Выполняется",
    succeeded: "Предобработка завершена",
    awaiting_ocr: "Ожидает OCR",
    failed: "Ошибка обработки",
  };

  return (
    <section className={`run-summary run-summary--${run.status}`}>
      <div className="run-summary-heading">
        <span><ScanText size={15} /> Последний запуск</span>
        <strong>v{run.run_number} / {total}</strong>
      </div>
      <p>{labels[run.status] ?? run.status}</p>
      <dl>
        <div><dt>Страниц</dt><dd>{run.page_count ?? "—"}</dd></div>
        <div><dt>Текстовый слой</dt><dd>{run.text_layer_pages}</dd></div>
        <div><dt>Символов</dt><dd>{run.text_char_count.toLocaleString("ru-RU")}</dd></div>
        <div><dt>OCR</dt><dd>{run.ocr_pending_pages ? `ожидают ${run.ocr_pending_pages}` : `готово ${run.ocr_pages}`}</dd></div>
      </dl>
      {run.status === "awaiting_ocr" && <small>Для сканов понадобится локальный Tesseract OCR.</small>}
      {run.error_message && <small>{run.error_message}</small>}
    </section>
  );
}
