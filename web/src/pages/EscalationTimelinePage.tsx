import { useSimulationStore } from '../stores/simulationStore';
import { LineChart, Line, XAxis, YAxis, ResponsiveContainer, Tooltip, ReferenceArea, ReferenceLine } from 'recharts';
import { colors } from '../theme';
import { SensitivityMatrix } from '../components/SensitivityMatrix';
import { ResetButton } from '../components/ResetButton';

const PHASES = [
  { y1: 0, y2: 3, label: 'Diplomatic', fill: '#3fb95020' },
  { y1: 3, y2: 5, label: 'Proxy', fill: '#d2992220' },
  { y1: 5, y2: 7, label: 'Direct', fill: '#f0883e20' },
  { y1: 7, y2: 9, label: 'Multi-State', fill: '#f8514920' },
  { y1: 9, y2: 10, label: 'Total War', fill: '#da363320' },
];

export function EscalationTimelinePage() {
  const { simState, turns, reset } = useSimulationStore();

  const data = turns.map(t => ({ turn: t.turn, level: t.escalation_level }));
  const esc = simState?.escalation;

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold">Escalation Timeline</h2>
        <ResetButton onClick={reset} label="New Sim" />
      </div>

      <div className="bg-bg-card border border-border rounded-lg p-4">
        <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Escalation Level with Phase Bands</h3>
        <ResponsiveContainer width="100%" height={350}>
          <LineChart data={data}>
            {PHASES.map(p => (
              <ReferenceArea key={p.label} y1={p.y1} y2={p.y2} fill={p.fill} label={{ value: p.label, position: 'insideLeft', fontSize: 9, fill: '#8b949e' }} />
            ))}
            <XAxis dataKey="turn" tick={{ fontSize: 10, fill: '#8b949e' }} />
            <YAxis domain={[0, 10]} tick={{ fontSize: 10, fill: '#8b949e' }} />
            <Tooltip contentStyle={{ background: '#111820', border: '1px solid #21262d', fontSize: 12 }} />
            <ReferenceLine y={7.5} stroke="#8b949e" strokeDasharray="3 3" label={{ value: 'Day 18', fontSize: 9, fill: '#8b949e' }} />
            <Line type="monotone" dataKey="level" stroke={colors.chart.escalation} strokeWidth={2} dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Richardson Dynamics */}
      {esc && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Richardson Arms-Race Dynamics</h3>
          <div className="grid grid-cols-3 gap-4">
            {Object.entries(esc.richardson_state).map(([side, params]) => (
              <div key={side} className="space-y-2">
                <div className="text-sm font-medium text-text-primary capitalize">{side.replace(/_/g, ' ')}</div>
                <div className="text-xs font-mono space-y-1">
                  <Row label="Grievance" value={params.grievance} color="#f85149" />
                  <Row label="Reactivity" value={params.reactivity} color="#f0883e" />
                  <Row label="Fatigue" value={params.fatigue} color="#3fb950" />
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Activity Heatmap */}
      <SensitivityMatrix turns={turns} />

      {/* Miscalculations */}
      {esc && esc.miscalculation_events.length > 0 && (
        <div className="bg-bg-card border border-border rounded-lg p-4">
          <h3 className="text-xs uppercase tracking-wider text-text-muted mb-3">Active Miscalculations</h3>
          <div className="space-y-1 max-h-48 overflow-auto">
            {esc.miscalculation_events.map((m, i) => (
              <div key={i} className="text-xs text-escalation">⚠ {m}</div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}

function Row({ label, value, color }: { label: string; value: number; color: string }) {
  return (
    <div className="flex items-center gap-2">
      <span className="text-text-muted w-20">{label}</span>
      <div className="flex-1 h-1.5 bg-bg-primary rounded-full overflow-hidden">
        <div className="h-full rounded-full" style={{ width: `${Math.min(100, value * 100)}%`, background: color }} />
      </div>
      <span style={{ color }}>{value.toFixed(2)}</span>
    </div>
  );
}
