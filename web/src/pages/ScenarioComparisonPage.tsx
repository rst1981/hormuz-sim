import { useState, useEffect } from 'react';
import { BarChart, Bar, XAxis, YAxis, ResponsiveContainer, Tooltip, Legend } from 'recharts';
import { getVariants, launchComparison, getComparisonResults } from '../api/client';
import { colors, OUTCOME_COLORS } from '../theme';
import type { Variant, MCResult } from '../types';
import { ResetButton } from '../components/ResetButton';

export function ScenarioComparisonPage() {
  const [variants, setVariants] = useState<Variant[]>([]);
  const [selected, setSelected] = useState<string[]>(['baseline', 'houthi_activation']);
  const [nRuns, setNRuns] = useState(50);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState<Record<string, MCResult> | null>(null);

  useEffect(() => { getVariants().then(setVariants).catch(() => {}); }, []);

  const handleLaunch = async () => {
    setLoading(true);
    try {
      const { job_id } = await launchComparison({ variants: selected, n_runs: nRuns });
      // Poll for results
      const poll = setInterval(async () => {
        const res = await getComparisonResults(job_id);
        if (res.status === 'completed') {
          clearInterval(poll);
          setResults(res.results);
          setLoading(false);
        }
      }, 2000);
    } catch {
      setLoading(false);
    }
  };

  const outcomeKeys = results ? [...new Set(Object.values(results).flatMap(r => r ? Object.keys(r.outcome_distribution) : []))] : [];

  const compData = results ? selected.map(v => {
    const r = results[v];
    if (!r) return { variant: v };
    const row: Record<string, unknown> = { variant: v };
    for (const k of outcomeKeys) row[k] = +((r.outcome_distribution[k] || 0) * 100).toFixed(1);
    return row;
  }) : [];

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Scenario Comparison</h2>
        <ResetButton onClick={() => { setResults(null); setSelected(['baseline', 'houthi_activation']); setNRuns(50); }} label="Reset" />
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Select Variants</h3>
        <div className="flex flex-wrap gap-2 mb-4">
          {variants.map(v => (
            <button
              key={v.id}
              onClick={() => setSelected(s => s.includes(v.id) ? s.filter(x => x !== v.id) : [...s, v.id])}
              className={`px-3 py-1.5 text-xs rounded border transition-colors ${
                selected.includes(v.id)
                  ? 'bg-text-accent/20 border-text-accent text-text-accent'
                  : 'bg-bg-input border-border text-text-muted hover:text-text-primary'
              }`}
            >
              {v.name}
            </button>
          ))}
        </div>
        <div className="flex items-center gap-4">
          <div>
            <label className="text-[10px] uppercase text-text-muted block mb-1">Runs per variant</label>
            <input type="number" value={nRuns} onChange={e => setNRuns(+e.target.value)} min={10} max={500}
              className="bg-bg-input border border-border rounded px-3 py-1.5 text-sm font-mono w-24 text-text-primary" />
          </div>
          <button onClick={handleLaunch} disabled={loading || selected.length < 2}
            className="px-4 py-1.5 bg-text-accent text-bg-primary rounded text-sm font-medium hover:opacity-90 disabled:opacity-50 mt-5">
            {loading ? 'Running...' : `Compare ${selected.length} Variants`}
          </button>
        </div>
      </div>

      {results && (
        <>
          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Outcome Distribution by Variant</h3>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={compData}>
                <XAxis dataKey="variant" tick={{ fontSize: 10, fill: '#8b949e' }} />
                <YAxis tick={{ fontSize: 10, fill: '#8b949e' }} unit="%" />
                <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
                <Legend wrapperStyle={{ fontSize: 10 }} />
                {outcomeKeys.map(k => (
                  <Bar key={k} dataKey={k} stackId="a" fill={OUTCOME_COLORS[k] || colors.text.muted} />
                ))}
              </BarChart>
            </ResponsiveContainer>
          </div>

          <div className="bg-bg-card border border-border rounded-lg p-4">
            <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Summary Statistics</h3>
            <div className="overflow-auto">
              <table className="w-full text-xs font-mono">
                <thead>
                  <tr className="text-text-muted border-b border-border">
                    <th className="text-left py-2 pr-4">Variant</th>
                    <th className="text-right px-2">Runs</th>
                    <th className="text-right px-2">Avg Duration</th>
                    <th className="text-right px-2">Avg Oil $</th>
                    <th className="text-right px-2">Avg Escalation</th>
                  </tr>
                </thead>
                <tbody>
                  {selected.map(v => {
                    const r = results[v];
                    if (!r) return null;
                    return (
                      <tr key={v} className="border-b border-border/50">
                        <td className="py-2 pr-4 text-text-primary">{v}</td>
                        <td className="text-right px-2">{r.n_runs}</td>
                        <td className="text-right px-2">{r.duration_stats.mean.toFixed(1)}</td>
                        <td className="text-right px-2" style={{ color: colors.chart.oil }}>${r.oil_price_stats.mean.toFixed(0)}</td>
                        <td className="text-right px-2" style={{ color: colors.chart.escalation }}>{r.escalation_stats.mean.toFixed(1)}</td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        </>
      )}
    </div>
  );
}
