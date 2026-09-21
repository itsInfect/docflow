import {
  BarChart3,
  ClipboardCheck,
  Files,
  History,
  LayoutGrid,
  Settings,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { SystemStatus } from "../components/SystemStatus";

const navigation = [
  { label: "Обзор", icon: LayoutGrid, to: "/", end: true },
  { label: "Документы", icon: Files, to: "/documents" },
  { label: "Проверка", icon: ClipboardCheck, to: "/review" },
  { label: "История", icon: History, to: "/history" },
  { label: "Качество", icon: BarChart3, to: "/quality" },
];

function navClass({ isActive }: { isActive: boolean }) {
  return `rail-item${isActive ? " rail-item--active" : ""}`;
}

function mobileNavClass({ isActive }: { isActive: boolean }) {
  return `mobile-nav-item${isActive ? " mobile-nav-item--active" : ""}`;
}

export function AppShell() {
  return (
    <div className="app-shell">
      <aside className="navigation-rail">
        <NavLink className="brand-mark" to="/" aria-label="Docflow">
          D
        </NavLink>
        <nav className="rail-nav" aria-label="Основная навигация">
          {navigation.map(({ label, icon: Icon, to, end }) => (
            <NavLink
              className={navClass}
              to={to}
              end={end}
              aria-label={label}
              title={label}
              key={label}
            >
              <Icon size={19} strokeWidth={1.7} />
              <span>{label}</span>
            </NavLink>
          ))}
        </nav>
        <NavLink
          className={({ isActive }) => `${navClass({ isActive })} rail-settings`}
          to="/settings"
          aria-label="Настройки"
          title="Настройки"
        >
          <Settings size={19} strokeWidth={1.7} />
          <span>Настройки</span>
        </NavLink>
      </aside>

      <main className="dashboard">
        <header className="mobile-header">
          <NavLink className="mobile-brand" to="/">
            <span className="brand-mark">D</span>
            <div>
              <strong>Docflow</strong>
              <small>Operations desk</small>
            </div>
          </NavLink>
          <SystemStatus />
        </header>

        <nav className="mobile-nav" aria-label="Мобильная навигация">
          {navigation.map(({ label, icon: Icon, to, end }) => (
            <NavLink className={mobileNavClass} to={to} end={end} key={label}>
              <Icon size={16} />
              <span>{label}</span>
            </NavLink>
          ))}
          <NavLink className={mobileNavClass} to="/settings">
            <Settings size={16} />
            <span>Настройки</span>
          </NavLink>
        </nav>

        <Outlet />
      </main>
    </div>
  );
}
