import { useQuery } from "@tanstack/react-query";
import {
  BarChart3,
  Bell,
  CheckCircle2,
  ClipboardCheck,
  Files,
  FileSearch,
  History,
  LayoutDashboard,
  Settings,
  Upload,
} from "lucide-react";

import { DocumentList } from "./components/DocumentList";
import { SystemStatus } from "./components/SystemStatus";
import { UploadPanel } from "./components/UploadPanel";
import { listDocuments } from "./lib/api";

const navigation = [
  { label: "Обзор", icon: LayoutDashboard, active: true },
  { label: "Документы", icon: Files },
  { label: "Проверка", icon: ClipboardCheck, badge: "0" },
  { label: "История", icon: History },
  { label: "Качество", icon: BarChart3 },
];

const monthLabel = new Intl.DateTimeFormat("ru-RU", {
  month: "long",
  year: "numeric",
}).format(new Date());

export function App() {
  const documents = useQuery({
    queryKey: ["documents"],
    queryFn: listDocuments,
  });
  const items = documents.data?.items ?? [];
  const uploaded = items.filter((item) => item.status === "uploaded").length;
  const duplicates = items.filter((item) => item.status === "duplicate_file").length;
  const needsReview = items.filter((item) => item.status === "needs_review").length;

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand-block">
          <span className="brand-mark">D</span>
          <div>
            <strong>Docflow</strong>
            <span>Document operations</span>
          </div>
        </div>

        <div className="workspace-switcher">
          <span className="workspace-avatar">DW</span>
          <div>
            <strong>Demo workspace</strong>
            <span>Локальный контур</span>
          </div>
        </div>

        <nav className="side-nav" aria-label="Основная навигация">
          <span className="nav-label">Рабочее пространство</span>
          {navigation.map(({ label, icon: Icon, active, badge }) => (
            <button
              className={`nav-item${active ? " nav-item--active" : ""}`}
              type="button"
              key={label}
            >
              <Icon size={18} strokeWidth={1.8} />
              <span>{label}</span>
              {badge && <em>{badge}</em>}
            </button>
          ))}
        </nav>

        <div className="sidebar-footer">
          <SystemStatus />
          <button className="nav-item" type="button">
            <Settings size={18} strokeWidth={1.8} />
            <span>Настройки</span>
          </button>
        </div>
      </aside>

      <main className="dashboard">
        <header className="mobile-header">
          <div className="brand-block">
            <span className="brand-mark">D</span>
            <strong>Docflow</strong>
          </div>
          <SystemStatus />
        </header>

        <nav className="mobile-nav" aria-label="Мобильная навигация">
          {navigation.slice(0, 4).map(({ label, icon: Icon, active }) => (
            <button
              className={active ? "mobile-nav-item mobile-nav-item--active" : "mobile-nav-item"}
              type="button"
              key={label}
            >
              <Icon size={17} />
              <span>{label}</span>
            </button>
          ))}
        </nav>

        <header className="topbar">
          <div>
            <span className="page-kicker">Рабочая панель</span>
            <h1>Обзор документов</h1>
            <p>Контроль входящих документов и состояния обработки.</p>
          </div>
          <div className="topbar-actions">
            <span className="period-label">{monthLabel}</span>
            <button className="notification-button" type="button" aria-label="Уведомления">
              <Bell size={18} />
            </button>
            <a className="primary-button" href="#upload">
              <Upload size={17} />
              Загрузить
            </a>
          </div>
        </header>

        <section className="metrics" aria-label="Сводные показатели">
          <article className="metric-card">
            <span className="metric-icon metric-icon--blue">
              <Files size={19} />
            </span>
            <div>
              <span>Всего документов</span>
              <strong>{documents.data?.total ?? 0}</strong>
            </div>
            <small>Локальная база</small>
          </article>
          <article className="metric-card">
            <span className="metric-icon metric-icon--cyan">
              <FileSearch size={19} />
            </span>
            <div>
              <span>Ожидают обработки</span>
              <strong>{uploaded}</strong>
            </div>
            <small>Следующий этап</small>
          </article>
          <article className="metric-card">
            <span className="metric-icon metric-icon--amber">
              <ClipboardCheck size={19} />
            </span>
            <div>
              <span>Требуют проверки</span>
              <strong>{needsReview}</strong>
            </div>
            <small>Очередь оператора</small>
          </article>
          <article className="metric-card">
            <span className="metric-icon metric-icon--violet">
              <Files size={19} />
            </span>
            <div>
              <span>Точные дубли</span>
              <strong>{duplicates}</strong>
            </div>
            <small>По SHA-256</small>
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
              <div>
                <span className="section-label">Конвейер</span>
                <h2>Этапы обработки</h2>
              </div>
              <span className="development-badge">В разработке</span>
            </div>
            <div className="process-steps">
              <div className="process-step process-step--done">
                <span>
                  <CheckCircle2 size={16} />
                </span>
                <div>
                  <strong>Приём файла</strong>
                  <small>Проверка сигнатуры и SHA-256</small>
                </div>
              </div>
              <div className="process-connector process-connector--active" />
              <div className="process-step process-step--current">
                <span>2</span>
                <div>
                  <strong>Предобработка</strong>
                  <small>Текстовый слой, страницы и превью</small>
                </div>
              </div>
              <div className="process-connector" />
              <div className="process-step">
                <span>3</span>
                <div>
                  <strong>Извлечение</strong>
                  <small>Схема документа и AI-провайдер</small>
                </div>
              </div>
              <div className="process-connector" />
              <div className="process-step">
                <span>4</span>
                <div>
                  <strong>Проверка</strong>
                  <small>Правила и решение оператора</small>
                </div>
              </div>
            </div>
          </article>

          <article className="readiness-card">
            <span className="readiness-icon">
              <CheckCircle2 size={20} />
            </span>
            <div>
              <span className="section-label">Текущий контур</span>
              <h2>Готов к локальной работе</h2>
              <p>
                SQLite и файловое хранилище запускаются без внешних сервисов. Docker подключит
                инфраструктурный профиль.
              </p>
            </div>
          </article>
        </section>
      </main>
    </div>
  );
}
