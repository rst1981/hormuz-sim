import { useState, useEffect } from 'react';
import { useSimulationStore } from '../stores/simulationStore';
import { useUpdateStore } from '../stores/updateStore';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip } from 'recharts';
import { colors, TRUMP_COLORS } from '../theme';
import { ReplayControls } from '../components/ReplayControls';
import { NarrativeFeed } from '../components/NarrativeFeed';
import { ResetButton } from '../components/ResetButton';

export function DashboardPage() {
  const { simId, simState, turns, createSim, runSim, loading, reset } = useSimulationStore();
  const { availableDates, snapshots, fetchDates, fetchSnapshots } = useUpdateStore();
  const [selectedDate, setSelectedDate] = useState('');
  const [selectedSnapshot, setSelectedSnapshot] = useState('');

  useEffect(() => { fetchDates(); fetchSnapshots(); }, [fetchDates, fetchSnapshots]);

  if (!simId) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-6">
        <div className="text-center">
          <h2 className="text-2xl font-semibold text-text-primary">Hormuz Crisis War Room</h2>
          <p className="text-text-muted text-sm max-w-md mt-2">
            Interactive simulation of the Strait of Hormuz crisis. Select a baseline and create a simulation to begin.
          </p>
        </div>

        {/* Baseline selector */}
        <div className="w-96 space-y-3">
          {/* Original baseline */}
          <button
            onClick={() => createSim()}
            disabled={loading}
            className="w-full bg-bg-card border border-border rounded-lg p-4 text-left hover:border-text-accent transition-colors disabled:opacity-50"
          >
            <div className="text-sm font-semibold text-text-primary">Load Original Baseline (17 Mar)</div>
            <div className="text-[10px] text-text-muted mt-1">Day 18 parameters — no situation updates applied</div>
          </button>

          {/* Situation update baselines */}
          <div className="bg-bg-card border border-border rounded-lg p-4 space-y-3">
            <h3 className="text-sm font-semibold text-text-primary text-center">Load Situation Update Baseline</h3>
            <p className="text-[10px] text-text-muted text-center">Baselines generated from approved news events and analysis</p>

            {snapshots.length === 0 ? (
              <p className="text-xs text-text-muted text-center py-4">
                No saved baselines yet. Use Situation Updates to scrape news, approve events, and save a baseline.
              </p>
            ) : (
              <>
                <div className="space-y-1.5 max-h-56 overflow-y-auto">
                  {snapshots.map(s => (
                    <button
                      key={s.id}
                      onClick={() => setSelectedSnapshot(s.id === selectedSnapshot ? '' : s.id)}
                      className={`w-full px-3 py-2 rounded border text-left text-sm transition-colors ${
                        selectedSnapshot === s.id
                          ? 'border-text-accent bg-[#58a6ff10] text-text-primary'
                          : 'border-border bg-bg-hover text-text-muted hover:text-text-primary hover:border-text-accent'
                      }`}
                    >
                      <div className="flex justify-between items-center">
                        <span className="font-mono text-xs">{s.name}</span>
                        <span className="text-[10px] text-text-muted">{s.date}</span>
                      </div>
                    </button>
                  ))}
                </div>
                {selectedSnapshot && (
                  <button
                    onClick={() => createSim('baseline', undefined, undefined, undefined, selectedSnapshot)}
                    disabled={loading}
                    className="w-full px-4 py-2.5 bg-text-accent text-bg-primary rounded font-medium text-sm hover:opacity-90 transition-opacity disabled:opacity-50"
                  >
                    {loading ? 'Creating...' : 'Create Simulation'}
                  </button>
                )}
              </>
            )}
          </div>

          {availableDates.length > 0 && (
            <div className="bg-bg-card border border-border rounded-lg p-4 space-y-2">
              <h3 className="text-xs uppercase tracking-wider text-text-muted font-semibold text-center">Historical Date</h3>
              <div className="flex gap-2">
                <select
                  value={selectedDate}
                  onChange={e => setSelectedDate(e.target.value)}
                  className="flex-1 px-3 py-2 bg-bg-primary border border-border rounded text-sm font-mono text-text-primary"
                >
                  <option value="">Select date...</option>
                  {availableDates.map(d => (
                    <option key={d} value={d}>{d}</option>
                  ))}
                </select>
                <button
                  onClick={() => selectedDate && createSim('baseline', undefined, undefined, selectedDate)}
                  disabled={!selectedDate || loading}
                  className="px-4 py-2 bg-bg-hover border border-border rounded text-sm hover:bg-bg-hover transition-colors disabled:opacity-40 font-mono"
                >
                  Go
                </button>
              </div>
            </div>
          )}
        </div>
      </div>
    );
  }

  const metrics = simState;
  const oilData = turns.map(t => ({ turn: t.turn, price: t.oil_price }));
  const escData = turns.map(t => ({ turn: t.turn, level: t.escalation_level }));
  const lastTurn = turns[turns.length - 1];

  return (
    <div className="space-y-6">
      {/* Replay Controls */}
      <div className="flex items-center justify-between">
        <ReplayControls />
        <div className="flex items-center gap-2">
          <button onClick={() => runSim()} disabled={loading || simState?.termination.outcome !== 'continuing'}
            className="px-4 py-1.5 bg-bg-card border border-border rounded text-sm hover:bg-bg-hover transition-colors disabled:opacity-40 font-mono">
            ⏩ Run All
          </button>
          <ResetButton onClick={reset} label="New Sim" />
        </div>
      </div>

      {/* KPI Cards */}
      <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-6 gap-3">
        <KPICard label="Oil Price" value={`$${metrics?.oil_market.price.toFixed(0) ?? '—'}`} color={colors.chart.oil} />
        <KPICard label="Escalation" value={metrics?.escalation.level.toFixed(1) ?? '—'} sub={metrics?.escalation.phase.replace(/_/g, ' ')} color={colors.chart.escalation} />
        <KPICard label="Trump Mode" value={lastTurn?.trump_mode ?? '—'} color={TRUMP_COLORS[lastTurn?.trump_mode ?? ''] ?? colors.text.muted} />
        <KPICard label="Iran Faction" value={lastTurn?.iran_dominant_faction ?? '—'} color={colors.chart.iran} />
        <KPICard label="Interceptors" value={`${((metrics?.ground_truth.israel_interceptor_stocks ?? 0) * 100).toFixed(0)}%`} color={colors.chart.coalition} />
        <KPICard label="Regime" value={`${((metrics?.ground_truth.regime_survival_index ?? 0) * 100).toFixed(0)}%`} color={colors.chart.iran} />
      </div>

      {/* Charts */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <ChartCard title="Oil Price Trajectory">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={oilData}>
              <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} domain={['auto', 'auto']} />
              <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
              <Line type="monotone" dataKey="price" stroke={colors.chart.oil} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
        <ChartCard title="Escalation Level">
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={escData}>
              <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
              <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} domain={[0, 10]} />
              <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
              <Line type="monotone" dataKey="level" stroke={colors.chart.escalation} strokeWidth={2} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        </ChartCard>
      </div>

      {/* Narrative Feed */}
      <NarrativeFeed turns={turns} />
    </div>
  );
}

function KPICard({ label, value, sub, color }: { label: string; value: string; sub?: string; color: string }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-3">
      <div className="text-[10px] uppercase tracking-wider text-text-muted">{label}</div>
      <div className="text-lg font-mono font-semibold mt-1" style={{ color }}>{value}</div>
      {sub && <div className="text-[10px] text-text-muted mt-0.5">{sub}</div>}
    </div>
  );
}

function ChartCard({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <div className="bg-bg-card border border-border rounded-lg p-4">
      <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">{title}</h3>
      {children}
    </div>
  );
}
