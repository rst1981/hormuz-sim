import { lazy, Suspense } from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { AppShell } from './components/layout/AppShell';
import { DashboardPage } from './pages/DashboardPage';

const ParameterEditorPage = lazy(() => import('./pages/ParameterEditorPage').then(m => ({ default: m.ParameterEditorPage })));
const MonteCarloPage = lazy(() => import('./pages/MonteCarloPage').then(m => ({ default: m.MonteCarloPage })));
const EscalationTimelinePage = lazy(() => import('./pages/EscalationTimelinePage').then(m => ({ default: m.EscalationTimelinePage })));
const OilMarketPage = lazy(() => import('./pages/OilMarketPage').then(m => ({ default: m.OilMarketPage })));
const AgentExplorerPage = lazy(() => import('./pages/AgentExplorerPage').then(m => ({ default: m.AgentExplorerPage })));
const TrumpTrackerPage = lazy(() => import('./pages/TrumpTrackerPage').then(m => ({ default: m.TrumpTrackerPage })));
const ScenarioComparisonPage = lazy(() => import('./pages/ScenarioComparisonPage').then(m => ({ default: m.ScenarioComparisonPage })));
const BranchComparisonPage = lazy(() => import('./pages/BranchComparisonPage').then(m => ({ default: m.BranchComparisonPage })));
const SituationUpdatesPage = lazy(() => import('./pages/SituationUpdatesPage').then(m => ({ default: m.SituationUpdatesPage })));

function PageLoader() {
  return (
    <div className="flex items-center justify-center h-64">
      <div className="text-text-muted text-sm font-mono">Loading...</div>
    </div>
  );
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route element={<AppShell />}>
          <Route path="/" element={<DashboardPage />} />
          <Route path="/parameters" element={<Suspense fallback={<PageLoader />}><ParameterEditorPage /></Suspense>} />
          <Route path="/montecarlo" element={<Suspense fallback={<PageLoader />}><MonteCarloPage /></Suspense>} />
          <Route path="/escalation" element={<Suspense fallback={<PageLoader />}><EscalationTimelinePage /></Suspense>} />
          <Route path="/oil" element={<Suspense fallback={<PageLoader />}><OilMarketPage /></Suspense>} />
          <Route path="/agents" element={<Suspense fallback={<PageLoader />}><AgentExplorerPage /></Suspense>} />
          <Route path="/trump" element={<Suspense fallback={<PageLoader />}><TrumpTrackerPage /></Suspense>} />
          <Route path="/comparison" element={<Suspense fallback={<PageLoader />}><ScenarioComparisonPage /></Suspense>} />
          <Route path="/branches" element={<Suspense fallback={<PageLoader />}><BranchComparisonPage /></Suspense>} />
          <Route path="/updates" element={<Suspense fallback={<PageLoader />}><SituationUpdatesPage /></Suspense>} />
        </Route>
      </Routes>
    </BrowserRouter>
  );
}
