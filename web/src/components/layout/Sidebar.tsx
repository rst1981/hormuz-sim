import { useLocation, useNavigate } from 'react-router-dom';

const NAV_ITEMS = [
  { path: '/', label: 'Dashboard', icon: '◆' },
  { path: '/parameters', label: 'Parameters', icon: '⚙' },
  { path: '/montecarlo', label: 'Monte Carlo', icon: '⊞' },
  { path: '/escalation', label: 'Escalation', icon: '▲' },
  { path: '/oil', label: 'Oil Market', icon: '◉' },
  { path: '/agents', label: 'Agents', icon: '◎' },
  { path: '/trump', label: 'Trump Tracker', icon: '★' },
  { path: '/comparison', label: 'Scenarios', icon: '⧉' },
  { path: '/branches', label: 'Ensembles', icon: '⑂' },
  { path: '/updates', label: 'Sit Updates', icon: '◈' },
];

export function Sidebar() {
  const location = useLocation();
  const navigate = useNavigate();

  return (
    <aside className="w-56 flex-shrink-0 bg-bg-card border-r border-border flex flex-col">
      <div className="p-4 border-b border-border">
        <h1 className="text-sm font-semibold text-text-accent tracking-wider uppercase">
          War Room
        </h1>
        <p className="text-xs text-text-muted mt-1">Hormuz Crisis Sim</p>
      </div>
      <nav className="flex-1 py-2">
        {NAV_ITEMS.map(item => {
          const active = location.pathname === item.path;
          return (
            <button
              key={item.path}
              onClick={() => navigate(item.path)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 text-sm transition-colors ${
                active
                  ? 'bg-bg-hover text-text-accent border-r-2 border-text-accent'
                  : 'text-text-muted hover:text-text-primary hover:bg-bg-hover'
              }`}
            >
              <span className="text-base">{item.icon}</span>
              {item.label}
            </button>
          );
        })}
      </nav>
    </aside>
  );
}
