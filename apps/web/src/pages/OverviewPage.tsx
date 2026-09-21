import { CheckCircle2, ClipboardCheck, Files, FileSearch, Upload } from "lucide-react";
import { Link } from "react-router-dom";

import { DocumentList } from "../components/DocumentList";
import { PageHeader } from "../components/PageHeader";
import { SystemStatus } from "../components/SystemStatus";
import { UploadPanel } from "../components/UploadPanel";
import { useDocuments } from "../hooks/useDocuments";

const monthLabel = new Intl.DateTimeFormat("ru-RU", {
  month: "long",
  year: "numeric",
}).format(new Date());

export function OverviewPage() {
  const documents = useDocuments();
  const items = documents.data?.items ?? [];
  const uploaded = items.filter((item) => item.status === "uploaded").length;
  const duplicates = items.filter((item) => item.status === "duplicate_file").length;
  const needsReview = items.filter((item) => item.status === "needs_review").length;

  return (
    <>
      <PageHeader
        kicker="DF / Операционный реестр"
        title="Входящие документы"
        description="Приём, контроль и подготовка бухгалтерских документов к обработке."
        actions={
          <>
            <SystemStatus />
            <span className="period-label">{monthLabel}</span>
            <Link className="primary-button" to="/documents#upload">
              <Upload size={16} />
              Принять файл
            </Link>
          </>
        }
      />

      <section className="status-strip" aria-label="Сводные показатели">
        <article className="status-cell">
          <span className="status-index">01</span>
          <div><small>Всего в реестре</small><strong>{documents.data?.total ?? 0}</strong></div>
          <Files size={17} />
        </article>
        <article className="status-cell">
          <span className="status-index">02</span>
          <div><small>Ждут обработки</small><strong>{uploaded}</strong></div>
          <FileSearch size={17} />
        </article>
        <article className="status-cell">
          <span className="status-index">03</span>
          <div><small>Ручная проверка</small><strong>{needsReview}</strong></div>
          <ClipboardCheck size={17} />
        </article>
        <article className="status-cell status-cell--signal">
          <span className="status-index">04</span>
          <div><small>Точные дубли</small><strong>{duplicates}</strong></div>
          <Files size={17} />
        </article>
      </section>

      <section className="workspace-grid" aria-label="Работа с документами">
        <UploadPanel />
        <DocumentList
          items={items}
          total={documents.data?.total ?? 0}
          loading={documents.isLoading}
          error={documents.error}
          onRefresh={() => void documents.refetch()}
        />
      </section>

      <section className="operations-grid">
        <article className="process-card">
          <div className="card-header">
            <div><span className="section-label">Маршрут документа</span><h2>Контрольные точки</h2></div>
            <span className="development-badge development-badge--ready">Рабочий контур</span>
          </div>
          <div className="process-steps">
            <div className="process-step process-step--done">
              <span><CheckCircle2 size={15} /></span>
              <div><strong>Приём</strong><small>Сигнатура и SHA-256</small></div>
            </div>
            <div className="process-connector process-connector--active" />
            <div className="process-step process-step--done">
              <span><CheckCircle2 size={15} /></span><div><strong>Предобработка</strong><small>Страницы, текст и превью</small></div>
            </div>
            <div className="process-connector" />
            <div className="process-step process-step--done">
              <span><CheckCircle2 size={15} /></span><div><strong>Извлечение</strong><small>Схема и AI-провайдер</small></div>
            </div>
            <div className="process-connector" />
            <div className="process-step process-step--done">
              <span><CheckCircle2 size={15} /></span><div><strong>Контроль</strong><small>Правила и оператор</small></div>
            </div>
          </div>
        </article>

        <article className="readiness-card">
          <span className="readiness-monogram">LOCAL</span>
          <div>
            <span className="section-label">Среда исполнения</span>
            <h2>Автономный контур</h2>
            <p>SQLite и локальное хранилище работают без внешних сервисов. Docker подключит инфраструктурный профиль.</p>
          </div>
        </article>
      </section>
    </>
  );
}
