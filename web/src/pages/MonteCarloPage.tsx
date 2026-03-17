import { useState, useEffect } from 'react';
import { useMonteCarloStore } from '../stores/monteCarloStore';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, ScatterChart, Scatter, CartesianGrid } from 'recharts';
import { colors, OUTCOME_COLORS } from '../theme';
import { getVariants } from '../api/client';
import type { Variant } from '../types';
import { ResetButton } from '../components/ResetButton';

export function MonteCarloPage() {
  const { jobs, activeJobId, launch, reset } = useMonteCarloStore();
  const [variant, setVariant] = useState('baseline');
  const [nRuns, setNRuns] = useState(100);
  const [maxTurns, setMaxTurns] = useState(120);
  const [variants, setVariants] = useState<Variant[]>([]);

  useEffect(() => { getVariants().then(setVariants).catch(() => {}); }, []);

  const job = activeJobId ? jobs[activeJobId] : null;
  const results = job?.results;

  const outcomeData = results ? Object.entries(results.outcome_distribution).map(([k, v]) => ({
    name: k.replace(/_/g, ' '), value: +(v * 100).toFixed(1), fill: OUTCOME_COLORS[k] || colors.text.muted,
  })) : [];

  const scatterData = results?.runs.map(r => ({
    turns: r.turns, oil: r.final_oil_price, outcome: r.outcome,
  })) || [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Monte Carlo Analysis</h2>
        <ResetButton onClick={reset} label="Reset MC" />
      </div>

      {/* Config */}
      <div className="bg-bg-card border border-border rounded-lg p-4 flex flex-wrap gap-4 items-end">
        <div>
          <label className="text-[10px] uppercase text-text-muted block mb-1">Variant</label>
          <select value={variant} onChange={e => setVariant(e.target.value)}
            className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm text-text-primary">
            {variants.map(v => <option key={v.id} value={v.id}>{v.name}</option>)}
          </select>
        </div>
        <div>
          <label className="text-[10px] uppercase text-text-muted block mb-1">Runs</label>
          <input type="number" value={nRuns} onChange={e => setNRuns(+e.target.value)} min={1} max={5000}
            className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm font-mono w-24 text-text-primary" />
        </div>
        <div>
          <label className="text-[10px] uppercase text-text-muted block mb-1">Max Turns</label>
          <input type="number" value={maxTurns} onChange={e => setMaxTurns(+e.target.value)} min={1} max={200}
            className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm font-mono w-24 text-text-primary" />
        </div>
        <button onClick={() => launch(variant, nRuns, maxTurns)}
          disabled={job?.status.status === 'running'}
          className="px-4 py-1.5 bg-text-accent text-bg-primary rounded text-sm font-medium hover:opacity-90 disabled:opacity-50">
          {job?.status.status === 'running' ? 'Running...' : 'Launch'}
        </button>
      </div>

      {/* Progress */}
      {job && job.status.status === 'running' && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <div className="flex justify-between text-xs text-text-muted mb-2">
            <span>Progress</span>
            <span className="font-mono">{job.status.completed} / {job.status.total}</span>
          </div>
          <div className="h-2 bg-bg-primary rounded-full overflow-hidden">
            <div className="h-full bg-text-accent transition-all rounded-full"
              style={{ width: `${(job.status.completed / job.status.total) * 100}%` }} />
          </div>
        </div>
      )}

      {/* Results */}
      {results && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Outcome Distribution</h3>
            <ResponsiveContainer width="100%" height={250}>
              <BarChart data={outcomeData}>
                <XAxis dataKey="name" tick={{ fontSize: 9, fill: '#8b949e' }} angle={-30} textAnchor="end" height={60} />
                <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} unit="%" />
                <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
                <Bar dataKey="value" radius={[4, 4, 0, 0]}>
                  {outcomeData.map((d, i) => <Bar key={i} dataKey="value" fill={d.fill} />)}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Duration vs Oil Price</h3>
            <ResponsiveContainer width="100%" height={250}>
              <ScatterChart>
                <CartesianGrid strokeDasharray="3 3" stroke="#21262d" />
                <XAxis dataKey="turns" name="Turns" tick={{ fontSize: 10, fill: '#8b949e' }} />
                <YAxis dataKey="oil" name="Oil $" tick={{ fontSize: 10, fill: '#8b949e' }} />
                <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
                <Scatter data={scatterData} fill={colors.chart.oil} fillOpacity={0.6} />
              </ScatterChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-4 col-span-full">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Statistics</h3>
            <div className="grid grid-cols-3 gap-4">
              <StatBlock label="Duration" stats={results.duration_stats} unit=" turns" />
              <StatBlock label="Final Oil Price" stats={results.oil_price_stats} unit="$" prefix />
              <StatBlock label="Final Escalation" stats={results.escalation_stats} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}

function StatBlock({ label, stats, unit = '', prefix = false }: {
  label: string; stats: { mean: number; min: number; max: number; std: number; median: number }; unit?: string; prefix?: boolean;
}) {
  const fmt = (v: number) => prefix ? `${unit}${v.toFixed(0)}` : `${v.toFixed(1)}${unit}`;
  return (
    <div>
      <div className="text-[10px] uppercase text-text-muted mb-2">{label}</div>
      <div className="grid grid-cols-2 gap-1 text-xs font-mono">
        <span className="text-text-muted">Mean</span><span>{fmt(stats.mean)}</span>
        <span className="text-text-muted">Median</span><span>{fmt(stats.median)}</span>
        <span className="text-text-muted">Min</span><span>{fmt(stats.min)}</span>
        <span className="text-text-muted">Max</span><span>{fmt(stats.max)}</span>
        <span className="text-text-muted">Std</span><span>{stats.std.toFixed(2)}</span>
      </div>
    </div>
  );
}
